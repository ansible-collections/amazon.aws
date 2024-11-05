# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import traceback
from copy import deepcopy

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .ec2 import get_ec2_security_group_ids_from_names
from .elb_utils import AnsibleELBv2Error
from .elb_utils import add_listener_certificates
from .elb_utils import add_tags
from .elb_utils import convert_tg_name_to_arn
from .elb_utils import create_listener
from .elb_utils import create_load_balancer
from .elb_utils import create_rule
from .elb_utils import delete_listener
from .elb_utils import delete_load_balancer
from .elb_utils import delete_rule
from .elb_utils import describe_listeners
from .elb_utils import describe_load_balancer_attributes
from .elb_utils import describe_rules
from .elb_utils import describe_tags
from .elb_utils import get_elb
from .elb_utils import modify_listener
from .elb_utils import modify_load_balancer_attributes
from .elb_utils import modify_rule
from .elb_utils import remove_tags
from .elb_utils import set_ip_address_type
from .elb_utils import set_rule_priorities
from .elb_utils import set_security_groups
from .elb_utils import set_subnets
from .modules import AnsibleAWSModule
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict
from .transformation import scrub_none_parameters
from .waiters import get_waiter


def _simple_forward_config_arn(config: Dict[str, Any], parent_arn: Optional[str]) -> Optional[str]:
    config = deepcopy(config)

    stickiness = config.pop("TargetGroupStickinessConfig", {"Enabled": False})
    # Stickiness options set, non default value
    if stickiness != {"Enabled": False}:
        return None

    target_groups = config.pop("TargetGroups", [])

    # non-default config left over, probably invalid
    if config:
        return None
    # Multiple TGS, not simple
    if len(target_groups) > 1:
        return None

    if not target_groups:
        # with no TGs defined, but an ARN set, this is one of the minimum possible configs
        return parent_arn

    target_group = target_groups[0]
    # We don't care about the weight with a single TG
    target_group.pop("Weight", None)

    target_group_arn = target_group.pop("TargetGroupArn", None)

    # non-default config left over
    if target_group:
        return None

    # We didn't find an ARN
    if not (target_group_arn or parent_arn):
        return None

    # Only one
    if not parent_arn:
        return target_group_arn
    if not target_group_arn:
        return parent_arn

    if parent_arn != target_group_arn:
        return None

    return target_group_arn


# ForwardConfig may be optional if we've got a single TargetGroupArn entry
def _prune_ForwardConfig(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drops a redundant ForwardConfig where TargetGroupARN has already been set.
    (So we can perform comparisons)
    """
    if action.get("Type", "") != "forward":
        return action
    if "ForwardConfig" not in action:
        return action

    parent_arn = action.get("TargetGroupArn", None)
    arn = _simple_forward_config_arn(action["ForwardConfig"], parent_arn)
    if not arn:
        return action

    # Remove the redundant ForwardConfig
    newAction = action.copy()
    del newAction["ForwardConfig"]
    newAction["TargetGroupArn"] = arn
    return newAction


# remove the client secret if UseExistingClientSecret, because aws won't return it
# add default values when they are not requested
def _prune_secret(action: Dict[str, Any]) -> Dict[str, Any]:
    if action["Type"] != "authenticate-oidc":
        return action

    if not action["AuthenticateOidcConfig"].get("Scope", False):
        action["AuthenticateOidcConfig"]["Scope"] = "openid"

    if not action["AuthenticateOidcConfig"].get("SessionTimeout", False):
        action["AuthenticateOidcConfig"]["SessionTimeout"] = 604800

    if action["AuthenticateOidcConfig"].get("UseExistingClientSecret", False):
        action["AuthenticateOidcConfig"].pop("ClientSecret", None)

    if not action["AuthenticateOidcConfig"].get("OnUnauthenticatedRequest", False):
        action["AuthenticateOidcConfig"]["OnUnauthenticatedRequest"] = "authenticate"

    if not action["AuthenticateOidcConfig"].get("SessionCookieName", False):
        action["AuthenticateOidcConfig"]["SessionCookieName"] = "AWSELBAuthSessionCookie"

    return action


# while AWS api also won't return UseExistingClientSecret key
# it must be added, because it's requested and compared
def _append_use_existing_client_secretn(action: Dict[str, Any]) -> Dict[str, Any]:
    if action["Type"] != "authenticate-oidc":
        return action

    action["AuthenticateOidcConfig"]["UseExistingClientSecret"] = True

    return action


def _sort_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(actions, key=lambda x: x.get("Order", 0))


def _sort_listener_actions(actions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(
        actions,
        key=lambda x: (
            x.get("AuthenticateOidcConfig"),
            x.get("FixedResponseConfig"),
            x.get("RedirectConfig"),
            x.get("TargetGroupArn"),
            x.get("Type"),
        ),
    )


class ElasticLoadBalancerV2:
    def __init__(self, connection: Any, module: AnsibleAWSModule) -> None:
        self.connection = connection
        self.module = module
        self.changed = False
        self.new_load_balancer = False
        self.scheme = module.params.get("scheme")
        self.name = module.params.get("name")
        self.type: str
        self.subnet_mappings = module.params.get("subnet_mappings")
        self.subnets = module.params.get("subnets")
        self.deletion_protection = module.params.get("deletion_protection")
        self.elb_ip_addr_type = module.params.get("ip_address_type")
        self.wait = module.params.get("wait")

        if module.params.get("tags") is not None:
            self.tags = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
        else:
            self.tags = None

        self.purge_tags = module.params.get("purge_tags")

        self.elb = get_elb(connection, module, self.name)
        self.elb_attributes = {}
        if self.elb is not None:
            self.elb_attributes = self.get_elb_attributes()
            self.elb_ip_addr_type = self.get_elb_ip_address_type()
            self.elb["tags"] = self.get_elb_tags()
        self.check_mode = module.check_mode
        self.exit_json = module.exit_json
        self.fail_json = module.fail_json
        self.fail_json_aws = module.fail_json_aws
        self.fail_json_aws_error = module.fail_json_aws_error
        self.params = module.params

    def wait_for_ip_type(self, elb_arn: str, ip_type: str) -> None:
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if not self.wait:
            return

        waiter_names = {
            "ipv4": "load_balancer_ip_address_type_ipv4",
            "dualstack": "load_balancer_ip_address_type_dualstack",
        }
        if ip_type not in waiter_names:
            return

        try:
            waiter = get_waiter(self.connection, waiter_names.get(ip_type))
            waiter.wait(LoadBalancerArns=[elb_arn])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def wait_for_status(self, elb_arn: str) -> None:
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if not self.wait:
            return

        try:
            waiter = get_waiter(self.connection, "load_balancer_available")
            waiter.wait(LoadBalancerArns=[elb_arn])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def wait_for_deletion(self, elb_arn: str) -> None:
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if self.wait:
            try:
                waiter = get_waiter(self.connection, "load_balancers_deleted")
                waiter.wait(LoadBalancerArns=[elb_arn])
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e)

    def get_elb_attributes(self) -> Dict[str, Any]:
        """
        Get load balancer attributes

        :return:
        """

        elb_attributes = boto3_tag_list_to_ansible_dict(
            describe_load_balancer_attributes(self.connection, self.elb["LoadBalancerArn"])
        )

        # Replace '.' with '_' in attribute key names to make it more Ansibley
        return dict((k.replace(".", "_"), v) for k, v in elb_attributes.items())

    def get_elb_ip_address_type(self) -> Optional[str]:
        """
        Retrieve load balancer ip address type using describe_load_balancers

        :return:
        """

        return self.elb.get("IpAddressType", None)

    def update_elb_attributes(self) -> None:
        """
        Update the elb_attributes parameter
        :return:
        """
        self.elb_attributes = self.get_elb_attributes()

    def get_elb_tags(self) -> Dict[str, str]:
        """
        Get load balancer tags

        :return:
        """

        try:
            elb_tags = describe_tags(self.connection, resource_arns=[self.elb["LoadBalancerArn"]])[0]["Tags"]
        except AnsibleELBv2Error as e:
            self.module.fail_json_aws(e)
        return elb_tags

    def delete_tags(self, tags_to_delete: List[str]) -> None:
        """
        Delete elb tags

        :return:
        """

        try:
            self.changed = remove_tags(self.connection, [self.elb["LoadBalancerArn"]], tags_to_delete)
        except AnsibleELBv2Error as e:
            self.module.fail_json_aws(e)

    def modify_tags(self) -> None:
        """
        Modify elb tags

        :return:
        """

        try:
            self.changed = add_tags(self.connection, [self.elb["LoadBalancerArn"]], self.tags)
        except AnsibleELBv2Error as e:
            self.module.fail_json_aws(e)

    def delete(self) -> None:
        """
        Delete elb
        :return:
        """

        try:
            self.changed = delete_load_balancer(self.connection, self.elb["LoadBalancerArn"])
        except AnsibleELBv2Error as e:
            self.module.fail_json_aws(e)
        if self.changed:
            self.wait_for_deletion(self.elb["LoadBalancerArn"])

    def compare_subnets(self) -> bool:
        """
        Compare user subnets with current ELB subnets

        :return: bool True if they match otherwise False
        """

        subnet_mapping_id_list = []
        subnet_mappings = []

        # Check if we're dealing with subnets or subnet_mappings
        if self.subnets is not None:
            # Convert subnets to subnet_mappings format for comparison
            for subnet in self.subnets:
                subnet_mappings.append({"SubnetId": subnet})

        if self.subnet_mappings is not None:
            # Use this directly since we're comparing as a mapping
            subnet_mappings = self.subnet_mappings

        # Build a subnet_mapping style struture of what's currently
        # on the load balancer
        for subnet in self.elb["AvailabilityZones"]:
            this_mapping = {"SubnetId": subnet["SubnetId"]}
            for address in subnet.get("LoadBalancerAddresses", []):
                if "AllocationId" in address:
                    this_mapping["AllocationId"] = address["AllocationId"]
                    break

            subnet_mapping_id_list.append(this_mapping)

        return set(frozenset(mapping.items()) for mapping in subnet_mapping_id_list) == set(
            frozenset(mapping.items()) for mapping in subnet_mappings
        )

    def modify_subnets(self) -> None:
        """
        Modify elb subnets to match module parameters
        :return:
        """
        set_subnets(self.connection, self.elb["LoadBalancerArn"], Subnets=self.subnets)
        self.changed = True

    def update(self) -> None:
        """
        Update the elb from AWS
        :return:
        """

        self.elb = get_elb(self.connection, self.module, self.module.params.get("name"))
        self.elb["tags"] = self.get_elb_tags()

    def modify_ip_address_type(self, ip_addr_type) -> None:
        """
        Modify ELB ip address type
        :return:
        """
        if ip_addr_type is None:
            return
        if self.elb_ip_addr_type == ip_addr_type:
            return

        set_ip_address_type(self.connection, self.elb["LoadBalancerArn"], ip_addr_type)

        self.changed = True
        self.wait_for_ip_type(self.elb["LoadBalancerArn"], ip_addr_type)

    def _elb_create_params(self) -> Dict[str, Any]:
        # Required parameters
        params = dict()
        params["Name"] = self.name
        params["Type"] = self.type

        # Other parameters
        if self.elb_ip_addr_type is not None:
            params["IpAddressType"] = self.elb_ip_addr_type
        if self.subnets is not None:
            params["Subnets"] = self.subnets
        if self.subnet_mappings is not None:
            params["SubnetMappings"] = self.subnet_mappings
        if self.tags:
            params["Tags"] = self.tags
        # Scheme isn't supported for GatewayLBs, so we won't add it here, even though we don't
        # support them yet.

        return params

    def create_elb(self) -> None:
        """
        Create a load balancer
        :return:
        """

        params = self._elb_create_params()

        name = params.pop("Name")
        self.elb = create_load_balancer(self.connection, name, **params)[0]
        self.changed = True
        self.new_load_balancer = True
        self.wait_for_status(self.elb["LoadBalancerArn"])


class ApplicationLoadBalancer(ElasticLoadBalancerV2):
    def __init__(self, connection: Any, connection_ec2: Any, module: AnsibleAWSModule) -> None:
        """

        :param connection: boto3 connection
        :param module: Ansible module
        """
        super().__init__(connection, module)

        self.connection_ec2 = connection_ec2

        # Ansible module parameters specific to ALBs
        self.type = "application"
        if module.params.get("security_groups") is not None:
            try:
                self.security_groups = AWSRetry.jittered_backoff()(get_ec2_security_group_ids_from_names)(
                    module.params.get("security_groups"), self.connection_ec2
                )
            except ValueError as e:
                self.fail_json(msg=str(e), exception=traceback.format_exc())
            except (BotoCoreError, ClientError) as e:
                self.fail_json_aws(e)
        else:
            self.security_groups = module.params.get("security_groups")
        self.access_logs_enabled = module.params.get("access_logs_enabled")
        self.access_logs_s3_bucket = module.params.get("access_logs_s3_bucket")
        self.access_logs_s3_prefix = module.params.get("access_logs_s3_prefix")
        self.idle_timeout = module.params.get("idle_timeout")
        self.http2 = module.params.get("http2")
        self.http_desync_mitigation_mode = module.params.get("http_desync_mitigation_mode")
        self.http_drop_invalid_header_fields = module.params.get("http_drop_invalid_header_fields")
        self.http_x_amzn_tls_version_and_cipher_suite = module.params.get("http_x_amzn_tls_version_and_cipher_suite")
        self.http_xff_client_port = module.params.get("http_xff_client_port")
        self.waf_fail_open = module.params.get("waf_fail_open")

        if self.elb is not None and self.elb["Type"] != "application":
            self.fail_json(
                msg="The load balancer type you are trying to manage is not application. Try elb_network_lb module instead.",
            )

    def _elb_create_params(self) -> Dict[str, Any]:
        params = super()._elb_create_params()

        if self.security_groups is not None:
            params["SecurityGroups"] = self.security_groups
        params["Scheme"] = self.scheme

        return params

    def compare_elb_attributes(self) -> bool:
        """
        Compare user attributes with current ELB attributes
        :return: bool True if they match otherwise False
        """

        update_attributes = []
        if (
            self.access_logs_enabled is not None
            and str(self.access_logs_enabled).lower() != self.elb_attributes["access_logs_s3_enabled"]
        ):
            update_attributes.append({"Key": "access_logs.s3.enabled", "Value": str(self.access_logs_enabled).lower()})
        if (
            self.access_logs_s3_bucket is not None
            and self.access_logs_s3_bucket != self.elb_attributes["access_logs_s3_bucket"]
        ):
            update_attributes.append({"Key": "access_logs.s3.bucket", "Value": self.access_logs_s3_bucket})
        if (
            self.access_logs_s3_prefix is not None
            and self.access_logs_s3_prefix != self.elb_attributes["access_logs_s3_prefix"]
        ):
            update_attributes.append({"Key": "access_logs.s3.prefix", "Value": self.access_logs_s3_prefix})
        if (
            self.deletion_protection is not None
            and str(self.deletion_protection).lower() != self.elb_attributes["deletion_protection_enabled"]
        ):
            update_attributes.append(
                {"Key": "deletion_protection.enabled", "Value": str(self.deletion_protection).lower()}
            )
        if (
            self.idle_timeout is not None
            and str(self.idle_timeout) != self.elb_attributes["idle_timeout_timeout_seconds"]
        ):
            update_attributes.append({"Key": "idle_timeout.timeout_seconds", "Value": str(self.idle_timeout)})
        if self.http2 is not None and str(self.http2).lower() != self.elb_attributes["routing_http2_enabled"]:
            update_attributes.append({"Key": "routing.http2.enabled", "Value": str(self.http2).lower()})
        if (
            self.http_desync_mitigation_mode is not None
            and str(self.http_desync_mitigation_mode).lower()
            != self.elb_attributes["routing_http_desync_mitigation_mode"]
        ):
            update_attributes.append(
                {"Key": "routing.http.desync_mitigation_mode", "Value": str(self.http_desync_mitigation_mode).lower()}
            )
        if (
            self.http_drop_invalid_header_fields is not None
            and str(self.http_drop_invalid_header_fields).lower()
            != self.elb_attributes["routing_http_drop_invalid_header_fields_enabled"]
        ):
            update_attributes.append(
                {
                    "Key": "routing.http.drop_invalid_header_fields.enabled",
                    "Value": str(self.http_drop_invalid_header_fields).lower(),
                }
            )
        if (
            self.http_x_amzn_tls_version_and_cipher_suite is not None
            and str(self.http_x_amzn_tls_version_and_cipher_suite).lower()
            != self.elb_attributes["routing_http_x_amzn_tls_version_and_cipher_suite_enabled"]
        ):
            update_attributes.append(
                {
                    "Key": "routing.http.x_amzn_tls_version_and_cipher_suite.enabled",
                    "Value": str(self.http_x_amzn_tls_version_and_cipher_suite).lower(),
                }
            )
        if (
            self.http_xff_client_port is not None
            and str(self.http_xff_client_port).lower() != self.elb_attributes["routing_http_xff_client_port_enabled"]
        ):
            update_attributes.append(
                {"Key": "routing.http.xff_client_port.enabled", "Value": str(self.http_xff_client_port).lower()}
            )
        if (
            self.waf_fail_open is not None
            and str(self.waf_fail_open).lower() != self.elb_attributes["waf_fail_open_enabled"]
        ):
            update_attributes.append({"Key": "waf.fail_open.enabled", "Value": str(self.waf_fail_open).lower()})

        return not update_attributes

    def modify_elb_attributes(self) -> None:
        """
        Update Application ELB attributes if required

        :return:
        """

        update_attributes = []

        if (
            self.access_logs_enabled is not None
            and str(self.access_logs_enabled).lower() != self.elb_attributes["access_logs_s3_enabled"]
        ):
            update_attributes.append({"Key": "access_logs.s3.enabled", "Value": str(self.access_logs_enabled).lower()})
        if (
            self.access_logs_s3_bucket is not None
            and self.access_logs_s3_bucket != self.elb_attributes["access_logs_s3_bucket"]
        ):
            update_attributes.append({"Key": "access_logs.s3.bucket", "Value": self.access_logs_s3_bucket})
        if (
            self.access_logs_s3_prefix is not None
            and self.access_logs_s3_prefix != self.elb_attributes["access_logs_s3_prefix"]
        ):
            update_attributes.append({"Key": "access_logs.s3.prefix", "Value": self.access_logs_s3_prefix})
        if (
            self.deletion_protection is not None
            and str(self.deletion_protection).lower() != self.elb_attributes["deletion_protection_enabled"]
        ):
            update_attributes.append(
                {"Key": "deletion_protection.enabled", "Value": str(self.deletion_protection).lower()}
            )
        if (
            self.idle_timeout is not None
            and str(self.idle_timeout) != self.elb_attributes["idle_timeout_timeout_seconds"]
        ):
            update_attributes.append({"Key": "idle_timeout.timeout_seconds", "Value": str(self.idle_timeout)})
        if self.http2 is not None and str(self.http2).lower() != self.elb_attributes["routing_http2_enabled"]:
            update_attributes.append({"Key": "routing.http2.enabled", "Value": str(self.http2).lower()})
        if (
            self.http_desync_mitigation_mode is not None
            and str(self.http_desync_mitigation_mode).lower()
            != self.elb_attributes["routing_http_desync_mitigation_mode"]
        ):
            update_attributes.append(
                {"Key": "routing.http.desync_mitigation_mode", "Value": str(self.http_desync_mitigation_mode).lower()}
            )
        if (
            self.http_drop_invalid_header_fields is not None
            and str(self.http_drop_invalid_header_fields).lower()
            != self.elb_attributes["routing_http_drop_invalid_header_fields_enabled"]
        ):
            update_attributes.append(
                {
                    "Key": "routing.http.drop_invalid_header_fields.enabled",
                    "Value": str(self.http_drop_invalid_header_fields).lower(),
                }
            )
        if (
            self.http_x_amzn_tls_version_and_cipher_suite is not None
            and str(self.http_x_amzn_tls_version_and_cipher_suite).lower()
            != self.elb_attributes["routing_http_x_amzn_tls_version_and_cipher_suite_enabled"]
        ):
            update_attributes.append(
                {
                    "Key": "routing.http.x_amzn_tls_version_and_cipher_suite.enabled",
                    "Value": str(self.http_x_amzn_tls_version_and_cipher_suite).lower(),
                }
            )
        if (
            self.http_xff_client_port is not None
            and str(self.http_xff_client_port).lower() != self.elb_attributes["routing_http_xff_client_port_enabled"]
        ):
            update_attributes.append(
                {"Key": "routing.http.xff_client_port.enabled", "Value": str(self.http_xff_client_port).lower()}
            )
        if (
            self.waf_fail_open is not None
            and str(self.waf_fail_open).lower() != self.elb_attributes["waf_fail_open_enabled"]
        ):
            update_attributes.append({"Key": "waf.fail_open.enabled", "Value": str(self.waf_fail_open).lower()})

        if update_attributes:
            try:
                modify_load_balancer_attributes(self.connection, self.elb["LoadBalancerArn"], update_attributes)
                self.changed = True
            except AnsibleELBv2Error as e:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    delete_load_balancer(self.connection, self.elb["LoadBalancerArn"])
                self.fail_json_aws(e)

    def compare_security_groups(self) -> bool:
        """
        Compare user security groups with current ELB security groups

        :return: bool True if they match otherwise False
        """

        if set(self.elb["SecurityGroups"]) != set(self.security_groups):
            return False
        return True

    def modify_security_groups(self) -> None:
        """
        Modify elb security groups to match module parameters
        :return:
        """
        set_security_groups(self.connection, self.elb["LoadBalancerArn"], self.security_groups)
        self.changed = True


class NetworkLoadBalancer(ElasticLoadBalancerV2):
    def __init__(self, connection: Any, connection_ec2: Any, module: AnsibleAWSModule) -> None:
        """

        :param connection: boto3 connection
        :param module: Ansible module
        """
        super().__init__(connection, module)

        self.connection_ec2 = connection_ec2

        # Ansible module parameters specific to NLBs
        self.type = "network"
        self.cross_zone_load_balancing = module.params.get("cross_zone_load_balancing")

        if self.elb is not None and self.elb["Type"] != "network":
            self.fail_json(
                msg="The load balancer type you are trying to manage is not network. Try elb_application_lb module instead.",
            )

    def _elb_create_params(self) -> Dict[str, Any]:
        params = super()._elb_create_params()

        params["Scheme"] = self.scheme

        return params

    def modify_elb_attributes(self) -> None:
        """
        Update Network ELB attributes if required

        :return:
        """

        update_attributes = []

        if (
            self.cross_zone_load_balancing is not None
            and str(self.cross_zone_load_balancing).lower() != self.elb_attributes["load_balancing_cross_zone_enabled"]
        ):
            update_attributes.append(
                {"Key": "load_balancing.cross_zone.enabled", "Value": str(self.cross_zone_load_balancing).lower()}
            )
        if (
            self.deletion_protection is not None
            and str(self.deletion_protection).lower() != self.elb_attributes["deletion_protection_enabled"]
        ):
            update_attributes.append(
                {"Key": "deletion_protection.enabled", "Value": str(self.deletion_protection).lower()}
            )

        if update_attributes:
            try:
                modify_load_balancer_attributes(self.connection, self.elb["LoadBalancerArn"], update_attributes)
                self.changed = True
            except AnsibleELBv2Error as e:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    delete_load_balancer(self.connection, LoadBalancerArn=self.elb["LoadBalancerArn"])
                self.fail_json_aws(e)

    def modify_subnets(self):
        """
        Modify elb subnets to match module parameters (unsupported for NLB)
        :return:
        """

        self.fail_json(msg="Modifying subnets and elastic IPs is not supported for Network Load Balancer")


def _compare_listener(current_listener: Dict[str, Any], new_listener: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compare two listeners. We do not check the port as the function is expecting that
    the two listeners are passed with the same port value.

    :param current_listener: The current listener attributes as stored into AWS
    :param new_listener: The listener as defined into module parameters
    :return: A dict containing the resulting update to perform on the current listener
    """

    modified_listener = {}

    # Protocol
    current_protocol = current_listener["Protocol"]
    new_protocol = new_listener["Protocol"]
    if current_protocol != new_protocol:
        modified_listener["Protocol"] = new_protocol

    # SslPolicy and Certificates are compared if the new listener protocol is
    # one of the following 'HTTPS', 'TLS'
    if new_protocol in ("HTTPS", "TLS"):
        # SslPolicy
        current_ssl_policy = current_listener.get("SslPolicy")
        new_ssl_policy = new_listener.get("SslPolicy")
        if new_ssl_policy and any(
            (not current_ssl_policy, current_ssl_policy and current_ssl_policy != new_ssl_policy)
        ):
            modified_listener["SslPolicy"] = new_ssl_policy

        # Certificates
        new_certificates = new_listener.get("Certificates")
        current_certificates = current_listener.get("Certificates")
        if new_certificates and any(
            (
                not current_certificates,
                current_certificates
                and current_certificates[0]["CertificateArn"] != new_certificates[0]["CertificateArn"],
            )
        ):
            modified_listener["Certificates"] = [{"CertificateArn": new_certificates[0]["CertificateArn"]}]

    # Default actions
    # If the lengths of the actions are the same, we'll have to verify that the
    # contents of those actions are the same
    current_default_actions = current_listener.get("DefaultActions")
    new_default_actions = new_listener.get("DefaultActions")
    if new_default_actions:
        if current_default_actions and len(current_default_actions) == len(new_default_actions):
            current_actions_sorted = _sort_listener_actions(
                {
                    k: v
                    for k, v in x.items()
                    if k
                    in ["AuthenticateOidcConfig", "FixedResponseConfig", "RedirectConfig", "TargetGroupArn", "Type"]
                }
                for x in current_default_actions
            )
            if current_actions_sorted != _sort_listener_actions(new_default_actions):
                modified_listener["DefaultActions"] = new_default_actions
        # If the action lengths are different, then replace with the new actions
        else:
            modified_listener["DefaultActions"] = new_default_actions

    # AlpnPolicy
    new_alpn_policy = new_listener.get("AlpnPolicy")
    if new_alpn_policy and new_protocol == "TLS":
        current_alpn_policy = current_listener.get("AlpnPolicy")
        if current_listener["Protocol"] != "TLS" or (
            current_listener["Protocol"] == "TLS"
            and (not current_alpn_policy or current_alpn_policy[0] != new_alpn_policy[0])
        ):
            modified_listener["AlpnPolicy"] = new_alpn_policy

    return modified_listener


def _group_listeners(
    current_listeners: List[Dict[str, Any]], new_listeners: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    This function groups listeners.
    - listeners to add: any new listener from module parameters not present of the current listeners stored in AWS resource.
    - listeners to delete: any listener currently stored in AWS resource and not present of the module parameters.
    - listeners to modify: any listener present in both list but with different properties.
    The listener key is the Port value.

    :param current_listeners: The current listeners stored into AWS.
    :param new_listeners: The listeners as defined into module parameters.
    :return: A dict containing 3 lists of listeners groups.
    """
    listeners_to_modify = []
    listeners_to_delete = []
    listeners_to_add = deepcopy(new_listeners)

    # Check each current listener port to see if it's been passed to the module
    for current_listener in current_listeners:
        idx = next(
            (i for i, listener in enumerate(listeners_to_add) if int(listener["Port"]) == current_listener["Port"]), -1
        )
        if idx == -1:
            # The current listener is not present in new_listeners
            listeners_to_delete.append(current_listener["ListenerArn"])
            continue
        # Remove what we match so that what is left can be marked as 'to be added'
        m_listener = listeners_to_add.pop(idx)
        # Now compare the 2 listeners with the same Port value
        modified_listener = _compare_listener(current_listener, m_listener)
        if modified_listener:
            modified_listener.update({"Port": current_listener["Port"], "ListenerArn": current_listener["ListenerArn"]})
            listeners_to_modify.append(modified_listener)

    return listeners_to_add, listeners_to_modify, listeners_to_delete


def _prepare_listeners(
    connection, module: AnsibleAWSModule, listeners: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    # This functions prepare listener defined in module parameters
    # 1. Remove None elements from listener attribute
    # 2. Tranform AlpnPolicy, value is set as string but API is expected a list
    # 3. For listener defining Target group name, replaced them with the corresponding Target group ARN
    updated_listeners = []
    if not listeners:
        return updated_listeners
    target_group_mapping = {}
    for item in listeners:
        listener = deepcopy(item)
        # Remove suboption argspec defaults of None from each listener
        listener = scrub_none_parameters(listener, descend_into_lists=False)
        # Converts 'AlpnPolicy' attribute of listener from string type to list
        if "AlpnPolicy" in listener:
            listener["AlpnPolicy"] = [listener["AlpnPolicy"]]
        # If a listener DefaultAction has been passed with a Target Group Name instead of ARN,
        # lookup the ARN and replace the name.
        for action in listener["DefaultActions"]:
            tg_name = action.pop("TargetGroupName", None)
            if tg_name:
                if tg_name not in target_group_mapping:
                    target_group_mapping[tg_name] = convert_tg_name_to_arn(connection, module, tg_name)
                action["TargetGroupArn"] = target_group_mapping[tg_name]
        updated_listeners.append(listener)
    return updated_listeners


class ELBListeners:
    def __init__(self, connection: Any, module: AnsibleAWSModule, elb_arn: str) -> None:
        self.connection = connection
        self.module = module
        self.elb_arn = elb_arn
        self.listeners = _prepare_listeners(connection, module, module.params.get("listeners"))
        self.update()
        self.purge_listeners = module.params.get("purge_listeners")
        self.changed = False

    def update(self) -> None:
        """
        Update the listeners for the ELB

        :return:
        """
        self.current_listeners = describe_listeners(self.connection, load_balancer_arn=self.elb_arn)

    def get_listener_arn_from_listener_port(self, listener_port: int) -> Optional[str]:
        listener_arn = None
        for listener in self.current_listeners:
            if listener["Port"] == listener_port:
                listener_arn = listener["ListenerArn"]
                break
        return listener_arn

    def compare_listeners(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """This function call the _group_listeners method and update the listeners
        to delete depending on the value set on `purge_listeners` parameter.
        """
        listeners_to_add, listeners_to_modify, listeners_to_delete = _group_listeners(
            self.current_listeners, self.listeners
        )
        # Prepare listeners to add/modify, Remove the key 'Rules' from attributes
        # 'Rules' is not a valid attribute for 'create_listener' and 'modify_listener'
        for listener in listeners_to_add + listeners_to_modify:
            listener.pop("Rules", None)
        # If `purge_listeners` is set to False, we empty the list of listeners to delete
        listeners_to_delete = listeners_to_delete if self.purge_listeners else []
        return listeners_to_add, listeners_to_modify, listeners_to_delete


class ELBListener:
    def __init__(self, connection: Any, module: AnsibleAWSModule, listener: Dict[str, Any], elb_arn: str) -> None:
        """

        :param connection:
        :param module:
        :param listener:
        :param elb_arn:
        """

        self.connection = connection
        self.module = module
        self.listener = listener
        self.elb_arn = elb_arn

    def create_listener(self) -> str:
        return create_listener(self.connection, self.elb_arn, **self.listener)[0]["ListenerArn"]

    def add(self) -> None:
        # handle multiple certs by adding only 1 cert during listener creation and make calls to add_listener_certificates to add other certs
        listener_certificates = self.listener.get("Certificates", [])
        first_certificate, other_certs = [], []
        if len(listener_certificates) > 0:
            first_certificate, other_certs = listener_certificates[0], listener_certificates[1:]
            self.listener["Certificates"] = [first_certificate]
        # create listener
        listener_arn = self.create_listener()
        # only one cert can be specified per call to add_listener_certificates
        for cert in other_certs:
            add_listener_certificates(self.connection, listener_arn=listener_arn, certificates=[cert])

    def modify(self) -> None:
        listener_arn = self.listener.pop("ListenerArn")
        modify_listener(self.connection, listener_arn=listener_arn, **self.listener)

    def delete(self) -> None:
        delete_listener(self.connection, self.listener)


def _check_rule_condition(current_conditions: List[Dict[str, Any]], condition: Dict[str, Any]) -> bool:
    """This function checks if the condition is part of the list of current condition

    Parameters:
    current_conditions: The list of conditions
    condition: The condition we are trying to find into the list

    Returns:
    True if the condition is part of the list, False if not.
    """

    condition_found = False
    compare_keys = (
        "HostHeaderConfig",
        "HttpHeaderConfig",
        "HttpRequestMethodConfig",
        "SourceIpConfig",
        "PathPatternConfig",
    )
    # Do an initial sorting of condition keys
    s_condition = deepcopy(condition)
    for key in compare_keys:
        if key in s_condition:
            s_condition[key]["Values"] = sorted(s_condition[key]["Values"])
    if "Values" in s_condition:
        s_condition["Values"] = sorted(s_condition["Values"])

    for current_condition in current_conditions:
        # 'Field' should match for the conditions to be equal, compare it once at the begining
        if current_condition["Field"] != s_condition["Field"]:
            continue
        # host-header: current_condition includes both HostHeaderConfig AND Values while
        # condition can be defined with either HostHeaderConfig OR Values. Only use
        # HostHeaderConfig['Values'] comparison if both conditions includes HostHeaderConfig.
        if current_condition.get("HostHeaderConfig") and s_condition.get("HostHeaderConfig"):
            if sorted(current_condition["HostHeaderConfig"]["Values"]) == s_condition["HostHeaderConfig"]["Values"]:
                condition_found = True
                break
        elif current_condition.get("HttpHeaderConfig"):
            if (
                sorted(current_condition["HttpHeaderConfig"]["Values"]) == s_condition["HttpHeaderConfig"]["Values"]
                and current_condition["HttpHeaderConfig"]["HttpHeaderName"]
                == s_condition["HttpHeaderConfig"]["HttpHeaderName"]
            ):
                condition_found = True
                break
        elif current_condition.get("HttpRequestMethodConfig"):
            if (
                sorted(current_condition["HttpRequestMethodConfig"]["Values"])
                == s_condition["HttpRequestMethodConfig"]["Values"]
            ):
                condition_found = True
                break
        # path-pattern: current_condition includes both PathPatternConfig AND Values while
        # condition can be defined with either PathPatternConfig OR Values. Only use
        # PathPatternConfig['Values'] comparison if both conditions includes PathPatternConfig.
        elif current_condition.get("PathPatternConfig") and s_condition.get("PathPatternConfig"):
            if sorted(current_condition["PathPatternConfig"]["Values"]) == s_condition["PathPatternConfig"]["Values"]:
                condition_found = True
                break
        elif current_condition.get("QueryStringConfig"):
            # QueryString Values is not sorted as it is the only list of dicts (not strings).
            if current_condition["QueryStringConfig"]["Values"] == s_condition["QueryStringConfig"]["Values"]:
                condition_found = True
                break
        elif current_condition.get("SourceIpConfig"):
            if sorted(current_condition["SourceIpConfig"]["Values"]) == s_condition["SourceIpConfig"]["Values"]:
                condition_found = True
                break
        # Not all fields are required to have Values list nested within a *Config dict
        # e.g. fields host-header/path-pattern can directly list Values
        elif sorted(current_condition["Values"]) == s_condition["Values"]:
            condition_found = True
            break

    return condition_found


def _compare_rule_actions(current_actions: List[Dict[str, Any]], new_actions: List[Dict[str, Any]]) -> bool:
    """This function compares current_actions with new_actions.
    Bfore to the comparison, the function will set the default values for some attributes of the new actions
    as these are not part of the module parameters.

    Parameters:
    current_actions: The current AWS rule actions
    new_actions: The rule actions from module parameters.

    Returns:
    True if the current_actions and new_actions are equal, False if not.
    """
    # If the lengths of the actions are the same, we'll have to verify that the
    # contents of those actions are the same
    if len(current_actions) != len(new_actions):
        return False

    # if actions have just one element, compare the contents and then update if
    # they're different
    current_actions_sorted = _sort_actions(current_actions)
    new_actions_sorted = _sort_actions(deepcopy(new_actions))

    new_current_actions_sorted = [_append_use_existing_client_secretn(i) for i in current_actions_sorted]
    new_actions_sorted_no_secret = [_prune_secret(i) for i in new_actions_sorted]

    return [_prune_ForwardConfig(i) for i in new_current_actions_sorted] == [
        _prune_ForwardConfig(i) for i in new_actions_sorted_no_secret
    ]


def _compare_rule(current_rule: Dict[str, Any], new_rule: Dict[str, Any]) -> Dict[str, Any]:
    """This function compares rule_a with rule_b and returns differences
    between the two rules as a dictionnary

    Parameters:
    current_rule: The current listener rule stored in AWS.
    new_rule: The new listener rule.

    Returns:
    A dictionnary containing the modified attributes.
    """

    modified_rule = {}

    # Priority
    if int(current_rule["Priority"]) != int(new_rule["Priority"]):
        modified_rule["Priority"] = new_rule["Priority"]

    # Actions
    actions_match = _compare_rule_actions(current_rule["Actions"], new_rule["Actions"])
    if not actions_match:
        modified_rule["Actions"] = new_rule["Actions"]

    # Conditions
    modified_conditions = [
        c for c in new_rule["Conditions"] if not _check_rule_condition(current_rule["Conditions"], c)
    ]
    if modified_conditions:
        modified_rule["Conditions"] = modified_conditions

    return modified_rule


def _group_rules(
    current_rules: List[Dict[str, Any]], rules: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """This function compares listener rules from AWS with module provided listener rules and a matrix with the
    following:
        - Rules to add: a rule is added when it is part of the module parameters and not currently stored on AWS
        - Rules to set priority: Any rule with unchanged attributes but with a different priority value
        - Rules to modify: Any rule on which one the following attribute has changed 'Actions', 'Conditions'
        - Rules to delete: Any rule currently stored on AWS and not defined in module parameters.

    Parameters:
    current_rules: The current listener rules stored in AWS.
    rules: The new listener rules.

    Returns:
    A tuple with a list of rules to add, a list of rules to set priority, a list of rules to modify and a list of rules to delete
    """

    rules_to_modify = []
    rules_to_delete = []
    rules_to_add = deepcopy(rules)
    rules_to_set_priority = []

    # List rules to update priority, 'Actions' and 'Conditions' remain the same
    # only the 'Priority' has changed
    _current_rules = deepcopy(current_rules)
    remaining_rules = []
    while _current_rules:
        current_rule = _current_rules.pop(0)
        # Skip the default rule, this one can't be modified
        if current_rule.get("IsDefault", False):
            continue
        to_keep = True
        for new_rule in rules_to_add:
            modified_rule = _compare_rule(current_rule, new_rule)
            if not modified_rule:
                # The current rule has been passed with the same properties to the module
                # Remove it for later comparison
                rules_to_add.remove(new_rule)
                to_keep = False
                break
            if modified_rule and list(modified_rule.keys()) == ["Priority"]:
                # if only the Priority has changed
                modified_rule["Priority"] = int(new_rule["Priority"])
                modified_rule["RuleArn"] = current_rule["RuleArn"]

                rules_to_set_priority.append(modified_rule)
                to_keep = False
                rules_to_add.remove(new_rule)
                break
        if to_keep:
            remaining_rules.append(current_rule)

    for current_rule in remaining_rules:
        current_rule_passed_to_module = False
        for new_rule in rules_to_add:
            if current_rule["Priority"] == str(new_rule["Priority"]):
                current_rule_passed_to_module = True
                # Remove what we match so that what is left can be marked as 'to be added'
                rules_to_add.remove(new_rule)
                modified_rule = _compare_rule(current_rule, new_rule)
                if modified_rule:
                    modified_rule["Priority"] = int(current_rule["Priority"])
                    modified_rule["RuleArn"] = current_rule["RuleArn"]
                    modified_rule["Actions"] = new_rule["Actions"]
                    modified_rule["Conditions"] = new_rule["Conditions"]
                    # You cannot both specify a client secret and set UseExistingClientSecret to true
                    for action in modified_rule.get("Actions", []):
                        if action.get("AuthenticateOidcConfig", {}).get("ClientSecret", False):
                            action["AuthenticateOidcConfig"]["UseExistingClientSecret"] = False
                    rules_to_modify.append(modified_rule)
                break

        # If the current rule was not matched against passed rules, mark for removal
        if not current_rule_passed_to_module and not current_rule.get("IsDefault", False):
            rules_to_delete.append(current_rule["RuleArn"])

    return rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete


class ELBListenerRules:
    def __init__(
        self,
        connection: Any,
        module: AnsibleAWSModule,
        listener_arn: Optional[str],
        listener_rules: List[Dict[str, Any]],
    ) -> None:
        self.connection = connection
        self.module = module
        self.rules = self._ensure_rules_action_has_arn(listener_rules)
        self.changed = False

        self.listener_arn = listener_arn
        self.current_rules = describe_rules(self.connection, ListenerArn=listener_arn)

    def _ensure_rules_action_has_arn(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        If a rule Action has been passed with a Target Group Name instead of ARN, lookup the ARN and
        replace the name.

        :param rules: a list of rule dicts
        :return: the same list of dicts ensuring that each rule Actions dict has TargetGroupArn key. If a TargetGroupName key exists, it is removed.
        """

        fixed_rules = []
        for rule in rules:
            fixed_actions = []
            for action in rule["Actions"]:
                if "TargetGroupName" in action:
                    action["TargetGroupArn"] = convert_tg_name_to_arn(
                        self.connection, self.module, action["TargetGroupName"]
                    )
                    del action["TargetGroupName"]
                fixed_actions.append(action)
            rule["Actions"] = fixed_actions
            fixed_rules.append(rule)

        return fixed_rules

    def compare_rules(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """This function creates the rule matrix (to add, to set priority, to modify, to delete)
        and prepare them to be ready for AWS API call.

        Returns:
        A tuple with a list of rules to add, a list of rules to set priority, a list of rules to modify and a list of rules to delete
        """
        rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete = _group_rules(
            self.current_rules, self.rules
        )

        # Prepare Rule to create (to add)
        # For rules to create 'UseExistingClientSecret' should be set to False, The 'Priority' need
        # To be an int value and the ListenerArn need to be set
        for rule in rules_to_add:
            for action in rule.get("Actions", []):
                if action.get("AuthenticateOidcConfig", {}).get("UseExistingClientSecret", False):
                    action["AuthenticateOidcConfig"]["UseExistingClientSecret"] = False
            rule["ListenerArn"] = self.listener_arn
            rule["Priority"] = int(rule["Priority"])

        # Prepare Rule to modify: We need to remove the 'Priority' key
        for rule in rules_to_modify:
            del rule["Priority"]

        return rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete


class ELBListenerRule:
    def __init__(self, connection, module) -> None:
        self.connection = connection
        self.module = module

    def create(self, rule: Dict[str, Any]) -> None:
        """
        Create a listener rule

        :return:
        """
        listener_arn = rule.pop("ListenerArn")
        conditions = rule.pop("Conditions")
        priority = rule.pop("Priority")
        actions = rule.pop("Actions")
        tags = rule.pop("Tags", None)
        create_rule(
            self.connection,
            listener_arn=listener_arn,
            conditions=conditions,
            actions=actions,
            tags=tags,
            priority=priority,
        )

    def modify(self, rule: Dict[str, Any]) -> None:
        """
        Modify a listener rule

        :return:
        """
        rule_arn = rule.pop("RuleArn")
        modify_rule(self.connection, rule_arn=rule_arn, **rule)

    def delete(self, rule_arn: str) -> None:
        """
        Delete a listener rule

        :return:
        """
        delete_rule(self.connection, rule_arn)

    def set_rule_priorities(self, rules: List[Dict[str, Any]]) -> None:
        """
        Sets the priorities of the specified rules.

        :return:
        """
        set_rule_priorities(
            self.connection, [{"RuleArn": rule["RuleArn"], "Priority": rule["Priority"]} for rule in rules]
        )

    def process_rules(
        self,
        rules_to_create: List[Dict[str, Any]],
        rules_to_set_priority: List[Dict[str, Any]],
        rules_to_modify: List[Dict[str, Any]],
        rules_to_delete: List[str],
    ) -> bool:
        changed = False
        if rules_to_set_priority:
            self.set_rule_priorities(rules_to_set_priority)
            changed = True
        if self.module.params["purge_rules"]:
            for arn in rules_to_delete:
                self.delete(arn)
                changed = True
        for rule in rules_to_create:
            self.create(rule)
            changed = True
        for rule in rules_to_modify:
            self.modify(rule)
            changed = True
        return changed

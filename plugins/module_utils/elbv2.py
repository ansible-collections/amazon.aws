# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import traceback
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# Not intended for general re-use / re-import
from ._elbv2 import actions as _actions
from ._elbv2 import common as _common
from ._elbv2 import listeners as _listeners
from ._elbv2 import rules as _rules
from ._elbv2 import transformations as _transformations
from ._elbv2 import waiters as _waiters
from .ec2 import get_ec2_security_group_ids_from_names

# Re-export API wrapper functions from _elbv2.api
from ._elbv2 import api as _api

add_listener_certificates = _api.add_listener_certificates
add_tags = _api.add_tags
create_listener = _api.create_listener
create_load_balancer = _api.create_load_balancer
create_rule = _api.create_rule
delete_listener = _api.delete_listener
delete_load_balancer = _api.delete_load_balancer
delete_rule = _api.delete_rule
describe_listeners = _api.describe_listeners
describe_load_balancer_attributes = _api.describe_load_balancer_attributes
describe_load_balancers = _api.describe_load_balancers
describe_rules = _api.describe_rules
describe_tags = _api.describe_tags
describe_target_groups = _api.describe_target_groups
modify_listener = _api.modify_listener
modify_load_balancer_attributes = _api.modify_load_balancer_attributes
modify_rule = _api.modify_rule
remove_tags = _api.remove_tags
set_ip_address_type = _api.set_ip_address_type
set_rule_priorities = _api.set_rule_priorities
set_security_groups = _api.set_security_groups
set_subnets = _api.set_subnets

# Re-export helper functions from elb_utils
from .elb_utils import convert_tg_name_to_arn
from .elb_utils import get_elb
from .elb_utils import get_elb_listener_rules
from .exceptions import AnsibleAWSError
from .modules import AnsibleAWSModule
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict

# Expose error handling classes
AnsibleELBv2Error = _common.AnsibleELBv2Error
ELBv2ErrorHandler = _common.ELBv2ErrorHandler
ELBv2ListenerErrorHandler = _common.ELBv2ListenerErrorHandler
ELBv2RuleErrorHandler = _common.ELBv2RuleErrorHandler
ELBv2TargetGroupErrorHandler = _common.ELBv2TargetGroupErrorHandler

# Expose transformation functions
normalize_application_load_balancer = _transformations.normalize_application_load_balancer

# Expose listener classes and functions
ELBListeners = _listeners.ELBListeners
ELBListener = _listeners.ELBListener
_compare_listener = _listeners._compare_listener
_group_listeners = _listeners._group_listeners
_prepare_listeners = _listeners._prepare_listeners

# Expose rule classes and functions
ELBListenerRules = _rules.ELBListenerRules
ELBListenerRule = _rules.ELBListenerRule
_check_rule_condition = _rules._check_rule_condition
_compare_rule_actions = _rules._compare_rule_actions
_compare_rule = _rules._compare_rule
_group_rules = _rules._group_rules

# Expose action processing functions
_simple_forward_config_arn = _actions._simple_forward_config_arn
_prune_ForwardConfig = _actions._prune_ForwardConfig
_prune_secret = _actions._prune_secret
_append_use_existing_client_secret = _actions._append_use_existing_client_secret


def get_elbv2_waiter(client: Any, waiter_name: str):
    """
    Get an ELBv2 waiter with improved error handling.

    Args:
        client: Boto3 ELBv2 client
        waiter_name: Name of the waiter to retrieve

    Returns:
        Waiter instance configured for the specified operation

    Raises:
        AnsibleELBv2Error: If waiter creation or operation fails
    """
    factory = _waiters.ELBv2WaiterFactory()
    return factory.get_waiter(client, waiter_name)


@ELBv2ErrorHandler.common_error_handler("wait for load balancer")
@AWSRetry.jittered_backoff(retries=10)
def wait_for_load_balancer(client: Any, waiter_name: str, **params) -> None:
    """
    Wait for a load balancer operation to complete.

    Args:
        client: Boto3 ELBv2 client
        waiter_name: Name of the waiter to use
        **params: Parameters to pass to the waiter

    Raises:
        AnsibleELBv2Error: If the wait operation fails
    """
    waiter = get_elbv2_waiter(client, waiter_name)
    waiter.wait(**params)


def build_application_load_balancer_description(
    connection: Any,
    load_balancer: Dict[str, Any],
    include_attributes: bool = True,
    include_listeners: bool = True,
    include_listener_rules: bool = True,
) -> Dict[str, Any]:
    """
    Build a complete ALB description with optional attributes, listeners, and rules.

    Takes a base load balancer dict from describe_load_balancers and enriches it with
    additional information based on the include_* parameters, then normalizes the result.

    Args:
        connection: boto3 elbv2 connection
        load_balancer: Base ALB dict from describe_load_balancers (in CamelCase boto3 format)
        include_attributes: Whether to fetch and attach load balancer attributes
        include_listeners: Whether to fetch and attach listeners
        include_listener_rules: Whether to fetch and attach rules to each listener

    Returns:
        Normalized ALB dict in snake_case Ansible format

    Note:
        This function does not fetch tags. Tags should be handled separately by the caller
        as they require a separate API call and may be added before or after normalization
        depending on the use case.
    """
    # Make a copy to avoid modifying the original
    alb = load_balancer.copy()

    # Optionally add attributes (in raw boto3 format, normalization will convert them)
    if include_attributes:
        alb["Attributes"] = describe_load_balancer_attributes(connection, alb["LoadBalancerArn"])

    # Optionally add listeners
    if include_listeners or include_listener_rules:
        alb["Listeners"] = describe_listeners(connection, load_balancer_arn=alb["LoadBalancerArn"])

        # Optionally add rules to each listener
        if include_listener_rules:
            for listener in alb["Listeners"]:
                listener["Rules"] = describe_rules(connection, ListenerArn=listener["ListenerArn"])

    # Normalize the entire ALB object (convert to snake_case, sort rules, convert tags)
    return normalize_application_load_balancer(alb)


def validate_listener_https_requirements(listeners: Optional[List[Dict[str, Any]]]) -> None:
    """
    Validate that HTTPS listeners have required SSL configuration.

    Checks that listeners using the HTTPS protocol include both SslPolicy
    and Certificates configuration.

    Args:
        listeners: List of listener configuration dicts, or None

    Raises:
        AnsibleELBv2Error: If any HTTPS listener is missing required SslPolicy or Certificates
    """
    if listeners is None:
        return

    for listener in listeners:
        if listener.get("Protocol") == "HTTPS":
            if listener.get("SslPolicy") is None:
                raise AnsibleELBv2Error(message="'SslPolicy' is a required listener dict key when Protocol = HTTPS")
            if listener.get("Certificates") is None:
                raise AnsibleELBv2Error(message="'Certificates' is a required listener dict key when Protocol = HTTPS")


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
            wait_for_load_balancer(self.connection, waiter_names.get(ip_type), LoadBalancerArns=[elb_arn])
        except AnsibleELBv2Error as e:
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
            wait_for_load_balancer(self.connection, "load_balancer_available", LoadBalancerArns=[elb_arn])
        except AnsibleELBv2Error as e:
            self.module.fail_json_aws(e)

    def wait_for_deletion(self, elb_arn: str) -> None:
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if self.wait:
            try:
                wait_for_load_balancer(self.connection, "load_balancers_deleted", LoadBalancerArns=[elb_arn])
            except AnsibleELBv2Error as e:
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
        return describe_tags(self.connection, resource_arns=[self.elb["LoadBalancerArn"]])[0]["Tags"]

    def delete_tags(self, tags_to_delete: List[str]) -> None:
        """
        Delete elb tags

        :return:
        """
        self.changed |= remove_tags(self.connection, [self.elb["LoadBalancerArn"]], tags_to_delete)

    def modify_tags(self) -> None:
        """
        Modify elb tags

        :return:
        """
        self.changed |= add_tags(self.connection, [self.elb["LoadBalancerArn"]], self.tags)

    def delete(self) -> None:
        """
        Delete elb
        :return:
        """
        self.changed |= delete_load_balancer(self.connection, self.elb["LoadBalancerArn"])
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
            except AnsibleAWSError as e:
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
            except AnsibleELBv2Error:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    delete_load_balancer(self.connection, self.elb["LoadBalancerArn"])
                raise

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
            except AnsibleELBv2Error:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    delete_load_balancer(self.connection, LoadBalancerArn=self.elb["LoadBalancerArn"])
                raise

    def modify_subnets(self):
        """
        Modify elb subnets to match module parameters (unsupported for NLB)
        :return:
        """

        self.fail_json(msg="Modifying subnets and elastic IPs is not supported for Network Load Balancer")

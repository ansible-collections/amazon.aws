# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import traceback
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# Intended for general use / re-import
# pylint: disable=unused-import,useless-import-alias
from ._elbv2.actions import _append_use_existing_client_secret as _append_use_existing_client_secret
from ._elbv2.actions import _prune_forward_config as _prune_forward_config
from ._elbv2.actions import _prune_secret as _prune_secret
from ._elbv2.actions import _simple_forward_config_arn as _simple_forward_config_arn
from ._elbv2.api import add_listener_certificates as add_listener_certificates
from ._elbv2.api import add_tags as add_tags
from ._elbv2.api import create_listener as create_listener
from ._elbv2.api import create_load_balancer as create_load_balancer
from ._elbv2.api import create_rule as create_rule
from ._elbv2.api import delete_listener as delete_listener
from ._elbv2.api import delete_load_balancer as delete_load_balancer
from ._elbv2.api import delete_rule as delete_rule
from ._elbv2.api import describe_listeners as describe_listeners
from ._elbv2.api import describe_load_balancer_attributes as describe_load_balancer_attributes
from ._elbv2.api import describe_load_balancers as describe_load_balancers
from ._elbv2.api import describe_rules as describe_rules
from ._elbv2.api import describe_tags as describe_tags
from ._elbv2.api import describe_target_groups as describe_target_groups
from ._elbv2.api import modify_listener as modify_listener
from ._elbv2.api import modify_load_balancer_attributes as modify_load_balancer_attributes
from ._elbv2.api import modify_rule as modify_rule
from ._elbv2.api import remove_tags as remove_tags
from ._elbv2.api import set_ip_address_type as set_ip_address_type
from ._elbv2.api import set_rule_priorities as set_rule_priorities
from ._elbv2.api import set_security_groups as set_security_groups
from ._elbv2.api import set_subnets as set_subnets
from ._elbv2.common import AnsibleELBv2Error as AnsibleELBv2Error
from ._elbv2.common import ELBv2ErrorHandler as ELBv2ErrorHandler
from ._elbv2.common import ELBv2ListenerErrorHandler as ELBv2ListenerErrorHandler
from ._elbv2.common import ELBv2RuleErrorHandler as ELBv2RuleErrorHandler
from ._elbv2.common import ELBv2TargetGroupErrorHandler as ELBv2TargetGroupErrorHandler
from ._elbv2.listeners import ELBListener as ELBListener
from ._elbv2.listeners import ELBListeners as ELBListeners
from ._elbv2.listeners import _compare_listener as _compare_listener
from ._elbv2.listeners import _group_listeners as _group_listeners
from ._elbv2.listeners import _prepare_listeners as _prepare_listeners
from ._elbv2.listeners import validate_listener_https_requirements as validate_listener_https_requirements
from ._elbv2.rules import ELBListenerRule as ELBListenerRule
from ._elbv2.rules import ELBListenerRules as ELBListenerRules
from ._elbv2.rules import _check_rule_condition as _check_rule_condition
from ._elbv2.rules import _compare_rule as _compare_rule
from ._elbv2.rules import _compare_rule_actions as _compare_rule_actions
from ._elbv2.rules import _group_rules as _group_rules
from ._elbv2.transformations import normalize_application_load_balancer as normalize_application_load_balancer
from .elb_utils import get_elb

# pylint: enable=unused-import,useless-import-alias

# isort: split
# Not intended for general re-use / re-import
from ._elbv2 import waiters as _waiters
from .ec2 import get_ec2_security_group_ids_from_names
from .exceptions import AnsibleAWSError
from .modules import AnsibleAWSModule
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict


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


def get_min_healthy_targets_waiter(client: Any, min_count: int) -> Any:
    """
    Get a waiter that waits for a minimum number of healthy targets in a target group.

    Args:
        client: boto3 ELBv2 client
        min_count: Minimum number of targets in healthy state required

    Returns:
        Waiter instance
    """
    return _waiters.get_waiter_with_min_targets(client, min_count)


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

    def _attribute_differs(self, new_value: Any, current_key: str) -> bool:
        """
        Check if a new attribute value differs from the current ELB attribute.

        :param new_value: The new value to compare (None values return False)
        :param current_key: The key in self.elb_attributes to compare against
        :return: True if values differ, False if same or new_value is None
        """
        if new_value is None:
            return False

        current_value = self.elb_attributes[current_key]
        # Boolean values from module params need to be lowercased to match API format
        if isinstance(new_value, bool):
            return str(new_value).lower() != current_value
        return str(new_value) != current_value

    def _add_attribute_update(self, update_list: List[Dict[str, str]], attribute_key: str, new_value: Any) -> None:
        """
        Add an attribute update to the list if needed, converting value appropriately.

        :param update_list: List to append the update dict to
        :param attribute_key: AWS ELB attribute key (e.g., "access_logs.s3.enabled")
        :param new_value: The value to set
        """
        # Boolean values from module params need to be lowercased to match API format
        if isinstance(new_value, bool):
            value = str(new_value).lower()
        else:
            value = str(new_value) if not isinstance(new_value, str) else new_value
        update_list.append({"Key": attribute_key, "Value": value})


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

    def _build_elb_attributes_update_list(self) -> List[Dict[str, str]]:
        """
        Build list of ELB attributes that need updating.

        :return: List of attribute dicts with Key/Value pairs that differ from current state
        """
        update_attributes = []

        if self._attribute_differs(self.access_logs_enabled, "access_logs_s3_enabled"):
            self._add_attribute_update(update_attributes, "access_logs.s3.enabled", self.access_logs_enabled)

        if self._attribute_differs(self.access_logs_s3_bucket, "access_logs_s3_bucket"):
            self._add_attribute_update(update_attributes, "access_logs.s3.bucket", self.access_logs_s3_bucket)

        if self._attribute_differs(self.access_logs_s3_prefix, "access_logs_s3_prefix"):
            self._add_attribute_update(update_attributes, "access_logs.s3.prefix", self.access_logs_s3_prefix)

        if self._attribute_differs(self.deletion_protection, "deletion_protection_enabled"):
            self._add_attribute_update(update_attributes, "deletion_protection.enabled", self.deletion_protection)

        if self._attribute_differs(self.idle_timeout, "idle_timeout_timeout_seconds"):
            self._add_attribute_update(update_attributes, "idle_timeout.timeout_seconds", self.idle_timeout)

        if self._attribute_differs(self.http2, "routing_http2_enabled"):
            self._add_attribute_update(update_attributes, "routing.http2.enabled", self.http2)

        if self._attribute_differs(self.http_desync_mitigation_mode, "routing_http_desync_mitigation_mode"):
            self._add_attribute_update(
                update_attributes, "routing.http.desync_mitigation_mode", self.http_desync_mitigation_mode
            )

        if self._attribute_differs(
            self.http_drop_invalid_header_fields, "routing_http_drop_invalid_header_fields_enabled"
        ):
            self._add_attribute_update(
                update_attributes,
                "routing.http.drop_invalid_header_fields.enabled",
                self.http_drop_invalid_header_fields,
            )

        if self._attribute_differs(
            self.http_x_amzn_tls_version_and_cipher_suite,
            "routing_http_x_amzn_tls_version_and_cipher_suite_enabled",
        ):
            self._add_attribute_update(
                update_attributes,
                "routing.http.x_amzn_tls_version_and_cipher_suite.enabled",
                self.http_x_amzn_tls_version_and_cipher_suite,
            )

        if self._attribute_differs(self.http_xff_client_port, "routing_http_xff_client_port_enabled"):
            self._add_attribute_update(
                update_attributes, "routing.http.xff_client_port.enabled", self.http_xff_client_port
            )

        if self._attribute_differs(self.waf_fail_open, "waf_fail_open_enabled"):
            self._add_attribute_update(update_attributes, "waf.fail_open.enabled", self.waf_fail_open)

        return update_attributes

    def compare_elb_attributes(self) -> bool:
        """
        Compare user attributes with current ELB attributes
        :return: bool True if they match otherwise False
        """
        update_attributes = self._build_elb_attributes_update_list()
        return not update_attributes

    def modify_elb_attributes(self) -> None:
        """
        Update Application ELB attributes if required

        :return:
        """
        update_attributes = self._build_elb_attributes_update_list()

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

        if self._attribute_differs(self.cross_zone_load_balancing, "load_balancing_cross_zone_enabled"):
            self._add_attribute_update(
                update_attributes, "load_balancing.cross_zone.enabled", self.cross_zone_load_balancing
            )

        if self._attribute_differs(self.deletion_protection, "deletion_protection_enabled"):
            self._add_attribute_update(update_attributes, "deletion_protection.enabled", self.deletion_protection)

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

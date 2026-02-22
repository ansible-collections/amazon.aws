# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from .botocore import is_boto3_error_code
from .errors import AWSErrorHandler
from .exceptions import AnsibleAWSError
from .retries import AWSRetry


class AnsibleELBv2Error(AnsibleAWSError):
    pass


# Elastic Load Balancers V2
class ELBv2ErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("LoadBalancerNotFound")


@ELBv2ErrorHandler.common_error_handler("create load balancer")
@AWSRetry.jittered_backoff(retries=10)
def create_load_balancer(client, name: str, **params) -> List[Dict[str, Any]]:
    return client.create_load_balancer(Name=name, **params)["LoadBalancers"]


@ELBv2ErrorHandler.common_error_handler("set subnets")
@AWSRetry.jittered_backoff(retries=10)
def set_subnets(client, load_balancer_arn: str, **params) -> List[Dict[str, Any]]:
    return client.set_subnets(LoadBalancerArn=load_balancer_arn, **params)["AvailabilityZones"]


@ELBv2ErrorHandler.common_error_handler("set ip address type")
@AWSRetry.jittered_backoff(retries=10)
def set_ip_address_type(client, load_balancer_arn: str, ip_address_type: str) -> str:
    return client.set_ip_address_type(LoadBalancerArn=load_balancer_arn, IpAddressType=ip_address_type)["IpAddressType"]


@ELBv2ErrorHandler.common_error_handler("set security groups")
@AWSRetry.jittered_backoff(retries=10)
def set_security_groups(
    client,
    load_balancer_arn: str,
    security_groups: List[str],
    enforce_security_group_inbound_rules_on_private_link_traffic: Optional[str] = None,
) -> Dict[str, Union[str, List[str]]]:
    params = {}
    if enforce_security_group_inbound_rules_on_private_link_traffic:
        params[
            "EnforceSecurityGroupInboundRulesOnPrivateLinkTraffic"
        ] = enforce_security_group_inbound_rules_on_private_link_traffic
    return client.set_security_groups(LoadBalancerArn=load_balancer_arn, SecurityGroups=security_groups, **params)


@ELBv2ErrorHandler.common_error_handler("describe tags")
@AWSRetry.jittered_backoff(retries=10)
def describe_tags(client, resource_arns: List[str]) -> List[Dict[str, Any]]:
    return client.describe_tags(ResourceArns=resource_arns)["TagDescriptions"]


@ELBv2ErrorHandler.common_error_handler("remove tags")
@AWSRetry.jittered_backoff(retries=10)
def remove_tags(client, resource_arns: List[str], tag_keys: List[str]) -> bool:
    client.remove_tags(ResourceArns=resource_arns, TagKeys=tag_keys)
    return True


@ELBv2ErrorHandler.common_error_handler("add tags")
@AWSRetry.jittered_backoff(retries=10)
def add_tags(client, resource_arns: List[str], tags: List[Dict[str, str]]) -> bool:
    client.add_tags(ResourceArns=resource_arns, Tags=tags)
    return True


@ELBv2ErrorHandler.common_error_handler("describe load balancer attributes")
@AWSRetry.jittered_backoff()
def describe_load_balancer_attributes(client, load_balancer_arn: str) -> List[Dict[str, str]]:
    return client.describe_load_balancer_attributes(LoadBalancerArn=load_balancer_arn)["Attributes"]


@ELBv2ErrorHandler.deletion_error_handler("delete load balancer")
@AWSRetry.jittered_backoff()
def delete_load_balancer(client, load_balancer_arn: str) -> bool:
    client.delete_load_balancer(LoadBalancerArn=load_balancer_arn)
    return True


@ELBv2ErrorHandler.common_error_handler("modify load balancer attributes")
@AWSRetry.jittered_backoff(retries=10)
def modify_load_balancer_attributes(
    client, load_balancer_arn: str, attributes: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    return client.modify_load_balancer_attributes(LoadBalancerArn=load_balancer_arn, Attributes=attributes)[
        "Attributes"
    ]


@ELBv2ErrorHandler.list_error_handler("describe load balancers")
@AWSRetry.jittered_backoff()
def describe_load_balancers(
    client, load_balancer_arns: Optional[List[str]] = None, names: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    params = {}
    if load_balancer_arns:
        params["LoadBalancerArns"] = load_balancer_arns
    if names:
        params["Names"] = names
    load_balancer_paginator = client.get_paginator("describe_load_balancers")
    return (load_balancer_paginator.paginate(**params).build_full_result())["LoadBalancers"]


@ELBv2ErrorHandler.common_error_handler("describe listeners")
@AWSRetry.jittered_backoff(retries=10)
def describe_listeners(
    client, load_balancer_arn: Optional[str] = None, listener_arns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    load_balancer_paginator = client.get_paginator("describe_listeners")
    params = {}
    if load_balancer_arn:
        params["LoadBalancerArn"] = load_balancer_arn
    if listener_arns:
        params["ListenerArns"] = listener_arns
    return load_balancer_paginator.paginate(**params).build_full_result()["Listeners"]


@ELBv2ErrorHandler.common_error_handler("create listener")
@AWSRetry.jittered_backoff(retries=10)
def create_listener(client, load_balancer_arn: str, **params) -> List[Dict[str, str]]:
    return client.create_listener(LoadBalancerArn=load_balancer_arn, **params)["Listeners"]


@ELBv2ErrorHandler.common_error_handler("add listener certificates")
@AWSRetry.jittered_backoff(retries=10)
def add_listener_certificates(
    client, listener_arn: str, certificates: List[Dict[str, str]]
) -> List[Dict[str, Union[str, bool]]]:
    return client.add_listener_certificates(ListenerArn=listener_arn, Certificates=certificates)["Certificates"]


# Listeners
class ELBv2ListenerErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("ListenerNotFound")


@ELBv2ListenerErrorHandler.common_error_handler("modify listener")
@AWSRetry.jittered_backoff()
def modify_listener(client, listener_arn: str, **params) -> List[Dict[str, Any]]:
    return client.modify_listener(ListenerArn=listener_arn, **params)["Listeners"]


@ELBv2ListenerErrorHandler.common_error_handler("delete listener")
@AWSRetry.jittered_backoff()
def delete_listener(client, listener_arn: str) -> bool:
    client.delete_listener(ListenerArn=listener_arn)
    return True


@ELBv2ListenerErrorHandler.common_error_handler("create rule")
@AWSRetry.jittered_backoff()
def create_rule(
    client,
    listener_arn: str,
    conditions: List[Dict[str, Any]],
    priority: int,
    actions: List[Dict[str, Any]],
    tags: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    params = {}
    if tags:
        params["Tags"] = tags
    return client.create_rule(
        ListenerArn=listener_arn, Conditions=conditions, Priority=priority, Actions=actions, **params
    )["Rules"]


# Rules
class ELBv2RuleErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("RuleNotFound")


@ELBv2RuleErrorHandler.common_error_handler("describe rules")
@AWSRetry.jittered_backoff(retries=10)
def describe_rules(client, **params) -> List[Dict[str, Any]]:
    return client.describe_rules(**params)["Rules"]


@ELBv2RuleErrorHandler.common_error_handler("set rule priorities")
@AWSRetry.jittered_backoff()
def set_rule_priorities(client, rule_priorities: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    return client.set_rule_priorities(RulePriorities=rule_priorities)["Rules"]


@ELBv2RuleErrorHandler.deletion_error_handler("delete rule")
@AWSRetry.jittered_backoff()
def delete_rule(client, rule_arn: str) -> bool:
    client.delete_rule(RuleArn=rule_arn)
    return True


@ELBv2RuleErrorHandler.common_error_handler("modify rule")
@AWSRetry.jittered_backoff()
def modify_rule(client, rule_arn: str, **params) -> List[Dict[str, Any]]:
    return client.modify_rule(RuleArn=rule_arn, **params)["Rules"]


# Target Groups
class ELBv2TargetGroupErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("TargetGroupNotFound")


@ELBv2TargetGroupErrorHandler.common_error_handler("describe target groups")
@AWSRetry.jittered_backoff(retries=10)
def describe_target_groups(client, **params) -> List[Dict[str, Any]]:
    load_balancer_paginator = client.get_paginator("describe_target_groups")
    return load_balancer_paginator.paginate(**params).build_full_result()["TargetGroups"]


def get_elb(connection, module, elb_name):
    """
    Get an ELB based on name. If not found, return None.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param elb_name: Name of load balancer to get
    :return: boto3 ELB dict or None if not found
    """
    result = None
    try:
        load_balancers = describe_load_balancers(connection, names=[elb_name])
        if load_balancers:
            result = load_balancers[0]
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)
    return result


def get_elb_listener_rules(connection, module, listener_arn):
    """
    Get rules for a particular ELB listener using the listener ARN.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param listener_arn: ARN of the ELB listener
    :return: boto3 ELB rules list
    """

    try:
        return describe_rules(connection, ListenerArn=listener_arn)
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)


def convert_tg_name_to_arn(connection, module, tg_name):
    """
    Get ARN of a target group using the target group's name

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param tg_name: Name of the target group
    :return: target group ARN string
    """

    try:
        target_groups = describe_target_groups(connection, Names=[tg_name])
        if not target_groups:
            module.fail_json_aws(msg=f"Target group '{tg_name}' does not exist.")
        return target_groups[0]["TargetGroupArn"]
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)

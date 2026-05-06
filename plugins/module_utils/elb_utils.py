# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

from ._elbv2 import api as _elbv2_api
from ._elbv2.common import AnsibleELBv2Error
from ._elbv2.common import ELBv2ListenerErrorHandler
from ._elbv2.common import ELBv2RuleErrorHandler
from ._elbv2.common import ELBv2TargetGroupErrorHandler

if typing.TYPE_CHECKING:
    from typing import Any

    from .botocore import ClientType

# Re-export API wrapper functions
add_listener_certificates = _elbv2_api.add_listener_certificates
add_tags = _elbv2_api.add_tags
create_listener = _elbv2_api.create_listener
create_load_balancer = _elbv2_api.create_load_balancer
create_rule = _elbv2_api.create_rule
delete_listener = _elbv2_api.delete_listener
delete_load_balancer = _elbv2_api.delete_load_balancer
delete_rule = _elbv2_api.delete_rule
describe_listeners = _elbv2_api.describe_listeners
describe_load_balancer_attributes = _elbv2_api.describe_load_balancer_attributes
describe_load_balancers = _elbv2_api.describe_load_balancers
describe_rules = _elbv2_api.describe_rules
describe_tags = _elbv2_api.describe_tags
describe_target_groups = _elbv2_api.describe_target_groups
modify_listener = _elbv2_api.modify_listener
modify_load_balancer_attributes = _elbv2_api.modify_load_balancer_attributes
modify_rule = _elbv2_api.modify_rule
remove_tags = _elbv2_api.remove_tags
set_ip_address_type = _elbv2_api.set_ip_address_type
set_rule_priorities = _elbv2_api.set_rule_priorities
set_security_groups = _elbv2_api.set_security_groups
set_subnets = _elbv2_api.set_subnets


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



# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Backward compatibility helpers for ELBv2 modules.

This module provides thin wrappers around _elbv2.api functions that handle
fail_json_aws translation. New code should prefer importing from _elbv2.api
or elbv2 and handling exceptions directly.
"""

from __future__ import annotations

import typing

from ._elbv2 import api as _elbv2_api
from ._elbv2 import common as _elbv2_common

# Re-export for backward compatibility
AnsibleELBv2Error = _elbv2_common.AnsibleELBv2Error
ELBv2ListenerErrorHandler = _elbv2_common.ELBv2ListenerErrorHandler
ELBv2RuleErrorHandler = _elbv2_common.ELBv2RuleErrorHandler
ELBv2TargetGroupErrorHandler = _elbv2_common.ELBv2TargetGroupErrorHandler

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional

    from .botocore import ClientType
    from .modules import AnsibleAWSModule

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


# Thin fail_json wrappers for backward compatibility
# New code should import from _elbv2.api and handle exceptions directly


def get_elb(connection: ClientType, module: AnsibleAWSModule, elb_name: str) -> Optional[Dict[str, Any]]:
    """
    Get an ELB based on name. If not found, return None.

    Note: This is a convenience wrapper that calls fail_json_aws on errors.
    New code should use _elbv2.api.get_load_balancer_by_name() and handle
    exceptions directly.

    Args:
        connection: AWS boto3 elbv2 connection
        module: Ansible module
        elb_name: Name of load balancer to get

    Returns:
        boto3 ELB dict or None if not found
    """
    try:
        return _elbv2_api.get_load_balancer_by_name(connection, elb_name)
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)


def get_elb_listener_rules(connection: ClientType, module: AnsibleAWSModule, listener_arn: str) -> List[Dict[str, Any]]:
    """
    Get rules for a particular ELB listener using the listener ARN.

    Note: This is a convenience wrapper that calls fail_json_aws on errors.
    New code should use _elbv2.api.get_listener_rules() and handle
    exceptions directly.

    Args:
        connection: AWS boto3 elbv2 connection
        module: Ansible module
        listener_arn: ARN of the ELB listener

    Returns:
        boto3 ELB rules list
    """
    try:
        return _elbv2_api.get_listener_rules(connection, listener_arn)
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)


def convert_tg_name_to_arn(connection: ClientType, module: AnsibleAWSModule, tg_name: str) -> str:
    """
    Get ARN of a target group using the target group's name.

    Note: This is a convenience wrapper that calls fail_json_aws on errors.
    New code should use _elbv2.api.get_target_group_arn_by_name() and handle
    exceptions directly.

    Args:
        connection: AWS boto3 elbv2 connection
        module: Ansible module
        tg_name: Name of the target group

    Returns:
        Target group ARN string
    """
    try:
        return _elbv2_api.get_target_group_arn_by_name(connection, tg_name)
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)

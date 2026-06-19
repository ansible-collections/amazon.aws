# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Backwards-compatibility helpers for ELBv2 modules.

This module provides re-exports from _elbv2.api and thin wrappers that handle
fail_json_aws translation. New code should prefer importing from _elbv2.api
or elbv2 and handling exceptions directly.

See the developer guidelines for details:
https://ansible-collections.github.io/amazon.aws/branch/main/dev_guidelines.html
"""

from __future__ import annotations

import typing

# Re-export for backward compatibility from public interface
# pylint: disable=unused-import,useless-import-alias
from .elbv2 import AnsibleELBv2Error as AnsibleELBv2Error
from .elbv2 import ELBv2ListenerErrorHandler as ELBv2ListenerErrorHandler
from .elbv2 import ELBv2RuleErrorHandler as ELBv2RuleErrorHandler
from .elbv2 import ELBv2TargetGroupErrorHandler as ELBv2TargetGroupErrorHandler
from .elbv2 import add_listener_certificates as add_listener_certificates
from .elbv2 import add_tags as add_tags
from .elbv2 import create_listener as create_listener
from .elbv2 import create_load_balancer as create_load_balancer
from .elbv2 import create_rule as create_rule
from .elbv2 import delete_listener as delete_listener
from .elbv2 import delete_load_balancer as delete_load_balancer
from .elbv2 import delete_rule as delete_rule
from .elbv2 import describe_listeners as describe_listeners
from .elbv2 import describe_load_balancer_attributes as describe_load_balancer_attributes
from .elbv2 import describe_load_balancers as describe_load_balancers
from .elbv2 import describe_rules as describe_rules
from .elbv2 import describe_tags as describe_tags
from .elbv2 import describe_target_groups as describe_target_groups
from .elbv2 import modify_listener as modify_listener
from .elbv2 import modify_load_balancer_attributes as modify_load_balancer_attributes
from .elbv2 import modify_rule as modify_rule
from .elbv2 import remove_tags as remove_tags
from .elbv2 import set_ip_address_type as set_ip_address_type
from .elbv2 import set_rule_priorities as set_rule_priorities
from .elbv2 import set_security_groups as set_security_groups
from .elbv2 import set_subnets as set_subnets

# pylint: enable=unused-import,useless-import-alias

# isort: split
# Used by wrapper functions below
from .elbv2 import get_listener_rules as _get_listener_rules
from .elbv2 import get_load_balancer_by_name as _get_load_balancer_by_name
from .elbv2 import get_target_group_arn_by_name as _get_target_group_arn_by_name

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional

    from .botocore import ClientType
    from .modules import AnsibleAWSModule


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
        return _get_load_balancer_by_name(connection, elb_name)
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
        return _get_listener_rules(connection, listener_arn)
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
        return _get_target_group_arn_by_name(connection, tg_name)
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e)

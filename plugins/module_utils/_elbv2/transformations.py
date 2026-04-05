# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import List

    from ..transformation import AnsibleAWSResource
    from ..transformation import AnsibleAWSResourceList
    from ..transformation import BotoResource
    from ..transformation import BotoResourceList

from ..transformation import boto3_resource_list_to_ansible_dict
from ..transformation import boto3_resource_to_ansible_dict


def _normalize_listener_rules(rules: BotoResourceList) -> AnsibleAWSResourceList:
    """
    Normalize and sort ELB listener rules by priority.

    Converts listener rules from the CamelCase boto3 format to the snake_case Ansible format
    and sorts them numerically by priority, with the "default" rule appearing last.

    Parameters:
        rules (list): List of listener rules from boto3

    Returns:
        List of rules in Ansible format, sorted by priority
    """
    if not rules:
        return rules

    # First sort the rules by Priority (while still in CamelCase)
    def sort_key(rule):
        priority = rule.get("Priority", "default")
        if priority == "default":
            # Put default rule last by using a very large number
            return float("inf")
        try:
            return int(priority)
        except (ValueError, TypeError):
            # Fallback for unexpected priority values
            return float("inf")

    sorted_rules = sorted(rules, key=sort_key)

    # Convert to Ansible dict format (force_tags=False to prevent automatic tags field)
    return boto3_resource_list_to_ansible_dict(sorted_rules, force_tags=False)


def _normalize_listeners(listeners: BotoResourceList) -> AnsibleAWSResourceList:
    """
    Normalize ELB listeners.

    Converts listeners from boto3 format to Ansible format, applying rule sorting.

    Parameters:
        listeners (list): List of listeners from boto3

    Returns:
        List of listeners in Ansible format with sorted rules
    """
    if not listeners:
        return listeners

    # Transform each listener, applying nested transforms to Rules (force_tags=False to prevent automatic tags field)
    transforms = {"Rules": _normalize_listener_rules}
    return [boto3_resource_to_ansible_dict(listener, nested_transforms=transforms, force_tags=False) for listener in listeners]


def normalize_application_load_balancer(alb: BotoResource) -> AnsibleAWSResource:
    """
    Normalize an Application Load Balancer from boto3 format to Ansible format.

    Handles conversion of the ALB and its nested listeners and rules. Listener rules
    are sorted by priority with the "default" rule appearing last.

    Parameters:
        alb (dict): Application Load Balancer dict in boto3 format

    Returns:
        Normalized ALB dict in Ansible format
    """
    if not alb:
        return alb

    # Transform the ALB, applying nested transforms to Listeners
    transforms = {"Listeners": _normalize_listeners}
    return boto3_resource_to_ansible_dict(alb, nested_transforms=transforms)

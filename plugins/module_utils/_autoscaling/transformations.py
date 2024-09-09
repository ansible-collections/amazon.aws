# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Optional

    from ..transformation import AnsibleAWSResource
    from ..transformation import AnsibleAWSResourceList
    from ..transformation import BotoResource
    from ..transformation import BotoResourceList

from ..transformation import boto3_resource_list_to_ansible_dict
from ..transformation import boto3_resource_to_ansible_dict


def _inject_asg_name(
    instance: BotoResource,
    group_name: Optional[str] = None,
) -> BotoResource:
    if not group_name:
        return instance
    if "AutoScalingGroupName" in instance:
        return instance
    instance["AutoScalingGroupName"] = group_name
    return instance


def normalize_autoscaling_instance(
    instance: BotoResource,
    group_name: Optional[str] = None,
) -> AnsibleAWSResource:
    """Converts an AutoScaling Instance from the CamelCase boto3 format to the snake_case Ansible format.

    Also handles inconsistencies in the output between describe_autoscaling_group() and describe_autoscaling_instances().
    """
    if not instance:
        return instance

    # describe_autoscaling_group doesn't add AutoScalingGroupName
    instance = _inject_asg_name(instance, group_name)

    try:
        # describe_autoscaling_group and describe_autoscaling_instances aren't consistent
        instance["HealthStatus"] = instance["HealthStatus"].upper()
    except KeyError:
        pass

    return boto3_resource_to_ansible_dict(instance, force_tags=False)


def normalize_autoscaling_instances(
    autoscaling_instances: BotoResourceList,
    group_name: Optional[str] = None,
) -> AnsibleAWSResourceList:
    """Converts a list of AutoScaling Instances from the CamelCase boto3 format to the snake_case Ansible format"""
    if not autoscaling_instances:
        return autoscaling_instances
    autoscaling_instances = [normalize_autoscaling_instance(i, group_name) for i in autoscaling_instances]
    return sorted(autoscaling_instances, key=lambda d: d.get("instance_id", None))


def normalize_autoscaling_groups(autoscaling_groups: BotoResourceList) -> AnsibleAWSResourceList:
    """Converts a list of AutoScaling Groups from the CamelCase boto3 format to the snake_case Ansible format"""
    autoscaling_groups = boto3_resource_list_to_ansible_dict(autoscaling_groups)
    return sorted(autoscaling_groups, key=lambda d: d.get("auto_scaling_group_name", None))

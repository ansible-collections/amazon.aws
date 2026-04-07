# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Any
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


def _build_instance_facts(instance: dict[str, Any]) -> dict[str, Any]:
    """
    Build instance facts dictionary from ASG instance data.

    Args:
        instance: Instance data from ASG (CamelCase)

    Returns:
        dict: Instance facts including health, lifecycle, and launch spec (CamelCase)
    """
    facts = {
        "health_status": instance["HealthStatus"],
        "lifecycle_state": instance["LifecycleState"],
    }

    if "LaunchConfigurationName" in instance:
        facts["launch_config_name"] = instance["LaunchConfigurationName"]
    elif "LaunchTemplate" in instance:
        facts["launch_template"] = instance["LaunchTemplate"]

    return facts


def _update_instance_counts(instance: dict[str, Any], counts: dict[str, int]) -> None:
    """
    Update instance count statistics based on instance state.

    Args:
        instance: Instance data from ASG (CamelCase)
        counts: Dictionary of count statistics to update in-place
    """
    health_status = instance["HealthStatus"]
    lifecycle_state = instance["LifecycleState"]

    # Count viable instances (healthy and in service)
    if health_status == "Healthy" and lifecycle_state == "InService":
        counts["viable_instances"] += 1

    # Count by health status
    if health_status == "Healthy":
        counts["healthy_instances"] += 1
    else:
        counts["unhealthy_instances"] += 1

    # Count by lifecycle state
    if lifecycle_state == "InService":
        counts["in_service_instances"] += 1
    elif lifecycle_state == "Terminating":
        counts["terminating_instances"] += 1
    elif lifecycle_state == "Pending":
        counts["pending_instances"] += 1


def _process_asg_instances(
    instances: list[dict[str, Any]],
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, int]]:
    """
    Process ASG instances to extract IDs, facts, and count statistics.

    Pure transformation function - no API calls, fully testable.

    Args:
        instances: List of instance dicts from ASG Instances field (CamelCase)

    Returns:
        tuple of (instance_ids, instance_facts, count_stats):
            - instance_ids: List of instance IDs
            - instance_facts: Dict mapping instance ID to facts
            - count_stats: Dict of instance count statistics
    """
    count_stats = {
        "healthy_instances": 0,
        "in_service_instances": 0,
        "unhealthy_instances": 0,
        "pending_instances": 0,
        "viable_instances": 0,
        "terminating_instances": 0,
    }

    if not instances:
        return [], {}, count_stats

    instance_ids = [i["InstanceId"] for i in instances]
    instance_facts = {}

    for instance in instances:
        instance_id = instance["InstanceId"]
        instance_facts[instance_id] = _build_instance_facts(instance)
        _update_instance_counts(instance, count_stats)

    return instance_ids, instance_facts, count_stats


def _extract_mixed_instances_policy_instance_types(mixed_instances_policy: dict[str, Any] | None) -> list[str]:
    """
    Extract instance types from MixedInstancesPolicy.

    Pure transformation function - no API calls, fully testable.

    Args:
        mixed_instances_policy: MixedInstancesPolicy dict from ASG (CamelCase format)

    Returns:
        list: Instance types from launch template overrides, or empty list
    """
    if not mixed_instances_policy:
        return []

    overrides = mixed_instances_policy.get("LaunchTemplate", {}).get("Overrides", [])
    return [override["InstanceType"] for override in overrides]


def _sort_metrics(metrics: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    """
    Sort metrics collection by metric name.

    Pure transformation function - no API calls, fully testable.

    Args:
        metrics: List of metric dicts (after snake_case conversion), or None

    Returns:
        Sorted list of metrics, or None if input was None
    """
    if not metrics:
        return metrics

    # After boto3_resource_to_ansible_dict, the key is lowercase "metric"
    return sorted(metrics, key=lambda x: x.get("metric", ""))


def transform_autoscaling_group(autoscaling_group: dict[str, Any], instances_as_ids: bool = True) -> dict[str, Any]:
    """
    Pure transformation function to convert boto3 ASG to Ansible format.

    Transforms AutoScaling Group data from CamelCase to snake_case and adds
    computed properties like instance counts and instance facts.

    Pure transformation function - no API calls, fully testable.

    Args:
        autoscaling_group: Boto3 ASG dict (CamelCase), optionally enriched with:
            - TargetGroupNames: list of target group names (if resolved)
            - LifecycleHooks: list of lifecycle hooks (if fetched)
        instances_as_ids: If True, set instances to list of IDs (autoscaling_group behavior).
                         If False, set instances to list of full details (autoscaling_group_info behavior).

    Returns:
        dict: Ansible format (snake_case) with computed fields including:
            - instances: list of instance IDs (if instances_as_ids=True) or list of dicts (if False)
            - instance_ids: list of instance IDs (always present)
            - instance_details: list of full instance dicts (always present)
            - instance_facts: dict mapping instance ID to facts
            - viable_instances, healthy_instances, unhealthy_instances, etc.: count statistics
            - mixed_instances_policy: list of instance types (if MixedInstancesPolicy present)
            - metrics_collection: sorted list of metrics
            - launch_config_name: for compatibility (if LaunchConfigurationName present)
    """
    # Use boto3_resource_to_ansible_dict for automatic CamelCase to snake_case conversion
    # transform_tags=False because ASG tags are already in dict format with Key/Value
    properties = boto3_resource_to_ansible_dict(autoscaling_group, transform_tags=False)

    # Process instances FIRST (before normalize which modifies in place)
    # This needs the original boto3 format
    instance_ids, instance_facts, count_stats = _process_asg_instances(autoscaling_group.get("Instances", []))

    # Normalize instance details (full instance dicts in snake_case)
    # Note: normalize_autoscaling_instances modifies instances in place, so call this AFTER _process_asg_instances
    instance_details = normalize_autoscaling_instances(
        autoscaling_group.get("Instances", []),
        group_name=autoscaling_group.get("AutoScalingGroupName"),
    )

    # Store both formats
    properties["instance_ids"] = instance_ids
    properties["instance_details"] = instance_details
    properties["instance_facts"] = instance_facts
    properties.update(count_stats)

    # Set instances based on flag
    if instances_as_ids:
        properties["instances"] = instance_ids
    else:
        properties["instances"] = instance_details

    # Extract mixed instances policy instance types - pure transformation (testable)
    properties["mixed_instances_policy"] = _extract_mixed_instances_policy_instance_types(
        autoscaling_group.get("MixedInstancesPolicy")
    )

    # Sort metrics - pure transformation (testable)
    # boto3 returns EnabledMetrics, boto3_resource_to_ansible_dict transforms it to enabled_metrics
    # We sort it and store as metrics_collection for compatibility
    properties["metrics_collection"] = _sort_metrics(properties.get("enabled_metrics"))

    # Add launch_config_name for compatibility with autoscaling_group module
    if "launch_configuration_name" in properties:
        properties["launch_config_name"] = properties["launch_configuration_name"]

    return properties

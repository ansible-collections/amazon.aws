#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: autoscaling_group
version_added: 5.0.0
short_description: Create or delete AWS AutoScaling Groups (ASGs)
description:
  - Can create or delete AWS AutoScaling Groups.
  - Can be used with the M(community.aws.autoscaling_launch_config) module to manage Launch Configurations.
  - Prior to release 5.0.0 this module was called M(community.aws.ec2_asg).
    The usage did not change.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - "Gareth Rushgrove (@garethr)"
options:
  state:
    description:
      - Register or deregister the instance.
    choices: ['present', 'absent']
    default: present
    type: str
  name:
    description:
      - Unique name for group to be created or deleted.
    aliases: ['group_name']
    required: true
    type: str
  load_balancers:
    description:
      - List of ELB names to use for the group. Use for classic load balancers.
    type: list
    elements: str
  target_group_arns:
    description:
      - List of target group ARNs to use for the group. Use for application load balancers.
    type: list
    elements: str
  availability_zones:
    description:
      - List of availability zone names in which to create the group.
      - Defaults to all the availability zones in the region if O(vpc_zone_identifier) is not set.
    type: list
    elements: str
  launch_config_name:
    description:
      - Name of the Launch configuration to use for the group. See the M(community.aws.autoscaling_launch_config) module for managing these.
      - Exactly one of O(launch_config_name) or O(launch_template) must be provided when creating a new AutoScaling Group.
      - B(Note) Amazon has deprecated support for AutoScaling Launch Configurations in favour of EC2 Launch Templates.  See
        U(https://docs.aws.amazon.com/autoscaling/ec2/userguide/launch-configurations.html) for more information
    type: str
  launch_template:
    description:
      - Dictionary describing the Launch Template to use.
      - Exactly one of O(launch_config_name) or O(launch_template) must be provided when creating a new AutoScaling Group.
    suboptions:
      version:
        description:
          - The version number of the launch template to use.
          - Defaults to latest version if not provided.
        type: str
      launch_template_name:
        description:
          - The name of the launch template. Only one of O(launch_template.launch_template_name) or O(launch_template.launch_template_id) is required.
        type: str
      launch_template_id:
        description:
          - The id of the launch template. Only one of O(launch_template.launch_template_name) or O(launch_template.launch_template_id) is required.
        type: str
    type: dict
  min_size:
    description:
      - Minimum number of instances in group, if unspecified then the current group value will be used.
    type: int
  max_size:
    description:
      - Maximum number of instances in group, if unspecified then the current group value will be used.
    type: int
  max_instance_lifetime:
    description:
      - The maximum amount of time, in seconds, that an instance can be in service.
      - Maximum instance lifetime must be equal to V(0), between V(604800) and V(31536000) seconds (inclusive), or not specified.
      - Value of V(0) removes lifetime restriction.
    type: int
  mixed_instances_policy:
    description:
      - A mixed instance policy to use for the ASG.
      - Only used when the ASG is configured to use a Launch Template (O(launch_template)).
      - 'See also U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-autoscaling-autoscalinggroup-mixedinstancespolicy.html)'
    required: false
    suboptions:
      instance_types:
        description:
          - A list of instance types.
        type: list
        elements: str
        required: false
      instances_distribution:
        description:
          - >-
            Specifies the distribution of On-Demand Instances and Spot Instances, the maximum price
            to pay for Spot Instances, and how the Auto Scaling group allocates instance types
            to fulfill On-Demand and Spot capacity.
          - 'See also U(https://docs.aws.amazon.com/autoscaling/ec2/APIReference/API_InstancesDistribution.html)'
        required: false
        type: dict
        version_added: 1.5.0
        version_added_collection: community.aws
        suboptions:
          on_demand_allocation_strategy:
            description:
              - Indicates how to allocate instance types to fulfill On-Demand capacity.
            type: str
            required: false
            version_added: 1.5.0
            version_added_collection: community.aws
          on_demand_base_capacity:
            description:
              - >-
                The minimum amount of the Auto Scaling group's capacity that must be fulfilled by On-Demand
                Instances. This base portion is provisioned first as your group scales.
              - >-
                Default if not set is V(0). If you leave it set to V(0), On-Demand Instances are launched as a
                percentage of the Auto Scaling group's desired capacity, per the
                O(mixed_instances_policy.instances_distribution.on_demand_percentage_above_base_capacity) setting.
            type: int
            required: false
            version_added: 1.5.0
            version_added_collection: community.aws
          on_demand_percentage_above_base_capacity:
            description:
              - Controls the percentages of On-Demand Instances and Spot Instances for your additional capacity beyond
                O(mixed_instances_policy.instances_distribution.on_demand_base_capacity).
              - Default if not set is V(100). If you leave it set to V(100), the percentages are 100% for On-Demand Instances and 0% for Spot Instances.
              - 'Valid range: V(0) to V(100).'
            type: int
            required: false
            version_added: 1.5.0
            version_added_collection: community.aws
          spot_allocation_strategy:
            description:
              - Indicates how to allocate instances across Spot Instance pools.
            type: str
            required: false
            version_added: 1.5.0
            version_added_collection: community.aws
          spot_instance_pools:
            description:
              - >-
                The number of Spot Instance pools across which to allocate your Spot Instances. The Spot pools are determined from
                the different instance types in the Overrides array of LaunchTemplate. Default if not set is V(2).
              - Used only when the Spot allocation strategy is lowest-price.
              - 'Valid Range: Minimum value of V(1). Maximum value of V(20).'
            type: int
            required: false
            version_added: 1.5.0
            version_added_collection: community.aws
          spot_max_price:
            description:
              - The maximum price per unit hour that you are willing to pay for a Spot Instance.
              - If you leave the value of this parameter blank (which is the default), the maximum Spot price is set at the On-Demand price.
              - To remove a value that you previously set, include the parameter but leave the value blank.
            type: str
            required: false
            version_added: 1.5.0
            version_added_collection: community.aws
    type: dict
  placement_group:
    description:
      - Physical location of your cluster placement group created in Amazon EC2.
    type: str
  desired_capacity:
    description:
      - Desired number of instances in group, if unspecified then the current group value will be used.
    type: int
  replace_all_instances:
    description:
      - Support for the O(replace_all_instances) parameter has been deprecated and will be removed
        in release 14.0.0.
        The M(amazon.aws.autoscaling_instance_refresh) module can be used to perform an automated
        replacement of instances.
      - In a rolling fashion, replace all instances that used the old launch configuration with one from the new launch configuration.
        It increases the ASG size by O(replace_batch_size), waits for the new instances to be up and running.
        After that, it terminates a batch of old instances, waits for the replacements, and repeats, until all old instances are replaced.
        Once that's done the ASG size is reduced back to the expected size.
    default: false
    type: bool
  replace_batch_size:
    description:
      - Support for the O(replace_all_instances) and O(replace_batch_size) parameters has been
        deprecated and will be removed in release 14.0.0.
        The M(amazon.aws.autoscaling_instance_refresh) module can be used to perform an automated
        replacement of instances.
      - Number of instances you'd like to replace at a time.  Used with O(replace_all_instances).
    required: false
    default: 1
    type: int
  replace_instances:
    description:
      - Support for the O(replace_instances) parameter has been deprecated and will be removed in
        release 14.0.0.
        The M(amazon.aws.autoscaling_instance) module can be used to terminate instances attached
        to an AutoScaling Group.
      - List of instance ids belonging to the named AutoScalingGroup that you would like to terminate and be replaced with instances
        matching the current launch configuration.
    type: list
    elements: str
    default: []
  detach_instances:
    description:
      - Support for the O(detach_instances) parameter has been deprecated and will be removed in
        release 14.0.0.
        The M(amazon.aws.autoscaling_instance) module can be used to attach instances to and detach
        and detach instances from an AutoScaling Group.
      - Removes one or more instances from the specified AutoScalingGroup.
      - If O(decrement_desired_capacity) flag is not set, new instance(s) are launched to replace the detached instance(s).
      - If a Classic Load Balancer is attached to the AutoScalingGroup, the instances are also deregistered from the load balancer.
      - If there are target groups attached to the AutoScalingGroup, the instances are also deregistered from the target groups.
    type: list
    elements: str
    default: []
    version_added: 3.2.0
    version_added_collection: community.aws
  decrement_desired_capacity:
    description:
      - Support for the O(detach_instances) and O(decrement_desired_capacity) parameters has been
        deprecated and will be removed in release 14.0.0.
        The M(amazon.aws.autoscaling_instance) module can be used to attach instances to and detach
        and detach instances from an AutoScaling Group.
      - Indicates whether the AutoScalingGroup decrements the desired capacity value by the number of instances detached.
    default: false
    type: bool
    version_added: 3.2.0
    version_added_collection: community.aws
  lc_check:
    description:
      - Support for the O(detach_instances) and O(lc_check) parameters has been deprecated and will
        be removed in release 14.0.0.
        The M(amazon.aws.autoscaling_instance) module can be used to attach instances to and detach
        and detach instances from an AutoScaling Group.
      - Check to make sure instances that are being replaced with O(replace_instances) do not already have the current launch config.
    default: true
    type: bool
  lt_check:
    description:
      - Support for the O(detach_instances) and O(lt_check) parameters has been deprecated and will
        be removed in release 14.0.0.
        The M(amazon.aws.autoscaling_instance) module can be used to attach instances to and detach
        and detach instances from an AutoScaling Group.
      - Check to make sure instances that are being replaced with O(replace_instances) do not already have the current
        O(launch_template) or O(launch_template) O(launch_template.version).
    default: true
    type: bool
  vpc_zone_identifier:
    description:
      - List of VPC subnets to use
    type: list
    elements: str
  protected_from_scale_in:
    description:
      - If V(true), new instances will have scale-in protection enabled when added to the AutoScaling Group.
      - Defaults to V(false) when creating a new AutoScaling Group.
    type: bool
    version_added: 11.1.0
  tags:
    description:
      - A list of tags to add to the Auto Scale Group.
      - Optional key is V(propagate_at_launch), which defaults to V(true).
      - When V(propagate_at_launch) is V(true) the tags will be propagated to the Instances created.
    type: list
    elements: dict
    default: []
  purge_tags:
    description:
      - If V(true), existing tags will be purged from the resource to match exactly what is defined by O(tags) parameter.
      - If the O(tags) parameter is not set then tags will not be modified.
    default: false
    type: bool
    version_added: 3.2.0
    version_added_collection: community.aws
  health_check_period:
    description:
      - Length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health.
    required: false
    default: 300
    type: int
  health_check_type:
    description:
      - The service you want the health status from, Amazon EC2 or Elastic Load Balancer.
    required: false
    default: EC2
    choices: ['EC2', 'ELB']
    type: str
  default_cooldown:
    description:
      - The number of seconds after a scaling activity completes before another can begin.
    default: 300
    type: int
  wait_timeout:
    description:
      - How long to wait for instances to become viable when replaced.  If you experience the error "Waited too long for ELB instances to be healthy",
        try increasing this value.
    default: 300
    type: int
  wait_for_instances:
    description:
      - Wait for the ASG instances to be in a ready state before exiting.  If instances are behind an ELB, it will wait until the ELB determines all
        instances have a lifecycle_state of  "InService" and  a health_status of "Healthy".
    default: true
    type: bool
  termination_policies:
    description:
        - An ordered list of criteria used for selecting instances to be removed from the Auto Scaling group when reducing capacity.
        - Using O(termination_policies=Default) when modifying an existing AutoScalingGroup will result in the existing policy being retained
          instead of changed to V(Default).
        - 'Valid values include: V(Default), V(OldestInstance), V(NewestInstance), V(OldestLaunchConfiguration), V(ClosestToNextInstanceHour)'
        - 'Full documentation of valid values can be found in the AWS documentation:'
        - 'U(https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html#custom-termination-policy)'
    default: Default
    type: list
    elements: str
  notification_topic:
    description:
      - A SNS topic ARN to send auto scaling notifications to.
    type: str
  notification_types:
    description:
      - A list of auto scaling events to trigger notifications on.
    default:
      - 'autoscaling:EC2_INSTANCE_LAUNCH'
      - 'autoscaling:EC2_INSTANCE_LAUNCH_ERROR'
      - 'autoscaling:EC2_INSTANCE_TERMINATE'
      - 'autoscaling:EC2_INSTANCE_TERMINATE_ERROR'
    required: false
    type: list
    elements: str
  suspend_processes:
    description:
      - A list of scaling processes to suspend.
      - 'Valid values include:'
      - V(Launch), V(Terminate), V(HealthCheck), V(ReplaceUnhealthy), V(AZRebalance), V(AlarmNotification), V(ScheduledActions), V(AddToLoadBalancer)
      - 'Full documentation of valid values can be found in the AWS documentation:'
      - 'U(https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html)'
    default: []
    type: list
    elements: str
  metrics_collection:
    description:
      - Enable ASG metrics collection.
    type: bool
    default: false
  metrics_granularity:
    description:
      - When O(metrics_collection=true) this will determine the granularity of metrics collected by CloudWatch.
    default: "1Minute"
    type: str
  metrics_list:
    description:
      - List of autoscaling metrics to collect when O(metrics_collection=true).
    default:
      - 'GroupMinSize'
      - 'GroupMaxSize'
      - 'GroupDesiredCapacity'
      - 'GroupInServiceInstances'
      - 'GroupPendingInstances'
      - 'GroupStandbyInstances'
      - 'GroupTerminatingInstances'
      - 'GroupTotalInstances'
    type: list
    elements: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Basic configuration with Launch Template

- name: Create an autoscaling group using launch template
  amazon.aws.autoscaling_group:
    name: example_asg
    load_balancers: ['lb1', 'lb2']
    availability_zones: ['eu-west-1a', 'eu-west-1b']
    launch_template:
      launch_template_name: 'template-1'
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: ['subnet-abcd1234', 'subnet-1a2b3c4d']
    tags:
      - environment: production
        propagate_at_launch: false

# Rolling ASG Updates

# Below is an example of how to assign a new launch template to an ASG and replace old instances.
# By setting max_healthy_percentage to a value over 100 the old rolling-replacement behaviour of
# scaling up before scaling in can be maintained.

- name: Update autoscaling group with new template - instances are not replaced
  amazon.aws.autoscaling_group:
    name: example_asg
    launch_template:
      launch_template_name: template-2
    health_check_period: 60
    health_check_type: ELB
    min_size: 2
    max_size: 13
    desired_capacity: 6
    region: us-east-1

- name: Replace 2 instances based on EC2 Instance ID by marking them for termination
  amazon.aws.autoscaling_instance:
    group_name: example_asg
    state: terminated
    instance_ids:
      - i-b345231
      - i-24c2931
    decrement_desired_capacity: false
    wait: true

- name: Trigger rolling replacement of all instances that do not match the current configuration.
  amazon.aws.autoscaling_instance_refresh:
    group_name: example_asg
    state: started
    strategy: Rolling
    preferences:
      skip_matching: true
      max_healthy_percentage: 125  # scale out before terminating instances during replacement

# Basic Configuration with Launch Template

- name: Example autoscaling group creation with a launch template
  amazon.aws.autoscaling_group:
    name: example_with_template
    load_balancers: ['lb1', 'lb2']
    availability_zones: ['eu-west-1a', 'eu-west-1b']
    launch_template:
      version: '1'
      launch_template_name: 'lt-example'
      launch_template_id: 'lt-123456'
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: ['subnet-abcd1234', 'subnet-1a2b3c4d']
    tags:
      - environment: production
        propagate_at_launch: false

# Basic Configuration with Launch Template using mixed instance policy

- name: Example autoscaling group creation with a mixed instance policy
  amazon.aws.autoscaling_group:
    name: example_with_policy
    load_balancers: ['lb1', 'lb2']
    availability_zones: ['eu-west-1a', 'eu-west-1b']
    launch_template:
      version: '1'
      launch_template_name: 'lt-example'
      launch_template_id: 'lt-123456'
    mixed_instances_policy:
      instance_types:
        - t3a.large
        - t3.large
        - t2.large
      instances_distribution:
        on_demand_percentage_above_base_capacity: 0
        spot_allocation_strategy: capacity-optimized
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: ['subnet-abcd1234', 'subnet-1a2b3c4d']
    tags:
      - environment: production
        propagate_at_launch: false
"""

RETURN = r"""
---
auto_scaling_group_name:
    description: The unique name of the auto scaling group
    returned: success
    type: str
    sample: "myasg"
auto_scaling_group_arn:
    description: The unique ARN of the autoscaling group
    returned: success
    type: str
    sample: "arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:6a09ad6d-eeee-1234-b987-ee123ced01ad:autoScalingGroupName/myasg"
availability_zones:
    description: The availability zones for the auto scaling group
    returned: success
    type: list
    sample: [
        "us-east-1d"
    ]
created_time:
    description: Timestamp of create time of the auto scaling group
    returned: success
    type: str
    sample: "2017-11-08T14:41:48.272000+00:00"
default_cooldown:
    description: The default cooldown time in seconds.
    returned: success
    type: int
    sample: 300
desired_capacity:
    description: The number of EC2 instances that should be running in this group.
    returned: success
    type: int
    sample: 3
healthcheck_period:
    description: Length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health.
    returned: success
    type: int
    sample: 30
healthcheck_type:
    description: The service you want the health status from, one of "EC2" or "ELB".
    returned: success
    type: str
    sample: "ELB"
healthy_instances:
    description: Number of instances in a healthy state
    returned: success
    type: int
    sample: 5
in_service_instances:
    description: Number of instances in service
    returned: success
    type: int
    sample: 3
instance_facts:
    description: Dictionary of EC2 instances and their status as it relates to the ASG.
    returned: success
    type: dict
    sample: {
        "i-0123456789012": {
            "health_status": "Healthy",
            "launch_config_name": "public-webapp-production-1",
            "lifecycle_state": "InService"
        }
    }
instances:
    description: list of instance IDs in the ASG
    returned: success
    type: list
    sample: [
        "i-0123456789012"
    ]
launch_config_name:
    description: >
      Name of launch configuration associated with the ASG. Same as launch_configuration_name,
      provided for compatibility with M(amazon.aws.autoscaling_group) module.
    returned: success
    type: str
    sample: "public-webapp-production-1"
load_balancers:
    description: List of load balancers names attached to the ASG.
    returned: success
    type: list
    sample: ["elb-webapp-prod"]
max_instance_lifetime:
    description: The maximum amount of time, in seconds, that an instance can be in service.
    returned: success
    type: int
    sample: 604800
max_size:
    description: Maximum size of group
    returned: success
    type: int
    sample: 3
min_size:
    description: Minimum size of group
    returned: success
    type: int
    sample: 1
mixed_instances_policy:
    description: Returns the list of instance types if a mixed instances policy is set.
    returned: success
    type: list
    sample: ["t3.micro", "t3a.micro"]
mixed_instances_policy_full:
    description: Returns the full dictionary representation of the mixed instances policy if a mixed instances policy is set.
    returned: success
    type: dict
    sample: {
        "instances_distribution": {
            "on_demand_allocation_strategy": "prioritized",
            "on_demand_base_capacity": 0,
            "on_demand_percentage_above_base_capacity": 0,
            "spot_allocation_strategy": "capacity-optimized"
        },
        "launch_template": {
            "launch_template_specification": {
                "launch_template_id": "lt-53c2425cffa544c23",
                "launch_template_name": "random-LaunchTemplate",
                "version": "2"
            },
            "overrides": [
                {
                    "instance_type": "m5.xlarge"
                },
                {
                    "instance_type": "m5a.xlarge"
                },
            ]
        }
    }
pending_instances:
    description: Number of instances in pending state
    returned: success
    type: int
    sample: 1
tags:
    description: List of tags for the ASG, and whether or not each tag propagates to instances at launch.
    returned: success
    type: list
    sample: [
        {
            "key": "Name",
            "value": "public-webapp-production-1",
            "resource_id": "public-webapp-production-1",
            "resource_type": "auto-scaling-group",
            "propagate_at_launch": "true"
        },
        {
            "key": "env",
            "value": "production",
            "resource_id": "public-webapp-production-1",
            "resource_type": "auto-scaling-group",
            "propagate_at_launch": "true"
        }
    ]
target_group_arns:
    description: List of ARNs of the target groups that the ASG populates
    returned: success
    type: list
    sample: [
        "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:targetgroup/target-group-host-hello/1a2b3c4d5e6f1a2b",
        "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:targetgroup/target-group-path-world/abcd1234abcd1234"
    ]
target_group_names:
    description: List of names of the target groups that the ASG populates
    returned: success
    type: list
    sample: [
        "target-group-host-hello",
        "target-group-path-world"
    ]
termination_policies:
    description: A list of termination policies for the group.
    returned: success
    type: list
    sample: ["Default"]
unhealthy_instances:
    description: Number of instances in an unhealthy state
    returned: success
    type: int
    sample: 0
viable_instances:
    description: Number of instances in a viable state
    returned: success
    type: int
    sample: 1
vpc_zone_identifier:
    description: VPC zone ID / subnet id for the auto scaling group
    returned: success
    type: str
    sample: "subnet-a31ef45f"
metrics_collection:
    description: List of enabled AutosSalingGroup metrics
    returned: success
    type: list
    sample: [
        {
            "Granularity": "1Minute",
            "Metric": "GroupInServiceInstances"
        }
    ]
"""

import time
import typing

if typing.TYPE_CHECKING:
    from typing import Any

    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AutoScalingErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import get_autoscaling_waiter
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import get_min_viable_instances_waiter
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import transform_autoscaling_group
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_templates
from ansible_collections.amazon.aws.plugins.module_utils.elb import get_elb_waiter
from ansible_collections.amazon.aws.plugins.module_utils.elb import get_min_healthy_instances_waiter
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_target_groups
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import get_min_healthy_targets_waiter
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.iterators import chunks
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters
from ansible_collections.amazon.aws.plugins.module_utils.waiter import custom_waiter_config

backoff_params = dict(retries=10, delay=3, backoff=1.5)


def _default_if_none(value: Any, default: Any) -> Any:
    """
    Return default if value is None, otherwise return value.

    This helper reduces cyclomatic complexity by removing conditional
    assignments from function complexity calculations.

    Args:
        value: The value to check
        default: The default to use if value is None

    Returns:
        default if value is None, otherwise value
    """
    return default if value is None else value


@AutoScalingErrorHandler.list_error_handler("describe auto scaling groups", [])
@AWSRetry.jittered_backoff(**backoff_params)
def describe_autoscaling_groups(connection, group_name):
    pg = connection.get_paginator("describe_auto_scaling_groups")
    return pg.paginate(AutoScalingGroupNames=[group_name]).build_full_result().get("AutoScalingGroups", [])


@AWSRetry.jittered_backoff(**backoff_params)
def deregister_lb_instances(connection, lb_name, instance_id):
    connection.deregister_instances_from_load_balancer(
        LoadBalancerName=lb_name, Instances=[dict(InstanceId=instance_id)]
    )


@AWSRetry.jittered_backoff(**backoff_params)
def describe_instance_health(connection, lb_name, instances):
    params = dict(LoadBalancerName=lb_name)
    if instances:
        params.update(Instances=instances)
    return connection.describe_instance_health(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def describe_target_health(connection, target_group_arn, instances):
    return connection.describe_target_health(TargetGroupArn=target_group_arn, Targets=instances)


@AutoScalingErrorHandler.common_error_handler("suspend processes")
@AWSRetry.jittered_backoff(**backoff_params)
def suspend_asg_processes(connection, asg_name, processes):
    connection.suspend_processes(AutoScalingGroupName=asg_name, ScalingProcesses=processes)


@AutoScalingErrorHandler.common_error_handler("resume processes")
@AWSRetry.jittered_backoff(**backoff_params)
def resume_asg_processes(connection, asg_name, processes):
    connection.resume_processes(AutoScalingGroupName=asg_name, ScalingProcesses=processes)


@AutoScalingErrorHandler.list_error_handler("describe launch configurations", {})
@AWSRetry.jittered_backoff(**backoff_params)
def describe_launch_configurations(connection, launch_config_name):
    pg = connection.get_paginator("describe_launch_configurations")
    return pg.paginate(LaunchConfigurationNames=[launch_config_name]).build_full_result()


@AWSRetry.jittered_backoff(**backoff_params)
def describe_launch_templates(connection, launch_template):
    if launch_template["launch_template_id"] is not None:
        try:
            lt = connection.describe_launch_templates(LaunchTemplateIds=[launch_template["launch_template_id"]])
            return lt
        except is_boto3_error_code("InvalidLaunchTemplateName.NotFoundException"):
            module.fail_json(msg=f"No launch template found matching: {launch_template}")
    else:
        try:
            lt = connection.describe_launch_templates(LaunchTemplateNames=[launch_template["launch_template_name"]])
            return lt
        except is_boto3_error_code("InvalidLaunchTemplateName.NotFoundException"):
            module.fail_json(msg=f"No launch template found matching: {launch_template}")


@AutoScalingErrorHandler.common_error_handler("create auto scaling group")
@AWSRetry.jittered_backoff(**backoff_params)
def create_asg(connection, **params):
    connection.create_auto_scaling_group(**params)


@AutoScalingErrorHandler.common_error_handler("configure notifications")
@AWSRetry.jittered_backoff(**backoff_params)
def put_notification_config(connection, asg_name, topic_arn, notification_types):
    connection.put_notification_configuration(
        AutoScalingGroupName=asg_name, TopicARN=topic_arn, NotificationTypes=notification_types
    )


@AutoScalingErrorHandler.deletion_error_handler("delete notification configuration")
@AWSRetry.jittered_backoff(**backoff_params)
def del_notification_config(connection, asg_name, topic_arn):
    connection.delete_notification_configuration(AutoScalingGroupName=asg_name, TopicARN=topic_arn)


@AutoScalingErrorHandler.common_error_handler("attach load balancers")
@AWSRetry.jittered_backoff(**backoff_params)
def attach_load_balancers(connection, asg_name, load_balancers):
    connection.attach_load_balancers(AutoScalingGroupName=asg_name, LoadBalancerNames=load_balancers)


@AutoScalingErrorHandler.common_error_handler("detach load balancers")
@AWSRetry.jittered_backoff(**backoff_params)
def detach_load_balancers(connection, asg_name, load_balancers):
    connection.detach_load_balancers(AutoScalingGroupName=asg_name, LoadBalancerNames=load_balancers)


@AutoScalingErrorHandler.common_error_handler("attach target groups")
@AWSRetry.jittered_backoff(**backoff_params)
def attach_lb_target_groups(connection, asg_name, target_group_arns):
    connection.attach_load_balancer_target_groups(AutoScalingGroupName=asg_name, TargetGroupARNs=target_group_arns)


@AutoScalingErrorHandler.common_error_handler("detach target groups")
@AWSRetry.jittered_backoff(**backoff_params)
def detach_lb_target_groups(connection, asg_name, target_group_arns):
    connection.detach_load_balancer_target_groups(AutoScalingGroupName=asg_name, TargetGroupARNs=target_group_arns)


@AutoScalingErrorHandler.common_error_handler("delete tags")
@AWSRetry.jittered_backoff(**backoff_params)
def delete_asg_tags(connection, tags):
    connection.delete_tags(Tags=tags)


@AutoScalingErrorHandler.common_error_handler("create or update tags")
@AWSRetry.jittered_backoff(**backoff_params)
def create_or_update_asg_tags(connection, tags):
    connection.create_or_update_tags(Tags=tags)


@AutoScalingErrorHandler.common_error_handler("update auto scaling group")
@AWSRetry.jittered_backoff(**backoff_params)
def update_asg(connection, **params):
    connection.update_auto_scaling_group(**params)


@AutoScalingErrorHandler.deletion_error_handler("delete auto scaling group")
@AWSRetry.jittered_backoff(catch_extra_error_codes=["ScalingActivityInProgress"], **backoff_params)
def delete_asg(connection, asg_name, force_delete):
    connection.delete_auto_scaling_group(AutoScalingGroupName=asg_name, ForceDelete=force_delete)


@AutoScalingErrorHandler.common_error_handler("terminate instance")
@AWSRetry.jittered_backoff(**backoff_params)
def terminate_asg_instance(connection, instance_id, decrement_capacity):
    connection.terminate_instance_in_auto_scaling_group(
        InstanceId=instance_id, ShouldDecrementDesiredCapacity=decrement_capacity
    )


@AutoScalingErrorHandler.common_error_handler("detach instances")
@AWSRetry.jittered_backoff(**backoff_params)
def detach_asg_instances(connection, instance_ids, as_group_name, decrement_capacity):
    connection.detach_instances(
        InstanceIds=instance_ids, AutoScalingGroupName=as_group_name, ShouldDecrementDesiredCapacity=decrement_capacity
    )


def enforce_required_arguments_for_create():
    """As many arguments are not required for autoscale group deletion
    they cannot be mandatory arguments for the module, so we enforce
    them here"""
    missing_args = []
    if module.params.get("launch_config_name") is None and module.params.get("launch_template") is None:
        module.fail_json(msg="Missing either launch_config_name or launch_template for autoscaling group create")
    for arg in ("min_size", "max_size"):
        if module.params[arg] is None:
            missing_args.append(arg)
    if missing_args:
        module.fail_json(msg=f"Missing required arguments for autoscaling group create: {','.join(missing_args)}")


def _resolve_target_group_names(target_group_arns: list[str]) -> list[str]:
    """
    Resolve target group ARNs to names in chunks.

    Args:
        target_group_arns: List of target group ARNs

    Returns:
        list: Target group names
    """
    if not target_group_arns:
        return []

    elbv2_connection = module.client("elbv2")
    target_group_names = []

    # Process in chunks of 20 (API limit)
    # https://github.com/ansible-collections/amazon.aws/pull/1593
    for chunk in chunks(target_group_arns, 20):
        target_group_names.extend(
            [tg["TargetGroupName"] for tg in describe_target_groups(elbv2_connection, TargetGroupArns=chunk)]
        )

    return target_group_names


def get_properties(autoscaling_group: dict[str, Any]) -> dict[str, Any]:
    """
    Convert ASG from boto3 CamelCase format to Ansible snake_case format.

    Resolves target group names via API, then transforms the enriched ASG data.

    Args:
        autoscaling_group: Raw ASG data from boto3 describe_auto_scaling_groups

    Returns:
        dict: Transformed ASG properties in snake_case with additional computed fields
    """
    # Resolve target group ARNs to names - API call (done first)
    target_group_names = _resolve_target_group_names(autoscaling_group.get("TargetGroupARNs", []))

    # Create enriched autoscaling_group with target group names
    enriched_asg = autoscaling_group.copy()
    enriched_asg["TargetGroupNames"] = target_group_names

    # Pass to pure transformation function from module_utils
    return transform_autoscaling_group(enriched_asg)


def _build_launch_template_spec(lt_data: dict[str, Any], requested_version: str | None) -> dict[str, Any]:
    """
    Build launch template specification from template data.

    Args:
        lt_data: Launch template data from AWS
        requested_version: Requested version or None for latest

    Returns:
        dict: Launch template specification with ID and version
    """
    version = requested_version if requested_version is not None else str(lt_data["LatestVersionNumber"])
    return {"LaunchTemplateId": lt_data["LaunchTemplateId"], "Version": version}


def _build_mixed_instances_policy(
    launch_template_spec: dict[str, Any], mixed_instances_policy: dict[str, Any]
) -> dict[str, Any]:
    """
    Build mixed instances policy from parameters.

    Args:
        launch_template_spec: Launch template specification
        mixed_instances_policy: Mixed instances policy parameters

    Returns:
        dict: Complete mixed instances policy
    """
    policy = {"LaunchTemplate": {"LaunchTemplateSpecification": launch_template_spec}}

    instance_types = mixed_instances_policy.get("instance_types", [])
    if instance_types:
        policy["LaunchTemplate"]["Overrides"] = [{"InstanceType": it} for it in instance_types]

    instances_distribution = mixed_instances_policy.get("instances_distribution", {})
    if instances_distribution:
        instances_distribution_params = scrub_none_parameters(instances_distribution)
        policy["InstancesDistribution"] = snake_dict_to_camel_dict(instances_distribution_params, capitalize_first=True)

    return policy


def get_launch_object(connection, ec2_connection):
    launch_config_name = module.params.get("launch_config_name")
    launch_template = module.params.get("launch_template")
    mixed_instances_policy = module.params.get("mixed_instances_policy")

    if launch_config_name is None and launch_template is None:
        return dict()

    if launch_config_name:
        launch_configs = describe_launch_configurations(connection, launch_config_name)
        if len(launch_configs["LaunchConfigurations"]) == 0:
            raise AnsibleAWSError(f"No launch config found with name {launch_config_name}")
        return {"LaunchConfigurationName": launch_configs["LaunchConfigurations"][0]["LaunchConfigurationName"]}

    # launch_template path
    lt = describe_launch_templates(ec2_connection, launch_template)["LaunchTemplates"][0]
    launch_template_spec = _build_launch_template_spec(lt, launch_template["version"])
    launch_object = {"LaunchTemplate": launch_template_spec}

    if mixed_instances_policy:
        launch_object["MixedInstancesPolicy"] = _build_mixed_instances_policy(
            launch_template_spec, mixed_instances_policy
        )

    return launch_object


@AutoScalingErrorHandler.common_error_handler("wait for ELB deregistration")
def _wait_for_elb_deregistration(elb_connection: str, lb_names: list[str], instance_id: str, timeout: int) -> None:
    """
    Wait for an instance to be deregistered from all load balancers.

    Args:
        elb_connection: ELB connection
        lb_names: List of load balancer names
        instance_id: Instance ID to wait for
        timeout: Wait timeout in seconds

    Raises:
        AnsibleAWSError: If timeout is reached
    """
    waiter_config = custom_waiter_config(timeout=timeout, default_pause=10)
    waiter = get_elb_waiter(elb_connection, "instance_deregistered")
    for lb_name in lb_names:
        waiter.wait(LoadBalancerName=lb_name, Instances=[{"InstanceId": instance_id}], WaiterConfig=waiter_config)


def elb_dreg(asg_connection, group_name, instance_id):
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]
    wait_timeout = module.params.get("wait_timeout")

    # Early return if no ELB health checking
    if not (as_group["LoadBalancerNames"] and as_group["HealthCheckType"] == "ELB"):
        return

    elb_connection = module.client("elb")

    # Deregister from all load balancers
    for lb in as_group["LoadBalancerNames"]:
        deregister_lb_instances(elb_connection, lb, instance_id)
        module.debug(f"De-registering {instance_id} from ELB {lb}")

    # Wait for deregistration to complete
    _wait_for_elb_deregistration(elb_connection, as_group["LoadBalancerNames"], instance_id, wait_timeout)


@AutoScalingErrorHandler.common_error_handler("wait for ELB health")
def wait_for_elb(asg_connection, group_name):
    """
    Wait for instances to be healthy on all attached ELBs.

    Waits until at least MinSize instances are healthy across all load balancers.

    Args:
        asg_connection: AutoScaling connection
        group_name: Name of the ASG
    """
    wait_timeout = module.params.get("wait_timeout")
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]

    # Only wait if using ELB health checks and ELBs are attached
    if not (as_group.get("LoadBalancerNames") and as_group.get("HealthCheckType") == "ELB"):
        return

    module.debug("Waiting for ELB to consider instances healthy.")
    elb_connection = module.client("elb")
    min_size = as_group.get("MinSize")

    # Get viable instances from ASG (Healthy + InService)
    props = get_properties(as_group)
    viable_instance_ids = [
        instance_id
        for instance_id, facts in props["instance_facts"].items()
        if facts["lifecycle_state"] == "InService" and facts["health_status"] == "Healthy"
    ]

    if not viable_instance_ids:
        module.debug("No viable instances in ASG yet")
        return

    instances_param = [{"InstanceId": iid} for iid in viable_instance_ids]

    # Track elapsed time to avoid exceeding total timeout across multiple ELBs
    start_time = time.time()

    # Wait for each ELB to have MinSize healthy instances
    for lb_name in as_group.get("LoadBalancerNames"):
        # Calculate remaining timeout, ensuring at least 1 second
        elapsed = time.time() - start_time
        remaining_timeout = max(1, int(wait_timeout - elapsed))

        module.debug(f"Waiting for {min_size} instances to be healthy on ELB {lb_name} (timeout: {remaining_timeout}s)")
        waiter_config = custom_waiter_config(timeout=remaining_timeout, default_pause=10)
        waiter = get_min_healthy_instances_waiter(elb_connection, min_size)
        waiter.wait(LoadBalancerName=lb_name, Instances=instances_param, WaiterConfig=waiter_config)

    module.debug(f"ELBs have at least {min_size} healthy instances")


@AutoScalingErrorHandler.common_error_handler("wait for target group health")
def wait_for_target_group(asg_connection, group_name):
    """
    Wait for instances to be healthy in all attached target groups.

    Waits until at least MinSize instances are healthy across all target groups.

    Args:
        asg_connection: AutoScaling connection
        group_name: Name of the ASG
    """
    wait_timeout = module.params.get("wait_timeout")
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]

    # Only wait if using ELB health checks and target groups are attached
    if not (as_group.get("TargetGroupARNs") and as_group.get("HealthCheckType") == "ELB"):
        return

    module.debug("Waiting for Target Group to consider instances healthy.")
    elbv2_connection = module.client("elbv2")
    min_size = as_group.get("MinSize")

    # Get viable instances from ASG (Healthy + InService)
    props = get_properties(as_group)
    viable_instance_ids = [
        instance_id
        for instance_id, facts in props["instance_facts"].items()
        if facts["lifecycle_state"] == "InService" and facts["health_status"] == "Healthy"
    ]

    if not viable_instance_ids:
        module.debug("No viable instances in ASG yet")
        return

    targets_param = [{"Id": iid} for iid in viable_instance_ids]

    # Track elapsed time to avoid exceeding total timeout across multiple target groups
    start_time = time.time()

    # Wait for each target group to have MinSize healthy targets
    for tg_arn in as_group.get("TargetGroupARNs"):
        # Calculate remaining timeout, ensuring at least 1 second
        elapsed = time.time() - start_time
        remaining_timeout = max(1, int(wait_timeout - elapsed))

        module.debug(f"Waiting for {min_size} targets to be healthy in target group {tg_arn} (timeout: {remaining_timeout}s)")
        waiter_config = custom_waiter_config(timeout=remaining_timeout, default_pause=10)
        waiter = get_min_healthy_targets_waiter(elbv2_connection, min_size)
        waiter.wait(TargetGroupArn=tg_arn, Targets=targets_param, WaiterConfig=waiter_config)

    module.debug(f"Target groups have at least {min_size} healthy targets")


def suspend_processes(ec2_connection, as_group):
    processes_to_suspend = set(module.params.get("suspend_processes"))

    try:
        suspended_processes = {p["ProcessName"] for p in as_group["SuspendedProcesses"]}
    except AttributeError:
        # New ASG being created, no suspended_processes defined yet
        suspended_processes = set()

    if processes_to_suspend == suspended_processes:
        return False

    resume_processes = list(suspended_processes - processes_to_suspend)
    if resume_processes:
        resume_asg_processes(ec2_connection, module.params.get("name"), resume_processes)

    if processes_to_suspend:
        suspend_asg_processes(ec2_connection, module.params.get("name"), list(processes_to_suspend))

    return True


def build_asg_tags(set_tags: list[dict[str, Any]], group_name: str) -> list[dict[str, Any]]:
    """
    Convert user-provided tags to ASG tag format.

    Args:
        set_tags: List of tag dictionaries from module params
        group_name: Name of the autoscaling group

    Returns:
        List of tags formatted for AWS ASG API
    """
    asg_tags = []
    for tag in set_tags:
        for k, v in tag.items():
            if k != "propagate_at_launch":
                asg_tags.append(
                    {
                        "Key": k,
                        "Value": to_native(v),
                        "PropagateAtLaunch": bool(tag.get("propagate_at_launch", True)),
                        "ResourceType": "auto-scaling-group",
                        "ResourceId": group_name,
                    }
                )
    return asg_tags


def compare_asg_tags(
    have_tags: list[dict[str, Any]] | None, want_tags: list[dict[str, Any]] | None, purge_tags: bool
) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
    """
    Compare current and desired ASG tags to determine changes.

    Compares full tag dictionaries including Key, Value, PropagateAtLaunch, etc.

    Args:
        have_tags: Current tags on the ASG (AWS format)
        want_tags: Desired tags (AWS format)
        purge_tags: Whether to remove tags not in want_tags

    Returns:
        tuple: (tags_to_delete, tags_to_set)
            - tags_to_delete: List of tag dicts to delete (empty if not purge_tags)
            - tags_to_set: List of tag dicts to create/update (or None if no changes)
    """
    # Sort for comparison
    have_sorted = sorted(have_tags or [], key=lambda x: x["Key"])
    want_sorted = sorted(want_tags or [], key=lambda x: x["Key"])

    # Find tags to delete
    have_keys = {tag["Key"] for tag in have_sorted}
    want_keys = {tag["Key"] for tag in want_sorted}
    keys_to_delete = have_keys - want_keys

    tags_to_delete = []
    if keys_to_delete and purge_tags:
        tags_to_delete = [tag for tag in have_sorted if tag["Key"] in keys_to_delete]

    # Compare remaining tags (including PropagateAtLaunch)
    have_remaining = [tag for tag in have_sorted if tag["Key"] not in keys_to_delete]
    tags_changed = have_remaining != want_sorted

    # Determine tags to set
    tags_to_set = want_sorted if tags_changed else None

    return tags_to_delete, tags_to_set


def apply_asg_tag_changes(
    connection: Any,
    as_group_name: str,
    tags_to_delete: list[dict[str, Any]],
    tags_to_set: list[dict[str, Any]] | None,
) -> bool:
    """
    Apply tag changes to an ASG.

    Args:
        connection: AutoScaling connection
        as_group_name: Name of the autoscaling group
        tags_to_delete: List of tag dicts to delete
        tags_to_set: List of tag dicts to create/update (or None if no changes)

    Returns:
        bool: True if changes were applied, False otherwise
    """
    if not tags_to_delete and tags_to_set is None:
        return False

    if tags_to_delete:
        # Format for delete_tags API
        delete_tags = [
            {
                "ResourceId": as_group_name,
                "ResourceType": "auto-scaling-group",
                "Key": tag["Key"],
            }
            for tag in tags_to_delete
        ]
        delete_asg_tags(connection, delete_tags)

    if tags_to_set is not None:
        create_or_update_asg_tags(connection, tags_to_set)

    return True


def update_load_balancers(
    connection: Any, group_name: str, current_elbs: list[str], desired_elbs: list[str] | None
) -> bool:
    """
    Update load balancers attached to an ASG.

    Args:
        connection: AutoScaling connection
        group_name: Name of the autoscaling group
        current_elbs: Currently attached load balancer names
        desired_elbs: Desired load balancer names (None means no change)

    Returns:
        True if changes were made, False otherwise
    """
    # If desired_elbs is None, no change requested
    if desired_elbs is None:
        return False

    changed = False
    current_set = set(current_elbs)
    desired_set = set(desired_elbs)

    # Detach load balancers no longer wanted
    elbs_to_detach = current_set - desired_set
    if elbs_to_detach:
        detach_load_balancers(connection, group_name, list(elbs_to_detach))
        changed = True

    # Attach new load balancers
    elbs_to_attach = desired_set - current_set
    if elbs_to_attach:
        attach_load_balancers(connection, group_name, list(elbs_to_attach))
        changed = True

    return changed


def update_target_groups(
    connection: Any, group_name: str, current_tgs: list[str], desired_tgs: list[str] | None
) -> bool:
    """
    Update target groups attached to an ASG.

    Args:
        connection: AutoScaling connection
        group_name: Name of the autoscaling group
        current_tgs: Currently attached target group ARNs
        desired_tgs: Desired target group ARNs (None means no change)

    Returns:
        True if changes were made, False otherwise
    """
    # If desired_tgs is None, no change requested
    if desired_tgs is None:
        return False

    changed = False
    current_set = set(current_tgs)
    desired_set = set(desired_tgs)

    # Detach target groups no longer wanted
    tgs_to_detach = current_set - desired_set
    if tgs_to_detach:
        detach_lb_target_groups(connection, group_name, list(tgs_to_detach))
        changed = True

    # Attach new target groups
    tgs_to_attach = desired_set - current_set
    if tgs_to_attach:
        attach_lb_target_groups(connection, group_name, list(tgs_to_attach))
        changed = True

    return changed


def build_launch_config_params(launch_object: dict[str, Any], as_group: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Build launch configuration parameters for ASG create/update.

    Args:
        launch_object: Launch object from get_launch_object()
        as_group: Existing ASG (for updates) or None (for creates)

    Returns:
        dict: Parameters to add to ASG create/update call

    Raises:
        AnsibleAWSError: If no launch configuration or template is available
    """
    if "LaunchConfigurationName" in launch_object:
        return {"LaunchConfigurationName": launch_object["LaunchConfigurationName"]}

    if "LaunchTemplate" in launch_object:
        if "MixedInstancesPolicy" in launch_object:
            return {"MixedInstancesPolicy": launch_object["MixedInstancesPolicy"]}
        return {"LaunchTemplate": launch_object["LaunchTemplate"]}

    # For updates when no launch object provided, use existing
    if as_group:
        if "LaunchConfigurationName" in as_group:
            return {"LaunchConfigurationName": as_group["LaunchConfigurationName"]}
        if "LaunchTemplate" in as_group:
            # Use existing launch template
            launch_template = as_group["LaunchTemplate"]
            # Prefer LaunchTemplateId over Name as it's more specific
            return {
                "LaunchTemplate": {
                    "LaunchTemplateId": launch_template["LaunchTemplateId"],
                    "Version": launch_template["Version"],
                }
            }

    raise AnsibleAWSError(message="Missing LaunchConfigurationName or LaunchTemplate")


def build_base_asg_params(
    group_name: str,
    min_size: int,
    max_size: int,
    desired_capacity: int,
    health_check_period: int,
    health_check_type: str,
    default_cooldown: int,
    termination_policies: list[str],
    protected_from_scale_in: bool,
    vpc_zone_identifier: str | None = None,
    availability_zones: list[str] | None = None,
    max_instance_lifetime: int | None = None,
) -> dict[str, Any]:
    """
    Build base ASG parameters common to both create and update operations.

    Args:
        group_name: Name of the AutoScaling Group
        min_size: Minimum number of instances
        max_size: Maximum number of instances
        desired_capacity: Desired number of instances
        health_check_period: Health check grace period in seconds
        health_check_type: Health check type (EC2 or ELB)
        default_cooldown: Default cooldown period in seconds
        termination_policies: List of termination policies
        protected_from_scale_in: Whether instances are protected from scale-in
        vpc_zone_identifier: Comma-separated subnet IDs (optional)
        availability_zones: List of availability zones (optional)
        max_instance_lifetime: Maximum instance lifetime in seconds (optional)

    Returns:
        dict: Base parameters for ASG create/update
    """
    params = {
        "AutoScalingGroupName": group_name,
        "MinSize": min_size,
        "MaxSize": max_size,
        "DesiredCapacity": desired_capacity,
        "HealthCheckGracePeriod": health_check_period,
        "HealthCheckType": health_check_type,
        "DefaultCooldown": default_cooldown,
        "TerminationPolicies": termination_policies,
        "NewInstancesProtectedFromScaleIn": protected_from_scale_in,
    }

    if vpc_zone_identifier:
        params["VPCZoneIdentifier"] = vpc_zone_identifier
    if availability_zones:
        params["AvailabilityZones"] = availability_zones
    if max_instance_lifetime is not None:
        params["MaxInstanceLifetime"] = max_instance_lifetime

    return params


def build_create_only_params(
    tags: list[dict[str, Any]],
    placement_group: str | None = None,
    load_balancers: list[str] | None = None,
    target_group_arns: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build parameters that can only be set during ASG creation.

    Args:
        tags: List of tags (always required for create)
        placement_group: Placement group name (optional, create-only)
        load_balancers: List of classic ELB names (optional, create-only)
        target_group_arns: List of target group ARNs (optional, create-only)

    Returns:
        dict: Create-only parameters for ASG
    """
    params = {"Tags": tags}

    if placement_group:
        params["PlacementGroup"] = placement_group
    if load_balancers:
        params["LoadBalancerNames"] = load_balancers
    if target_group_arns:
        params["TargetGroupARNs"] = target_group_arns

    return params


def _create_new_asg(connection: Any, group_name: str, ec2_connection: Any) -> tuple[bool, dict[str, Any]]:
    """
    Create a new AutoScaling Group.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG to create
        ec2_connection: EC2 connection for launch template lookups

    Returns:
        tuple: (changed=True, asg_properties)
    """
    load_balancers = module.params["load_balancers"]
    target_group_arns = module.params["target_group_arns"]
    availability_zones = module.params["availability_zones"]
    min_size = module.params["min_size"]
    max_size = module.params["max_size"]
    max_instance_lifetime = module.params.get("max_instance_lifetime")
    placement_group = module.params.get("placement_group")
    desired_capacity = module.params.get("desired_capacity")
    vpc_zone_identifier = module.params.get("vpc_zone_identifier")
    set_tags = module.params.get("tags")
    protected_from_scale_in = module.params.get("protected_from_scale_in")
    health_check_period = module.params.get("health_check_period")
    health_check_type = module.params.get("health_check_type")
    default_cooldown = module.params.get("default_cooldown")
    wait_for_instances = module.params.get("wait_for_instances")
    wait_timeout = module.params.get("wait_timeout")
    termination_policies = module.params.get("termination_policies")
    notification_topic = module.params.get("notification_topic")
    notification_types = module.params.get("notification_types")
    metrics_collection = module.params.get("metrics_collection")
    metrics_granularity = module.params.get("metrics_granularity")
    metrics_list = module.params.get("metrics_list")

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have created AutoScalingGroup if not in check_mode.")

    if vpc_zone_identifier:
        vpc_zone_identifier = ",".join(vpc_zone_identifier)

    if not vpc_zone_identifier and not availability_zones:
        availability_zones = module.params["availability_zones"] = [
            zone["ZoneName"] for zone in ec2_connection.describe_availability_zones()["AvailabilityZones"]
        ]

    enforce_required_arguments_for_create()

    desired_capacity = _default_if_none(desired_capacity, min_size)
    protected_from_scale_in = _default_if_none(protected_from_scale_in, False)

    asg_tags = build_asg_tags(set_tags, group_name)

    ag = build_base_asg_params(
        group_name=group_name,
        min_size=min_size,
        max_size=max_size,
        desired_capacity=desired_capacity,
        health_check_period=health_check_period,
        health_check_type=health_check_type,
        default_cooldown=default_cooldown,
        termination_policies=termination_policies,
        protected_from_scale_in=protected_from_scale_in,
        vpc_zone_identifier=vpc_zone_identifier,
        availability_zones=availability_zones,
        max_instance_lifetime=max_instance_lifetime,
    )

    ag.update(
        build_create_only_params(
            tags=asg_tags,
            placement_group=placement_group,
            load_balancers=load_balancers,
            target_group_arns=target_group_arns,
        )
    )

    launch_object = get_launch_object(connection, ec2_connection)
    ag.update(build_launch_config_params(launch_object, None))

    create_asg(connection, **ag)

    if metrics_collection:
        connection.enable_metrics_collection(
            AutoScalingGroupName=group_name, Granularity=metrics_granularity, Metrics=metrics_list
        )

    all_ag = describe_autoscaling_groups(connection, group_name)
    if len(all_ag) == 0:
        module.fail_json(msg=f"No auto scaling group found with the name {group_name}")

    as_group = all_ag[0]
    suspend_processes(connection, as_group)

    if wait_for_instances:
        wait_for_new_inst(connection, group_name, wait_timeout, desired_capacity, "viable_instances")
        if load_balancers:
            wait_for_elb(connection, group_name)
        if target_group_arns:
            wait_for_target_group(connection, group_name)

    if notification_topic:
        put_notification_config(connection, group_name, notification_topic, notification_types)

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    asg_properties = get_properties(as_group)
    return True, asg_properties


def _update_existing_asg(
    connection: Any, group_name: str, ec2_connection: Any, as_group: dict[str, Any]
) -> tuple[bool, dict[str, Any]]:
    """
    Update an existing AutoScaling Group.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG to update
        ec2_connection: EC2 connection for launch template lookups
        as_group: Existing ASG configuration

    Returns:
        tuple: (changed, asg_properties)
    """
    load_balancers = module.params["load_balancers"]
    target_group_arns = module.params["target_group_arns"]
    availability_zones = module.params["availability_zones"]
    min_size = module.params["min_size"]
    max_size = module.params["max_size"]
    max_instance_lifetime = module.params.get("max_instance_lifetime")
    desired_capacity = module.params.get("desired_capacity")
    vpc_zone_identifier = module.params.get("vpc_zone_identifier")
    set_tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    protected_from_scale_in = module.params.get("protected_from_scale_in")
    health_check_period = module.params.get("health_check_period")
    health_check_type = module.params.get("health_check_type")
    default_cooldown = module.params.get("default_cooldown")
    wait_for_instances = module.params.get("wait_for_instances")
    wait_timeout = module.params.get("wait_timeout")
    termination_policies = module.params.get("termination_policies")
    notification_topic = module.params.get("notification_topic")
    notification_types = module.params.get("notification_types")
    metrics_collection = module.params.get("metrics_collection")
    metrics_granularity = module.params.get("metrics_granularity")
    metrics_list = module.params.get("metrics_list")

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have modified AutoScalingGroup if required if not in check_mode.")

    if vpc_zone_identifier:
        vpc_zone_identifier = ",".join(vpc_zone_identifier)

    initial_asg_properties = get_properties(as_group)
    changed = False

    changed |= suspend_processes(connection, as_group)

    # Process tag changes
    asg_tags = build_asg_tags(set_tags, group_name)
    tags_to_delete, tags_to_set = compare_asg_tags(as_group.get("Tags"), asg_tags, purge_tags)
    changed |= apply_asg_tag_changes(connection, as_group["AutoScalingGroupName"], tags_to_delete, tags_to_set)

    # Handle load balancer and target group attachments/detachments
    changed |= update_load_balancers(connection, group_name, as_group["LoadBalancerNames"], load_balancers)
    changed |= update_target_groups(connection, group_name, as_group["TargetGroupARNs"], target_group_arns)

    # Use existing ASG values as defaults if not specified
    min_size = _default_if_none(min_size, as_group["MinSize"])
    max_size = _default_if_none(max_size, as_group["MaxSize"])
    desired_capacity = _default_if_none(desired_capacity, as_group["DesiredCapacity"])
    protected_from_scale_in = _default_if_none(protected_from_scale_in, as_group["NewInstancesProtectedFromScaleIn"])

    ag = build_base_asg_params(
        group_name=group_name,
        min_size=min_size,
        max_size=max_size,
        desired_capacity=desired_capacity,
        health_check_period=health_check_period,
        health_check_type=health_check_type,
        default_cooldown=default_cooldown,
        termination_policies=termination_policies,
        protected_from_scale_in=protected_from_scale_in,
        vpc_zone_identifier=vpc_zone_identifier,
        availability_zones=availability_zones,
        max_instance_lifetime=max_instance_lifetime,
    )

    # Get the launch object (config or template) if one is provided in args or use the existing one attached to ASG if not.
    launch_object = get_launch_object(connection, ec2_connection)
    ag.update(build_launch_config_params(launch_object, as_group))

    update_asg(connection, **ag)

    if metrics_collection:
        connection.enable_metrics_collection(
            AutoScalingGroupName=group_name, Granularity=metrics_granularity, Metrics=metrics_list
        )
    else:
        connection.disable_metrics_collection(AutoScalingGroupName=group_name, Metrics=metrics_list)

    if notification_topic:
        put_notification_config(connection, group_name, notification_topic, notification_types)

    if wait_for_instances:
        wait_for_new_inst(connection, group_name, wait_timeout, desired_capacity, "viable_instances")
        if load_balancers:
            module.debug("\tWAITING FOR ELB HEALTH")
            wait_for_elb(connection, group_name)
        if target_group_arns:
            module.debug("\tWAITING FOR TG HEALTH")
            wait_for_target_group(connection, group_name)

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    asg_properties = get_properties(as_group)

    if asg_properties != initial_asg_properties:
        changed = True

    return changed, asg_properties


def create_autoscaling_group(connection):
    """
    Create or update an AutoScaling Group.

    Dispatcher function that checks if ASG exists and delegates to
    _create_new_asg() or _update_existing_asg() accordingly.

    Args:
        connection: AutoScaling connection

    Returns:
        tuple: (changed, asg_properties)
    """
    group_name = module.params.get("name")
    as_groups = describe_autoscaling_groups(connection, group_name)
    ec2_connection = module.client("ec2")

    if not as_groups:
        return _create_new_asg(connection, group_name, ec2_connection)
    else:
        as_group = as_groups[0]
        return _update_existing_asg(connection, group_name, ec2_connection, as_group)


@AutoScalingErrorHandler.common_error_handler("wait for ASG instances to terminate")
def _wait_for_asg_instances_to_terminate(connection: str, group_name: str, timeout: int) -> None:
    """
    Wait for all instances in an ASG to terminate.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG
        timeout: Wait timeout in seconds

    Raises:
        Fails the module if timeout is reached
    """
    waiter_config = custom_waiter_config(timeout=timeout, default_pause=10)
    waiter = get_autoscaling_waiter(connection, "group_instances_terminated")
    waiter.wait(AutoScalingGroupNames=[group_name], WaiterConfig=waiter_config)


@AutoScalingErrorHandler.common_error_handler("wait for ASG to delete")
def _wait_for_asg_to_delete(connection: str, group_name: str, timeout: int) -> None:
    """
    Wait for an ASG to be fully deleted.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG
        timeout: Wait timeout in seconds

    Raises:
        Fails the module if timeout is reached
    """
    waiter_config = custom_waiter_config(timeout=timeout, default_pause=5)
    waiter = get_autoscaling_waiter(connection, "group_not_exists")
    waiter.wait(AutoScalingGroupNames=[group_name], WaiterConfig=waiter_config)


def _scale_asg_to_zero(connection: str, group_name: str) -> None:
    """
    Scale an ASG to zero instances before deletion.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG
    """
    updated_params = dict(AutoScalingGroupName=group_name, MinSize=0, MaxSize=0, DesiredCapacity=0)
    update_asg(connection, **updated_params)


def delete_autoscaling_group(connection):
    group_name = module.params.get("name")
    notification_topic = module.params.get("notification_topic")
    wait_for_instances = module.params.get("wait_for_instances")
    wait_timeout = module.params.get("wait_timeout")

    if notification_topic:
        del_notification_config(connection, group_name, notification_topic)

    groups = describe_autoscaling_groups(connection, group_name)
    if not groups:
        return False

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have deleted AutoScalingGroup if not in check_mode.")

    # Scale to zero and wait for instances to terminate if requested
    if wait_for_instances:
        _scale_asg_to_zero(connection, group_name)
        _wait_for_asg_instances_to_terminate(connection, group_name, wait_timeout)
        delete_asg(connection, group_name, force_delete=False)
    else:
        delete_asg(connection, group_name, force_delete=True)

    # Wait for ASG to be fully deleted
    _wait_for_asg_to_delete(connection, group_name, wait_timeout)
    return True


def update_size(connection, group, max_size, min_size, dc, protected_from_scale_in):
    module.debug("setting ASG sizes")
    module.debug(
        f"minimum size: {min_size}, desired_capacity: {dc}, max size: {max_size}, protected from scale in: {protected_from_scale_in}"
    )
    updated_group = dict()
    updated_group["AutoScalingGroupName"] = group["AutoScalingGroupName"]
    updated_group["MinSize"] = min_size
    updated_group["MaxSize"] = max_size
    updated_group["DesiredCapacity"] = dc
    if protected_from_scale_in is not None:
        updated_group["NewInstancesProtectedFromScaleIn"] = bool(protected_from_scale_in)
    update_asg(connection, **updated_group)


def _get_launch_spec_check_flags() -> tuple[bool, bool]:
    """
    Determine if launch config/template checks should be performed.

    Returns:
        tuple: (lc_check, lt_check) flags
    """
    launch_config_name = module.params.get("launch_config_name")
    launch_template = module.params.get("launch_template")

    # Required to maintain the default value being set to 'true'
    lc_check = module.params.get("lc_check") if launch_config_name else False
    lt_check = module.params.get("lt_check") if launch_template else False

    return lc_check, lt_check


def _wait_for_replacement_instances(connection: str, group_name: str, wait_timeout: int, desired_size: int) -> None:
    """
    Wait for replacement instances to be viable and registered with load balancers.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG
        wait_timeout: Timeout in seconds
        desired_size: Number of viable instances to wait for
    """
    wait_for_new_inst(connection, group_name, wait_timeout, desired_size, "viable_instances")
    wait_for_elb(connection, group_name)
    wait_for_target_group(connection, group_name)


def replace(connection):
    batch_size = module.params.get("replace_batch_size")
    wait_timeout = module.params.get("wait_timeout")
    wait_for_instances = module.params.get("wait_for_instances")
    group_name = module.params.get("name")
    max_size = module.params.get("max_size")
    min_size = module.params.get("min_size")
    protected_from_scale_in = module.params.get("protected_from_scale_in")
    desired_capacity = module.params.get("desired_capacity")
    launch_config_name = module.params.get("launch_config_name")
    launch_template = module.params.get("launch_template")
    replace_instances = module.params.get("replace_instances")
    replace_all_instances = module.params.get("replace_all_instances")

    lc_check, lt_check = _get_launch_spec_check_flags()

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    desired_capacity = _default_if_none(desired_capacity, as_group["DesiredCapacity"])

    if wait_for_instances:
        wait_for_new_inst(connection, group_name, wait_timeout, as_group["MinSize"], "viable_instances")

    props = get_properties(as_group)
    instances = props["instances"]
    if replace_all_instances:
        # If replacing all instances, then set replace_instances to current set
        # This allows replace_instances and replace_all_instances to behave same
        replace_instances = instances
    if replace_instances:
        instances = replace_instances

    # check to see if instances are replaceable if checking launch configs
    if launch_config_name:
        new_instances, old_instances = get_instances_by_launch_config(props, lc_check, instances)
    elif launch_template:
        new_instances, old_instances = get_instances_by_launch_template(props, lt_check, instances)

    num_new_inst_needed = desired_capacity - len(new_instances)

    if lc_check or lt_check:
        if num_new_inst_needed == 0 and old_instances:
            module.debug("No new instances needed, but old instances are present. Removing old instances")
            terminate_batch(connection, old_instances, instances, True)
            as_group = describe_autoscaling_groups(connection, group_name)[0]
            props = get_properties(as_group)
            changed = True
            return changed, props

        #  we don't want to spin up extra instances if not necessary
        if num_new_inst_needed < batch_size:
            module.debug(f"Overriding batch size to {num_new_inst_needed}")
            batch_size = num_new_inst_needed

    if not old_instances:
        changed = False
        return changed, props

    # check if min_size/max_size/desired capacity have been specified and if not use ASG values
    min_size = _default_if_none(min_size, as_group["MinSize"])
    max_size = _default_if_none(max_size, as_group["MaxSize"])

    # set temporary settings and wait for them to be reached
    # This should get overwritten if the number of instances left is less than the batch size.

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    update_size(
        connection,
        as_group,
        max_size + batch_size,
        min_size + batch_size,
        desired_capacity + batch_size,
        protected_from_scale_in,
    )

    if wait_for_instances:
        _wait_for_replacement_instances(connection, group_name, wait_timeout, as_group["MinSize"] + batch_size)

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    props = get_properties(as_group)
    instances = props["instances"]
    if replace_instances:
        instances = replace_instances

    module.debug("beginning main loop")
    for i in chunks(instances, batch_size):
        # break out of this loop if we have enough new instances
        break_early, desired_size, term_instances = terminate_batch(connection, i, instances, False)

        if wait_for_instances:
            wait_for_term_inst(connection, term_instances)
            _wait_for_replacement_instances(connection, group_name, wait_timeout, desired_size)

        if break_early:
            module.debug("breaking loop")
            break

    update_size(connection, as_group, max_size, min_size, desired_capacity, protected_from_scale_in)
    as_group = describe_autoscaling_groups(connection, group_name)[0]
    asg_properties = get_properties(as_group)
    module.debug("Rolling update complete.")
    changed = True
    return changed, asg_properties


def detach(connection):
    group_name = module.params.get("name")
    detach_instances = module.params.get("detach_instances")
    as_group = describe_autoscaling_groups(connection, group_name)[0]
    decrement_desired_capacity = module.params.get("decrement_desired_capacity")
    min_size = module.params.get("min_size")
    props = get_properties(as_group)
    instances = props["instances"]

    # check if provided instance exists in asg, create list of instances to detach which exist in asg
    instances_to_detach = []
    for instance_id in detach_instances:
        if instance_id in instances:
            instances_to_detach.append(instance_id)

    # check if setting decrement_desired_capacity will make desired_capacity smaller
    # than the currently set minimum size in ASG configuration
    if decrement_desired_capacity:
        decremented_desired_capacity = len(instances) - len(instances_to_detach)
        if min_size and min_size > decremented_desired_capacity:
            module.fail_json(
                msg=(
                    "Detaching instance(s) with 'decrement_desired_capacity' flag set reduces number of instances to"
                    f" {decremented_desired_capacity} which is below current min_size {min_size}, please update"
                    " AutoScalingGroup Sizes properly."
                )
            )

    if instances_to_detach:
        detach_asg_instances(connection, instances_to_detach, group_name, decrement_desired_capacity)

    asg_properties = get_properties(as_group)
    return True, asg_properties


def _is_instance_using_launch_config(instance_id: str, props: dict[str, Any]) -> bool:
    """
    Check if an instance is using the current launch configuration.

    Args:
        instance_id: Instance ID to check
        props: ASG properties including instance facts and launch config name

    Returns:
        bool: True if instance uses current launch config, False otherwise
    """
    instance_facts = props["instance_facts"][instance_id]

    # Migration check - instance has launch template instead of launch config
    if "launch_template" in instance_facts:
        return False

    # Match check - instance has the current launch config
    if instance_facts.get("launch_config_name") == props["launch_config_name"]:
        return True

    return False


def _is_instance_using_launch_template(instance_id: str, props: dict[str, Any]) -> bool:
    """
    Check if an instance is using the current launch template.

    Args:
        instance_id: Instance ID to check
        props: ASG properties including instance facts and launch template

    Returns:
        bool: True if instance uses current launch template, False otherwise
    """
    instance_facts = props["instance_facts"][instance_id]

    # Migration check - instance has launch config instead of launch template
    if "launch_config_name" in instance_facts:
        return False

    # Match check - instance has the current launch template
    if instance_facts.get("launch_template") == props["launch_template"]:
        return True

    return False


def _get_instances_by_launch_spec(props, check_enabled, initial_instances, is_using_current_spec):
    """
    Classify instances as new or old based on launch specification.

    Args:
        props: ASG properties including instances and instance facts
        check_enabled: Whether to check launch spec or use initial_instances
        initial_instances: List of initial instance IDs (used when check_enabled is False)
        is_using_current_spec: Function to determine if instance uses current spec

    Returns:
        tuple: (new_instances, old_instances) lists
    """
    new_instances = []
    old_instances = []

    if check_enabled:
        for i in props["instances"]:
            if is_using_current_spec(i, props):
                new_instances.append(i)
            else:
                old_instances.append(i)
    else:
        module.debug(f"Comparing initial instances with current: {(*initial_instances,)}")
        for i in props["instances"]:
            if i not in initial_instances:
                new_instances.append(i)
            else:
                old_instances.append(i)

    module.debug(f"New instances: {len(new_instances)}, {(*new_instances,)}")
    module.debug(f"Old instances: {len(old_instances)}, {(*old_instances,)}")

    return new_instances, old_instances


def get_instances_by_launch_config(props, lc_check, initial_instances):
    return _get_instances_by_launch_spec(props, lc_check, initial_instances, _is_instance_using_launch_config)


def get_instances_by_launch_template(props, lt_check, initial_instances):
    return _get_instances_by_launch_spec(props, lt_check, initial_instances, _is_instance_using_launch_template)


def _should_terminate_instance_for_launch_config(
    instance_id: str, props: dict[str, Any], lc_check: bool, initial_instances: list[str]
) -> bool:
    """
    Determine if an instance should be terminated based on launch configuration.

    Args:
        instance_id: Instance ID to check
        props: ASG properties including instance facts
        lc_check: Whether to check if instance has current launch config
        initial_instances: List of initial instance IDs

    Returns:
        bool: True if instance should be terminated
    """
    if not lc_check:
        return instance_id in initial_instances

    instance_facts = props["instance_facts"][instance_id]

    # Terminate if migrating from launch template to launch config
    if "launch_template" in instance_facts:
        return True

    # Terminate if instance has different launch config
    if instance_facts.get("launch_config_name") != props.get("launch_config_name"):
        return True

    return False


def _should_terminate_instance_for_launch_template(
    instance_id: str, props: dict[str, Any], lt_check: bool, initial_instances: list[str]
) -> bool:
    """
    Determine if an instance should be terminated based on launch template.

    Args:
        instance_id: Instance ID to check
        props: ASG properties including instance facts
        lt_check: Whether to check if instance has current launch template
        initial_instances: List of initial instance IDs

    Returns:
        bool: True if instance should be terminated
    """
    if not lt_check:
        return instance_id in initial_instances

    instance_facts = props["instance_facts"][instance_id]

    # Terminate if migrating from launch config to launch template
    if "launch_config_name" in instance_facts:
        return True

    # Terminate if instance has different launch template
    if instance_facts.get("launch_template") != props.get("launch_template"):
        return True

    return False


def list_purgeable_instances(props, lc_check, lt_check, replace_instances, initial_instances):
    """
    Identify instances that should be terminated during replacement.

    Args:
        props: ASG properties including instance facts
        lc_check: Whether to check launch config matches
        lt_check: Whether to check launch template matches
        replace_instances: List of instance IDs to potentially replace
        initial_instances: List of initial instance IDs

    Returns:
        list: Instance IDs that should be terminated
    """
    instances_to_terminate = []
    # Filter to only instances that are actually in the ASG
    instances = [inst_id for inst_id in replace_instances if inst_id in props["instances"]]

    if "launch_config_name" in module.params:
        instances_to_terminate = [
            i for i in instances if _should_terminate_instance_for_launch_config(i, props, lc_check, initial_instances)
        ]
    elif "launch_template" in module.params:
        instances_to_terminate = [
            i
            for i in instances
            if _should_terminate_instance_for_launch_template(i, props, lt_check, initial_instances)
        ]

    return instances_to_terminate


def terminate_batch(connection, replace_instances, initial_instances, leftovers=False):
    batch_size = module.params.get("replace_batch_size")
    min_size = module.params.get("min_size")
    desired_capacity = module.params.get("desired_capacity")
    group_name = module.params.get("name")
    lc_check = module.params.get("lc_check")
    lt_check = module.params.get("lt_check")
    decrement_capacity = False
    break_loop = False

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    desired_capacity = _default_if_none(desired_capacity, as_group["DesiredCapacity"])

    props = get_properties(as_group)
    desired_size = as_group["MinSize"]
    if module.params.get("launch_config_name"):
        new_instances, old_instances = get_instances_by_launch_config(props, lc_check, initial_instances)
    else:
        new_instances, old_instances = get_instances_by_launch_template(props, lt_check, initial_instances)
    num_new_inst_needed = desired_capacity - len(new_instances)

    # check to make sure instances given are actually in the given ASG
    # and they have a non-current launch config
    instances_to_terminate = list_purgeable_instances(props, lc_check, lt_check, replace_instances, initial_instances)

    module.debug(f"new instances needed: {num_new_inst_needed}")
    module.debug(f"new instances: {(*new_instances,)}")
    module.debug(f"old instances: {(*old_instances,)}")
    module.debug(f"batch instances: {(*instances_to_terminate,)}")

    if num_new_inst_needed == 0:
        decrement_capacity = True
        if as_group["MinSize"] != min_size:
            min_size = _default_if_none(min_size, as_group["MinSize"])
            updated_params = dict(AutoScalingGroupName=as_group["AutoScalingGroupName"], MinSize=min_size)
            update_asg(connection, **updated_params)
            module.debug(f"Updating minimum size back to original of {min_size}")
        # if are some leftover old instances, but we are already at capacity with new ones
        # we don't want to decrement capacity
        if leftovers:
            decrement_capacity = False
        break_loop = True
        instances_to_terminate = old_instances
        desired_size = min_size
        module.debug("No new instances needed")

    if num_new_inst_needed < batch_size and num_new_inst_needed != 0:
        instances_to_terminate = instances_to_terminate[:num_new_inst_needed]
        decrement_capacity = False
        break_loop = False
        module.debug(f"{num_new_inst_needed} new instances needed")

    module.debug(f"decrementing capacity: {decrement_capacity}")

    for instance_id in instances_to_terminate:
        elb_dreg(connection, group_name, instance_id)
        module.debug(f"terminating instance: {instance_id}")
        terminate_asg_instance(connection, instance_id, decrement_capacity)

    # we wait to make sure the machines we marked as Unhealthy are
    # no longer in the list

    return break_loop, desired_size, instances_to_terminate


def wait_for_term_inst(connection, term_instances):
    wait_timeout = module.params.get("wait_timeout")
    group_name = module.params.get("name")
    count = 1
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and count > 0:
        module.debug("waiting for instances to terminate")
        count = 0
        as_group = describe_autoscaling_groups(connection, group_name)[0]
        props = get_properties(as_group)
        instance_facts = props["instance_facts"]
        instances = (i for i in instance_facts if i in term_instances)
        for i in instances:
            lifecycle = instance_facts[i]["lifecycle_state"]
            health = instance_facts[i]["health_status"]
            module.debug(f"Instance {i} has state of {lifecycle},{health}")
            if lifecycle.startswith("Terminating") or health == "Unhealthy":
                count += 1
        time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg=f"Waited too long for old instances to terminate. {time.asctime()}")


@AutoScalingErrorHandler.common_error_handler("wait for viable instances")
def wait_for_new_inst(connection, group_name, wait_timeout, desired_size, prop):
    """
    Wait for a minimum number of viable instances in an ASG.

    Args:
        connection: AutoScaling connection
        group_name: Name of the ASG
        wait_timeout: Wait timeout in seconds
        desired_size: Minimum number of viable instances required
        prop: Property to wait for (always "viable_instances")

    Returns:
        dict: ASG properties after waiting completes
    """
    module.debug(f"Waiting for {prop} >= {desired_size}")
    waiter_config = custom_waiter_config(timeout=wait_timeout, default_pause=10)
    waiter = get_min_viable_instances_waiter(connection, desired_size)
    waiter.wait(AutoScalingGroupNames=[group_name], WaiterConfig=waiter_config)

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    props = get_properties(as_group)
    module.debug(f"Reached {prop}: {props[prop]}")
    return props


def asg_exists(connection):
    group_name = module.params.get("name")
    as_group = describe_autoscaling_groups(connection, group_name)
    return bool(len(as_group))


def main():
    argument_spec = dict(
        name=dict(required=True, type="str", aliases=["group_name"]),
        load_balancers=dict(type="list", elements="str"),
        target_group_arns=dict(type="list", elements="str"),
        availability_zones=dict(type="list", elements="str"),
        launch_config_name=dict(type="str"),
        launch_template=dict(
            type="dict",
            default=None,
            options=dict(
                version=dict(type="str"),
                launch_template_name=dict(type="str"),
                launch_template_id=dict(type="str"),
            ),
        ),
        min_size=dict(type="int"),
        max_size=dict(type="int"),
        max_instance_lifetime=dict(type="int"),
        mixed_instances_policy=dict(
            type="dict",
            default=None,
            options=dict(
                instance_types=dict(type="list", elements="str"),
                instances_distribution=dict(
                    type="dict",
                    default=None,
                    options=dict(
                        on_demand_allocation_strategy=dict(type="str"),
                        on_demand_base_capacity=dict(type="int"),
                        on_demand_percentage_above_base_capacity=dict(type="int"),
                        spot_allocation_strategy=dict(type="str"),
                        spot_instance_pools=dict(type="int"),
                        spot_max_price=dict(type="str"),
                    ),
                ),
            ),
        ),
        placement_group=dict(type="str"),
        protected_from_scale_in=dict(type="bool", default=None),
        desired_capacity=dict(type="int"),
        vpc_zone_identifier=dict(type="list", elements="str"),
        replace_batch_size=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="int",
            default=1,
        ),
        replace_all_instances=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="bool",
            default=False,
        ),
        replace_instances=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="list",
            default=[],
            elements="str",
        ),
        detach_instances=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="list",
            default=[],
            elements="str",
        ),
        decrement_desired_capacity=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="bool",
            default=False,
        ),
        lc_check=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="bool",
            default=True,
        ),
        lt_check=dict(
            removed_in_version="14.0.0",
            removed_from_collection="amazon.aws",
            type="bool",
            default=True,
        ),
        wait_timeout=dict(type="int", default=300),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(type="list", default=[], elements="dict"),
        purge_tags=dict(type="bool", default=False),
        health_check_period=dict(type="int", default=300),
        health_check_type=dict(default="EC2", choices=["EC2", "ELB"]),
        default_cooldown=dict(type="int", default=300),
        wait_for_instances=dict(type="bool", default=True),
        termination_policies=dict(type="list", default="Default", elements="str"),
        notification_topic=dict(type="str", default=None),
        notification_types=dict(
            type="list",
            default=[
                "autoscaling:EC2_INSTANCE_LAUNCH",
                "autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
                "autoscaling:EC2_INSTANCE_TERMINATE",
                "autoscaling:EC2_INSTANCE_TERMINATE_ERROR",
            ],
            elements="str",
        ),
        suspend_processes=dict(type="list", default=[], elements="str"),
        metrics_collection=dict(type="bool", default=False),
        metrics_granularity=dict(type="str", default="1Minute"),
        metrics_list=dict(
            type="list",
            default=[
                "GroupMinSize",
                "GroupMaxSize",
                "GroupDesiredCapacity",
                "GroupInServiceInstances",
                "GroupPendingInstances",
                "GroupStandbyInstances",
                "GroupTerminatingInstances",
                "GroupTotalInstances",
            ],
            elements="str",
        ),
    )

    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ["replace_all_instances", "replace_instances"],
            ["replace_all_instances", "detach_instances"],
            ["launch_config_name", "launch_template"],
        ],
    )

    state = module.params.get("state")
    replace_instances = module.params.get("replace_instances")
    replace_all_instances = module.params.get("replace_all_instances")
    detach_instances = module.params.get("detach_instances")

    connection = module.client("autoscaling")
    changed = create_changed = replace_changed = detach_changed = False
    exists = asg_exists(connection)

    if state == "present":
        create_changed, asg_properties = create_autoscaling_group(connection)
    elif state == "absent":
        changed = delete_autoscaling_group(connection)
        module.exit_json(changed=changed)

    # Only replace instances if asg existed at start of call
    if (
        exists
        and (replace_all_instances or replace_instances)
        and (module.params.get("launch_config_name") or module.params.get("launch_template"))
    ):
        replace_changed, asg_properties = replace(connection)

    # Only detach instances if asg existed at start of call
    if (
        exists
        and (detach_instances)
        and (module.params.get("launch_config_name") or module.params.get("launch_template"))
    ):
        detach_changed, asg_properties = detach(connection)

    if create_changed or replace_changed or detach_changed:
        changed = True

    module.exit_json(changed=changed, **asg_properties)


if __name__ == "__main__":
    main()

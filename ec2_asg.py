#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_asg
version_added: 1.0.0
short_description: Create or delete AWS AutoScaling Groups (ASGs)
description:
  - Can create or delete AWS AutoScaling Groups.
  - Can be used with the M(community.aws.ec2_lc) module to manage Launch Configurations.
author: "Gareth Rushgrove (@garethr)"
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
      - Defaults to all the availability zones in the region if I(vpc_zone_identifier) is not set.
    type: list
    elements: str
  launch_config_name:
    description:
      - Name of the Launch configuration to use for the group. See the community.aws.ec2_lc) module for managing these.
      - If unspecified then the current group value will be used.  One of I(launch_config_name) or I(launch_template) must be provided.
    type: str
  launch_template:
    description:
      - Dictionary describing the Launch Template to use
    suboptions:
      version:
        description:
          - The version number of the launch template to use.
          - Defaults to latest version if not provided.
        type: str
      launch_template_name:
        description:
          - The name of the launch template. Only one of I(launch_template_name) or I(launch_template_id) is required.
        type: str
      launch_template_id:
        description:
          - The id of the launch template. Only one of I(launch_template_name) or I(launch_template_id) is required.
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
      - Maximum instance lifetime must be equal to 0, between 604800 and 31536000 seconds (inclusive), or not specified.
      - Value of 0 removes lifetime restriction.
    type: int
  mixed_instances_policy:
    description:
      - A mixed instance policy to use for the ASG.
      - Only used when the ASG is configured to use a Launch Template (I(launch_template)).
      - 'See also U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-autoscaling-autoscalinggroup-mixedinstancespolicy.html)'
    required: false
    suboptions:
      instance_types:
        description:
          - A list of instance_types.
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
        suboptions:
          on_demand_allocation_strategy:
            description:
              - Indicates how to allocate instance types to fulfill On-Demand capacity.
            type: str
            required: false
            version_added: 1.5.0
          on_demand_base_capacity:
            description:
              - >-
                The minimum amount of the Auto Scaling group's capacity that must be fulfilled by On-Demand
                Instances. This base portion is provisioned first as your group scales.
              - >-
                Default if not set is 0. If you leave it set to 0, On-Demand Instances are launched as a
                percentage of the Auto Scaling group's desired capacity, per the OnDemandPercentageAboveBaseCapacity setting.
            type: int
            required: false
            version_added: 1.5.0
          on_demand_percentage_above_base_capacity:
            description:
              - Controls the percentages of On-Demand Instances and Spot Instances for your additional capacity beyond OnDemandBaseCapacity.
              - Default if not set is 100. If you leave it set to 100, the percentages are 100% for On-Demand Instances and 0% for Spot Instances.
              - 'Valid range: 0 to 100'
            type: int
            required: false
            version_added: 1.5.0
          spot_allocation_strategy:
            description:
              - Indicates how to allocate instances across Spot Instance pools.
            type: str
            required: false
            version_added: 1.5.0
          spot_instance_pools:
            description:
              - >-
                The number of Spot Instance pools across which to allocate your Spot Instances. The Spot pools are determined from
                the different instance types in the Overrides array of LaunchTemplate. Default if not set is 2.
              - Used only when the Spot allocation strategy is lowest-price.
              - 'Valid Range: Minimum value of 1. Maximum value of 20.'
            type: int
            required: false
            version_added: 1.5.0
          spot_max_price:
            description:
              - The maximum price per unit hour that you are willing to pay for a Spot Instance.
              - If you leave the value of this parameter blank (which is the default), the maximum Spot price is set at the On-Demand price.
              - To remove a value that you previously set, include the parameter but leave the value blank.
            type: str
            required: false
            version_added: 1.5.0
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
      - In a rolling fashion, replace all instances that used the old launch configuration with one from the new launch configuration.
        It increases the ASG size by I(replace_batch_size), waits for the new instances to be up and running.
        After that, it terminates a batch of old instances, waits for the replacements, and repeats, until all old instances are replaced.
        Once that's done the ASG size is reduced back to the expected size.
    default: false
    type: bool
  replace_batch_size:
    description:
      - Number of instances you'd like to replace at a time.  Used with I(replace_all_instances).
    required: false
    default: 1
    type: int
  replace_instances:
    description:
      - List of I(instance_ids) belonging to the named AutoScalingGroup that you would like to terminate and be replaced with instances
        matching the current launch configuration.
    type: list
    elements: str
  lc_check:
    description:
      - Check to make sure instances that are being replaced with I(replace_instances) do not already have the current I(launch_config).
    default: true
    type: bool
  lt_check:
    description:
      - Check to make sure instances that are being replaced with I(replace_instances) do not already have the current
        I(launch_template or I(launch_template) I(version).
    default: true
    type: bool
  vpc_zone_identifier:
    description:
      - List of VPC subnets to use
    type: list
    elements: str
  tags:
    description:
      - A list of tags to add to the Auto Scale Group.
      - Optional key is I(propagate_at_launch), which defaults to true.
      - When I(propagate_at_launch) is true the tags will be propagated to the Instances created.
    type: list
    elements: dict
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
        - Using I(termination_policies=Default) when modifying an existing AutoScalingGroup will result in the existing policy being retained
          instead of changed to C(Default).
        - 'Valid values include: C(Default), C(OldestInstance), C(NewestInstance), C(OldestLaunchConfiguration), C(ClosestToNextInstanceHour)'
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
      - C(Launch), C(Terminate), C(HealthCheck), C(ReplaceUnhealthy), C(AZRebalance), C(AlarmNotification), C(ScheduledActions), C(AddToLoadBalancer)
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
      - When I(metrics_collection=true) this will determine the granularity of metrics collected by CloudWatch.
    default: "1Minute"
    type: str
  metrics_list:
    description:
      - List of autoscaling metrics to collect when I(metrics_collection=true).
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
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Basic configuration with Launch Configuration

- community.aws.ec2_asg:
    name: special
    load_balancers: [ 'lb1', 'lb2' ]
    availability_zones: [ 'eu-west-1a', 'eu-west-1b' ]
    launch_config_name: 'lc-1'
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: [ 'subnet-abcd1234', 'subnet-1a2b3c4d' ]
    tags:
      - environment: production
        propagate_at_launch: no

# Rolling ASG Updates

# Below is an example of how to assign a new launch config to an ASG and terminate old instances.
#
# All instances in "myasg" that do not have the launch configuration named "my_new_lc" will be terminated in
# a rolling fashion with instances using the current launch configuration, "my_new_lc".
#
# This could also be considered a rolling deploy of a pre-baked AMI.
#
# If this is a newly created group, the instances will not be replaced since all instances
# will have the current launch configuration.

- name: create launch config
  community.aws.ec2_lc:
    name: my_new_lc
    image_id: ami-lkajsf
    key_name: mykey
    region: us-east-1
    security_groups: sg-23423
    instance_type: m1.small
    assign_public_ip: yes

- community.aws.ec2_asg:
    name: myasg
    launch_config_name: my_new_lc
    health_check_period: 60
    health_check_type: ELB
    replace_all_instances: yes
    min_size: 5
    max_size: 5
    desired_capacity: 5
    region: us-east-1

# To only replace a couple of instances instead of all of them, supply a list
# to "replace_instances":

- community.aws.ec2_asg:
    name: myasg
    launch_config_name: my_new_lc
    health_check_period: 60
    health_check_type: ELB
    replace_instances:
    - i-b345231
    - i-24c2931
    min_size: 5
    max_size: 5
    desired_capacity: 5
    region: us-east-1

# Basic Configuration with Launch Template

- community.aws.ec2_asg:
    name: special
    load_balancers: [ 'lb1', 'lb2' ]
    availability_zones: [ 'eu-west-1a', 'eu-west-1b' ]
    launch_template:
        version: '1'
        launch_template_name: 'lt-example'
        launch_template_id: 'lt-123456'
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: [ 'subnet-abcd1234', 'subnet-1a2b3c4d' ]
    tags:
      - environment: production
        propagate_at_launch: no

# Basic Configuration with Launch Template using mixed instance policy

- community.aws.ec2_asg:
    name: special
    load_balancers: [ 'lb1', 'lb2' ]
    availability_zones: [ 'eu-west-1a', 'eu-west-1b' ]
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
    vpc_zone_identifier: [ 'subnet-abcd1234', 'subnet-1a2b3c4d' ]
    tags:
      - environment: production
        propagate_at_launch: no
'''

RETURN = r'''
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
      provided for compatibility with ec2_asg module.
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
'''

import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import scrub_none_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

ASG_ATTRIBUTES = ('AvailabilityZones', 'DefaultCooldown', 'DesiredCapacity',
                  'HealthCheckGracePeriod', 'HealthCheckType', 'LaunchConfigurationName',
                  'LoadBalancerNames', 'MaxInstanceLifetime', 'MaxSize', 'MinSize',
                  'AutoScalingGroupName', 'PlacementGroup', 'TerminationPolicies',
                  'VPCZoneIdentifier')

INSTANCE_ATTRIBUTES = ('instance_id', 'health_status', 'lifecycle_state', 'launch_config_name')

backoff_params = dict(retries=10, delay=3, backoff=1.5)


@AWSRetry.jittered_backoff(**backoff_params)
def describe_autoscaling_groups(connection, group_name):
    pg = connection.get_paginator('describe_auto_scaling_groups')
    return pg.paginate(AutoScalingGroupNames=[group_name]).build_full_result().get('AutoScalingGroups', [])


@AWSRetry.jittered_backoff(**backoff_params)
def deregister_lb_instances(connection, lb_name, instance_id):
    connection.deregister_instances_from_load_balancer(LoadBalancerName=lb_name, Instances=[dict(InstanceId=instance_id)])


@AWSRetry.jittered_backoff(**backoff_params)
def describe_instance_health(connection, lb_name, instances):
    params = dict(LoadBalancerName=lb_name)
    if instances:
        params.update(Instances=instances)
    return connection.describe_instance_health(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def describe_target_health(connection, target_group_arn, instances):
    return connection.describe_target_health(TargetGroupArn=target_group_arn, Targets=instances)


@AWSRetry.jittered_backoff(**backoff_params)
def suspend_asg_processes(connection, asg_name, processes):
    connection.suspend_processes(AutoScalingGroupName=asg_name, ScalingProcesses=processes)


@AWSRetry.jittered_backoff(**backoff_params)
def resume_asg_processes(connection, asg_name, processes):
    connection.resume_processes(AutoScalingGroupName=asg_name, ScalingProcesses=processes)


@AWSRetry.jittered_backoff(**backoff_params)
def describe_launch_configurations(connection, launch_config_name):
    pg = connection.get_paginator('describe_launch_configurations')
    return pg.paginate(LaunchConfigurationNames=[launch_config_name]).build_full_result()


@AWSRetry.jittered_backoff(**backoff_params)
def describe_launch_templates(connection, launch_template):
    if launch_template['launch_template_id'] is not None:
        try:
            lt = connection.describe_launch_templates(LaunchTemplateIds=[launch_template['launch_template_id']])
            return lt
        except is_boto3_error_code('InvalidLaunchTemplateName.NotFoundException'):
            module.fail_json(msg="No launch template found matching: %s" % launch_template)
    else:
        try:
            lt = connection.describe_launch_templates(LaunchTemplateNames=[launch_template['launch_template_name']])
            return lt
        except is_boto3_error_code('InvalidLaunchTemplateName.NotFoundException'):
            module.fail_json(msg="No launch template found matching: %s" % launch_template)


@AWSRetry.jittered_backoff(**backoff_params)
def create_asg(connection, **params):
    connection.create_auto_scaling_group(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def put_notification_config(connection, asg_name, topic_arn, notification_types):
    connection.put_notification_configuration(
        AutoScalingGroupName=asg_name,
        TopicARN=topic_arn,
        NotificationTypes=notification_types
    )


@AWSRetry.jittered_backoff(**backoff_params)
def del_notification_config(connection, asg_name, topic_arn):
    connection.delete_notification_configuration(
        AutoScalingGroupName=asg_name,
        TopicARN=topic_arn
    )


@AWSRetry.jittered_backoff(**backoff_params)
def attach_load_balancers(connection, asg_name, load_balancers):
    connection.attach_load_balancers(AutoScalingGroupName=asg_name, LoadBalancerNames=load_balancers)


@AWSRetry.jittered_backoff(**backoff_params)
def detach_load_balancers(connection, asg_name, load_balancers):
    connection.detach_load_balancers(AutoScalingGroupName=asg_name, LoadBalancerNames=load_balancers)


@AWSRetry.jittered_backoff(**backoff_params)
def attach_lb_target_groups(connection, asg_name, target_group_arns):
    connection.attach_load_balancer_target_groups(AutoScalingGroupName=asg_name, TargetGroupARNs=target_group_arns)


@AWSRetry.jittered_backoff(**backoff_params)
def detach_lb_target_groups(connection, asg_name, target_group_arns):
    connection.detach_load_balancer_target_groups(AutoScalingGroupName=asg_name, TargetGroupARNs=target_group_arns)


@AWSRetry.jittered_backoff(**backoff_params)
def update_asg(connection, **params):
    connection.update_auto_scaling_group(**params)


@AWSRetry.jittered_backoff(catch_extra_error_codes=['ScalingActivityInProgress'], **backoff_params)
def delete_asg(connection, asg_name, force_delete):
    connection.delete_auto_scaling_group(AutoScalingGroupName=asg_name, ForceDelete=force_delete)


@AWSRetry.jittered_backoff(**backoff_params)
def terminate_asg_instance(connection, instance_id, decrement_capacity):
    connection.terminate_instance_in_auto_scaling_group(InstanceId=instance_id,
                                                        ShouldDecrementDesiredCapacity=decrement_capacity)


def enforce_required_arguments_for_create():
    ''' As many arguments are not required for autoscale group deletion
        they cannot be mandatory arguments for the module, so we enforce
        them here '''
    missing_args = []
    if module.params.get('launch_config_name') is None and module.params.get('launch_template') is None:
        module.fail_json(msg="Missing either launch_config_name or launch_template for autoscaling group create")
    for arg in ('min_size', 'max_size'):
        if module.params[arg] is None:
            missing_args.append(arg)
    if missing_args:
        module.fail_json(msg="Missing required arguments for autoscaling group create: %s" % ",".join(missing_args))


def get_properties(autoscaling_group):
    properties = dict(
        healthy_instances=0,
        in_service_instances=0,
        unhealthy_instances=0,
        pending_instances=0,
        viable_instances=0,
        terminating_instances=0
    )
    instance_facts = dict()
    autoscaling_group_instances = autoscaling_group.get('Instances')

    if autoscaling_group_instances:
        properties['instances'] = [i['InstanceId'] for i in autoscaling_group_instances]
        for i in autoscaling_group_instances:
            instance_facts[i['InstanceId']] = {
                'health_status': i['HealthStatus'],
                'lifecycle_state': i['LifecycleState']
            }
            if 'LaunchConfigurationName' in i:
                instance_facts[i['InstanceId']]['launch_config_name'] = i['LaunchConfigurationName']
            elif 'LaunchTemplate' in i:
                instance_facts[i['InstanceId']]['launch_template'] = i['LaunchTemplate']

            if i['HealthStatus'] == 'Healthy' and i['LifecycleState'] == 'InService':
                properties['viable_instances'] += 1

            if i['HealthStatus'] == 'Healthy':
                properties['healthy_instances'] += 1
            else:
                properties['unhealthy_instances'] += 1

            if i['LifecycleState'] == 'InService':
                properties['in_service_instances'] += 1
            if i['LifecycleState'] == 'Terminating':
                properties['terminating_instances'] += 1
            if i['LifecycleState'] == 'Pending':
                properties['pending_instances'] += 1
    else:
        properties['instances'] = []

    properties['auto_scaling_group_name'] = autoscaling_group.get('AutoScalingGroupName')
    properties['auto_scaling_group_arn'] = autoscaling_group.get('AutoScalingGroupARN')
    properties['availability_zones'] = autoscaling_group.get('AvailabilityZones')
    properties['created_time'] = autoscaling_group.get('CreatedTime')
    properties['instance_facts'] = instance_facts
    properties['load_balancers'] = autoscaling_group.get('LoadBalancerNames')
    if 'LaunchConfigurationName' in autoscaling_group:
        properties['launch_config_name'] = autoscaling_group.get('LaunchConfigurationName')
    else:
        properties['launch_template'] = autoscaling_group.get('LaunchTemplate')
    properties['tags'] = autoscaling_group.get('Tags')
    properties['max_instance_lifetime'] = autoscaling_group.get('MaxInstanceLifetime')
    properties['min_size'] = autoscaling_group.get('MinSize')
    properties['max_size'] = autoscaling_group.get('MaxSize')
    properties['desired_capacity'] = autoscaling_group.get('DesiredCapacity')
    properties['default_cooldown'] = autoscaling_group.get('DefaultCooldown')
    properties['healthcheck_grace_period'] = autoscaling_group.get('HealthCheckGracePeriod')
    properties['healthcheck_type'] = autoscaling_group.get('HealthCheckType')
    properties['default_cooldown'] = autoscaling_group.get('DefaultCooldown')
    properties['termination_policies'] = autoscaling_group.get('TerminationPolicies')
    properties['target_group_arns'] = autoscaling_group.get('TargetGroupARNs')
    properties['vpc_zone_identifier'] = autoscaling_group.get('VPCZoneIdentifier')
    raw_mixed_instance_object = autoscaling_group.get('MixedInstancesPolicy')
    if raw_mixed_instance_object:
        properties['mixed_instances_policy_full'] = camel_dict_to_snake_dict(raw_mixed_instance_object)
        properties['mixed_instances_policy'] = [x['InstanceType'] for x in raw_mixed_instance_object.get('LaunchTemplate').get('Overrides')]

    metrics = autoscaling_group.get('EnabledMetrics')
    if metrics:
        metrics.sort(key=lambda x: x["Metric"])
    properties['metrics_collection'] = metrics

    if properties['target_group_arns']:
        elbv2_connection = module.client('elbv2')
        tg_paginator = elbv2_connection.get_paginator('describe_target_groups')
        tg_result = tg_paginator.paginate(
            TargetGroupArns=properties['target_group_arns']
        ).build_full_result()
        target_groups = tg_result['TargetGroups']
    else:
        target_groups = []

    properties['target_group_names'] = [
        tg['TargetGroupName']
        for tg in target_groups
    ]

    return properties


def get_launch_object(connection, ec2_connection):
    launch_object = dict()
    launch_config_name = module.params.get('launch_config_name')
    launch_template = module.params.get('launch_template')
    mixed_instances_policy = module.params.get('mixed_instances_policy')
    if launch_config_name is None and launch_template is None:
        return launch_object
    elif launch_config_name:
        try:
            launch_configs = describe_launch_configurations(connection, launch_config_name)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to describe launch configurations")
        if len(launch_configs['LaunchConfigurations']) == 0:
            module.fail_json(msg="No launch config found with name %s" % launch_config_name)
        launch_object = {"LaunchConfigurationName": launch_configs['LaunchConfigurations'][0]['LaunchConfigurationName']}
        return launch_object
    elif launch_template:
        lt = describe_launch_templates(ec2_connection, launch_template)['LaunchTemplates'][0]
        if launch_template['version'] is not None:
            launch_object = {"LaunchTemplate": {"LaunchTemplateId": lt['LaunchTemplateId'], "Version": launch_template['version']}}
        else:
            launch_object = {"LaunchTemplate": {"LaunchTemplateId": lt['LaunchTemplateId'], "Version": str(lt['LatestVersionNumber'])}}

        if mixed_instances_policy:
            instance_types = mixed_instances_policy.get('instance_types', [])
            instances_distribution = mixed_instances_policy.get('instances_distribution', {})
            policy = {
                'LaunchTemplate': {
                    'LaunchTemplateSpecification': launch_object['LaunchTemplate']
                }
            }
            if instance_types:
                policy['LaunchTemplate']['Overrides'] = []
                for instance_type in instance_types:
                    instance_type_dict = {'InstanceType': instance_type}
                    policy['LaunchTemplate']['Overrides'].append(instance_type_dict)
            if instances_distribution:
                instances_distribution_params = scrub_none_parameters(instances_distribution)
                policy['InstancesDistribution'] = snake_dict_to_camel_dict(instances_distribution_params, capitalize_first=True)
            launch_object['MixedInstancesPolicy'] = policy
        return launch_object


def elb_dreg(asg_connection, group_name, instance_id):
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]
    wait_timeout = module.params.get('wait_timeout')
    count = 1
    if as_group['LoadBalancerNames'] and as_group['HealthCheckType'] == 'ELB':
        elb_connection = module.client('elb')
    else:
        return

    for lb in as_group['LoadBalancerNames']:
        deregister_lb_instances(elb_connection, lb, instance_id)
        module.debug("De-registering %s from ELB %s" % (instance_id, lb))

    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and count > 0:
        count = 0
        for lb in as_group['LoadBalancerNames']:
            lb_instances = describe_instance_health(elb_connection, lb, [])
            for i in lb_instances['InstanceStates']:
                if i['InstanceId'] == instance_id and i['State'] == "InService":
                    count += 1
                    module.debug("%s: %s, %s" % (i['InstanceId'], i['State'], i['Description']))
        time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg="Waited too long for instance to deregister. {0}".format(time.asctime()))


def elb_healthy(asg_connection, elb_connection, group_name):
    healthy_instances = set()
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]
    props = get_properties(as_group)
    # get healthy, inservice instances from ASG
    instances = []
    for instance, settings in props['instance_facts'].items():
        if settings['lifecycle_state'] == 'InService' and settings['health_status'] == 'Healthy':
            instances.append(dict(InstanceId=instance))
    module.debug("ASG considers the following instances InService and Healthy: %s" % instances)
    module.debug("ELB instance status:")
    lb_instances = list()
    for lb in as_group.get('LoadBalancerNames'):
        # we catch a race condition that sometimes happens if the instance exists in the ASG
        # but has not yet show up in the ELB
        try:
            lb_instances = describe_instance_health(elb_connection, lb, instances)
        except is_boto3_error_code('InvalidInstance'):
            return None
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to get load balancer.")

        for i in lb_instances.get('InstanceStates'):
            if i['State'] == "InService":
                healthy_instances.add(i['InstanceId'])
            module.debug("ELB Health State %s: %s" % (i['InstanceId'], i['State']))
    return len(healthy_instances)


def tg_healthy(asg_connection, elbv2_connection, group_name):
    healthy_instances = set()
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]
    props = get_properties(as_group)
    # get healthy, inservice instances from ASG
    instances = []
    for instance, settings in props['instance_facts'].items():
        if settings['lifecycle_state'] == 'InService' and settings['health_status'] == 'Healthy':
            instances.append(dict(Id=instance))
    module.debug("ASG considers the following instances InService and Healthy: %s" % instances)
    module.debug("Target Group instance status:")
    tg_instances = list()
    for tg in as_group.get('TargetGroupARNs'):
        # we catch a race condition that sometimes happens if the instance exists in the ASG
        # but has not yet show up in the ELB
        try:
            tg_instances = describe_target_health(elbv2_connection, tg, instances)
        except is_boto3_error_code('InvalidInstance'):
            return None
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to get target group.")

        for i in tg_instances.get('TargetHealthDescriptions'):
            if i['TargetHealth']['State'] == "healthy":
                healthy_instances.add(i['Target']['Id'])
            module.debug("Target Group Health State %s: %s" % (i['Target']['Id'], i['TargetHealth']['State']))
    return len(healthy_instances)


def wait_for_elb(asg_connection, group_name):
    wait_timeout = module.params.get('wait_timeout')

    # if the health_check_type is ELB, we want to query the ELBs directly for instance
    # status as to avoid health_check_grace period that is awarded to ASG instances
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]

    if as_group.get('LoadBalancerNames') and as_group.get('HealthCheckType') == 'ELB':
        module.debug("Waiting for ELB to consider instances healthy.")
        elb_connection = module.client('elb')

        wait_timeout = time.time() + wait_timeout
        healthy_instances = elb_healthy(asg_connection, elb_connection, group_name)

        while healthy_instances < as_group.get('MinSize') and wait_timeout > time.time():
            healthy_instances = elb_healthy(asg_connection, elb_connection, group_name)
            module.debug("ELB thinks %s instances are healthy." % healthy_instances)
            time.sleep(10)
        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="Waited too long for ELB instances to be healthy. %s" % time.asctime())
        module.debug("Waiting complete. ELB thinks %s instances are healthy." % healthy_instances)


def wait_for_target_group(asg_connection, group_name):
    wait_timeout = module.params.get('wait_timeout')

    # if the health_check_type is ELB, we want to query the ELBs directly for instance
    # status as to avoid health_check_grace period that is awarded to ASG instances
    as_group = describe_autoscaling_groups(asg_connection, group_name)[0]

    if as_group.get('TargetGroupARNs') and as_group.get('HealthCheckType') == 'ELB':
        module.debug("Waiting for Target Group to consider instances healthy.")
        elbv2_connection = module.client('elbv2')

        wait_timeout = time.time() + wait_timeout
        healthy_instances = tg_healthy(asg_connection, elbv2_connection, group_name)

        while healthy_instances < as_group.get('MinSize') and wait_timeout > time.time():
            healthy_instances = tg_healthy(asg_connection, elbv2_connection, group_name)
            module.debug("Target Group thinks %s instances are healthy." % healthy_instances)
            time.sleep(10)
        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="Waited too long for ELB instances to be healthy. %s" % time.asctime())
        module.debug("Waiting complete. Target Group thinks %s instances are healthy." % healthy_instances)


def suspend_processes(ec2_connection, as_group):
    suspend_processes = set(module.params.get('suspend_processes'))

    try:
        suspended_processes = set([p['ProcessName'] for p in as_group['SuspendedProcesses']])
    except AttributeError:
        # New ASG being created, no suspended_processes defined yet
        suspended_processes = set()

    if suspend_processes == suspended_processes:
        return False

    resume_processes = list(suspended_processes - suspend_processes)
    if resume_processes:
        resume_asg_processes(ec2_connection, module.params.get('name'), resume_processes)

    if suspend_processes:
        suspend_asg_processes(ec2_connection, module.params.get('name'), list(suspend_processes))

    return True


def create_autoscaling_group(connection):
    group_name = module.params.get('name')
    load_balancers = module.params['load_balancers']
    target_group_arns = module.params['target_group_arns']
    availability_zones = module.params['availability_zones']
    launch_config_name = module.params.get('launch_config_name')
    launch_template = module.params.get('launch_template')
    mixed_instances_policy = module.params.get('mixed_instances_policy')
    min_size = module.params['min_size']
    max_size = module.params['max_size']
    max_instance_lifetime = module.params.get('max_instance_lifetime')
    placement_group = module.params.get('placement_group')
    desired_capacity = module.params.get('desired_capacity')
    vpc_zone_identifier = module.params.get('vpc_zone_identifier')
    set_tags = module.params.get('tags')
    health_check_period = module.params.get('health_check_period')
    health_check_type = module.params.get('health_check_type')
    default_cooldown = module.params.get('default_cooldown')
    wait_for_instances = module.params.get('wait_for_instances')
    wait_timeout = module.params.get('wait_timeout')
    termination_policies = module.params.get('termination_policies')
    notification_topic = module.params.get('notification_topic')
    notification_types = module.params.get('notification_types')
    metrics_collection = module.params.get('metrics_collection')
    metrics_granularity = module.params.get('metrics_granularity')
    metrics_list = module.params.get('metrics_list')

    try:
        as_groups = describe_autoscaling_groups(connection, group_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe auto scaling groups.")

    ec2_connection = module.client('ec2')

    if vpc_zone_identifier:
        vpc_zone_identifier = ','.join(vpc_zone_identifier)

    asg_tags = []
    for tag in set_tags:
        for k, v in tag.items():
            if k != 'propagate_at_launch':
                asg_tags.append(dict(Key=k,
                                     Value=to_native(v),
                                     PropagateAtLaunch=bool(tag.get('propagate_at_launch', True)),
                                     ResourceType='auto-scaling-group',
                                     ResourceId=group_name))
    if not as_groups:
        if not vpc_zone_identifier and not availability_zones:
            availability_zones = module.params['availability_zones'] = [zone['ZoneName'] for
                                                                        zone in ec2_connection.describe_availability_zones()['AvailabilityZones']]

        enforce_required_arguments_for_create()

        if desired_capacity is None:
            desired_capacity = min_size
        ag = dict(
            AutoScalingGroupName=group_name,
            MinSize=min_size,
            MaxSize=max_size,
            DesiredCapacity=desired_capacity,
            Tags=asg_tags,
            HealthCheckGracePeriod=health_check_period,
            HealthCheckType=health_check_type,
            DefaultCooldown=default_cooldown,
            TerminationPolicies=termination_policies)
        if vpc_zone_identifier:
            ag['VPCZoneIdentifier'] = vpc_zone_identifier
        if availability_zones:
            ag['AvailabilityZones'] = availability_zones
        if placement_group:
            ag['PlacementGroup'] = placement_group
        if load_balancers:
            ag['LoadBalancerNames'] = load_balancers
        if target_group_arns:
            ag['TargetGroupARNs'] = target_group_arns
        if max_instance_lifetime:
            ag['MaxInstanceLifetime'] = max_instance_lifetime

        launch_object = get_launch_object(connection, ec2_connection)
        if 'LaunchConfigurationName' in launch_object:
            ag['LaunchConfigurationName'] = launch_object['LaunchConfigurationName']
        elif 'LaunchTemplate' in launch_object:
            if 'MixedInstancesPolicy' in launch_object:
                ag['MixedInstancesPolicy'] = launch_object['MixedInstancesPolicy']
            else:
                ag['LaunchTemplate'] = launch_object['LaunchTemplate']
        else:
            module.fail_json_aws(e, msg="Missing LaunchConfigurationName or LaunchTemplate")

        try:
            create_asg(connection, **ag)
            if metrics_collection:
                connection.enable_metrics_collection(AutoScalingGroupName=group_name, Granularity=metrics_granularity, Metrics=metrics_list)

            all_ag = describe_autoscaling_groups(connection, group_name)
            if len(all_ag) == 0:
                module.fail_json(msg="No auto scaling group found with the name %s" % group_name)
            as_group = all_ag[0]
            suspend_processes(connection, as_group)
            if wait_for_instances:
                wait_for_new_inst(connection, group_name, wait_timeout, desired_capacity, 'viable_instances')
                if load_balancers:
                    wait_for_elb(connection, group_name)
                # Wait for target group health if target group(s)defined
                if target_group_arns:
                    wait_for_target_group(connection, group_name)
            if notification_topic:
                put_notification_config(connection, group_name, notification_topic, notification_types)
            as_group = describe_autoscaling_groups(connection, group_name)[0]
            asg_properties = get_properties(as_group)
            changed = True
            return changed, asg_properties
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to create Autoscaling Group.")
    else:
        as_group = as_groups[0]
        initial_asg_properties = get_properties(as_group)
        changed = False

        if suspend_processes(connection, as_group):
            changed = True

        # process tag changes
        if len(set_tags) > 0:
            have_tags = as_group.get('Tags')
            want_tags = asg_tags
            if have_tags:
                have_tags.sort(key=lambda x: x["Key"])
            if want_tags:
                want_tags.sort(key=lambda x: x["Key"])
            dead_tags = []
            have_tag_keyvals = [x['Key'] for x in have_tags]
            want_tag_keyvals = [x['Key'] for x in want_tags]

            for dead_tag in set(have_tag_keyvals).difference(want_tag_keyvals):
                changed = True
                dead_tags.append(dict(ResourceId=as_group['AutoScalingGroupName'],
                                      ResourceType='auto-scaling-group', Key=dead_tag))
                have_tags = [have_tag for have_tag in have_tags if have_tag['Key'] != dead_tag]
            if dead_tags:
                connection.delete_tags(Tags=dead_tags)

            zipped = zip(have_tags, want_tags)
            if len(have_tags) != len(want_tags) or not all(x == y for x, y in zipped):
                changed = True
                connection.create_or_update_tags(Tags=asg_tags)

        # Handle load balancer attachments/detachments
        # Attach load balancers if they are specified but none currently exist
        if load_balancers and not as_group['LoadBalancerNames']:
            changed = True
            try:
                attach_load_balancers(connection, group_name, load_balancers)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to update Autoscaling Group.")

        # Update load balancers if they are specified and one or more already exists
        elif as_group['LoadBalancerNames']:
            change_load_balancers = load_balancers is not None
            # Get differences
            if not load_balancers:
                load_balancers = list()
            wanted_elbs = set(load_balancers)

            has_elbs = set(as_group['LoadBalancerNames'])
            # check if all requested are already existing
            if has_elbs - wanted_elbs and change_load_balancers:
                # if wanted contains less than existing, then we need to delete some
                elbs_to_detach = has_elbs.difference(wanted_elbs)
                if elbs_to_detach:
                    changed = True
                    try:
                        detach_load_balancers(connection, group_name, list(elbs_to_detach))
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, msg="Failed to detach load balancers {0}".format(elbs_to_detach))
            if wanted_elbs - has_elbs:
                # if has contains less than wanted, then we need to add some
                elbs_to_attach = wanted_elbs.difference(has_elbs)
                if elbs_to_attach:
                    changed = True
                    try:
                        attach_load_balancers(connection, group_name, list(elbs_to_attach))
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, msg="Failed to attach load balancers {0}".format(elbs_to_attach))

        # Handle target group attachments/detachments
        # Attach target groups if they are specified but none currently exist
        if target_group_arns and not as_group['TargetGroupARNs']:
            changed = True
            try:
                attach_lb_target_groups(connection, group_name, target_group_arns)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to update Autoscaling Group.")
        # Update target groups if they are specified and one or more already exists
        elif target_group_arns is not None and as_group['TargetGroupARNs']:
            # Get differences
            wanted_tgs = set(target_group_arns)
            has_tgs = set(as_group['TargetGroupARNs'])

            tgs_to_detach = has_tgs.difference(wanted_tgs)
            if tgs_to_detach:
                changed = True
                try:
                    detach_lb_target_groups(connection, group_name, list(tgs_to_detach))
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Failed to detach load balancer target groups {0}".format(tgs_to_detach))

            tgs_to_attach = wanted_tgs.difference(has_tgs)
            if tgs_to_attach:
                changed = True
                try:
                    attach_lb_target_groups(connection, group_name, list(tgs_to_attach))
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json(msg="Failed to attach load balancer target groups {0}".format(tgs_to_attach))

        # check for attributes that aren't required for updating an existing ASG
        # check if min_size/max_size/desired capacity have been specified and if not use ASG values
        if min_size is None:
            min_size = as_group['MinSize']
        if max_size is None:
            max_size = as_group['MaxSize']
        if desired_capacity is None:
            desired_capacity = as_group['DesiredCapacity']
        ag = dict(
            AutoScalingGroupName=group_name,
            MinSize=min_size,
            MaxSize=max_size,
            DesiredCapacity=desired_capacity,
            HealthCheckGracePeriod=health_check_period,
            HealthCheckType=health_check_type,
            DefaultCooldown=default_cooldown,
            TerminationPolicies=termination_policies)

        # Get the launch object (config or template) if one is provided in args or use the existing one attached to ASG if not.
        launch_object = get_launch_object(connection, ec2_connection)
        if 'LaunchConfigurationName' in launch_object:
            ag['LaunchConfigurationName'] = launch_object['LaunchConfigurationName']
        elif 'LaunchTemplate' in launch_object:
            if 'MixedInstancesPolicy' in launch_object:
                ag['MixedInstancesPolicy'] = launch_object['MixedInstancesPolicy']
            else:
                ag['LaunchTemplate'] = launch_object['LaunchTemplate']
        else:
            try:
                ag['LaunchConfigurationName'] = as_group['LaunchConfigurationName']
            except Exception:
                launch_template = as_group['LaunchTemplate']
                # Prefer LaunchTemplateId over Name as it's more specific.  Only one can be used for update_asg.
                ag['LaunchTemplate'] = {"LaunchTemplateId": launch_template['LaunchTemplateId'], "Version": launch_template['Version']}

        if availability_zones:
            ag['AvailabilityZones'] = availability_zones
        if vpc_zone_identifier:
            ag['VPCZoneIdentifier'] = vpc_zone_identifier
        if max_instance_lifetime is not None:
            ag['MaxInstanceLifetime'] = max_instance_lifetime

        try:
            update_asg(connection, **ag)

            if metrics_collection:
                connection.enable_metrics_collection(AutoScalingGroupName=group_name, Granularity=metrics_granularity, Metrics=metrics_list)
            else:
                connection.disable_metrics_collection(AutoScalingGroupName=group_name, Metrics=metrics_list)

        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to update autoscaling group")

        if notification_topic:
            try:
                put_notification_config(connection, group_name, notification_topic, notification_types)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to update Autoscaling Group notifications.")
        if wait_for_instances:
            wait_for_new_inst(connection, group_name, wait_timeout, desired_capacity, 'viable_instances')
            # Wait for ELB health if ELB(s)defined
            if load_balancers:
                module.debug('\tWAITING FOR ELB HEALTH')
                wait_for_elb(connection, group_name)
            # Wait for target group health if target group(s)defined

            if target_group_arns:
                module.debug('\tWAITING FOR TG HEALTH')
                wait_for_target_group(connection, group_name)

        try:
            as_group = describe_autoscaling_groups(connection, group_name)[0]
            asg_properties = get_properties(as_group)
            if asg_properties != initial_asg_properties:
                changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to read existing Autoscaling Groups.")
        return changed, asg_properties


def delete_autoscaling_group(connection):
    group_name = module.params.get('name')
    notification_topic = module.params.get('notification_topic')
    wait_for_instances = module.params.get('wait_for_instances')
    wait_timeout = module.params.get('wait_timeout')

    if notification_topic:
        del_notification_config(connection, group_name, notification_topic)
    groups = describe_autoscaling_groups(connection, group_name)
    if groups:
        wait_timeout = time.time() + wait_timeout
        if not wait_for_instances:
            delete_asg(connection, group_name, force_delete=True)
        else:
            updated_params = dict(AutoScalingGroupName=group_name, MinSize=0, MaxSize=0, DesiredCapacity=0)
            update_asg(connection, **updated_params)
            instances = True
            while instances and wait_for_instances and wait_timeout >= time.time():
                tmp_groups = describe_autoscaling_groups(connection, group_name)
                if tmp_groups:
                    tmp_group = tmp_groups[0]
                    if not tmp_group.get('Instances'):
                        instances = False
                time.sleep(10)

            if wait_timeout <= time.time():
                # waiting took too long
                module.fail_json(msg="Waited too long for old instances to terminate. %s" % time.asctime())

            delete_asg(connection, group_name, force_delete=False)
        while describe_autoscaling_groups(connection, group_name) and wait_timeout >= time.time():
            time.sleep(5)
        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="Waited too long for ASG to delete. %s" % time.asctime())
        return True

    return False


def get_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def update_size(connection, group, max_size, min_size, dc):
    module.debug("setting ASG sizes")
    module.debug("minimum size: %s, desired_capacity: %s, max size: %s" % (min_size, dc, max_size))
    updated_group = dict()
    updated_group['AutoScalingGroupName'] = group['AutoScalingGroupName']
    updated_group['MinSize'] = min_size
    updated_group['MaxSize'] = max_size
    updated_group['DesiredCapacity'] = dc
    update_asg(connection, **updated_group)


def replace(connection):
    batch_size = module.params.get('replace_batch_size')
    wait_timeout = module.params.get('wait_timeout')
    wait_for_instances = module.params.get('wait_for_instances')
    group_name = module.params.get('name')
    max_size = module.params.get('max_size')
    min_size = module.params.get('min_size')
    desired_capacity = module.params.get('desired_capacity')
    launch_config_name = module.params.get('launch_config_name')
    # Required to maintain the default value being set to 'true'
    if launch_config_name:
        lc_check = module.params.get('lc_check')
    else:
        lc_check = False
    # Mirror above behavior for Launch Templates
    launch_template = module.params.get('launch_template')
    if launch_template:
        lt_check = module.params.get('lt_check')
    else:
        lt_check = False
    replace_instances = module.params.get('replace_instances')
    replace_all_instances = module.params.get('replace_all_instances')

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    if desired_capacity is None:
        desired_capacity = as_group['DesiredCapacity']

    if wait_for_instances:
        wait_for_new_inst(connection, group_name, wait_timeout, as_group['MinSize'], 'viable_instances')

    props = get_properties(as_group)
    instances = props['instances']
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
            module.debug("Overriding batch size to %s" % num_new_inst_needed)
            batch_size = num_new_inst_needed

    if not old_instances:
        changed = False
        return changed, props

    # check if min_size/max_size/desired capacity have been specified and if not use ASG values
    if min_size is None:
        min_size = as_group['MinSize']
    if max_size is None:
        max_size = as_group['MaxSize']

    # set temporary settings and wait for them to be reached
    # This should get overwritten if the number of instances left is less than the batch size.

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    update_size(connection, as_group, max_size + batch_size, min_size + batch_size, desired_capacity + batch_size)

    if wait_for_instances:
        wait_for_new_inst(connection, group_name, wait_timeout, as_group['MinSize'] + batch_size, 'viable_instances')
        wait_for_elb(connection, group_name)
        wait_for_target_group(connection, group_name)

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    props = get_properties(as_group)
    instances = props['instances']
    if replace_instances:
        instances = replace_instances

    module.debug("beginning main loop")
    for i in get_chunks(instances, batch_size):
        # break out of this loop if we have enough new instances
        break_early, desired_size, term_instances = terminate_batch(connection, i, instances, False)

        if wait_for_instances:
            wait_for_term_inst(connection, term_instances)
            wait_for_new_inst(connection, group_name, wait_timeout, desired_size, 'viable_instances')
            wait_for_elb(connection, group_name)
            wait_for_target_group(connection, group_name)

        if break_early:
            module.debug("breaking loop")
            break

    update_size(connection, as_group, max_size, min_size, desired_capacity)
    as_group = describe_autoscaling_groups(connection, group_name)[0]
    asg_properties = get_properties(as_group)
    module.debug("Rolling update complete.")
    changed = True
    return changed, asg_properties


def get_instances_by_launch_config(props, lc_check, initial_instances):
    new_instances = []
    old_instances = []
    # old instances are those that have the old launch config
    if lc_check:
        for i in props['instances']:
            # Check if migrating from launch_template to launch_config first
            if 'launch_template' in props['instance_facts'][i]:
                old_instances.append(i)
            elif props['instance_facts'][i].get('launch_config_name') == props['launch_config_name']:
                new_instances.append(i)
            else:
                old_instances.append(i)

    else:
        module.debug("Comparing initial instances with current: %s" % initial_instances)
        for i in props['instances']:
            if i not in initial_instances:
                new_instances.append(i)
            else:
                old_instances.append(i)

    module.debug("New instances: %s, %s" % (len(new_instances), new_instances))
    module.debug("Old instances: %s, %s" % (len(old_instances), old_instances))

    return new_instances, old_instances


def get_instances_by_launch_template(props, lt_check, initial_instances):
    new_instances = []
    old_instances = []
    # old instances are those that have the old launch template or version of the same launch template
    if lt_check:
        for i in props['instances']:
            # Check if migrating from launch_config_name to launch_template_name first
            if 'launch_config_name' in props['instance_facts'][i]:
                old_instances.append(i)
            elif props['instance_facts'][i].get('launch_template') == props['launch_template']:
                new_instances.append(i)
            else:
                old_instances.append(i)
    else:
        module.debug("Comparing initial instances with current: %s" % initial_instances)
        for i in props['instances']:
            if i not in initial_instances:
                new_instances.append(i)
            else:
                old_instances.append(i)

    module.debug("New instances: %s, %s" % (len(new_instances), new_instances))
    module.debug("Old instances: %s, %s" % (len(old_instances), old_instances))

    return new_instances, old_instances


def list_purgeable_instances(props, lc_check, lt_check, replace_instances, initial_instances):
    instances_to_terminate = []
    instances = (inst_id for inst_id in replace_instances if inst_id in props['instances'])
    # check to make sure instances given are actually in the given ASG
    # and they have a non-current launch config
    if 'launch_config_name' in module.params:
        if lc_check:
            for i in instances:
                if (
                    'launch_template' in props['instance_facts'][i]
                    or props['instance_facts'][i]['launch_config_name'] != props['launch_config_name']
                ):
                    instances_to_terminate.append(i)
        else:
            for i in instances:
                if i in initial_instances:
                    instances_to_terminate.append(i)
    elif 'launch_template' in module.params:
        if lt_check:
            for i in instances:
                if (
                    'launch_config_name' in props['instance_facts'][i]
                    or props['instance_facts'][i]['launch_template'] != props['launch_template']
                ):
                    instances_to_terminate.append(i)
        else:
            for i in instances:
                if i in initial_instances:
                    instances_to_terminate.append(i)

    return instances_to_terminate


def terminate_batch(connection, replace_instances, initial_instances, leftovers=False):
    batch_size = module.params.get('replace_batch_size')
    min_size = module.params.get('min_size')
    desired_capacity = module.params.get('desired_capacity')
    group_name = module.params.get('name')
    lc_check = module.params.get('lc_check')
    lt_check = module.params.get('lt_check')
    decrement_capacity = False
    break_loop = False

    as_group = describe_autoscaling_groups(connection, group_name)[0]
    if desired_capacity is None:
        desired_capacity = as_group['DesiredCapacity']

    props = get_properties(as_group)
    desired_size = as_group['MinSize']
    if module.params.get('launch_config_name'):
        new_instances, old_instances = get_instances_by_launch_config(props, lc_check, initial_instances)
    else:
        new_instances, old_instances = get_instances_by_launch_template(props, lt_check, initial_instances)
    num_new_inst_needed = desired_capacity - len(new_instances)

    # check to make sure instances given are actually in the given ASG
    # and they have a non-current launch config
    instances_to_terminate = list_purgeable_instances(props, lc_check, lt_check, replace_instances, initial_instances)

    module.debug("new instances needed: %s" % num_new_inst_needed)
    module.debug("new instances: %s" % new_instances)
    module.debug("old instances: %s" % old_instances)
    module.debug("batch instances: %s" % ",".join(instances_to_terminate))

    if num_new_inst_needed == 0:
        decrement_capacity = True
        if as_group['MinSize'] != min_size:
            if min_size is None:
                min_size = as_group['MinSize']
            updated_params = dict(AutoScalingGroupName=as_group['AutoScalingGroupName'], MinSize=min_size)
            update_asg(connection, **updated_params)
            module.debug("Updating minimum size back to original of %s" % min_size)
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
        module.debug("%s new instances needed" % num_new_inst_needed)

    module.debug("decrementing capacity: %s" % decrement_capacity)

    for instance_id in instances_to_terminate:
        elb_dreg(connection, group_name, instance_id)
        module.debug("terminating instance: %s" % instance_id)
        terminate_asg_instance(connection, instance_id, decrement_capacity)

    # we wait to make sure the machines we marked as Unhealthy are
    # no longer in the list

    return break_loop, desired_size, instances_to_terminate


def wait_for_term_inst(connection, term_instances):
    wait_timeout = module.params.get('wait_timeout')
    group_name = module.params.get('name')
    as_group = describe_autoscaling_groups(connection, group_name)[0]
    count = 1
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and count > 0:
        module.debug("waiting for instances to terminate")
        count = 0
        as_group = describe_autoscaling_groups(connection, group_name)[0]
        props = get_properties(as_group)
        instance_facts = props['instance_facts']
        instances = (i for i in instance_facts if i in term_instances)
        for i in instances:
            lifecycle = instance_facts[i]['lifecycle_state']
            health = instance_facts[i]['health_status']
            module.debug("Instance %s has state of %s,%s" % (i, lifecycle, health))
            if lifecycle.startswith('Terminating') or health == 'Unhealthy':
                count += 1
        time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg="Waited too long for old instances to terminate. %s" % time.asctime())


def wait_for_new_inst(connection, group_name, wait_timeout, desired_size, prop):
    # make sure we have the latest stats after that last loop.
    as_group = describe_autoscaling_groups(connection, group_name)[0]
    props = get_properties(as_group)
    module.debug("Waiting for %s = %s, currently %s" % (prop, desired_size, props[prop]))
    # now we make sure that we have enough instances in a viable state
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and desired_size > props[prop]:
        module.debug("Waiting for %s = %s, currently %s" % (prop, desired_size, props[prop]))
        time.sleep(10)
        as_group = describe_autoscaling_groups(connection, group_name)[0]
        props = get_properties(as_group)
    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg="Waited too long for new instances to become viable. %s" % time.asctime())
    module.debug("Reached %s: %s" % (prop, desired_size))
    return props


def asg_exists(connection):
    group_name = module.params.get('name')
    as_group = describe_autoscaling_groups(connection, group_name)
    return bool(len(as_group))


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        load_balancers=dict(type='list', elements='str'),
        target_group_arns=dict(type='list', elements='str'),
        availability_zones=dict(type='list', elements='str'),
        launch_config_name=dict(type='str'),
        launch_template=dict(
            type='dict',
            default=None,
            options=dict(
                version=dict(type='str'),
                launch_template_name=dict(type='str'),
                launch_template_id=dict(type='str'),
            )
        ),
        min_size=dict(type='int'),
        max_size=dict(type='int'),
        max_instance_lifetime=dict(type='int'),
        mixed_instances_policy=dict(
            type='dict',
            default=None,
            options=dict(
                instance_types=dict(
                    type='list',
                    elements='str'
                ),
                instances_distribution=dict(
                    type='dict',
                    default=None,
                    options=dict(
                        on_demand_allocation_strategy=dict(type='str'),
                        on_demand_base_capacity=dict(type='int'),
                        on_demand_percentage_above_base_capacity=dict(type='int'),
                        spot_allocation_strategy=dict(type='str'),
                        spot_instance_pools=dict(type='int'),
                        spot_max_price=dict(type='str'),
                    )
                )
            )
        ),
        placement_group=dict(type='str'),
        desired_capacity=dict(type='int'),
        vpc_zone_identifier=dict(type='list', elements='str'),
        replace_batch_size=dict(type='int', default=1),
        replace_all_instances=dict(type='bool', default=False),
        replace_instances=dict(type='list', default=[], elements='str'),
        lc_check=dict(type='bool', default=True),
        lt_check=dict(type='bool', default=True),
        wait_timeout=dict(type='int', default=300),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(type='list', default=[], elements='dict'),
        health_check_period=dict(type='int', default=300),
        health_check_type=dict(default='EC2', choices=['EC2', 'ELB']),
        default_cooldown=dict(type='int', default=300),
        wait_for_instances=dict(type='bool', default=True),
        termination_policies=dict(type='list', default='Default', elements='str'),
        notification_topic=dict(type='str', default=None),
        notification_types=dict(
            type='list',
            default=[
                'autoscaling:EC2_INSTANCE_LAUNCH',
                'autoscaling:EC2_INSTANCE_LAUNCH_ERROR',
                'autoscaling:EC2_INSTANCE_TERMINATE',
                'autoscaling:EC2_INSTANCE_TERMINATE_ERROR'
            ],
            elements='str'
        ),
        suspend_processes=dict(type='list', default=[], elements='str'),
        metrics_collection=dict(type='bool', default=False),
        metrics_granularity=dict(type='str', default='1Minute'),
        metrics_list=dict(
            type='list',
            default=[
                'GroupMinSize',
                'GroupMaxSize',
                'GroupDesiredCapacity',
                'GroupInServiceInstances',
                'GroupPendingInstances',
                'GroupStandbyInstances',
                'GroupTerminatingInstances',
                'GroupTotalInstances'
            ],
            elements='str'
        )
    )

    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['replace_all_instances', 'replace_instances'],
            ['launch_config_name', 'launch_template']
        ]
    )

    state = module.params.get('state')
    replace_instances = module.params.get('replace_instances')
    replace_all_instances = module.params.get('replace_all_instances')

    connection = module.client('autoscaling')
    changed = create_changed = replace_changed = False
    exists = asg_exists(connection)

    if state == 'present':
        create_changed, asg_properties = create_autoscaling_group(connection)
    elif state == 'absent':
        changed = delete_autoscaling_group(connection)
        module.exit_json(changed=changed)

    # Only replace instances if asg existed at start of call
    if (
        exists
        and (replace_all_instances or replace_instances)
        and (module.params.get('launch_config_name') or module.params.get('launch_template'))
    ):
        replace_changed, asg_properties = replace(connection)

    if create_changed or replace_changed:
        changed = True

    module.exit_json(changed=changed, **asg_properties)


if __name__ == '__main__':
    main()

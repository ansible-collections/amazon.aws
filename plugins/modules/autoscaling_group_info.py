#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_group_info
version_added: 5.0.0
short_description: Gather information about EC2 Auto Scaling Groups (ASGs) in AWS
description:
  - Gather information about EC2 Auto Scaling Groups (ASGs) in AWS.
  - Prior to release 5.0.0 this module was called M(community.aws.ec2_asg_info).
    The usage did not change.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - "Rob White (@wimnat)"
options:
  name:
    description:
      - The prefix or name of the auto scaling group(s) you are searching for.
      - "Note: This is a regular expression match with implicit '^' (beginning of string). Append '$' for a complete name match."
    type: str
    required: false
    aliases: ["group_name"]
  tags:
    description:
      - >
        A dictionary/hash of tags in the format { tag1_name: 'tag1_value', tag2_name: 'tag2_value' } to match against the auto scaling
        group(s) you are searching for.
    required: false
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Find all groups
  amazon.aws.autoscaling_group_info:
  register: asgs

- name: Find a group with matching name/prefix
  amazon.aws.autoscaling_group_info:
    name: public-webserver-asg
  register: asgs

- name: Find a group with matching tags
  amazon.aws.autoscaling_group_info:
    tags:
      project: webapp
      env: production
  register: asgs

- name: Find a group with matching name/prefix and tags
  amazon.aws.autoscaling_group_info:
    name: myproject
    tags:
      env: production
  register: asgs

- name: Fail if no groups are found
  amazon.aws.autoscaling_group_info:
    name: public-webserver-asg
  register: asgs
  failed_when: "{{ asgs.results | length == 0 }}"

- name: Fail if more than 1 group is found
  amazon.aws.autoscaling_group_info:
    name: public-webserver-asg
  register: asgs
  failed_when: "{{ asgs.results | length > 1 }}"
"""

RETURN = r"""
results:
    description: A list of Auto Scaling Groups.
    returned: always
    type: list
    elements: dict
    contains:
        auto_scaling_group_arn:
            description: The Amazon Resource Name of the ASG.
            returned: success
            type: str
            sample: "arn:aws:autoscaling:us-west-2:123456789012:autoScalingGroup:10787c52-0bcb-427d-82ba-c8e4b008ed2e:autoScalingGroupName/dev11"
        auto_scaling_group_name:
            description: Name of autoscaling group.
            returned: success
            type: str
            sample: "public-webapp-production-1"
        availability_zones:
            description: List of Availability Zones that are enabled for this ASG.
            returned: success
            type: list
            sample: ["us-west-2a", "us-west-2b", "us-west-2a"]
        created_time:
            description: The date and time this ASG was created, in ISO 8601 format.
            returned: success
            type: str
            sample: "2015-11-25T00:05:36.309Z"
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
        enabled_metrics:
            description: The metrics enabled for the group.
            returned: success
            type: list
            elements: dict
            sample: [{
                        "granularity": "1Minute",
                        "metric": "GroupAndWarmPoolTotalCapacity"
                    }]
            contains:
                metric:
                    description: Name of the metric.
                    type: str
                    sample: "GroupAndWarmPoolTotalCapacity"
                granularity:
                    description: The granularity of the metric. The only valid value is 1Minute.
                    type: str
                    sample: "1Minute"
        health_check_grace_period:
            description: Length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health.
            returned: success
            type: int
            sample: 300
        health_check_type:
            description: The service you want the health status from, one of "EC2" or "ELB".
            returned: success
            type: str
            sample: "ELB"
        instances:
            description: List of EC2 instances associated with ASG and their status.
            returned: success
            type: list
            elements: dict
            sample: [
                {
                    "availability_zone": "us-west-2a",
                    "health_status": "Healthy",
                    "instance_id": "i-es22ad25",
                    "launch_configuration_name": "public-webapp-production-1",
                    "launch_template": {
                            "launch_template_id": "lt-0b19eb00123456789",
                            "launch_template_name": "test-template",
                            "version": "1"
                    },
                    "lifecycle_state": "InService",
                    "protected_from_scale_in": "false"
                }
            ]
            contains:
                availability_zone:
                    description: The Availability Zone of the instance.
                    type: str
                    sample: "ap-southeast-2a"
                health_status:
                    description: The last reported health status of the instance.
                    type: str
                    sample: "Healthy"
                instance_id:
                    description: The ID of the instance.
                    type: str
                    sample: "i-012345678"
                instance_type:
                    description: The instance type size of the running instance.
                    type: str
                    sample: "t2.micro"
                launch_template:
                    description: The EC2 launch template to base instance configuration on.
                    type: dict
                    contains:
                        launch_template_id:
                            description: The ID of the launch template.
                            type: str
                        launch_template_name:
                            description: The name of the launch template.
                            type: str
                        version:
                            description: The specific version of the launch template to use.
                            type: int
                lifecycle_state:
                    description: A description of the current lifecycle state.
                    type: str
                protected_from_scale_in:
                    description: Indicates whether the instance is protected from termination by Amazon EC2 Auto Scaling when scaling in.
                    type: bool
        launch_config_name:
            description: >
                Name of launch configuration associated with the ASG. Same as launch_configuration_name,
                provided for compatibility with M(amazon.aws.autoscaling_group) module.
            returned: success
            type: str
            sample: "public-webapp-production-1"
        launch_configuration_name:
            description: Name of launch configuration associated with the ASG.
            returned: success
            type: str
            sample: "public-webapp-production-1"
        lifecycle_hooks:
            description: List of lifecycle hooks for the ASG.
            returned: success
            type: list
            sample: [
                {
                    "AutoScalingGroupName": "public-webapp-production-1",
                    "DefaultResult": "ABANDON",
                    "GlobalTimeout": 172800,
                    "HeartbeatTimeout": 3600,
                    "LifecycleHookName": "instance-launch",
                    "LifecycleTransition": "autoscaling:EC2_INSTANCE_LAUNCHING"
                },
                {
                    "AutoScalingGroupName": "public-webapp-production-1",
                    "DefaultResult": "ABANDON",
                    "GlobalTimeout": 172800,
                    "HeartbeatTimeout": 3600,
                    "LifecycleHookName": "instance-terminate",
                    "LifecycleTransition": "autoscaling:EC2_INSTANCE_TERMINATING"
                }
            ]
        load_balancer_names:
            description: List of load balancers names attached to the ASG.
            returned: success
            type: list
            sample: ["elb-webapp-prod"]
        max_size:
            description: Maximum size of group.
            returned: success
            type: int
            sample: 3
        min_size:
            description: Minimum size of group.
            returned: success
            type: int
            sample: 1
        new_instances_protected_from_scale_in:
            description: Whether or not new instances a protected from automatic scaling in.
            returned: success
            type: bool
            sample: false
        placement_group:
            description: Placement group into which instances are launched, if any.
            returned: success
            type: str
            sample: None
        service_linked_role_arn:
            description: The ARN of the service-linked role that the Auto Scaling group uses to call other Amazon Web Services on your behalf.
            returned: success
            type: str
            sample: "arn:aws:iam::721234567890:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling"
        suspended_processes:
            description: The suspended processes associated with the group.
            returned: success
            type: list
            elements: dict
            sample: [{
                        "process_name": "AddToLoadBalancer",
                        "suspension_reason": "User suspended at 2018-08-30T14:11:58Z"
                    }]
            contains:
                process_name:
                    description: The name of the suspended process.
                    type: str
                suspension_reason:
                    description: The reason that the process was suspended.
                    type: str
        status:
            description: The current state of the group when DeleteAutoScalingGroup is in progress.
            returned: success
            type: str
            sample: None
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
            description: List of ARNs of the target groups that the ASG populates.
            returned: success
            type: list
            sample: [
                "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:targetgroup/target-group-host-hello/1a2b3c4d5e6f1a2b",
                "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:targetgroup/target-group-path-world/abcd1234abcd1234"
            ]
        target_group_names:
            description: List of names of the target groups that the ASG populates.
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
            elements: str
            sample: ["Default"]
        traffic_sources:
            description: The traffic sources associated with this Auto Scaling group.
            returned: success
            type: list
            sample: [{
                        "identifier": "arn:aws:elasticloadbalancing:us-west-2:721234567890:targetgroup/Check-Exter-A4XXXXXXXXXX/8aXXXXXXXXXXXXXX",
                        "type": "elbv2"
                    }]
            contains:
                identifier:
                    description: Identifies the traffic source.
                    type: str
                type:
                    description: Provides additional context for the value of Identifier.
                    type: str
        vpc_zone_identifier:
            description: One or more subnet IDs, if applicable, separated by commas.
            returned: success
            type: str
            sample: "subnet-0352db1247ae60b40,subnet-01f266bb9928ddaee"
"""

import re

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import AnsibleELBv2Error
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_target_groups
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def match_asg_tags(tags_to_match, asg):
    for key, value in tags_to_match.items():
        for tag in asg["Tags"]:
            if key == tag["Key"] and value == tag["Value"]:
                break
        else:
            return False
    return True


def find_asgs(conn, module, name=None, tags=None):
    """
    Args:
        conn (boto3.AutoScaling.Client): Valid Boto3 ASG client.
        name (str): Optional name of the ASG you are looking for.
        tags (dict): Optional dictionary of tags and values to search for.

    Basic Usage:
        >>> name = 'public-webapp-production'
        >>> tags = { 'env': 'production' }
        >>> conn = boto3.client('autoscaling', region_name='us-west-2')
        >>> results = find_asgs(name, conn)

    Returns:
        List
        [
            {
                "auto_scaling_group_arn": (
                    "arn:aws:autoscaling:us-west-2:123456789012:autoScalingGroup:58abc686-9783-4528-b338-3ad6f1cbbbaf:"
                    "autoScalingGroupName/public-webapp-production"
                ),
                "auto_scaling_group_name": "public-webapp-production",
                "availability_zones": ["us-west-2c", "us-west-2b", "us-west-2a"],
                "created_time": "2016-02-02T23:28:42.481000+00:00",
                "default_cooldown": 300,
                "desired_capacity": 2,
                "enabled_metrics": [],
                "health_check_grace_period": 300,
                "health_check_type": "ELB",
                "instances":
                [
                    {
                        "availability_zone": "us-west-2c",
                        "health_status": "Healthy",
                        "instance_id": "i-047a12cb",
                        "launch_configuration_name": "public-webapp-production-1",
                        "lifecycle_state": "InService",
                        "protected_from_scale_in": false
                    },
                    {
                        "availability_zone": "us-west-2a",
                        "health_status": "Healthy",
                        "instance_id": "i-7a29df2c",
                        "launch_configuration_name": "public-webapp-production-1",
                        "lifecycle_state": "InService",
                        "protected_from_scale_in": false
                    }
                ],
                "launch_config_name": "public-webapp-production-1",
                "launch_configuration_name": "public-webapp-production-1",
                "lifecycle_hooks":
                [
                    {
                        "AutoScalingGroupName": "public-webapp-production-1",
                        "DefaultResult": "ABANDON",
                        "GlobalTimeout": 172800,
                        "HeartbeatTimeout": 3600,
                        "LifecycleHookName": "instance-launch",
                        "LifecycleTransition": "autoscaling:EC2_INSTANCE_LAUNCHING"
                    },
                    {
                        "AutoScalingGroupName": "public-webapp-production-1",
                        "DefaultResult": "ABANDON",
                        "GlobalTimeout": 172800,
                        "HeartbeatTimeout": 3600,
                        "LifecycleHookName": "instance-terminate",
                        "LifecycleTransition": "autoscaling:EC2_INSTANCE_TERMINATING"
                    }
                ],
                "load_balancer_names": ["public-webapp-production-lb"],
                "max_size": 4,
                "min_size": 2,
                "new_instances_protected_from_scale_in": false,
                "placement_group": None,
                "status": None,
                "suspended_processes": [],
                "tags":
                [
                    {
                        "key": "Name",
                        "propagate_at_launch": true,
                        "resource_id": "public-webapp-production",
                        "resource_type": "auto-scaling-group",
                        "value": "public-webapp-production"
                    },
                    {
                        "key": "env",
                        "propagate_at_launch": true,
                        "resource_id": "public-webapp-production",
                        "resource_type": "auto-scaling-group",
                        "value": "production"
                    }
                ],
                "target_group_names": [],
                "target_group_arns": [],
                "termination_policies":
                [
                    "Default"
                ],
                "vpc_zone_identifier":
                [
                    "subnet-a1b1c1d1",
                    "subnet-a2b2c2d2",
                    "subnet-a3b3c3d3"
                ]
            }
        ]
    """

    try:
        asgs_paginator = conn.get_paginator("describe_auto_scaling_groups")
        asgs = asgs_paginator.paginate().build_full_result()
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe AutoScalingGroups")

    if not asgs:
        return asgs

    try:
        elbv2 = module.client("elbv2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        # This is nice to have, not essential
        elbv2 = None
    matched_asgs = []

    if name is not None:
        # if the user didn't specify a name
        name_prog = re.compile(r"^" + name)

    for asg in asgs["AutoScalingGroups"]:
        if name:
            matched_name = name_prog.search(asg["AutoScalingGroupName"])
        else:
            matched_name = True

        if tags:
            matched_tags = match_asg_tags(tags, asg)
        else:
            matched_tags = True

        if matched_name and matched_tags:
            asg = camel_dict_to_snake_dict(asg)
            # compatibility with autoscaling_group module
            if "launch_configuration_name" in asg:
                asg["launch_config_name"] = asg["launch_configuration_name"]
            # workaround for https://github.com/ansible/ansible/pull/25015
            if "target_group_ar_ns" in asg:
                asg["target_group_arns"] = asg["target_group_ar_ns"]
                del asg["target_group_ar_ns"]
            if asg.get("target_group_arns"):
                if elbv2:
                    try:
                        # Limit of 20 similar to https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_DescribeLoadBalancers.html
                        tg_chunk_size = 20
                        asg["target_group_names"] = []
                        tg_chunks = [
                            asg["target_group_arns"][i: i + tg_chunk_size]
                            for i in range(0, len(asg["target_group_arns"]), tg_chunk_size)
                        ]  # fmt: skip
                        for chunk in tg_chunks:
                            asg["target_group_names"].extend(
                                [tg["TargetGroupName"] for tg in describe_target_groups(elbv2, TargetGroupArns=chunk)]
                            )
                    except AnsibleELBv2Error as e:
                        module.fail_json_aws(e, msg="Failed to describe Target Groups")
            else:
                asg["target_group_names"] = []
            # get asg lifecycle hooks if any
            try:
                asg_lifecyclehooks = conn.describe_lifecycle_hooks(AutoScalingGroupName=asg["auto_scaling_group_name"])
                asg["lifecycle_hooks"] = asg_lifecyclehooks["LifecycleHooks"]
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to fetch information about ASG lifecycle hooks")
            matched_asgs.append(asg)

    return matched_asgs


def main():
    argument_spec = dict(
        name=dict(type="str", aliases=["group_name"]),
        tags=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    asg_name = module.params.get("name")
    asg_tags = module.params.get("tags")

    autoscaling = module.client("autoscaling")

    results = find_asgs(autoscaling, module, name=asg_name, tags=asg_tags)
    module.exit_json(results=results)


if __name__ == "__main__":
    main()

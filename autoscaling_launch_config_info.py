#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_launch_config_info
version_added: 1.0.0
short_description: Gather information about AWS Autoscaling Launch Configurations
description:
  - Gather information about AWS Autoscaling Launch Configurations.
  - Prior to release 5.0.0 this module was called C(community.aws.ec2_lc_info).
    The usage did not change.
author:
  - "Loïc Latreille (@psykotox)"
options:
  name:
    description:
      - A name or a list of name to match.
    default: []
    type: list
    elements: str
  sort:
    description:
      - Optional attribute which with to sort the results.
    choices: ['launch_configuration_name', 'image_id', 'created_time', 'instance_type', 'kernel_id', 'ramdisk_id', 'key_name']
    type: str
  sort_order:
    description:
      - Order in which to sort results.
      - Only used when the 'sort' parameter is specified.
    choices: ['ascending', 'descending']
    default: 'ascending'
    type: str
  sort_start:
    description:
      - Which result to start with (when sorting).
      - Corresponds to Python slice notation.
    type: int
  sort_end:
    description:
      - Which result to end with (when sorting).
      - Corresponds to Python slice notation.
    type: int
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all launch configurations
  community.aws.autoscaling_launch_config_info:

- name: Gather information about launch configuration with name "example"
  community.aws.autoscaling_launch_config_info:
    name: example

- name: Gather information sorted by created_time from most recent to least recent
  community.aws.autoscaling_launch_config_info:
    sort: created_time
    sort_order: descending
"""

RETURN = r"""
block_device_mapping:
    description: Block device mapping for the instances of launch configuration.
    type: list
    returned: always
    sample: "[{
        'device_name': '/dev/xvda':,
        'ebs': {
            'delete_on_termination': true,
            'volume_size': 8,
            'volume_type': 'gp2'
    }]"
classic_link_vpc_security_groups:
    description: IDs of one or more security groups for the VPC specified in classic_link_vpc_id.
    type: str
    returned: always
    sample:
created_time:
    description: The creation date and time for the launch configuration.
    type: str
    returned: always
    sample: "2016-05-27T13:47:44.216000+00:00"
ebs_optimized:
    description: EBS I/O optimized C(true) or not C(false).
    type: bool
    returned: always
    sample: true,
image_id:
    description: ID of the Amazon Machine Image (AMI).
    type: str
    returned: always
    sample: "ami-12345678"
instance_monitoring:
    description: Launched with detailed monitoring or not.
    type: dict
    returned: always
    sample: "{
        'enabled': true
    }"
instance_type:
    description: Instance type.
    type: str
    returned: always
    sample: "t2.micro"
kernel_id:
    description: ID of the kernel associated with the AMI.
    type: str
    returned: always
    sample:
key_name:
    description: Name of the key pair.
    type: str
    returned: always
    sample: "user_app"
launch_configuration_arn:
    description: Amazon Resource Name (ARN) of the launch configuration.
    type: str
    returned: always
    sample: "arn:aws:autoscaling:us-east-1:123456798012:launchConfiguration:ba785e3a-dd42-6f02-4585-ea1a2b458b3d:launchConfigurationName/lc-app"
launch_configuration_name:
    description: Name of the launch configuration.
    type: str
    returned: always
    sample: "lc-app"
ramdisk_id:
    description: ID of the RAM disk associated with the AMI.
    type: str
    returned: always
    sample:
security_groups:
    description: Security groups to associated.
    type: list
    returned: always
    sample: "[
        'web'
    ]"
user_data:
    description: User data available.
    type: str
    returned: always
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def list_launch_configs(connection, module):
    launch_config_name = module.params.get("name")
    sort = module.params.get("sort")
    sort_order = module.params.get("sort_order")
    sort_start = module.params.get("sort_start")
    sort_end = module.params.get("sort_end")

    try:
        pg = connection.get_paginator("describe_launch_configurations")
        launch_configs = pg.paginate(LaunchConfigurationNames=launch_config_name).build_full_result()
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="Failed to list launch configs")

    snaked_launch_configs = []
    for launch_config in launch_configs["LaunchConfigurations"]:
        snaked_launch_configs.append(camel_dict_to_snake_dict(launch_config))

    for launch_config in snaked_launch_configs:
        if "CreatedTime" in launch_config:
            launch_config["CreatedTime"] = str(launch_config["CreatedTime"])

    if sort:
        snaked_launch_configs.sort(key=lambda e: e[sort], reverse=(sort_order == "descending"))

    if sort and sort_start and sort_end:
        snaked_launch_configs = snaked_launch_configs[sort_start:sort_end]
    elif sort and sort_start:
        snaked_launch_configs = snaked_launch_configs[sort_start:]
    elif sort and sort_end:
        snaked_launch_configs = snaked_launch_configs[:sort_end]

    module.exit_json(launch_configurations=snaked_launch_configs)


def main():
    argument_spec = dict(
        name=dict(required=False, default=[], type="list", elements="str"),
        sort=dict(
            required=False,
            default=None,
            choices=[
                "launch_configuration_name",
                "image_id",
                "created_time",
                "instance_type",
                "kernel_id",
                "ramdisk_id",
                "key_name",
            ],
        ),
        sort_order=dict(required=False, default="ascending", choices=["ascending", "descending"]),
        sort_start=dict(required=False, type="int"),
        sort_end=dict(required=False, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        connection = module.client("autoscaling")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    list_launch_configs(connection, module)


if __name__ == "__main__":
    main()

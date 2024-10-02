#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_launch_template_info
version_added: 9.0.0
short_description: Gather information about launch templates and versions.
description:
  - Gather information about launch templates.
author:
  - Aubin Bikouo (@abikouo)
options:
  launch_template_ids:
    description: The IDs of the launch templates.
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeLaunchTemplates.html) for possible filters.
      - Filter names and values are case sensitive.
    type: dict
    default: {}

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about a launch template
  amazon.aws.ec2_launch_template_info:
    launch_template_ids:
      - 'lt-01238c059e3466abc'

- name: Gather information launch template using name
  amazon.aws.ec2_launch_template_info:
    filters:
      launch-template-name: my-test-launch-template
"""

RETURN = r"""
launch_templates:
  description: A list of launch templates.
  returned: always
  type: list
  elements: dict
  contains:
    launch_template_id:
      description: The ID of the launch template.
      type: str
      returned: always
    launch_template_name:
      description: The name of the launch template.
      type: str
      returned: always
    create_time:
      description: The time launch template was created.
      type: str
      returned: always
    created_by:
      description: The principal that created the launch template.
      type: str
      returned: always
    default_version_number:
      description: The version number of the default version of the launch template.
      type: int
      returned: always
    latest_version_number:
      description: The version number of the latest version of the launch template.
      type: int
      returned: always
    tags:
      description: A dictionary of tags assigned to image.
      returned: when AMI is created or already exists
      type: dict
      sample: {
          "Env": "devel",
          "Name": "nat-server"
      }
    versions:
      description: All available versions of the launch template.
      type: list
      elements: dict
      returned: always
      contains:
        launch_template_id:
          description: The ID of the launch template.
          type: str
          returned: always
        launch_template_name:
          description: The name of the launch template.
          type: str
          returned: always
        create_time:
          description: The time the version was created.
          type: str
          returned: always
        created_by:
          description: The principal that created the version.
          type: str
          returned: always
        default_version:
          description: Indicates whether the version is the default version.
          type: bool
          returned: always
        version_number:
          description: The version number.
          type: int
          returned: always
        version_description:
          description: The description for the version.
          type: str
          returned: always
        launch_template_data:
          description: Information about the launch template.
          returned: always
          type: dict
          sample: {
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/sdb",
                    "Ebs": {
                        "DeleteOnTermination": true,
                        "Encrypted": true,
                        "VolumeSize": 5
                    }
                }
            ],
            "EbsOptimized": false,
            "ImageId": "ami-0231217be14a6f3ba",
            "InstanceType": "t2.micro",
            "NetworkInterfaces": [
                {
                    "AssociatePublicIpAddress": false,
                    "DeviceIndex": 0,
                    "Ipv6Addresses": [
                        {
                            "Ipv6Address": "2001:0:130F:0:0:9C0:876A:130B"
                        }
                    ]
                }
            ]
        }
"""

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_template_versions
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_templates
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def list_launch_templates(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    try:
        # Describe launch templates
        launch_templates = describe_launch_templates(
            client,
            launch_template_ids=module.params.get("launch_template_ids"),
            filters=ansible_dict_to_boto3_filter_list(module.params.get("filters")),
        )

        # Describe launch templates versions
        for template in launch_templates:
            template["Versions"] = describe_launch_template_versions(
                client, LaunchTemplateId=template["LaunchTemplateId"]
            )

        # format output
        launch_templates = [camel_dict_to_snake_dict(t, ignore_list=["Tags"]) for t in launch_templates]
        for t in launch_templates:
            t["tags"] = boto3_tag_list_to_ansible_dict(t.pop("tags", {}))

        return normalize_boto3_result(launch_templates)

    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


def main():
    argument_spec = dict(
        launch_template_ids=dict(type="list", elements="str"),
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    client = module.client("ec2")

    launch_templates = list_launch_templates(client, module)
    module.exit_json(launch_templates=launch_templates)


if __name__ == "__main__":
    main()

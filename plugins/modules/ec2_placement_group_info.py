#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_placement_group_info
version_added: 7.0.0
short_description: Gather information about EC2 placement groups.
description:
   - Gather information about EC2 placement groups.
options:
  group_names:
    description: A name for the placement group.
    aliases: [ "group_name" ]
    type: list
    elements: str
    default: []
  group_ids:
    description: A name for the placement group.
    aliases: [ "group_id" ]
    type: list
    elements: str
    default: []
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribePlacementGroups.html) for possible filters.
      - Filter names and values are case sensitive.
    type: dict
    default: {}
author:
  - "Mathieu Fortin (@mfortin) <mathieu.fortin@autodesk.com>"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

# Thank you to Autodesk for sponsoring development of this module.

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about a placement group using group name
  amazon.aws.ec2_placement_group_info:
    group_name: TestGroup

- name: Gather information about a placement group using group id
  amazon.aws.ec2_placement_group_info:
    group_id: TestGroup

- name: Gather information about a placement group using filters
  amazon.aws.ec2_placement_group_info:
    filters: 
      "tag:Name": TestGroup      

- name: Gather information about a placement group using filters for group-name
  amazon.aws.ec2_placement_group_info:
    filters: 
      "group-name": TestGroup      
"""

RETURN = r"""
placement_groups:
    description: A list of placement groups.
    returned: always
    type: complex
    contains:
        group_name:
            description: The name of the placement group.
            returned: When Placement Group is created or already exists
            type: str
            sample: "TestGroup"
        state:
            description: The state of the placement group.
            type: str
            returned: When Placement Group is created or already exists
            sample: "available"
        strategy:
            description: The placement strategy.
            type: str
            returned: When Placement Group is created or already exists
            sample: "cluster"
        partition_count:
            description: The number of partitions. Valid only when 'strategy' is set to 'partition'.
            type: int
            returned: When Placement Group is created or already exists
            sample: 2  
        group_id:
            description: The ID of the placement group.
            returned: When Placement Group is created or already exists
            type: str
            sample: "pg-1234567890abcdef0"
        tags:
            description: A dictionary of tags assigned to image.
            returned: when AMI is created or already exists
            type: dict
            sample: {
                "Env": "devel",
                "Name": "cluster-group"
            }
        group_arn:
            description: The ARN of the placement group.
            returned: When Placement Group is created or already exists
            type: str
            sample: "arn:aws:ec2:us-east-1:123456789012:placement-group/my-cluster"
        spread_level:
            description: The spread level for the placement group. Only Outpost placement groups can be spread across hosts.
            returned: When Placement Group is created or already exists
            type: str
            sample: "host"
"""

import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list

class Ec2PlacementGroupInfoFailure(Exception):
    def __init__(self, message=None, original_e=None):
        super().__init__(message)
        self.original_e = original_e
        self.message = message


def build_request_args(filters, group_ids, group_names):
    request_args = dict()
    if group_ids:
        request_args["GroupIds"] = [str(group_id) for group_id in group_ids]
    if group_names:
        request_args["GroupNames"] = [str(group_name) for group_name in group_names]
    if filters:
        request_args["Filters"] = ansible_dict_to_boto3_filter_list(filters)

    request_args = {k: v for k, v in request_args.items() if v is not None}

    return request_args

def get_placement_groups(connection, request_args):
    try:
        placement_groups = connection.describe_placement_groups(aws_retry=True, **request_args)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as err:
        raise Ec2PlacementGroupInfoFailure("Error retrieving placement groups", err)
    return placement_groups


def list_placement_groups(connection, request_args):
    placement_groups = get_placement_groups(connection, request_args)["PlacementGroups"]

    camel_placement_groups = []
    for pg in placement_groups:
        try:
            placement_group = camel_dict_to_snake_dict(pg)
            placement_group["tags"] = boto3_tag_list_to_ansible_dict(placement_group.get("tags", []))
            camel_placement_groups.append(placement_group)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as err:
            raise Ec2PlacementGroupInfoFailure("Error describing placement group", err)

    return camel_placement_groups

def main():
    argument_spec = dict(
        group_names=dict(default = [], type = "list", elements = "str", aliases = ["group_name"]),
        group_ids=dict(default = [], type = "list", elements = "str", aliases = ["group_id"]),
        filters=dict(default={}, type = "dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    connection = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    request_args = build_request_args(
        filters=module.params["filters"],
        group_ids=module.params["group_ids"],
        group_names=module.params["group_names"],
    )

    placement_groups = list_placement_groups(connection, request_args)

    module.exit_json(placement_groups=placement_groups)

if __name__ == "__main__":
    main()

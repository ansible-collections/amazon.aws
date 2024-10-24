#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_placement_group_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: List EC2 Placement Group(s) details
description:
  - List details of EC2 Placement Group(s).
author:
  - "Brad Macpherson (@iiibrad)"
options:
  names:
    description:
      - A list of names to filter on. If a listed group does not exist, there
        will be no corresponding entry in the result; no error will be raised.
    type: list
    elements: str
    required: false
    default: []
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details or the AWS region,
# see the AWS Guide for details.

- name: List all placement groups.
  amazon.aws.ec2_placement_group_info:
  register: all_ec2_placement_groups

- name: List two placement groups.
  amazon.aws.ec2_placement_group_info:
    names:
      - my-cluster
      - my-other-cluster
  register: specific_ec2_placement_groups

- ansible.builtin.debug:
    msg: >
      {{ specific_ec2_placement_groups | json_query("[?name=='my-cluster']") }}
"""


RETURN = r"""
placement_groups:
  description: Placement group attributes.
  returned: always
  type: complex
  contains:
    name:
      description: PG name.
      type: str
      sample: "my-cluster"
    state:
      description: PG state.
      type: str
      sample: "available"
    strategy:
      description: PG strategy.
      type: str
      sample: "cluster"
    tags:
      description: Tags associated with the placement group.
      type: dict
      version_added: 8.1.0
      sample:
        tags:
          some: value1
          other: value2
"""

from typing import Any
from typing import Dict
from typing import List

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_placement_groups
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def get_placement_groups_details(connection, names: List) -> Dict[str, Any]:
    params = {}
    if len(names) > 0:
        params["Filters"] = [
            {
                "Name": "group-name",
                "Values": names,
            }
        ]
    response = describe_ec2_placement_groups(connection, **params)

    results = []
    for placement_group in response:
        results.append(
            {
                "name": placement_group["GroupName"],
                "state": placement_group["State"],
                "strategy": placement_group["Strategy"],
                "tags": boto3_tag_list_to_ansible_dict(placement_group.get("Tags")),
            }
        )
    return results


def main():
    argument_spec = dict(
        names=dict(type="list", default=[], elements="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    connection = module.client("ec2")
    names = module.params.get("names")

    placement_groups = get_placement_groups_details(connection, names)
    module.exit_json(changed=False, placement_groups=placement_groups)


if __name__ == "__main__":
    main()

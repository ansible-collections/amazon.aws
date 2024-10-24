#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_placement_group
version_added: 1.0.0
version_added_collection: community.aws
short_description: Create or delete an EC2 Placement Group
description:
  - Create an EC2 Placement Group; if the placement group already exists,
    nothing is done. Or, delete an existing placement group. If the placement
    group is absent, do nothing. See also
    U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/placement-groups.html).
author:
  - "Brad Macpherson (@iiibrad)"
options:
  name:
    description:
      - The name for the placement group.
    required: true
    type: str
  partition_count:
    description:
      - The number of partitions.
      - Valid only when O(strategy) is set to V(partition).
      - Must be a value between V(1) and V(7).
    type: int
    version_added: 3.1.0
  state:
    description:
      - Create or delete placement group.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  strategy:
    description:
      - Placement group strategy. Cluster will cluster instances into a
        low-latency group in a single Availability Zone, while Spread spreads
        instances across underlying hardware.
    default: cluster
    choices: [ 'cluster', 'spread', 'partition' ]
    type: str
  tags:
    description:
      - A dict of key value pairs to associate with the placement group.
    type: dict
    version_added: 8.1.0
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide
# for details.

- name: Create a placement group.
  amazon.aws.ec2_placement_group:
    name: my-cluster
    state: present

- name: Create a Spread placement group.
  amazon.aws.ec2_placement_group:
    name: my-cluster
    state: present
    strategy: spread

- name: Create a Partition strategy placement group.
  amazon.aws.ec2_placement_group:
    name: my-cluster
    state: present
    strategy: partition
    partition_count: 3

- name: Delete a placement group.
  amazon.aws.ec2_placement_group:
    name: my-cluster
    state: absent
"""

RETURN = r"""
placement_group:
  description: Placement group attributes.
  returned: when state != absent
  type: dict
  contains:
    group_arn:
      description: Placement Group ARN.
      type: str
      returned: always
      sample: "arn:aws:ec2:us-east-1:123456789012:placement-group"
    group_id:
      description: Placement Group Id.
      type: str
      returned: always
      sample: "pg-123456789012"
    name:
      description: Placement Group name.
      type: str
      returned: always
      sample: "my-cluster"
    partition_count:
      description: Partition Count.
      type: str
      returned: If applicable
      sample: "my-cluster"
    state:
      description: Placement Groupt state.
      type: str
      returned: If applicable
      sample: "available"
    strategy:
      description: Placement Group strategy.
      type: str
      returned: If applicable
      sample: "cluster"
    tags:
      description: Tags associated with the placement group.
      type: dict
      returned: If applicable
      version_added: 8.1.0
      sample:
        tags:
          some: value1
          other: value2
"""

from typing import Any
from typing import Dict

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_ec2_placement_group
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_ec2_placement_group
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_placement_groups
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications


def search_placement_group(connection, name: str) -> Dict[str, Any]:
    """
    Check if a placement group exists.
    """
    response = describe_ec2_placement_groups(connection, Filters=[{"Name": "group-name", "Values": [name]}])

    if len(response) != 1:
        return None
    else:
        return format_placement_group_information(response[0])


def format_placement_group_information(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format placement group information
    """

    response = camel_dict_to_snake_dict(response, ignore_list=["Tags"])
    if "tags" in response:
        response["tags"] = boto3_tag_list_to_ansible_dict(response.get("tags", []))
    response["name"] = response["group_name"]
    return response


def create_placement_group(connection, module: AnsibleAWSModule) -> None:
    name = module.params.get("name")
    strategy = module.params.get("strategy")
    tags = module.params.get("tags")
    partition_count = module.params.get("partition_count")

    if strategy != "partition" and partition_count:
        module.fail_json(msg="'partition_count' can only be set when strategy is set to 'partition'.")

    params = {}
    params["GroupName"] = name
    params["Strategy"] = strategy
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types=["placement-group"])
    if partition_count:
        params["PartitionCount"] = partition_count
    if module.check_mode:
        module.exit_json(
            changed=True,
            placement_group={
                "name": name,
                "strategy": strategy,
                "tags": tags,
            },
            msg="EC2 placement group would be created if not in check mode",
        )

    response = create_ec2_placement_group(connection, **params)
    module.exit_json(changed=True, placement_group=format_placement_group_information(response))


def delete_placement_group(connection, module: AnsibleAWSModule) -> None:
    if module.check_mode:
        module.exit_json(changed=True, msg="VPC would be deleted if not in check mode")
    name = module.params.get("name")
    delete_ec2_placement_group(connection, name)
    module.exit_json(changed=True)


def main():
    argument_spec = dict(
        name=dict(required=True, type="str"),
        partition_count=dict(type="int"),
        state=dict(default="present", choices=["present", "absent"]),
        strategy=dict(default="cluster", choices=["cluster", "spread", "partition"]),
        tags=dict(type="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2")

    state = module.params.get("state")
    name = module.params.get("name")
    placement_group = search_placement_group(connection, name)

    if state == "present":
        if placement_group is None:
            create_placement_group(connection, module)
        else:
            strategy = module.params.get("strategy")
            if placement_group["strategy"] == strategy:
                module.exit_json(changed=False, placement_group=placement_group)
            else:
                name = module.params.get("name")
                module.fail_json(
                    msg=f"Placement group '{name}' exists, can't change strategy from '{placement_group['strategy']}' to '{strategy}'"
                )

    elif state == "absent":
        if placement_group is None:
            module.exit_json(changed=False)
        else:
            delete_placement_group(connection, module)


if __name__ == "__main__":
    main()

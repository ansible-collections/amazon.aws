#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_placement_group
version_added: 7.0.0
short_description: Create or destroy a placement group in EC2
description:
   - Create or destroy a placement group in EC2
options:
  group_name:
    description:
      - A name for the placement group. Must be unique within the scope of your account for the Region.
    type: str
  strategy:
    description:
      - The placement strategy.
    type: str
    choices: [ "cluster", "partition", "spread" ]
  partition_count:
    description:
      - The number of partitions. Valid only when 'strategy' is set to 'partition'.
    type: int
  spread_level:
    description:
      - Determines how placement groups spread instances.
    type: str
    choices: ["host", "rack"]
author:
  - "Mathieu Fortin (@mfortin) <mathieu.fortin@autodesk.com>"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

# Thank you to Autodesk for sponsoring development of this module.

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Basic group creation
  amazon.aws.ec2_placement_group:
    group_name: TestGroup
    tags:
      Name: grouptest

- name: Group Creation with Spread Strategy
  amazon.aws.ec2_placement_group:
    group_name: SpreadGroup
    state: present
    strategy: spread
    spread_level: host
    tags:
      Name: spreadtest
    
- name: Group Creation with Partition Strategy
  amazon.aws.ec2_placement_group:
    group_name: PartitonGroup
    state: present
    strategy: partition
    partition_count: 2
    tags:
      Name: paritiontest

- nane: Remove group
  amazon.aws.ec2_placement_group:
    group_name: TestGroup
    state: absent
"""

RETURN = r"""
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

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import add_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications


class Ec2PlacementGroupFailure(Exception):
    def __init__(self, message=None, original_e=None):
        super().__init__(message)
        self.original_e = original_e
        self.message = message


def get_placement_group_info(camel_placement_group):
    placement_group = camel_dict_to_snake_dict(camel_placement_group)
    return dict(
        group_name=placement_group.get("group_name"),
        state=placement_group.get("state"),
        strategy=placement_group.get("strategy"),
        partition_count=placement_group.get("partition_count"),
        group_id=placement_group.get("group_id"),
        tags=boto3_tag_list_to_ansible_dict(placement_group.get("tags")),
        group_arn=placement_group.get("group_arn"),
        spread_level=placement_group.get("spread_level"),
    )


def get_placement_group_by_name(connection, placement_group_name):
    try:
        placement_group_response = connection.describe_placement_groups(
            aws_retry=True,
            GroupNames=[placement_group_name],
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        if is_boto3_error_code(e, "InvalidPlacementGroup.NotFound"):
            return None
        else:
            raise Ec2PlacementGroupFailure(f"Error retrieving placement group by {placement_group_name}", e)

    placement_groups = placement_group_response.get("PlacementGroups", [])
    if len(placement_groups) == 0:
        return None

    if len(placement_groups) > 1:
        raise Ec2PlacementGroupFailure(f"Invalid number of placement groups ({str(len(placement_groups))}) found for group_name: {placement_group_name}.")

    result = placement_groups[0]
    return result


def rename_item_if_exists(dict_object, attribute, new_attribute, child_node=None, attribute_type=None):
    new_item = dict_object.get(attribute)
    if new_item is not None:
        if attribute_type is not None:
            new_item = attribute_type(new_item)
        if child_node is None:
            dict_object[new_attribute] = new_item
        else:
            dict_object[child_node][new_attribute] = new_item
        dict_object.pop(attribute)
    return dict_object


def validate_params(
    module,
    strategy=None,
    partition_count=None,
    spread_level=None,
    **_,
):
    if (strategy == 'partition' and partition_count is None) or (partition_count is not None and strategy != 'partition'):
        module.fail_json("Specify partition count when using partition strategy.")

    elif (strategy == "spread" and spread_level is None) or (spread_level is not None and strategy != "spread"):
        module.fail_json("You must define a spread level when using spread strategy.")


class DeletePlacementGroup:
    @staticmethod
    def do_check_mode(module, connection, group_name):
        placement_group = get_placement_group_by_name(connection, group_name)

        if placement_group is None:
            module.exit_json(changed=False)

        if "PlacementGroups" in placement_group:
            module.exit_json(changed=True, msg="Would have deleted the placement group if not in check mode.")
        else:
            module.exit_json(msg=f"Placement group {group_name} has already been deleted.", changed=False)

    @classmethod
    def do(cls, module, connection, group_name):
        """Entrypoint to delete a placement group"""
        placement_group = get_placement_group_by_name(connection, group_name)

        if placement_group is None:
            module.exit_json(changed=False)

        # When trying to re-deregister an already deregistered image it doesn't raise an exception, it just returns an object without image attributes.
        if "PlacementGroups" in placement_group:
            try:
                connection.delete_placement_group(aws_retry=True, GroupName=group_name)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                raise Ec2PlacementGroupFailure("Error deleting placement group", e)
        else:
            module.exit_json(msg=f"Placement group {group_name} has already been deleted.", changed=False)

        exit_params = {"msg": "Placement group delete operation complete.", "changed": True}

        module.exit_json(**exit_params)


class UpdatePlacementGroup:
    @staticmethod
    def set_tags(connection, module, group_name, tags, purge_tags):
        if not tags:
            return False

        return ensure_ec2_tags(connection, module, group_name, tags=tags, purge_tags=purge_tags)

    @classmethod
    def do(cls, module, connection, group_name):
        """Entry point to update a placement group"""
        placement_group = get_placement_group_by_name(connection, group_name)
        if placement_group is None:
            raise Ec2PlacementGroupFailure(f"Placement group {group_name} does not exist")

        changed = False
        changed |= cls.set_tags(connection, module, placement_group['GroupArn'], module.params["tags"], module.params["purge_tags"])
        
        if changed and module.check_mode:
            module.exit_json(changed=True, msg="Would have updated placement group if not in check mode.")
        elif changed:
            module.exit_json(msg="Placement group updated.", changed=True, **get_placement_group_info(get_placement_group_by_name(connection, group_name)))
        else:
            module.exit_json(msg="Placement group not updated.", changed=False, **get_placement_group_info(placement_group))


class CreatePlacementGroup:
    @staticmethod
    def do_check_mode(module, connection, group_name):
        placement_group = get_placement_group_by_name(connection, group_name)
        if not placement_group["PlacementGroups"]:
            module.exit_json(changed=True, msg="Would have created a placement group if not in check mode.")
        else:
            module.exit_json(changed=False, msg="Error creating placement group: Group name is already in used by another placement group.")

    @staticmethod
    def set_tags(connection, module, tags, group_name):
        if not tags:
            return

        placement_group = get_placement_group_by_name(connection, group_name)
        add_ec2_tags(connection, module, placement_group['GroupArn'], module.params["tags"])

    @staticmethod
    def build_create_placement_group_parameters(module_params):
        group_name = module_params.get("group_name"),
        strategy = module_params.get("strategy")
        partition_count = module_params.get("partition_count")
        tags = module_params.get("tags")
        spread_level = module_params.get("spread_level")
        
        params = {
            "GroupName": group_name,
            "Strategy": strategy,
            "PartitionCount": partition_count,
            "SpreadLevel": spread_level,
            "TagSpecifications": boto3_tag_specifications(tags, types=["placement_group"]),
        }

        return {k: v for k, v in params.items() if v is not None}

    @classmethod
    def do(cls, module, connection, group_name):
        """Entry point to create placement group"""
        params = cls.build_create_placement_group_parameters(module.params)

        try:
            placement_group = connection.create_placement_group(**params)
            group_name = placement_group.get("PlacementGroups")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise Ec2PlacementGroupFailure("Error creating placement group", e)

        if "TagSpecifications" not in params:
            cls.set_tags(connection, module, module.params.get("tags"), group_name)

        module.exit_json(
            msg="Placement group creation operation complete.", changed=True, **get_placement_group_info(get_placement_group_by_name(connection, group_name))
        )


def main():
    argument_spec = dict(
        group_name={"type": "str", "required": True},
        strategy={"type": "str", "choices": ["cluster", "partition", "spread"]},
        parition_count={"type": "int"},
        spread_level={"type": "str", "choices": ["host", "rack"]},
        state={"default": "present", "choices": ["present", "absent"]},
        tags={"type": "dict", "aliases": ["resource_tags"]},
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ["spread_level", "partition_count"],
        ],
        required_if=[
            ["state", "absent", ["group_name"]],
            ["state", "present", ["group_name"]],
        ],
        supports_check_mode=True,
    )

    validate_params(module, **module.params)

    connection = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    try:
        if module.params["state"] == "present":
            placement_group = get_placement_group_by_name(connection, module.params["group_name"])
            if placement_group is None:
                CreatePlacementGroup.do_check_mode(
                    module, connection, module.params["group_name"]
                ) if module.check_mode else CreatePlacementGroup.do(
                    module, connection, module.params["group_name"]
                )
            else:
                UpdatePlacementGroup.do(
                    module, connection, module.params["group_name"]
                )

        elif module.params["state"] == "absent":
            DeletePlacementGroup.do_check_mode(
                module, connection, module.params["group_name"]
            ) if module.check_mode else DeletePlacementGroup.do(
                module, connection, module.params["group_name"]
            )

    except Ec2PlacementGroupFailure as e:
        if e.original_e:
            module.fail_json_aws(e.original_e, e.message)
        else:
            module.fail_json(e.message)


if __name__ == "__main__":
    main()

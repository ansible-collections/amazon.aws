#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_subnet_group
version_added: 5.0.0
short_description: manage RDS database subnet groups
description:
  - Creates, modifies, and deletes RDS database subnet groups.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    required: true
    choices: [ 'present' , 'absent' ]
    type: str
  name:
    description:
      - Database subnet group identifier.
    required: true
    type: str
  description:
    description:
      - Database subnet group description.
      - Required when O(state=present).
    type: str
  subnets:
    description:
      - List of subnet IDs that make up the database subnet group.
      - Required when O(state=present).
    type: list
    elements: str
notes:
  - Support for O(tags) and O(purge_tags) was added in release 3.2.0.
author:
  - "Scott Anderson (@tastychutney)"
  - "Alina Buzachis (@alinabuzachis)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Add or change a subnet group
  amazon.aws.rds_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb

- name: Add or change a subnet group and associate tags
  amazon.aws.rds_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb
    tags:
      tag1: Tag1
      tag2: Tag2

- name: Remove a subnet group
  amazon.aws.rds_subnet_group:
    state: absent
    name: norwegian-blue
"""

RETURN = r"""
changed:
    description: True if listing the RDS subnet group succeeds.
    type: bool
    returned: always
    sample: false
subnet_group:
    description: Dictionary of DB subnet group values,
    returned: O(state=present)
    type: complex
    contains:
        name:
            description: The name of the DB subnet group (maintained for backward compatibility).
            returned: O(state=present)
            type: str
            sample: "ansible-test-mbp-13950442"
        db_subnet_group_name:
            description: The name of the DB subnet group.
            returned: O(state=present)
            type: str
            sample: "ansible-test-mbp-13950442"
        description:
            description: The description of the DB subnet group (maintained for backward compatibility).
            returned: O(state=present)
            type: str
            sample: "Simple description."
        db_subnet_group_description:
            description: The description of the DB subnet group.
            returned: O(state=present)
            type: str
            sample: "Simple description."
        vpc_id:
            description: The VPC Id of the DB subnet group.
            returned: O(state=present)
            type: str
            sample: "vpc-0acb0ba033ff2119c"
        subnet_ids:
            description: Contains a list of Subnet IDs.
            returned: O(state=present)
            type: list
            sample:
                "subnet-08c94870f4480797e"
        subnets:
            description: Contains a list of Subnet elements (@see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.describe_db_subnet_groups). # noqa
            returned: O(state=present)
            type: list
            contains:
                subnet_availability_zone:
                    description: Contains Availability Zone information.
                    returned: O(state=present)
                    type: dict
                    version_added: 3.2.0
                    version_added_collection: community.aws
                    sample:
                        name: "eu-north-1b"
                subnet_identifier:
                    description: The identifier of the subnet.
                    returned: O(state=present)
                    type: str
                    version_added: 3.2.0
                    version_added_collection: community.aws
                    sample: "subnet-08c94870f4480797e"
                subnet_outpost:
                    description: This value specifies the Outpost.
                    returned: O(state=present)
                    type: dict
                    version_added: 3.2.0
                    version_added_collection: community.aws
                    sample: {}
                subnet_status:
                    description: The status of the subnet.
                    returned: O(state=present)
                    type: str
                    version_added: 3.2.0
                    version_added_collection: community.aws
                    sample: "Active"
        status:
            description: The status of the DB subnet group (maintained for backward compatibility).
            returned: O(state=present)
            type: str
            sample: "Complete"
        subnet_group_status:
            description: The status of the DB subnet group.
            returned: O(state=present)
            type: str
            sample: "Complete"
        db_subnet_group_arn:
            description: The ARN of the DB subnet group.
            returned: O(state=present)
            type: str
            sample: "arn:aws:rds:eu-north-1:123456789012:subgrp:ansible-test-13950442"
        tags:
            description: The tags associated with the subnet group.
            returned: O(state=present)
            type: dict
            version_added: 3.2.0
            version_added_collection: community.aws
            sample:
                tag1: Tag1
                tag2: Tag2
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import call_method
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_subnet_groups
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list


def create_subnet_list(subnets: List[Dict[str, Any]]) -> List[str]:
    """
    Construct a list of subnet ids from a list of subnet dicts returned by boto3.

    Args:
        subnets: A list of subnet definitions as returned by describe_db_subnet_groups.

    Returns:
        A list of subnet ids.
    """
    return [subnet.get("subnet_identifier") for subnet in subnets]


def create_result(changed: bool, subnet_group: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build the module result, adding backward compatible keys to the subnet group.

    Args:
        changed: Whether the module made a change.
        subnet_group: The subnet group as a snake_cased dict, or None.

    Returns:
        The module result dict.
    """
    if subnet_group is None:
        return dict(changed=changed)
    result_subnet_group = dict(subnet_group)
    result_subnet_group["name"] = result_subnet_group.get("db_subnet_group_name")
    result_subnet_group["description"] = result_subnet_group.get("db_subnet_group_description")
    result_subnet_group["status"] = result_subnet_group.get("subnet_group_status")
    result_subnet_group["subnet_ids"] = create_subnet_list(subnet_group.get("subnets"))
    return dict(changed=changed, subnet_group=result_subnet_group)


def get_subnet_group(client, module: AnsibleAWSModule) -> Optional[Dict[str, Any]]:
    """
    Return the matching DB subnet group as a snake_cased dict, or None if it does not exist.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.

    Returns:
        The subnet group (including tags) as a snake_cased dict, or None.
    """
    name = module.params.get("name").lower()
    try:
        subnet_groups = describe_db_subnet_groups(client, DBSubnetGroupName=name)
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Could not describe subnet group {name}")

    if not subnet_groups:
        return None

    subnet_group = camel_dict_to_snake_dict(subnet_groups[0])
    subnet_group["tags"] = get_tags(client, module, subnet_group["db_subnet_group_arn"])
    return subnet_group


def create_subnet_group(client, module: AnsibleAWSModule) -> bool:
    """
    Create a DB subnet group.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.

    Returns:
        True if a change was made.
    """
    params = {
        "DBSubnetGroupName": module.params.get("name").lower(),
        "DBSubnetGroupDescription": module.params.get("description"),
        "SubnetIds": module.params.get("subnets"),
    }
    if module.params.get("tags"):
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params.get("tags"))

    _result, changed = call_method(client, module, "create_db_subnet_group", params)
    return changed


def update_subnet_group(client, module: AnsibleAWSModule, subnet_group: Dict[str, Any]) -> bool:
    """
    Update an existing DB subnet group's description, subnets and tags.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.
        subnet_group: The existing subnet group as a snake_cased dict.

    Returns:
        True if a change was made.
    """
    changed = ensure_tags(
        client,
        module,
        subnet_group["db_subnet_group_arn"],
        subnet_group["tags"],
        module.params.get("tags"),
        module.params["purge_tags"],
    )

    description = module.params.get("description")
    subnets = sorted(module.params.get("subnets") or [])
    existing_subnets = sorted(create_subnet_list(subnet_group.get("subnets")))

    if subnet_group["db_subnet_group_description"] != description or existing_subnets != subnets:
        params = {
            "DBSubnetGroupName": module.params.get("name").lower(),
            "DBSubnetGroupDescription": description,
            "SubnetIds": module.params.get("subnets"),
        }
        _result, modified = call_method(client, module, "modify_db_subnet_group", params)
        changed |= modified

    return changed


def delete_subnet_group(client, module: AnsibleAWSModule) -> bool:
    """
    Delete a DB subnet group.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.

    Returns:
        True if a change was made.
    """
    params = {"DBSubnetGroupName": module.params.get("name").lower()}
    _result, changed = call_method(client, module, "delete_db_subnet_group", params)
    return changed


def main():
    argument_spec = dict(
        state=dict(required=True, choices=["present", "absent"]),
        name=dict(required=True),
        description=dict(required=False),
        subnets=dict(required=False, type="list", elements="str"),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )
    required_if = [("state", "present", ["description", "subnets"])]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)

    state = module.params.get("state")
    client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())

    subnet_group = get_subnet_group(client, module)
    changed = False

    if state == "present":
        if subnet_group is None:
            changed = create_subnet_group(client, module)
        else:
            changed = update_subnet_group(client, module, subnet_group)
        subnet_group = get_subnet_group(client, module)
    elif subnet_group is not None:
        changed = delete_subnet_group(client, module)
        if not module.check_mode:
            subnet_group = None

    module.exit_json(**create_result(changed, subnet_group))


if __name__ == "__main__":
    main()

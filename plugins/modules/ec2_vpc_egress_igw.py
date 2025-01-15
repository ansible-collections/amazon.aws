#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_egress_igw
version_added: 1.0.0
version_added_collection: community.aws
short_description: Manage an AWS VPC Egress Only Internet gateway
description:
  - Manage an AWS VPC Egress Only Internet gateway
author:
  - Daniel Shepherd (@shepdelacreme)
options:
  vpc_id:
    description:
      - The VPC ID for the VPC that this Egress Only Internet Gateway should be attached.
    required: true
    type: str
  state:
    description:
      - Create or delete the EIGW.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
notes:
  - Support for O(tags) and O(purge_tags) was added in release 9.0.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags.modules
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{eigw.gateway_id}} for use in setting up NATs etc.
- name: Create Egress internet only gateway
  amazon.aws.ec2_vpc_egress_igw:
    vpc_id: vpc-abcdefgh
    state: present

- name: Delete Egress internet only gateway
  amazon.aws.ec2_vpc_egress_igw:
    vpc_id: vpc-abcdefgh
    state: absent
"""

RETURN = r"""
gateway_id:
    description: The ID of the Egress Only Internet Gateway or Null.
    returned: always
    type: str
    sample: "eigw-0e00cf111ba5bc11e"
vpc_id:
    description: The ID of the VPC to attach or detach gateway from.
    returned: always
    type: str
    sample: "vpc-012345678"
tags:
    description: Any tags assigned to the internet gateway.
    returned: always
    type: dict
"""

from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_egress_only_internet_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_egress_only_internet_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_egress_only_internet_gateways
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def delete_eigw(module: AnsibleAWSModule, connection, eigw_id: str) -> Dict[str, Union[str, bool]]:
    """
    Delete EIGW.

    module     : AnsibleAWSModule object
    connection : boto3 client connection object
    eigw_id    : ID of the EIGW to delete
    """

    if module.check_mode:
        return dict(
            changed=True, msg=f"Would have deleted Egress internet only Gateway id '{eigw_id}' if not in check mode."
        )

    try:
        changed = delete_egress_only_internet_gateway(connection, egress_only_internet_gateway_id=eigw_id)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    return dict(changed=changed)


def create_eigw(module: AnsibleAWSModule, connection, vpc_id: str) -> Dict[str, Union[str, bool]]:
    """
    Create EIGW.

    module       : AnsibleAWSModule object
    connection   : boto3 client connection object
    vpc_id       : ID of the VPC we are operating on
    """

    if module.check_mode:
        return dict(changed=True, msg="Would have created Egress internet only Gateway if not in check mode.")

    gateway_id = None
    changed = False

    try:
        response = create_egress_only_internet_gateway(connection, vpc_id=vpc_id, tags=module.params.get("tags"))
        changed = True
    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    gateway = response.get("EgressOnlyInternetGateway", {})
    state = gateway.get("Attachments", [{}])[0].get("State")
    gateway_id = gateway.get("EgressOnlyInternetGatewayId")
    tags = boto3_tag_list_to_ansible_dict(gateway.get("Tags", []))

    if not gateway_id or state not in ("attached", "attaching"):
        # EIGW gave back a bad attachment state or an invalid response so we error out
        module.fail_json(
            msg=f"Unable to create and attach Egress Only Internet Gateway to VPCId: {vpc_id}. Bad or no state in response",
            **camel_dict_to_snake_dict(response),
        )

    return dict(changed=changed, gateway_id=gateway_id, tags=tags)


def find_egress_only_igw(module: AnsibleAWSModule, connection, vpc_id: str) -> Optional[Dict[str, Any]]:
    """
    Describe EIGWs.

    module     : AnsibleAWSModule object
    connection : boto3 client connection object
    vpc_id     : ID of the VPC we are operating on
    """
    result = None

    try:
        for eigw in describe_egress_only_internet_gateways(connection):
            for attachment in eigw.get("Attachments", []):
                if attachment.get("VpcId") == vpc_id and attachment.get("State") in ("attached", "attaching"):
                    return {
                        "gateway_id": eigw.get("EgressOnlyInternetGatewayId"),
                        "tags": boto3_tag_list_to_ansible_dict(eigw.get("Tags", [])),
                    }
    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    return result


def ensure_present(connection, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]]) -> None:
    vpc_id = module.params.get("vpc_id")
    result = dict(vpc_id=vpc_id, changed=False)

    if not existing:
        result.update(create_eigw(module, connection, vpc_id))
    else:
        egress_only_igw_id = existing.get("gateway_id")
        changed = False
        result = existing
        tags = module.params.get("tags")
        purge_tags = module.params.get("purge_tags")
        if tags is not None:
            changed = ensure_ec2_tags(
                connection,
                module,
                egress_only_igw_id,
                resource_type="egress-only-internet-gateway",
                tags=tags,
                purge_tags=purge_tags,
            )
        result.update(dict(changed=changed, vpc_id=vpc_id))

    module.exit_json(**result)


def ensure_absent(connection, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]]) -> None:
    vpc_id = module.params.get("vpc_id")
    if not existing:
        module.exit_json(changed=False, msg=f"No Egress only internet gateway attached to the VPC id '{vpc_id}'")

    egress_only_igw_id = existing.get("gateway_id")
    result = dict(gateway_id=egress_only_igw_id, vpc_id=vpc_id, changed=False)
    result.update(delete_eigw(module, connection, egress_only_igw_id))
    module.exit_json(**result)


def main():
    argument_spec = dict(
        vpc_id=dict(required=True),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2")

    vpc_id = module.params.get("vpc_id")
    state = module.params.get("state")

    existing_egress_only_igw = find_egress_only_igw(module, connection, vpc_id)

    if state == "present":
        ensure_present(connection, module, existing_egress_only_igw)
    else:
        ensure_absent(connection, module, existing_egress_only_igw)


if __name__ == "__main__":
    main()

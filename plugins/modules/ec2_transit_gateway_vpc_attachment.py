#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_transit_gateway_vpc_attachment
short_description: Create and delete AWS Transit Gateway VPC attachments
version_added: 4.0.0
version_added_collection: community.aws
description:
  - Creates, Deletes and Updates AWS Transit Gateway VPC Attachments.
options:
  transit_gateway:
    description:
      - The ID of the Transit Gateway that the attachment belongs to.
      - When creating a new attachment, O(transit_gateway) must be provided.
      - At least one of O(name), O(transit_gateway) and O(id) must be provided.
      - O(transit_gateway) is an immutable setting and can not be updated on an
        existing attachment.
    type: str
    required: false
    aliases: ["transit_gateway_id"]
  id:
    description:
      - The ID of the Transit Gateway Attachment.
      - When O(id) is not set, a search using O(transit_gateway) and O(name) will be
        performed. If multiple results are returned, the module will fail.
      - At least one of O(name), O(transit_gateway) and O(id) must be provided.
    type: str
    required: false
    aliases: ["attachment_id"]
  name:
    description:
      - The V(Name) tag of the Transit Gateway attachment.
      - Providing both O(id) and O(name) will set the V(Name) tag on an existing
        attachment the matching O(id).
      - Setting the V(Name) tag in O(tags) will also result in the V(Name) tag being
        updated.
      - At least one of O(name), O(transit_gateway) and O(id) must be provided.
    type: str
    required: false
  state:
    description:
      - Create or remove the Transit Gateway attachment.
    type: str
    required: false
    choices: ["present", "absent"]
    default: 'present'
  subnets:
    description:
      - The ID of the subnets in which to create the transit gateway VPC attachment.
      - Required when creating a new attachment.
    type: list
    elements: str
    required: false
  purge_subnets:
    description:
      - If O(purge_subnets=true), existing subnets will be removed from the
        attachment as necessary to match exactly what is defined by O(subnets).
    type: bool
    required: false
    default: true
  dns_support:
    description:
      - Whether DNS support is enabled.
    type: bool
    required: false
  ipv6_support:
    description:
      - Whether IPv6 support is enabled.
    type: bool
    required: false
  appliance_mode_support:
    description:
      - Whether the attachment is configured for appliance mode.
      - When appliance mode is enabled, Transit Gateway, using 4-tuples of an
        IP packet, selects a single Transit Gateway ENI in the Appliance VPC
        for the life of a flow to send traffic to.
    type: bool
    required: false
  wait:
    description:
      - Whether to wait for the Transit Gateway attachment to reach the
        C(Available) or C(Deleted) state before the module returns.
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - Maximum time, in seconds, to wait for the Transit Gateway attachment
        to reach the expected state.
      - Defaults to 600 seconds.
    type: int
    default: 600
    required: false
author:
  - Mark Chappell (@tremble)
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create a Transit Gateway attachment
  amazon.aws.ec2_transit_gateway_vpc_attachment:
    state: "present"
    transit_gateway: "tgw-123456789abcdef01"
    name: "AnsibleTest-1"
    subnets:
      - "subnet-00000000000000000"
      - "subnet-11111111111111111"
      - "subnet-22222222222222222"
    ipv6_support: true
    purge_subnets: true
    dns_support: true
    appliance_mode_support: true
    tags:
      TestTag: "changed data in Test Tag"

- name: Set sub options on a Transit Gateway attachment
  amazon.aws.ec2_transit_gateway_vpc_attachment:
    state: "present"
    id: "tgw-attach-0c0c5fd0b0f01d1c9"
    name: "AnsibleTest-1"
    ipv6_support: true
    purge_subnets: false
    dns_support: false
    appliance_mode_support: true

- name: Delete the transit gateway
  amazon.aws.ec2_transit_gateway_vpc_attachment:
    state: "absent"
    id: "tgw-attach-0c0c5fd0b0f01d1c9"
"""

RETURN = r"""
attachments:
  description: The attributes of the Transit Gateway attachments.
  type: list
  elements: dict
  returned: success
  contains:
    creation_time:
      description:
        - An ISO 8601 date time stamp of when the attachment was created.
      type: str
      returned: success
      sample: "2022-03-10T16:40:26+00:00"
    options:
      description:
        - Additional VPC attachment options.
      type: dict
      returned: success
      contains:
        appliance_mode_support:
          description:
            - Indicates whether appliance mode support is enabled.
          type: str
          returned: success
          sample: "enable"
        dns_support:
          description:
            - Indicates whether DNS support is enabled.
          type: str
          returned: success
          sample: "disable"
        ipv6_support:
          description:
            - Indicates whether IPv6 support is disabled.
          type: str
          returned: success
          sample: "disable"
        security_group_referencing_support:
          description:
            - Indicated weather security group referencing support is disabled.
          type: str
          returned: success
          sample: "enable"
    state:
      description:
        - The state of the attachment.
      type: str
      returned: success
      sample: "deleting"
    subnet_ids:
      description:
        - The IDs of the subnets in use by the attachment.
      type: list
      elements: str
      returned: success
      sample: ["subnet-0123456789abcdef0", "subnet-11111111111111111"]
    tags:
      description:
        - A dictionary representing the resource tags.
      type: dict
      returned: success
    transit_gateway_attachment_id:
      description:
        - The ID of the attachment.
      type: str
      returned: success
      sample: "tgw-attach-0c0c5fd0b0f01d1c9"
    transit_gateway_id:
      description:
        - The ID of the transit gateway that the attachment is connected to.
      type: str
      returned: success
      sample: "tgw-0123456789abcdef0"
    vpc_id:
      description:
        - The ID of the VPC that the attachment is connected to.
      type: str
      returned: success
      sample: "vpc-0123456789abcdef0"
    vpc_owner_id:
      description:
        - The ID of the account that the VPC belongs to.
      type: str
      returned: success
      sample: "1234567890122"
"""

from typing import NoReturn

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transitgateway import TransitGatewayVpcAttachmentManager
from ansible_collections.amazon.aws.plugins.module_utils.transitgateway import find_existing_attachment
from ansible_collections.amazon.aws.plugins.module_utils.transitgateway import get_states
from ansible_collections.amazon.aws.plugins.module_utils.transitgateway import subnets_to_vpc


def handle_vpc_attachments(client, module: AnsibleAWSModule) -> NoReturn:
    """
    Handle the creation, modification, or deletion of VPC attachments
    based on the parameters provided in the Ansible module.

    Args:
        client: The AWS client to interact with EC2 services.
        module: An instance of AnsibleAWSModule.

    Returns:
        NoReturn: The function exits by calling module.exit_json()
                  with the results of the operation.
    """
    attach_id = module.params.get("id", None)
    attachment = None

    if not attach_id:
        filters = {}
        if module.params.get("transit_gateway"):
            filters["transit-gateway-id"] = module.params["transit_gateway"]
        if module.params.get("name"):
            filters["tag:Name"] = module.params["name"]
        if module.params.get("subnets"):
            vpc_id = subnets_to_vpc(client, module, module.params["subnets"])
            filters["vpc-id"] = vpc_id

        # Attachments lurk in a 'deleted' state, for a while, ignore them so we
        # can reuse the names
        filters["state"] = get_states()

        attachment = find_existing_attachment(client, module, filters=filters)
        if attachment:
            attach_id = attachment["TransitGatewayAttachmentId"]
    else:
        attachment = find_existing_attachment(client, module, attachment_id=attach_id)

    manager = TransitGatewayVpcAttachmentManager(client, module, attachment, attachment_id=attach_id)

    if module.params["state"] == "absent":
        manager.delete_attachment()
    else:
        manager.create_or_modify_attachment()

    results = dict(
        changed=manager.changed,
        attachments=[manager.updated],
    )
    if manager.changed:
        results["diff"] = dict(
            before=boto3_resource_to_ansible_dict(manager.existing),
            after=manager.updated,
        )

    module.exit_json(**results)


def main():
    argument_spec = dict(
        state=dict(type="str", required=False, default="present", choices=["absent", "present"]),
        transit_gateway=dict(type="str", required=False, aliases=["transit_gateway_id"]),
        id=dict(type="str", required=False, aliases=["attachment_id"]),
        name=dict(type="str", required=False),
        subnets=dict(type="list", elements="str", required=False),
        purge_subnets=dict(type="bool", required=False, default=True),
        tags=dict(type="dict", required=False, aliases=["resource_tags"]),
        purge_tags=dict(type="bool", required=False, default=True),
        appliance_mode_support=dict(type="bool", required=False),
        dns_support=dict(type="bool", required=False),
        ipv6_support=dict(type="bool", required=False),
        wait=dict(type="bool", required=False, default=True),
        wait_timeout=dict(type="int", default=600, required=False),
    )

    one_of = [
        ["id", "transit_gateway", "name"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=one_of,
    )

    client = module.client("ec2")

    handle_vpc_attachments(client, module)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_transit_gateway_vpc_attachment_info
short_description: describes AWS Transit Gateway VPC attachments
version_added: 4.0.0
version_added_collection: community.aws
description:
  - Describes AWS Transit Gateway VPC Attachments.
options:
  id:
    description:
      - The ID of the Transit Gateway Attachment.
      - Mutually exclusive with O(name) and O(filters).
    type: str
    required: false
    aliases: ["attachment_id"]
  name:
    description:
      - The V(Name) tag of the Transit Gateway attachment.
    type: str
    required: false
  filters:
    description:
      - A dictionary of filters to apply. Each dict item consists of a filter key and a filter value.
      - Setting a V(tag:Name) filter will override the O(name) parameter.
    type: dict
    required: false
  include_deleted:
    description:
      - If O(include_deleted=True), then attachments in a deleted state will
        also be returned.
      - Setting a V(state) filter will override the O(include_deleted) parameter.
    type: bool
    required: false
    default: false
author:
  - Mark Chappell (@tremble)
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Describe a specific Transit Gateway attachment
  amazon.aws.ec2_transit_gateway_vpc_attachment_info:
    id: "tgw-attach-0123456789abcdef0"

- name: Describe all attachments attached to a transit gateway
  amazon.aws.ec2_transit_gateway_vpc_attachment_info:
    filters:
      transit-gateway-id: "tgw-0fedcba9876543210"

- name: Describe all attachments in an account
  amazon.aws.ec2_transit_gateway_vpc_attachment_info:
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
      sample: "123456789012"
"""

from typing import Any
from typing import Dict
from typing import List

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_transit_gateway_vpc_attachments
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transitgateway import get_states


def main():
    argument_spec = dict(
        id=dict(type="str", required=False, aliases=["attachment_id"]),
        name=dict(type="str", required=False),
        filters=dict(type="dict", required=False),
        include_deleted=dict(type="bool", required=False, default=False),
    )

    mutually_exclusive = [
        ["id", "name"],
        ["id", "filters"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
    )

    name = module.params.get("name")
    attachment_id = module.params.get("id")
    opt_filters = module.params.get("filters")
    include_deleted = module.params.get("include_deleted")

    client = module.client("ec2")

    params: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}
    attachments: List[Dict[str, Any]] = []

    if attachment_id:
        params["TransitGatewayAttachmentIds"] = [attachment_id]

    # Add filter by name if provided
    if name:
        filters["tag:Name"] = name

    # Include only active states if "include_deleted" is False
    if not include_deleted:
        filters["state"] = get_states()

    # Include any additional filters provided by the user
    if opt_filters:
        filters.update(opt_filters)

    if filters:
        params["Filters"] = ansible_dict_to_boto3_filter_list(filters)

    try:
        result = describe_transit_gateway_vpc_attachments(client, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    if result:
        attachments = [boto3_resource_to_ansible_dict(attachment) for attachment in result]

    module.exit_json(changed=False, attachments=attachments, filters=filters)


if __name__ == "__main__":
    main()

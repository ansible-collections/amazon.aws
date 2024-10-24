#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_vgw_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: Gather information about virtual gateways in AWS
description:
  - Gather information about virtual gateways (VGWs) in AWS.
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpnGateways.html) for possible filters.
    type: dict
    default: {}
  vpn_gateway_ids:
    description: One or more virtual private gateway IDs.
    type: list
    elements: str
author:
  - "Nick Aslanidis (@naslanidis)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all virtual gateways for an account or profile
  amazon.aws.ec2_vpc_vgw_info:
    region: ap-southeast-2

- name: Gather information about a filtered list of Virtual Gateways
  amazon.aws.ec2_vpc_vgw_info:
    region: ap-southeast-2
    profile: production
    filters:
      "tag:Name": "main-virt-gateway"

- name: Gather information about a specific virtual gateway by VpnGatewayIds
  amazon.aws.ec2_vpc_vgw_info:
    region: ap-southeast-2
    profile: production
    vpn_gateway_ids: vgw-c432f6a7
"""

RETURN = r"""
virtual_gateways:
    description: Information about one or more virtual private gateways.
    returned: always
    type: list
    elements: dict
    contains:
      vpn_gateway_id:
        description: The ID of the virtual private gateway.
        type: str
        returned: success
        example: "vgw-0123456789abcdef0"
      state:
        description: Informtion about the current state of the virtual private gateway.
        type: str
        returned: success
        example: "available"
      type:
        description: Information about type of VPN connection the virtual private gateway supports.
        type: str
        returned: success
        example: "ipsec.1"
      vpc_attachments:
        description: Information about the VPCs attached to the virtual private gateway.
        type: list
        elements: dict
        returned: success
        contains:
          state:
            description: The current state of the attachment.
            type: str
            returned: success
            example: "available"
          vpc_id:
            description: The ID of the VPC.
            type: str
            returned: success
            example: "vpc-12345678901234567"
      tags:
        description:
          - A list of dictionaries representing the tags attached to the virtual private gateway.
          - Represents the same details as RV(virtual_gateways.resource_tags).
        type: list
        elements: dict
        returned: success
        contains:
          key:
            description: The key of the tag.
            type: str
            returned: success
            example: "MyKey"
          value:
            description: The value of the tag.
            type: str
            returned: success
            example: "MyValue"
      resource_tags:
        description:
          - A dictionary representing the tags attached to the VGW.
          - Represents the same details as RV(virtual_gateways.tags).
        type: dict
        returned: success
        example: {
                    "MyKey": "MyValue",
                    "Env": "Dev_Test_01"
                  }
"""

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpn_gateways
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def get_virtual_gateway_info(virtual_gateway):
    tags = virtual_gateway.get("Tags", [])
    resource_tags = boto3_tag_list_to_ansible_dict(tags)
    virtual_gateway_info = dict(
        VpnGatewayId=virtual_gateway["VpnGatewayId"],
        State=virtual_gateway["State"],
        Type=virtual_gateway["Type"],
        VpcAttachments=virtual_gateway["VpcAttachments"],
        Tags=tags,
        ResourceTags=resource_tags,
    )
    return virtual_gateway_info


def list_virtual_gateways(client, module):
    params = dict()
    vpn_gateway_ids = module.params.get("vpn_gateway_ids")
    filters = module.params.get("filters")

    if filters:
        params["Filters"] = ansible_dict_to_boto3_filter_list(filters)
    if vpn_gateway_ids:
        params["VpnGatewayIds"] = vpn_gateway_ids

    try:
        all_virtual_gateways = describe_vpn_gateways(client, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    return [
        camel_dict_to_snake_dict(get_virtual_gateway_info(vgw), ignore_list=["ResourceTags"])
        for vgw in all_virtual_gateways
    ]


def main():
    argument_spec = dict(
        filters=dict(type="dict", default=dict()),
        vpn_gateway_ids=dict(type="list", default=None, elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2")
    results = list_virtual_gateways(connection, module)

    module.exit_json(virtual_gateways=results)


if __name__ == "__main__":
    main()

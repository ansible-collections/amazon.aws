#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_vpc_vgw_info
version_added: 1.0.0
short_description: Gather information about virtual gateways in AWS
description:
  - Gather information about virtual gateways (VGWs) in AWS.
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpnGateways.html) for possible filters.
    type: dict
  vpn_gateway_ids:
    description:
      - Get details of a specific Virtual Gateway ID.
    type: list
    elements: str
author:
  - "Nick Aslanidis (@naslanidis)"
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = r'''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all virtual gateways for an account or profile
  community.aws.ec2_vpc_vgw_info:
    region: ap-southeast-2
    profile: production
  register: vgw_info

- name: Gather information about a filtered list of Virtual Gateways
  community.aws.ec2_vpc_vgw_info:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "main-virt-gateway"
  register: vgw_info

- name: Gather information about a specific virtual gateway by VpnGatewayIds
  community.aws.ec2_vpc_vgw_info:
    region: ap-southeast-2
    profile: production
    vpn_gateway_ids: vgw-c432f6a7
  register: vgw_info
'''

RETURN = r'''
virtual_gateways:
    description: The virtual gateways for the account.
    returned: always
    type: list
    elements: dict
    contains:
      vpn_gateway_id:
        description: The ID of the VGW.
        type: str
        returned: success
        example: "vgw-0123456789abcdef0"
      state:
        description: The current state of the VGW.
        type: str
        returned: success
        example: "available"
      type:
        description: The type of VPN connection the VGW supports.
        type: str
        returned: success
        example: "ipsec.1"
      vpc_attachments:
        description: A description of the attachment of VPCs to the VGW.
        type: list
        elements: dict
        returned: success
        contains:
          state:
            description: The current state of the attachment.
            type: str
            returned: success
            example: available
          vpc_id:
            description: The ID of the VPC.
            type: str
            returned: success
            example: vpc-12345678901234567
      tags:
        description:
          - A list of dictionaries representing the tags attached to the VGW.
          - Represents the same details as I(resource_tags).
        type: list
        elements: dict
        returned: success
        contains:
          key:
            description: The key of the tag.
            type: str
            returned: success
            example: MyKey
          value:
            description: The value of the tag.
            type: str
            returned: success
            example: MyValue
      resource_tags:
        description:
          - A dictionary representing the tags attached to the VGW.
          - Represents the same details as I(tags).
        type: dict
        returned: success
        example: {"MyKey": "MyValue"}
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def get_virtual_gateway_info(virtual_gateway):
    tags = virtual_gateway.get('Tags', [])
    resource_tags = boto3_tag_list_to_ansible_dict(tags)
    virtual_gateway_info = dict(
        VpnGatewayId=virtual_gateway['VpnGatewayId'],
        State=virtual_gateway['State'],
        Type=virtual_gateway['Type'],
        VpcAttachments=virtual_gateway['VpcAttachments'],
        Tags=tags,
        ResourceTags=resource_tags,
    )
    return virtual_gateway_info


def list_virtual_gateways(client, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))

    if module.params.get("vpn_gateway_ids"):
        params['VpnGatewayIds'] = module.params.get("vpn_gateway_ids")

    try:
        all_virtual_gateways = client.describe_vpn_gateways(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list gateways")

    return [camel_dict_to_snake_dict(get_virtual_gateway_info(vgw), ignore_list=['ResourceTags'])
            for vgw in all_virtual_gateways['VpnGateways']]


def main():
    argument_spec = dict(
        filters=dict(type='dict', default=dict()),
        vpn_gateway_ids=dict(type='list', default=None, elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        connection = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # call your function here
    results = list_virtual_gateways(connection, module)

    module.exit_json(virtual_gateways=results)


if __name__ == '__main__':
    main()

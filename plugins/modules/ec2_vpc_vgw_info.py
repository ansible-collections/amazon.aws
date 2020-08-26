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
    - Gather information about virtual gateways in AWS.
    - This module was called C(ec2_vpc_vgw_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpnGateways.html) for possible filters.
    type: dict
  vpn_gateway_ids:
    description:
      - Get details of a specific Virtual Gateway ID. This value should be provided as a list.
    type: list
    elements: str
author: "Nick Aslanidis (@naslanidis)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

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
    sample: [
        {
            "state": "available",
            "tags": [
                {
                    "key": "Name",
                    "value": "TEST-VGW"
                }
            ],
            "type": "ipsec.1",
            "vpc_attachments": [
                {
                    "state": "attached",
                    "vpc_id": "vpc-22a93c74"
                }
            ],
            "vpn_gateway_id": "vgw-23e3d64e"
        }
    ]

changed:
    description: True if listing the virtual gateways succeeds.
    returned: always
    type: bool
    sample: "false"
'''
import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list


def get_virtual_gateway_info(virtual_gateway):
    virtual_gateway_info = {'VpnGatewayId': virtual_gateway['VpnGatewayId'],
                            'State': virtual_gateway['State'],
                            'Type': virtual_gateway['Type'],
                            'VpcAttachments': virtual_gateway['VpcAttachments'],
                            'Tags': virtual_gateway.get('Tags', [])}
    return virtual_gateway_info


def list_virtual_gateways(client, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['DryRun'] = module.check_mode

    if module.params.get("vpn_gateway_ids"):
        params['VpnGatewayIds'] = module.params.get("vpn_gateway_ids")

    try:
        all_virtual_gateways = client.describe_vpn_gateways(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    return [camel_dict_to_snake_dict(get_virtual_gateway_info(vgw))
            for vgw in all_virtual_gateways['VpnGateways']]


def main():
    argument_spec = dict(
        filters=dict(type='dict', default=dict()),
        vpn_gateway_ids=dict(type='list', default=None, elements='str')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ec2_vpc_vgw_facts':
        module.deprecate("The 'ec2_vpc_vgw_facts' module has been renamed to 'ec2_vpc_vgw_info'", date='2021-12-01', collection_name='community.aws')

    try:
        connection = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # call your function here
    results = list_virtual_gateways(connection, module)

    module.exit_json(virtual_gateways=results)


if __name__ == '__main__':
    main()

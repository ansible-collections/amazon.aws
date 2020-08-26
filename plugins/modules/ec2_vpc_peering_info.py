#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_peering_info
short_description: Retrieves AWS VPC Peering details using AWS methods.
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC Peers
  - This module was called C(ec2_vpc_peering_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
options:
  peer_connection_ids:
    description:
      - List of specific VPC peer IDs to get details for.
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcPeeringConnections.html)
        for possible filters.
    type: dict
author: Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Simple example of listing all VPC Peers
- name: List all vpc peers
  community.aws.ec2_vpc_peering_info:
    region: ap-southeast-2
  register: all_vpc_peers

- name: Debugging the result
  ansible.builtin.debug:
    msg: "{{ all_vpc_peers.result }}"

- name: Get details on specific VPC peer
  community.aws.ec2_vpc_peering_info:
    peer_connection_ids:
      - pcx-12345678
      - pcx-87654321
    region: ap-southeast-2
  register: all_vpc_peers

- name: Get all vpc peers with specific filters
  community.aws.ec2_vpc_peering_info:
    region: ap-southeast-2
    filters:
      status-code: ['pending-acceptance']
  register: pending_vpc_peers
'''

RETURN = r'''
result:
  description: The result of the describe.
  returned: success
  type: list
'''

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def get_vpc_peers(client, module):
    params = dict()
    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('peer_connection_ids'):
        params['VpcPeeringConnectionIds'] = module.params.get('peer_connection_ids')
    try:
        result = json.loads(json.dumps(client.describe_vpc_peering_connections(**params), default=date_handler))
    except Exception as e:
        module.fail_json(msg=to_native(e))

    return result['VpcPeeringConnections']


def main():
    argument_spec = dict(
        filters=dict(default=dict(), type='dict'),
        peer_connection_ids=dict(default=None, type='list', elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,)
    if module._name == 'ec2_vpc_peering_facts':
        module.deprecate("The 'ec2_vpc_peering_facts' module has been renamed to 'ec2_vpc_peering_info'", date='2021-12-01', collection_name='community.aws')

    try:
        ec2 = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # Turn the boto3 result in to ansible friendly_snaked_names
    results = [camel_dict_to_snake_dict(peer) for peer in get_vpc_peers(ec2, module)]

    # Turn the boto3 result in to ansible friendly tag dictionary
    for peer in results:
        peer['tags'] = boto3_tag_list_to_ansible_dict(peer.get('tags', []))

    module.exit_json(result=results)


if __name__ == '__main__':
    main()

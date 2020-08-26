#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_nat_gateway_info
short_description: Retrieves AWS VPC Managed Nat Gateway details using AWS methods.
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC Managed Nat Gateways
  - This module was called C(ec2_vpc_nat_gateway_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
options:
  nat_gateway_ids:
    description:
      - List of specific nat gateway IDs to fetch details for.
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNatGateways.html)
        for possible filters.
    type: dict
author: Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Simple example of listing all nat gateways
- name: List all managed nat gateways in ap-southeast-2
  community.aws.ec2_vpc_nat_gateway_info:
    region: ap-southeast-2
  register: all_ngws

- name: Debugging the result
  ansible.builtin.debug:
    msg: "{{ all_ngws.result }}"

- name: Get details on specific nat gateways
  community.aws.ec2_vpc_nat_gateway_info:
    nat_gateway_ids:
      - nat-1234567891234567
      - nat-7654321987654321
    region: ap-southeast-2
  register: specific_ngws

- name: Get all nat gateways with specific filters
  community.aws.ec2_vpc_nat_gateway_info:
    region: ap-southeast-2
    filters:
      state: ['pending']
  register: pending_ngws

- name: Get nat gateways with specific filter
  community.aws.ec2_vpc_nat_gateway_info:
    region: ap-southeast-2
    filters:
      subnet-id: subnet-12345678
      state: ['available']
  register: existing_nat_gateways
'''

RETURN = r'''
result:
  description: The result of the describe, converted to ansible snake case style.
    See http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_nat_gateways for the response.
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
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def get_nat_gateways(client, module, nat_gateway_id=None):
    params = dict()
    nat_gateways = list()

    params['Filter'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['NatGatewayIds'] = module.params.get('nat_gateway_ids')

    try:
        result = json.loads(json.dumps(client.describe_nat_gateways(**params), default=date_handler))
    except Exception as e:
        module.fail_json(msg=to_native(e))

    for gateway in result['NatGateways']:
        # Turn the boto3 result into ansible_friendly_snaked_names
        converted_gateway = camel_dict_to_snake_dict(gateway)
        if 'tags' in converted_gateway:
            # Turn the boto3 result into ansible friendly tag dictionary
            converted_gateway['tags'] = boto3_tag_list_to_ansible_dict(converted_gateway['tags'])

        nat_gateways.append(converted_gateway)

    return nat_gateways


def main():
    argument_spec = dict(
        filters=dict(default={}, type='dict'),
        nat_gateway_ids=dict(default=[], type='list', elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,)
    if module._name == 'ec2_vpc_nat_gateway_facts':
        module.deprecate("The 'ec2_vpc_nat_gateway_facts' module has been renamed to 'ec2_vpc_nat_gateway_info'",
                         date='2021-12-01', collection_name='community.aws')

    try:
        connection = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    results = get_nat_gateways(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()

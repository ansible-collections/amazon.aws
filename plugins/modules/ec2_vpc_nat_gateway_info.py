#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_nat_gateway_info
short_description: Retrieves AWS VPC Managed Nat Gateway details using AWS methods
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC Managed Nat Gateways
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
- amazon.aws.boto3
'''

EXAMPLES = r'''
# Simple example of listing all nat gateways
- name: List all managed nat gateways in ap-southeast-2
  amazon.aws.ec2_vpc_nat_gateway_info:
    region: ap-southeast-2
  register: all_ngws

- name: Debugging the result
  ansible.builtin.debug:
    msg: "{{ all_ngws.result }}"

- name: Get details on specific nat gateways
  amazon.aws.ec2_vpc_nat_gateway_info:
    nat_gateway_ids:
      - nat-1234567891234567
      - nat-7654321987654321
    region: ap-southeast-2
  register: specific_ngws

- name: Get all nat gateways with specific filters
  amazon.aws.ec2_vpc_nat_gateway_info:
    region: ap-southeast-2
    filters:
      state: ['pending']
  register: pending_ngws

- name: Get nat gateways with specific filter
  amazon.aws.ec2_vpc_nat_gateway_info:
    region: ap-southeast-2
    filters:
      subnet-id: subnet-12345678
      state: ['available']
  register: existing_nat_gateways
'''

RETURN = r'''
changed:
  description: True if listing the internet gateways succeeds.
  type: bool
  returned: always
  sample: false
result:
  description:
    - The result of the describe, converted to ansible snake case style.
    - See also U(http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_nat_gateways).
  returned: suceess
  type: list
  contains:
    create_time:
        description: The date and time the NAT gateway was created.
        returned: always
        type: str
        sample: "2021-03-11T22:43:25+00:00"
    delete_time:
        description: The date and time the NAT gateway was deleted.
        returned: when the NAT gateway has been deleted
        type: str
        sample: "2021-03-11T22:43:25+00:00"
    nat_gateway_addresses:
        description: List containing a dictionary with the IP addresses and network interface associated with the NAT gateway.
        returned: always
        type: dict
        contains:
            allocation_id:
                description: The allocation ID of the Elastic IP address that's associated with the NAT gateway.
                returned: always
                type: str
                sample: eipalloc-0853e66a40803da76
            network_interface_id:
                description: The ID of the network interface associated with the NAT gateway.
                returned: always
                type: str
                sample: eni-0a37acdbe306c661c
            private_ip:
                description: The private IP address associated with the Elastic IP address.
                returned: always
                type: str
                sample: 10.0.238.227
            public_ip:
                description: The Elastic IP address associated with the NAT gateway.
                returned: always
                type: str
                sample: 34.204.123.52
    nat_gateway_id:
        description: The ID of the NAT gateway.
        returned: always
        type: str
        sample: nat-0c242a2397acf6173
    state:
        description: state of the NAT gateway.
        returned: always
        type: str
        sample: available
    subnet_id:
        description: The ID of the subnet in which the NAT gateway is located.
        returned: always
        type: str
        sample: subnet-098c447465d4344f9
    vpc_id:
        description: The ID of the VPC in which the NAT gateway is located.
        returned: always
        type: str
        sample: vpc-02f37f48438ab7d4c
    tags:
        description: Tags applied to the NAT gateway.
        returned: always
        type: dict
        sample:
            Tag1: tag1
            Tag_2: tag_2
'''


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result


@AWSRetry.jittered_backoff(retries=10)
def _describe_nat_gateways(client, module, **params):
    try:
        paginator = client.get_paginator('describe_nat_gateways')
        return paginator.paginate(**params).build_full_result()['NatGateways']
    except is_boto3_error_code('InvalidNatGatewayID.NotFound'):
        module.exit_json(msg="NAT gateway not found.")
    except is_boto3_error_code('NatGatewayMalformed'):  # pylint: disable=duplicate-except
        module.fail_json_aws(msg="NAT gateway id is malformed.")


def get_nat_gateways(client, module):
    params = dict()
    nat_gateways = list()

    params['Filter'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['NatGatewayIds'] = module.params.get('nat_gateway_ids')

    try:
        result = normalize_boto3_result(_describe_nat_gateways(client, module, **params))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, 'Unable to describe NAT gateways.')

    for gateway in result:
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

    try:
        connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    results = get_nat_gateways(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()

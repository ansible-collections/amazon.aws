#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_vpc_igw_info
version_added: 1.0.0
short_description: Gather information about internet gateways in AWS
description:
    - Gather information about internet gateways in AWS.
    - This module was called C(ec2_vpc_igw_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInternetGateways.html) for possible filters.
    type: dict
  internet_gateway_ids:
    description:
      - Get details of specific Internet Gateway ID. Provide this value as a list.
    type: list
    elements: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all Internet Gateways for an account or profile
  community.aws.ec2_vpc_igw_info:
    region: ap-southeast-2
    profile: production
  register: igw_info

- name: Gather information about a filtered list of Internet Gateways
  community.aws.ec2_vpc_igw_info:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "igw-123"
  register: igw_info

- name: Gather information about a specific internet gateway by InternetGatewayId
  community.aws.ec2_vpc_igw_info:
    region: ap-southeast-2
    profile: production
    internet_gateway_ids: igw-c1231234
  register: igw_info
'''

RETURN = r'''
internet_gateways:
    description: The internet gateways for the account.
    returned: always
    type: list
    sample: [
        {
            "attachments": [
                {
                    "state": "available",
                    "vpc_id": "vpc-02123b67"
                }
            ],
            "internet_gateway_id": "igw-2123634d",
            "tags": [
                {
                    "key": "Name",
                    "value": "test-vpc-20-igw"
                }
            ]
        }
    ]

changed:
    description: True if listing the internet gateways succeeds.
    type: bool
    returned: always
    sample: "false"
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list


def get_internet_gateway_info(internet_gateway):
    internet_gateway_info = {'InternetGatewayId': internet_gateway['InternetGatewayId'],
                             'Attachments': internet_gateway['Attachments'],
                             'Tags': internet_gateway['Tags']}
    return internet_gateway_info


def list_internet_gateways(client, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))

    if module.params.get("internet_gateway_ids"):
        params['InternetGatewayIds'] = module.params.get("internet_gateway_ids")

    try:
        all_internet_gateways = client.describe_internet_gateways(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    return [camel_dict_to_snake_dict(get_internet_gateway_info(igw))
            for igw in all_internet_gateways['InternetGateways']]


def main():
    argument_spec = dict(
        filters=dict(type='dict', default=dict()),
        internet_gateway_ids=dict(type='list', default=None, elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ec2_vpc_igw_facts':
        module.deprecate("The 'ec2_vpc_igw_facts' module has been renamed to 'ec2_vpc_igw_info'", date='2021-12-01', collection_name='community.aws')

    # Validate Requirements
    try:
        connection = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # call your function here
    results = list_internet_gateways(connection, module)

    module.exit_json(internet_gateways=results)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_dhcp_option_info
version_added: 1.0.0
short_description: Gather information about dhcp options sets in AWS
description:
    - Gather information about dhcp options sets in AWS.
    - This module was called C(ec2_vpc_dhcp_option_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeDhcpOptions.html) for possible filters.
    type: dict
  dhcp_options_ids:
    description:
      - Get details of specific DHCP Option IDs.
    aliases: ['DhcpOptionIds']
    type: list
    elements: str
  dry_run:
    description:
      - Checks whether you have the required permissions to view the DHCP
        Options.
    aliases: ['DryRun']
    type: bool
    default: false
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all DHCP Option sets for an account or profile
  amazon.aws.ec2_vpc_dhcp_option_info:
    region: ap-southeast-2
    profile: production
  register: dhcp_info

- name: Gather information about a filtered list of DHCP Option sets
  amazon.aws.ec2_vpc_dhcp_option_info:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "abc-123"
  register: dhcp_info

- name: Gather information about a specific DHCP Option set by DhcpOptionId
  amazon.aws.ec2_vpc_dhcp_option_info:
    region: ap-southeast-2
    profile: production
    DhcpOptionsIds: dopt-123fece2
  register: dhcp_info

'''

RETURN = '''
dhcp_options:
    description: The dhcp option sets for the account
    returned: always
    type: list

changed:
    description: True if listing the dhcp options succeeds
    type: bool
    returned: always
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict


def get_dhcp_options_info(dhcp_option):
    dhcp_option_info = {'DhcpOptionsId': dhcp_option['DhcpOptionsId'],
                        'DhcpConfigurations': dhcp_option['DhcpConfigurations'],
                        'Tags': boto3_tag_list_to_ansible_dict(dhcp_option.get('Tags', [{'Value': '', 'Key': 'Name'}]))}
    return dhcp_option_info


def list_dhcp_options(client, module):
    params = dict(Filters=ansible_dict_to_boto3_filter_list(module.params.get('filters')))

    if module.params.get("dry_run"):
        params['DryRun'] = True

    if module.params.get("dhcp_options_ids"):
        params['DhcpOptionsIds'] = module.params.get("dhcp_options_ids")

    try:
        all_dhcp_options = client.describe_dhcp_options(aws_retry=True, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    return [camel_dict_to_snake_dict(get_dhcp_options_info(option))
            for option in all_dhcp_options['DhcpOptions']]


def main():
    argument_spec = dict(
        filters=dict(type='dict', default={}),
        dry_run=dict(type='bool', default=False, aliases=['DryRun']),
        dhcp_options_ids=dict(type='list', elements='str', aliases=['DhcpOptionIds'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    if module._name == 'ec2_vpc_dhcp_option_facts':
        module.deprecate("The 'ec2_vpc_dhcp_option_facts' module has been renamed to 'ec2_vpc_dhcp_option_info'",
                         date='2021-12-01', collection_name='amazon.aws')

    client = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    # call your function here
    results = list_dhcp_options(client, module)

    module.exit_json(dhcp_options=results)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_vpc_dhcp_option_info
short_description: Gather information about dhcp options sets in AWS
description:
    - Gather information about dhcp options sets in AWS
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
extends_documentation_fragment:
- ansible.amazon.aws
- ansible.amazon.ec2

'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all DHCP Option sets for an account or profile
  ec2_vpc_dhcp_option_info:
    region: ap-southeast-2
    profile: production
  register: dhcp_info

- name: Gather information about a filtered list of DHCP Option sets
  ec2_vpc_dhcp_option_info:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "abc-123"
  register: dhcp_info

- name: Gather information about a specific DHCP Option set by DhcpOptionId
  ec2_vpc_dhcp_option_info:
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

import traceback

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.amazon.plugins.module_utils.ec2 import (ec2_argument_spec, boto3_conn, HAS_BOTO3,
                                      ansible_dict_to_boto3_filter_list, get_aws_connection_info,
                                      camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict)


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
        all_dhcp_options = client.describe_dhcp_options(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    return [camel_dict_to_snake_dict(get_dhcp_options_info(option))
            for option in all_dhcp_options['DhcpOptions']]


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(type='dict', default={}),
            dry_run=dict(type='bool', default=False, aliases=['DryRun']),
            dhcp_options_ids=dict(type='list', aliases=['DhcpOptionIds'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    if module._name == 'ec2_vpc_dhcp_option_facts':
        module.deprecate("The 'ec2_vpc_dhcp_option_facts' module has been renamed to 'ec2_vpc_dhcp_option_info'", version='2.13')

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - " + str(e))

    # call your function here
    results = list_dhcp_options(connection, module)

    module.exit_json(dhcp_options=results)


if __name__ == '__main__':
    main()

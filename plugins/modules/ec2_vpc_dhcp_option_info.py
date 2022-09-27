#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_dhcp_option_info
version_added: 1.0.0
short_description: Gather information about DHCP options sets in AWS
description:
  - Gather information about DHCP options sets in AWS.
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeDhcpOptions.html) for possible filters.
    type: dict
  dhcp_options_ids:
    description:
      - Get details of specific DHCP option IDs.
    type: list
    elements: str
  dry_run:
    description:
      - Checks whether you have the required permissions to view the DHCP
        options.
    type: bool
    default: false
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
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
    dhcp_options_ids: dopt-123fece2
  register: dhcp_info

'''

RETURN = '''
dhcp_options:
    description: The DHCP options created, associated or found.
    returned: always
    type: list
    elements: dict
    contains:
        dhcp_configurations:
            description: The DHCP configuration for the option set.
            type: list
            elements: dict
            contains:
                key:
                    description: The name of a DHCP option.
                    returned: always
                    type: str
                values:
                    description: List of values for the DHCP option.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        value:
                            description: The attribute value. This value is case-sensitive.
                            returned: always
                            type: str
            sample:
              - '{"key": "ntp-servers", "values": [{"value": "10.0.0.2" , "value": "10.0.1.2"}]}'
              - '{"key": "netbios-name-servers", "values": [{value": "10.0.0.1"}, {"value": "10.0.1.1" }]}'
        dhcp_options_id:
            description: The aws resource id of the primary DHCP options set created or found.
            type: str
            sample: "dopt-0955331de6a20dd07"
        owner_id:
            description: The ID of the AWS account that owns the DHCP options set.
            type: str
            sample: 012345678912
        tags:
            description: The tags to be applied to a DHCP options set.
            type: list
            elements: dict
            sample:
              - '{"Key": "CreatedBy", "Value": "ansible-test"}'
              - '{"Key": "Collection", "Value": "amazon.aws"}'
dhcp_config:
    description: The boto2-style DHCP options created, associated or found. Provided for consistency with ec2_vpc_dhcp_option's C(dhcp_config).
    returned: always
    type: list
    elements: dict
    contains:
      domain-name-servers:
        description: The IP addresses of up to four domain name servers, or AmazonProvidedDNS.
        returned: when available
        type: list
        sample:
          - 10.0.0.1
          - 10.0.1.1
      domain-name:
        description: The domain name for hosts in the DHCP option sets.
        returned: when available
        type: list
        sample:
          - "my.example.com"
      ntp-servers:
        description: The IP addresses of up to four Network Time Protocol (NTP) servers.
        returned: when available
        type: list
        sample:
          - 10.0.0.1
          - 10.0.1.1
      netbios-name-servers:
        description: The IP addresses of up to four NetBIOS name servers.
        returned: when available
        type: list
        sample:
          - 10.0.0.1
          - 10.0.1.1
      netbios-node-type:
        description: The NetBIOS node type (1, 2, 4, or 8).
        returned: when available
        type: str
        sample: 2
changed:
    description: True if listing the dhcp options succeeds.
    type: bool
    returned: always
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import normalize_ec2_vpc_dhcp_config


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

    normalized_config = [normalize_ec2_vpc_dhcp_config(config['DhcpConfigurations']) for config in all_dhcp_options['DhcpOptions']]
    raw_config = [camel_dict_to_snake_dict(get_dhcp_options_info(option), ignore_list=['Tags']) for option in all_dhcp_options['DhcpOptions']]
    return raw_config, normalized_config


def main():
    argument_spec = dict(
        filters=dict(type='dict', default={}),
        dry_run=dict(type='bool', default=False),
        dhcp_options_ids=dict(type='list', elements='str'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    # call your function here
    results, normalized_config = list_dhcp_options(client, module)

    module.exit_json(dhcp_options=results, dhcp_config=normalized_config)


if __name__ == '__main__':
    main()

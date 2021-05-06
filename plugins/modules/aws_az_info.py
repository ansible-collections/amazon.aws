#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
module: aws_az_info
short_description: Gather information about availability zones in AWS.
version_added: 1.0.0
description:
    - Gather information about availability zones in AWS.
    - This module was called M(amazon.aws.aws_az_facts) before Ansible 2.9. The usage did not change.
author: 'Henrique Rodrigues (@Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply.
      - Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeAvailabilityZones.html) for possible filters.
      - Filter names and values are case sensitive.
      - You can use underscores instead of dashes (-) in the filter keys.
      - Filter keys with underscores will take precedence in case of conflict.
    required: false
    default: {}
    type: dict
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all availability zones
  amazon.aws.aws_az_info:

- name: Gather information about a single availability zone
  amazon.aws.aws_az_info:
    filters:
      zone-name: eu-west-1a
'''

RETURN = '''
availability_zones:
    returned: on success
    description: >
        Availability zones that match the provided filters. Each element consists of a dict with all the information
        related to that available zone.
    type: list
    sample: "[
        {
            'messages': [],
            'region_name': 'us-west-1',
            'state': 'available',
            'zone_name': 'us-west-1b'
        },
        {
            'messages': [],
            'region_name': 'us-west-1',
            'state': 'available',
            'zone_name': 'us-west-1c'
        }
    ]"
'''

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_filter_list


def main():
    argument_spec = dict(
        filters=dict(default={}, type='dict')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'aws_az_facts':
        module.deprecate("The 'aws_az_facts' module has been renamed to 'aws_az_info'", date='2022-06-01', collection_name='amazon.aws')

    connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict(module.params.get('filters'))
    for k in module.params.get('filters').keys():
        if "_" in k:
            sanitized_filters[k.replace('_', '-')] = sanitized_filters[k]
            del sanitized_filters[k]

    try:
        availability_zones = connection.describe_availability_zones(aws_retry=True, Filters=ansible_dict_to_boto3_filter_list(sanitized_filters))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe availability zones.")

    # Turn the boto3 result into ansible_friendly_snaked_names
    snaked_availability_zones = [camel_dict_to_snake_dict(az) for az in availability_zones['AvailabilityZones']]

    module.exit_json(availability_zones=snaked_availability_zones)


if __name__ == '__main__':
    main()

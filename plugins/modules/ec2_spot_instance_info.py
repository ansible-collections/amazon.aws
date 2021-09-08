#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_spot_instance_info
version_added: 2.0.0
short_description: Gather information about ec2 spot instance requests
description:
  - Describes the specified Spot Instance requests.
author:
  - Mandar Vijay Kulkarni (@mandar242)
options:
  filters:
    description:
      - A list of filters to apply.
      - Each list item is a dict consisting of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSpotInstanceRequests.html) for possible filters.
    type: list
    elements: dict
  dry_run:
    description:
      - A boolean to check if you have the required permissions for the action.
      - Does not make the request.
      - If required permissions are not present then returns an error response UnauthorizedOperation else DryRunOperation.
    default: False
    choices: [ True, False ]
    type: bool
  spot_instance_request_ids:
    description:
      - One or more Spot Instance request IDs.
    type: list
    elements: str
  next_token:
    description:
      - A token to request the next set of results.
      - Value is null when no more results to return
    type: str
  max_results:
    description:
      - Maximum number of results to be returned in a single call.
      - Value can be between 5 and 1000.
    type: int

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: describe the Spot Instance requests based on request IDs
  amazon.aws.ec2_spot_instance_info:
    spot_instance_request_ids:
      - sir-12345678

- name: describe the Spot Instance requests and filter results based on instance type
  amazon.aws.ec2_spot_instance_info:
    spot_instance_request_ids:
      - sir-12345678
      - sir-13579246
      - sir-87654321
    filters:
      - name: 'launch.instance-type'
        values:
          - t3.medium

'''

RETURN = '''
spot_request:
    description:  The gathered information about specified spot instance requests.
    returned: when success
    type: dict
    sample: {
        "create_time": "2021-09-01T21:05:57+00:00",
        "instance_id": "i-08877936b801ac475",
        "instance_interruption_behavior": "terminate",
        "launch_specification": {
            "ebs_optimized": false,
            "image_id": "ami-0443305dabd4be2bc",
            "instance_type": "t2.medium",
            "key_name": "zuul",
            "monitoring": {
                "enabled": false
            },
            "placement": {
                "availability_zone": "us-east-2b"
            },
            "security_groups": [
                {
                    "group_id": "sg-01f9833207d53b937",
                    "group_name": "default"
                }
            ],
            "subnet_id": "subnet-07d906b8358869bda"
        },
        "launched_availability_zone": "us-east-2b",
        "product_description": "Linux/UNIX",
        "spot_instance_request_id": "sir-c3cp9jsk",
        "spot_price": "0.046400",
        "state": "active",
        "status": {
            "code": "fulfilled",
            "message": "Your spot request is fulfilled.",
            "update_time": "2021-09-01T21:05:59+00:00"
        },
        "tags": {},
        "type": "one-time",
        "valid_until": "2021-09-08T21:05:57+00:00"
      }
'''

import time
import datetime

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code


def describe_spot_instance_requests(connection, module):

    changed = True

    if module.check_mode:
        module.exit_json(changed=changed)

    params = {}

    if module.params.get('filters'):
        filters_dit = module.params.get('filters')
        camel_filters = snake_dict_to_camel_dict(filters_dit, capitalize_first=True)
        params['Filters'] = camel_filters
    if module.params.get('dry_run'):
        params['DryRun'] = module.params.get('dry_run')
    if module.params.get('spot_instance_request_ids'):
        params['SpotInstanceRequestIds'] = module.params.get('spot_instance_request_ids')
    if module.params.get('next_token'):
        params['NextToken'] = module.params.get('next_token')
    if module.params.get('max_results'):
        params['MaxResults'] = module.params.get('max_results')

    try:
        describe_spot_instance_requests_response = (connection.describe_spot_instance_requests(**params))['SpotInstanceRequests']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe sport instance requests')

    spot_request = {'spot_instance_requests': []}
    for response_list_item in describe_spot_instance_requests_response:
        spot_request['spot_instance_requests'].append(camel_dict_to_snake_dict(response_list_item))

    module.exit_json(spot_request=spot_request['spot_instance_requests'], changed=changed)


def main():

    argument_spec = dict(
        filters=dict(default=[], type='list', elements='dict'),
        dry_run=dict(default=False, type='bool', choices=[True, False]),
        spot_instance_request_ids=dict(default=[], type='list', elements='str'),
        next_token=dict(default=None, type='str', no_log=False),
        max_results=dict(type='int')
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    try:
        connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    describe_spot_instance_requests(connection, module)


if __name__ == '__main__':
    main()

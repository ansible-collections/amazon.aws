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
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - Filter names and values are case sensitive.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSpotInstanceRequests.html) for possible filters.
    required: false
    default: {}
    type: dict
  spot_instance_request_ids:
    description:
      - One or more Spot Instance request IDs.
    required: false
    type: list
    elements: str

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
        launch.instance-type: t3.medium

- name: describe the Spot requests filtered using multiple filters
  amazon.aws.ec2_spot_instance_info:
    filters:
        state: active
        launch.block-device-mapping.device-name: /dev/sdb

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


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list


def _describe_spot_instance_requests(connection, **params):
    paginator = connection.get_paginator('describe_spot_instance_requests')
    return paginator.paginate(**params).build_full_result()


def describe_spot_instance_requests(connection, module):

    params = {}

    if module.params.get('filters'):
        params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('spot_instance_request_ids'):
        params['SpotInstanceRequestIds'] = module.params.get('spot_instance_request_ids')

    try:
        describe_spot_instance_requests_response = _describe_spot_instance_requests(connection, **params)['SpotInstanceRequests']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe spot instance requests')

    spot_request = []
    for response_list_item in describe_spot_instance_requests_response:
        spot_request.append(camel_dict_to_snake_dict(response_list_item))

    if len(spot_request) == 0:
        module.exit_json(msg='No spot requests found for specified options')

    module.exit_json(spot_request=spot_request)


def main():

    argument_spec = dict(
        filters=dict(default={}, type='dict'),
        spot_instance_request_ids=dict(default=[], type='list', elements='str'),
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

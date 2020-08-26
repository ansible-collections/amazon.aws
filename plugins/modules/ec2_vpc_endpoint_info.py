#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_endpoint_info
short_description: Retrieves AWS VPC endpoints details using AWS methods.
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC Endpoints.
  - This module was called C(ec2_vpc_endpoint_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
options:
  query:
    description:
      - Specifies the query action to take. Services returns the supported
        AWS services that can be specified when creating an endpoint.
    required: True
    choices:
      - services
      - endpoints
    type: str
  vpc_endpoint_ids:
    description:
      - Get details of specific endpoint IDs
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcEndpoints.html)
        for possible filters.
    type: dict
author: Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Simple example of listing all support AWS services for VPC endpoints
- name: List supported AWS endpoint services
  community.aws.ec2_vpc_endpoint_info:
    query: services
    region: ap-southeast-2
  register: supported_endpoint_services

- name: Get all endpoints in ap-southeast-2 region
  community.aws.ec2_vpc_endpoint_info:
    query: endpoints
    region: ap-southeast-2
  register: existing_endpoints

- name: Get all endpoints with specific filters
  community.aws.ec2_vpc_endpoint_info:
    query: endpoints
    region: ap-southeast-2
    filters:
      vpc-id:
        - vpc-12345678
        - vpc-87654321
      vpc-endpoint-state:
        - available
        - pending
  register: existing_endpoints

- name: Get details on specific endpoint
  community.aws.ec2_vpc_endpoint_info:
    query: endpoints
    region: ap-southeast-2
    vpc_endpoint_ids:
      - vpce-12345678
  register: endpoint_details
'''

RETURN = r'''
service_names:
  description: AWS VPC endpoint service names
  returned: I(query) is C(services)
  type: list
  sample:
    service_names:
    - com.amazonaws.ap-southeast-2.s3
vpc_endpoints:
  description:
    - A list of endpoints that match the query. Each endpoint has the keys creation_timestamp,
      policy_document, route_table_ids, service_name, state, vpc_endpoint_id, vpc_id.
  returned: I(query) is C(endpoints)
  type: list
  sample:
    vpc_endpoints:
    - creation_timestamp: "2017-02-16T11:06:48+00:00"
      policy_document: >
        "{\"Version\":\"2012-10-17\",\"Id\":\"Policy1450910922815\",
        \"Statement\":[{\"Sid\":\"Stmt1450910920641\",\"Effect\":\"Allow\",
        \"Principal\":\"*\",\"Action\":\"s3:*\",\"Resource\":[\"arn:aws:s3:::*/*\",\"arn:aws:s3:::*\"]}]}"
      route_table_ids:
      - rtb-abcd1234
      service_name: "com.amazonaws.ap-southeast-2.s3"
      state: "available"
      vpc_endpoint_id: "vpce-abbad0d0"
      vpc_id: "vpc-1111ffff"
'''

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


@AWSRetry.exponential_backoff()
def get_supported_services(client, module):
    results = list()
    params = dict()
    while True:
        response = client.describe_vpc_endpoint_services(**params)
        results.extend(response['ServiceNames'])
        if 'NextToken' in response:
            params['NextToken'] = response['NextToken']
        else:
            break
    return dict(service_names=results)


@AWSRetry.exponential_backoff()
def get_endpoints(client, module):
    results = list()
    params = dict()
    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('vpc_endpoint_ids'):
        params['VpcEndpointIds'] = module.params.get('vpc_endpoint_ids')
    while True:
        response = client.describe_vpc_endpoints(**params)
        results.extend(response['VpcEndpoints'])
        if 'NextToken' in response:
            params['NextToken'] = response['NextToken']
        else:
            break
    try:
        results = json.loads(json.dumps(results, default=date_handler))
    except Exception as e:
        module.fail_json_aws(e, msg="Failed to get endpoints")
    return dict(vpc_endpoints=[camel_dict_to_snake_dict(result) for result in results])


def main():
    argument_spec = dict(
        query=dict(choices=['services', 'endpoints'], required=True),
        filters=dict(default={}, type='dict'),
        vpc_endpoint_ids=dict(type='list', elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ec2_vpc_endpoint_facts':
        module.deprecate("The 'ec2_vpc_endpoint_facts' module has been renamed to 'ec2_vpc_endpoint_info'", date='2021-12-01', collection_name='community.aws')

    # Validate Requirements
    try:
        connection = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    invocations = {
        'services': get_supported_services,
        'endpoints': get_endpoints,
    }
    results = invocations[module.params.get('query')](connection, module)

    module.exit_json(**results)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_endpoint_info
short_description: Retrieves AWS VPC endpoints details using AWS methods.
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC endpoints.
options:
  query:
    description:
      - Defaults to C(endpoints).
      - Specifies the query action to take.
      - I(query=endpoints) returns information about AWS VPC endpoints.
      - Retrieving information about services using I(query=services) has been
        deprecated in favour of the M(amazon.aws.ec2_vpc_endpoint_service_info) module.
      - The I(query) option has been deprecated and will be removed after 2022-12-01.
    required: False
    choices:
      - services
      - endpoints
    type: str
  vpc_endpoint_ids:
    description:
      - The IDs of specific endpoints to retrieve the details of.
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
  amazon.aws.ec2_vpc_endpoint_info:
    query: services
    region: ap-southeast-2
  register: supported_endpoint_services

- name: Get all endpoints in ap-southeast-2 region
  amazon.aws.ec2_vpc_endpoint_info:
    query: endpoints
    region: ap-southeast-2
  register: existing_endpoints

- name: Get all endpoints with specific filters
  amazon.aws.ec2_vpc_endpoint_info:
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
  amazon.aws.ec2_vpc_endpoint_info:
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

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list


@AWSRetry.jittered_backoff()
def _describe_endpoints(client, **params):
    paginator = client.get_paginator('describe_vpc_endpoints')
    return paginator.paginate(**params).build_full_result()


@AWSRetry.jittered_backoff()
def _describe_endpoint_services(client, **params):
    paginator = client.get_paginator('describe_vpc_endpoint_services')
    return paginator.paginate(**params).build_full_result()


def get_supported_services(client, module):
    try:
        services = _describe_endpoint_services(client)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to get endpoint servicess")

    results = list(services['ServiceNames'])
    return dict(service_names=results)


def get_endpoints(client, module):
    results = list()
    params = dict()
    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('vpc_endpoint_ids'):
        params['VpcEndpointIds'] = module.params.get('vpc_endpoint_ids')
    try:
        results = _describe_endpoints(client, **params)['VpcEndpoints']
        results = normalize_boto3_result(results)
    except is_boto3_error_code('InvalidVpcEndpointId.NotFound'):
        module.exit_json(msg='VpcEndpoint {0} does not exist'.format(module.params.get('vpc_endpoint_ids')), vpc_endpoints=[])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get endpoints")

    return dict(vpc_endpoints=[camel_dict_to_snake_dict(result) for result in results])


def main():
    argument_spec = dict(
        query=dict(choices=['services', 'endpoints'], required=False),
        filters=dict(default={}, type='dict'),
        vpc_endpoint_ids=dict(type='list', elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    try:
        connection = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    query = module.params.get('query')
    if query == 'endpoints':
        module.deprecate('The query option has been deprecated and'
                         ' will be removed after 2022-12-01.  Searching for'
                         ' `endpoints` is now the default and after'
                         ' 2022-12-01 this module will only support fetching'
                         ' endpoints.',
                         date='2022-12-01', collection_name='amazon.aws')
    elif query == 'services':
        module.deprecate('Support for fetching service information with this '
                         'module has been deprecated and will be removed after'
                         ' 2022-12-01.  '
                         'Please use the ec2_vpc_endpoint_service_info module '
                         'instead.', date='2022-12-01',
                         collection_name='amazon.aws')
    else:
        query = 'endpoints'

    invocations = {
        'services': get_supported_services,
        'endpoints': get_endpoints,
    }
    results = invocations[query](connection, module)

    module.exit_json(**results)


if __name__ == '__main__':
    main()

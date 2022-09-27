#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_endpoint
short_description: Create and delete AWS VPC endpoints
version_added: 1.0.0
description:
  - Creates AWS VPC endpoints.
  - Deletes AWS VPC endpoints.
  - This module supports check mode.
options:
  vpc_id:
    description:
      - Required when creating a VPC endpoint.
    required: false
    type: str
  vpc_endpoint_type:
    description:
      - The type of endpoint.
    required: false
    default: Gateway
    choices: [ "Interface", "Gateway", "GatewayLoadBalancer" ]
    type: str
    version_added: 1.5.0
  vpc_endpoint_subnets:
    description:
      - The list of subnets to attach to the endpoint.
      - Requires I(vpc_endpoint_type=GatewayLoadBalancer) or I(vpc_endpoint_type=Interface).
    required: false
    type: list
    elements: str
    version_added: 2.1.0
  vpc_endpoint_security_groups:
    description:
      - The list of security groups to attach to the endpoint.
      - Requires I(vpc_endpoint_type=GatewayLoadBalancer) or I(vpc_endpoint_type=Interface).
    required: false
    type: list
    elements: str
    version_added: 2.1.0
  service:
    description:
      - An AWS supported VPC endpoint service. Use the M(amazon.aws.ec2_vpc_endpoint_info)
        module to describe the supported endpoint services.
      - Required when creating an endpoint.
    required: false
    type: str
  policy:
    description:
      - A properly formatted JSON policy as string, see
        U(https://github.com/ansible/ansible/issues/7005#issuecomment-42894813).
        Cannot be used with I(policy_file).
      - Option when creating an endpoint. If not provided AWS will
        utilise a default policy which provides full access to the service.
    required: false
    type: json
  policy_file:
    description:
      - The path to the properly json formatted policy file, see
        U(https://github.com/ansible/ansible/issues/7005#issuecomment-42894813)
        on how to use it properly. Cannot be used with I(policy).
      - Option when creating an endpoint. If not provided AWS will
        utilise a default policy which provides full access to the service.
      - This option has been deprecated and will be removed after 2022-12-01
        to maintain the existing functionality please use the I(policy) option
        and a file lookup.
    required: false
    aliases: [ "policy_path" ]
    type: path
  state:
    description:
      - C(present) to ensure resource is created.
      - C(absent) to remove resource.
    required: false
    default: present
    choices: [ "present", "absent" ]
    type: str
  wait:
    description:
      - When specified, will wait for status to reach C(available) for I(state=present).
      - Unfortunately this is ignored for delete actions due to a difference in
        behaviour from AWS.
    required: false
    default: false
    type: bool
  wait_timeout:
    description:
      - Used in conjunction with I(wait).
      - Number of seconds to wait for status.
      - Unfortunately this is ignored for delete actions due to a difference in
        behaviour from AWS.
    required: false
    default: 320
    type: int
  route_table_ids:
    description:
      - List of one or more route table IDs to attach to the endpoint.
      - A route is added to the route table with the destination of the
        endpoint if provided.
      - Route table IDs are only valid for C(Gateway) endpoints.
    required: false
    type: list
    elements: str
  vpc_endpoint_id:
    description:
      - One or more VPC endpoint IDs to remove from the AWS account.
      - Required if I(state=absent).
    required: false
    type: str
  client_token:
    description:
      - Optional client token to ensure idempotency.
    required: false
    type: str
author:
  - Karen Cheng (@Etherdaemon)
notes:
  - Support for I(tags) and I(purge_tags) was added in release 1.5.0.
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
  - amazon.aws.boto3
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create new vpc endpoint with a json template for policy
  amazon.aws.ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    policy: " {{ lookup( 'template', 'endpoint_policy.json.j2') }} "
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Create new vpc endpoint with the default policy
  amazon.aws.ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Create new vpc endpoint with json file
  amazon.aws.ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    policy_file: "{{ role_path }}/files/endpoint_policy.json"
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Delete newly created vpc endpoint
  amazon.aws.ec2_vpc_endpoint:
    state: absent
    vpc_endpoint_id: "{{ new_vpc_endpoint.result['VpcEndpointId'] }}"
    region: ap-southeast-2
'''

RETURN = r'''
endpoints:
  description: The resulting endpoints from the module call
  returned: success
  type: list
  sample: [
      {
        "creation_timestamp": "2017-02-20T05:04:15+00:00",
        "policy_document": {
          "Id": "Policy1450910922815",
          "Statement": [
            {
              "Action": "s3:*",
              "Effect": "Allow",
              "Principal": "*",
              "Resource": [
                "arn:aws:s3:::*/*",
                "arn:aws:s3:::*"
              ],
              "Sid": "Stmt1450910920641"
            }
          ],
          "Version": "2012-10-17"
        },
        "route_table_ids": [
          "rtb-abcd1234"
        ],
        "service_name": "com.amazonaws.ap-southeast-2.s3",
        "vpc_endpoint_id": "vpce-a1b2c3d4",
        "vpc_id": "vpc-abbad0d0"
      }
    ]
'''

import datetime
import json
import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.six import string_types
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications


def get_endpoints(client, module, endpoint_id=None):
    params = dict()
    if endpoint_id:
        params['VpcEndpointIds'] = [endpoint_id]
    else:
        filters = list()
        if module.params.get('service'):
            filters.append({'Name': 'service-name', 'Values': [module.params.get('service')]})
        if module.params.get('vpc_id'):
            filters.append({'Name': 'vpc-id', 'Values': [module.params.get('vpc_id')]})
        params['Filters'] = filters
    try:
        result = client.describe_vpc_endpoints(aws_retry=True, **params)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to get endpoints")

    # normalize iso datetime fields in result
    normalized_result = normalize_boto3_result(result)
    return normalized_result


def match_endpoints(route_table_ids, service_name, vpc_id, endpoint):
    found = False
    sorted_route_table_ids = []

    if route_table_ids:
        sorted_route_table_ids = sorted(route_table_ids)

    if endpoint['VpcId'] == vpc_id and endpoint['ServiceName'] == service_name:
        sorted_endpoint_rt_ids = sorted(endpoint['RouteTableIds'])
        if sorted_endpoint_rt_ids == sorted_route_table_ids:
            found = True
    return found


def setup_creation(client, module):
    endpoint_id = module.params.get('vpc_endpoint_id')
    route_table_ids = module.params.get('route_table_ids')
    service_name = module.params.get('service')
    vpc_id = module.params.get('vpc_id')
    changed = False

    if not endpoint_id:
        # Try to use the module parameters to match any existing endpoints
        all_endpoints = get_endpoints(client, module, endpoint_id)
        if len(all_endpoints['VpcEndpoints']) > 0:
            for endpoint in all_endpoints['VpcEndpoints']:
                if match_endpoints(route_table_ids, service_name, vpc_id, endpoint):
                    endpoint_id = endpoint['VpcEndpointId']
                    break

    if endpoint_id:
        # If we have an endpoint now, just ensure tags and exit
        if module.params.get('tags'):
            changed |= ensure_ec2_tags(client, module, endpoint_id,
                                       resource_type='vpc-endpoint',
                                       tags=module.params.get('tags'),
                                       purge_tags=module.params.get('purge_tags'))
        normalized_result = get_endpoints(client, module, endpoint_id=endpoint_id)['VpcEndpoints'][0]
        return changed, camel_dict_to_snake_dict(normalized_result, ignore_list=['Tags'])

    changed, result = create_vpc_endpoint(client, module)

    return changed, camel_dict_to_snake_dict(result, ignore_list=['Tags'])


def create_vpc_endpoint(client, module):
    params = dict()
    changed = False
    token_provided = False
    params['VpcId'] = module.params.get('vpc_id')
    params['VpcEndpointType'] = module.params.get('vpc_endpoint_type')
    params['ServiceName'] = module.params.get('service')

    if module.params.get('vpc_endpoint_type') != 'Gateway' and module.params.get('route_table_ids'):
        module.fail_json(msg="Route table IDs are only supported for Gateway type VPC Endpoint.")

    if module.check_mode:
        changed = True
        result = 'Would have created VPC Endpoint if not in check mode'
        module.exit_json(changed=changed, result=result)

    if module.params.get('route_table_ids'):
        params['RouteTableIds'] = module.params.get('route_table_ids')

    if module.params.get('vpc_endpoint_subnets'):
        params['SubnetIds'] = module.params.get('vpc_endpoint_subnets')

    if module.params.get('vpc_endpoint_security_groups'):
        params['SecurityGroupIds'] = module.params.get('vpc_endpoint_security_groups')

    if module.params.get('client_token'):
        token_provided = True
        request_time = datetime.datetime.utcnow()
        params['ClientToken'] = module.params.get('client_token')

    policy = None
    if module.params.get('policy'):
        try:
            policy = json.loads(module.params.get('policy'))
        except ValueError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    elif module.params.get('policy_file'):
        try:
            with open(module.params.get('policy_file'), 'r') as json_data:
                policy = json.load(json_data)
        except (OSError, json.JSONDecodeError) as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    if policy:
        params['PolicyDocument'] = json.dumps(policy)

    if module.params.get('tags'):
        params["TagSpecifications"] = boto3_tag_specifications(module.params.get('tags'), ['vpc-endpoint'])

    try:
        changed = True
        result = client.create_vpc_endpoint(aws_retry=True, **params)['VpcEndpoint']
        if token_provided and (request_time > result['creation_timestamp'].replace(tzinfo=None)):
            changed = False
        elif module.params.get('wait') and not module.check_mode:
            try:
                waiter = get_waiter(client, 'vpc_endpoint_exists')
                waiter.wait(VpcEndpointIds=[result['VpcEndpointId']], WaiterConfig=dict(Delay=15, MaxAttempts=module.params.get('wait_timeout') // 15))
            except botocore.exceptions.WaiterError as e:
                module.fail_json_aws(msg='Error waiting for vpc endpoint to become available - please check the AWS console')
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
                module.fail_json_aws(e, msg='Failure while waiting for status')

    except is_boto3_error_code('IdempotentParameterMismatch'):  # pylint: disable=duplicate-except
        module.fail_json(msg="IdempotentParameterMismatch - updates of endpoints are not allowed by the API")
    except is_boto3_error_code('RouteAlreadyExists'):  # pylint: disable=duplicate-except
        module.fail_json(msg="RouteAlreadyExists for one of the route tables - update is not allowed by the API")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to create VPC.")

    # describe and normalize iso datetime fields in result after adding tags
    normalized_result = get_endpoints(client, module, endpoint_id=result['VpcEndpointId'])['VpcEndpoints'][0]
    return changed, normalized_result


def setup_removal(client, module):
    params = dict()
    changed = False

    if module.check_mode:
        try:
            exists = client.describe_vpc_endpoints(aws_retry=True, VpcEndpointIds=[module.params.get('vpc_endpoint_id')])
            if exists:
                result = {'msg': 'Would have deleted VPC Endpoint if not in check mode'}
                changed = True
        except is_boto3_error_code('InvalidVpcEndpointId.NotFound'):
            result = {'msg': 'Endpoint does not exist, nothing to delete.'}
            changed = False
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to get endpoints")

        return changed, result

    if isinstance(module.params.get('vpc_endpoint_id'), string_types):
        params['VpcEndpointIds'] = [module.params.get('vpc_endpoint_id')]
    else:
        params['VpcEndpointIds'] = module.params.get('vpc_endpoint_id')
    try:
        result = client.delete_vpc_endpoints(aws_retry=True, **params)['Unsuccessful']
        if len(result) < len(params['VpcEndpointIds']):
            changed = True
        # For some reason delete_vpc_endpoints doesn't throw exceptions it
        # returns a list of failed 'results' instead.  Throw these so we can
        # catch them the way we expect
        for r in result:
            try:
                raise botocore.exceptions.ClientError(r, 'delete_vpc_endpoints')
            except is_boto3_error_code('InvalidVpcEndpoint.NotFound'):
                continue

    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, "Failed to delete VPC endpoint")
    return changed, result


def main():
    argument_spec = dict(
        vpc_id=dict(),
        vpc_endpoint_type=dict(default='Gateway', choices=['Interface', 'Gateway', 'GatewayLoadBalancer']),
        vpc_endpoint_security_groups=dict(type='list', elements='str'),
        vpc_endpoint_subnets=dict(type='list', elements='str'),
        service=dict(),
        policy=dict(type='json'),
        policy_file=dict(type='path', aliases=['policy_path']),
        state=dict(default='present', choices=['present', 'absent']),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=320, required=False),
        route_table_ids=dict(type='list', elements='str'),
        vpc_endpoint_id=dict(),
        client_token=dict(no_log=False),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['policy', 'policy_file']],
        required_if=[
            ['state', 'present', ['vpc_id', 'service']],
            ['state', 'absent', ['vpc_endpoint_id']],
        ],
    )

    # Validate Requirements
    state = module.params.get('state')

    if module.params.get('policy_file'):
        module.deprecate('The policy_file option has been deprecated and'
                         ' will be removed after 2022-12-01',
                         date='2022-12-01', collection_name='amazon.aws')

    if module.params.get('vpc_endpoint_type'):
        if module.params.get('vpc_endpoint_type') == 'Gateway':
            if module.params.get('vpc_endpoint_subnets') or module.params.get('vpc_endpoint_security_groups'):
                module.fail_json(msg="Parameter vpc_endpoint_subnets and/or vpc_endpoint_security_groups can't be used with Gateway endpoint type")

        if module.params.get('vpc_endpoint_type') == 'GatewayLoadBalancer':
            if module.params.get('vpc_endpoint_security_groups'):
                module.fail_json(msg="Parameter vpc_endpoint_security_groups can't be used with GatewayLoadBalancer endpoint type")

        if module.params.get('vpc_endpoint_type') == 'Interface':
            if module.params.get('vpc_endpoint_subnets') and not module.params.get('vpc_endpoint_security_groups'):
                module.fail_json(msg="Parameter vpc_endpoint_security_groups must be set when endpoint type is Interface and vpc_endpoint_subnets is defined")
            if not module.params.get('vpc_endpoint_subnets') and module.params.get('vpc_endpoint_security_groups'):
                module.fail_json(msg="Parameter vpc_endpoint_subnets must be set when endpoint type is Interface and vpc_endpoint_security_groups is defined")

    try:
        ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # Ensure resource is present
    if state == 'present':
        (changed, results) = setup_creation(ec2, module)
    else:
        (changed, results) = setup_removal(ec2, module)

    module.exit_json(changed=changed, result=results)


if __name__ == '__main__':
    main()

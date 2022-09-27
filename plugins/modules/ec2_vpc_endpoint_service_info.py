#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_endpoint_service_info
short_description: Retrieves AWS VPC endpoint service details
version_added: 1.5.0
description:
  - Gets details related to AWS VPC Endpoint Services.
options:
  filters:
    description:
      - A dict of filters to apply.
      - Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcEndpointServices.html)
        for possible filters.
    type: dict
  service_names:
    description:
      - A list of service names which can be used to narrow the search results.
    type: list
    elements: str
author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = r'''
# Simple example of listing all supported AWS services for VPC endpoints
- name: List supported AWS endpoint services
  amazon.aws.ec2_vpc_endpoint_service_info:
    region: ap-southeast-2
  register: supported_endpoint_services
'''

RETURN = r'''
service_names:
  description: List of supported AWS VPC endpoint service names.
  returned: success
  type: list
  sample:
    service_names:
    - com.amazonaws.ap-southeast-2.s3
service_details:
  description: Detailed information about the AWS VPC endpoint services.
  returned: success
  type: complex
  contains:
    service_name:
      returned: success
      description: The ARN of the endpoint service.
      type: str
    service_id:
      returned: success
      description: The ID of the endpoint service.
      type: str
    service_type:
      returned: success
      description: The type of the service
      type: list
    availability_zones:
      returned: success
      description: The Availability Zones in which the service is available.
      type: list
    owner:
      returned: success
      description: The AWS account ID of the service owner.
      type: str
    base_endpoint_dns_names:
      returned: success
      description: The DNS names for the service.
      type: list
    private_dns_name:
      returned: success
      description: The private DNS name for the service.
      type: str
    private_dns_names:
      returned: success
      description: The private DNS names assigned to the VPC endpoint service.
      type: list
    vpc_endpoint_policy_supported:
      returned: success
      description: Whether the service supports endpoint policies.
      type: bool
    acceptance_required:
      returned: success
      description:
        Whether VPC endpoint connection requests to the service must be
        accepted by the service owner.
      type: bool
    manages_vpc_endpoints:
      returned: success
      description: Whether the service manages its VPC endpoints.
      type: bool
    tags:
      returned: success
      description: A dict of tags associated with the service
      type: dict
    private_dns_name_verification_state:
      returned: success
      description:
      - The verification state of the VPC endpoint service.
      - Consumers of an endpoint service cannot use the private name when the state is not C(verified).
      type: str
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


# We're using a paginator so we can't use the client decorators
@AWSRetry.jittered_backoff()
def get_services(client, module):
    paginator = client.get_paginator('describe_vpc_endpoint_services')
    params = {}
    if module.params.get("filters"):
        params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    if module.params.get("service_names"):
        params['ServiceNames'] = module.params.get("service_names")

    results = paginator.paginate(**params).build_full_result()
    return results


def normalize_service(service):
    normalized = camel_dict_to_snake_dict(service, ignore_list=['Tags'])
    normalized["tags"] = boto3_tag_list_to_ansible_dict(service.get('Tags'))
    return normalized


def normalize_result(result):
    normalized = {}
    normalized['service_details'] = [normalize_service(service) for service in result.get('ServiceDetails')]
    normalized['service_names'] = result.get('ServiceNames', [])
    return normalized


def main():
    argument_spec = dict(
        filters=dict(default={}, type='dict'),
        service_names=dict(type='list', elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    try:
        client = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    try:
        results = get_services(client, module)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to retrieve service details')
    normalized_result = normalize_result(results)

    module.exit_json(changed=False, **normalized_result)


if __name__ == '__main__':
    main()

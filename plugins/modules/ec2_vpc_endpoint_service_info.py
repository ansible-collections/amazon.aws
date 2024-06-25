#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
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
    default: {}
  service_names:
    description:
      - A list of service names which can be used to narrow the search results.
    type: list
    elements: str
author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Simple example of listing all supported AWS services for VPC endpoints
- name: List supported AWS endpoint services
  amazon.aws.ec2_vpc_endpoint_service_info:
    region: ap-southeast-2
  register: supported_endpoint_services
"""

RETURN = r"""
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
    supported_ip_address_types:
      returned: success
      description: The supported IP address types.
      type: str
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_endpoint_services
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def normalize_service(service):
    normalized = camel_dict_to_snake_dict(service, ignore_list=["Tags"])
    normalized["tags"] = boto3_tag_list_to_ansible_dict(service.get("Tags"))
    return normalized


def normalize_result(result):
    normalized = {}
    normalized["service_details"] = [normalize_service(service) for service in result.get("ServiceDetails")]
    normalized["service_names"] = result.get("ServiceNames", [])
    return normalized


def list_endpoint_services(client, module: AnsibleAWSModule) -> None:
    try:
        filters = None
        if module.params.get("filters"):
            filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
        results = describe_vpc_endpoint_services(
            client, filters=filters, service_names=module.params.get("service_names")
        )
        if results:
            results = normalize_result(results)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to connect to retrieve service details")
    module.exit_json(changed=False, **results)


def main() -> None:
    argument_spec = dict(
        filters=dict(default={}, type="dict"),
        service_names=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    try:
        client = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    list_endpoint_services(client, module)


if __name__ == "__main__":
    main()

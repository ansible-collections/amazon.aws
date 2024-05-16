#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_endpoint_info
short_description: Retrieves AWS VPC endpoints details using AWS methods
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC endpoints.
options:
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
    default: {}
author:
  - Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
notes:
  - Support for the I(query) parameter was dropped in release 6.0.0.  This module now only queries
    for endpoints. Information about endpoint services can be retrieved using the
    M(amazon.aws.ec2_vpc_endpoint_service_info) module.
"""

EXAMPLES = r"""
# Simple example of listing all support AWS services for VPC endpoints
- name: Get all endpoints in ap-southeast-2 region
  amazon.aws.ec2_vpc_endpoint_info:
    region: ap-southeast-2
  register: existing_endpoints

- name: Get all endpoints with specific filters
  amazon.aws.ec2_vpc_endpoint_info:
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
    region: ap-southeast-2
    vpc_endpoint_ids:
      - vpce-12345678
  register: endpoint_details
"""

RETURN = r"""
vpc_endpoints:
  description:
    - A list of matching endpoints.
  returned: always
  type: list
  elements: dict
  contains:
    creation_timestamp:
      description: The date and time that the endpoint was created.
      returned: always
      type: str
    dns_entries:
      description: List of DNS entires for the endpoint.
      returned: always
      type: list
      elements: dict
      contains:
        dns_name:
          description: The DNS name.
          returned: always
          type: str
        hosted_zone_id:
          description: The ID of the private hosted zone.
          type: str
    groups:
      description: List of security groups associated with the network interface.
      returned: always
      type: list
      elements: dict
      contains:
        group_id:
          description: The ID of the security group.
          returned: always
          type: str
        group_name:
          description: The name of the security group.
          returned: always
          type: str
    ip_address_type:
      description: The IP address type for the endpoint.
      type: str
    network_interface_ids:
      description: List of network interfaces for the endpoint.
      returned: always
      type: list
      elements: str
    owner_id:
      description: The ID of the AWS account that owns the endpoint.
      returned: always
      type: str
    policy_document:
      description: The policy document associated with the endpoint.
      returned: always
      type: str
    private_dns_enabled:
      description: Indicates whether the VPC is associated with a private hosted zone.
      returned: always
      type: bool
    requester_managed:
      description: Indicated whether the endpoint is being managed by its service.
      returned: always
      type: bool
    route_table_ids:
      description: List of route table IDs associated with the endpoint.
      returned: always
      type: list
      elements: str
    service_name:
      description: The name of the service to which the endpoint is associated.
      returned: always
      type: str
    state:
      description: The state of the endpoint.
      returned: always
      type: str
    subnet_ids:
      description: List of subnets associated with the endpoint.
      returned: always
      type: list
    tags:
      description: List of tags associated with the endpoint.
      returned: always
      type: list
      elements: dict
    vpc_endpoint_id:
      description: The ID of the endpoint.
      returned: always
      type: str
    vpc_endpoint_type:
      description: The type of endpoint.
      returned: always
      type: str
    vpc_id:
      description: The ID of the VPC.
      returned: always
      type: str
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
"""

from typing import Any
from typing import Dict
from typing import List

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_endpoints
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def get_endpoints(client, module: AnsibleAWSModule) -> Dict[str, List[Dict[str, Any]]]:
    results = list()
    params = dict()
    params["Filters"] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    if module.params.get("vpc_endpoint_ids"):
        params["VpcEndpointIds"] = module.params.get("vpc_endpoint_ids")
    try:
        results = describe_vpc_endpoints(client, **params)
        if not results:
            module.exit_json(
                msg=f"VpcEndpoint {module.params.get('vpc_endpoint_ids')} does not exist", vpc_endpoints=[]
            )
        results = normalize_boto3_result(results)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to get endpoints")

    return dict(vpc_endpoints=[camel_dict_to_snake_dict(result) for result in results])


def main() -> None:
    argument_spec = dict(
        filters=dict(default={}, type="dict"),
        vpc_endpoint_ids=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    try:
        connection = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    results = get_endpoints(connection, module)

    module.exit_json(**results)


if __name__ == "__main__":
    main()

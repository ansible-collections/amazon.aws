#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_vpc_route_table_info
version_added: 1.0.0
short_description: Gather information about ec2 VPC route tables in AWS
description:
    - Gather information about ec2 VPC route tables in AWS
author:
- "Rob White (@wimnat)"
- "Mark Chappell (@tremble)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
    type: dict
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all VPC route tables
  amazon.aws.ec2_vpc_route_table_info:

- name: Gather information about a particular VPC route table using route table ID
  amazon.aws.ec2_vpc_route_table_info:
    filters:
      route-table-id: rtb-00112233

- name: Gather information about any VPC route table with a tag key Name and value Example
  amazon.aws.ec2_vpc_route_table_info:
    filters:
      "tag:Name": Example

- name: Gather information about any VPC route table within VPC with ID vpc-abcdef00
  amazon.aws.ec2_vpc_route_table_info:
    filters:
      vpc-id: vpc-abcdef00
'''

RETURN = r'''
route_tables:
  description:
    - A list of dictionarys describing route tables.
    - See also U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_route_tables).
  returned: always
  type: complex
  contains:
    associations:
      description: List of associations between the route table and one or more subnets or a gateway.
      returned: always
      type: complex
      contains:
        association_state:
          description: The state of the association.
          returned: always
          type: complex
          contains:
            state:
              description: The state of the association.
              returned: always
              type: str
              sample: associated
            state_message:
              description: Additional information about the state of the association.
              returned: when available
              type: str
              sample: 'Creating association'
        gateway_id:
          description: ID of the internet gateway or virtual private gateway.
          returned: when route table is a gateway route table
          type: str
          sample: igw-03312309
        main:
          description: Whether this is the main route table.
          returned: always
          type: bool
          sample: false
        route_table_association_id:
          description: ID of association between route table and subnet.
          returned: always
          type: str
          sample: rtbassoc-ab47cfc3
        route_table_id:
          description: ID of the route table.
          returned: always
          type: str
          sample: rtb-bf779ed7
        subnet_id:
          description: ID of the subnet.
          returned: when route table is a subnet route table
          type: str
          sample: subnet-82055af9
    id:
      description: ID of the route table (same as route_table_id for backwards compatibility).
      returned: always
      type: str
      sample: rtb-bf779ed7
    owner_id:
      description: ID of the account which owns the route table.
      returned: always
      type: str
      sample: '012345678912'
    propagating_vgws:
      description: List of Virtual Private Gateways propagating routes.
      returned: always
      type: list
      sample: []
    route_table_id:
      description: ID of the route table.
      returned: always
      type: str
      sample: rtb-bf779ed7
    routes:
      description: List of routes in the route table.
      returned: always
      type: complex
      contains:
        destination_cidr_block:
          description: CIDR block of destination.
          returned: always
          type: str
          sample: 10.228.228.0/22
        gateway_id:
          description: ID of the gateway.
          returned: when gateway is local or internet gateway
          type: str
          sample: local
        instance_id:
          description:
            - ID of a NAT instance.
            - Empty unless the route is via an EC2 instance.
          returned: always
          type: str
          sample: i-abcd123456789
        instance_owner_id:
          description:
            - AWS account owning the NAT instance.
            - Empty unless the route is via an EC2 instance.
          returned: always
          type: str
          sample: 123456789012
        network_interface_id:
          description:
            - The ID of the network interface.
            - Empty unless the route is via an EC2 instance.
          returned: always
          type: str
          sample: 123456789012
        nat_gateway_id:
          description: ID of the NAT gateway.
          returned: when the route is via a NAT gateway.
          type: str
          sample: local
        origin:
          description: mechanism through which the route is in the table.
          returned: always
          type: str
          sample: CreateRouteTable
        state:
          description: state of the route.
          returned: always
          type: str
          sample: active
    tags:
      description: Tags applied to the route table.
      returned: always
      type: dict
      sample:
        Name: Public route table
        Public: 'true'
    vpc_id:
      description: ID for the VPC in which the route lives.
      returned: always
      type: str
      sample: vpc-6e2d2407
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


@AWSRetry.jittered_backoff()
def describe_route_tables_with_backoff(connection, **params):
    try:
        paginator = connection.get_paginator('describe_route_tables')
        return paginator.paginate(**params).build_full_result()
    except is_boto3_error_code('InvalidRouteTableID.NotFound'):
        return None


def normalize_route(route):
    # Historically these were all there, but set to null when empty'
    for legacy_key in ['DestinationCidrBlock', 'GatewayId', 'InstanceId',
                       'Origin', 'State', 'NetworkInterfaceId']:
        if legacy_key not in route:
            route[legacy_key] = None
    route['InterfaceId'] = route['NetworkInterfaceId']
    return route


def normalize_association(assoc):
    # Name change between boto v2 and boto v3, return both
    assoc['Id'] = assoc['RouteTableAssociationId']
    return assoc


def normalize_route_table(table):
    table['tags'] = boto3_tag_list_to_ansible_dict(table['Tags'])
    table['Associations'] = [normalize_association(assoc) for assoc in table['Associations']]
    table['Routes'] = [normalize_route(route) for route in table['Routes']]
    table['Id'] = table['RouteTableId']
    del table['Tags']
    return camel_dict_to_snake_dict(table, ignore_list=['tags'])


def normalize_results(results):
    """
    We used to be a boto v2 module, make sure that the old return values are
    maintained and the shape of the return values are what people expect
    """

    routes = [normalize_route_table(route) for route in results['RouteTables']]
    del results['RouteTables']
    results = camel_dict_to_snake_dict(results)
    results['route_tables'] = routes
    return results


def list_ec2_vpc_route_tables(connection, module):

    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        results = describe_route_tables_with_backoff(connection, Filters=filters)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to get route tables")

    results = normalize_results(results)
    module.exit_json(changed=False, **results)


def main():
    argument_spec = dict(
        filters=dict(default=None, type='dict'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))

    list_ec2_vpc_route_tables(connection, module)


if __name__ == '__main__':
    main()

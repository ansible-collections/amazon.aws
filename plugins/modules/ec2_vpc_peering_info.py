#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_peering_info
short_description: Retrieves AWS VPC Peering details using AWS methods.
version_added: 1.0.0
description:
  - Gets various details related to AWS VPC Peers
options:
  peer_connection_ids:
    description:
      - List of specific VPC peer IDs to get details for.
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcPeeringConnections.html)
        for possible filters.
    type: dict
    default: {}
author: Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = r'''
# Simple example of listing all VPC Peers
- name: List all vpc peers
  community.aws.ec2_vpc_peering_info:
    region: ap-southeast-2
  register: all_vpc_peers

- name: Debugging the result
  ansible.builtin.debug:
    msg: "{{ all_vpc_peers.result }}"

- name: Get details on specific VPC peer
  community.aws.ec2_vpc_peering_info:
    peer_connection_ids:
      - pcx-12345678
      - pcx-87654321
    region: ap-southeast-2
  register: all_vpc_peers

- name: Get all vpc peers with specific filters
  community.aws.ec2_vpc_peering_info:
    region: ap-southeast-2
    filters:
      status-code: ['pending-acceptance']
  register: pending_vpc_peers
'''

RETURN = r'''
vpc_peering_connections:
  description: Details of the matching VPC peering connections.
  returned: success
  type: list
  contains:
    accepter_vpc_info:
      description: Information about the VPC which accepted the connection.
      returned: success
      type: complex
      contains:
        cidr_block:
          description: The primary CIDR for the VPC.
          returned: when connection is in the accepted state.
          type: str
          example: '10.10.10.0/23'
        cidr_block_set:
          description: A list of all CIDRs for the VPC.
          returned: when connection is in the accepted state.
          type: complex
          contains:
            cidr_block:
              description: A CIDR block used by the VPC.
              returned: success
              type: str
              example: '10.10.10.0/23'
        owner_id:
          description: The AWS account that owns the VPC.
          returned: success
          type: str
          example: 123456789012
        peering_options:
          description: Additional peering configuration.
          returned: when connection is in the accepted state.
          type: dict
          contains:
            allow_dns_resolution_from_remote_vpc:
              description: Indicates whether a VPC can resolve public DNS hostnames to private IP addresses when queried from instances in a peer VPC.
              returned: success
              type: bool
            allow_egress_from_local_classic_link_to_remote_vpc:
              description: Indicates whether a local ClassicLink connection can communicate with the peer VPC over the VPC peering connection.
              returned: success
              type: bool
            allow_egress_from_local_vpc_to_remote_classic_link:
              description: Indicates whether a local VPC can communicate with a ClassicLink connection in the peer VPC over the VPC peering connection.
              returned: success
              type: bool
        region:
          description: The AWS region that the VPC is in.
          returned: success
          type: str
          example: us-east-1
        vpc_id:
          description: The ID of the VPC
          returned: success
          type: str
          example: vpc-0123456789abcdef0
    requester_vpc_info:
      description: Information about the VPC which requested the connection.
      returned: success
      type: complex
      contains:
        cidr_block:
          description: The primary CIDR for the VPC.
          returned: when connection is not in the deleted state.
          type: str
          example: '10.10.10.0/23'
        cidr_block_set:
          description: A list of all CIDRs for the VPC.
          returned: when connection is not in the deleted state.
          type: complex
          contains:
            cidr_block:
              description: A CIDR block used by the VPC
              returned: success
              type: str
              example: '10.10.10.0/23'
        owner_id:
          description: The AWS account that owns the VPC.
          returned: success
          type: str
          example: 123456789012
        peering_options:
          description: Additional peering configuration.
          returned: when connection is not in the deleted state.
          type: dict
          contains:
            allow_dns_resolution_from_remote_vpc:
              description: Indicates whether a VPC can resolve public DNS hostnames to private IP addresses when queried from instances in a peer VPC.
              returned: success
              type: bool
            allow_egress_from_local_classic_link_to_remote_vpc:
              description: Indicates whether a local ClassicLink connection can communicate with the peer VPC over the VPC peering connection.
              returned: success
              type: bool
            allow_egress_from_local_vpc_to_remote_classic_link:
              description: Indicates whether a local VPC can communicate with a ClassicLink connection in the peer VPC over the VPC peering connection.
              returned: success
              type: bool
        region:
          description: The AWS region that the VPC is in.
          returned: success
          type: str
          example: us-east-1
        vpc_id:
          description: The ID of the VPC
          returned: success
          type: str
          example: vpc-0123456789abcdef0
    status:
      description: Details of the current status of the connection.
      returned: success
      type: complex
      contains:
        code:
          description: A short code describing the status of the connection.
          returned: success
          type: str
          example: active
        message:
          description: Additional information about the status of the connection.
          returned: success
          type: str
          example: Pending Acceptance by 123456789012
    tags:
      description: Tags applied to the connection.
      returned: success
      type: dict
    vpc_peering_connection_id:
      description: The ID of the VPC peering connection.
      returned: success
      type: str
      example: "pcx-0123456789abcdef0"

result:
  description: The result of the describe.
  returned: success
  type: list
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def get_vpc_peers(client, module):
    params = dict()
    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('peer_connection_ids'):
        params['VpcPeeringConnectionIds'] = module.params.get('peer_connection_ids')
    try:
        result = client.describe_vpc_peering_connections(aws_retry=True, **params)
        result = normalize_boto3_result(result)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe peering connections")

    return result['VpcPeeringConnections']


def main():
    argument_spec = dict(
        filters=dict(default=dict(), type='dict'),
        peer_connection_ids=dict(default=None, type='list', elements='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,)

    try:
        ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # Turn the boto3 result in to ansible friendly_snaked_names
    results = [camel_dict_to_snake_dict(peer) for peer in get_vpc_peers(ec2, module)]

    # Turn the boto3 result in to ansible friendly tag dictionary
    for peer in results:
        peer['tags'] = boto3_tag_list_to_ansible_dict(peer.get('tags', []))

    module.exit_json(result=results, vpc_peering_connections=results)


if __name__ == '__main__':
    main()

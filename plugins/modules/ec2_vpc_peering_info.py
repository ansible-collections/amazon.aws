#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_peering_info
short_description: Retrieves AWS VPC Peering details using AWS methods
version_added: 1.0.0
version_added_collection: community.aws
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
author:
  - Karen Cheng (@Etherdaemon)
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: List all EC2 VPC Peering Connections
  amazon.aws.ec2_vpc_peering_info:
    region: ap-southeast-2
  register: all_vpc_peers

- name: Debugging the result
  ansible.builtin.debug:
    msg: "{{ all_vpc_peers.result }}"

- name: Get details on specific EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering_info:
    peer_connection_ids:
      - "pcx-12345678"
      - "pcx-87654321"
    region: "ap-southeast-2"
  register: all_vpc_peers

- name: Get all EC2 VPC Peering Connections with specific filters
  amazon.aws.ec2_vpc_peering_info:
    region: "ap-southeast-2"
    filters:
      status-code: ["pending-acceptance"]
  register: pending_vpc_peers
"""

RETURN = r"""
vpc_peering_connections:
  description: Details of the matching VPC peering connections.
  returned: success
  type: list
  elements: dict
  contains:
    accepter_vpc_info:
      description: Information about the VPC which accepted the connection.
      returned: success
      type: dict
      contains:
        cidr_block:
          description: The primary CIDR for the VPC.
          returned: when connection is in the accepted state.
          type: str
          sample: "10.10.10.0/23"
        cidr_block_set:
          description: A list of all CIDRs for the VPC.
          returned: when connection is in the accepted state.
          type: list
          elements: dict
          contains:
            cidr_block:
              description: A CIDR block used by the VPC.
              returned: success
              type: str
              sample: "10.10.10.0/23"
        owner_id:
          description: The AWS account that owns the VPC.
          returned: success
          type: str
          sample: "123456789012"
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
          sample: "us-east-1"
        vpc_id:
          description: The ID of the VPC
          returned: success
          type: str
          sample: "vpc-0123456789abcdef0"
    requester_vpc_info:
      description: Information about the VPC which requested the connection.
      returned: success
      type: dict
      contains:
        cidr_block:
          description: The primary CIDR for the VPC.
          returned: when connection is not in the deleted state.
          type: str
          sample: "10.10.10.0/23"
        cidr_block_set:
          description: A list of all CIDRs for the VPC.
          returned: when connection is not in the deleted state.
          type: list
          elements: dict
          contains:
            cidr_block:
              description: A CIDR block used by the VPC
              returned: success
              type: str
              sample: "10.10.10.0/23"
        owner_id:
          description: The AWS account that owns the VPC.
          returned: success
          type: str
          sample: "123456789012"
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
          sample: "us-east-1"
        vpc_id:
          description: The ID of the VPC
          returned: success
          type: str
          sample: "vpc-0123456789abcdef0"
    status:
      description: Details of the current status of the connection.
      returned: success
      type: dict
      contains:
        code:
          description: A short code describing the status of the connection.
          returned: success
          type: str
          sample: "active"
        message:
          description: Additional information about the status of the connection.
          returned: success
          type: str
          sample: "Pending Acceptance by 123456789012"
    tags:
      description: Tags applied to the connection.
      returned: success
      type: dict
    vpc_peering_connection_id:
      description: The ID of the VPC peering connection.
      returned: success
      type: str
      sample: "pcx-0123456789abcdef0"

result:
  description: The result of the describe.
  returned: success
  type: list
  elements: dict
  contains:
    accepter_vpc_info:
      description: Information about the VPC which accepted the connection.
      returned: success
      type: dict
      contains:
        cidr_block:
          description: The primary CIDR for the VPC.
          returned: when connection is in the accepted state.
          type: str
          sample: "10.10.10.0/23"
        cidr_block_set:
          description: A list of all CIDRs for the VPC.
          returned: when connection is in the accepted state.
          type: list
          elements: dict
          contains:
            cidr_block:
              description: A CIDR block used by the VPC.
              returned: success
              type: str
              sample: "10.10.10.0/23"
        owner_id:
          description: The AWS account that owns the VPC.
          returned: success
          type: str
          sample: "123456789012"
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
          sample: "us-east-1"
        vpc_id:
          description: The ID of the VPC
          returned: success
          type: str
          sample: "vpc-0123456789abcdef0"
    requester_vpc_info:
      description: Information about the VPC which requested the connection.
      returned: success
      type: dict
      contains:
        cidr_block:
          description: The primary CIDR for the VPC.
          returned: when connection is not in the deleted state.
          type: str
          sample: "10.10.10.0/23"
        cidr_block_set:
          description: A list of all CIDRs for the VPC.
          returned: when connection is not in the deleted state.
          type: list
          elements: dict
          contains:
            cidr_block:
              description: A CIDR block used by the VPC
              returned: success
              type: str
              sample: "10.10.10.0/23"
        owner_id:
          description: The AWS account that owns the VPC.
          returned: success
          type: str
          sample: "123456789012"
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
          sample: "us-east-1"
        vpc_id:
          description: The ID of the VPC
          returned: success
          type: str
          sample: "vpc-0123456789abcdef0"
    status:
      description: Details of the current status of the connection.
      returned: success
      type: dict
      contains:
        code:
          description: A short code describing the status of the connection.
          returned: success
          type: str
          sample: "active"
        message:
          description: Additional information about the status of the connection.
          returned: success
          type: str
          sample: "Pending Acceptance by 123456789012"
    tags:
      description: Tags applied to the connection.
      returned: success
      type: dict
    vpc_peering_connection_id:
      description: The ID of the VPC peering connection.
      returned: success
      type: str
      sample: "pcx-0123456789abcdef0"
"""


from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_peering_connections
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def get_vpc_peers(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    params: Dict = {}
    params["Filters"] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    if module.params.get("peer_connection_ids"):
        params["VpcPeeringConnectionIds"] = module.params.get("peer_connection_ids")

    result = describe_vpc_peering_connections(client, **params)

    return normalize_boto3_result(result)


def main():
    argument_spec = dict(
        filters=dict(default=dict(), type="dict"),
        peer_connection_ids=dict(default=None, type="list", elements="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = module.client("ec2")

    # Turn the boto3 result in to ansible friendly_snaked_names
    results = [camel_dict_to_snake_dict(peer) for peer in get_vpc_peers(client, module)]

    # Turn the boto3 result in to ansible friendly tag dictionary
    for peer in results:
        peer["tags"] = boto3_tag_list_to_ansible_dict(peer.get("tags", []))

    module.deprecate(
        (
            "The 'result' return key is deprecated and will be replaced by 'vpc_peering_connections'. Both values are"
            " returned for now."
        ),
        version="11.0.0",
        collection_name="amazon.aws",
    )

    module.exit_json(result=results, vpc_peering_connections=results)


if __name__ == "__main__":
    main()

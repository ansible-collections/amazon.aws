#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_peering
short_description: create, delete, accept, and reject VPC peering connections between two VPCs.
version_added: 1.0.0
version_added_collection: community.aws
description:
  - Read the AWS documentation for VPC Peering Connections
    U(https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/vpc-peering.html).
options:
  vpc_id:
    description:
      - VPC id of the requesting VPC.
    required: false
    type: str
  peering_id:
    description:
      - Peering connection id.
    required: false
    type: str
  peer_region:
    description:
      - Region of the accepting VPC.
    required: false
    type: str
  peer_vpc_id:
    description:
      - VPC id of the accepting VPC.
    required: false
    type: str
  peer_owner_id:
    description:
      - The AWS account number for cross account peering.
    required: false
    type: str
  state:
    description:
      - Create, delete, accept, reject a peering connection.
    required: false
    default: present
    choices: ['present', 'absent', 'accept', 'reject']
    type: str
  wait:
    description:
      - Wait for peering state changes to complete.
    required: false
    default: false
    type: bool
notes:
  - Support for O(purge_tags) was added in release 2.0.0.
author:
  - Mike Mochan (@mmochan)
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Complete example to create and accept a local peering connection.
- name: Create local account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-87654321"
    state: "present"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Accept local EC2 VPC Peering request
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    state: "accept"
  register: action_peer

# Complete example to delete a local peering connection.
- name: Create local account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-87654321"
    state: "present"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Delete a local EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    state: "absent"
  register: vpc_peer

  # Complete example to create and accept a cross account peering connection.
- name: Create cross account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-12345678"
    peer_owner_id: "123456789012"
    state: "present"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Accept EC2 VPC Peering Connection from remote account
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: "bot03_profile_for_cross_account"
    state: "accept"
  register: vpc_peer

# Complete example to create and accept an intra-region peering connection.
- name: Create intra-region EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "us-east-1"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-87654321"
    peer_region: "us-west-2"
    state: "present"
    tags:
      Name: "Peering connection for us-east-1 VPC to us-west-2 VPC"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Accept EC2 VPC Peering Connection from peer region
  amazon.aws.ec2_vpc_peer:
    region: "us-west-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    state: "accept"
  register: vpc_peer

# Complete example to create and reject a local peering connection.
- name: Create local account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-87654321"
    state: "present"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Reject a local EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    state: "reject"

# Complete example to create and accept a cross account peering connection.
- name: Create cross account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-12345678"
    peer_owner_id: "123456789012"
    state: "present"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Accept a cross account EC2 VPC Peering Connection request
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: "bot03_profile_for_cross_account"
    state: "accept"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"

# Complete example to create and reject a cross account peering connection.
- name: Create cross account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peering:
    region: "ap-southeast-2"
    vpc_id: "vpc-12345678"
    peer_vpc_id: "vpc-12345678"
    peer_owner_id: "123456789012"
    state: "present"
    tags:
      Name: "Peering connection for VPC 21 to VPC 22"
      CostCode: "CC1234"
      Project: "phoenix"
  register: vpc_peer

- name: Reject a cross account EC2 VPC Peering Connection
  amazon.aws.ec2_vpc_peeriing:
    region: "ap-southeast-2"
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: "bot03_profile_for_cross_account"
    state: "reject"
"""

RETURN = r"""
peering_id:
  description: The id of the VPC peering connection created/deleted.
  returned: always
  type: str
  sample: "pcx-034223d7c0aec3cde"
vpc_peering_connection:
  description: The details of the VPC peering connection.
  returned: success
  type: dict
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
      type: complex
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
    expiration_time:
      description: The time that an unaccepted VPC peering connection will expire.
      type: str
      sample: "2024-10-01T12:11:12+00:00"
    vpc_peering_connection_id:
      description: The ID of the VPC peering connection.
      returned: success
      type: str
      sample: "pcx-0123456789abcdef0"
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import NoReturn
from typing import Tuple

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import accept_vpc_peering_connection
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_vpc_peering_connection
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_vpc_peering_connection
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_peering_connections
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import reject_vpc_peering_connection
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def wait_for_state(client, module: AnsibleAWSModule, state: str, peering_id: str) -> NoReturn:
    waiter = client.get_waiter("vpc_peering_connection_exists")
    filters = {
        "vpc-peering-connection-id": peering_id,
        "status-code": state,
    }
    try:
        waiter.wait(Filters=ansible_dict_to_boto3_filter_list(filters))
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, "Failed to wait for state change")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Unable to describe Peering Connection while waiting for state to change")


def describe_peering_connections(client, module: AnsibleAWSModule, params) -> Dict[str, Any]:
    peering_connections: Dict = {}

    filters = {
        "requester-vpc-info.vpc-id": params["VpcId"],
        "accepter-vpc-info.vpc-id": params["PeerVpcId"],
    }

    peering_connections = describe_vpc_peering_connections(client, Filters=ansible_dict_to_boto3_filter_list(filters))
    if peering_connections == []:
        # Try again with the VPC/Peer relationship reversed
        filters = {
            "requester-vpc-info.vpc-id": params["PeerVpcId"],
            "accepter-vpc-info.vpc-id": params["VpcId"],
        }
        peering_connections = describe_vpc_peering_connections(
            client, Filters=ansible_dict_to_boto3_filter_list(filters)
        )

    return peering_connections


def is_active(peering_connection: Dict[str, Any]) -> bool:
    return peering_connection["Status"]["Code"] == "active"


def is_rejected(peering_connection: Dict[str, Any]) -> bool:
    return peering_connection["Status"]["Code"] == "rejected"


def is_pending(peering_connection: Dict[str, Any]) -> bool:
    return peering_connection["Status"]["Code"] == "pending-acceptance"


def is_deleted(peering_connection: Dict[str, Any]) -> bool:
    return peering_connection["Status"]["Code"] == "deleted"


def create_peering_connection(client, module: AnsibleAWSModule) -> Tuple[bool, Dict[str, Any]]:
    changed: bool = False
    params: Dict = {}

    params["VpcId"] = module.params.get("vpc_id")
    params["PeerVpcId"] = module.params.get("peer_vpc_id")

    if module.params.get("peer_region"):
        params["PeerRegion"] = module.params["peer_region"]

    if module.params.get("peer_owner_id"):
        params["PeerOwnerId"] = module.params["peer_owner_id"]

    peering_connections = describe_peering_connections(client, module, params)
    for peering_connection in peering_connections:
        changed |= ensure_ec2_tags(
            client,
            module,
            peering_connection["VpcPeeringConnectionId"],
            purge_tags=module.params.get("purge_tags"),
            tags=module.params.get("tags"),
        )

        if is_active(peering_connection):
            return (changed, peering_connection)

        if is_pending(peering_connection):
            return (changed, peering_connection)

    if module.params.get("tags"):
        params["TagSpecifications"] = boto3_tag_specifications(module.params["tags"], types="vpc-peering-connection")

    if module.check_mode:
        return (True, {"VpcPeeringConnectionId": ""})

    peering_connection = create_vpc_peering_connection(client, **params)
    if module.params.get("wait"):
        wait_for_state(client, module, "pending-acceptance", peering_connection["VpcPeeringConnectionId"])
    changed = True
    return (changed, peering_connection)


def delete_peering_connection(client, module: AnsibleAWSModule) -> NoReturn:
    peering_id = module.params.get("peering_id")
    if peering_id:
        peering_connection = get_peering_connection_by_id(client, module, peering_id)
    else:
        params: Dict = {}
        params["VpcId"] = module.params.get("vpc_id")
        params["PeerVpcId"] = module.params.get("peer_vpc_id")
        params["PeerRegion"] = module.params.get("peer_region")

        if module.params.get("peer_owner_id"):
            params["PeerOwnerId"] = module.params["peer_owner_id"]

        peering_connection = describe_peering_connections(client, module, params)[0]

    if not peering_connection:
        module.exit_json(changed=False)
    else:
        peering_id = peering_id or peering_connection["VpcPeeringConnectionId"]

    if is_deleted(peering_connection):
        module.exit_json(msg="Connection in deleted state.", changed=False, peering_id=peering_id)

    if is_rejected(peering_connection):
        module.exit_json(
            msg="Connection has been rejected. State cannot be changed and will be removed automatically by AWS",
            changed=False,
            peering_id=peering_id,
        )

    if not module.check_mode:
        delete_vpc_peering_connection(client, peering_id)
        if module.params.get("wait"):
            wait_for_state(client, module, "deleted", peering_id)

    module.exit_json(changed=True, peering_id=peering_id)


def get_peering_connection_by_id(client, module: AnsibleAWSModule, peering_id: str) -> Dict[str, Any]:
    filters: Dict = {}
    filters["VpcPeeringConnectionIds"] = [peering_id]

    try:
        result = describe_vpc_peering_connections(client, VpcPeeringConnectionIds=[peering_id])
        return result[0]
    except is_boto3_error_code("InvalidVpcPeeringConnectionId.Malformed") as e:
        module.fail_json_aws(e, msg="Malformed connection ID")


def accept_reject_peering_connection(client, module: AnsibleAWSModule, state: str) -> Tuple[bool, Dict[str, Any]]:
    changed: bool = False

    peering_id = module.params.get("peering_id")
    vpc_peering_connection = get_peering_connection_by_id(client, module, peering_id)

    if not (is_active(vpc_peering_connection) or is_rejected(vpc_peering_connection)):
        if not module.check_mode:
            if state == "accept":
                changed |= accept_vpc_peering_connection(client, peering_id)
                target_state = "active"
            else:
                changed |= reject_vpc_peering_connection(client, peering_id)
                target_state = "rejected"

            if module.params.get("wait"):
                wait_for_state(client, module, target_state, peering_id)

        changed = True

    changed |= ensure_ec2_tags(
        client,
        module,
        peering_id,
        purge_tags=module.params.get("purge_tags"),
        tags=module.params.get("tags"),
    )

    # Reload peering conection info to return latest state/params
    vpc_peering_connection = get_peering_connection_by_id(client, module, peering_id)

    return (changed, vpc_peering_connection)


def main():
    argument_spec = dict(
        vpc_id=dict(type="str"),
        peer_vpc_id=dict(type="str"),
        peer_region=dict(type="str"),
        peering_id=dict(type="str"),
        peer_owner_id=dict(type="str"),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        state=dict(default="present", type="str", choices=["present", "absent", "accept", "reject"]),
        wait=dict(default=False, type="bool"),
    )
    required_if = [
        ("state", "present", ["vpc_id", "peer_vpc_id"]),
        ("state", "accept", ["peering_id"]),
        ("state", "reject", ["peering_id"]),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)

    state = module.params.get("state")
    peering_id = module.params.get("peering_id")
    vpc_id = module.params.get("vpc_id")
    peer_vpc_id = module.params.get("peer_vpc_id")

    client = module.client("ec2")

    if state == "present":
        (changed, results) = create_peering_connection(client, module)
    elif state == "absent":
        if not peering_id and (not vpc_id or not peer_vpc_id):
            module.fail_json(
                msg="state is absent but one of the following is missing: peering_id or [vpc_id, peer_vpc_id]"
            )

        delete_peering_connection(client, module)
    else:
        (changed, results) = accept_reject_peering_connection(client, module, state)

    formatted_results = camel_dict_to_snake_dict(results)
    # Turn the resource tags from boto3 into an ansible friendly tag dictionary
    formatted_results["tags"] = boto3_tag_list_to_ansible_dict(formatted_results.get("tags", []))

    module.exit_json(
        changed=changed, vpc_peering_connection=formatted_results, peering_id=results["VpcPeeringConnectionId"]
    )


if __name__ == "__main__":
    main()

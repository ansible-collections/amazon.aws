#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_peer
short_description: create, delete, accept, and reject VPC peering connections between two VPCs.
version_added: 1.0.0
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
  - Support for I(purge_tags) was added in release 2.0.0.
author:
  - Mike Mochan (@mmochan)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Complete example to create and accept a local peering connection.
- name: Create local account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: Accept local VPC peering request
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: accept
  register: action_peer

# Complete example to delete a local peering connection.
- name: Create local account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: delete a local VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: absent
  register: vpc_peer

  # Complete example to create and accept a cross account peering connection.
- name: Create cross account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-12345678
    peer_owner_id: 123456789012
    state: present
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: Accept peering connection from remote account
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: accept
  register: vpc_peer

# Complete example to create and accept an intra-region peering connection.
- name: Create intra-region VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: us-east-1
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    peer_region: us-west-2
    state: present
    tags:
      Name: Peering connection for us-east-1 VPC to us-west-2 VPC
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: Accept peering connection from peer region
  community.aws.ec2_vpc_peer:
    region: us-west-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: accept
  register: vpc_peer

# Complete example to create and reject a local peering connection.
- name: Create local account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: Reject a local VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: reject

# Complete example to create and accept a cross account peering connection.
- name: Create cross account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-12345678
    peer_owner_id: 123456789012
    state: present
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: Accept a cross account VPC peering connection request
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: accept
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix

# Complete example to create and reject a cross account peering connection.
- name: Create cross account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-12345678
    peer_owner_id: 123456789012
    state: present
    tags:
      Name: Peering connection for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix
  register: vpc_peer

- name: Reject a cross account VPC peering Connection
  community.aws.ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: reject
"""

RETURN = r"""
peering_id:
  description: The id of the VPC peering connection created/deleted.
  returned: always
  type: str
  sample: pcx-034223d7c0aec3cde
vpc_peering_connection:
  description: The details of the VPC peering connection as returned by Boto3 (snake cased).
  returned: success
  type: complex
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
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import add_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def wait_for_state(client, module, state, pcx_id):
    waiter = client.get_waiter("vpc_peering_connection_exists")
    peer_filter = {
        "vpc-peering-connection-id": pcx_id,
        "status-code": state,
    }
    try:
        waiter.wait(Filters=ansible_dict_to_boto3_filter_list(peer_filter))
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, "Failed to wait for state change")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Enable to describe Peerig Connection while waiting for state to change")


def describe_peering_connections(params, client):
    peer_filter = {
        "requester-vpc-info.vpc-id": params["VpcId"],
        "accepter-vpc-info.vpc-id": params["PeerVpcId"],
    }
    result = client.describe_vpc_peering_connections(
        aws_retry=True,
        Filters=ansible_dict_to_boto3_filter_list(peer_filter),
    )
    if result["VpcPeeringConnections"] == []:
        # Try again with the VPC/Peer relationship reversed
        peer_filter = {
            "requester-vpc-info.vpc-id": params["PeerVpcId"],
            "accepter-vpc-info.vpc-id": params["VpcId"],
        }
        result = client.describe_vpc_peering_connections(
            aws_retry=True,
            Filters=ansible_dict_to_boto3_filter_list(peer_filter),
        )

    return result


def is_active(peering_conn):
    return peering_conn["Status"]["Code"] == "active"


def is_pending(peering_conn):
    return peering_conn["Status"]["Code"] == "pending-acceptance"


def create_peer_connection(client, module):
    changed = False
    params = dict()
    params["VpcId"] = module.params.get("vpc_id")
    params["PeerVpcId"] = module.params.get("peer_vpc_id")
    if module.params.get("peer_region"):
        params["PeerRegion"] = module.params.get("peer_region")
    if module.params.get("peer_owner_id"):
        params["PeerOwnerId"] = str(module.params.get("peer_owner_id"))
    peering_conns = describe_peering_connections(params, client)
    for peering_conn in peering_conns["VpcPeeringConnections"]:
        pcx_id = peering_conn["VpcPeeringConnectionId"]
        if ensure_ec2_tags(
            client,
            module,
            pcx_id,
            purge_tags=module.params.get("purge_tags"),
            tags=module.params.get("tags"),
        ):
            changed = True
        if is_active(peering_conn):
            return (changed, peering_conn)
        if is_pending(peering_conn):
            return (changed, peering_conn)
    try:
        peering_conn = client.create_vpc_peering_connection(aws_retry=True, **params)
        pcx_id = peering_conn["VpcPeeringConnection"]["VpcPeeringConnectionId"]
        if module.params.get("tags"):
            # Once the minimum botocore version is bumped to > 1.17.24
            # (hopefully community.aws 3.0.0) we can add the tags to the
            # creation parameters
            add_ec2_tags(
                client,
                module,
                pcx_id,
                module.params.get("tags"),
                retry_codes=["InvalidVpcPeeringConnectionID.NotFound"],
            )
        if module.params.get("wait"):
            wait_for_state(client, module, "pending-acceptance", pcx_id)
        changed = True
        return (changed, peering_conn["VpcPeeringConnection"])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def remove_peer_connection(client, module):
    pcx_id = module.params.get("peering_id")
    if pcx_id:
        peering_conn = get_peering_connection_by_id(pcx_id, client, module)
    else:
        params = dict()
        params["VpcId"] = module.params.get("vpc_id")
        params["PeerVpcId"] = module.params.get("peer_vpc_id")
        params["PeerRegion"] = module.params.get("peer_region")
        if module.params.get("peer_owner_id"):
            params["PeerOwnerId"] = str(module.params.get("peer_owner_id"))
        peering_conn = describe_peering_connections(params, client)["VpcPeeringConnections"][0]

    if not peering_conn:
        module.exit_json(changed=False)
    else:
        pcx_id = pcx_id or peering_conn["VpcPeeringConnectionId"]

    if peering_conn["Status"]["Code"] == "deleted":
        module.exit_json(msg="Connection in deleted state.", changed=False, peering_id=pcx_id)
    if peering_conn["Status"]["Code"] == "rejected":
        module.exit_json(
            msg="Connection has been rejected. State cannot be changed and will be removed automatically by AWS",
            changed=False,
            peering_id=pcx_id,
        )

    try:
        params = dict()
        params["VpcPeeringConnectionId"] = pcx_id
        client.delete_vpc_peering_connection(aws_retry=True, **params)
        if module.params.get("wait"):
            wait_for_state(client, module, "deleted", pcx_id)
        module.exit_json(changed=True, peering_id=pcx_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def get_peering_connection_by_id(peering_id, client, module):
    params = dict()
    params["VpcPeeringConnectionIds"] = [peering_id]
    try:
        vpc_peering_connection = client.describe_vpc_peering_connections(aws_retry=True, **params)
        return vpc_peering_connection["VpcPeeringConnections"][0]
    except is_boto3_error_code("InvalidVpcPeeringConnectionId.Malformed") as e:
        module.fail_json_aws(e, msg="Malformed connection ID")
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Error while describing peering connection by peering_id")


def accept_reject(state, client, module):
    changed = False
    params = dict()
    peering_id = module.params.get("peering_id")
    params["VpcPeeringConnectionId"] = peering_id
    vpc_peering_connection = get_peering_connection_by_id(peering_id, client, module)
    peering_status = vpc_peering_connection["Status"]["Code"]

    if peering_status not in ["active", "rejected"]:
        try:
            if state == "accept":
                client.accept_vpc_peering_connection(aws_retry=True, **params)
                target_state = "active"
            else:
                client.reject_vpc_peering_connection(aws_retry=True, **params)
                target_state = "rejected"
            if module.params.get("tags"):
                add_ec2_tags(
                    client,
                    module,
                    peering_id,
                    module.params.get("tags"),
                    retry_codes=["InvalidVpcPeeringConnectionID.NotFound"],
                )
            changed = True
            if module.params.get("wait"):
                wait_for_state(client, module, target_state, peering_id)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))
    if ensure_ec2_tags(
        client,
        module,
        peering_id,
        purge_tags=module.params.get("purge_tags"),
        tags=module.params.get("tags"),
    ):
        changed = True

    # Relaod peering conection infos to return latest state/params
    vpc_peering_connection = get_peering_connection_by_id(peering_id, client, module)
    return (changed, vpc_peering_connection)


def main():
    argument_spec = dict(
        vpc_id=dict(),
        peer_vpc_id=dict(),
        peer_region=dict(),
        peering_id=dict(),
        peer_owner_id=dict(),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        state=dict(default="present", choices=["present", "absent", "accept", "reject"]),
        wait=dict(default=False, type="bool"),
    )
    required_if = [
        ("state", "present", ["vpc_id", "peer_vpc_id"]),
        ("state", "accept", ["peering_id"]),
        ("state", "reject", ["peering_id"]),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if)

    state = module.params.get("state")
    peering_id = module.params.get("peering_id")
    vpc_id = module.params.get("vpc_id")
    peer_vpc_id = module.params.get("peer_vpc_id")

    try:
        client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    if state == "present":
        (changed, results) = create_peer_connection(client, module)
    elif state == "absent":
        if not peering_id and (not vpc_id or not peer_vpc_id):
            module.fail_json(
                msg="state is absent but one of the following is missing: peering_id or [vpc_id, peer_vpc_id]"
            )

        remove_peer_connection(client, module)
    else:
        (changed, results) = accept_reject(state, client, module)

    formatted_results = camel_dict_to_snake_dict(results)
    # Turn the resource tags from boto3 into an ansible friendly tag dictionary
    formatted_results["tags"] = boto3_tag_list_to_ansible_dict(formatted_results.get("tags", []))

    module.exit_json(
        changed=changed, vpc_peering_connection=formatted_results, peering_id=results["VpcPeeringConnectionId"]
    )


if __name__ == "__main__":
    main()

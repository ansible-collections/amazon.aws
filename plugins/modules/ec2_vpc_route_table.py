#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_route_table
version_added: 1.0.0
short_description: Manage route tables for AWS Virtual Private Clouds
description:
  - Manage route tables for AWS Virtual Private Clouds (VPCs).
author:
  - Robert Estelle (@erydo)
  - Rob White (@wimnat)
  - Will Thames (@willthames)
options:
  gateway_id:
    description:
      - The ID of the gateway to associate with the route table.
      - If O(gateway_id) is V('None') or V(''), gateway will be disassociated with the route table.
    type: str
    version_added: 3.2.0
  lookup:
    description:
      - Look up route table by either O(tags) or by O(route_table_id).
      - If O(lookup=tag) and O(tags) is not specified then no lookup for an
        existing route table is performed and a new route table will be created.
      - When using O(lookup=tag), multiple matches being found will result in
        a failure and no changes will be made.
      - To change the tags of a route table use O(lookup=id).
      - O(vpc_id) must be specified when O(lookup=tag).
    default: tag
    choices: [ 'tag', 'id' ]
    type: str
  propagating_vgw_ids:
    description: Enable route propagation from virtual gateways specified by ID.
    type: list
    elements: str
  purge_routes:
    description: Purge existing routes that are not found in routes.
    type: bool
    default: True
  purge_subnets:
    description:
      - Purge existing subnets that are not found in subnets.
      - Ignored unless the subnets option is supplied.
    default: True
    type: bool
  route_table_id:
    description:
      - The ID of the route table to update or delete.
      - Required when O(lookup=id).
    type: str
  routes:
    description:
      - List of routes in the route table.
      - Routes are specified as dicts containing the keys V(dest) and one of V(gateway_id),
        V(instance_id), V(network_interface_id), V(transit_gateway_id), or V(vpc_peering_connection_id).
      - The value of V(dest) is used for the destination match. It may be a IPv4 CIDR block
        or a IPv6 CIDR block.
      - If V(gateway_id) is specified, you can refer to the VPC's IGW by using the value V(igw).
      - Routes are required for present states.
    type: list
    elements: dict
    default: []
  state:
    description: Create or destroy the VPC route table.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  subnets:
    description: An array of subnets to add to this route table. Subnets may be specified
      by either subnet ID, Name tag, or by a CIDR such as '10.0.0.0/24' or 'fd00::/8'.
    type: list
    elements: str
  vpc_id:
    description:
      - VPC ID of the VPC in which to create the route table.
      - Required when O(state=present) or O(lookup=tag).
    type: str
notes:
  - Tags are used to uniquely identify route tables within a VPC when the O(route_table_id) is not supplied.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic creation example:
- name: Set up public subnet route table
  amazon.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    tags:
      Name: Public
    subnets:
      - "{{ jumpbox_subnet.subnet.id }}"
      - "{{ frontend_subnet.subnet.id }}"
      - "{{ vpn_subnet.subnet_id }}"
    routes:
      - dest: 0.0.0.0/0
        gateway_id: "{{ igw.gateway_id }}"
      - dest: ::/0
        gateway_id: "{{ igw.gateway_id }}"
      - dest: 0.0.0.0/0
        gateway_id: "{{ transit_gateway_id }}"
  register: public_route_table

- name: Create VPC gateway
  amazon.aws.ec2_vpc_igw:
    vpc_id: vpc-1245678
  register: vpc_igw

- name: Create gateway route table
  amazon.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    tags:
      Name: Gateway route table
    gateway_id: "{{ vpc_igw.gateway_id }}"
  register: gateway_route_table

- name: Disassociate gateway from route table
  amazon.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    tags:
      Name: Gateway route table
    gateway_id: None
  register: gateway_route_table

- name: Set up NAT-protected route table
  amazon.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    tags:
      Name: Internal
    subnets:
      - "{{ application_subnet.subnet.id }}"
      - 'Database Subnet'
      - '10.0.0.0/8'
    routes:
      - dest: 0.0.0.0/0
        instance_id: "{{ nat.instance_id }}"
  register: nat_route_table

- name: delete route table
  amazon.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    route_table_id: "{{ route_table.id }}"
    lookup: id
    state: absent
"""

RETURN = r"""
route_table:
  description: Route Table result.
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
      description: ID of the route table (same as RV(route_table.route_table_id) for backwards compatibility).
      returned: always
      type: str
      sample: rtb-bf779ed7
    owner_id:
        description: AWS account owning resource.
        type: str
        sample: 123456789012
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
          description: IPv4 CIDR block of destination
          returned: always
          type: str
          sample: 10.228.228.0/22
        destination_ipv6_cidr_block:
          description: IPv6 CIDR block of destination
          returned: when the route includes an IPv6 destination
          type: str
          sample: 2600:1f1c:1b3:8f00:8000::/65
        gateway_id:
          description: ID of the gateway.
          returned: when gateway is local or internet gateway
          type: str
          sample: local
        instance_id:
          description: ID of a NAT instance.
          returned: when the route is via an EC2 instance
          type: str
          sample: i-abcd123456789
        instance_owner_id:
          description: AWS account owning the NAT instance.
          returned: when the route is via an EC2 instance
          type: str
          sample: 123456789012
        nat_gateway_id:
          description: ID of the NAT gateway.
          returned: when the route is via a NAT gateway
          type: str
          sample: local
        carrier_gateway_id:
          description: ID of the Carrier gateway.
          returned: when the route is via a Carrier gateway
          type: str
          sample: local
          version_added: 6.0.0
        transit_gateway_id:
          description: ID of the Transit gateway.
          returned: when the route is via a Transit gateway
          type: str
          sample: tgw-123456789012
          version_added: 9.0.0
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
"""

import re
from ipaddress import ip_network
from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import associate_route_table
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_route
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_route_table
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_route
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_route_table
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_internet_gateways
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_route_tables
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_subnets
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import disassociate_route_table
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import enable_vgw_route_propagation
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import replace_route
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def find_subnets(
    connection, module: AnsibleAWSModule, vpc_id: str, identified_subnets: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """
    Finds a list of subnets, each identified either by a raw ID, a unique
    'Name' tag, or a CIDR such as 10.0.0.0/8.
    """
    CIDR_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$")
    SUBNET_RE = re.compile(r"^subnet-[A-z0-9]+$")

    subnet_ids = []
    subnet_names = []
    subnet_cidrs = []
    for subnet in identified_subnets or []:
        if re.match(SUBNET_RE, subnet):
            subnet_ids.append(subnet)
        elif re.match(CIDR_RE, subnet):
            subnet_cidrs.append(subnet)
        else:
            subnet_names.append(subnet)

    subnets_by_id = []
    if subnet_ids:
        filters = ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id})
        try:
            subnets_by_id = describe_subnets(connection, SubnetIds=subnet_ids, Filters=filters)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg=f"Couldn't find subnet with id {subnet_ids}")

    subnets_by_cidr = []
    if subnet_cidrs:
        filters = ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id, "cidr": subnet_cidrs})
        try:
            subnets_by_cidr = describe_subnets(connection, Filters=filters)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg=f"Couldn't find subnet with cidr {subnet_cidrs}")

    subnets_by_name = []
    if subnet_names:
        filters = ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id, "tag:Name": subnet_names})
        try:
            subnets_by_name = describe_subnets(connection, Filters=filters)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg=f"Couldn't find subnet with names {subnet_names}")

        for name in subnet_names:
            matching_count = len(
                [1 for s in subnets_by_name for t in s.get("Tags", []) if t["Key"] == "Name" and t["Value"] == name]
            )
            if matching_count == 0:
                module.fail_json(msg=f'Subnet named "{name}" does not exist')
            elif matching_count > 1:
                module.fail_json(msg=f'Multiple subnets named "{name}"')

    return subnets_by_id + subnets_by_cidr + subnets_by_name


def find_igw(connection, module: AnsibleAWSModule, vpc_id: str) -> str:
    """
    Finds the Internet gateway for the given VPC ID.
    """
    filters = ansible_dict_to_boto3_filter_list({"attachment.vpc-id": vpc_id})
    igw = describe_internet_gateways(connection, Filters=filters)

    if len(igw) == 0:
        module.fail_json(msg=f"No IGWs found for VPC {vpc_id}")
    elif len(igw) > 1:
        module.fail_json(msg=f"Multiple IGWs found for VPC {vpc_id}")
    return igw[0]["InternetGatewayId"]


def tags_match(match_tags, candidate_tags):
    return all((k in candidate_tags and candidate_tags[k] == v for k, v in match_tags.items()))


def get_route_table_by_id(connection, route_table_id: str) -> Optional[Dict[str, Any]]:
    route_table = None
    route_tables = describe_route_tables(connection, RouteTableIds=[route_table_id])

    if route_tables:
        route_table = route_tables[0]

    return route_table


def get_route_table_by_tags(
    connection, module: AnsibleAWSModule, vpc_id: str, tags: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    count = 0
    route_table = None
    filters = ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id})
    route_tables = describe_route_tables(connection, Filters=filters)

    for table in route_tables:
        this_tags = describe_ec2_tags(connection, module, table["RouteTableId"])
        if tags_match(tags, this_tags):
            route_table = table
            count += 1

    if count > 1:
        module.fail_json(msg="Tags provided do not identify a unique route table")
    return route_table


def route_spec_matches_route(route_spec, route):
    if route_spec.get("GatewayId") and "nat-" in route_spec["GatewayId"]:
        route_spec["NatGatewayId"] = route_spec.pop("GatewayId")
    if route_spec.get("GatewayId") and "vpce-" in route_spec["GatewayId"]:
        if route_spec.get("DestinationCidrBlock", "").startswith("pl-"):
            route_spec["DestinationPrefixListId"] = route_spec.pop("DestinationCidrBlock")

    return set(route_spec.items()).issubset(route.items())


def route_spec_matches_route_cidr(route_spec, route):
    if route_spec.get("DestinationCidrBlock") and route.get("DestinationCidrBlock"):
        return route_spec.get("DestinationCidrBlock") == route.get("DestinationCidrBlock")
    if route_spec.get("DestinationIpv6CidrBlock") and route.get("DestinationIpv6CidrBlock"):
        return route_spec.get("DestinationIpv6CidrBlock") == route.get("DestinationIpv6CidrBlock")
    return False


def rename_key(d, old_key, new_key):
    d[new_key] = d.pop(old_key)


def index_of_matching_route(route_spec, routes_to_match):
    for i, route in enumerate(routes_to_match):
        if route_spec_matches_route(route_spec, route):
            return "exact", i
        elif "Origin" in route and route["Origin"] != "EnableVgwRoutePropagation":  # only replace created routes
            if route_spec_matches_route_cidr(route_spec, route):
                return "replace", i


def ensure_routes(
    connection,
    module: AnsibleAWSModule,
    route_table: Dict[str, Any],
    route_specs: List[Dict[str, Any]],
    purge_routes: bool,
) -> bool:
    routes_to_match = list(route_table["Routes"])
    route_specs_to_create = []
    route_specs_to_recreate = []
    for route_spec in route_specs:
        match = index_of_matching_route(route_spec, routes_to_match)
        if match is None:
            if route_spec.get("DestinationCidrBlock") or route_spec.get("DestinationIpv6CidrBlock"):
                route_specs_to_create.append(route_spec)
            else:
                module.warn(
                    f"Skipping creating {route_spec} because it has no destination cidr block. To add VPC endpoints to"
                    " route tables use the ec2_vpc_endpoint module."
                )
        else:
            if match[0] == "replace":
                if route_spec.get("DestinationCidrBlock"):
                    route_specs_to_recreate.append(route_spec)
                else:
                    module.warn(f"Skipping recreating route {route_spec} because it has no destination cidr block.")
            del routes_to_match[match[1]]

    routes_to_delete = []
    if purge_routes:
        for route in routes_to_match:
            if not route.get("DestinationCidrBlock"):
                module.warn(
                    f"Skipping purging route {route} because it has no destination cidr block. To remove VPC endpoints"
                    " from route tables use the ec2_vpc_endpoint module."
                )
                continue
            if route["Origin"] == "CreateRoute":
                routes_to_delete.append(route)

    if module.check_mode:
        return bool(routes_to_delete or route_specs_to_create or route_specs_to_recreate)

    changed = False
    # Delete routes
    for route in routes_to_delete:
        changed |= delete_route(
            connection,
            route_table_id=route_table["RouteTableId"],
            DestinationCidrBlock=route["DestinationCidrBlock"],
        )
    # Replace routes
    for route_spec in route_specs_to_recreate:
        replace_route(connection, route_table_id=route_table["RouteTableId"], **route_spec)
        changed = True
    # Create routes
    for route_spec in route_specs_to_create:
        create_route(connection, route_table_id=route_table["RouteTableId"], **route_spec)
        changed = True

    return changed


def ensure_subnet_association(
    connection, module: AnsibleAWSModule, vpc_id: str, route_table_id: str, subnet_id: str
) -> Tuple[bool, Optional[str]]:
    filters = ansible_dict_to_boto3_filter_list({"association.subnet-id": subnet_id, "vpc-id": vpc_id})
    route_tables = describe_route_tables(connection, Filters=filters)

    association_id = None
    for route_table in route_tables:
        if route_table.get("RouteTableId"):
            for association in route_table["Associations"]:
                if association["Main"]:
                    continue
                if association["SubnetId"] == subnet_id:
                    if route_table["RouteTableId"] == route_table_id:
                        return False, association["RouteTableAssociationId"]
                    if not module.check_mode:
                        disassociate_route_table(connection, association["RouteTableAssociationId"])
                    return True, association_id

    if not module.check_mode:
        association_id = associate_route_table(connection, route_table_id=route_table_id, SubnetId=subnet_id)[
            "AssociationId"
        ]
    return True, association_id


def ensure_subnet_associations(
    connection,
    module: AnsibleAWSModule,
    route_table: Dict[str, Any],
    subnets: List[Dict[str, Any]],
    purge_subnets: bool,
) -> bool:
    current_association_ids = [
        association["RouteTableAssociationId"]
        for association in route_table["Associations"]
        if not association["Main"] and association.get("SubnetId")
    ]
    new_association_ids = []
    changed = False
    for subnet in subnets:
        result, association_id = ensure_subnet_association(
            connection=connection,
            module=module,
            vpc_id=route_table["VpcId"],
            route_table_id=route_table["RouteTableId"],
            subnet_id=subnet["SubnetId"],
        )
        changed |= result
        if changed and module.check_mode:
            return True
        new_association_ids.append(association_id)

    if purge_subnets:
        to_delete = [
            association_id for association_id in current_association_ids if association_id not in new_association_ids
        ]
        for association_id in to_delete:
            changed = True
            if not module.check_mode:
                disassociate_route_table(connection, association_id)

    return changed


def disassociate_gateway(connection, module: AnsibleAWSModule, route_table: Dict[str, Any]) -> bool:
    # Delete all gateway associations that have state = associated
    # Subnet associations are handled in its method
    changed = False
    associations_to_delete = [
        association["RouteTableAssociationId"]
        for association in route_table["Associations"]
        if not association["Main"]
        and association.get("GatewayId")
        and association["AssociationState"]["State"] in ["associated", "associating"]
    ]
    for association_id in associations_to_delete:
        changed = True
        if not module.check_mode:
            disassociate_route_table(connection, association_id)

    return changed


def associate_gateway(connection, module: AnsibleAWSModule, route_table: Dict[str, Any], gateway_id: str) -> bool:
    filters = ansible_dict_to_boto3_filter_list({"association.gateway-id": gateway_id, "vpc-id": route_table["VpcId"]})
    route_tables = describe_route_tables(connection, Filters=filters)

    for table in route_tables:
        if table.get("RouteTableId"):
            for association in table.get("Associations"):
                if association["Main"]:
                    continue
                if association.get("GatewayId", "") == gateway_id and (
                    association["AssociationState"]["State"] in ["associated", "associating"]
                ):
                    if table["RouteTableId"] == route_table["RouteTableId"]:
                        return False
                    elif module.check_mode:
                        return True
                    else:
                        disassociate_route_table(connection, association["RouteTableAssociationId"])

    if not module.check_mode:
        associate_route_table(connection, route_table_id=route_table["RouteTableId"], GatewayId=gateway_id)
    return True


def ensure_propagation(
    connection, module: AnsibleAWSModule, route_table: Dict[str, Any], propagating_vgw_ids: List[str]
) -> bool:
    changed = False
    gateways = [gateway["GatewayId"] for gateway in route_table["PropagatingVgws"]]
    vgws_to_add = set(propagating_vgw_ids) - set(gateways)
    if not vgws_to_add:
        return changed
    changed = True
    if module.check_mode:
        return changed
    for vgw_id in vgws_to_add:
        enable_vgw_route_propagation(connection, route_table_id=route_table["RouteTableId"], gateway_id=vgw_id)

    return changed


def ensure_route_table_absent(connection, module: AnsibleAWSModule) -> Dict[str, bool]:
    lookup = module.params.get("lookup")
    route_table_id = module.params.get("route_table_id")
    tags = module.params.get("tags")
    vpc_id = module.params.get("vpc_id")
    purge_subnets = module.params.get("purge_subnets")
    route_table = None

    if lookup == "tag" and tags is not None:
        route_table = get_route_table_by_tags(connection, module, vpc_id, tags)
    elif lookup == "id":
        route_table = get_route_table_by_id(connection, route_table_id)

    if route_table is None:
        return {"changed": False}

    # disassociate subnets and gateway before deleting route table
    changed = False
    if module.check_mode:
        changed = True
    else:
        changed = ensure_subnet_associations(
            connection=connection, module=module, route_table=route_table, subnets=[], purge_subnets=purge_subnets
        )
        changed |= disassociate_gateway(connection=connection, module=module, route_table=route_table)
        changed |= delete_route_table(connection, route_table_id=route_table["RouteTableId"])

    return {"changed": changed}


def get_route_table_info(connection, module: AnsibleAWSModule, route_table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    result = get_route_table_by_id(connection, route_table["RouteTableId"]) or {}
    if result:
        result["Tags"] = describe_ec2_tags(connection, module, route_table["RouteTableId"])
        result = camel_dict_to_snake_dict(result, ignore_list=["Tags"])
        # backwards compatibility
        result["id"] = result["route_table_id"]
    return result


def create_route_spec(connection, module, vpc_id):
    routes = module.params.get("routes")
    for route_spec in routes:
        cidr_block_type = str(type(ip_network(route_spec["dest"])))
        if "IPv4" in cidr_block_type:
            rename_key(route_spec, "dest", "destination_cidr_block")
        if "IPv6" in cidr_block_type:
            rename_key(route_spec, "dest", "destination_ipv6_cidr_block")

        if route_spec.get("gateway_id") and route_spec["gateway_id"].lower() == "igw":
            igw = find_igw(connection, module, vpc_id)
            route_spec["gateway_id"] = igw
        if route_spec.get("gateway_id") and route_spec["gateway_id"].startswith("nat-"):
            rename_key(route_spec, "gateway_id", "nat_gateway_id")
        if route_spec.get("gateway_id") and route_spec["gateway_id"].startswith("cagw-"):
            rename_key(route_spec, "gateway_id", "carrier_gateway_id")
        if route_spec.get("gateway_id") and route_spec["gateway_id"].startswith("tgw-"):
            rename_key(route_spec, "gateway_id", "transit_gateway_id")

    return snake_dict_to_camel_dict(routes, capitalize_first=True)


def ensure_route_table_present(connection, module: AnsibleAWSModule) -> Dict[str, Any]:
    gateway_id = module.params.get("gateway_id")
    lookup = module.params.get("lookup")
    propagating_vgw_ids = module.params.get("propagating_vgw_ids")
    purge_routes = module.params.get("purge_routes")
    purge_subnets = module.params.get("purge_subnets")
    purge_tags = module.params.get("purge_tags")
    route_table_id = module.params.get("route_table_id")
    subnets = module.params.get("subnets")
    tags = module.params.get("tags")
    vpc_id = module.params.get("vpc_id")
    routes = create_route_spec(connection, module, vpc_id)

    changed = False
    tags_valid = False
    route_table = None

    if lookup == "tag" and tags is not None:
        route_table = get_route_table_by_tags(connection, module, vpc_id, tags)
    elif lookup == "id":
        route_table = get_route_table_by_id(connection, route_table_id)

    # If no route table returned then create new route table
    if route_table is None:
        changed = True
        if module.check_mode:
            route_table = {"id": "rtb-xxxxxxxx", "route_table_id": "rtb-xxxxxxxx", "vpc_id": vpc_id}
            module.exit_json(changed=changed, route_table=route_table)

        route_table = create_route_table(connection, vpc_id, tags)
        # try to wait for route table to be present before moving on
        wait_for_resource_state(connection, module, "route_table_exists", RouteTableIds=[route_table["RouteTableId"]])

    if routes is not None:
        changed |= ensure_routes(
            connection=connection, module=module, route_table=route_table, route_specs=routes, purge_routes=purge_routes
        )

    if propagating_vgw_ids is not None:
        changed |= ensure_propagation(
            connection=connection, module=module, route_table=route_table, propagating_vgw_ids=propagating_vgw_ids
        )

    if not tags_valid and tags is not None:
        changed |= ensure_ec2_tags(
            connection,
            module,
            route_table["RouteTableId"],
            tags=tags,
            purge_tags=purge_tags,
            retry_codes=["InvalidRouteTableID.NotFound"],
        )
        route_table["Tags"] = describe_ec2_tags(connection, module, route_table["RouteTableId"])

    if subnets is not None:
        associated_subnets = find_subnets(connection, module, vpc_id, subnets)
        changed |= ensure_subnet_associations(
            connection=connection,
            module=module,
            route_table=route_table,
            subnets=associated_subnets,
            purge_subnets=purge_subnets,
        )

    if gateway_id == "None" or gateway_id == "":
        gateway_changed = disassociate_gateway(connection=connection, module=module, route_table=route_table)
    elif gateway_id is not None:
        gateway_changed = associate_gateway(
            connection=connection, module=module, route_table=route_table, gateway_id=gateway_id
        )
    else:
        gateway_changed = False
    changed = changed or gateway_changed

    if changed:
        # pause to allow route table routes/subnets/associations to be updated before exiting with final state
        sleep(5)

    return dict(changed=changed, route_table=get_route_table_info(connection, module, route_table))


def main() -> None:
    argument_spec = dict(
        gateway_id=dict(type="str"),
        lookup=dict(default="tag", choices=["tag", "id"]),
        propagating_vgw_ids=dict(type="list", elements="str"),
        purge_routes=dict(default=True, type="bool"),
        purge_subnets=dict(default=True, type="bool"),
        purge_tags=dict(type="bool", default=True),
        route_table_id=dict(),
        routes=dict(default=[], type="list", elements="dict"),
        state=dict(default="present", choices=["present", "absent"]),
        subnets=dict(type="list", elements="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        vpc_id=dict(),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ["lookup", "id", ["route_table_id"]],
            ["lookup", "tag", ["vpc_id"]],
            ["state", "present", ["vpc_id"]],
        ],
        supports_check_mode=True,
    )

    connection = module.client("ec2")
    method_operation = (
        ensure_route_table_present if module.params.get("state") == "present" else ensure_route_table_absent
    )

    try:
        result = method_operation(connection, module)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    module.exit_json(**result)


if __name__ == "__main__":
    main()

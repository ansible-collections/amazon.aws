#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_vpn
version_added: 1.0.0
version_added_collection: community.aws
short_description: Create, modify, and delete EC2 VPN connections
description:
  - This module creates, modifies, and deletes VPN connections.
  - Idempotence is achieved by using the O(filters) option or specifying the VPN connection identifier.
author:
  - Sloane Hertel (@s-hertel)
options:
  state:
    description:
      - The desired state of the VPN connection.
    choices: ["present", "absent"]
    default: present
    required: false
    type: str
  customer_gateway_id:
    description:
      - The ID of the customer gateway.
    type: str
  connection_type:
    description:
      - The type of VPN connection.
      - At this time only V(ipsec.1) is supported.
    default: "ipsec.1"
    type: str
  vpn_gateway_id:
    description:
      - The ID of the virtual private gateway.
      - Mutually exclusive with O(transit_gateway_id).
    type: str
  vpn_connection_id:
    description:
      - The ID of the VPN connection. Required to modify or delete a connection if the filters option does not provide a unique match.
    type: str
  static_only:
    description:
      - Indicates whether the VPN connection uses static routes only. Static routes must be used for devices that don't support BGP.
    default: false
    type: bool
    required: false
  transit_gateway_id:
    description:
      - The ID of the transit gateway.
      - Mutually exclusive with O(vpn_gateway_id).
    type: str
    version_added: 6.2.0
  local_ipv4_network_cidr:
    description:
      - The IPv4 CIDR on the customer gateway (on-premises) side of the VPN connection.
    required: false
    type: str
    default: "0.0.0.0/0"
    version_added: 9.0.0
  tunnel_options:
    description:
      - An optional list object containing no more than two dict members, each of which may contain O(tunnel_options.TunnelInsideCidr)
        and/or O(tunnel_options.PreSharedKey) keys with appropriate string values.
        AWS defaults will apply in absence of either of the aforementioned keys.
    required: false
    type: list
    elements: dict
    default: []
    suboptions:
        TunnelInsideCidr:
            type: str
            description:
              - The range of inside IPv4 addresses for the tunnel.
        TunnelInsideIpv6Cidr:
            type: str
            description:
              - The range of inside IPv6 addresses for the tunnel.
            version_added: 9.0.0
        PreSharedKey:
            type: str
            description:
              - The pre-shared key (PSK) to establish initial authentication between the virtual private gateway and customer gateway.
  filters:
    description:
      - An alternative to using O(vpn_connection_id). If multiple matches are found, O(vpn_connection_id) is required.
        If one of the following suboptions is a list of items to filter by, only one item needs to match to find the VPN
        that correlates. e.g. if the filter O(filters.cidr) is V(["194.168.2.0/24", "192.168.2.0/24"]) and the VPN route only has the
        destination cidr block of V(192.168.2.0/24) it will be found with this filter (assuming there are not multiple
        VPNs that are matched). Another example, if the filter O(filters.vpn) is equal to V(["vpn-ccf7e7ad", "vpn-cb0ae2a2"]) and one
        of of the VPNs has the state deleted (exists but is unmodifiable) and the other exists and is not deleted,
        it will be found via this filter.
    suboptions:
      cgw-config:
        description:
          - The customer gateway configuration of the VPN as a string (in the format of the return value) or a list of those strings.
      static-routes-only:
        description:
          - The type of routing; V(true) or V(false).
        type: bool
      cidr:
        description:
          - The destination cidr of the VPN's route as a string or a list of those strings.
      bgp:
        description:
          - The BGP ASN number associated with a BGP device. Only works if the connection is attached.
            This filtering option is currently not working.
      vpn:
        description:
          - The VPN connection id as a string or a list of those strings.
      vgw:
        description:
          - The virtual private gateway as a string or a list of those strings.
      tag-keys:
        description:
          - The key of a tag as a string or a list of those strings.
      tag-values:
        description:
          - The value of a tag as a string or a list of those strings.
      tags:
        description:
          - A dict of key value pairs.
        type: dict
      cgw:
        description:
          - The customer gateway id as a string or a list of those strings.
    type: dict
    default: {}
  routes:
    description:
      - Routes to add to the connection.
    type: list
    elements: str
    default: []
  purge_routes:
    description:
      - Whether or not to delete VPN connections routes that are not specified in the task.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long, in seconds, before wait gives up.
    default: 600
    type: int
    required: false
  delay:
    description:
      - The time, in seconds, to wait before checking operation again.
    required: false
    type: int
    default: 15
extends_documentation_fragment:
  - amazon.aws.region.modules
  - amazon.aws.common.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a VPN connection with vpn_gateway_id
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    vpn_gateway_id: "vgw-XXXXXXXX"
    customer_gateway_id: "cgw-XXXXXXXX"

- name: Attach a vpn connection to transit gateway
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    transit_gateway_id: "tgw-XXXXXXXX"
    customer_gateway_id: "cgw-XXXXXXXX"

- name: Modify VPN connection tags
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    vpn_connection_id: "vpn-XXXXXXXX"
    tags:
      Name: "ansible-tag-1"
      Other: "ansible-tag-2"

- name: Delete a connection
  amazon.aws.ec2_vpc_vpn:
    vpn_connection_id: "vpn-XXXXXXXX"
    state: "absent"

- name: Modify VPN tags (identifying VPN by filters)
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    filters:
      cidr: "194.168.1.0/24"
      tag-keys:
        - "Ansible"
        - "Other"
    tags:
      New: "Tag"
    purge_tags: true
    static_only: true

- name: Set up VPN with tunnel options utilizing 'TunnelInsideCidr' only
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    filters:
      vpn: "vpn-XXXXXXXX"
    static_only: true
    tunnel_options:
      - TunnelInsideCidr: "169.254.100.1/30"
      - TunnelInsideCidr: "169.254.100.5/30"

- name: Add routes and remove any preexisting ones
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    filters:
      vpn: "vpn-XXXXXXXX"
    routes:
      - "195.168.2.0/24"
      - "196.168.2.0/24"
    purge_routes: true

- name: Remove all routes
  amazon.aws.ec2_vpc_vpn:
    state: "present"
    vpn_connection_id: "vpn-XXXXXXXX"
    routes: []
    purge_routes: true

- name: Delete a VPN identified by filters
  amazon.aws.ec2_vpc_vpn:
    state: "absent"
    filters:
      tags:
        Ansible: "Tag"
"""

RETURN = r"""
changed:
  description: If the VPN connection has changed.
  type: bool
  returned: always
  sample: true
customer_gateway_configuration:
  description: The configuration of the VPN connection.
  returned: O(state=present)
  type: str
customer_gateway_id:
  description: The customer gateway connected via the connection.
  type: str
  returned: O(state=present)
  sample: "cgw-1220c87b"
gateway_association_state:
  description: The current state of the gateway association.
  type: str
  returned: O(state=present)
  sample: "associated"
vpn_gateway_id:
  description: The virtual private gateway connected via the connection.
  type: str
  returned: O(state=present)
  sample: "vgw-cb0ae2a2"
transit_gateway_id:
  description: The transit gateway id to which the vpn connection can be attached.
  type: str
  returned: O(state=present)
  sample: "tgw-cb0ae2a2"
options:
  description: The VPN connection options.
  type: list
  elements: dict
  returned: O(state=present)
  contains:
    static_routes_only:
      description: If the VPN connection only allows static routes.
      returned: O(state=present)
      type: bool
      sample: true
    enable_acceleration:
      description: Indicates whether acceleration is enabled for the VPN connection.
      returned: O(state=present)
      type: bool
      sample: false
    local_ipv4_network_cidr:
      description: The IPv4 CIDR on the customer gateway (on-premises) side of the VPN connection.
      returned: O(state=present)
      type: str
      sample: "0.0.0.0/0"
    outside_ip_address_type:
      description: The external IP address of the VPN tunnel.
      returned: O(state=present)
      type: str
      sample: "PublicIpv4"
    remote_ipv4_network_cidr:
      description: The IPv4 CIDR on the Amazon Web Services side of the VPN connection.
      returned: O(state=present)
      type: str
      sample: "0.0.0.0/0"
    tunnel_inside_ip_version:
      description: Indicates whether the VPN tunnels process IPv4 or IPv6 traffic.
      returned: O(state=present)
      type: str
      sample: "ipv4"
    tunnel_options:
      description: Indicates the VPN tunnel options.
      returned: O(state=present)
      type: list
      elements: dict
      sample: [{
                "log_options": {
                    "cloud_watch_log_options": {
                        "log_enabled": false
                    }
                },
                "outside_ip_address": "34.225.101.10",
                "pre_shared_key": "8n7hnjNE8zhIt4VpMOIfcrw6XnUTHLW9",
                "tunnel_inside_cidr": "169.254.31.8/30"
            }]
      contains:
        log_options:
          description: Options for logging VPN tunnel activity.
          returned: O(state=present)
          type: dict
          contains:
            cloud_watch_log_options:
              description: Options for sending VPN tunnel logs to CloudWatch.
              type: dict
              returned: O(state=present)
        outside_ip_address:
          description: The external IP address of the VPN tunnel.
          type: str
          returned: O(state=present)
        pre_shared_key:
          description:
            - The pre-shared key (PSK) to establish initial authentication between the
              virtual private gateway and the customer gateway.
          type: str
          returned: O(state=present)
        tunnel_inside_cidr:
          description: The range of inside IPv4 addresses for the tunnel.
          type: str
          returned: O(state=present)
routes:
  description: The routes of the VPN connection.
  type: list
  returned: O(state=present)
  sample: [{
              "destination_cidr_block": "192.168.1.0/24",
              "state": "available"
            }]
  contains:
    destination_cidr_block:
      description:
        - The CIDR block associated with the local subnet of the customer data center.
      type: str
      returned: O(state=present)
    source:
      description: Indicates how the routes were provided.
      type: str
      returned: O(state=present)
    state:
      description: The current state of the static route.
      type: str
      returned: O(state=present)
state:
  description: The status of the VPN connection.
  type: str
  returned: O(state=present)
  sample: "available"
tags:
  description: The tags associated with the connection.
  type: dict
  returned: O(state=present)
  sample: {
      "name": "ansible-test",
      "other": "tag"
    }
type:
  description: The type of VPN connection (currently only ipsec.1 is available).
  type: str
  returned: O(state=present)
  sample: "ipsec.1"
vgw_telemetry:
  type: list
  returned: O(state=present)
  description: The telemetry for the VPN tunnel.
  sample: [{
            "accepted_route_count": 0,
            "last_status_change": "2024-09-30T13:12:33+00:00",
            "outside_ip_address": "34.225.101.10",
            "status": "DOWN",
            "status_message": "IPSEC IS DOWN"
        }]
  contains:
    accepted_route_count:
      type: int
      returned: O(state=present)
      description: The number of accepted routes.
    last_status_change:
      type: str
      returned: O(state=present)
      description: The date and time of the last change in status.
    outside_ip_address:
      type: str
      returned: O(state=present)
      description:
        - The Internet-routable IP address of the virtual private gateway's outside interface.
    status:
      type: str
      returned: O(state=present)
      description: The status of the VPN tunnel.
    status_message:
      type: str
      returned: O(state=present)
      description: If an error occurs, a description of the error.
    certificate_arn:
      description: The Amazon Resource Name of the virtual private gateway tunnel endpoint certificate.
      returned: when a private certificate is used for authentication
      type: str
      sample: "arn:aws:acm:us-east-1:123456789012:certificate/c544d8ce-20b8-4fff-98b0-example"
vpn_connection_id:
  description: The identifier for the VPN connection.
  type: str
  returned: O(state=present)
  sample: "vpn-781e0e19"
"""

try:
    from botocore.exceptions import WaiterError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import NoReturn
from typing import Optional
from typing import Tuple
from typing import Union

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_vpn_connection
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_vpn_connection_route
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_vpn_connection
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_vpn_connection_route
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpn_connections
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def find_vpn_connection(
    client, module: AnsibleAWSModule, vpn_connection_id: Optional[str] = None
) -> Union[None, Dict[str, Any]]:
    """Looks for a unique VPN connection. Uses find_connection_response() to return the connection found, None,
    or raise an error if there were multiple viable connections."""

    filters = module.params.get("filters")
    params: Dict[str, Any] = {}

    # vpn_connection_id may be provided via module option; takes precedence over any filter values
    if not vpn_connection_id and module.params.get("vpn_connection_id"):
        vpn_connection_id = module.params["vpn_connection_id"]

    if not isinstance(vpn_connection_id, list) and vpn_connection_id:
        vpn_connection_id = [to_text(vpn_connection_id)]
    elif isinstance(vpn_connection_id, list):
        vpn_connection_id = [to_text(connection) for connection in vpn_connection_id]

    formatted_filter: List = []
    # if vpn_connection_id is provided it will take precedence over any filters since it is a unique identifier
    if not vpn_connection_id:
        formatted_filter = create_filter(module, filters)

    if vpn_connection_id:
        params["VpnConnectionIds"] = vpn_connection_id
    params["Filters"] = formatted_filter

    # see if there is a unique matching connection
    try:
        existing_conn = describe_vpn_connections(client, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed while describing VPN connection.")

    return find_connection_response(module, connections=existing_conn)


def add_routes(client, module: AnsibleAWSModule, vpn_connection_id: str, routes_to_add: List[Dict[str, Any]]) -> bool:
    changed: bool = False
    for route in routes_to_add:
        try:
            changed |= create_vpn_connection_route(client, vpn_connection_id, route)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg=f"Failed while adding route {route} to the VPN connection {vpn_connection_id}.")
    return changed


def remove_routes(
    client, module: AnsibleAWSModule, vpn_connection_id: str, routes_to_remove: List[Dict[str, Any]]
) -> bool:
    changed: bool = False
    for route in routes_to_remove:
        try:
            changed |= delete_vpn_connection_route(client, vpn_connection_id, route)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg=f"Failed to remove route {route} from the VPN connection {vpn_connection_id}.")
    return changed


def create_filter(module, provided_filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Creates a filter using the user-specified parameters and unmodifiable options that may have been specified in the task"""

    boto3ify_filter = {
        "cgw-config": "customer-gateway-configuration",
        "static-routes-only": "option.static-routes-only",
        "cidr": "route.destination-cidr-block",
        "bgp": "bgp-asn",
        "vpn": "vpn-connection-id",
        "vgw": "vpn-gateway-id",
        "tag-keys": "tag-key",
        "tag-values": "tag-value",
        "tags": "tag",
        "cgw": "customer-gateway-id",
    }

    # unmodifiable options and their filter name counterpart
    param_to_filter = {
        "customer_gateway_id": "customer-gateway-id",
        "vpn_gateway_id": "vpn-gateway-id",
        "transit_gateway_id": "transit-gateway-id",
        "vpn_connection_id": "vpn-connection-id",
    }

    flat_filter_dict = {}
    formatted_filter: List = []

    for raw_param in dict(provided_filters):
        # fix filter names to be recognized by boto3
        if raw_param in boto3ify_filter:
            param = boto3ify_filter[raw_param]
            provided_filters[param] = provided_filters.pop(raw_param)
        elif raw_param in list(boto3ify_filter.items()):
            param = raw_param
        else:
            module.fail_json(msg=f"{raw_param} is not a valid filter.")

        # reformat filters with special formats
        if param == "tag":
            for key in provided_filters[param]:
                formatted_key = "tag:" + key
                if isinstance(provided_filters[param][key], list):
                    flat_filter_dict[formatted_key] = str(provided_filters[param][key])
                else:
                    flat_filter_dict[formatted_key] = [str(provided_filters[param][key])]
        elif param == "option.static-routes-only":
            flat_filter_dict[param] = [str(provided_filters[param]).lower()]
        else:
            if isinstance(provided_filters[param], list):
                flat_filter_dict[param] = provided_filters[param]
            else:
                flat_filter_dict[param] = [str(provided_filters[param])]

    # if customer_gateway, vpn_gateway, or vpn_connection was specified in the task but not the filter, add it
    for param, param_value in param_to_filter.items():
        if param_value not in flat_filter_dict and module.params.get(param):
            flat_filter_dict[param_value] = [module.params.get(param)]

    # change the flat dict into something boto3 will understand
    formatted_filter = [{"Name": key, "Values": value} for key, value in flat_filter_dict.items()]

    return formatted_filter


def find_connection_response(module, connections: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Determine if there is a viable unique match in the connections described. Returns the unique VPN connection if one is found,
    returns None if the connection does not exist, raise an error if multiple matches are found."""

    # Found no connections
    if not connections:
        return None

    # Too many results
    elif connections and len(connections) > 1:
        viable = []
        for each in connections:
            # deleted connections are not modifiable
            if each["State"] not in ("deleted", "deleting"):
                viable.append(each)
        if len(viable) == 1:
            # Found one viable result; return unique match
            return viable[0]
        elif len(viable) == 0:
            # Found a result but it was deleted already; since there was only one viable result create a new one
            return None
        else:
            module.fail_json(
                msg=(
                    "More than one matching VPN connection was found. "
                    "To modify or delete a VPN please specify vpn_connection_id or add filters."
                )
            )

    # Found unique match
    elif connections and len(connections) == 1:
        # deleted connections are not modifiable
        if connections[0]["State"] not in ("deleted", "deleting"):
            return connections[0]


def create_connection(
    client,
    module: AnsibleAWSModule,
    customer_gateway_id: Optional[str],
    static_only: Optional[bool],
    vpn_gateway_id: str,
    transit_gateway_id: str,
    connection_type: Optional[str],
    max_attempts: Optional[int],
    delay: Optional[int],
    local_ipv4_network_cidr: Optional[str],
    tunnel_options: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Creates a VPN connection"""

    options = {"StaticRoutesOnly": static_only, "LocalIpv4NetworkCidr": local_ipv4_network_cidr}

    if tunnel_options and len(tunnel_options) <= 2:
        t_opt = []
        for m in tunnel_options:
            # See Boto3 docs regarding 'create_vpn_connection'
            # tunnel options for allowed 'TunnelOptions' keys.
            if not isinstance(m, dict):
                raise TypeError("non-dict list member")
            t_opt.append(m)
        if t_opt:
            options["TunnelOptions"] = t_opt

    if not (customer_gateway_id and (vpn_gateway_id or transit_gateway_id)):
        module.fail_json(
            msg=(
                "No matching connection was found. To create a new connection you must provide "
                "customer_gateway_id and one of either transit_gateway_id or vpn_gateway_id."
            )
        )
    vpn_connection_params: Dict[str, Any] = {
        "Type": connection_type,
        "CustomerGatewayId": customer_gateway_id,
        "Options": options,
    }

    if vpn_gateway_id:
        vpn_connection_params["VpnGatewayId"] = vpn_gateway_id
    if transit_gateway_id:
        vpn_connection_params["TransitGatewayId"] = transit_gateway_id

    try:
        vpn = create_vpn_connection(client, **vpn_connection_params)
        client.get_waiter("vpn_connection_available").wait(
            VpnConnectionIds=[vpn["VpnConnectionId"]],
            WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
        )
    except WaiterError as e:
        module.fail_json_aws(e, msg=f"Failed to wait for VPN connection {vpn['VpnConnectionId']} to be available")
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to create VPN connection")

    return vpn


def delete_connection(client, module: AnsibleAWSModule, vpn_connection_id: str) -> NoReturn:
    """Deletes a VPN connection"""

    delay = module.params.get("delay")
    max_attempts = module.params.get("wait_timeout") // delay

    try:
        delete_vpn_connection(client, vpn_connection_id)
        client.get_waiter("vpn_connection_deleted").wait(
            VpnConnectionIds=[vpn_connection_id], WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts}
        )
    except WaiterError as e:
        module.fail_json_aws(e, msg=f"Failed to wait for VPN connection {vpn_connection_id} to be removed")
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg=f"Failed to delete the VPN connection: {vpn_connection_id}")


def check_for_routes_update(client, module: AnsibleAWSModule, vpn_connection_id: str) -> Dict[str, Any]:
    """Determines if there are any routes that need to be updated. Ensures non-modifiable attributes aren't expected to change."""
    routes = module.params.get("routes")
    purge_routes = module.params.get("purge_routes")

    vpn_connection = find_vpn_connection(client, module, vpn_connection_id)
    current_attrs = camel_dict_to_snake_dict(vpn_connection)

    # Initialize changes dict
    changes: Dict[str, Any] = {"routes_to_add": [], "routes_to_remove": []}

    # Get changes to routes
    if "Routes" in vpn_connection:
        current_routes = [route["DestinationCidrBlock"] for route in vpn_connection["Routes"]]
        if purge_routes:
            changes["routes_to_remove"] = [old_route for old_route in current_routes if old_route not in routes]
        changes["routes_to_add"] = [new_route for new_route in routes if new_route not in current_routes]

    # Check if nonmodifiable attributes are attempted to be modified
    for attribute in current_attrs:
        if attribute in ("tags", "routes", "state"):
            continue
        if attribute == "options":
            will_be = module.params.get("static_only")
            is_now = bool(current_attrs[attribute]["static_routes_only"])
            attribute = "static_only"
        elif attribute == "type":
            will_be = module.params.get("connection_type")
            is_now = current_attrs[attribute]
        else:
            is_now = current_attrs[attribute]
            will_be = module.params.get(attribute)

        if will_be is not None and to_text(will_be) != to_text(is_now):
            module.fail_json(
                msg=(
                    f"You cannot modify {attribute}, the current value of which is {is_now}. Modifiable VPN connection"
                    f" attributes are tags and routes. The value you tried to change it to is {will_be}."
                )
            )

    return changes


def make_changes(client, module: AnsibleAWSModule, vpn_connection_id: str, changes: Dict[str, Any]) -> bool:
    """changes is a dict with the keys 'routes_to_add', 'routes_to_remove',
    the values of which are lists (generated by check_for_routes_update()).
    """
    changed: bool = False

    if module.params.get("tags") is not None:
        changed |= ensure_ec2_tags(
            client,
            module,
            vpn_connection_id,
            resource_type="vpn-connection",
            tags=module.params.get("tags"),
            purge_tags=module.params.get("purge_tags"),
        )

    if changes["routes_to_add"]:
        changed |= add_routes(client, module, vpn_connection_id, changes["routes_to_add"])

    if changes["routes_to_remove"]:
        changed |= remove_routes(client, module, vpn_connection_id, changes["routes_to_remove"])

    return changed


def get_check_mode_results(
    module_params: Dict[str, Any], vpn_connection_id: Optional[str] = None, current_state: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """Returns the changes that would be made to a VPN Connection"""
    changed: bool = False
    results: Dict[str, Any] = {
        "customer_gateway_configuration": "",
        "customer_gateway_id": module_params.get("customer_gateway_id"),
        "vpn_gateway_id": module_params.get("vpn_gateway_id"),
        "transit_gateway_id": module_params.get("transit_gateway_id"),
        "options": {"static_routes_only": module_params.get("static_only")},
        "routes": [module_params.get("routes")],
    }

    present_tags = module_params.get("tags")
    # get combined current tags and tags to set
    if present_tags is None:
        pass
    elif current_state and "Tags" in current_state:
        current_tags = boto3_tag_list_to_ansible_dict(current_state["Tags"])
        tags_to_add, tags_to_remove = compare_aws_tags(current_tags, present_tags, module_params.get("purge_tags"))
        changed |= bool(tags_to_remove) or bool(tags_to_add)
        if module_params.get("purge_tags"):
            current_tags = {}
        current_tags.update(present_tags)
        results["tags"] = current_tags
    elif module_params.get("tags"):
        changed = True

    if present_tags:
        results["tags"] = present_tags

    # get combined current routes and routes to add
    present_routes = module_params.get("routes")
    if current_state and "Routes" in current_state:
        current_routes = [route["DestinationCidrBlock"] for route in current_state["Routes"]]
        if module_params.get("purge_routes"):
            if set(current_routes) != set(present_routes):
                changed = True
        elif set(present_routes) != set(current_routes):
            if not set(present_routes) < set(current_routes):
                changed = True
            present_routes.extend([route for route in current_routes if route not in present_routes])
    elif module_params.get("routes"):
        changed = True
    results["routes"] = [{"destination_cidr_block": cidr, "state": "available"} for cidr in present_routes]

    # return the vpn_connection_id if it's known
    if vpn_connection_id:
        results["vpn_connection_id"] = vpn_connection_id
    else:
        changed = True
        results["vpn_connection_id"] = "vpn-XXXXXXXX"

    return changed, results


def ensure_present(
    client, module: AnsibleAWSModule, vpn_connection: Optional[Dict[str, Any]]
) -> Tuple[bool, Dict[str, Any]]:
    """Creates and adds tags to a VPN connection. If the connection already exists update tags."""
    changed: bool = False
    delay = module.params.get("delay")
    max_attempts = module.params.get("wait_timeout") // delay

    # No match but vpn_connection_id was specified.
    if not vpn_connection and module.params.get("vpn_connection_id"):
        module.fail_json(msg="There is no VPN connection available or pending with that id. Did you delete it?")

    # Unique match was found. Check if attributes provided differ.
    elif vpn_connection:
        vpn_connection_id = vpn_connection["VpnConnectionId"]
        # check_for_update returns a dict with the keys routes_to_add, routes_to_remove
        changes = check_for_routes_update(client, module, vpn_connection_id)

        if module.check_mode:
            return get_check_mode_results(module.params, vpn_connection_id, current_state=vpn_connection)

        changed |= make_changes(client, module, vpn_connection_id, changes)

    # No match was found. Create and tag a connection and add routes.
    else:
        changed = True

        if module.check_mode:
            return get_check_mode_results(module.params)

        vpn_connection = create_connection(
            client,
            module,
            customer_gateway_id=module.params.get("customer_gateway_id"),
            static_only=module.params.get("static_only"),
            vpn_gateway_id=module.params.get("vpn_gateway_id"),
            transit_gateway_id=module.params.get("transit_gateway_id"),
            connection_type=module.params.get("connection_type"),
            local_ipv4_network_cidr=module.params.get("local_ipv4_network_cidr"),
            tunnel_options=module.params.get("tunnel_options"),
            max_attempts=max_attempts,
            delay=delay,
        )

        changes = check_for_routes_update(client, module, vpn_connection["VpnConnectionId"])
        make_changes(client, module, vpn_connection["VpnConnectionId"], changes)

    # get latest version if a change has been made and make tags output nice before returning it
    if vpn_connection:
        vpn_connection = find_vpn_connection(client, module, vpn_connection["VpnConnectionId"])
        if "Tags" in vpn_connection:
            vpn_connection["Tags"] = boto3_tag_list_to_ansible_dict(vpn_connection["Tags"])

    return (changed, vpn_connection)


def ensure_absent(client, module: AnsibleAWSModule, vpn_connection: Dict[str, Any]) -> bool:
    """Deletes a VPN connection if it exists."""
    changed: bool = False

    if vpn_connection:
        changed = True

        if module.check_mode:
            return changed

        delete_connection(client, module, vpn_connection["VpnConnectionId"])

    return changed


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        filters=dict(type="dict", default={}),
        vpn_gateway_id=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        connection_type=dict(default="ipsec.1", type="str"),
        transit_gateway_id=dict(type="str"),
        local_ipv4_network_cidr=dict(type="str", default="0.0.0.0/0"),
        tunnel_options=dict(
            no_log=True,
            type="list",
            default=[],
            elements="dict",
            options=dict(
                TunnelInsideCidr=dict(type="str"),
                TunnelInsideIpv6Cidr=dict(type="str"),
                PreSharedKey=dict(type="str", no_log=True),
            ),
        ),
        static_only=dict(default=False, type="bool"),
        customer_gateway_id=dict(type="str"),
        vpn_connection_id=dict(type="str"),
        purge_tags=dict(type="bool", default=True),
        routes=dict(type="list", default=[], elements="str"),
        purge_routes=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=600),
        delay=dict(type="int", default=15),
    )
    mutually_exclusive = [
        ["vpn_gateway_id", "transit_gateway_id"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
    )
    client = module.client("ec2")

    response: Dict[str, Any] = {}
    state = module.params.get("state")

    vpn_connection = find_vpn_connection(client, module)

    if state == "present":
        changed, response = ensure_present(client, module, vpn_connection)
    elif state == "absent":
        changed = ensure_absent(client, module, vpn_connection)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


if __name__ == "__main__":
    main()

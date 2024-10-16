#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_vpn_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: Gather information about EC2 VPN Connections in AWS
description:
  - Gather information about EC2 VPN Connections in AWS.
author:
  - Madhura Naniwadekar (@Madhura-CSI)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpnConnections.html) for possible filters.
    required: false
    type: dict
    default: {}
  vpn_connection_ids:
    description:
      - Get details of specific EC2 VPN Connection(s) using vpn connection ID/IDs. This value should be provided as a list.
    required: false
    type: list
    elements: str
    default: []
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# # Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Gather information about all  EC2 VPN Connections
  amazon.aws.ec2_vpc_vpn_info:

- name: Gather information about a filtered list of  EC2 VPN Connections, based on tags
  amazon.aws.ec2_vpc_vpn_info:
    filters:
      "tag:Name": "test-connection"
  register: vpn_conn_info

- name: Gather information about EC2 VPN Connections by specifying connection IDs
  amazon.aws.ec2_vpc_vpn_info:
    filters:
      "vpn-gateway-id": "vgw-cbe66beb"
  register: vpn_conn_info
"""

RETURN = r"""
vpn_connections:
    description: List of one or more EC2 VPN Connections.
    type: list
    elements: dict
    returned: always
    contains:
      category:
        description: The category of the VPN connection.
        returned: always
        type: str
        sample: "VPN"
      customer_gatway_configuration:
        description: The configuration information for the VPN connection's customer gateway (in the native XML format).
        returned: always
        type: str
      customer_gateway_id:
        description: The ID of the customer gateway at your end of the VPN connection.
        returned: always
        type: str
        sample: "cgw-17a53c37"
      gateway_association_state:
        description: The current state of the gateway association.
        type: str
        sample: "associated"
      options:
        description: The VPN connection options.
        type: list
        elements: dict
        contains:
          static_routes_only:
            description: If the VPN connection only allows static routes.
            type: bool
            sample: true
          enable_acceleration:
            description: Indicates whether acceleration is enabled for the VPN connection.
            type: bool
            sample: false
          local_ipv4_network_cidr:
            description: The IPv4 CIDR on the customer gateway (on-premises) side of the VPN connection.
            type: str
            sample: "0.0.0.0/0"
          outside_ip_address_type:
            description: The external IP address of the VPN tunnel.
            type: str
            sample: "PublicIpv4"
          remote_ipv4_network_cidr:
            description: The IPv4 CIDR on the Amazon Web Services side of the VPN connection.
            type: str
            sample: "0.0.0.0/0"
          tunnel_inside_ip_version:
            description: Indicates whether the VPN tunnels process IPv4 or IPv6 traffic.
            type: str
            sample: "ipv4"
          tunnel_options:
            description: Indicates the VPN tunnel options.
            type: list
            elements: dict
            sample: [
                  {
                      "log_options": {
                          "cloud_watch_log_options": {
                              "log_enabled": false
                          }
                      },
                      "outside_ip_address": "34.225.101.10",
                      "pre_shared_key": "8n7hnjNE8zhIt4VpMOIfcrw6XnUTHLW9",
                      "tunnel_inside_cidr": "169.254.31.8/30"
                  },
              ]
            contains:
              log_options:
                description: Options for logging VPN tunnel activity.
                type: dict
                contains:
                  cloud_watch_log_options:
                    description: Options for sending VPN tunnel logs to CloudWatch.
                    type: dict
              outside_ip_address:
                description: The external IP address of the VPN tunnel.
                type: str
              pre_shared_key:
                description:
                  - The pre-shared key (PSK) to establish initial authentication between the
                    virtual private gateway and the customer gateway.
                type: str
              tunnel_inside_cidr:
                description: The range of inside IPv4 addresses for the tunnel.
                type: str
      routes:
        description: List of static routes associated with the VPN connection.
        returned: always
        type: list
        elements: dict
        contains:
          destination_cidr_block:
            description:
              - The CIDR block associated with the local subnet of the customer data center.
            type: str
          source:
            description: Indicates how the routes were provided.
            type: str
          state:
            description: The current state of the static route.
            type: str
      state:
        description: The current state of the VPN connection.
        returned: always
        type: str
        sample: "available"
      tags:
        description: Any tags assigned to the VPN connection.
        returned: always
        type: dict
        sample: {
                  "Name": "test-conn"
                }
      type:
        description: The type of VPN connection.
        returned: always
        type: str
        sample: "ipsec.1"
      vgw_telemetry:
         description: Information about the VPN tunnel.
         returned: always
         type: dict
         contains:
           accepted_route_count:
             description: The number of accepted routes.
             returned: always
             type: int
             sample: 0
           last_status_change:
               description: The date and time of the last change in status.
               returned: always
               type: str
               sample: "2018-02-09T14:35:27+00:00"
           outside_ip_address:
               description: The Internet-routable IP address of the virtual private gateway's outside interface.
               returned: always
               type: str
               sample: "13.127.79.191"
           status:
               description: The status of the VPN tunnel.
               returned: always
               type: str
               sample: "DOWN"
           status_message:
               description: If an error occurs, a description of the error.
               returned: always
               type: str
               sample: "IPSEC IS DOWN"
           certificate_arn:
               description: The Amazon Resource Name of the virtual private gateway tunnel endpoint certificate.
               returned: when a private certificate is used for authentication
               type: str
               sample: "arn:aws:acm:us-east-1:123456789012:certificate/c544d8ce-20b8-4fff-98b0-example"
      vpn_connection_id:
        description: The ID of the VPN connection.
        returned: always
        type: str
        sample: "vpn-f700d5c0"
      vpn_gateway_id:
        description: The ID of the virtual private gateway at the AWS side of the VPN connection.
        returned: always
        type: str
        sample: "vgw-cbe56bfb"
"""

import json
from typing import Any
from typing import Dict
from typing import NoReturn

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpn_connections
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def date_handler(obj: Dict[str, Any]) -> Dict[str, Any]:
    return obj.isoformat() if hasattr(obj, "isoformat") else obj


def list_vpn_connections(client, module: AnsibleAWSModule) -> NoReturn:
    params: Dict[str, Any] = {}

    params["Filters"] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    params["VpnConnectionIds"] = module.params.get("vpn_connection_ids")

    try:
        result = json.loads(json.dumps(describe_vpn_connections(client, **params), default=date_handler))
    except ValueError as e:
        module.fail_json(e, msg="Cannot validate JSON data")
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Could not describe customer gateways")

    snaked_vpn_connections = [camel_dict_to_snake_dict(vpn_connection) for vpn_connection in result]
    if snaked_vpn_connections:
        for vpn_connection in snaked_vpn_connections:
            vpn_connection["tags"] = boto3_tag_list_to_ansible_dict(vpn_connection.get("tags", []))

    module.exit_json(changed=False, vpn_connections=snaked_vpn_connections)


def main():
    argument_spec = dict(
        vpn_connection_ids=dict(default=[], type="list", elements="str"),
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["vpn_connection_ids", "filters"]],
        supports_check_mode=True,
    )

    connection = module.client("ec2")

    list_vpn_connections(connection, module)


if __name__ == "__main__":
    main()

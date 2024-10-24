#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_transit_gateway_info
short_description: Retrieve information about EC2 Transit Gateways in AWS
version_added: 1.0.0
version_added_collection: community.aws
description:
  - Gather information about EC2 Transit Gateways in AWS.
author:
  - "Bob Boldin (@BobBoldin)"
options:
  transit_gateway_ids:
    description:
      - A list of Transit Gateway IDs for which to gather information.
    aliases: [transit_gateway_id]
    type: list
    elements: str
    default: []
  filters:
    description:
      - A dictionary of filters to apply to the query. Each key-value pair represents a filter key and its corresponding value.
      - For a complete list of available filters,
        refer to the AWS documentation U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeTransitGateways.html).
    type: dict
    default: {}
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather info about all transit gateways
  amazon.aws.ec2_transit_gateway_info:

- name: Gather info about a particular transit gateway using filter transit gateway ID
  amazon.aws.ec2_transit_gateway_info:
    filters:
      transit-gateway-id: tgw-02c42332e6b7da829

- name: Gather info about a particular transit gateway using multiple option filters
  amazon.aws.ec2_transit_gateway_info:
    filters:
      options.dns-support: enable
      options.vpn-ecmp-support: enable

- name: Gather info about multiple transit gateways using module param
  amazon.aws.ec2_transit_gateway_info:
    transit_gateway_ids:
      - tgw-02c42332e6b7da829
      - tgw-03c53443d5a8cb716
"""

RETURN = r"""
transit_gateways:
    description:
      - Transit gateways that match the provided filters.
      - Each element consists of a dict with all the information related to that transit gateway.
    returned: on success
    type: list
    elements: dict
    contains:
        creation_time:
            description: The creation time.
            returned: always
            type: str
            sample: "2019-02-05T16:19:58+00:00"
        description:
            description: The description of the transit gateway.
            returned: always
            type: str
            sample: "A transit gateway"
        options:
            description: A dictionary of the transit gateway options.
            returned: always
            type: dict
            contains:
                 amazon_side_asn:
                    description:
                      - A private Autonomous System Number (ASN) for the Amazon ide of a BGP session.
                      - The range is 64512 to 65534 for 16-bit ASNs and 4200000000 to 4294967294 for 32-bit ASNs.
                    returned: always
                    type: int
                    sample: 64512
                 auto_accept_shared_attachments:
                    description: Indicates whether attachment requests are automatically accepted.
                    returned: always
                    type: str
                    sample: "enable"
                 default_route_table_association:
                    description: Indicates whether resource attachments are automatically associated with the default association route table.
                    returned: always
                    type: str
                    sample: "disable"
                 association_default_route_table_id:
                    description: The ID of the default association route table.
                    returned: when present
                    type: str
                    sample: "tgw-rtb-0fd332c911223344"
                 default_route_table_propagation:
                    description: Indicates whether resource attachments automatically propagate routes to the default propagation route table.
                    returned: always
                    type: str
                    sample: "disable"
                 dns_support:
                    description: Indicates whether DNS support is enabled.
                    returned: always
                    type: str
                    sample: "enable"
                 multicast_support:
                    description: Indicates whether Multicast support is enabled.
                    returned: always
                    type: str
                    sample: "enable"
                    version_added: 7.3.0
                 propagation_default_route_table_id:
                    description: The ID of the default propagation route table.
                    returned: when present
                    type: str
                    sample: "rtb-11223344"
                 vpn_ecmp_support:
                    description: Indicates whether Equal Cost Multipath Protocol support is enabled.
                    returned: always
                    type: str
                    sample: "enable"
        owner_id:
            description: The AWS account number ID which owns the transit gateway.
            returned: always
            type: str
            sample: "123456789012"
        state:
            description: The state of the transit gateway.
            returned: always
            type: str
            sample: "available"
        tags:
            description: A dict of tags associated with the transit gateway.
            returned: always
            type: dict
            sample: {
                      "Name": "A sample TGW",
                      "Env": "Dev"
                    }
        transit_gateway_arn:
            description: The Amazon Resource Name (ARN) of the transit gateway.
            returned: always
            type: str
            sample: "arn:aws:ec2:us-west-2:123456789012:transit-gateway/tgw-02c42332e6b7da829"
        transit_gateway_id:
            description: The ID of the transit gateway.
            returned: always
            type: str
            sample: "tgw-02c42332e6b7da829"
"""

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_transit_gateways
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def get_transit_gateway_response(module: AnsibleAWSModule, connection) -> Dict[str, Any]:
    """
    Get transit gateway response from AWS.

    module     : AnsibleAWSModule object
    connection : boto3 client connection object
    :return: Response from describe_transit_gateways call
    """
    filters = ansible_dict_to_boto3_filter_list(module.params["filters"])
    transit_gateway_ids = module.params["transit_gateway_ids"]

    params = {}
    if transit_gateway_ids:
        params["TransitGatewayIds"] = transit_gateway_ids
    if filters:
        params["Filters"] = filters

    result = describe_ec2_transit_gateways(connection, **params)
    return result


def extract_transit_gateway_info(transit_gateway: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and transform transit gateway information.

    transit_gateway : The transit gateway data from AWS
    :return: Transformed transit gateway information
    """
    tgw_data = camel_dict_to_snake_dict(transit_gateway, ignore_list=["Tags"])
    tgw_data["tags"] = boto3_tag_list_to_ansible_dict(transit_gateway.get("Tags", []))
    return tgw_data


def describe_transit_gateways(module: AnsibleAWSModule, connection) -> List[Dict[str, Any]]:
    """
    Describe transit gateways.

    module     : AnsibleAWSModule object
    connection : boto3 client connection object
    :return: List of transit gateways
    """
    response = get_transit_gateway_response(module, connection)
    return [extract_transit_gateway_info(tgw) for tgw in response]


def setup_module_object() -> AnsibleAWSModule:
    """
    Merge argument spec and create Ansible module object.
    :return: Ansible module object
    """
    argument_spec = dict(
        transit_gateway_ids=dict(type="list", default=[], elements="str", aliases=["transit_gateway_id"]),
        filters=dict(type="dict", default={}),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    return module


def main():
    module = setup_module_object()
    results = {"changed": False}

    connection = module.client("ec2")
    try:
        transit_gateways = describe_transit_gateways(module, connection)
        results["transit_gateways"] = transit_gateways
    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    module.exit_json(**results)


if __name__ == "__main__":
    main()

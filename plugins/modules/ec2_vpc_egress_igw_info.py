#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_egress_igw_info
version_added: 9.0.0
short_description: Gather information about AWS VPC Egress Only Internet gateway
description:
    - Gather information about AWS VPC Egress Only Internet gateway.
author: "Aubin Bikouo (@abikouo)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeEgressOnlyInternetGateways.html) for possible filters.
    type: dict
    default: {}
  egress_only_internet_gateway_ids:
    description:
      - Get details of specific VPC Egress Internet Gateway ID.
    type: list
    elements: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all VPC Egress only Internet Gateways for an account or profile
  amazon.aws.ec2_vpc_igw_info:
    region: ap-southeast-2
    profile: production

- name: Gather information about a filtered list of VPC Egress only Internet Gateways
  amazon.aws.ec2_vpc_igw_info:
    region: ap-southeast-2
    profile: production
    filters:
      "tag:Name": "igw-123"

- name: Gather information about a specific VPC egress only internet gateway by EgressOnlyInternetGatewayId
  amazon.aws.ec2_vpc_igw_info:
    region: ap-southeast-2
    profile: production
    egress_only_internet_gateway_ids: igw-c1231234
"""

RETURN = r"""
egress_only_internet_gateways:
    description: The AWS Egress only internet gateways.
    returned: always
    type: list
    contains:
        attachments:
            description: Information about the attachment of the egress-only internet gateway.
            returned: always
            type: list
            contains:
                state:
                    description: The current state of the attachment.
                    returned: always
                    type: str
                    sample: "available"
                vpc_id:
                    description: The ID of the VPC.
                    returned: always
                    type: str
                    sample: "vpc-02123b67"
        egress_only_internet_gateway_id:
            description: The ID of the egress-only internet gateway.
            returned: always
            type: str
            sample: "eigw-0123456789abcdef"
        tags:
            description: Any tags assigned to the egress-only internet gateway.
            returned: always
            type: dict
"""

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_egress_only_internet_gateways
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def format_egress_only_internet_gateway(internet_gateway: Dict[str, Any]) -> Dict[str, Any]:
    tags = boto3_tag_list_to_ansible_dict(internet_gateway.get("Tags", []))
    egress_only_igw = {
        "EgressOnlyInternetGatewayId": internet_gateway["EgressOnlyInternetGatewayId"],
        "Attachments": internet_gateway["Attachments"],
        "Tags": tags,
    }
    return camel_dict_to_snake_dict(egress_only_igw, ignore_list=["Tags"])


def list_egress_only_internet_gateways(connection, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    params = dict()

    params["Filters"] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    if module.params.get("egress_only_internet_gateway_ids"):
        params["EgressOnlyInternetGatewayIds"] = module.params.get("egress_only_internet_gateway_ids")

    try:
        egress_only_igws = describe_egress_only_internet_gateways(connection, **params)
        return [format_egress_only_internet_gateway(igw) for igw in egress_only_igws]
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, "Unable to describe egress only internet gateways")


def main() -> None:
    argument_spec = dict(
        filters=dict(type="dict", default=dict()),
        egress_only_internet_gateway_ids=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    client = module.client("ec2")

    results = list_egress_only_internet_gateways(client, module)
    module.exit_json(egress_only_internet_gateways=results)


if __name__ == "__main__":
    main()

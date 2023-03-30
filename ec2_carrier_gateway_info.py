#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_carrier_gateway_info
version_added: 6.0.0
short_description: Gather information about carrier gateways in AWS
description:
  - Gather information about carrier gateways in AWS.
author:
  - "Marco Braga (@mtulio)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeCarrierGateways.html) for possible filters.
    required: false
    default: {}
    type: dict
  carrier_gateway_ids:
    description:
      - Get details of specific Carrier Gateway ID.
    required: false
    type: list
    elements: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all Carrier Gateways for an account or profile
  community.aws.ec2_carrier_gateway_info:
    region: ap-southeast-2
  register: cagw_info

- name: Gather information about a filtered list of Carrier Gateways
  community.aws.ec2_carrier_gateway_info:
    region: ap-southeast-2
    filters:
        "tag:Name": "cagw-123"
  register: cagw_info

- name: Gather information about a specific carrier gateway by CarrierGatewayId
  community.aws.ec2_carrier_gateway_info:
    region: ap-southeast-2
    carrier_gateway_ids: cagw-c1231234
  register: cagw_info
"""

RETURN = r"""
changed:
    description: True if listing the carrier gateways succeeds.
    type: bool
    returned: always
    sample: "false"
carrier_gateways:
    description: The carrier gateways for the account.
    returned: always
    type: complex
    contains:
        vpc_id:
            description: The ID of the VPC.
            returned: I(state=present)
            type: str
            sample: vpc-02123b67
        carrier_gateway_id:
            description: The ID of the carrier gateway.
            returned: I(state=present)
            type: str
            sample: cagw-2123634d
        tags:
            description: Any tags assigned to the carrier gateway.
            returned: I(state=present)
            type: dict
            sample:
                tags:
                    "Ansible": "Test"
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def get_carrier_gateway_info(carrier_gateway):
    tags = boto3_tag_list_to_ansible_dict(carrier_gateway["Tags"])
    ignore_list = []
    carrier_gateway_info = {
        "CarrierGatewayId": carrier_gateway["CarrierGatewayId"],
        "VpcId": carrier_gateway["VpcId"],
        "Tags": tags,
    }

    carrier_gateway_info = camel_dict_to_snake_dict(carrier_gateway_info, ignore_list=ignore_list)
    return carrier_gateway_info


def list_carrier_gateways(connection, module):
    params = dict()

    params["Filters"] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    if module.params.get("carrier_gateway_ids"):
        params["CarrierGatewayIds"] = module.params.get("carrier_gateway_ids")

    try:
        all_carrier_gateways = connection.describe_carrier_gateways(aws_retry=True, **params)
    except is_boto3_error_code("InvalidCarrierGatewayID.NotFound"):
        module.fail_json("CarrierGateway not found")
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, "Unable to describe carrier gateways")

    return [get_carrier_gateway_info(cagw) for cagw in all_carrier_gateways["CarrierGateways"]]


def main():
    argument_spec = dict(
        carrier_gateway_ids=dict(default=None, elements="str", type="list"),
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Validate Requirements
    try:
        connection = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    results = list_carrier_gateways(connection, module)

    module.exit_json(carrier_gateways=results)


if __name__ == "__main__":
    main()

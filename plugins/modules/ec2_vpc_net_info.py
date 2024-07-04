#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_net_info
version_added: 1.0.0
short_description: Gather information about EC2 VPCs in AWS
description:
    - Gather information about EC2 VPCs in AWS.
author: "Rob White (@wimnat)"
options:
  vpc_ids:
    description:
      - A list of VPC IDs that exist in your account.
    type: list
    elements: str
    default: []
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcs.html) for possible filters.
    type: dict
    default: {}
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all VPCs
- amazon.aws.ec2_vpc_net_info:

# Gather information about a particular VPC using VPC ID
- amazon.aws.ec2_vpc_net_info:
    vpc_ids: vpc-00112233

# Gather information about any VPC with a tag key Name and value Example
- amazon.aws.ec2_vpc_net_info:
    filters:
      "tag:Name": Example
"""

RETURN = r"""
vpcs:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        id:
            description: The ID of the VPC (for backwards compatibility).
            returned: always
            type: str
        vpc_id:
            description: The ID of the VPC.
            returned: always
            type: str
        state:
            description: The state of the VPC.
            returned: always
            type: str
        tags:
            description: A dict of tags associated with the VPC.
            returned: always
            type: dict
        instance_tenancy:
            description: The instance tenancy setting for the VPC.
            returned: always
            type: str
        is_default:
            description: True if this is the default VPC for account.
            returned: always
            type: bool
        cidr_block:
            description: The IPv4 CIDR block assigned to the VPC.
            returned: always
            type: str
        enable_dns_hostnames:
            description: True/False depending on attribute setting for DNS hostnames support.
            returned: always
            type: bool
        enable_dns_support:
            description: True/False depending on attribute setting for DNS support.
            returned: always
            type: bool
        cidr_block_association_set:
            description: An array of IPv4 cidr block association set information.
            returned: always
            type: complex
            contains:
                association_id:
                    description: The association ID.
                    returned: always
                    type: str
                cidr_block:
                    description: The IPv4 CIDR block that is associated with the VPC.
                    returned: always
                    type: str
                cidr_block_state:
                    description: A hash/dict that contains a single item. The state of the cidr block association.
                    returned: always
                    type: dict
                    contains:
                        state:
                            description: The CIDR block association state.
                            returned: always
                            type: str
        ipv6_cidr_block_association_set:
            description: An array of IPv6 cidr block association set information.
            returned: always
            type: complex
            contains:
                association_id:
                    description: The association ID.
                    returned: always
                    type: str
                ipv6_cidr_block:
                    description: The IPv6 CIDR block that is associated with the VPC.
                    returned: always
                    type: str
                ipv6_cidr_block_state:
                    description: A hash/dict that contains a single item. The state of the cidr block association.
                    returned: always
                    type: dict
                    contains:
                        state:
                            description: The CIDR block association state.
                            returned: always
                            type: str
        owner_id:
            description: The AWS account which owns the VPC.
            returned: always
            type: str
            sample: 123456789012
        dhcp_options_id:
            description: The ID of the DHCP options associated with this VPC.
            returned: always
            type: str
            sample: dopt-12345678
"""

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpcs
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def list_vpcs(connection, module: AnsibleAWSModule) -> None:
    """
    Describe VPCs.

    connection  : boto3 client connection object
    module  : AnsibleAWSModule object
    """
    # collect parameters
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    vpc_ids = module.params.get("vpc_ids")

    # init empty list for return vars
    vpc_info = list()

    # Get the basic VPC info
    try:
        vpcs = describe_vpcs(connection, VpcIds=vpc_ids, Filters=filters)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg=f"Unable to describe VPCs {vpc_ids}")

    # Loop through the results and add the other VPC attributes we gathered
    for vpc in vpcs:
        error_message = "Unable to describe VPC attribute {0} on VPC {1}"
        vpc_attributes = {}
        for attribute in ("enableDnsSupport", "enableDnsHostnames"):
            try:
                vpc_attributes[attribute] = describe_vpc_attribute(connection, vpc_id=vpc["VpcId"], attribute=attribute)
                if not vpc_attributes[attribute]:
                    module.warn(error_message.format(attribute, vpc["VpcId"]))
            except AnsibleEC2Error as e:
                module.fail_json_aws(e, msg=error_message.format(attribute, vpc))

        # add the two DNS attributes
        if vpc_attributes["enableDnsSupport"]:
            vpc["EnableDnsSupport"] = vpc_attributes["enableDnsSupport"]["EnableDnsSupport"].get("Value")
        if vpc_attributes["enableDnsHostnames"]:
            vpc["EnableDnsHostnames"] = vpc_attributes["enableDnsHostnames"]["EnableDnsHostnames"].get("Value")
        # for backwards compatibility
        vpc["id"] = vpc["VpcId"]
        vpc_info.append(camel_dict_to_snake_dict(vpc))
        # convert tag list to ansible dict
        vpc_info[-1]["tags"] = boto3_tag_list_to_ansible_dict(vpc.get("Tags", []))

    module.exit_json(vpcs=vpc_info)


def main() -> None:
    argument_spec = dict(
        vpc_ids=dict(type="list", elements="str", default=[]),
        filters=dict(type="dict", default={}),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    connection = module.client("ec2")

    list_vpcs(connection, module)


if __name__ == "__main__":
    main()

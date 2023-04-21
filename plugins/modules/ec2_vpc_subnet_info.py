#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_subnet_info
version_added: 1.0.0
short_description: Gather information about ec2 VPC subnets in AWS
description:
    - Gather information about ec2 VPC subnets in AWS
author: "Rob White (@wimnat)"
options:
  subnet_ids:
    description:
      - A list of subnet IDs to gather information for.
    aliases: ['subnet_id']
    type: list
    elements: str
    default: []
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSubnets.html) for possible filters.
    type: dict
    default: {}
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all VPC subnets
- amazon.aws.ec2_vpc_subnet_info:

# Gather information about a particular VPC subnet using ID
- amazon.aws.ec2_vpc_subnet_info:
    subnet_ids: subnet-00112233

# Gather information about any VPC subnet with a tag key Name and value Example
- amazon.aws.ec2_vpc_subnet_info:
    filters:
      "tag:Name": Example

# Gather information about any VPC subnet within VPC with ID vpc-abcdef00
- amazon.aws.ec2_vpc_subnet_info:
    filters:
      vpc-id: vpc-abcdef00

# Gather information about a set of VPC subnets, publicA, publicB and publicC within a
# VPC with ID vpc-abcdef00 and then use the jinja map function to return the
# subnet_ids as a list.

- amazon.aws.ec2_vpc_subnet_info:
    filters:
      vpc-id: vpc-abcdef00
      "tag:Name": "{{ item }}"
  loop:
    - publicA
    - publicB
    - publicC
  register: subnet_info

- set_fact:
    subnet_ids: "{{ subnet_info.results | sum(attribute='subnets', start=[]) | map(attribute='subnet_id') }}"
"""

RETURN = r"""
subnets:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        subnet_id:
            description: The ID of the Subnet.
            returned: always
            type: str
        id:
            description: The ID of the Subnet (for backwards compatibility).
            returned: always
            type: str
        vpc_id:
            description: The ID of the VPC .
            returned: always
            type: str
        state:
            description: The state of the subnet.
            returned: always
            type: str
        tags:
            description: A dict of tags associated with the Subnet.
            returned: always
            type: dict
        map_public_ip_on_launch:
            description: True/False depending on attribute setting for public IP mapping.
            returned: always
            type: bool
        default_for_az:
            description: True if this is the default subnet for AZ.
            returned: always
            type: bool
        cidr_block:
            description: The IPv4 CIDR block assigned to the subnet.
            returned: always
            type: str
        available_ip_address_count:
            description: Count of available IPs in subnet.
            returned: always
            type: str
        availability_zone:
            description: The availability zone where the subnet exists.
            returned: always
            type: str
        assign_ipv6_address_on_creation:
            description: True/False depending on attribute setting for IPv6 address assignment.
            returned: always
            type: bool
        ipv6_cidr_block_association_set:
            description: An array of IPv6 cidr block association set information.
            returned: always
            type: complex
            contains:
                association_id:
                    description: The association ID
                    returned: always
                    type: str
                ipv6_cidr_block:
                    description: The IPv6 CIDR block that is associated with the subnet.
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
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


@AWSRetry.exponential_backoff()
def describe_subnets_with_backoff(connection, subnet_ids, filters):
    """
    Describe Subnets with AWSRetry backoff throttling support.

    connection  : boto3 client connection object
    subnet_ids  : list of subnet ids for which to gather information
    filters     : additional filters to apply to request
    """
    return connection.describe_subnets(SubnetIds=subnet_ids, Filters=filters)


def describe_subnets(connection, module):
    """
    Describe Subnets.

    module  : AnsibleAWSModule object
    connection  : boto3 client connection object
    """
    # collect parameters
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    subnet_ids = module.params.get("subnet_ids")

    if subnet_ids is None:
        # Set subnet_ids to empty list if it is None
        subnet_ids = []

    # init empty list for return vars
    subnet_info = list()

    # Get the basic VPC info
    try:
        response = describe_subnets_with_backoff(connection, subnet_ids, filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe subnets")

    for subnet in response["Subnets"]:
        # for backwards compatibility
        subnet["id"] = subnet["SubnetId"]
        subnet_info.append(camel_dict_to_snake_dict(subnet))
        # convert tag list to ansible dict
        subnet_info[-1]["tags"] = boto3_tag_list_to_ansible_dict(subnet.get("Tags", []))

    module.exit_json(subnets=subnet_info)


def main():
    argument_spec = dict(
        subnet_ids=dict(type="list", elements="str", default=[], aliases=["subnet_id"]),
        filters=dict(type="dict", default={}),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2")

    describe_subnets(connection, module)


if __name__ == "__main__":
    main()

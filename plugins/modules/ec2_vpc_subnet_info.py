#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_subnet_info
version_added: 1.0.0
short_description: Gather information about EC2 VPC subnets in AWS
description:
    - Gather information about EC2 VPC subnets in AWS.
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
        id:
            description: Subnet resource id.
            returned: always
            type: str
            sample: subnet-b883b2c4
        cidr_block:
            description: The IPv4 CIDR of the Subnet.
            returned: always
            type: str
            sample: "10.0.0.0/16"
        ipv6_cidr_block:
            description: The IPv6 CIDR block actively associated with the Subnet.
            returned: always
            type: str
            sample: "2001:db8:0:102::/64"
        availability_zone:
            description: Availability zone of the Subnet.
            returned: always
            type: str
            sample: us-east-1a
        availability_zone_id:
            description: The AZ ID of the subnet.
            returned: always
            type: str
            sample: use1-az6
        state:
            description: state of the Subnet.
            returned: always
            type: str
            sample: available
        tags:
            description: tags attached to the Subnet, includes name.
            returned: always
            type: dict
            sample: {"Name": "My Subnet", "env": "staging"}
        map_public_ip_on_launch:
            description: whether public IP is auto-assigned to new instances.
            returned: always
            type: bool
            sample: false
        assign_ipv6_address_on_creation:
            description: whether IPv6 address is auto-assigned to new instances.
            returned: always
            type: bool
            sample: false
        vpc_id:
            description: the id of the VPC where this Subnet exists.
            returned: always
            type: str
            sample: vpc-67236184
        available_ip_address_count:
            description: number of available IPv4 addresses.
            returned: always
            type: str
            sample: 251
        default_for_az:
            description: indicates whether this is the default Subnet for this Availability Zone.
            returned: always
            type: bool
            sample: false
        enable_dns64:
            description:
            - Indicates whether DNS queries made should return synthetic IPv6 addresses for IPv4-only destinations.
            type: bool
            sample: false
        ipv6_association_id:
            description: The IPv6 association ID for the currently associated CIDR.
            returned: always
            type: str
            sample: subnet-cidr-assoc-b85c74d2
        ipv6_native:
            description: Indicates whether this is an IPv6 only subnet.
            type: bool
            sample: false
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
        map_customer_owned_ip_on_launch:
            description:
            - Indicates whether a network interface receives a customer-owned IPv4 address.
            type: bool
            sample: flase
        owner_id:
            description: The ID of the Amazon Web Services account that owns the subnet.
            type: str
            sample: 12344567
        private_dns_name_options_on_launch:
            description:
            - The type of hostnames to assign to instances in the subnet at launch.
            - An instance hostname is based on the IPv4 address or ID of the instance.
            type: dict
            sample: {
                "enable_resource_name_dns_a_record": false,
                "enable_resource_name_dns_aaaa_record": false,
                "hostname_type": "ip-name"
            }
        subnet_arn:
            description: The Amazon Resource Name (ARN) of the subnet.
            type: str
            sample: arn:aws:ec2:us-east-1:xxx:subnet/subnet-xxx
        subnet_id:
            description: The ID of the Subnet.
            returned: always
            type: str
"""

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_subnets
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def _describe_subnets(connection, module: AnsibleAWSModule) -> None:
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
    subnets = describe_subnets(connection, SubnetIds=subnet_ids, Filters=filters)

    for subnet in subnets:
        # for backwards compatibility
        subnet["id"] = subnet["SubnetId"]
        subnet_info.append(camel_dict_to_snake_dict(subnet))
        # convert tag list to ansible dict
        subnet_info[-1]["tags"] = boto3_tag_list_to_ansible_dict(subnet.get("Tags", []))

    module.exit_json(subnets=subnet_info)


def main() -> None:
    argument_spec = dict(
        subnet_ids=dict(type="list", elements="str", default=[], aliases=["subnet_id"]),
        filters=dict(type="dict", default={}),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2")

    _describe_subnets(connection, module)


if __name__ == "__main__":
    main()

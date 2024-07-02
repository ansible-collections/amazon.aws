#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_eni_info
version_added: 1.0.0
short_description: Gather information about EC2 ENI interfaces in AWS
description:
  - Gather information about EC2 ENI interfaces in AWS.
author:
  - "Rob White (@wimnat)"
options:
  eni_id:
    description:
      - The ID of the ENI.
      - This option is mutually exclusive of O(filters).
    type: str
    version_added: 1.3.0
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkInterfaces.html) for possible filters.
      - This option is mutually exclusive of O(eni_id).
    type: dict
    default: {}
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all ENIs
- amazon.aws.ec2_eni_info:

# Gather information about a particular ENI
- amazon.aws.ec2_eni_info:
    filters:
      network-interface-id: eni-xxxxxxx
"""

RETURN = r"""
network_interfaces:
  description: List of matching elastic network interfaces.
  returned: always
  type: complex
  contains:
    association:
      description: Info of associated elastic IP (EIP).
      returned: When an ENI is associated with an EIP
      type: dict
      sample: {
          allocation_id: "eipalloc-5sdf123",
          association_id: "eipassoc-8sdf123",
          ip_owner_id: "123456789012",
          public_dns_name: "ec2-52-1-0-63.compute-1.amazonaws.com",
          public_ip: "52.1.0.63"
        }
    attachment:
      description: Info about attached ec2 instance.
      returned: When an ENI is attached to an ec2 instance
      type: dict
      sample: {
        attach_time: "2017-08-05T15:25:47+00:00",
        attachment_id: "eni-attach-149d21234",
        delete_on_termination: false,
        device_index: 1,
        instance_id: "i-15b8d3cadbafa1234",
        instance_owner_id: "123456789012",
        "network_card_index": 0,
        status: "attached"
      }
    availability_zone:
      description: Availability zone of ENI.
      returned: always
      type: str
      sample: "us-east-1b"
    description:
      description: Description text for ENI.
      returned: always
      type: str
      sample: "My favourite network interface"
    groups:
      description: List of attached security groups.
      returned: always
      type: list
      sample: [
        {
          group_id: "sg-26d0f1234",
          group_name: "my_ec2_security_group"
        }
      ]
    id:
      description: The id of the ENI (alias for RV(network_interfaces.network_interface_id)).
      returned: always
      type: str
      sample: "eni-392fsdf"
    interface_type:
      description: Type of the network interface.
      returned: always
      type: str
      sample: "interface"
    ipv6_addresses:
      description: List of IPv6 addresses for this interface.
      returned: always
      type: list
      sample: []
    mac_address:
      description: MAC address of the network interface.
      returned: always
      type: str
      sample: "0a:f8:10:2f:ab:a1"
    name:
      description: The Name tag of the ENI, often displayed in the AWS UIs as Name.
      returned: When a Name tag has been set
      type: str
      version_added: 1.3.0
    network_interface_id:
      description: The id of the ENI.
      returned: always
      type: str
      sample: "eni-392fsdf"
    owner_id:
      description: AWS account id of the owner of the ENI.
      returned: always
      type: str
      sample: "123456789012"
    private_dns_name:
      description: Private DNS name for the ENI.
      returned: always
      type: str
      sample: "ip-172-16-1-180.ec2.internal"
    private_ip_address:
      description: Private IP address for the ENI.
      returned: always
      type: str
      sample: "172.16.1.180"
    private_ip_addresses:
      description: List of private IP addresses attached to the ENI.
      returned: always
      type: list
      sample: []
    requester_id:
      description: The ID of the entity that launched the ENI.
      type: str
      sample: "AIDA12345EXAMPLE54321"
    requester_managed:
      description:  Indicates whether the network interface is being managed by an AWS service.
      returned: always
      type: bool
      sample: false
    source_dest_check:
      description: Indicates whether the network interface performs source/destination checking.
      returned: always
      type: bool
      sample: false
    status:
      description: Indicates if the network interface is attached to an instance or not.
      returned: always
      type: str
      sample: "in-use"
    subnet_id:
      description: Subnet ID the ENI is in.
      returned: always
      type: str
      sample: "subnet-7bbf01234"
    tags:
      description: Dictionary of tags added to the ENI.
      returned: always
      type: dict
      sample: {}
      version_added: 1.3.0
    tag_set:
      description: Dictionary of tags added to the ENI.
      returned: always
      type: dict
      sample: {}
    vpc_id:
      description: ID of the VPC the network interface it part of.
      returned: always
      type: str
      sample: "vpc-b3f1f123"
"""

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_network_interfaces
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def build_request_args(eni_id, filters):
    request_args = {
        "NetworkInterfaceIds": [eni_id] if eni_id else [],
        "Filters": ansible_dict_to_boto3_filter_list(filters),
    }

    request_args = {k: v for k, v in request_args.items() if v}

    return request_args


def get_network_interfaces(connection, module: AnsibleAWSModule, request_args: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        network_interfaces_result = describe_network_interfaces(connection, **request_args)
        if not network_interfaces_result:
            module.exit_json(network_interfaces=[])
    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    return network_interfaces_result


def list_eni(connection, module: AnsibleAWSModule, request_args: Dict[str, Any]) -> List[Dict[str, Any]]:
    network_interfaces_result = get_network_interfaces(connection, module, request_args)

    # Modify boto3 tags list to be ansible friendly dict and then camel_case
    camel_network_interfaces = []
    for network_interface in network_interfaces_result:
        network_interface["TagSet"] = boto3_tag_list_to_ansible_dict(network_interface["TagSet"])
        network_interface["Tags"] = network_interface["TagSet"]
        if "Name" in network_interface["Tags"]:
            network_interface["Name"] = network_interface["Tags"]["Name"]
        # Added id to interface info to be compatible with return values of ec2_eni module:
        network_interface["Id"] = network_interface["NetworkInterfaceId"]
        camel_network_interfaces.append(camel_dict_to_snake_dict(network_interface, ignore_list=["Tags", "TagSet"]))

    return camel_network_interfaces


def main():
    argument_spec = dict(
        eni_id=dict(type="str"),
        filters=dict(default={}, type="dict"),
    )
    mutually_exclusive = [
        ["eni_id", "filters"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
    )

    connection = module.client("ec2")

    request_args = build_request_args(
        eni_id=module.params["eni_id"],
        filters=module.params["filters"],
    )

    result = list_eni(connection, module, request_args)

    module.exit_json(network_interfaces=result)


if __name__ == "__main__":
    main()

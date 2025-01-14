#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_nacl_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: Gather information about Network ACLs in an AWS VPC
description:
  - Gather information about Network ACLs in an AWS VPC.
author:
  - "Brad Davidson (@brandond)"
options:
  nacl_ids:
    description:
      - A list of Network ACL IDs to retrieve information about.
    required: false
    default: []
    aliases: [nacl_id]
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkAcls.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    default: {}
    type: dict
notes:
  - By default, the module will return all Network ACLs.

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all Network ACLs:
- name: Get All NACLs
  amazon.aws.ec2_vpc_nacl_info:
    region: us-west-2
  register: all_nacls

# Retrieve default Network ACLs:
- name: Get Default NACLs
  amazon.aws.ec2_vpc_nacl_info:
    region: us-west-2
    filters:
      'default': 'true'
  register: default_nacls
"""

RETURN = r"""
nacls:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        nacl_id:
            description: The ID of the Network Access Control List.
            returned: always
            type: str
        vpc_id:
            description: The ID of the VPC that the NACL is attached to.
            returned: always
            type: str
        is_default:
            description: True if the NACL is the default for its VPC.
            returned: always
            type: bool
        tags:
            description: A dict of tags associated with the NACL.
            returned: always
            type: dict
        subnets:
            description: A list of subnet IDs that are associated with the NACL.
            returned: always
            type: list
            elements: str
        ingress:
            description:
              - A list of NACL ingress rules.
              - The rule format is C([rule no, protocol, allow/deny, v4 or v6 cidr, icmp_type, icmp_code, port from, port to]).
            returned: always
            type: list
            elements: list
            sample: [[100, 'tcp', 'allow', '0.0.0.0/0', null, null, 22, 22]]
        egress:
            description:
              - A list of NACL egress rules.
              - The rule format is C([rule no, protocol, allow/deny, v4 or v6 cidr, icmp_type, icmp_code, port from, port to]).
            returned: always
            type: list
            elements: list
            sample: [[100, 'all', 'allow', '0.0.0.0/0', null, null, null, null]]
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_network_acls
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list

# VPC-supported IANA protocol numbers
# http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_NAMES = {"-1": "all", "1": "icmp", "6": "tcp", "17": "udp"}


def format_nacl(nacl: Dict[str, Any]) -> Dict[str, Any]:
    # Turn the boto3 result into ansible friendly snake cases
    nacl = camel_dict_to_snake_dict(nacl)

    # convert boto3 tags list into ansible dict
    if "tags" in nacl:
        nacl["tags"] = boto3_tag_list_to_ansible_dict(nacl["tags"], "key", "value")

    # Convert NACL entries
    if "entries" in nacl:
        nacl["egress"] = [
            nacl_entry_to_list(entry) for entry in nacl["entries"] if entry["rule_number"] < 32767 and entry["egress"]
        ]
        nacl["ingress"] = [
            nacl_entry_to_list(entry)
            for entry in nacl["entries"]
            if entry["rule_number"] < 32767 and not entry["egress"]
        ]
        del nacl["entries"]

    # Read subnets from NACL Associations
    if "associations" in nacl:
        nacl["subnets"] = [a["subnet_id"] for a in nacl["associations"]]
        del nacl["associations"]

    # Read Network ACL id
    if "network_acl_id" in nacl:
        nacl["nacl_id"] = nacl["network_acl_id"]
        del nacl["network_acl_id"]

    return nacl


def list_ec2_vpc_nacls(connection, module: AnsibleAWSModule) -> None:
    nacl_ids = module.params.get("nacl_ids")
    filters = module.params.get("filters")

    params = {}
    if filters:
        params["Filters"] = ansible_dict_to_boto3_filter_list(filters)
    if nacl_ids:
        params["NetworkAclIds"] = nacl_ids

    try:
        network_acls = describe_network_acls(connection, **params)
        if nacl_ids and not len(nacl_ids) == len(network_acls):
            if len(nacl_ids) == 1:
                module.fail_json(msg="Unable to describe ACL. NetworkAcl does not exist.")
            else:
                module.fail_json(msg="Unable to describe all ACLs. One or more NetworkAcls does not exist.")
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    module.exit_json(nacls=[format_nacl(nacl) for nacl in network_acls])


def nacl_entry_to_list(entry: Dict[str, Any]) -> List[Union[str, int, None]]:
    # entry list format
    # [ rule_num, protocol name or number, allow or deny, ipv4/6 cidr, icmp type, icmp code, port from, port to]
    elist = []

    elist.append(entry["rule_number"])

    if entry.get("protocol") in PROTOCOL_NAMES:
        elist.append(PROTOCOL_NAMES[entry["protocol"]])
    else:
        elist.append(entry.get("protocol"))

    elist.append(entry["rule_action"])

    if entry.get("cidr_block"):
        elist.append(entry["cidr_block"])
    elif entry.get("ipv6_cidr_block"):
        elist.append(entry["ipv6_cidr_block"])
    else:
        elist.append(None)

    elist = elist + [None, None, None, None]

    if entry["protocol"] in ("1", "58"):
        elist[4] = entry.get("icmp_type_code", {}).get("type")
        elist[5] = entry.get("icmp_type_code", {}).get("code")

    if entry["protocol"] not in ("1", "6", "17", "58"):
        elist[6] = 0
        elist[7] = 65535
    elif "port_range" in entry:
        elist[6] = entry["port_range"]["from"]
        elist[7] = entry["port_range"]["to"]

    return elist


def main():
    argument_spec = dict(
        nacl_ids=dict(default=[], type="list", aliases=["nacl_id"], elements="str"),
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    connection = module.client("ec2")

    list_ec2_vpc_nacls(connection, module)


if __name__ == "__main__":
    main()

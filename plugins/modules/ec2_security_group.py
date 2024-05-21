#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_security_group
version_added: 1.0.0
author:
  - "Andrew de Quincey (@adq)"
  - "Razique Mahroua (@Razique)"
short_description: Maintain an EC2 security group
description:
  - Maintains EC2 security groups.
options:
  name:
    description:
      - Name of the security group.
      - One of and only one of I(name) or I(group_id) is required.
      - Required if I(state=present).
    required: false
    type: str
  group_id:
    description:
      - Id of group to delete (works only with absent).
      - One of and only one of I(name) or I(group_id) is required.
    required: false
    type: str
  description:
    description:
      - Description of the security group.
      - Required when I(state) is C(present).
    required: false
    type: str
  vpc_id:
    description:
      - ID of the VPC to create the group in.
    required: false
    type: str
  rules:
    description:
      - List of firewall inbound rules to enforce in this group (see example). If none are supplied,
        no inbound rules will be enabled. Rules list may include its own name in I(group_name).
        This allows idempotent loopback additions (e.g. allow group to access itself).
    required: false
    type: list
    elements: dict
    suboptions:
        cidr_ip:
          type: list
          elements: raw
          description:
            - The IPv4 CIDR range traffic is coming from.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
            - Support for passing nested lists of strings to I(cidr_ip) has been deprecated and will
              be removed in a release after 2024-12-01.
        cidr_ipv6:
          type: list
          elements: raw
          description:
            - The IPv6 CIDR range traffic is coming from.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
            - Support for passing nested lists of strings to I(cidr_ipv6) has been deprecated and will
              be removed in a release after 2024-12-01.
        ip_prefix:
          type: list
          elements: str
          description:
            - The IP Prefix U(https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-prefix-lists.html)
              that traffic is coming from.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
        group_id:
          type: list
          elements: str
          description:
            - The ID of the Security Group that traffic is coming from.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
        group_name:
          type: list
          elements: str
          description:
            - Name of the Security Group that traffic is coming from.
            - If the Security Group doesn't exist a new Security Group will be
              created with I(group_desc) as the description.
            - I(group_name) can accept values of type str and list.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
        group_desc:
          type: str
          description:
            - If the I(group_name) is set and the Security Group doesn't exist a new Security Group will be
              created with I(group_desc) as the description.
        proto:
          type: str
          description:
            - The IP protocol name (C(tcp), C(udp), C(icmp), C(icmpv6)) or
              number (U(https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers)).
          default: 'tcp'
        from_port:
          type: int
          description:
            - The start of the range of ports that traffic is going to.
            - A value can be between C(0) to C(65535).
            - When I(proto=icmp) a value of C(-1) indicates all ports.
            - Mutually exclusive with I(icmp_code), I(icmp_type) and I(ports).
        to_port:
          type: int
          description:
            - The end of the range of ports that traffic is going to.
            - A value can be between C(0) to C(65535).
            - When I(proto=icmp) a value of C(-1) indicates all ports.
            - Mutually exclusive with I(icmp_code), I(icmp_type) and I(ports).
        ports:
          type: list
          elements: str
          description:
            - A list of ports that traffic is going to.
            - Elements of the list can be a single port (for example C(8080)), or a range of ports
              specified as C(<START>-<END>), (for example C(1011-1023)).
            - Mutually exclusive with I(icmp_code), I(icmp_type), I(from_port) and I(to_port).
        icmp_type:
          version_added: 3.3.0
          type: int
          description:
            - The ICMP type of the packet.
            - A value of C(-1) indicates all ICMP types.
            - Requires I(proto=icmp) or I(proto=icmpv6).
            - Mutually exclusive with I(ports), I(from_port) and I(to_port).
        icmp_code:
          version_added: 3.3.0
          type: int
          description:
            - The ICMP code of the packet.
            - A value of C(-1) indicates all ICMP codes.
            - Requires I(proto=icmp) or I(proto=icmpv6).
            - Mutually exclusive with I(ports), I(from_port) and I(to_port).
        rule_desc:
          type: str
          description: A description for the rule.

  rules_egress:
    description:
      - List of firewall outbound rules to enforce in this group (see example). If none are supplied,
        a default all-out rule is assumed. If an empty list is supplied, no outbound rules will be enabled.
    required: false
    type: list
    elements: dict
    aliases: ['egress_rules']
    suboptions:
        cidr_ip:
          type: list
          elements: raw
          description:
            - The IPv4 CIDR range traffic is going to.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
            - Support for passing nested lists of strings to I(cidr_ip) has been deprecated and will
              be removed in a release after 2024-12-01.
        cidr_ipv6:
          type: list
          elements: raw
          description:
            - The IPv6 CIDR range traffic is going to.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
            - Support for passing nested lists of strings to I(cidr_ipv6) has been deprecated and will
              be removed in a release after 2024-12-01.
        ip_prefix:
          type: list
          elements: str
          description:
            - The IP Prefix U(https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-prefix-lists.html)
              that traffic is going to.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
        group_id:
          type: list
          elements: str
          description:
            - The ID of the Security Group that traffic is going to.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
        group_name:
          type: list
          elements: str
          description:
            - Name of the Security Group that traffic is going to.
            - If the Security Group doesn't exist a new Security Group will be
              created with I(group_desc) as the description.
            - You can specify only one of I(cidr_ip), I(cidr_ipv6), I(ip_prefix), I(group_id)
              and I(group_name).
        group_desc:
          type: str
          description:
            - If the I(group_name) is set and the Security Group doesn't exist a new Security Group will be
              created with I(group_desc) as the description.
        proto:
          type: str
          description:
            - The IP protocol name (C(tcp), C(udp), C(icmp), C(icmpv6)) or
              number (U(https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers)).
          default: 'tcp'
        from_port:
          type: int
          description:
            - The start of the range of ports that traffic is going to.
            - A value can be between C(0) to C(65535).
            - When I(proto=icmp) a value of C(-1) indicates all ports.
            - Mutually exclusive with I(icmp_code), I(icmp_type) and I(ports).
        to_port:
          type: int
          description:
            - The end of the range of ports that traffic is going to.
            - A value can be between C(0) to C(65535).
            - When I(proto=icmp) a value of C(-1) indicates all ports.
            - Mutually exclusive with I(icmp_code), I(icmp_type) and I(ports).
        ports:
          type: list
          elements: str
          description:
            - A list of ports that traffic is going to.
            - Elements of the list can be a single port (for example C(8080)), or a range of ports
              specified as C(<START>-<END>), (for example C(1011-1023)).
            - Mutually exclusive with I(icmp_code), I(icmp_type), I(from_port) and I(to_port).
        icmp_type:
          version_added: 3.3.0
          type: int
          description:
            - The ICMP type of the packet.
            - A value of C(-1) indicates all ICMP types.
            - Requires I(proto=icmp) or I(proto=icmpv6).
            - Mutually exclusive with I(ports), I(from_port) and I(to_port).
        icmp_code:
          version_added: 3.3.0
          type: int
          description:
            - The ICMP code of the packet.
            - A value of C(-1) indicates all ICMP codes.
            - Requires I(proto=icmp) or I(proto=icmpv6).
            - Mutually exclusive with I(ports), I(from_port) and I(to_port).
        rule_desc:
            type: str
            description: A description for the rule.
  state:
    description:
      - Create or delete a security group.
    required: false
    default: 'present'
    choices: [ "present", "absent" ]
    aliases: []
    type: str
  purge_rules:
    description:
      - Purge existing rules on security group that are not found in rules.
    required: false
    default: 'true'
    aliases: []
    type: bool
  purge_rules_egress:
    description:
      - Purge existing rules_egress on security group that are not found in rules_egress.
    required: false
    default: 'true'
    aliases: ['purge_egress_rules']
    type: bool

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3

notes:
  - If a rule declares a group_name and that group doesn't exist, it will be
    automatically created. In that case, group_desc should be provided as well.
    The module will refuse to create a depended-on group without a description.
  - Prior to release 5.0.0 this module was called C(amazon.aws.ec2_group_info).  The usage did not
    change.
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: example using security group rule descriptions
  amazon.aws.ec2_security_group:
    name: "{{ name }}"
    description: sg with rule descriptions
    vpc_id: vpc-xxxxxxxx
    rules:
      - proto: tcp
        ports:
          - 80
        cidr_ip: 0.0.0.0/0
        rule_desc: allow all on port 80

- name: example using ICMP types and codes
  amazon.aws.ec2_security_group:
    name: "{{ name }}"
    description: sg for ICMP
    vpc_id: vpc-xxxxxxxx
    rules:
      - proto: icmp
        icmp_type: 3
        icmp_code: 1
        cidr_ip: 0.0.0.0/0

- name: example ec2 group
  amazon.aws.ec2_security_group:
    name: example
    description: an example EC2 group
    vpc_id: 12345
    rules:
      - proto: tcp
        from_port: 80
        to_port: 80
        cidr_ip: 0.0.0.0/0
      - proto: tcp
        from_port: 22
        to_port: 22
        cidr_ip: 10.0.0.0/8
      - proto: tcp
        from_port: 443
        to_port: 443
        # this should only be needed for EC2 Classic security group rules
        # because in a VPC an ELB will use a user-account security group
        group_id: amazon-elb/sg-87654321/amazon-elb-sg
      - proto: tcp
        from_port: 3306
        to_port: 3306
        group_id: 123456789012/sg-87654321/exact-name-of-sg
      - proto: udp
        from_port: 10050
        to_port: 10050
        cidr_ip: 10.0.0.0/8
      - proto: udp
        from_port: 10051
        to_port: 10051
        group_id: sg-12345678
      - proto: icmp
        from_port: 8 # icmp type, -1 = any type
        to_port: -1 # icmp subtype, -1 = any subtype
        cidr_ip: 10.0.0.0/8
      - proto: all
        # the containing group name may be specified here
        group_name: example
      - proto: all
        # in the 'proto' attribute, if you specify -1 (only supported when I(proto=icmp)), all, or a protocol number
        # other than tcp, udp, icmp, or 58 (ICMPv6), traffic on all ports is allowed, regardless of any ports that
        # you specify.
        from_port: 10050 # this value is ignored
        to_port: 10050   # this value is ignored
        cidr_ip: 10.0.0.0/8

    rules_egress:
      - proto: tcp
        from_port: 80
        to_port: 80
        cidr_ip: 0.0.0.0/0
        cidr_ipv6: 64:ff9b::/96
        group_name: example-other
        # description to use if example-other needs to be created
        group_desc: other example EC2 group

- name: example2 ec2 group
  amazon.aws.ec2_security_group:
    name: example2
    description: an example2 EC2 group
    vpc_id: 12345
    rules:
      # 'ports' rule keyword was introduced in version 2.4. It accepts a single
      # port value or a list of values including ranges (from_port-to_port).
      - proto: tcp
        ports: 22
        group_name: example-vpn
      - proto: tcp
        ports:
          - 80
          - 443
          - 8080-8099
        cidr_ip: 0.0.0.0/0
      # Rule sources list support was added in version 2.4. This allows to
      # define multiple sources per source type as well as multiple source types per rule.
      - proto: tcp
        ports:
          - 6379
          - 26379
        group_name:
          - example-vpn
          - example-redis
      - proto: tcp
        ports: 5665
        group_name: example-vpn
        cidr_ip:
          - 172.16.1.0/24
          - 172.16.17.0/24
        cidr_ipv6:
          - 2607:F8B0::/32
          - 64:ff9b::/96
        group_id:
          - sg-edcd9784
  diff: true

- name: "Delete group by its id"
  amazon.aws.ec2_security_group:
    group_id: sg-33b4ee5b
    state: absent
"""

RETURN = r"""
description:
  description: Description of security group
  sample: My Security Group
  type: str
  returned: on create/update
group_id:
  description: Security group id
  sample: sg-abcd1234
  type: str
  returned: on create/update
group_name:
  description: Security group name
  sample: My Security Group
  type: str
  returned: on create/update
ip_permissions:
    description: The inbound rules associated with the security group.
    returned: always
    type: list
    elements: dict
    contains:
        from_port:
            description: If the protocol is TCP or UDP, this is the start of the port range.
            type: int
            sample: 80
        ip_protocol:
            description: The IP protocol name or number.
            returned: always
            type: str
        ip_ranges:
            description: The IPv4 ranges.
            returned: always
            type: list
            elements: dict
            contains:
                cidr_ip:
                    description: The IPv4 CIDR range.
                    returned: always
                    type: str
        ipv6_ranges:
            description: The IPv6 ranges.
            returned: always
            type: list
            elements: dict
            contains:
                cidr_ipv6:
                    description: The IPv6 CIDR range.
                    returned: always
                    type: str
        prefix_list_ids:
            description: The prefix list IDs.
            returned: always
            type: list
            elements: dict
            contains:
                prefix_list_id:
                    description: The ID of the prefix.
                    returned: always
                    type: str
        to_group:
            description: If the protocol is TCP or UDP, this is the end of the port range.
            type: int
            sample: 80
        user_id_group_pairs:
            description: The security group and AWS account ID pairs.
            returned: always
            type: list
            elements: dict
            contains:
                group_id:
                    description: The security group ID of the pair.
                    returned: always
                    type: str
                user_id:
                    description: The user ID of the pair.
                    returned: always
                    type: str
ip_permissions_egress:
    description: The outbound rules associated with the security group.
    returned: always
    type: list
    elements: dict
    contains:
        ip_protocol:
            description: The IP protocol name or number.
            returned: always
            type: str
        ip_ranges:
            description: The IPv4 ranges.
            returned: always
            type: list
            elements: dict
            contains:
                cidr_ip:
                    description: The IPv4 CIDR range.
                    returned: always
                    type: str
        ipv6_ranges:
            description: The IPv6 ranges.
            returned: always
            type: list
            elements: dict
            contains:
                cidr_ipv6:
                    description: The IPv6 CIDR range.
                    returned: always
                    type: str
        prefix_list_ids:
            description: The prefix list IDs.
            returned: always
            type: list
            elements: dict
            contains:
                prefix_list_id:
                    description: The ID of the prefix.
                    returned: always
                    type: str
        user_id_group_pairs:
            description: The security group and AWS account ID pairs.
            returned: always
            type: list
            elements: dict
            contains:
                group_id:
                    description: The security group ID of the pair.
                    returned: always
                    type: str
                user_id:
                    description: The user ID of the pair.
                    returned: always
                    type: str
owner_id:
  description: AWS Account ID of the security group
  sample: 123456789012
  type: int
  returned: on create/update
tags:
  description: Tags associated with the security group
  sample:
    Name: My Security Group
    Purpose: protecting stuff
  type: dict
  returned: on create/update
vpc_id:
  description: ID of VPC to which the security group belongs
  sample: vpc-abcd1234
  type: str
  returned: on create/update
"""

import itertools
import json
import re
from collections import namedtuple
from copy import deepcopy
from ipaddress import ip_network
from time import sleep

try:
    import botocore
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.network import to_ipv6_subnet
from ansible.module_utils.common.network import to_subnet
from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_aws_account_id
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter

Rule = namedtuple("Rule", ["port_range", "protocol", "target", "target_type", "description"])
TARGET_TYPES_ALL = {"ipv4", "ipv6", "group", "ip_prefix"}
SOURCE_TYPES_ALL = {"cidr_ip", "cidr_ipv6", "group_id", "group_name", "ip_prefix"}
PORT_TYPES_ALL = {"from_port", "to_port", "ports", "icmp_type", "icmp_code"}
current_account_id = None


class SecurityGroupError(Exception):
    def __init__(self, msg, e=None, **kwargs):
        super().__init__(msg)
        self.message = msg
        self.exception = e
        self.kwargs = kwargs

    # Simple helper to perform the module.fail_... call once we have module available to us
    def fail(self, module):
        if self.exception:
            module.fail_json_aws(self.exception, msg=self.message, **self.kwargs)
        module.fail_json(msg=self.message, **self.kwargs)


def rule_cmp(a, b):
    """Compare rules without descriptions"""
    for prop in ["port_range", "protocol", "target", "target_type"]:
        if prop == "port_range" and to_text(a.protocol) == to_text(b.protocol):
            # equal protocols can interchange `(-1, -1)` and `(None, None)`
            if a.port_range in ((None, None), (-1, -1)) and b.port_range in ((None, None), (-1, -1)):
                continue
            if getattr(a, prop) != getattr(b, prop):
                return False
        elif getattr(a, prop) != getattr(b, prop):
            return False
    return True


def rules_to_permissions(rules):
    return [to_permission(rule) for rule in rules]


def to_permission(rule):
    # take a Rule, output the serialized grant
    perm = {
        "IpProtocol": rule.protocol,
    }
    perm["FromPort"], perm["ToPort"] = rule.port_range
    if rule.target_type == "ipv4":
        perm["IpRanges"] = [
            {
                "CidrIp": rule.target,
            }
        ]
        if rule.description:
            perm["IpRanges"][0]["Description"] = rule.description
    elif rule.target_type == "ipv6":
        perm["Ipv6Ranges"] = [
            {
                "CidrIpv6": rule.target,
            }
        ]
        if rule.description:
            perm["Ipv6Ranges"][0]["Description"] = rule.description
    elif rule.target_type == "group":
        if isinstance(rule.target, tuple):
            pair = {}
            if rule.target[0]:
                pair["UserId"] = rule.target[0]
            # group_id/group_name are mutually exclusive - give group_id more precedence as it is more specific
            if rule.target[1]:
                pair["GroupId"] = rule.target[1]
            elif rule.target[2]:
                pair["GroupName"] = rule.target[2]
            perm["UserIdGroupPairs"] = [pair]
        else:
            perm["UserIdGroupPairs"] = [{"GroupId": rule.target}]
        if rule.description:
            perm["UserIdGroupPairs"][0]["Description"] = rule.description
    elif rule.target_type == "ip_prefix":
        perm["PrefixListIds"] = [
            {
                "PrefixListId": rule.target,
            }
        ]
        if rule.description:
            perm["PrefixListIds"][0]["Description"] = rule.description
    elif rule.target_type not in TARGET_TYPES_ALL:
        raise ValueError(f"Invalid target type for rule {rule}")
    return fix_port_and_protocol(perm)


def rule_from_group_permission(perm):
    """
    Returns a rule dict from an existing security group.

    When using a security group as a target all 3 fields (OwnerId, GroupId, and
    GroupName) need to exist in the target. This ensures consistency of the
    values that will be compared to desired_ingress or desired_egress
    in wait_for_rule_propagation().
    GroupId is preferred as it is more specific except when targeting 'amazon-'
    prefixed security groups (such as EC2 Classic ELBs).
    """

    def ports_from_permission(p):
        if "FromPort" not in p and "ToPort" not in p:
            return (None, None)
        return (int(perm["FromPort"]), int(perm["ToPort"]))

    # outputs a rule tuple
    for target_key, target_subkey, target_type in [
        ("IpRanges", "CidrIp", "ipv4"),
        ("Ipv6Ranges", "CidrIpv6", "ipv6"),
        ("PrefixListIds", "PrefixListId", "ip_prefix"),
    ]:
        if target_key not in perm:
            continue
        for r in perm[target_key]:
            # there may be several IP ranges here, which is ok
            yield Rule(
                ports_from_permission(perm),
                to_text(perm["IpProtocol"]),
                r[target_subkey],
                target_type,
                r.get("Description"),
            )
    if "UserIdGroupPairs" in perm and perm["UserIdGroupPairs"]:
        for pair in perm["UserIdGroupPairs"]:
            target = (
                pair.get("UserId", current_account_id),
                pair.get("GroupId", None),
                None,
            )
            if pair.get("UserId", "").startswith("amazon-"):
                # amazon-elb and amazon-prefix rules don't need
                # group-id specified, so remove it when querying
                # from permission
                target = (
                    pair.get("UserId", None),
                    None,
                    pair.get("GroupName", None),
                )
            elif "VpcPeeringConnectionId" not in pair and pair["UserId"] != current_account_id:
                # EC2-Classic cross-account
                pass
            elif "VpcPeeringConnectionId" in pair:
                # EC2-VPC cross-account VPC peering
                target = (
                    pair.get("UserId", None),
                    pair.get("GroupId", None),
                    None,
                )

            yield Rule(
                ports_from_permission(perm), to_text(perm["IpProtocol"]), target, "group", pair.get("Description")
            )


# Wrap just this method so we can retry on missing groups
@AWSRetry.jittered_backoff(retries=5, delay=5, catch_extra_error_codes=["InvalidGroup.NotFound"])
def get_security_groups_with_backoff(client, **kwargs):
    return client.describe_security_groups(**kwargs)


def sg_exists_with_backoff(client, **kwargs):
    try:
        return client.describe_security_groups(aws_retry=True, **kwargs)
    except is_boto3_error_code("InvalidGroup.NotFound"):
        return {"SecurityGroups": []}


def deduplicate_rules_args(rules):
    """Returns unique rules"""
    if rules is None:
        return None
    return list(dict(zip((json.dumps(r, sort_keys=True) for r in rules), rules)).values())


def validate_rule(rule):
    icmp_type = rule.get("icmp_type", None)
    icmp_code = rule.get("icmp_code", None)
    proto = rule["proto"]
    if (icmp_type is not None or icmp_code is not None) and ("icmp" not in proto):
        raise SecurityGroupError(msg="Specify proto: icmp or icmpv6 when using icmp_type/icmp_code")


def _target_from_rule_with_group_id(rule, groups):
    owner_id = current_account_id
    FOREIGN_SECURITY_GROUP_REGEX = r"^([^/]+)/?(sg-\S+)?/(\S+)"
    foreign_rule = re.match(FOREIGN_SECURITY_GROUP_REGEX, rule["group_id"])

    if not foreign_rule:
        return "group", (owner_id, rule["group_id"], None), False

    # this is a foreign Security Group. Since you can't fetch it you must create an instance of it
    # Matches on groups like amazon-elb/sg-5a9c116a/amazon-elb-sg, amazon-elb/amazon-elb-sg,
    # and peer-VPC groups like 0987654321/sg-1234567890/example
    owner_id, group_id, group_name = foreign_rule.groups()
    group_instance = dict(UserId=owner_id, GroupId=group_id, GroupName=group_name)
    groups[group_id] = group_instance
    groups[group_name] = group_instance
    if group_id and group_name:
        if group_name.startswith("amazon-"):
            # amazon-elb and amazon-prefix rules don't need group_id specified,
            group_id = None
        else:
            # For cross-VPC references we'll use group_id as it is more specific
            group_name = None
    return "group", (owner_id, group_id, group_name), False


def _lookup_target_or_fail(client, group_name, vpc_id, groups, msg):
    owner_id = current_account_id
    filters = {"group-name": group_name}
    if vpc_id:
        filters["vpc-id"] = vpc_id

    filters = ansible_dict_to_boto3_filter_list(filters)
    try:
        found_group = get_security_groups_with_backoff(client, Filters=filters).get("SecurityGroups", [])[0]
    except (is_boto3_error_code("InvalidGroup.NotFound"), IndexError):
        raise SecurityGroupError(msg=msg)
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        raise SecurityGroupError(msg="Failed to get security group", e=e)

    group_id = found_group["GroupId"]
    groups[group_id] = found_group
    groups[group_name] = found_group
    return "group", (owner_id, group_id, None), False


def _create_target_from_rule(client, rule, groups, vpc_id, tags, check_mode):
    owner_id = current_account_id
    # We can't create a group in check mode...
    if check_mode:
        return "group", (owner_id, None, None), True

    group_name = rule["group_name"]

    try:
        created_group = _create_security_group_with_wait(client, group_name, rule["group_desc"], vpc_id, tags)
    except is_boto3_error_code("InvalidGroup.Duplicate"):
        # The group exists, but didn't show up in any of our previous describe-security-groups calls
        # Try searching on a filter for the name, and allow a retry window for AWS to update
        # the model on their end.
        fail_msg = (
            f"Could not create or use existing group '{group_name}' in rule {rule}.  "
            "Make sure the group exists and try using the group_id "
            "instead of the name"
        )
        return _lookup_target_or_fail(client, group_name, vpc_id, groups, fail_msg)
    except (BotoCoreError, ClientError) as e:
        raise SecurityGroupError(msg="Failed to create security group '{0}' in rule {1}", e=e)

    group_id = created_group["GroupId"]
    groups[group_id] = created_group
    groups[group_name] = created_group

    return "group", (owner_id, group_id, None), True


def _target_from_rule_with_group_name(client, rule, name, group, groups, vpc_id, tags, check_mode):
    group_name = rule["group_name"]
    owner_id = current_account_id
    if group_name == name:
        # Simplest case, the rule references itself
        group_id = group["GroupId"]
        groups[group_id] = group
        groups[group_name] = group
        return "group", (owner_id, group_id, None), False

    # Already cached groups
    if group_name in groups and group.get("VpcId") and groups[group_name].get("VpcId"):
        # both are VPC groups, this is ok
        group_id = groups[group_name]["GroupId"]
        return "group", (owner_id, group_id, None), False

    if group_name in groups and not (group.get("VpcId") or groups[group_name].get("VpcId")):
        # both are EC2 classic, this is ok
        group_id = groups[group_name]["GroupId"]
        return "group", (owner_id, group_id, None), False

    # if we got here, either the target group does not exist, or there
    # is a mix of EC2 classic + VPC groups. Mixing of EC2 classic + VPC
    # is bad, so we have to create a new SG because no compatible group
    # exists

    # Without a group description we can't create a new group, try looking up the group, or fail
    # with a descriptive error message
    if not rule.get("group_desc", "").strip():
        # retry describing the group
        fail_msg = (
            f"group '{group_name}' not found and would be automatically created by rule {rule} but "
            "no description was provided"
        )
        return _lookup_target_or_fail(client, group_name, vpc_id, groups, fail_msg)

    return _create_target_from_rule(client, rule, groups, vpc_id, tags, check_mode)


def get_target_from_rule(module, client, rule, name, group, groups, vpc_id, tags):
    """
    Returns tuple of (target_type, target, group_created) after validating rule params.

    rule: Dict describing a rule.
    name: Name of the security group being managed.
    groups: Dict of all available security groups.

    AWS accepts an ip range or a security group as target of a rule. This
    function validate the rule specification and return either a non-None
    group_id or a non-None ip range.

    When using a security group as a target all 3 fields (OwnerId, GroupId, and
    GroupName) need to exist in the target. This ensures consistency of the
    values that will be compared to current_rules (from current_ingress and
    current_egress) in wait_for_rule_propagation().
    """
    try:
        if rule.get("group_id"):
            return _target_from_rule_with_group_id(rule, groups)
        if "group_name" in rule:
            return _target_from_rule_with_group_name(client, rule, name, group, groups, vpc_id, tags, module.check_mode)
        if "cidr_ip" in rule:
            return "ipv4", validate_ip(module, rule["cidr_ip"]), False
        if "cidr_ipv6" in rule:
            return "ipv6", validate_ip(module, rule["cidr_ipv6"]), False
        if "ip_prefix" in rule:
            return "ip_prefix", rule["ip_prefix"], False
    except SecurityGroupError as e:
        e.fail(module)

    module.fail_json(msg="Could not match target for rule", failed_rule=rule)


def _strip_rule(rule):
    """
    Returns a copy of the rule with the Target/Source and Port information
    from a rule stripped out.
    This can then be combined with the expanded information
    """
    stripped_rule = deepcopy(rule)
    # Get just the non-source/port info from the rule
    [stripped_rule.pop(source_type, None) for source_type in SOURCE_TYPES_ALL]
    [stripped_rule.pop(port_type, None) for port_type in PORT_TYPES_ALL]
    return stripped_rule


def expand_rules(rules):
    if rules is None:
        return rules

    expanded_rules = []
    for rule in rules:
        expanded_rules.extend(expand_rule(rule))

    return expanded_rules


def expand_rule(rule):
    rule = scrub_none_parameters(rule)
    ports_list = expand_ports_from_rule(rule)
    sources_list = expand_sources_from_rule(rule)
    stripped_rule = _strip_rule(rule)

    # expands out all possible combinations of ports and sources for the rule
    # This results in a list of pairs of dictionaries...
    ports_and_sources = itertools.product(ports_list, sources_list)

    # Combines each pair of port/source dictionaries with rest of the info from the rule
    return [{**stripped_rule, **port, **source} for (port, source) in ports_and_sources]


def expand_sources_from_rule(rule):
    sources = []
    for type_name in sorted(SOURCE_TYPES_ALL):
        if rule.get(type_name) is not None:
            sources.extend([{type_name: target} for target in rule.get(type_name)])
    if not sources:
        raise SecurityGroupError("Unable to find source/target information in rule", rule=rule)
    return tuple(sources)


def expand_ports_from_rule(rule):
    # While icmp_type/icmp_code could have been aliases, this wouldn't be obvious in the
    # documentation
    if rule.get("icmp_type") is not None:
        return ({"from_port": rule.get("icmp_type"), "to_port": rule.get("icmp_code")},)
    if rule.get("from_port") is not None or rule.get("to_port") is not None:
        return ({"from_port": rule.get("from_port"), "to_port": rule.get("to_port")},)
    if rule.get("ports") is not None:
        ports = expand_ports_list(rule.get("ports"))
        return tuple({"from_port": from_port, "to_port": to_port} for (from_port, to_port) in ports)
    return ({},)


def expand_ports_list(ports):
    # takes a list of ports and returns a list of (port_from, port_to)
    ports_expanded = []
    for port in ports:
        try:
            port_list = (int(port.strip()),) * 2
        except ValueError as e:
            # Someone passed a range
            if "-" in port:
                port_list = [int(p.strip()) for p in port.split("-", 1)]
            else:
                raise SecurityGroupError("Unable to parse port", port=port) from e
        ports_expanded.append(tuple(sorted(port_list)))

    return ports_expanded


def update_rules_description(module, client, rule_type, group_id, ip_permissions):
    if module.check_mode:
        return
    try:
        if rule_type == "in":
            client.update_security_group_rule_descriptions_ingress(
                aws_retry=True, GroupId=group_id, IpPermissions=ip_permissions
            )
        if rule_type == "out":
            client.update_security_group_rule_descriptions_egress(
                aws_retry=True, GroupId=group_id, IpPermissions=ip_permissions
            )
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Unable to update rule description for group {group_id}")


def fix_port_and_protocol(permission):
    for key in ("FromPort", "ToPort"):
        if key in permission:
            if permission[key] is None:
                del permission[key]
            else:
                permission[key] = int(permission[key])

    permission["IpProtocol"] = to_text(permission["IpProtocol"])

    return permission


def remove_old_permissions(client, module, revoke_ingress, revoke_egress, group_id):
    if revoke_ingress:
        revoke(client, module, revoke_ingress, group_id, "in")
    if revoke_egress:
        revoke(client, module, revoke_egress, group_id, "out")
    return bool(revoke_ingress or revoke_egress)


def revoke(client, module, ip_permissions, group_id, rule_type):
    if not module.check_mode:
        try:
            if rule_type == "in":
                client.revoke_security_group_ingress(aws_retry=True, GroupId=group_id, IpPermissions=ip_permissions)
            elif rule_type == "out":
                client.revoke_security_group_egress(aws_retry=True, GroupId=group_id, IpPermissions=ip_permissions)
        except (BotoCoreError, ClientError) as e:
            rules = "ingress rules" if rule_type == "in" else "egress rules"
            module.fail_json_aws(e, f"Unable to revoke {rules}: {ip_permissions}")


def add_new_permissions(client, module, new_ingress, new_egress, group_id):
    if new_ingress:
        authorize(client, module, new_ingress, group_id, "in")
    if new_egress:
        authorize(client, module, new_egress, group_id, "out")
    return bool(new_ingress or new_egress)


def authorize(client, module, ip_permissions, group_id, rule_type):
    if not module.check_mode:
        try:
            if rule_type == "in":
                client.authorize_security_group_ingress(aws_retry=True, GroupId=group_id, IpPermissions=ip_permissions)
            elif rule_type == "out":
                client.authorize_security_group_egress(aws_retry=True, GroupId=group_id, IpPermissions=ip_permissions)
        except (BotoCoreError, ClientError) as e:
            rules = "ingress rules" if rule_type == "in" else "egress rules"
            module.fail_json_aws(e, f"Unable to authorize {rules}: {ip_permissions}")


def validate_ip(module, cidr_ip):
    split_addr = cidr_ip.split("/")
    if len(split_addr) != 2:
        return cidr_ip

    try:
        ip = ip_network(to_text(cidr_ip))
        return str(ip)
    except ValueError:
        # If a host bit is incorrectly set, ip_network will throw an error at us,
        # we'll continue, convert the address to a CIDR AWS will accept, but issue a warning.
        pass

    # Try evaluating as an IPv4 network, it'll throw a ValueError if it can't parse cidr_ip as an
    # IPv4 network
    try:
        ip = to_subnet(split_addr[0], split_addr[1])
        module.warn(
            f"One of your CIDR addresses ({cidr_ip}) has host bits set. To get rid of this warning, check the network"
            f" mask and make sure that only network bits are set: {ip}."
        )
        return ip
    except ValueError:
        pass

    # Try again, evaluating as an IPv6 network.
    try:
        ip6 = to_ipv6_subnet(split_addr[0]) + "/" + split_addr[1]
        module.warn(
            f"One of your IPv6 CIDR addresses ({cidr_ip}) has host bits set. To get rid of this warning, check the"
            f" network mask and make sure that only network bits are set: {ip6}."
        )
        return ip6
    except ValueError:
        module.warn(f"Unable to parse CIDR ({cidr_ip}).")
        return cidr_ip


def update_rule_descriptions(
    module, client, group_id, present_ingress, named_tuple_ingress_list, present_egress, named_tuple_egress_list
):
    changed = False
    ingress_needs_desc_update = []
    egress_needs_desc_update = []

    for present_rule in present_egress:
        needs_update = [
            r
            for r in named_tuple_egress_list
            if rule_cmp(r, present_rule) and r.description != present_rule.description
        ]
        for r in needs_update:
            named_tuple_egress_list.remove(r)
        egress_needs_desc_update.extend(needs_update)
    for present_rule in present_ingress:
        needs_update = [
            r
            for r in named_tuple_ingress_list
            if rule_cmp(r, present_rule) and r.description != present_rule.description
        ]
        for r in needs_update:
            named_tuple_ingress_list.remove(r)
        ingress_needs_desc_update.extend(needs_update)

    if ingress_needs_desc_update:
        update_rules_description(module, client, "in", group_id, rules_to_permissions(ingress_needs_desc_update))
        changed |= True
    if egress_needs_desc_update:
        update_rules_description(module, client, "out", group_id, rules_to_permissions(egress_needs_desc_update))
        changed |= True
    return changed


def _create_security_group_with_wait(client, name, description, vpc_id, tags):
    params = dict(GroupName=name, Description=description)
    if vpc_id:
        params["VpcId"] = vpc_id
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, ["security-group"])

    created_group = client.create_security_group(aws_retry=True, **params)
    get_waiter(
        client,
        "security_group_exists",
    ).wait(
        GroupIds=[created_group["GroupId"]],
    )
    return created_group


def create_security_group(client, module, name, description, vpc_id, tags):
    if not module.check_mode:
        params = dict(GroupName=name, Description=description)
        if vpc_id:
            params["VpcId"] = vpc_id
        if tags:
            params["TagSpecifications"] = boto3_tag_specifications(tags, ["security-group"])
        try:
            group = client.create_security_group(aws_retry=True, **params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to create security group")
        # When a group is created, an egress_rule ALLOW ALL
        # to 0.0.0.0/0 is added automatically but it's not
        # reflected in the object returned by the AWS API
        # call. We re-read the group for getting an updated object
        # amazon sometimes takes a couple seconds to update the security group so wait till it exists
        while True:
            sleep(3)
            group = get_security_groups_with_backoff(client, GroupIds=[group["GroupId"]])["SecurityGroups"][0]
            if group.get("VpcId") and not group.get("IpPermissionsEgress"):
                pass
            else:
                break
        return group
    return None


def wait_for_rule_propagation(module, client, group, desired_ingress, desired_egress, purge_ingress, purge_egress):
    group_id = group["GroupId"]
    tries = 6

    def await_rules(group, desired_rules, purge, rule_key):
        for _i in range(tries):
            current_rules = set(sum([list(rule_from_group_permission(p)) for p in group[rule_key]], []))
            if purge and len(current_rules ^ set(desired_rules)) == 0:
                return group
            elif purge:
                conflicts = current_rules ^ set(desired_rules)
                # For cases where set comparison is equivalent, but invalid port/proto exist
                for a, b in itertools.combinations(conflicts, 2):
                    if rule_cmp(a, b):
                        conflicts.discard(a)
                        conflicts.discard(b)
                if not len(conflicts):
                    return group
            elif current_rules.issuperset(desired_rules) and not purge:
                return group
            sleep(10)
            group = get_security_groups_with_backoff(client, GroupIds=[group_id])["SecurityGroups"][0]
        module.warn(
            f"Ran out of time waiting for {group_id} {rule_key}. Current: {current_rules}, Desired: {desired_rules}"
        )
        return group

    group = get_security_groups_with_backoff(client, GroupIds=[group_id])["SecurityGroups"][0]
    if "VpcId" in group and module.params.get("rules_egress") is not None:
        group = await_rules(group, desired_egress, purge_egress, "IpPermissionsEgress")
    return await_rules(group, desired_ingress, purge_ingress, "IpPermissions")


def group_exists(client, module, vpc_id, group_id, name):
    filters = dict()
    params = dict()
    if group_id:
        if isinstance(group_id, list):
            params["GroupIds"] = group_id
        else:
            params["GroupIds"] = [group_id]
    if name:
        # Add name to filters rather than params['GroupNames']
        # because params['GroupNames'] only checks the default vpc if no vpc is provided
        filters["group-name"] = name
    if vpc_id:
        filters["vpc-id"] = vpc_id
    # Don't filter by description to maintain backwards compatibility
    params["Filters"] = ansible_dict_to_boto3_filter_list(filters)
    try:
        security_groups = sg_exists_with_backoff(client, **params).get("SecurityGroups", [])
        all_groups = get_security_groups_with_backoff(client).get("SecurityGroups", [])
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Error in describe_security_groups")

    if security_groups:
        groups = dict((group["GroupId"], group) for group in all_groups)
        groups.update(dict((group["GroupName"], group) for group in all_groups))
        if vpc_id:
            vpc_wins = dict(
                (group["GroupName"], group) for group in all_groups if group.get("VpcId") and group["VpcId"] == vpc_id
            )
            groups.update(vpc_wins)
        # maintain backwards compatibility by using the last matching group
        return security_groups[-1], groups
    return None, {}


def get_diff_final_resource(client, module, security_group):
    def get_account_id(security_group, module):
        try:
            owner_id = security_group.get("owner_id", current_account_id)
        except (BotoCoreError, ClientError) as e:
            owner_id = f"Unable to determine owner_id: {to_text(e)}"
        return owner_id

    def get_final_tags(security_group_tags, specified_tags, purge_tags):
        if specified_tags is None:
            return security_group_tags
        tags_need_modify, tags_to_delete = compare_aws_tags(security_group_tags, specified_tags, purge_tags)
        end_result_tags = dict((k, v) for k, v in specified_tags.items() if k not in tags_to_delete)
        end_result_tags.update(dict((k, v) for k, v in security_group_tags.items() if k not in tags_to_delete))
        end_result_tags.update(tags_need_modify)
        return end_result_tags

    def get_final_rules(client, module, security_group_rules, specified_rules, purge_rules):
        if specified_rules is None:
            return security_group_rules
        if purge_rules:
            final_rules = []
        else:
            final_rules = list(security_group_rules)
        specified_rules = flatten_nested_targets(module, deepcopy(specified_rules))
        for rule in specified_rules:
            format_rule = {
                "from_port": None,
                "to_port": None,
                "ip_protocol": rule.get("proto"),
                "ip_ranges": [],
                "ipv6_ranges": [],
                "prefix_list_ids": [],
                "user_id_group_pairs": [],
            }
            if rule.get("proto") in ("all", "-1", -1):
                format_rule["ip_protocol"] = "-1"
                format_rule.pop("from_port")
                format_rule.pop("to_port")
            elif rule.get("ports"):
                if rule.get("ports") and (isinstance(rule["ports"], string_types) or isinstance(rule["ports"], int)):
                    rule["ports"] = [rule["ports"]]
                for port in rule.get("ports"):
                    if isinstance(port, string_types) and "-" in port:
                        format_rule["from_port"], format_rule["to_port"] = port.split("-")
                    else:
                        format_rule["from_port"] = format_rule["to_port"] = port
            elif rule.get("from_port") or rule.get("to_port"):
                format_rule["from_port"] = rule.get("from_port", rule.get("to_port"))
                format_rule["to_port"] = rule.get("to_port", rule.get("from_port"))
            for source_type in ("cidr_ip", "cidr_ipv6", "prefix_list_id"):
                if rule.get(source_type):
                    rule_key = {
                        "cidr_ip": "ip_ranges",
                        "cidr_ipv6": "ipv6_ranges",
                        "prefix_list_id": "prefix_list_ids",
                    }.get(source_type)
                    if rule.get("rule_desc"):
                        format_rule[rule_key] = [{source_type: rule[source_type], "description": rule["rule_desc"]}]
                    else:
                        if not isinstance(rule[source_type], list):
                            rule[source_type] = [rule[source_type]]
                        format_rule[rule_key] = [{source_type: target} for target in rule[source_type]]
            if rule.get("group_id") or rule.get("group_name"):
                # XXX bug - doesn't cope with a list of ids/names
                rule_sg = group_exists(
                    client, module, module.params["vpc_id"], rule.get("group_id"), rule.get("group_name")
                )[0]
                if rule_sg is None:
                    # --diff during --check
                    format_rule["user_id_group_pairs"] = [
                        {
                            "group_id": rule.get("group_id"),
                            "group_name": rule.get("group_name"),
                            "peering_status": None,
                            "user_id": get_account_id(security_group, module),
                            "vpc_id": module.params["vpc_id"],
                            "vpc_peering_connection_id": None,
                        }
                    ]
                else:
                    rule_sg = camel_dict_to_snake_dict(rule_sg)
                    format_rule["user_id_group_pairs"] = [
                        {
                            "description": rule_sg.get("description", rule_sg.get("group_desc")),
                            "group_id": rule_sg.get("group_id", rule.get("group_id")),
                            "group_name": rule_sg.get("group_name", rule.get("group_name")),
                            "peering_status": rule_sg.get("peering_status"),
                            "user_id": rule_sg.get("user_id", get_account_id(security_group, module)),
                            "vpc_id": rule_sg.get("vpc_id", module.params["vpc_id"]),
                            "vpc_peering_connection_id": rule_sg.get("vpc_peering_connection_id"),
                        }
                    ]
                for k, v in list(format_rule["user_id_group_pairs"][0].items()):
                    if v is None:
                        format_rule["user_id_group_pairs"][0].pop(k)
            final_rules.append(format_rule)
        return final_rules

    security_group_ingress = security_group.get("ip_permissions", [])
    specified_ingress = module.params["rules"]
    purge_ingress = module.params["purge_rules"]
    security_group_egress = security_group.get("ip_permissions_egress", [])
    specified_egress = module.params["rules_egress"]
    purge_egress = module.params["purge_rules_egress"]
    return {
        "description": module.params["description"],
        "group_id": security_group.get("group_id", "sg-xxxxxxxx"),
        "group_name": security_group.get("group_name", module.params["name"]),
        "ip_permissions": get_final_rules(client, module, security_group_ingress, specified_ingress, purge_ingress),
        "ip_permissions_egress": get_final_rules(client, module, security_group_egress, specified_egress, purge_egress),
        "owner_id": get_account_id(security_group, module),
        "tags": get_final_tags(security_group.get("tags", {}), module.params["tags"], module.params["purge_tags"]),
        "vpc_id": security_group.get("vpc_id", module.params["vpc_id"]),
    }


def flatten_nested_targets(module, rules):
    def _flatten(targets):
        for target in targets:
            if isinstance(target, list):
                module.deprecate(
                    (
                        "Support for nested lists in cidr_ip and cidr_ipv6 has been "
                        "deprecated.  The flatten filter can be used instead."
                    ),
                    date="2024-12-01",
                    collection_name="amazon.aws",
                )
                yield from _flatten(target)
            elif isinstance(target, string_types):
                yield target

    if rules is not None:
        for rule in rules:
            target_list_type = None
            if isinstance(rule.get("cidr_ip"), list):
                target_list_type = "cidr_ip"
            elif isinstance(rule.get("cidr_ipv6"), list):
                target_list_type = "cidr_ipv6"
            if target_list_type is not None:
                rule[target_list_type] = list(_flatten(rule[target_list_type]))
    return rules


def get_rule_sort_key(dicts):
    if dicts.get("cidr_ip"):
        return str(dicts.get("cidr_ip"))
    if dicts.get("cidr_ipv6"):
        return str(dicts.get("cidr_ipv6"))
    if dicts.get("prefix_list_id"):
        return str(dicts.get("prefix_list_id"))
    if dicts.get("group_id"):
        return str(dicts.get("group_id"))
    return None


def get_ip_permissions_sort_key(rule):
    RULE_KEYS_ALL = {"ip_ranges", "ipv6_ranges", "prefix_list_ids", "user_id_group_pairs"}
    # Ensure content of these keys is sorted
    for rule_key in RULE_KEYS_ALL:
        if rule.get(rule_key):
            rule.get(rule_key).sort(key=get_rule_sort_key)

    # Returns the first value plus a prefix so the types get clustered together when sorted
    if rule.get("ip_ranges"):
        value = str(rule.get("ip_ranges")[0]["cidr_ip"])
        return f"ipv4:{value}"
    if rule.get("ipv6_ranges"):
        value = str(rule.get("ipv6_ranges")[0]["cidr_ipv6"])
        return f"ipv6:{value}"
    if rule.get("prefix_list_ids"):
        value = str(rule.get("prefix_list_ids")[0]["prefix_list_id"])
        return f"pl:{value}"
    if rule.get("user_id_group_pairs"):
        value = str(rule.get("user_id_group_pairs")[0].get("group_id", ""))
        return f"ugid:{value}"
    return None


def sort_security_group(security_group):
    if not security_group:
        return security_group

    if security_group.get("ip_permissions"):
        security_group["ip_permissions"].sort(key=get_ip_permissions_sort_key)
    if security_group.get("ip_permissions_egress"):
        security_group["ip_permissions_egress"].sort(key=get_ip_permissions_sort_key)

    return security_group


def validate_rules(module, rules):
    if not rules:
        return
    try:
        for rule in rules:
            validate_rule(rule)
    except SecurityGroupError as e:
        e.fail(module)


def ensure_absent(client, group, check_mode):
    if not group:
        return False
    if check_mode:
        return True

    try:
        client.delete_security_group(aws_retry=True, GroupId=group["GroupId"])
    except is_boto3_error_code("InvalidGroup.NotFound"):
        return False
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        raise SecurityGroupError(f"Unable to delete security group '{group}'", e=e)

    return True


def ensure_present(module, client, group, groups):
    name = module.params["name"]
    group_id = module.params["group_id"]
    description = module.params["description"]
    vpc_id = module.params["vpc_id"]
    # Deprecated
    rules = flatten_nested_targets(module, deepcopy(module.params["rules"]))
    rules_egress = flatten_nested_targets(module, deepcopy(module.params["rules_egress"]))
    # /end Deprecated
    validate_rules(module, rules)
    validate_rules(module, rules_egress)
    rules = deduplicate_rules_args(expand_rules(rules))
    rules_egress = deduplicate_rules_args(expand_rules(rules_egress))
    state = module.params.get("state")
    purge_rules = module.params["purge_rules"]
    purge_rules_egress = module.params["purge_rules_egress"]
    tags = module.params["tags"]
    purge_tags = module.params["purge_tags"]

    changed = False
    group_created_new = False

    if not group:
        # Short circuit things if we're in check_mode
        if module.check_mode:
            return True, None

        group = create_security_group(client, module, name, description, vpc_id, tags)
        group_created_new = True
        changed = True

    else:
        # Description is immutable
        if group["Description"] != description:
            module.warn(
                "Group description does not match existing group. Descriptions cannot be changed without deleting "
                "and re-creating the security group. Try using state=absent to delete, then rerunning this task."
            )

    changed |= ensure_ec2_tags(client, module, group["GroupId"], tags=tags, purge_tags=purge_tags)

    named_tuple_ingress_list = []
    named_tuple_egress_list = []
    current_ingress = sum([list(rule_from_group_permission(p)) for p in group["IpPermissions"]], [])
    current_egress = sum([list(rule_from_group_permission(p)) for p in group["IpPermissionsEgress"]], [])

    for new_rules, _rule_type, named_tuple_rule_list in [
        (rules, "in", named_tuple_ingress_list),
        (rules_egress, "out", named_tuple_egress_list),
    ]:
        if new_rules is None:
            continue
        for rule in new_rules:
            target_type, target, target_group_created = get_target_from_rule(
                module, client, rule, name, group, groups, vpc_id, tags
            )
            changed |= target_group_created

            if rule.get("proto") in ("all", "-1", -1):
                rule["proto"] = "-1"
                rule["from_port"] = None
                rule["to_port"] = None

            try:
                int(rule.get("proto"))
                rule["proto"] = to_text(rule.get("proto"))
                rule["from_port"] = None
                rule["to_port"] = None
            except ValueError:
                # rule does not use numeric protocol spec
                pass
            named_tuple_rule_list.append(
                Rule(
                    port_range=(rule["from_port"], rule["to_port"]),
                    protocol=to_text(rule.get("proto")),
                    target=target,
                    target_type=target_type,
                    description=rule.get("rule_desc"),
                )
            )

    # List comprehensions for rules to add, rules to modify, and rule ids to determine purging
    new_ingress_permissions = [to_permission(r) for r in (set(named_tuple_ingress_list) - set(current_ingress))]
    new_egress_permissions = [to_permission(r) for r in (set(named_tuple_egress_list) - set(current_egress))]

    if module.params.get("rules_egress") is None and "VpcId" in group:
        # when no egress rules are specified and we're in a VPC,
        # we add in a default allow all out rule, which was the
        # default behavior before egress rules were added
        rule = Rule((None, None), "-1", "0.0.0.0/0", "ipv4", None)
        if rule in current_egress:
            named_tuple_egress_list.append(rule)
        if rule not in current_egress:
            current_egress.append(rule)

    # List comprehensions for rules to add, rules to modify, and rule ids to determine purging
    present_ingress = list(set(named_tuple_ingress_list).union(set(current_ingress)))
    present_egress = list(set(named_tuple_egress_list).union(set(current_egress)))

    if purge_rules:
        revoke_ingress = []
        for p in present_ingress:
            if not any(rule_cmp(p, b) for b in named_tuple_ingress_list):
                revoke_ingress.append(to_permission(p))
    else:
        revoke_ingress = []

    if purge_rules_egress and module.params.get("rules_egress") is not None:
        revoke_egress = []
        for p in present_egress:
            if not any(rule_cmp(p, b) for b in named_tuple_egress_list):
                revoke_egress.append(to_permission(p))
    else:
        revoke_egress = []

    # named_tuple_ingress_list and named_tuple_egress_list get updated by
    # method update_rule_descriptions, deep copy these two lists to new
    # variables for the record of the 'desired' ingress and egress sg permissions
    desired_ingress = deepcopy(named_tuple_ingress_list)
    desired_egress = deepcopy(named_tuple_egress_list)

    changed |= update_rule_descriptions(
        module,
        client,
        group["GroupId"],
        present_ingress,
        named_tuple_ingress_list,
        present_egress,
        named_tuple_egress_list,
    )

    # Revoke old rules
    changed |= remove_old_permissions(client, module, revoke_ingress, revoke_egress, group["GroupId"])

    new_ingress_permissions = [to_permission(r) for r in (set(named_tuple_ingress_list) - set(current_ingress))]
    new_ingress_permissions = rules_to_permissions(set(named_tuple_ingress_list) - set(current_ingress))
    new_egress_permissions = rules_to_permissions(set(named_tuple_egress_list) - set(current_egress))
    # Authorize new rules
    changed |= add_new_permissions(client, module, new_ingress_permissions, new_egress_permissions, group["GroupId"])

    if group_created_new and module.params.get("rules") is None and module.params.get("rules_egress") is None:
        # A new group with no rules provided is already being awaited.
        # When it is created we wait for the default egress rule to be added by AWS
        security_group = get_security_groups_with_backoff(client, GroupIds=[group["GroupId"]])["SecurityGroups"][0]
    elif changed and not module.check_mode:
        # keep pulling until current security group rules match the desired ingress and egress rules
        security_group = wait_for_rule_propagation(
            module, client, group, desired_ingress, desired_egress, purge_rules, purge_rules_egress
        )
    else:
        security_group = get_security_groups_with_backoff(client, GroupIds=[group["GroupId"]])["SecurityGroups"][0]
    security_group = camel_dict_to_snake_dict(security_group, ignore_list=["Tags"])
    security_group["tags"] = boto3_tag_list_to_ansible_dict(security_group.get("tags", []))

    return changed, security_group


def main():
    rule_spec = dict(
        rule_desc=dict(type="str"),
        # We have historically allowed for lists of lists in cidr_ip and cidr_ipv6
        # https://github.com/ansible-collections/amazon.aws/pull/1213
        cidr_ip=dict(type="list", elements="raw"),
        cidr_ipv6=dict(type="list", elements="raw"),
        ip_prefix=dict(type="list", elements="str"),
        group_id=dict(type="list", elements="str"),
        group_name=dict(type="list", elements="str"),
        group_desc=dict(type="str"),
        proto=dict(type="str", default="tcp"),
        ports=dict(type="list", elements="str"),
        from_port=dict(type="int"),
        to_port=dict(type="int"),
        icmp_type=dict(type="int"),
        icmp_code=dict(type="int"),
    )
    rule_requirements = dict(
        mutually_exclusive=(
            # PORTS / ICMP_TYPE + ICMP_CODE / TO_PORT + FROM_PORT
            (
                "ports",
                "to_port",
            ),
            (
                "ports",
                "from_port",
            ),
            (
                "ports",
                "icmp_type",
            ),
            (
                "ports",
                "icmp_code",
            ),
            (
                "icmp_type",
                "to_port",
            ),
            (
                "icmp_code",
                "to_port",
            ),
            (
                "icmp_type",
                "from_port",
            ),
            (
                "icmp_code",
                "from_port",
            ),
        ),
        required_one_of=(
            # A target must be specified
            (
                "group_id",
                "group_name",
                "cidr_ip",
                "cidr_ipv6",
                "ip_prefix",
            ),
        ),
        required_by=dict(
            # If you specify an ICMP code, you must specify the ICMP type
            icmp_code=("icmp_type",),
        ),
    )

    argument_spec = dict(
        name=dict(),
        group_id=dict(),
        description=dict(),
        vpc_id=dict(),
        rules=dict(type="list", elements="dict", options=rule_spec, **rule_requirements),
        rules_egress=dict(
            type="list", elements="dict", aliases=["egress_rules"], options=rule_spec, **rule_requirements
        ),
        state=dict(default="present", type="str", choices=["present", "absent"]),
        purge_rules=dict(default=True, required=False, type="bool"),
        purge_rules_egress=dict(default=True, required=False, type="bool", aliases=["purge_egress_rules"]),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, required=False, type="bool"),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[["name", "group_id"]],
        required_if=[["state", "present", ["name", "description"]]],
    )

    name = module.params["name"]
    group_id = module.params["group_id"]
    vpc_id = module.params["vpc_id"]
    state = module.params.get("state")

    client = module.client("ec2", AWSRetry.jittered_backoff())

    group, groups = group_exists(client, module, vpc_id, group_id, name)

    global current_account_id
    current_account_id = get_aws_account_id(module)

    before = {}
    after = {}

    if group:
        before = camel_dict_to_snake_dict(group, ignore_list=["Tags"])
        before["tags"] = boto3_tag_list_to_ansible_dict(before.get("tags", []))

    try:
        # Ensure requested group is absent
        if state == "absent":
            changed = ensure_absent(client, group, module.check_mode)
            security_group = {"group_id": None}
        # Ensure requested group is present
        elif state == "present":
            (changed, security_group) = ensure_present(module, client, group, groups)
            # Check mode can't create anything
            if not security_group:
                security_group = {"group_id": None}
    except SecurityGroupError as e:
        e.fail(module)

    if module._diff:
        if state == "present":
            after = get_diff_final_resource(client, module, security_group)

        # Order final rules consistently
        before = sort_security_group(before)
        after = sort_security_group(after)

        security_group["diff"] = [{"before": before, "after": after}]

    module.exit_json(changed=changed, **security_group)


if __name__ == "__main__":
    main()

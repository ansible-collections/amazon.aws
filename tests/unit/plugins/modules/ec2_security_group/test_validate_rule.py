# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy

import pytest

import ansible_collections.amazon.aws.plugins.modules.ec2_security_group as ec2_security_group_module

VALID_RULES = [
    dict(
        proto="all",
    ),
    dict(
        proto="tcp",
        from_port="1",
        to_port="65535",
    ),
    dict(
        proto="icmpv6",
        from_port="-1",
        to_port="-1",
    ),
    dict(
        proto="icmp",
        from_port="-1",
        to_port="-1",
    ),
    dict(proto="icmpv6", icmp_type="8", icmp_code="1"),
    dict(proto="icmpv6", icmp_code="1"),
    dict(proto="icmpv6", icmp_type="8"),
    dict(proto="icmp", icmp_type="8", icmp_code="1"),
    dict(proto="icmp", icmp_code="1"),
    dict(proto="icmp", icmp_type="8"),
]

INVALID_RULES = [
    (
        dict(
            proto="tcp",
            icmp_code="1",
        ),
        r"Specify proto: icmp or icmpv6",
    ),
    (
        dict(
            proto="tcp",
            icmp_type="8",
        ),
        r"Specify proto: icmp or icmpv6",
    ),
    (
        dict(
            proto="tcp",
            icmp_type="8",
            icmp_code="1",
        ),
        r"Specify proto: icmp or icmpv6",
    ),
    (
        dict(
            proto="all",
            icmp_code="1",
        ),
        r"Specify proto: icmp or icmpv6",
    ),
    (
        dict(
            proto="all",
            icmp_type="8",
        ),
        r"Specify proto: icmp or icmpv6",
    ),
    (
        dict(
            proto="all",
            icmp_type="8",
            icmp_code="1",
        ),
        r"Specify proto: icmp or icmpv6",
    ),
]


@pytest.mark.parametrize("rule,error_msg", INVALID_RULES)
def test_validate_rule_invalid(rule, error_msg):
    original_rule = deepcopy(rule)
    with pytest.raises(ec2_security_group_module.SecurityGroupError, match=error_msg):
        ec2_security_group_module.validate_rule(rule)
    assert original_rule == rule


@pytest.mark.parametrize("rule", VALID_RULES)
def test_validate_rule_valid(rule):
    original_rule = deepcopy(rule)
    ec2_security_group_module.validate_rule(rule)
    # validate_rule shouldn't change the rule
    assert original_rule == rule

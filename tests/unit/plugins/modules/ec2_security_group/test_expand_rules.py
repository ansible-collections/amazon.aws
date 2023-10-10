# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.modules.ec2_security_group as ec2_security_group_module

PORT_EXPANSION = [
    ({"from_port": 83}, ({"from_port": 83, "to_port": None},)),
    ({"to_port": 36}, ({"from_port": None, "to_port": 36},)),
    ({"icmp_type": 90}, ({"from_port": 90, "to_port": None},)),
    ({"icmp_type": 74, "icmp_code": 66}, ({"from_port": 74, "to_port": 66},)),
    # Note: ports is explicitly a list of strings because we support "<port a>-<port b>"
    ({"ports": ["1"]}, ({"from_port": 1, "to_port": 1},)),
    ({"ports": ["41-85"]}, ({"from_port": 41, "to_port": 85},)),
    (
        {"ports": ["63", "74"]},
        (
            {"from_port": 63, "to_port": 63},
            {"from_port": 74, "to_port": 74},
        ),
    ),
    (
        {"ports": ["97-30", "41-80"]},
        (
            {"from_port": 30, "to_port": 97},
            {"from_port": 41, "to_port": 80},
        ),
    ),
    (
        {"ports": ["95", "67-79"]},
        (
            {"from_port": 95, "to_port": 95},
            {"from_port": 67, "to_port": 79},
        ),
    ),
    # There are legitimate cases with no port info
    ({}, ({},)),
]
PORTS_EXPANSION = [
    (["28"], [(28, 28)]),
    (["80-83"], [(80, 83)]),
    # We tolerate the order being backwards
    (["83-80"], [(80, 83)]),
    (["41", "1"], [(41, 41), (1, 1)]),
    (["70", "39-0"], [(70, 70), (0, 39)]),
    (["57-6", "31"], [(6, 57), (31, 31)]),
    # https://github.com/ansible-collections/amazon.aws/pull/1241
    (["-1"], [(-1, -1)]),
]
SOURCE_EXPANSION = [
    (
        {"cidr_ip": ["192.0.2.0/24"]},
        ({"cidr_ip": "192.0.2.0/24"},),
    ),
    (
        {"cidr_ipv6": ["2001:db8::/32"]},
        ({"cidr_ipv6": "2001:db8::/32"},),
    ),
    (
        {"group_id": ["sg-123456789"]},
        ({"group_id": "sg-123456789"},),
    ),
    (
        {"group_name": ["MyExampleGroupName"]},
        ({"group_name": "MyExampleGroupName"},),
    ),
    (
        {"ip_prefix": ["pl-123456abcde123456"]},
        ({"ip_prefix": "pl-123456abcde123456"},),
    ),
    (
        {"cidr_ip": ["192.0.2.0/24", "198.51.100.0/24"]},
        (
            {"cidr_ip": "192.0.2.0/24"},
            {"cidr_ip": "198.51.100.0/24"},
        ),
    ),
    (
        {"cidr_ipv6": ["2001:db8::/32", "100::/64"]},
        (
            {"cidr_ipv6": "2001:db8::/32"},
            {"cidr_ipv6": "100::/64"},
        ),
    ),
    (
        {"group_id": ["sg-123456789", "sg-abcdef1234"]},
        (
            {"group_id": "sg-123456789"},
            {"group_id": "sg-abcdef1234"},
        ),
    ),
    (
        {"group_name": ["MyExampleGroupName", "AnotherExample"]},
        (
            {"group_name": "MyExampleGroupName"},
            {"group_name": "AnotherExample"},
        ),
    ),
    (
        {"ip_prefix": ["pl-123456abcde123456", "pl-abcdef12345abcdef"]},
        ({"ip_prefix": "pl-123456abcde123456"}, {"ip_prefix": "pl-abcdef12345abcdef"}),
    ),
    (
        {
            "cidr_ip": ["192.0.2.0/24"],
            "cidr_ipv6": ["2001:db8::/32"],
            "group_id": ["sg-123456789"],
            "group_name": ["MyExampleGroupName"],
            "ip_prefix": ["pl-123456abcde123456"],
        },
        (
            {"cidr_ip": "192.0.2.0/24"},
            {"cidr_ipv6": "2001:db8::/32"},
            {"group_id": "sg-123456789"},
            {"group_name": "MyExampleGroupName"},
            {"ip_prefix": "pl-123456abcde123456"},
        ),
    ),
    (
        {
            "cidr_ip": ["192.0.2.0/24", "198.51.100.0/24"],
            "cidr_ipv6": ["2001:db8::/32", "100::/64"],
            "group_id": ["sg-123456789", "sg-abcdef1234"],
            "group_name": ["MyExampleGroupName", "AnotherExample"],
            "ip_prefix": ["pl-123456abcde123456", "pl-abcdef12345abcdef"],
        },
        (
            {"cidr_ip": "192.0.2.0/24"},
            {"cidr_ip": "198.51.100.0/24"},
            {"cidr_ipv6": "2001:db8::/32"},
            {"cidr_ipv6": "100::/64"},
            {"group_id": "sg-123456789"},
            {"group_id": "sg-abcdef1234"},
            {"group_name": "MyExampleGroupName"},
            {"group_name": "AnotherExample"},
            {"ip_prefix": "pl-123456abcde123456"},
            {"ip_prefix": "pl-abcdef12345abcdef"},
        ),
    ),
]

RULE_EXPANSION = [
    (
        {"ports": ["24"], "cidr_ip": ["192.0.2.0/24"], "sentinel": sentinel.RULE_VALUE},
        [
            {"from_port": 24, "to_port": 24, "cidr_ip": "192.0.2.0/24", "sentinel": sentinel.RULE_VALUE},
        ],
    ),
    (
        {"ports": ["24", "50"], "cidr_ip": ["192.0.2.0/24", "198.51.100.0/24"], "sentinel": sentinel.RULE_VALUE},
        [
            {"from_port": 24, "to_port": 24, "cidr_ip": "192.0.2.0/24", "sentinel": sentinel.RULE_VALUE},
            {"from_port": 24, "to_port": 24, "cidr_ip": "198.51.100.0/24", "sentinel": sentinel.RULE_VALUE},
            {"from_port": 50, "to_port": 50, "cidr_ip": "192.0.2.0/24", "sentinel": sentinel.RULE_VALUE},
            {"from_port": 50, "to_port": 50, "cidr_ip": "198.51.100.0/24", "sentinel": sentinel.RULE_VALUE},
        ],
    ),
]


@pytest.mark.parametrize("rule, expected", PORT_EXPANSION)
def test_expand_ports_from_rule(rule, expected):
    assert ec2_security_group_module.expand_ports_from_rule(rule) == expected

    # We shouldn't care about extra values lurking in the rule definition
    rule["junk"] = sentinel.EXTRA_JUNK
    assert ec2_security_group_module.expand_ports_from_rule(rule) == expected


@pytest.mark.parametrize("rule, expected", SOURCE_EXPANSION)
def test_expand_sources_from_rule(rule, expected):
    assert ec2_security_group_module.expand_sources_from_rule(rule) == expected

    # We shouldn't care about extra values lurking in the rule definition
    rule["junk"] = sentinel.EXTRA_JUNK
    assert ec2_security_group_module.expand_sources_from_rule(rule) == expected


@pytest.mark.parametrize("rule, expected", PORTS_EXPANSION)
def test_expand_ports_list(rule, expected):
    assert ec2_security_group_module.expand_ports_list(rule) == expected


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="requires Python 3.7 or higher - sentinel doesn't behave well with deepcopy in Python 3.6",
)
@pytest.mark.parametrize("source_type", sorted(ec2_security_group_module.SOURCE_TYPES_ALL))
def test_strip_rule_source(source_type):
    rule = {source_type: sentinel.SOURCE_VALUE}
    assert ec2_security_group_module._strip_rule(rule) == {}
    assert rule == {source_type: sentinel.SOURCE_VALUE}

    rule = {source_type: sentinel.SOURCE_VALUE, "sentinel": sentinel.SENTINEL_VALUE}
    assert ec2_security_group_module._strip_rule(rule) == {"sentinel": sentinel.SENTINEL_VALUE}
    assert rule == {source_type: sentinel.SOURCE_VALUE, "sentinel": sentinel.SENTINEL_VALUE}


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="requires Python 3.7 or higher - sentinel doesn't behave well with deepcopy in Python 3.6",
)
@pytest.mark.parametrize("port_type", sorted(ec2_security_group_module.PORT_TYPES_ALL))
def test_strip_rule_port(port_type):
    rule = {port_type: sentinel.PORT_VALUE}
    assert ec2_security_group_module._strip_rule(rule) == {}
    assert rule == {port_type: sentinel.PORT_VALUE}

    rule = {port_type: sentinel.PORT_VALUE, "sentinel": sentinel.SENTINEL_VALUE}
    assert ec2_security_group_module._strip_rule(rule) == {"sentinel": sentinel.SENTINEL_VALUE}
    assert rule == {port_type: sentinel.PORT_VALUE, "sentinel": sentinel.SENTINEL_VALUE}


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="requires Python 3.7 or higher - sentinel doesn't behave well with deepcopy in Python 3.6",
)
@pytest.mark.parametrize("rule, expected", RULE_EXPANSION)
def test_rule_expand(rule, expected):
    assert ec2_security_group_module.expand_rule(rule) == expected


##########################################################
# Examples where we explicitly expect to raise an exception


def test_expand_ports_list_bad():
    with pytest.raises(ec2_security_group_module.SecurityGroupError):
        ec2_security_group_module.expand_ports_list(["junk"])


def test_expand_sources_from_rule_bad():
    with pytest.raises(ec2_security_group_module.SecurityGroupError):
        ec2_security_group_module.expand_sources_from_rule(dict())

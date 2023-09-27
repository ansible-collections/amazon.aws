# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.modules.ec2_security_group as ec2_security_group_module

SORT_ORDER = [
    (dict(), dict()),
    (
        dict(ip_permissions=[], ip_permissions_egress=[]),
        dict(ip_permissions=[], ip_permissions_egress=[]),
    ),
    (
        dict(
            ip_permissions=[
                dict(
                    ip_protocol="tcp",
                    ip_ranges=[],
                    ipv6_ranges=[
                        dict(cidr_ipv6="2001:DB8:8000::/34"),
                        dict(cidr_ipv6="2001:DB8:4000::/34"),
                    ],
                    prefix_list_ids=[],
                    user_id_group_pairs=[],
                ),
                dict(
                    ip_protocol="-1",
                    ip_ranges=[
                        dict(cidr_ip="198.51.100.0/24"),
                        dict(cidr_ip="192.0.2.0/24"),
                    ],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    user_id_group_pairs=[],
                ),
                dict(
                    from_port="22",
                    ip_ranges=[],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    to_port="22",
                    user_id_group_pairs=[
                        dict(group_id="sg-3950599b", user_id="123456789012"),
                        dict(group_id="sg-fbfd1e3a", user_id="012345678901"),
                        dict(group_id="sg-00ec640f", user_id="012345678901"),
                    ],
                ),
                dict(
                    from_port=38,
                    ip_protocol="tcp",
                    ip_ranges=[],
                    ipv6_ranges=[],
                    prefix_list_ids=[
                        dict(prefix_list_id="pl-2263adef"),
                        dict(prefix_list_id="pl-0a5fccee"),
                        dict(prefix_list_id="pl-65911ba9"),
                    ],
                    to_port=38,
                    user_id_group_pairs=[],
                ),
            ],
            ip_permissions_egress=[
                dict(
                    ip_protocol="-1",
                    ip_ranges=[
                        dict(cidr_ip="198.51.100.0/24"),
                        dict(cidr_ip="192.0.2.0/24"),
                    ],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    user_id_group_pairs=[],
                ),
                dict(
                    from_port=443,
                    ip_protocol="tcp",
                    ip_ranges=[],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    to_port=443,
                    user_id_group_pairs=[
                        dict(group_id="sg-fbfd1e3a", user_id="012345678901"),
                        dict(group_id="sg-00ec640f", user_id="012345678901"),
                    ],
                ),
            ],
        ),
        dict(
            ip_permissions=[
                dict(
                    ip_protocol="-1",
                    ip_ranges=[
                        dict(cidr_ip="192.0.2.0/24"),
                        dict(cidr_ip="198.51.100.0/24"),
                    ],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    user_id_group_pairs=[],
                ),
                dict(
                    ip_protocol="tcp",
                    ip_ranges=[],
                    ipv6_ranges=[
                        dict(cidr_ipv6="2001:DB8:4000::/34"),
                        dict(cidr_ipv6="2001:DB8:8000::/34"),
                    ],
                    prefix_list_ids=[],
                    user_id_group_pairs=[],
                ),
                dict(
                    from_port=38,
                    ip_protocol="tcp",
                    ip_ranges=[],
                    ipv6_ranges=[],
                    prefix_list_ids=[
                        dict(prefix_list_id="pl-0a5fccee"),
                        dict(prefix_list_id="pl-2263adef"),
                        dict(prefix_list_id="pl-65911ba9"),
                    ],
                    to_port=38,
                    user_id_group_pairs=[],
                ),
                dict(
                    from_port="22",
                    ip_ranges=[],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    to_port="22",
                    user_id_group_pairs=[
                        dict(group_id="sg-00ec640f", user_id="012345678901"),
                        dict(group_id="sg-3950599b", user_id="123456789012"),
                        dict(group_id="sg-fbfd1e3a", user_id="012345678901"),
                    ],
                ),
            ],
            ip_permissions_egress=[
                dict(
                    ip_protocol="-1",
                    ip_ranges=[
                        dict(cidr_ip="192.0.2.0/24"),
                        dict(cidr_ip="198.51.100.0/24"),
                    ],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    user_id_group_pairs=[],
                ),
                dict(
                    from_port=443,
                    ip_protocol="tcp",
                    ip_ranges=[],
                    ipv6_ranges=[],
                    prefix_list_ids=[],
                    to_port=443,
                    user_id_group_pairs=[
                        dict(group_id="sg-00ec640f", user_id="012345678901"),
                        dict(group_id="sg-fbfd1e3a", user_id="012345678901"),
                    ],
                ),
            ],
        ),
    ),
]


@pytest.mark.parametrize("group, expected", SORT_ORDER)
def test_sort_security_group(group, expected):
    assert ec2_security_group_module.sort_security_group(group) == expected

    # We shouldn't care about extra values lurking in the security group definition
    group["junk"] = sentinel.EXTRA_JUNK
    expected["junk"] = sentinel.EXTRA_JUNK
    assert ec2_security_group_module.sort_security_group(group) == expected


def test_get_rule_sort_key():
    # Random text, to try and ensure the content of the string doesn't affect the key returned
    dict_to_sort = dict(
        cidr_ip="MtY0d3Ps6ePsMM0zB18g",
        cidr_ipv6="ffbCwK2xhCsy8cyXqHuz",
        prefix_list_id="VXKCoW296XxIRiBrTUw8",
        group_id="RZpolpZ5wYPPpbqVo1Db",
        sentinel=sentinel.EXTRA_RULE_KEY,
    )

    # Walk through through the keys we use and check that they have the priority we expect
    for key_name in ["cidr_ip", "cidr_ipv6", "prefix_list_id", "group_id"]:
        assert ec2_security_group_module.get_rule_sort_key(dict_to_sort) == dict_to_sort[key_name]
        # Remove the current key so that the next time round another key will have priority
        dict_to_sort.pop(key_name)

    assert dict_to_sort == {"sentinel": sentinel.EXTRA_RULE_KEY}
    assert ec2_security_group_module.get_rule_sort_key(dict_to_sort) is None


def test_get_ip_permissions_sort_key():
    dict_to_sort = dict(
        ip_ranges=[
            dict(cidr_ip="198.51.100.0/24", original_index=0),
            dict(cidr_ip="192.0.2.0/24", original_index=1),
            dict(cidr_ip="203.0.113.0/24", original_index=2),
        ],
        ipv6_ranges=[
            dict(cidr_ipv6="2001:DB8:4000::/34", original_index=0),
            dict(cidr_ipv6="2001:DB8:0000::/34", original_index=1),
            dict(cidr_ipv6="2001:DB8:8000::/34", original_index=2),
        ],
        prefix_list_ids=[
            dict(prefix_list_id="pl-2263adef", original_index=0),
            dict(prefix_list_id="pl-0a5fccee", original_index=1),
            dict(prefix_list_id="pl-65911ba9", original_index=2),
        ],
        user_id_group_pairs=[
            dict(group_id="sg-3950599b", original_index=0),
            dict(group_id="sg-fbfd1e3a", original_index=1),
            dict(group_id="sg-00ec640f", original_index=2),
        ],
        sentinel=sentinel.EXTRA_RULE_KEY,
    )

    expected_keys = dict(
        ip_ranges="ipv4:192.0.2.0/24",
        ipv6_ranges="ipv6:2001:DB8:0000::/34",
        prefix_list_ids="pl:pl-0a5fccee",
        user_id_group_pairs="ugid:sg-00ec640f",
    )

    # Walk through through the keys we use and check that they have the priority we expect
    for key_name in ["ip_ranges", "ipv6_ranges", "prefix_list_ids", "user_id_group_pairs"]:
        sort_key = ec2_security_group_module.get_ip_permissions_sort_key(dict_to_sort)
        assert sort_key == expected_keys[key_name]
        # Remove the current key so that the next time round another key will have priority
        dict_to_sort.pop(key_name)

    assert dict_to_sort == {"sentinel": sentinel.EXTRA_RULE_KEY}
    assert ec2_security_group_module.get_ip_permissions_sort_key(dict_to_sort) is None

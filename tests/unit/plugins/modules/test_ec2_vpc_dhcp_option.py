# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_vpc_dhcp_option as dhcp_module

test_normalize_cases = [
    # Empty list
    ([], {}),
    # domain-name single value
    (
        [{"Key": "domain-name", "Values": [{"Value": "example.com"}]}],
        {"domain-name": ["example.com"]},
    ),
    # domain-name multiple values
    (
        [{"Key": "domain-name", "Values": [{"Value": "example.com"}, {"Value": "example.org"}]}],
        {"domain-name": ["example.com", "example.org"]},
    ),
    # domain-name-servers single value
    (
        [{"Key": "domain-name-servers", "Values": [{"Value": "8.8.8.8"}]}],
        {"domain-name-servers": ["8.8.8.8"]},
    ),
    # domain-name-servers multiple values
    (
        [{"Key": "domain-name-servers", "Values": [{"Value": "8.8.8.8"}, {"Value": "8.8.4.4"}]}],
        {"domain-name-servers": ["8.8.8.8", "8.8.4.4"]},
    ),
    # ntp-servers single value
    (
        [{"Key": "ntp-servers", "Values": [{"Value": "10.0.0.1"}]}],
        {"ntp-servers": ["10.0.0.1"]},
    ),
    # ntp-servers multiple values
    (
        [{"Key": "ntp-servers", "Values": [{"Value": "10.0.0.1"}, {"Value": "10.0.0.2"}]}],
        {"ntp-servers": ["10.0.0.1", "10.0.0.2"]},
    ),
    # netbios-name-servers single value
    (
        [{"Key": "netbios-name-servers", "Values": [{"Value": "10.20.0.1"}]}],
        {"netbios-name-servers": ["10.20.0.1"]},
    ),
    # netbios-name-servers multiple values
    (
        [{"Key": "netbios-name-servers", "Values": [{"Value": "10.20.0.1"}, {"Value": "10.20.0.2"}]}],
        {"netbios-name-servers": ["10.20.0.1", "10.20.0.2"]},
    ),
    # netbios-node-type as integer
    (
        [{"Key": "netbios-node-type", "Values": 2}],
        {"netbios-node-type": "2"},
    ),
    # netbios-node-type as list
    (
        [{"Key": "netbios-node-type", "Values": [{"Value": 2}]}],
        {"netbios-node-type": "2"},
    ),
    # Combined configuration
    (
        [
            {"Key": "domain-name", "Values": [{"Value": "us-west-2.compute.internal"}]},
            {"Key": "domain-name-servers", "Values": [{"Value": "AmazonProvidedDNS"}]},
            {"Key": "ntp-servers", "Values": [{"Value": "10.10.2.3"}, {"Value": "10.10.4.5"}]},
            {"Key": "netbios-name-servers", "Values": [{"Value": "10.20.2.3"}, {"Value": "10.20.4.5"}]},
            {"Key": "netbios-node-type", "Values": 2},
        ],
        {
            "domain-name": ["us-west-2.compute.internal"],
            "domain-name-servers": ["AmazonProvidedDNS"],
            "ntp-servers": ["10.10.2.3", "10.10.4.5"],
            "netbios-name-servers": ["10.20.2.3", "10.20.4.5"],
            "netbios-node-type": "2",
        },
    ),
]


@pytest.mark.parametrize("config_input,expected_output", test_normalize_cases)
def test_normalize_config(config_input, expected_output):
    result = dhcp_module.normalize_ec2_vpc_dhcp_config(config_input)
    assert result == expected_output

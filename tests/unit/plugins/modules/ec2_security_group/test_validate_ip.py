# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import warnings
from unittest.mock import MagicMock
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.modules.ec2_security_group as ec2_security_group_module


@pytest.fixture(name="aws_module")
def fixture_aws_module():
    aws_module = MagicMock()
    aws_module.warn = warnings.warn
    return aws_module


@pytest.fixture(name="ec2_security_group")
def fixture_ec2_security_group(monkeypatch):
    # monkey patches various ec2_security_group module functions, we'll separately test the operation of
    # these functions, we just care that it's passing the results into the right place in the
    # instance spec.
    monkeypatch.setattr(ec2_security_group_module, "current_account_id", sentinel.CURRENT_ACCOUNT_ID)
    return ec2_security_group_module


IPS_GOOD = [
    (
        "192.0.2.2",
        "192.0.2.2",
    ),
    (
        "192.0.2.1/32",
        "192.0.2.1/32",
    ),
    (
        "192.0.2.1/255.255.255.255",
        "192.0.2.1/32",
    ),
    (
        "192.0.2.0/24",
        "192.0.2.0/24",
    ),
    (
        "192.0.2.0/255.255.255.255",
        "192.0.2.0/32",
    ),
    (
        "2001:db8::1/128",
        "2001:db8::1/128",
    ),
    (
        "2001:db8::/32",
        "2001:db8::/32",
    ),
    ("2001:db8:fe80:b897:8990:8a7c:99bf:323d/128", "2001:db8:fe80:b897:8990:8a7c:99bf:323d/128"),
]

IPS_WARN = [
    ("192.0.2.1/24", "192.0.2.0/24", "One of your CIDR addresses"),
    ("2001:DB8::1/32", "2001:DB8::/32", "One of your IPv6 CIDR addresses"),
    ("2001:db8:fe80:b897:8990:8a7c:99bf:323d/64", "2001:db8:fe80:b897::/64", "One of your IPv6 CIDR addresses"),
]


@pytest.mark.parametrize("ip,expected", IPS_GOOD)
def test_validate_ip_no_warn(ec2_security_group, aws_module, ip, expected):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ec2_security_group.validate_ip(aws_module, ip)

    assert result == expected


@pytest.mark.parametrize("ip,expected,warn_msg", IPS_WARN)
def test_validate_ip_warn(ec2_security_group, aws_module, ip, warn_msg, expected):
    with pytest.warns(UserWarning, match=warn_msg) as recorded:
        result = ec2_security_group.validate_ip(aws_module, ip)

    assert len(recorded) == 1
    assert result == expected

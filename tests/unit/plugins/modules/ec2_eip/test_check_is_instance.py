# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_eip

EXAMPLE_DATA = [
    (
        None,
        True,
        False,
    ),
    (
        None,
        False,
        False,
    ),
    (
        "",
        True,
        False,
    ),
    (
        "",
        False,
        False,
    ),
    (
        "i-123456789",
        True,
        True,
    ),
    (
        "i-123456789",
        False,
        True,
    ),
    (
        "eni-123456789",
        True,
        False,
    ),
    (
        "junk",
        True,
        False,
    ),
    (
        "junk",
        False,
        False,
    ),
]


def test_check_is_instance_needs_in_vpc():
    with pytest.raises(ec2_eip.EipError):
        ec2_eip.check_is_instance("eni-123456789", False)


@pytest.mark.parametrize("device,in_vpc,expected", EXAMPLE_DATA)
def test_check_is_instance(device, in_vpc, expected):
    result = ec2_eip.check_is_instance(device, in_vpc)
    assert result is expected

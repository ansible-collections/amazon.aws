# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

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


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.params = {}
    module.fail_json.side_effect = SystemExit(1)
    return module


def test_check_is_instance_needs_in_vpc(ansible_module):
    with pytest.raises(SystemExit):
        ansible_module.params.update({"device_id": "eni-123456789", "in_vpc": False})
        ec2_eip.check_is_instance(ansible_module)


@pytest.mark.parametrize("device,in_vpc,expected", EXAMPLE_DATA)
def test_check_is_instance(ansible_module, device, in_vpc, expected):
    ansible_module.params.update({"device_id": device, "in_vpc": in_vpc})
    result = ec2_eip.check_is_instance(ansible_module)
    assert result is expected

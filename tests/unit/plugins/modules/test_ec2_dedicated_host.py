# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_dedicated_host

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_dedicated_host"


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.params = {}
    module.exit_json = MagicMock()
    module.fail_json = MagicMock()
    module.fail_json.side_effect = SystemExit(1)
    return module


@pytest.mark.parametrize(
    "dedicated_hosts,expected",
    [
        ([], None),
        (
            [{"host_id": "h-01ca0a554a7f8787b", "mac_os_latest_supported_versions": ["15.3", "14.7.3", "13.7.3"]}],
            {"host_id": "h-01ca0a554a7f8787b", "mac_os_latest_supported_versions": ["15.3", "14.7.3", "13.7.3"]},
        ),
    ],
)
@patch(module_name + ".describe_ec2_dedicated_hosts")
def test_get_ec2_dedicated_host_with_lookup_host_id(
    m_describe_ec2_dedicated_hosts, ansible_module, dedicated_hosts, expected
):
    ansible_module.params = {"host_id": "h-012345", "lookup": "host_id"}
    client = MagicMock()
    m_describe_ec2_dedicated_hosts.return_value = dedicated_hosts

    assert ec2_dedicated_host.get_ec2_dedicated_host(client, ansible_module) == expected
    expected_params = {
        "Filters": [{"Name": "state", "Values": ["available", "under-assessment", "permanent-failure"]}],
        "HostIds": ["h-012345"],
    }
    m_describe_ec2_dedicated_hosts.assert_called_once_with(client, **expected_params)


@pytest.mark.parametrize(
    "dedicated_hosts,expected",
    [
        ([], None),
        ([{"host_id": "host-1"}, {"host_id": "host-2", "Tags": {"foo": "bar"}}], None),
        ([{"host_id": "host-1"}, {"host_id": "host-2", "Tags": {"phase": "test"}}], None),
        (
            [
                {"host_id": "host-1"},
                {"host_id": "host-2", "Tags": {"foo": "bar", "phase": "test", "session": "active"}},
            ],
            None,
        ),
        (
            [{"host_id": "host-1"}, {"host_id": "host-2", "Tags": {"foo": "bar", "phase": "test"}}],
            {"host_id": "host-2", "Tags": {"foo": "bar", "phase": "test"}},
        ),
        (
            [
                {"host_id": "host-1", "Tags": {"foo": "bar", "phase": "test"}},
                {"host_id": "host-2", "Tags": {"foo": "bar", "phase": "test"}},
            ],
            [
                {"host_id": "host-1", "Tags": {"foo": "bar", "phase": "test"}},
                {"host_id": "host-2", "Tags": {"foo": "bar", "phase": "test"}},
            ],
        ),
    ],
)
@patch(module_name + ".boto3_tag_list_to_ansible_dict")
@patch(module_name + ".describe_ec2_dedicated_hosts")
def test_get_ec2_dedicated_host_with_lookup_tag(
    m_describe_ec2_dedicated_hosts, m_boto3_tag_list_to_ansible_dict, ansible_module, dedicated_hosts, expected
):
    ansible_module.params = {"host_id": "h-012345", "lookup": "tag", "tags": {"foo": "bar", "phase": "test"}}
    client = MagicMock()
    m_describe_ec2_dedicated_hosts.return_value = dedicated_hosts
    m_boto3_tag_list_to_ansible_dict.side_effect = lambda x: x

    if expected and isinstance(expected, list) and len(expected) > 1:
        with pytest.raises(SystemExit):
            ec2_dedicated_host.get_ec2_dedicated_host(client, ansible_module)
        ansible_module.fail_json.assert_called_once_with(
            msg=f"Tags provided do not identify a unique dedicated host ({len(expected)} found)."
        )
    else:
        assert ec2_dedicated_host.get_ec2_dedicated_host(client, ansible_module) == expected
    expected_params = {
        "Filters": [{"Name": "state", "Values": ["available", "under-assessment", "permanent-failure"]}],
    }
    m_describe_ec2_dedicated_hosts.assert_called_once_with(client, **expected_params)

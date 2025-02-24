# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleError


@pytest.mark.parametrize("executable_path_exists", [True, False])
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.os")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.to_bytes")
def test_get_executable_user_provided(m_to_bytes, m_os, connection_aws_ssm, executable_path_exists):
    ssm_plugin = MagicMock()
    connection_aws_ssm.get_option.return_value = ssm_plugin
    b_ssm_plugin = MagicMock()
    m_to_bytes.return_value = b_ssm_plugin
    m_os.path = MagicMock()
    m_os.path.exists = MagicMock()
    m_os.path.exists.return_value = executable_path_exists

    if executable_path_exists:
        assert ssm_plugin == connection_aws_ssm.get_executable()
    else:
        with pytest.raises(AnsibleError) as exc_info:
            connection_aws_ssm.get_executable()
        assert str(exc_info.value) == f"failed to find the executable specified {ssm_plugin}."

    connection_aws_ssm.get_option.assert_called_once_with("plugin")
    m_to_bytes.assert_called_once_with(ssm_plugin, errors="surrogate_or_strict")
    m_os.path.exists.assert_called_once_with(b_ssm_plugin)


@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.get_bin_path")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.os")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.to_bytes")
def test_get_executable_default_value_exists(m_to_bytes, m_os, m_get_bin_path, connection_aws_ssm):
    connection_aws_ssm.get_option.return_value = None
    b_ssm_plugin = MagicMock()
    m_to_bytes.return_value = b_ssm_plugin
    m_os.path = MagicMock()
    m_os.path.exists = MagicMock()
    m_os.path.exists.return_value = True

    ssm_plugin_default = "/usr/local/bin/session-manager-plugin"

    assert ssm_plugin_default == connection_aws_ssm.get_executable()

    connection_aws_ssm.get_option.assert_called_once_with("plugin")
    m_to_bytes.assert_called_once_with(ssm_plugin_default, errors="surrogate_or_strict")
    m_os.path.exists.assert_called_once_with(b_ssm_plugin)
    m_get_bin_path.assert_not_called()


@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.get_bin_path")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.os")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.to_bytes")
def test_get_executable_default_from_path(m_to_bytes, m_os, m_get_bin_path, connection_aws_ssm):
    connection_aws_ssm.get_option.return_value = None
    b_ssm_plugin = MagicMock()
    m_to_bytes.return_value = b_ssm_plugin
    m_os.path = MagicMock()
    m_os.path.exists = MagicMock()
    m_os.path.exists.return_value = False
    ssm_plugin = MagicMock()
    m_get_bin_path.return_value = ssm_plugin

    ssm_plugin_default = "/usr/local/bin/session-manager-plugin"

    assert ssm_plugin == connection_aws_ssm.get_executable()

    connection_aws_ssm.get_option.assert_called_once_with("plugin")
    m_to_bytes.assert_called_once_with(ssm_plugin_default, errors="surrogate_or_strict")
    m_os.path.exists.assert_called_once_with(b_ssm_plugin)
    m_get_bin_path.assert_called_once_with("session-manager-plugin")


@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.get_bin_path")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.os")
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.to_bytes")
def test_get_executable_default_missing_from_path(m_to_bytes, m_os, m_get_bin_path, connection_aws_ssm):
    connection_aws_ssm.get_option.return_value = None
    b_ssm_plugin = MagicMock()
    m_to_bytes.return_value = b_ssm_plugin
    m_os.path = MagicMock()
    m_os.path.exists = MagicMock()
    m_os.path.exists.return_value = False
    m_get_bin_path.side_effect = ValueError("executable missing from PATH")

    ssm_plugin_default = "/usr/local/bin/session-manager-plugin"
    with pytest.raises(AnsibleError) as exc_info:
        connection_aws_ssm.get_executable()
    assert str(exc_info.value) == "executable missing from PATH"

    connection_aws_ssm.get_option.assert_called_once_with("plugin")
    m_to_bytes.assert_called_once_with(ssm_plugin_default, errors="surrogate_or_strict")
    m_os.path.exists.assert_called_once_with(b_ssm_plugin)
    m_get_bin_path.assert_called_once_with("session-manager-plugin")

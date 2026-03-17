# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import sentinel

import pytest

from ansible.errors import AnsibleError

import ansible_collections.amazon.aws.plugins.plugin_utils.base as utils_base


class TestAWSPluginBase:
    @pytest.mark.parametrize("level", ["invalid value", -1, 0, 7])
    @patch("ansible_collections.amazon.aws.plugins.plugin_utils.base.display")
    def test_v_log_invalid_level(self, mock_display, level):
        """Test that v_log raises an error for invalid verbosity levels"""
        plugin = utils_base.AWSPluginBase()
        with pytest.raises(AnsibleError) as exc_info:
            plugin.v_log(level, "test message")
        assert str(exc_info.value) == f"Invalid verbosity level: {level}"
        for method in ("v", "vv", "vvv", "vvvv", "vvvvv", "vvvvvv"):
            getattr(mock_display, method).assert_not_called()

    @pytest.mark.parametrize("host", [None, "test-host"])
    @pytest.mark.parametrize(
        "level,method",
        [
            (1, "v"),
            (2, "vv"),
            (3, "vvv"),
            (4, "vvvv"),
            (5, "vvvvv"),
            (6, "vvvvvv"),
        ],
    )
    @patch("ansible_collections.amazon.aws.plugins.plugin_utils.base.display")
    def test_v_log(self, mock_display, host, level, method):
        """Test that v_log calls the correct display method with correct arguments"""
        plugin = utils_base.AWSPluginBase()
        message = "unit testing plugin base v_log"

        # Test with explicit host parameter
        plugin.v_log(level, message, host=host)
        args = {}
        if host:
            args["host"] = host
        getattr(mock_display, method).assert_called_once_with(message, **args)

    @patch("ansible_collections.amazon.aws.plugins.plugin_utils.base.display")
    def test_v_log_uses_self_host(self, mock_display):
        """Test that v_log uses self.host when no host parameter is provided"""
        plugin = utils_base.AWSPluginBase()
        plugin.host = "auto-detected-host"
        message = "test message"

        plugin.v_log(2, message)
        mock_display.vv.assert_called_once_with(message, host="auto-detected-host")

    @patch("ansible_collections.amazon.aws.plugins.plugin_utils.base.display")
    def test_v_log_explicit_host_overrides_self_host(self, mock_display):
        """Test that explicit host parameter overrides self.host"""
        plugin = utils_base.AWSPluginBase()
        plugin.host = "auto-detected-host"
        message = "test message"

        plugin.v_log(2, message, host="explicit-host")
        mock_display.vv.assert_called_once_with(message, host="explicit-host")

    @patch("ansible_collections.amazon.aws.plugins.plugin_utils.base.display")
    def test_v_log_no_host_available(self, mock_display):
        """Test that v_log works when no host is available"""
        plugin = utils_base.AWSPluginBase()
        # Plugin doesn't have self.host attribute at all
        message = "test message"

        plugin.v_log(3, message)
        mock_display.vvv.assert_called_once_with(message)

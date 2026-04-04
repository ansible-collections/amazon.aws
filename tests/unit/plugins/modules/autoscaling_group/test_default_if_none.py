# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.modules.autoscaling_group import _default_if_none


class TestDefaultIfNone:
    """Test suite for _default_if_none helper function."""

    def test_returns_value_when_not_none(self):
        """Test that function returns the value when it's not None."""
        assert _default_if_none(5, 10) == 5
        assert _default_if_none("hello", "world") == "hello"
        assert _default_if_none(0, 10) == 0
        assert _default_if_none(False, True) is False
        assert _default_if_none([], ["default"]) == []

    def test_returns_default_when_none(self):
        """Test that function returns default when value is None."""
        assert _default_if_none(None, 10) == 10
        assert _default_if_none(None, "default") == "default"
        assert _default_if_none(None, []) == []
        assert _default_if_none(None, {}) == {}
        assert _default_if_none(None, False) is False

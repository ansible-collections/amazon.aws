# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


@pytest.fixture(name="ec2_instance")
def fixture_ec2_instance():
    module = MagicMock()
    return ec2_metadata_facts.Ec2Metadata(module)


def test_fix_colons(ec2_instance):
    """Test that colons are replaced with underscores."""
    data = {"key:with:colons": "value1", "normal_key": "value2"}
    result = ec2_instance.fix_invalid_varnames(data)

    assert "key_with_colons" in result
    assert result["key_with_colons"] == "value1"
    assert "normal_key" in result
    assert result["normal_key"] == "value2"
    assert "key:with:colons" not in result


def test_fix_hyphens(ec2_instance):
    """Test that hyphens are replaced with underscores."""
    data = {"key-with-hyphens": "value1", "another-key": "value2"}
    result = ec2_instance.fix_invalid_varnames(data)

    assert "key_with_hyphens" in result
    assert result["key_with_hyphens"] == "value1"
    assert "another_key" in result
    assert result["another_key"] == "value2"
    assert "key-with-hyphens" not in result
    assert "another-key" not in result


def test_fix_mixed_characters(ec2_instance):
    """Test that both colons and hyphens are replaced."""
    data = {"key:with-both": "value1", "another-key:here": "value2"}
    result = ec2_instance.fix_invalid_varnames(data)

    assert "key_with_both" in result
    assert result["key_with_both"] == "value1"
    assert "another_key_here" in result
    assert result["another_key_here"] == "value2"


def test_no_changes_needed(ec2_instance):
    """Test that valid keys are unchanged."""
    data = {"valid_key": "value1", "another_valid_key": "value2"}
    result = ec2_instance.fix_invalid_varnames(data)

    assert result == data
    assert "valid_key" in result
    assert "another_valid_key" in result


def test_empty_dict(ec2_instance):
    """Test that empty dict is handled correctly."""
    data = {}
    result = ec2_instance.fix_invalid_varnames(data)

    assert result == {}


def test_does_not_modify_original(ec2_instance):
    """Test that the original dict is not modified."""
    data = {"key:with:colons": "value"}
    result = ec2_instance.fix_invalid_varnames(data)

    # Original should still have the colon
    assert "key:with:colons" in data
    # Result should have underscore
    assert "key_with_colons" in result

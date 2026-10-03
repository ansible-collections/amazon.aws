# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch
from unittest.mock import sentinel

import pytest

import ansible.plugins.inventory as base_inventory

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory


@patch("ansible.plugins.inventory.BaseInventoryPlugin.parse", MagicMock)
def test_parse(monkeypatch):
    require_aws_sdk = MagicMock(name="require_aws_sdk")
    require_aws_sdk.return_value = sentinel.RETURNED_SDK
    config_data = MagicMock(name="_read_config_data")
    config_data.return_value = sentinel.RETURNED_OPTIONS
    frozen_credentials = MagicMock(name="_set_frozen_credentials")
    frozen_credentials.return_value = sentinel.RETURNED_CREDENTIALS

    inventory_plugin = utils_inventory.AWSInventoryBase()
    monkeypatch.setattr(inventory_plugin, "require_aws_sdk", require_aws_sdk)
    monkeypatch.setattr(inventory_plugin, "_read_config_data", config_data)
    monkeypatch.setattr(inventory_plugin, "_set_frozen_credentials", frozen_credentials)

    inventory_plugin.parse(sentinel.PARAM_INVENTORY, sentinel.PARAM_LOADER, sentinel.PARAM_PATH)
    assert require_aws_sdk.call_args == call(botocore_version=None, boto3_version=None)
    assert config_data.call_args == call(sentinel.PARAM_PATH)
    assert frozen_credentials.call_args == call()


@pytest.mark.parametrize(
    "filename,result",
    [
        ("inventory_aws_ec2.yml", True),
        ("inventory_aws_ec2.yaml", True),
        ("inventory_aws_EC2.yaml", False),
        ("inventory_Aws_ec2.yaml", False),
        ("aws_ec2_inventory.yml", False),
        ("aws_ec2.yml_inventory", False),
        ("aws_ec2.yml", True),
        ("aws_ec2.yaml", True),
    ],
)
def test_inventory_verify_file(monkeypatch, filename, result):
    base_verify = MagicMock(name="verify_file")
    monkeypatch.setattr(base_inventory.BaseInventoryPlugin, "verify_file", base_verify)
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # With INVENTORY_FILE_SUFFIXES not set, we should simply pass through the return from the base
    base_verify.return_value = True
    assert inventory_plugin.verify_file(filename) is True
    base_verify.return_value = False
    assert inventory_plugin.verify_file(filename) is False

    # With INVENTORY_FILE_SUFFIXES set, we only return True of the base is good *and* the filename matches
    inventory_plugin.INVENTORY_FILE_SUFFIXES = ("aws_ec2.yml", "aws_ec2.yaml")
    base_verify.return_value = True
    assert inventory_plugin.verify_file(filename) is result
    base_verify.return_value = False
    assert inventory_plugin.verify_file(filename) is False


@pytest.fixture(name="aws_inventory_base")
def fixture_aws_inventory_base():
    inventory = utils_inventory.AWSInventoryBase()
    inventory._options = {}
    inventory.templar = None
    return inventory


def test_inventory_get_options_without_templar(aws_inventory_base, mocker):
    """Test get_options() returns TemplatedOptions that can retrieve values."""
    inventory_options = {
        "access_key": "amazon_ansible_access_key_001",
        "region": "us-east-2",
    }
    aws_inventory_base._options = inventory_options

    super_get_options_patch = mocker.patch(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory.BaseInventoryPlugin.get_options"
    )
    super_get_options_patch.return_value = aws_inventory_base._options

    options = aws_inventory_base.get_options()

    # Verify it returns TemplatedOptions wrapper
    assert isinstance(options, utils_inventory.AWSInventoryBase.TemplatedOptions)

    # Verify basic get() works
    assert options.get("access_key") == "amazon_ansible_access_key_001"
    assert options.get("region") == "us-east-2"
    assert options.get("missing_key") is None


def test_inventory_get_options_with_templar(aws_inventory_base, mocker):
    """Test get_options() and get_option() integrate with templar."""
    inventory_options = {
        "access_key": "plain_value",
        "region": "{{ templated_region }}",
    }
    aws_inventory_base._options = inventory_options

    # Mock templar
    mock_templar = MagicMock(name="templar")
    mock_templar.is_template.side_effect = lambda x: "{{" in str(x) if x else False
    mock_templar.template.return_value = "us-east-1"
    aws_inventory_base.templar = mock_templar

    super_get_options_patch = mocker.patch(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory.BaseInventoryPlugin.get_options"
    )
    super_get_options_patch.return_value = aws_inventory_base._options

    super_get_option_patch = mocker.patch(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory.BaseInventoryPlugin.get_option"
    )
    super_get_option_patch.side_effect = lambda x, hostvars=None: aws_inventory_base._options.get(x)

    # Test get_options() returns TemplatedOptions that uses templar
    options = aws_inventory_base.get_options()
    assert isinstance(options, utils_inventory.AWSInventoryBase.TemplatedOptions)
    assert options.get("region") == "us-east-1"

    # Verify templar was called
    assert mock_templar.template.called

    # Test get_option() also uses templar
    assert aws_inventory_base.get_option("region") == "us-east-1"


def test_cache_format_version_default():
    """Test that CACHE_FORMAT_VERSION defaults to 1."""
    inventory = utils_inventory.AWSInventoryBase()
    assert inventory.CACHE_FORMAT_VERSION == 1


def test_update_cached_result_includes_version(aws_inventory_base, mocker):
    """Test that update_cached_result wraps data with version metadata."""
    aws_inventory_base._cache = {}
    aws_inventory_base._options = {"cache": True}

    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    test_data = {"hosts": ["host1", "host2"], "vars": {"key": "value"}}
    aws_inventory_base.update_cached_result("test_path", cache=False, result=test_data)

    assert "test_key" in aws_inventory_base._cache
    cached_value = aws_inventory_base._cache["test_key"]
    assert isinstance(cached_value, dict)
    assert "_cache_format_version" in cached_value
    assert cached_value["_cache_format_version"] == 1
    assert "_data" in cached_value
    assert cached_value["_data"] == test_data


def test_get_cached_result_validates_version(aws_inventory_base, mocker):
    """Test that get_cached_result invalidates cache when version doesn't match."""
    aws_inventory_base._options = {"cache": True}
    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    # Test with matching version
    test_data = {"hosts": ["host1"]}
    aws_inventory_base._cache = {"test_key": {"_cache_format_version": 1, "_data": test_data}}
    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is True
    assert result == test_data

    # Test with mismatched version
    aws_inventory_base._cache = {"test_key": {"_cache_format_version": 2, "_data": test_data}}
    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is False
    assert result is None


def test_get_cached_result_assumes_version_1_for_legacy_cache(aws_inventory_base, mocker):
    """Test that cache without version metadata is treated as version 1."""
    aws_inventory_base._options = {"cache": True}
    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    # Legacy cache without version metadata (should be treated as version 1)
    legacy_data = {"hosts": ["host1"], "vars": {"key": "value"}}
    aws_inventory_base._cache = {"test_key": legacy_data}

    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is True
    assert result == legacy_data

    # Legacy dict cache with _meta but no version (should default to version 1)
    legacy_formatted = {"_meta": {"hostvars": {}}, "aws_rds": {"hosts": []}}
    aws_inventory_base._cache = {"test_key": legacy_formatted}

    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is True
    assert result == legacy_formatted


def test_get_cached_result_invalidates_legacy_cache_for_v2_plugin(aws_inventory_base, mocker):
    """Test that legacy v1 cache is invalidated when plugin expects v2."""
    aws_inventory_base.CACHE_FORMAT_VERSION = 2
    aws_inventory_base._options = {"cache": True}
    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    # Legacy cache (implicitly v1) should be invalidated for v2 plugin
    legacy_data = {"_meta": {"hostvars": {}}, "aws_rds": {"hosts": []}}
    aws_inventory_base._cache = {"test_key": legacy_data}

    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is False
    assert result is None


def test_update_cached_result_respects_existing_cache(aws_inventory_base, mocker):
    """Test that update_cached_result doesn't overwrite existing cache when cache=True."""
    aws_inventory_base._options = {"cache": True}
    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    existing_data = {"_cache_format_version": 1, "_data": {"existing": "data"}}
    aws_inventory_base._cache = {"test_key": existing_data}

    new_data = {"new": "data"}
    aws_inventory_base.update_cached_result("test_path", cache=True, result=new_data)

    # Should not update when cache=True and key exists
    assert aws_inventory_base._cache["test_key"] == existing_data


def test_get_cached_result_non_dict_cache_v1_plugin(aws_inventory_base, mocker):
    """Test that non-dict legacy cache works with version 1 plugin."""
    aws_inventory_base.CACHE_FORMAT_VERSION = 1
    aws_inventory_base._options = {"cache": True}
    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    # Non-dict cache (e.g., plain list) should work with v1 plugin
    legacy_list_cache = ["host1", "host2", "host3"]
    aws_inventory_base._cache = {"test_key": legacy_list_cache}

    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is True
    assert result == legacy_list_cache


def test_get_cached_result_non_dict_cache_v2_plugin(aws_inventory_base, mocker):
    """Test that non-dict legacy cache is invalidated for version 2+ plugin."""
    aws_inventory_base.CACHE_FORMAT_VERSION = 2
    aws_inventory_base._options = {"cache": True}
    mocker.patch.object(aws_inventory_base, "get_cache_key", return_value="test_key")

    # Non-dict cache should be invalidated when plugin expects v2
    legacy_list_cache = ["host1", "host2", "host3"]
    aws_inventory_base._cache = {"test_key": legacy_list_cache}

    result_was_cached, result = aws_inventory_base.get_cached_result("test_path", cache=True)
    assert result_was_cached is False
    assert result is None

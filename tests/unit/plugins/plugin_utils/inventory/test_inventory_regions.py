# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call

import botocore.exceptions
import pytest

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory

# Note for Ansible Core < 2.19:
# Prior to 2.19 templar isn't available to the plugin until we start through the "parse" run (which
# we're not # doing as part of these tests).  This means we need to patch it in.  In 2.19 it
# becomes a cached property, and while there won't be any options available to pull data from, it
# is at least available for self.region → get_aws_region() → get_options() → self.templar


def test_boto3_regions_with_user_provided_regions(monkeypatch):
    """Test _boto3_regions when user provides regions option."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    user_regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = user_regions
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    # _describe_regions should not be called if user provides regions
    mock_describe = MagicMock(name="_describe_regions")
    monkeypatch.setattr(inventory_plugin, "_describe_regions", mock_describe)

    result = inventory_plugin._boto3_regions("rds")

    assert result == user_regions
    assert mock_get_option.call_args == call("regions")
    assert mock_describe.call_count == 0


def test_boto3_regions_service_describe_success(monkeypatch):
    """Test _boto3_regions when describe_regions succeeds for requested service."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = None
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    service_regions = ["us-east-1", "us-west-2"]
    mock_describe = MagicMock(name="_describe_regions")
    mock_describe.return_value = service_regions
    monkeypatch.setattr(inventory_plugin, "_describe_regions", mock_describe)

    result = inventory_plugin._boto3_regions("rds")

    assert result == service_regions
    # Should only call describe_regions once for the requested service
    assert mock_describe.call_count == 1
    assert mock_describe.call_args == call("rds")


def test_boto3_regions_fallback_to_ec2(monkeypatch):
    """Test _boto3_regions falls back to ec2 when service describe fails."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = None
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    ec2_regions = ["us-east-1", "us-west-1", "eu-west-1"]
    mock_describe = MagicMock(name="_describe_regions")
    # First call (rds) returns None, second call (ec2) returns regions
    mock_describe.side_effect = [None, ec2_regions]
    monkeypatch.setattr(inventory_plugin, "_describe_regions", mock_describe)

    result = inventory_plugin._boto3_regions("rds")

    assert result == ec2_regions
    # Should call describe_regions twice: first for rds, then for ec2
    assert mock_describe.call_count == 2
    assert mock_describe.call_args_list == [call("rds"), call("ec2")]


def test_boto3_regions_ec2_service_no_duplicate(monkeypatch):
    """Test _boto3_regions doesn't try ec2 twice when service is ec2."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = None
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    ec2_regions = ["us-east-1", "us-west-2"]
    mock_describe = MagicMock(name="_describe_regions")
    mock_describe.return_value = ec2_regions
    monkeypatch.setattr(inventory_plugin, "_describe_regions", mock_describe)

    result = inventory_plugin._boto3_regions("ec2")

    assert result == ec2_regions
    # Should only call describe_regions once for ec2
    assert mock_describe.call_count == 1
    assert mock_describe.call_args == call("ec2")


def test_boto3_regions_fallback_to_boto3_session(monkeypatch):
    """Test _boto3_regions falls back to boto3 session when describe fails."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = None
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    # Both describe_regions calls return None
    mock_describe = MagicMock(name="_describe_regions")
    mock_describe.return_value = None
    monkeypatch.setattr(inventory_plugin, "_describe_regions", mock_describe)

    # Mock the boto3 session
    boto3_regions = ["us-east-1", "us-west-2", "eu-central-1"]
    mock_session = MagicMock(name="boto3_session")
    mock_session.get_available_regions.return_value = boto3_regions

    mock_boto3_session_func = MagicMock(name="_boto3_session")
    mock_boto3_session_func.return_value = mock_session
    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory._boto3_session",
        mock_boto3_session_func,
    )

    result = inventory_plugin._boto3_regions("rds")

    assert result == boto3_regions
    # Should try describe_regions for both rds and ec2
    assert mock_describe.call_count == 2
    # Should call boto3 session with profile
    assert mock_boto3_session_func.call_count == 1
    assert mock_session.get_available_regions.call_args == call("rds")


def test_boto3_regions_no_regions_available(monkeypatch):
    """Test _boto3_regions fails when no regions available from any source."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = None
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    # All describe_regions calls return None
    mock_describe = MagicMock(name="_describe_regions")
    mock_describe.return_value = None
    monkeypatch.setattr(inventory_plugin, "_describe_regions", mock_describe)

    # boto3 session also returns empty list
    mock_session = MagicMock(name="boto3_session")
    mock_session.get_available_regions.return_value = []

    mock_boto3_session_func = MagicMock(name="_boto3_session")
    mock_boto3_session_func.return_value = mock_session
    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory._boto3_session",
        mock_boto3_session_func,
    )

    mock_fail_aws = MagicMock(name="fail_aws")
    mock_fail_aws.side_effect = Exception("fail_aws called")
    monkeypatch.setattr(inventory_plugin, "fail_aws", mock_fail_aws)

    with pytest.raises(Exception, match="fail_aws called"):
        inventory_plugin._boto3_regions("rds")

    # Verify fail_aws was called with appropriate message
    assert mock_fail_aws.call_count == 1
    assert "Unable to get regions list" in mock_fail_aws.call_args[0][0]
    assert "regions" in mock_fail_aws.call_args[0][0]


def test_describe_regions_success(monkeypatch):
    """Test _describe_regions successfully returns regions."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # Mock the region property
    monkeypatch.setattr(type(inventory_plugin), "region", property(lambda self: "us-east-1"))

    mock_client = MagicMock(name="ec2_client")
    mock_client.describe_regions.return_value = {
        "Regions": [
            {"RegionName": "us-east-1"},
            {"RegionName": "us-west-1"},
            {"RegionName": "eu-west-1"},
        ]
    }

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    result = inventory_plugin._describe_regions("ec2")

    assert result == ["us-east-1", "us-west-1", "eu-west-1"]
    assert mock_get_client.call_args == call("ec2", region="us-east-1")
    assert mock_client.describe_regions.call_count == 1


def test_describe_regions_no_region_uses_default(monkeypatch):
    """Test _describe_regions uses us-east-1 when no region set."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # Mock the region property to return None
    monkeypatch.setattr(type(inventory_plugin), "region", property(lambda self: None))

    mock_client = MagicMock(name="ec2_client")
    mock_client.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    result = inventory_plugin._describe_regions("ec2")

    assert result == ["us-east-1"]
    # Should use us-east-1 as default when region is None
    assert mock_get_client.call_args == call("ec2", region="us-east-1")


def test_describe_regions_attribute_error(monkeypatch):
    """Test _describe_regions returns None on AttributeError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_client = MagicMock(name="service_client")
    # Service doesn't support describe_regions
    mock_client.describe_regions.side_effect = AttributeError("no describe_regions")

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    result = inventory_plugin._describe_regions("lambda")

    assert result is None


def test_describe_regions_unauthorized_operation(monkeypatch):
    """Test _describe_regions warns on UnauthorizedOperation."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # Mock the region property
    monkeypatch.setattr(type(inventory_plugin), "region", property(lambda self: None))

    test_error = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "UnauthorizedOperation"}}, operation_name="DescribeRegions"
    )

    mock_client = MagicMock(name="ec2_client")
    mock_client.describe_regions.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_warn = MagicMock(name="warn")
    monkeypatch.setattr(inventory_plugin, "warn", mock_warn)

    result = inventory_plugin._describe_regions("ec2")

    assert result is None
    assert mock_warn.call_count == 1
    assert "UnauthorizedOperation" in mock_warn.call_args[0][0]
    assert "ec2" in mock_warn.call_args[0][0]


def test_describe_regions_no_region_error(monkeypatch):
    """Test _describe_regions warns on NoRegionError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # Mock the region property
    monkeypatch.setattr(type(inventory_plugin), "region", property(lambda self: None))

    test_error = botocore.exceptions.NoRegionError()

    mock_client = MagicMock(name="ec2_client")
    mock_client.describe_regions.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_warn = MagicMock(name="warn")
    monkeypatch.setattr(inventory_plugin, "warn", mock_warn)

    result = inventory_plugin._describe_regions("ec2")

    assert result is None
    assert mock_warn.call_count == 1
    assert "NoRegionError" in mock_warn.call_args[0][0]


def test_describe_regions_client_error(monkeypatch):
    """Test _describe_regions warns on generic ClientError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # Mock the region property
    monkeypatch.setattr(type(inventory_plugin), "region", property(lambda self: None))

    test_error = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Not authorized"}},
        operation_name="DescribeRegions",
    )

    mock_client = MagicMock(name="ec2_client")
    mock_client.describe_regions.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_warn = MagicMock(name="warn")
    monkeypatch.setattr(inventory_plugin, "warn", mock_warn)

    result = inventory_plugin._describe_regions("ec2")

    assert result is None
    assert mock_warn.call_count == 1
    assert "Unexpected error" in mock_warn.call_args[0][0]
    assert "ec2" in mock_warn.call_args[0][0]


def test_describe_regions_botocore_error(monkeypatch):
    """Test _describe_regions warns on BotoCoreError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # Mock the region property
    monkeypatch.setattr(type(inventory_plugin), "region", property(lambda self: None))

    test_error = botocore.exceptions.BotoCoreError()

    mock_client = MagicMock(name="ec2_client")
    mock_client.describe_regions.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_warn = MagicMock(name="warn")
    monkeypatch.setattr(inventory_plugin, "warn", mock_warn)

    result = inventory_plugin._describe_regions("ec2")

    assert result is None
    assert mock_warn.call_count == 1
    assert "Unexpected error" in mock_warn.call_args[0][0]


def test_describe_regions_empty_response(monkeypatch):
    """Test _describe_regions returns None when response has no regions."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_client = MagicMock(name="ec2_client")
    # Empty Regions list
    mock_client.describe_regions.return_value = {"Regions": []}

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    result = inventory_plugin._describe_regions("ec2")

    assert result is None

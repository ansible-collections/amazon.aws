# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible_collections.amazon.aws.plugins.inventory.aws_ec2 import InventoryModule
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AnsibleInventoryPermissionsError


@pytest.fixture(name="inventory")
def fixture_inventory():
    """Create a basic inventory module instance for testing."""
    inventory = InventoryModule()
    inventory._options = {}
    inventory.get_option = MagicMock()
    inventory.get_option.side_effect = inventory._options.get
    return inventory


@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2.describe_availability_zones")
def test_describe_azs_by_region(m_describe_availability_zones, inventory):
    mock_client = MagicMock()
    inventory.client = MagicMock(return_value=mock_client)

    m_describe_availability_zones.return_value = [
        {"ZoneName": "us-east-1a", "ZoneId": "use1-az1", "State": "available"},
        {"ZoneName": "us-east-1b", "ZoneId": "use1-az2", "State": "available"},
        {"ZoneName": "us-east-1c", "ZoneId": "use1-az3", "State": "available"},
    ]

    result = inventory._describe_azs_by_region("us-east-1")

    assert result == {
        "us-east-1a": {"ZoneName": "us-east-1a", "ZoneId": "use1-az1", "State": "available"},
        "us-east-1b": {"ZoneName": "us-east-1b", "ZoneId": "use1-az2", "State": "available"},
        "us-east-1c": {"ZoneName": "us-east-1c", "ZoneId": "use1-az3", "State": "available"},
    }
    inventory.client.assert_called_once_with("ec2", region="us-east-1")
    m_describe_availability_zones.assert_called_once_with(mock_client)


@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2.describe_availability_zones")
def test_describe_azs_by_region_caching(m_describe_availability_zones, inventory):
    mock_client = MagicMock()
    inventory.client = MagicMock(return_value=mock_client)

    m_describe_availability_zones.return_value = [
        {"ZoneName": "us-east-1a", "ZoneId": "use1-az1", "State": "available"},
    ]

    # First call
    result1 = inventory._describe_azs_by_region("us-east-1")
    # Second call should use cache
    result2 = inventory._describe_azs_by_region("us-east-1")

    assert result1 == result2
    # describe_availability_zones should only be called once due to caching
    m_describe_availability_zones.assert_called_once()
    inventory.client.assert_called_once()


@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2.describe_availability_zones")
def test_get_availability_zone_ids(m_describe_availability_zones, inventory):
    inventory.all_clients = MagicMock()
    inventory.all_clients.return_value = [
        (MagicMock(), "us-east-1"),
        (MagicMock(), "us-west-2"),
    ]

    m_describe_availability_zones.side_effect = [
        [
            {"ZoneName": "us-east-1a", "ZoneId": "use1-az1"},
            {"ZoneName": "us-east-1b", "ZoneId": "use1-az2"},
        ],
        [
            {"ZoneName": "us-west-2a", "ZoneId": "usw2-az1"},
            {"ZoneName": "us-west-2b", "ZoneId": "usw2-az2"},
        ],
    ]

    inventory.client = MagicMock(side_effect=lambda service, region: MagicMock())

    result = inventory._get_availability_zone_ids(strict_permissions=False)

    assert result == {
        "us-east-1a": "use1-az1",
        "us-east-1b": "use1-az2",
        "us-west-2a": "usw2-az1",
        "us-west-2b": "usw2-az2",
    }
    inventory.all_clients.assert_called_once_with("ec2")


@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2.describe_availability_zones")
def test_get_availability_zone_ids_with_permissions_error(m_describe_availability_zones, inventory):
    inventory.all_clients = MagicMock()
    inventory.all_clients.return_value = [
        (MagicMock(), "us-east-1"),
        (MagicMock(), "us-west-2"),
    ]

    # First region succeeds, second fails with permissions error
    def describe_side_effect(client):
        if not hasattr(describe_side_effect, "call_count"):
            describe_side_effect.call_count = 0
        describe_side_effect.call_count += 1

        if describe_side_effect.call_count == 1:
            return [{"ZoneName": "us-east-1a", "ZoneId": "use1-az1"}]
        else:
            raise AnsibleInventoryPermissionsError(
                message="Failed to describe availability zones (permission denied)",
                exception=botocore.exceptions.ClientError(
                    {
                        "Error": {"Code": "UnauthorizedOperation", "Message": "Not authorized"},
                        "ResponseMetadata": {"HTTPStatusCode": 403},
                    },
                    "describe_availability_zones",
                ),
            )

    m_describe_availability_zones.side_effect = describe_side_effect
    inventory.client = MagicMock(side_effect=lambda service, region: MagicMock())

    # With strict_permissions=False, should continue on permissions errors
    result = inventory._get_availability_zone_ids(strict_permissions=False)
    assert result == {"us-east-1a": "use1-az1"}

    # With strict_permissions=True, should raise
    # Clear cache and reset side effect
    inventory._availability_zone_cache = {}
    m_describe_availability_zones.side_effect = describe_side_effect
    describe_side_effect.call_count = 0
    with pytest.raises(AnsibleInventoryPermissionsError):
        inventory._get_availability_zone_ids(strict_permissions=True)

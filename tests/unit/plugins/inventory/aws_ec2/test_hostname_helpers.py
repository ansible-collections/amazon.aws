# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible.errors import AnsibleError

from ansible_collections.amazon.aws.plugins.inventory.aws_ec2 import InventoryModule


@pytest.fixture(name="inventory")
def fixture_inventory():
    """Create a basic inventory module instance for testing."""
    inventory = InventoryModule()
    inventory._options = {
        "route53_enabled": False,
    }
    inventory.get_option = MagicMock()
    inventory.get_option.side_effect = inventory._options.get
    return inventory


class TestProcessHostnameDictPreference:
    """Tests for _process_hostname_dict_preference helper method."""

    def test_missing_name_key_raises_error(self, inventory):
        """Test that missing 'name' key raises AnsibleError."""
        instance = {}
        preference = {"prefix": "test"}

        with pytest.raises(AnsibleError, match="A 'name' key must be defined in a hostnames dictionary"):
            inventory._process_hostname_dict_preference(instance, preference)

    def test_name_only_no_prefix(self, inventory, monkeypatch):
        """Test processing with only 'name' key, no prefix."""
        instance = {"InstanceId": "i-12345"}
        preference = {"name": "instance-id"}

        # Mock _get_preferred_hostname to return a hostname
        def mock_get_preferred_hostname(inst, hostnames):
            if hostnames == ["instance-id"]:
                return "i-12345"
            return None

        monkeypatch.setattr(inventory, "_get_preferred_hostname", mock_get_preferred_hostname)

        result = inventory._process_hostname_dict_preference(instance, preference)
        assert result == "i-12345"

    def test_name_with_prefix(self, inventory, monkeypatch):
        """Test processing with both 'name' and 'prefix' keys."""
        instance = {"InstanceId": "i-12345", "Tags": [{"Key": "Name", "Value": "web-server"}]}
        preference = {"name": "tag:Name", "prefix": "instance-id"}

        # Mock _get_preferred_hostname
        def mock_get_preferred_hostname(inst, hostnames):
            if hostnames == ["tag:Name"]:
                return "web-server"
            elif hostnames == ["instance-id"]:
                return "i-12345"
            return None

        monkeypatch.setattr(inventory, "_get_preferred_hostname", mock_get_preferred_hostname)

        result = inventory._process_hostname_dict_preference(instance, preference)
        assert result == "i-12345_web-server"

    def test_name_with_prefix_custom_separator(self, inventory, monkeypatch):
        """Test processing with custom separator."""
        instance = {"InstanceId": "i-12345", "Tags": [{"Key": "Name", "Value": "web-server"}]}
        preference = {"name": "tag:Name", "prefix": "instance-id", "separator": "-"}

        # Mock _get_preferred_hostname
        def mock_get_preferred_hostname(inst, hostnames):
            if hostnames == ["tag:Name"]:
                return "web-server"
            elif hostnames == ["instance-id"]:
                return "i-12345"
            return None

        monkeypatch.setattr(inventory, "_get_preferred_hostname", mock_get_preferred_hostname)

        result = inventory._process_hostname_dict_preference(instance, preference)
        assert result == "i-12345-web-server"

    def test_name_with_prefix_but_no_hostname(self, inventory, monkeypatch):
        """Test when name returns None but prefix is specified."""
        instance = {}
        preference = {"name": "tag:Name", "prefix": "instance-id"}

        # Mock _get_preferred_hostname to return None for name
        def mock_get_preferred_hostname(inst, hostnames):
            return None

        monkeypatch.setattr(inventory, "_get_preferred_hostname", mock_get_preferred_hostname)

        result = inventory._process_hostname_dict_preference(instance, preference)
        assert result is None

    def test_name_with_prefix_but_no_prefix_hostname(self, inventory, monkeypatch):
        """Test when prefix returns None but name has a value."""
        instance = {}
        preference = {"name": "tag:Name", "prefix": "instance-id"}

        # Mock _get_preferred_hostname to return None for prefix
        def mock_get_preferred_hostname(inst, hostnames):
            if hostnames == ["tag:Name"]:
                return "web-server"
            return None

        monkeypatch.setattr(inventory, "_get_preferred_hostname", mock_get_preferred_hostname)

        result = inventory._process_hostname_dict_preference(instance, preference)
        assert result == "web-server"


class TestProcessAllHostnamesDictPreference:
    """Tests for _process_all_hostnames_dict_preference helper method."""

    def test_missing_name_key_raises_error(self, inventory):
        """Test that missing 'name' key raises AnsibleError."""
        instance = {}
        preference = {"prefix": "test"}

        with pytest.raises(AnsibleError, match="A 'name' key must be defined in a hostnames dictionary"):
            inventory._process_all_hostnames_dict_preference(instance, preference)

    def test_name_only_returns_list(self, inventory, monkeypatch):
        """Test processing with only 'name' key returns list."""
        instance = {"PrivateIpAddress": "192.0.2.1"}
        preference = {"name": "private-ip-address"}

        # Mock _get_all_hostnames to return a list
        def mock_get_all_hostnames(inst, hostnames):
            if hostnames == ["private-ip-address"]:
                return ["192.0.2.1"]
            return []

        monkeypatch.setattr(inventory, "_get_all_hostnames", mock_get_all_hostnames)

        result = inventory._process_all_hostnames_dict_preference(instance, preference)
        assert result == ["192.0.2.1"]

    def test_name_with_prefix_constructs_combined(self, inventory, monkeypatch):
        """Test processing with both name and prefix constructs combined hostname."""
        instance = {"InstanceId": "i-12345", "Tags": [{"Key": "Name", "Value": "web-server"}]}
        preference = {"name": "tag:Name", "prefix": "instance-id"}

        # Mock _get_all_hostnames
        def mock_get_all_hostnames(inst, hostnames):
            if hostnames == ["tag:Name"]:
                return ["web-server"]
            elif hostnames == ["instance-id"]:
                return ["i-12345"]
            return []

        monkeypatch.setattr(inventory, "_get_all_hostnames", mock_get_all_hostnames)

        result = inventory._process_all_hostnames_dict_preference(instance, preference)
        assert result == "i-12345_web-server"

    def test_name_with_prefix_custom_separator(self, inventory, monkeypatch):
        """Test processing with custom separator for all hostnames."""
        instance = {"InstanceId": "i-12345", "Tags": [{"Key": "Name", "Value": "web-server"}]}
        preference = {"name": "tag:Name", "prefix": "instance-id", "separator": "-"}

        # Mock _get_all_hostnames
        def mock_get_all_hostnames(inst, hostnames):
            if hostnames == ["tag:Name"]:
                return ["web-server"]
            elif hostnames == ["instance-id"]:
                return ["i-12345"]
            return []

        monkeypatch.setattr(inventory, "_get_all_hostnames", mock_get_all_hostnames)

        result = inventory._process_all_hostnames_dict_preference(instance, preference)
        assert result == "i-12345-web-server"

    def test_name_with_prefix_but_empty_results(self, inventory, monkeypatch):
        """Test when results are empty lists."""
        instance = {}
        preference = {"name": "tag:Name", "prefix": "instance-id"}

        # Mock _get_all_hostnames to return empty lists
        def mock_get_all_hostnames(inst, hostnames):
            return []

        monkeypatch.setattr(inventory, "_get_all_hostnames", mock_get_all_hostnames)

        result = inventory._process_all_hostnames_dict_preference(instance, preference)
        assert result == []


class TestAddHostnameToList:
    """Tests for _add_hostname_to_list helper method."""

    def test_add_string_hostname(self, inventory, monkeypatch):
        """Test adding a string hostname to the list."""
        hostname_list = []
        hostname = "test-host.example.com"

        # Mock _sanitize_hostname
        def mock_sanitize(name):
            return name.replace(".", "-")

        monkeypatch.setattr(inventory, "_sanitize_hostname", mock_sanitize)

        inventory._add_hostname_to_list(hostname_list, hostname)
        assert hostname_list == ["test-host-example-com"]

    def test_add_list_of_hostnames(self, inventory, monkeypatch):
        """Test adding a list of hostnames."""
        hostname_list = []
        hostnames = ["host1.example.com", "host2.example.com", "host3.example.com"]

        # Mock _sanitize_hostname
        def mock_sanitize(name):
            return name.replace(".", "-")

        monkeypatch.setattr(inventory, "_sanitize_hostname", mock_sanitize)

        inventory._add_hostname_to_list(hostname_list, hostnames)
        assert hostname_list == ["host1-example-com", "host2-example-com", "host3-example-com"]

    def test_add_to_existing_list(self, inventory, monkeypatch):
        """Test adding hostnames to an existing list."""
        hostname_list = ["existing-host"]
        hostname = "new-host.example.com"

        # Mock _sanitize_hostname
        def mock_sanitize(name):
            return name.replace(".", "-")

        monkeypatch.setattr(inventory, "_sanitize_hostname", mock_sanitize)

        inventory._add_hostname_to_list(hostname_list, hostname)
        assert hostname_list == ["existing-host", "new-host-example-com"]

    def test_add_empty_list(self, inventory, monkeypatch):
        """Test adding an empty list does nothing."""
        hostname_list = ["existing-host"]
        hostnames = []

        # Mock _sanitize_hostname (shouldn't be called)
        def mock_sanitize(name):
            return name

        monkeypatch.setattr(inventory, "_sanitize_hostname", mock_sanitize)

        inventory._add_hostname_to_list(hostname_list, hostnames)
        assert hostname_list == ["existing-host"]

    def test_add_neither_string_nor_list(self, inventory, monkeypatch):
        """Test that non-string, non-list types are ignored."""
        hostname_list = []

        # Mock _sanitize_hostname (shouldn't be called)
        def mock_sanitize(name):
            return name

        monkeypatch.setattr(inventory, "_sanitize_hostname", mock_sanitize)

        # Should not raise an error, just ignore
        inventory._add_hostname_to_list(hostname_list, None)
        assert hostname_list == []

        inventory._add_hostname_to_list(hostname_list, 123)
        assert hostname_list == []

        inventory._add_hostname_to_list(hostname_list, {"key": "value"})
        assert hostname_list == []

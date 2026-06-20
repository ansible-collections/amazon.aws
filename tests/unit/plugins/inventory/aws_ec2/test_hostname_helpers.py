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


# Route53 hostname matching tests


@pytest.mark.parametrize(
    "route53_hostnames,hostname,expected",
    [
        (None, "test.example.com", True),
        ([], "test.example.com", True),
        (["example.com"], "test.example.com", True),
        (["example.com"], "test.other.com", False),
        (["example.com", "test.com"], "my.test.com", True),
        (["example.com", "test.com"], "my.other.com", False),
    ],
)
def test__is_matching_route53_hostname(inventory, route53_hostnames, hostname, expected):
    inventory.get_option = MagicMock(return_value=route53_hostnames)
    result = inventory._is_matching_route53_hostname(hostname)
    assert result == expected


# Jinja2 filter template formatting tests


@pytest.mark.parametrize(
    "preference,expected_template",
    [
        ("dns-name|upper", "{{'test.example.com'|upper}}"),
        ("dns-name|lower", "{{'test.example.com'|lower}}"),
        ("tag:Name|upper", "{{['host1', 'host2']|upper}}"),
        ("tag:Environment|lower", "{{['PROD', 'DEV']|lower}}"),
    ],
)
def test__get_hostname_with_jinja2_filter_template_format(inventory, preference, expected_template, monkeypatch):
    instance = {"dns-name": "test.example.com", "tag:Name": ["host1", "host2"]}

    def tag_hostname_side_effect(pref, inst):
        if pref == "tag:Name":
            return inst.get("tag:Name")
        if pref == "tag:Environment":
            return ["PROD", "DEV"]
        return None

    def boto_attr_side_effect(pref, inst):
        if pref == "dns-name":
            return inst.get("dns-name")
        return None

    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_tag_hostname", tag_hostname_side_effect
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_boto_attr_chain", boto_attr_side_effect
    )

    # Mock the templar to capture the template variable
    inventory.templar = MagicMock()
    inventory.templar.template = MagicMock(side_effect=lambda variable: variable)

    result = inventory._get_hostname_with_jinja2_filter(instance, preference)

    # Verify the correct template format was passed to templar
    inventory.templar.template.assert_called_once()
    call_args = inventory.templar.template.call_args
    assert call_args[1]["variable"] == expected_template


# Additional hostname-related tests moved from test_aws_ec2.py


@pytest.mark.parametrize(
    "hostnames,expected",
    [
        ([], "test-instance.ansible.com"),
        (["private-dns-name"], "test-instance.localhost"),
        (["tag:os_version"], "RHEL"),
        (["tag:os_version", "dns-name"], "RHEL"),
        ([{"name": "Name", "prefix": "Phase"}], "dev_test-instance-01"),
        ([{"name": "Name", "prefix": "Phase", "separator": "-"}], "dev-test-instance-01"),
        ([{"name": "Name", "prefix": "OSVersion", "separator": "-"}], "test-instance-01"),
        ([{"name": "Name", "separator": "-"}], "test-instance-01"),
        ([{"name": "Name", "prefix": "Phase"}, "private-dns-name"], "dev_test-instance-01"),
        ([{"name": "Name", "prefix": "Phase"}, "tag:os_version"], "dev_test-instance-01"),
        (["private-dns-name", "dns-name"], "test-instance.localhost"),
        (["private-dns-name", {"name": "Name", "separator": "-"}], "test-instance.localhost"),
        (["private-dns-name", "tag:os_version"], "test-instance.localhost"),
        (["OSRelease"], None),
    ],
)
def test_inventory_get_preferred_hostname(inventory, hostnames, expected, monkeypatch):
    instance = {
        "Name": "test-instance-01",
        "Phase": "dev",
        "tag:os_version": ["RHEL", "CoreOS"],
        "another_key": "another_value",
        "dns-name": "test-instance.ansible.com",
        "private-dns-name": "test-instance.localhost",
    }

    inventory._sanitize_hostname = MagicMock()
    inventory._sanitize_hostname.side_effect = lambda x: x

    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_boto_attr_chain",
        lambda pref, instance: instance.get(pref),
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_tag_hostname",
        lambda pref, instance: instance.get(pref),
    )

    assert expected == inventory._get_preferred_hostname(instance, hostnames)


def test_inventory_get_preferred_hostname_failure(inventory):
    instance = {}
    hostnames = [{"value": "saome_value"}]

    inventory._sanitize_hostname = MagicMock()
    inventory._sanitize_hostname.side_effect = lambda x: x

    with pytest.raises(AnsibleError) as err:
        inventory._get_preferred_hostname(instance, hostnames)
    assert "A 'name' key must be defined in a hostnames dictionary." in str(err.value)


@pytest.mark.parametrize("hostname,expected", [(1, "1"), ("a:b", "a_b"), ("a:/b", "a__b"), ("example", "example")])
def test_sanitize_hostname(inventory, hostname, expected):
    assert inventory._sanitize_hostname(hostname) == expected


def test_sanitize_hostname_legacy(inventory):
    inventory._sanitize_group_name = inventory._legacy_script_compatible_group_sanitization
    assert inventory._sanitize_hostname("a:/b") == "a__b"


@pytest.mark.parametrize(
    "hostnames,expected",
    [
        ([], ["test-instance.ansible.com", "test-instance.localhost"]),
        (["private-dns-name"], ["test-instance.localhost"]),
        (["tag:os_version"], ["RHEL", "CoreOS"]),
        (["tag:os_version", "dns-name"], ["RHEL", "CoreOS", "test-instance.ansible.com"]),
        ([{"name": "Name", "prefix": "Phase"}], ["dev_test-instance-01"]),
        ([{"name": "Name", "prefix": "Phase", "separator": "-"}], ["dev-test-instance-01"]),
        ([{"name": "Name", "prefix": "OSVersion", "separator": "-"}], ["test-instance-01"]),
        ([{"name": "Name", "separator": "-"}], ["test-instance-01"]),
        (
            [{"name": "Name", "prefix": "Phase"}, "private-dns-name"],
            ["dev_test-instance-01", "test-instance.localhost"],
        ),
        ([{"name": "Name", "prefix": "Phase"}, "tag:os_version"], ["dev_test-instance-01", "RHEL", "CoreOS"]),
        (["private-dns-name", {"name": "Name", "separator": "-"}], ["test-instance.localhost", "test-instance-01"]),
        (["OSRelease"], []),
    ],
)
def test_inventory_get_all_hostnames(inventory, hostnames, expected, monkeypatch):
    instance = {
        "Name": "test-instance-01",
        "Phase": "dev",
        "tag:os_version": ["RHEL", "CoreOS"],
        "another_key": "another_value",
        "dns-name": "test-instance.ansible.com",
        "private-dns-name": "test-instance.localhost",
    }

    inventory._sanitize_hostname = MagicMock()
    inventory._sanitize_hostname.side_effect = lambda x: x

    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_boto_attr_chain",
        lambda pref, instance: instance.get(pref),
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_tag_hostname",
        lambda pref, instance: instance.get(pref),
    )

    assert expected == inventory._get_all_hostnames(instance, hostnames)


def test_inventory_get_all_hostnames_failure(inventory):
    instance = {}
    hostnames = [{"value": "some_value"}]

    with pytest.raises(AnsibleError) as err:
        inventory._get_all_hostnames(instance, hostnames)
    assert "A 'name' key must be defined in a hostnames dictionary." in str(err.value)

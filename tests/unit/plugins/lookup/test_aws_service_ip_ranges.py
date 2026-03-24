# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges import LookupModule


@pytest.fixture(name="lookup_plugin")
def fixture_lookup_plugin():
    lookup = LookupModule()
    lookup._display = MagicMock()
    return lookup


class TestDeterminePrefixLabels:
    """Unit tests for _determine_prefix_labels method"""

    def test_determine_ipv4_labels(self, lookup_plugin):
        """Test that IPv4 labels are returned when use_ipv6 is False"""
        prefixes_label, ip_prefix_label = lookup_plugin._determine_prefix_labels(False)
        assert prefixes_label == "prefixes"
        assert ip_prefix_label == "ip_prefix"

    def test_determine_ipv6_labels(self, lookup_plugin):
        """Test that IPv6 labels are returned when use_ipv6 is True"""
        prefixes_label, ip_prefix_label = lookup_plugin._determine_prefix_labels(True)
        assert prefixes_label == "ipv6_prefixes"
        assert ip_prefix_label == "ipv6_prefix"

    def test_determine_labels_returns_tuple(self, lookup_plugin):
        """Test that the method returns a tuple"""
        result = lookup_plugin._determine_prefix_labels(False)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestFetchIpRanges:
    """Unit tests for _fetch_ip_ranges method"""

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_success_ipv4(self, mock_open_url, lookup_plugin):
        """Test successful fetch of IPv4 IP ranges"""
        mock_response = MagicMock()
        mock_response.read.return_value = (
            '{"prefixes": [{"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"}]}'
        )
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "prefixes": [{"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"}]
            }
            result = lookup_plugin._fetch_ip_ranges("prefixes")

        assert result == [{"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"}]
        mock_open_url.assert_called_once_with("https://ip-ranges.amazonaws.com/ip-ranges.json")

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_success_ipv6(self, mock_open_url, lookup_plugin):
        """Test successful fetch of IPv6 IP ranges"""
        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "ipv6_prefixes": [{"ipv6_prefix": "2001:db8::/32", "region": "us-east-1", "service": "EC2"}]
            }
            result = lookup_plugin._fetch_ip_ranges("ipv6_prefixes")

        assert result == [{"ipv6_prefix": "2001:db8::/32", "region": "us-east-1", "service": "EC2"}]

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_json_decode_error(self, mock_open_url, lookup_plugin):
        """Test that JSON decode errors are properly handled"""
        import json

        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        # Use the appropriate exception type (JSONDecodeError in Python 3+, ValueError in Python 2)
        json_error = getattr(json.decoder, "JSONDecodeError", ValueError)

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.side_effect = json_error("Invalid JSON", "", 0)
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin._fetch_ip_ranges("prefixes")

        assert "Could not decode AWS IP ranges" in str(exc_info.value)

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_http_error(self, mock_open_url, lookup_plugin):
        """Test that HTTP errors are properly handled"""
        import ansible.module_utils.six.moves.urllib.error as urllib_error

        mock_open_url.side_effect = urllib_error.HTTPError("url", 404, "Not Found", {}, None)

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._fetch_ip_ranges("prefixes")

        assert "Received HTTP error while pulling IP ranges" in str(exc_info.value)

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_ssl_error(self, mock_open_url, lookup_plugin):
        """Test that SSL validation errors are properly handled"""
        import ansible.module_utils.urls

        mock_open_url.side_effect = ansible.module_utils.urls.SSLValidationError("SSL Error")

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._fetch_ip_ranges("prefixes")

        assert "Error validating the server's certificate" in str(exc_info.value)

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_url_error(self, mock_open_url, lookup_plugin):
        """Test that URL errors are properly handled"""
        import ansible.module_utils.six.moves.urllib.error as urllib_error

        mock_open_url.side_effect = urllib_error.URLError("Connection refused")

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._fetch_ip_ranges("prefixes")

        assert "Failed look up IP range service" in str(exc_info.value)

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_fetch_ip_ranges_connection_error(self, mock_open_url, lookup_plugin):
        """Test that connection errors are properly handled"""
        import ansible.module_utils.urls

        mock_open_url.side_effect = ansible.module_utils.urls.ConnectionError("Connection failed")

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._fetch_ip_ranges("prefixes")

        assert "Error connecting to IP range service" in str(exc_info.value)


class TestFilterByRegion:
    """Unit tests for _filter_by_region method"""

    def test_filter_by_region_single_match(self, lookup_plugin):
        """Test filtering with a single matching region"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "eu-west-1", "service": "EC2"},
        ]
        result = list(lookup_plugin._filter_by_region(ip_ranges, "us-east-1"))
        assert len(result) == 1
        assert result[0]["region"] == "us-east-1"

    def test_filter_by_region_multiple_matches(self, lookup_plugin):
        """Test filtering with multiple matching regions"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
            {"ip_prefix": "203.0.113.0/24", "region": "eu-west-1", "service": "EC2"},
        ]
        result = list(lookup_plugin._filter_by_region(ip_ranges, "us-east-1"))
        assert len(result) == 2
        assert all(item["region"] == "us-east-1" for item in result)

    def test_filter_by_region_no_matches(self, lookup_plugin):
        """Test filtering with no matching regions"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "eu-west-1", "service": "EC2"},
        ]
        result = list(lookup_plugin._filter_by_region(ip_ranges, "ap-southeast-1"))
        assert len(result) == 0

    def test_filter_by_region_empty_input(self, lookup_plugin):
        """Test filtering with empty input"""
        result = list(lookup_plugin._filter_by_region([], "us-east-1"))
        assert len(result) == 0


class TestFilterByService:
    """Unit tests for _filter_by_service method"""

    def test_filter_by_service_single_match(self, lookup_plugin):
        """Test filtering with a single matching service"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
        ]
        result = list(lookup_plugin._filter_by_service(ip_ranges, "EC2"))
        assert len(result) == 1
        assert result[0]["service"] == "EC2"

    def test_filter_by_service_case_insensitive(self, lookup_plugin):
        """Test that service filtering is case-insensitive"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
        ]
        result = list(lookup_plugin._filter_by_service(ip_ranges, "ec2"))
        assert len(result) == 1
        assert result[0]["service"] == "EC2"

    def test_filter_by_service_multiple_matches(self, lookup_plugin):
        """Test filtering with multiple matching services"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "eu-west-1", "service": "EC2"},
            {"ip_prefix": "203.0.113.0/24", "region": "us-east-1", "service": "S3"},
        ]
        result = list(lookup_plugin._filter_by_service(ip_ranges, "EC2"))
        assert len(result) == 2
        assert all(item["service"] == "EC2" for item in result)

    def test_filter_by_service_no_matches(self, lookup_plugin):
        """Test filtering with no matching services"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
        ]
        result = list(lookup_plugin._filter_by_service(ip_ranges, "CLOUDFRONT"))
        assert len(result) == 0

    def test_filter_by_service_empty_input(self, lookup_plugin):
        """Test filtering with empty input"""
        result = list(lookup_plugin._filter_by_service([], "EC2"))
        assert len(result) == 0


class TestExtractIpAddresses:
    """Unit tests for _extract_ip_addresses method"""

    def test_extract_ipv4_addresses(self, lookup_plugin):
        """Test extracting IPv4 addresses"""
        ip_ranges = [
            {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
            {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
        ]
        result = lookup_plugin._extract_ip_addresses(ip_ranges, "ip_prefix")
        assert result == ["192.0.2.0/24", "198.51.100.0/24"]

    def test_extract_ipv6_addresses(self, lookup_plugin):
        """Test extracting IPv6 addresses"""
        ip_ranges = [
            {"ipv6_prefix": "2001:db8::/32", "region": "us-east-1", "service": "EC2"},
            {"ipv6_prefix": "2001:db8:1::/48", "region": "us-east-1", "service": "S3"},
        ]
        result = lookup_plugin._extract_ip_addresses(ip_ranges, "ipv6_prefix")
        assert result == ["2001:db8::/32", "2001:db8:1::/48"]

    def test_extract_addresses_empty_input(self, lookup_plugin):
        """Test extracting addresses from empty input"""
        result = lookup_plugin._extract_ip_addresses([], "ip_prefix")
        assert result == []

    def test_extract_addresses_single_item(self, lookup_plugin):
        """Test extracting addresses from single item"""
        ip_ranges = [{"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"}]
        result = lookup_plugin._extract_ip_addresses(ip_ranges, "ip_prefix")
        assert result == ["192.0.2.0/24"]


class TestRun:
    """Unit tests for run method integration"""

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_run_ipv4_no_filters(self, mock_open_url, lookup_plugin):
        """Test run method with IPv4 and no filters"""
        lookup_plugin.set_options = MagicMock()
        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "prefixes": [
                    {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
                    {"ip_prefix": "198.51.100.0/24", "region": "eu-west-1", "service": "S3"},
                ]
            }
            result = lookup_plugin.run([], {})

        assert len(result) == 2
        assert "192.0.2.0/24" in result
        assert "198.51.100.0/24" in result

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_run_ipv6(self, mock_open_url, lookup_plugin):
        """Test run method with IPv6"""
        lookup_plugin.set_options = MagicMock()
        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "ipv6_prefixes": [
                    {"ipv6_prefix": "2001:db8::/32", "region": "us-east-1", "service": "EC2"},
                ]
            }
            result = lookup_plugin.run([], {}, ipv6_prefixes=True)

        assert len(result) == 1
        assert "2001:db8::/32" in result

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_run_filter_by_region(self, mock_open_url, lookup_plugin):
        """Test run method with region filter"""
        lookup_plugin.set_options = MagicMock()
        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "prefixes": [
                    {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
                    {"ip_prefix": "198.51.100.0/24", "region": "eu-west-1", "service": "EC2"},
                ]
            }
            result = lookup_plugin.run([], {}, region="us-east-1")

        assert len(result) == 1
        assert "192.0.2.0/24" in result

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_run_filter_by_service(self, mock_open_url, lookup_plugin):
        """Test run method with service filter"""
        lookup_plugin.set_options = MagicMock()
        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "prefixes": [
                    {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
                    {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
                ]
            }
            result = lookup_plugin.run([], {}, service="EC2")

        assert len(result) == 1
        assert "192.0.2.0/24" in result

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.ansible.module_utils.urls.open_url")
    def test_run_filter_by_both(self, mock_open_url, lookup_plugin):
        """Test run method with both region and service filters"""
        lookup_plugin.set_options = MagicMock()
        mock_response = MagicMock()
        mock_open_url.return_value = mock_response

        with patch("ansible_collections.amazon.aws.plugins.lookup.aws_service_ip_ranges.json.load") as mock_json_load:
            mock_json_load.return_value = {
                "prefixes": [
                    {"ip_prefix": "192.0.2.0/24", "region": "us-east-1", "service": "EC2"},
                    {"ip_prefix": "198.51.100.0/24", "region": "us-east-1", "service": "S3"},
                    {"ip_prefix": "203.0.113.0/24", "region": "eu-west-1", "service": "EC2"},
                ]
            }
            result = lookup_plugin.run([], {}, region="us-east-1", service="EC2")

        assert len(result) == 1
        assert "192.0.2.0/24" in result

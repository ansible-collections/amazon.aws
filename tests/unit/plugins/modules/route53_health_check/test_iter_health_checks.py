# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.modules.route53_health_check import iter_health_checks


class TestIterHealthChecks:
    """Tests for iter_health_checks generator function."""

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_single_page_no_checks(self, mock_list):
        """Test iteration with a single page containing no health checks."""
        client = MagicMock()
        mock_list.return_value = {"HealthChecks": [], "IsTruncated": False}

        result = list(iter_health_checks(client))

        assert result == []
        mock_list.assert_called_once_with(client)

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_single_page_with_checks(self, mock_list):
        """Test iteration with a single page containing health checks."""
        client = MagicMock()
        check1 = {"Id": "check1", "HealthCheckConfig": {"Type": "HTTP"}}
        check2 = {"Id": "check2", "HealthCheckConfig": {"Type": "HTTPS"}}
        mock_list.return_value = {"HealthChecks": [check1, check2], "IsTruncated": False}

        result = list(iter_health_checks(client))

        assert len(result) == 2
        assert result[0] == check1
        assert result[1] == check2
        mock_list.assert_called_once_with(client)

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_multiple_pages(self, mock_list):
        """Test pagination across multiple pages."""
        client = MagicMock()
        check1 = {"Id": "check1"}
        check2 = {"Id": "check2"}
        check3 = {"Id": "check3"}

        # First page
        page1 = {"HealthChecks": [check1, check2], "IsTruncated": True, "NextMarker": "marker1"}
        # Second page
        page2 = {"HealthChecks": [check3], "IsTruncated": False}

        mock_list.side_effect = [page1, page2]

        result = list(iter_health_checks(client))

        assert len(result) == 3
        assert result[0] == check1
        assert result[1] == check2
        assert result[2] == check3
        assert mock_list.call_count == 2
        # First call without marker
        mock_list.assert_any_call(client)
        # Second call with marker
        mock_list.assert_any_call(client, Marker="marker1")

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_three_pages(self, mock_list):
        """Test pagination across three pages."""
        client = MagicMock()
        check1 = {"Id": "check1"}
        check2 = {"Id": "check2"}
        check3 = {"Id": "check3"}
        check4 = {"Id": "check4"}

        page1 = {"HealthChecks": [check1], "IsTruncated": True, "NextMarker": "marker1"}
        page2 = {"HealthChecks": [check2, check3], "IsTruncated": True, "NextMarker": "marker2"}
        page3 = {"HealthChecks": [check4], "IsTruncated": False}

        mock_list.side_effect = [page1, page2, page3]

        result = list(iter_health_checks(client))

        assert len(result) == 4
        assert result[0]["Id"] == "check1"
        assert result[1]["Id"] == "check2"
        assert result[2]["Id"] == "check3"
        assert result[3]["Id"] == "check4"
        assert mock_list.call_count == 3

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_empty_pages_handled(self, mock_list):
        """Test that empty pages in the middle are handled correctly."""
        client = MagicMock()
        check1 = {"Id": "check1"}
        check2 = {"Id": "check2"}

        page1 = {"HealthChecks": [check1], "IsTruncated": True, "NextMarker": "marker1"}
        page2 = {"HealthChecks": [], "IsTruncated": True, "NextMarker": "marker2"}
        page3 = {"HealthChecks": [check2], "IsTruncated": False}

        mock_list.side_effect = [page1, page2, page3]

        result = list(iter_health_checks(client))

        assert len(result) == 2
        assert result[0] == check1
        assert result[1] == check2
        assert mock_list.call_count == 3

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_generator_can_be_consumed_partially(self, mock_list):
        """Test that the generator can be stopped early without consuming all pages."""
        client = MagicMock()
        check1 = {"Id": "check1"}
        check2 = {"Id": "check2"}
        check3 = {"Id": "check3"}

        page1 = {"HealthChecks": [check1, check2], "IsTruncated": True, "NextMarker": "marker1"}
        page2 = {"HealthChecks": [check3], "IsTruncated": False}

        mock_list.side_effect = [page1, page2]

        # Only consume first item
        gen = iter_health_checks(client)
        first = next(gen)

        assert first == check1
        # Should only have called once since we stopped early
        assert mock_list.call_count == 1

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_missing_health_checks_key(self, mock_list):
        """Test graceful handling when HealthChecks key is missing."""
        client = MagicMock()
        mock_list.return_value = {"IsTruncated": False}

        result = list(iter_health_checks(client))

        assert result == []
        mock_list.assert_called_once_with(client)

    @patch("ansible_collections.amazon.aws.plugins.modules.route53_health_check._list_health_checks")
    def test_stops_when_is_truncated_false(self, mock_list):
        """Test that iteration stops when IsTruncated is False, even if NextMarker exists."""
        client = MagicMock()
        check1 = {"Id": "check1"}
        check2 = {"Id": "check2"}

        # First page with truncation
        page1 = {"HealthChecks": [check1], "IsTruncated": True, "NextMarker": "marker1"}
        # Second page without truncation but with NextMarker (should stop here)
        page2 = {"HealthChecks": [check2], "IsTruncated": False, "NextMarker": "marker2"}
        # Third page that should never be requested
        page3 = {"HealthChecks": [{"Id": "check3"}], "IsTruncated": False}

        mock_list.side_effect = [page1, page2, page3]

        result = list(iter_health_checks(client))

        # Should only get checks from first two pages
        assert len(result) == 2
        assert result[0] == check1
        assert result[1] == check2
        # Should only have called twice, not three times
        assert mock_list.call_count == 2
        mock_list.assert_any_call(client)
        mock_list.assert_any_call(client, Marker="marker1")

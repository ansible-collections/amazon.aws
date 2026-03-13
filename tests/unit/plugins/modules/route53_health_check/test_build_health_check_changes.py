# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.modules.route53_health_check import build_health_check_changes


class TestBuildHealthCheckChanges:
    """Tests for build_health_check_changes function."""

    def test_no_changes_when_params_match_existing(self):
        """Test that no changes are detected when params match existing config."""
        params = {"resource_path": "/health", "failure_threshold": 3}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {
                "ResourcePath": "/health",
                "FailureThreshold": 3,
            },
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

    @pytest.mark.parametrize(
        "param_key,param_value,existing_value,expected_change_key",
        [
            ("resource_path", "/new-path", "/old-path", "ResourcePath"),
            ("string_match", "NEW", "OLD", "SearchString"),
            ("failure_threshold", 5, 3, "FailureThreshold"),
        ],
    )
    def test_always_updatable_fields_detect_changes(self, param_key, param_value, existing_value, expected_change_key):
        """Test that always-updatable fields detect changes correctly."""
        params = {"type": "HTTP", param_key: param_value}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {expected_change_key: existing_value},
        }
        result = build_health_check_changes(params, existing_check)
        assert expected_change_key in result
        assert result[expected_change_key] == param_value

    def test_disabled_field_detects_change_from_none_to_true(self):
        """Test disabled field change from None to True."""
        params = {"disabled": True}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {"Disabled": True}

    def test_disabled_field_detects_change_from_true_to_false(self):
        """Test disabled field change from True to False."""
        params = {"disabled": False}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"Disabled": True},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {"Disabled": False}

    def test_disabled_field_no_change_when_matching(self):
        """Test disabled field doesn't change when values match."""
        params = {"disabled": True}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"Disabled": True},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

    def test_disabled_field_not_in_changes_when_not_provided(self):
        """Test disabled field not in changes when not in params."""
        params = {}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"Disabled": True},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

    def test_failure_threshold_not_updated_for_calculated_type(self):
        """Test that failure_threshold is not updated for CALCULATED type."""
        params = {"type": "CALCULATED", "failure_threshold": 5}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"Type": "CALCULATED", "FailureThreshold": 3},
        }
        result = build_health_check_changes(params, existing_check)
        assert "FailureThreshold" not in result

    @pytest.mark.parametrize(
        "param_key,param_value,existing_key,existing_value,expected_key",
        [
            ("ip_address", "192.0.2.2", "IPAddress", "192.0.2.1", "IPAddress"),
            ("port", 9000, "Port", 8080, "Port"),
            ("fqdn", "new.example.com", "FullyQualifiedDomainName", "old.example.com", "FullyQualifiedDomainName"),
        ],
    )
    def test_immutable_fields_updated_with_health_check_id(
        self, param_key, param_value, existing_key, existing_value, expected_key
    ):
        """Test that immutable fields are updated when health_check_id is present."""
        params = {"health_check_id": "abc123", param_key: param_value}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {existing_key: existing_value},
        }
        result = build_health_check_changes(params, existing_check)
        assert expected_key in result
        assert result[expected_key] == param_value

    @pytest.mark.parametrize(
        "param_key,param_value",
        [
            ("ip_address", "192.0.2.2"),
            ("port", 9000),
            ("fqdn", "new.example.com"),
        ],
    )
    def test_immutable_fields_updated_with_use_unique_names(self, param_key, param_value):
        """Test that immutable fields are updated when use_unique_names is present."""
        params = {"use_unique_names": True, param_key: param_value}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {},
        }
        result = build_health_check_changes(params, existing_check)
        # Should have the change since use_unique_names is True
        assert len(result) == 1

    @pytest.mark.parametrize(
        "param_key,param_value",
        [
            ("ip_address", "192.0.2.2"),
            ("port", 9000),
            ("fqdn", "new.example.com"),
        ],
    )
    def test_immutable_fields_not_updated_without_id_or_unique_names(self, param_key, param_value):
        """Test that immutable fields are NOT updated without health_check_id or use_unique_names."""
        params = {param_key: param_value}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

    def test_calculated_type_child_health_checks_updated_with_id(self):
        """Test CALCULATED type child_health_checks updated with health_check_id."""
        params = {
            "health_check_id": "abc123",
            "type": "CALCULATED",
            "child_health_checks": ["check1", "check2", "check3"],
        }
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {
                "Type": "CALCULATED",
                "ChildHealthChecks": ["check1", "check2"],
            },
        }
        result = build_health_check_changes(params, existing_check)
        assert "ChildHealthChecks" in result
        assert result["ChildHealthChecks"] == ["check1", "check2", "check3"]

    def test_calculated_type_health_threshold_updated_with_id(self):
        """Test CALCULATED type health_threshold updated with health_check_id."""
        params = {
            "health_check_id": "abc123",
            "type": "CALCULATED",
            "health_threshold": 3,
        }
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {
                "Type": "CALCULATED",
                "HealthThreshold": 2,
            },
        }
        result = build_health_check_changes(params, existing_check)
        assert "HealthThreshold" in result
        assert result["HealthThreshold"] == 3

    def test_calculated_fields_not_updated_without_id(self):
        """Test CALCULATED fields not updated without health_check_id or use_unique_names."""
        params = {
            "type": "CALCULATED",
            "child_health_checks": ["check1", "check2"],
            "health_threshold": 3,
        }
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {
                "Type": "CALCULATED",
                "ChildHealthChecks": ["check1"],
                "HealthThreshold": 2,
            },
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

    def test_calculated_fields_not_updated_for_non_calculated_type(self):
        """Test CALCULATED fields not checked when type is not CALCULATED."""
        params = {
            "health_check_id": "abc123",
            "type": "HTTP",
            "child_health_checks": ["check1"],
            "health_threshold": 3,
        }
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"Type": "HTTP"},
        }
        result = build_health_check_changes(params, existing_check)
        assert "ChildHealthChecks" not in result
        assert "HealthThreshold" not in result

    def test_multiple_changes_detected(self):
        """Test multiple changes are all detected."""
        params = {
            "health_check_id": "abc123",
            "resource_path": "/new",
            "disabled": True,
            "port": 9000,
        }
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {
                "ResourcePath": "/old",
                "Disabled": False,
                "Port": 8080,
            },
        }
        result = build_health_check_changes(params, existing_check)
        assert len(result) == 3
        assert result["ResourcePath"] == "/new"
        assert result["Disabled"] is True
        assert result["Port"] == 9000

    def test_empty_existing_config_handled(self):
        """Test that empty existing config is handled properly."""
        params = {"health_check_id": "abc123", "port": 80}
        existing_check = {"Id": "abc123"}
        result = build_health_check_changes(params, existing_check)
        assert result == {"Port": 80}

    def test_none_values_in_params_dont_trigger_changes(self):
        """Test that None values in params don't trigger false changes."""
        params = {"resource_path": None, "port": None}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {
                "ResourcePath": "/health",
                "Port": 80,
            },
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

    def test_empty_string_resource_path_not_considered_change(self):
        """Test that empty string for resource_path is not considered a change."""
        params = {"resource_path": ""}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"ResourcePath": "/health"},
        }
        result = build_health_check_changes(params, existing_check)
        # Empty string is falsy, so it won't trigger a change
        assert result == {}

    def test_string_match_change_detected(self):
        """Test that string_match changes are detected."""
        params = {"string_match": "HEALTHY"}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"SearchString": "OK"},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {"SearchString": "HEALTHY"}

    def test_string_match_no_change_when_matching(self):
        """Test that string_match doesn't change when values match."""
        params = {"string_match": "OK"}
        existing_check = {
            "Id": "abc123",
            "HealthCheckConfig": {"SearchString": "OK"},
        }
        result = build_health_check_changes(params, existing_check)
        assert result == {}

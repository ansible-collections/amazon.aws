# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.modules.route53_health_check import build_health_check_config


class TestBuildHealthCheckConfig:
    """Tests for build_health_check_config function."""

    @pytest.mark.parametrize(
        "healthcheck_type,ip_addr,fqdn,port,params,expected_fields",
        [
            # Basic HTTP health check
            (
                "HTTP",
                "192.0.2.1",
                None,
                80,
                {"disabled": False, "resource_path": "/health", "measure_latency": True},
                {
                    "Type": "HTTP",
                    "IPAddress": "192.0.2.1",
                    "Port": 80,
                    "ResourcePath": "/health",
                    "Disabled": False,
                    "MeasureLatency": True,
                    "FailureThreshold": 3,
                    "RequestInterval": 30,
                },
            ),
            # HTTPS with FQDN
            (
                "HTTPS",
                None,
                "example.com",
                443,
                {"resource_path": "/status", "failure_threshold": 5},
                {
                    "Type": "HTTPS",
                    "FullyQualifiedDomainName": "example.com",
                    "Port": 443,
                    "ResourcePath": "/status",
                    "FailureThreshold": 5,
                    "RequestInterval": 30,
                },
            ),
            # HTTP_STR_MATCH
            (
                "HTTP_STR_MATCH",
                "192.0.2.2",
                None,
                8080,
                {"resource_path": "/", "string_match": "OK", "failure_threshold": 2},
                {
                    "Type": "HTTP_STR_MATCH",
                    "IPAddress": "192.0.2.2",
                    "Port": 8080,
                    "SearchString": "OK",
                    "ResourcePath": "/",
                    "FailureThreshold": 2,
                    "RequestInterval": 10,
                },
            ),
            # HTTPS_STR_MATCH
            (
                "HTTPS_STR_MATCH",
                None,
                "secure.example.com",
                443,
                {"resource_path": "/check", "string_match": "SUCCESS"},
                {
                    "Type": "HTTPS_STR_MATCH",
                    "FullyQualifiedDomainName": "secure.example.com",
                    "Port": 443,
                    "ResourcePath": "/check",
                    "SearchString": "SUCCESS",
                    "FailureThreshold": 3,
                    "RequestInterval": 30,
                },
            ),
            # TCP
            (
                "TCP",
                "192.0.2.4",
                None,
                3306,
                {"disabled": False},
                {
                    "Type": "TCP",
                    "IPAddress": "192.0.2.4",
                    "Port": 3306,
                    "Disabled": False,
                    "FailureThreshold": 3,
                    "RequestInterval": 30,
                },
            ),
            # HTTP without optional fields
            (
                "HTTP",
                None,
                "example.com",
                None,
                {},
                {
                    "Type": "HTTP",
                    "FullyQualifiedDomainName": "example.com",
                    "FailureThreshold": 3,
                    "RequestInterval": 30,
                },
            ),
        ],
    )
    def test_valid_health_check_configs(self, healthcheck_type, ip_addr, fqdn, port, params, expected_fields):
        """Test various valid health check configurations."""
        request_interval = expected_fields.get("RequestInterval", 30)
        result = build_health_check_config(
            params=params,
            ip_addr=ip_addr,
            fqdn=fqdn,
            healthcheck_type=healthcheck_type,
            request_interval=request_interval,
            port=port,
            child_health_checks=None,
            health_threshold=None,
        )

        # Check all expected fields are present with correct values
        for key, value in expected_fields.items():
            assert key in result, f"Expected key '{key}' not found in result"
            assert result[key] == value, f"Expected {key}={value}, got {result[key]}"

        # Check that unexpected fields are not present
        for key in result:
            if key not in expected_fields:
                # These fields should not be in the result unless explicitly expected
                assert key not in [
                    "IPAddress",
                    "FullyQualifiedDomainName",
                    "Port",
                    "Disabled",
                    "MeasureLatency",
                    "ResourcePath",
                    "SearchString",
                    "ChildHealthChecks",
                    "HealthThreshold",
                ], f"Unexpected key '{key}' found in result"

    def test_calculated_with_children(self):
        """Test CALCULATED health check with child health checks."""
        params = {}
        result = build_health_check_config(
            params=params,
            ip_addr=None,
            fqdn=None,
            healthcheck_type="CALCULATED",
            request_interval=30,
            port=None,
            child_health_checks=["check-1", "check-2", "check-3"],
            health_threshold=2,
        )

        assert result["Type"] == "CALCULATED"
        assert result["ChildHealthChecks"] == ["check-1", "check-2", "check-3"]
        assert result["HealthThreshold"] == 2
        # CALCULATED type should not have these fields
        assert "FailureThreshold" not in result
        assert "RequestInterval" not in result

    @pytest.mark.parametrize(
        "params,expected_failure_threshold",
        [
            ({}, 3),  # Default
            ({"failure_threshold": 1}, 1),  # Custom value
            ({"failure_threshold": 10}, 10),  # Another custom value
        ],
    )
    def test_failure_threshold_values(self, params, expected_failure_threshold):
        """Test default and custom failure_threshold values."""
        result = build_health_check_config(
            params=params,
            ip_addr="192.0.2.1",
            fqdn=None,
            healthcheck_type="TCP",
            request_interval=30,
            port=22,
            child_health_checks=None,
            health_threshold=None,
        )

        assert result["FailureThreshold"] == expected_failure_threshold

    @pytest.mark.parametrize(
        "disabled_value,should_be_present",
        [
            (None, False),  # Not in params, should not be in result
            (True, True),  # Explicitly True
            (False, True),  # Explicitly False
        ],
    )
    def test_disabled_field(self, disabled_value, should_be_present):
        """Test Disabled field is only present when explicitly set."""
        params = {}
        if disabled_value is not None:
            params["disabled"] = disabled_value

        result = build_health_check_config(
            params=params,
            ip_addr="192.0.2.1",
            fqdn=None,
            healthcheck_type="HTTP",
            request_interval=30,
            port=80,
            child_health_checks=None,
            health_threshold=None,
        )

        if should_be_present:
            assert "Disabled" in result
            assert result["Disabled"] == disabled_value
        else:
            assert "Disabled" not in result

    @pytest.mark.parametrize(
        "measure_latency,should_be_present",
        [
            (None, False),  # Not in params
            (True, True),
            (False, True),
        ],
    )
    def test_measure_latency_field(self, measure_latency, should_be_present):
        """Test MeasureLatency field is only present when explicitly set."""
        params = {}
        if measure_latency is not None:
            params["measure_latency"] = measure_latency

        result = build_health_check_config(
            params=params,
            ip_addr="192.0.2.1",
            fqdn=None,
            healthcheck_type="HTTP",
            request_interval=30,
            port=80,
            child_health_checks=None,
            health_threshold=None,
        )

        if should_be_present:
            assert "MeasureLatency" in result
            assert result["MeasureLatency"] == measure_latency
        else:
            assert "MeasureLatency" not in result

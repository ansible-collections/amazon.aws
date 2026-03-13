# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.route53 import AnsibleRoute53Error
from ansible_collections.amazon.aws.plugins.modules.route53_health_check import validate_parameters


class TestValidateParameters:
    """Tests for validate_parameters function."""

    @pytest.mark.parametrize(
        "healthcheck_type,expected_port",
        [
            ("HTTP", 80),
            ("HTTP_STR_MATCH", 80),
            ("HTTPS", 443),
            ("HTTPS_STR_MATCH", 443),
            ("TCP", None),
            ("CALCULATED", None),
        ],
    )
    def test_default_port_by_type(self, healthcheck_type, expected_port):
        """Test default port assignment for different health check types."""
        params = {"type": healthcheck_type}
        result = validate_parameters(params)
        assert result == expected_port

    @pytest.mark.parametrize(
        "healthcheck_type,explicit_port",
        [
            ("HTTP", 8080),
            ("HTTPS", 8443),
            ("TCP", 3306),
            ("CALCULATED", 9000),
        ],
    )
    def test_explicit_port_overrides_default(self, healthcheck_type, explicit_port):
        """Test that explicitly provided port overrides default."""
        params = {"type": healthcheck_type, "port": explicit_port}
        result = validate_parameters(params)
        assert result == explicit_port

    def test_health_check_id_without_type(self):
        """Test that health_check_id allows validation without type."""
        params = {"health_check_id": "abc123"}
        result = validate_parameters(params)
        # No type means no default port
        assert result is None

    def test_health_check_id_with_type_and_port(self):
        """Test that health_check_id with type and port returns the port."""
        params = {"health_check_id": "abc123", "type": "HTTP", "port": 9999}
        result = validate_parameters(params)
        assert result == 9999

    def test_missing_type_without_health_check_id_raises_error(self):
        """Test that missing type when no health_check_id raises error."""
        params = {}
        with pytest.raises(
            AnsibleRoute53Error,
            match="parameter 'type' is required if not updating or deleting health check by ID",
        ):
            validate_parameters(params)

    @pytest.mark.parametrize(
        "healthcheck_type,string_match",
        [
            ("HTTP_STR_MATCH", "OK"),
            ("HTTP_STR_MATCH", "SUCCESS"),
            ("HTTPS_STR_MATCH", "HEALTHY"),
            ("HTTPS_STR_MATCH", "A" * 255),  # Max length
        ],
    )
    def test_valid_string_match(self, healthcheck_type, string_match):
        """Test valid string_match configurations."""
        params = {"type": healthcheck_type, "string_match": string_match}
        result = validate_parameters(params)
        # Should not raise, just return the port
        assert result in [80, 443]

    @pytest.mark.parametrize(
        "healthcheck_type",
        [
            "HTTP",
            "HTTPS",
            "TCP",
            "CALCULATED",
        ],
    )
    def test_string_match_with_wrong_type_raises_error(self, healthcheck_type):
        """Test that string_match with non-STR_MATCH type raises error."""
        params = {"type": healthcheck_type, "string_match": "OK"}
        with pytest.raises(
            AnsibleRoute53Error,
            match="parameter 'string_match' argument is only for the HTTP\\(S\\)_STR_MATCH types",
        ):
            validate_parameters(params)

    def test_string_match_exceeds_max_length_raises_error(self):
        """Test that string_match exceeding 255 characters raises error."""
        params = {"type": "HTTP_STR_MATCH", "string_match": "A" * 256}
        with pytest.raises(
            AnsibleRoute53Error,
            match="parameter 'string_match' is limited to 255 characters max",
        ):
            validate_parameters(params)

    def test_string_match_at_max_length_is_valid(self):
        """Test that string_match at exactly 255 characters is valid."""
        params = {"type": "HTTP_STR_MATCH", "string_match": "A" * 255}
        result = validate_parameters(params)
        assert result == 80

    def test_empty_string_match_is_valid(self):
        """Test that empty string_match is allowed."""
        params = {"type": "HTTP_STR_MATCH", "string_match": ""}
        result = validate_parameters(params)
        assert result == 80

    def test_minimal_valid_params(self):
        """Test minimal valid parameters."""
        params = {"type": "TCP", "port": 22}
        result = validate_parameters(params)
        assert result == 22

    def test_http_without_port(self):
        """Test HTTP type without explicit port gets default 80."""
        params = {"type": "HTTP"}
        result = validate_parameters(params)
        assert result == 80

    def test_https_without_port(self):
        """Test HTTPS type without explicit port gets default 443."""
        params = {"type": "HTTPS"}
        result = validate_parameters(params)
        assert result == 443

    def test_tcp_without_port(self):
        """Test TCP type without explicit port returns None."""
        params = {"type": "TCP"}
        result = validate_parameters(params)
        assert result is None

    def test_calculated_without_port(self):
        """Test CALCULATED type without explicit port returns None."""
        params = {"type": "CALCULATED"}
        result = validate_parameters(params)
        assert result is None

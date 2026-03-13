# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.route53 import AnsibleRoute53Error
from ansible_collections.amazon.aws.plugins.modules.route53_health_check import validate_health_check_creation_params


class TestValidateHealthCheckCreationParams:
    """Tests for validate_health_check_creation_params function."""

    @pytest.mark.parametrize(
        "healthcheck_type,string_match,child_health_checks,health_threshold",
        [
            # HTTP type with no required params
            ("HTTP", None, None, None),
            # HTTPS type with no required params
            ("HTTPS", None, None, None),
            # TCP type with no required params
            ("TCP", None, None, None),
            # HTTP_STR_MATCH with string_match provided
            ("HTTP_STR_MATCH", "ALIVE", None, None),
            # HTTPS_STR_MATCH with string_match provided
            ("HTTPS_STR_MATCH", "OK", None, None),
            # CALCULATED with all required params
            ("CALCULATED", None, ["check-1", "check-2"], 2),
        ],
    )
    def test_valid_parameters(self, healthcheck_type, string_match, child_health_checks, health_threshold):
        """Test that valid parameter combinations do not raise errors."""
        # Should not raise
        validate_health_check_creation_params(
            healthcheck_type=healthcheck_type,
            string_match=string_match,
            child_health_checks=child_health_checks,
            health_threshold=health_threshold,
        )

    @pytest.mark.parametrize(
        "healthcheck_type,string_match,child_health_checks,health_threshold,expected_error",
        [
            # Missing string_match for HTTP_STR_MATCH
            ("HTTP_STR_MATCH", None, None, None, "string_match"),
            # Missing string_match for HTTPS_STR_MATCH
            ("HTTPS_STR_MATCH", None, None, None, "string_match"),
            # Missing child_health_checks for CALCULATED
            ("CALCULATED", None, None, 2, "child_health_checks"),
            # Missing health_threshold for CALCULATED
            ("CALCULATED", None, ["check-1"], None, "health_threshold"),
            # Missing both for CALCULATED
            ("CALCULATED", None, None, None, "child_health_checks.*health_threshold"),
        ],
    )
    def test_missing_required_parameters(
        self, healthcheck_type, string_match, child_health_checks, health_threshold, expected_error
    ):
        """Test that missing required parameters raise appropriate errors."""
        with pytest.raises(AnsibleRoute53Error, match=f"missing required arguments.*{expected_error}"):
            validate_health_check_creation_params(
                healthcheck_type=healthcheck_type,
                string_match=string_match,
                child_health_checks=child_health_checks,
                health_threshold=health_threshold,
            )

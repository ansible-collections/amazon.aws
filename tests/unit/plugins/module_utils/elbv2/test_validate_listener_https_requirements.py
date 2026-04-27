# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import AnsibleELBv2Error


class TestValidateListenerHttpsRequirements:
    """Tests for validate_listener_https_requirements function"""

    def test_none_listeners(self):
        """Test with None listeners - should not raise error"""
        elbv2.validate_listener_https_requirements(None)

    def test_empty_listeners(self):
        """Test with empty list - should not raise error"""
        elbv2.validate_listener_https_requirements([])

    def test_http_listener_without_ssl(self):
        """Test HTTP listener without SSL config - should not raise error"""
        listeners = [
            {
                "Protocol": "HTTP",
                "Port": 80,
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            }
        ]
        elbv2.validate_listener_https_requirements(listeners)

    def test_https_listener_with_complete_ssl_config(self):
        """Test HTTPS listener with both SslPolicy and Certificates - should not raise error"""
        listeners = [
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "SslPolicy": "ELBSecurityPolicy-2016-08",
                "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/12345"}],
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            }
        ]
        elbv2.validate_listener_https_requirements(listeners)

    def test_https_listener_missing_ssl_policy(self):
        """Test HTTPS listener without SslPolicy - should raise AnsibleELBv2Error"""
        listeners = [
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/12345"}],
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            }
        ]
        with pytest.raises(
            AnsibleELBv2Error, match="'SslPolicy' is a required listener dict key when Protocol = HTTPS"
        ):
            elbv2.validate_listener_https_requirements(listeners)

    def test_https_listener_missing_certificates(self):
        """Test HTTPS listener without Certificates - should raise AnsibleELBv2Error"""
        listeners = [
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "SslPolicy": "ELBSecurityPolicy-2016-08",
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            }
        ]
        with pytest.raises(
            AnsibleELBv2Error, match="'Certificates' is a required listener dict key when Protocol = HTTPS"
        ):
            elbv2.validate_listener_https_requirements(listeners)

    def test_https_listener_missing_both(self):
        """Test HTTPS listener without both SslPolicy and Certificates - should raise AnsibleELBv2Error for SslPolicy first"""
        listeners = [
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            }
        ]
        with pytest.raises(
            AnsibleELBv2Error, match="'SslPolicy' is a required listener dict key when Protocol = HTTPS"
        ):
            elbv2.validate_listener_https_requirements(listeners)

    def test_multiple_listeners_with_one_https_invalid(self):
        """Test multiple listeners where one HTTPS listener is missing SslPolicy"""
        listeners = [
            {
                "Protocol": "HTTP",
                "Port": 80,
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            },
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/12345"}],
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            },
        ]
        with pytest.raises(
            AnsibleELBv2Error, match="'SslPolicy' is a required listener dict key when Protocol = HTTPS"
        ):
            elbv2.validate_listener_https_requirements(listeners)

    def test_multiple_https_listeners_all_valid(self):
        """Test multiple HTTPS listeners with complete SSL config - should not raise error"""
        listeners = [
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "SslPolicy": "ELBSecurityPolicy-2016-08",
                "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/12345"}],
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            },
            {
                "Protocol": "HTTPS",
                "Port": 8443,
                "SslPolicy": "ELBSecurityPolicy-TLS-1-2-2017-01",
                "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/67890"}],
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            },
        ]
        elbv2.validate_listener_https_requirements(listeners)

    def test_mixed_http_and_https_listeners(self):
        """Test mix of HTTP and HTTPS listeners with valid config - should not raise error"""
        listeners = [
            {
                "Protocol": "HTTP",
                "Port": 80,
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            },
            {
                "Protocol": "HTTPS",
                "Port": 443,
                "SslPolicy": "ELBSecurityPolicy-2016-08",
                "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/12345"}],
                "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}],
            },
        ]
        elbv2.validate_listener_https_requirements(listeners)

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_location
from ansible_collections.amazon.aws.plugins.module_utils.s3 import parse_s3_endpoint
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_extra_params


class TestParseS3Endpoint:
    def test_ceph_endpoint_returns_false_and_ceph_config(self):
        """Test that ceph option returns False and ceph endpoint config."""
        options = {"ceph": True, "endpoint_url": "http://ceph.example.com:8080"}

        is_aws, config = parse_s3_endpoint(options)

        assert is_aws is False
        assert config["endpoint"] == "http://ceph.example.com:8080"
        assert config["use_ssl"] is False

    def test_ceph_with_https_sets_use_ssl(self):
        """Test that ceph with https sets use_ssl to True."""
        options = {"ceph": True, "endpoint_url": "https://ceph.example.com"}

        is_aws, config = parse_s3_endpoint(options)

        assert is_aws is False
        assert config["use_ssl"] is True

    def test_fakes3_endpoint_returns_false_and_fakes3_config(self):
        """Test that fakes3:// URL returns False and fakes3 config."""
        options = {"endpoint_url": "fakes3://localhost:4567"}

        is_aws, config = parse_s3_endpoint(options)

        assert is_aws is False
        assert config["endpoint"] == "http://localhost:4567"
        assert config["use_ssl"] is False

    def test_fakes3s_endpoint_uses_https(self):
        """Test that fakes3s:// URL uses https."""
        options = {"endpoint_url": "fakes3s://localhost:4567"}

        is_aws, config = parse_s3_endpoint(options)

        assert is_aws is False
        assert config["endpoint"] == "https://localhost:4567"
        assert config["use_ssl"] is True

    def test_aws_endpoint_returns_true(self):
        """Test that regular AWS endpoint returns True."""
        options = {"endpoint_url": "https://s3.amazonaws.com"}

        is_aws, config = parse_s3_endpoint(options)

        assert is_aws is True
        assert config == {"endpoint": "https://s3.amazonaws.com"}

    def test_none_endpoint_returns_true(self):
        """Test that None endpoint_url returns True (default AWS)."""
        options = {}

        is_aws, config = parse_s3_endpoint(options)

        assert is_aws is True
        assert config == {"endpoint": None}


class TestS3ExtraParams:
    def test_non_aws_returns_params_as_is(self):
        """Test that non-AWS endpoints return params unchanged."""
        options = {"ceph": True, "endpoint_url": "http://ceph.example.com"}

        result = s3_extra_params(options, sigv4=False)

        assert result == {"endpoint": "http://ceph.example.com", "use_ssl": False}
        assert "config" not in result

    def test_aws_without_dualstack_or_sigv4_returns_params_as_is(self):
        """Test that AWS without special config returns params unchanged."""
        options = {"endpoint_url": "https://s3.amazonaws.com"}

        result = s3_extra_params(options, sigv4=False)

        assert result == {"endpoint": "https://s3.amazonaws.com"}
        assert "config" not in result

    def test_aws_with_dualstack_adds_config(self):
        """Test that dualstack option adds config."""
        options = {"endpoint_url": "https://s3.amazonaws.com", "dualstack": True}

        result = s3_extra_params(options, sigv4=False)

        assert result["endpoint"] == "https://s3.amazonaws.com"
        assert result["config"]["use_dualstack_endpoint"] is True
        assert "signature_version" not in result["config"]

    def test_aws_with_sigv4_adds_config(self):
        """Test that sigv4 parameter adds config."""
        options = {"endpoint_url": "https://s3.amazonaws.com"}

        result = s3_extra_params(options, sigv4=True)

        assert result["endpoint"] == "https://s3.amazonaws.com"
        assert result["config"]["signature_version"] == "s3v4"
        assert "use_dualstack_endpoint" not in result["config"]

    def test_aws_with_both_dualstack_and_sigv4(self):
        """Test that both dualstack and sigv4 are added to config."""
        options = {"endpoint_url": "https://s3.amazonaws.com", "dualstack": True}

        result = s3_extra_params(options, sigv4=True)

        assert result["endpoint"] == "https://s3.amazonaws.com"
        assert result["config"]["use_dualstack_endpoint"] is True
        assert result["config"]["signature_version"] == "s3v4"

    def test_dualstack_false_does_not_add_config(self):
        """Test that dualstack=False doesn't add config."""
        options = {"endpoint_url": "https://s3.amazonaws.com", "dualstack": False}

        result = s3_extra_params(options, sigv4=False)

        assert "config" not in result


class TestGetS3BucketLocation:
    def test_ceph_mode_returns_region_param(self):
        """Test that ceph mode returns the region parameter."""
        module = MagicMock()
        module.params.get.return_value = True
        module.params = {"ceph": True, "region": "us-west-1"}

        result = get_s3_bucket_location(module)

        assert result == "us-west-1"

    def test_normal_mode_with_region_returns_module_region(self):
        """Test that normal mode returns module.region."""
        module = MagicMock()
        module.params.get.return_value = False
        module.region = "eu-west-1"

        result = get_s3_bucket_location(module)

        assert result == "eu-west-1"

    def test_normal_mode_without_region_returns_default(self):
        """Test that normal mode without region returns us-east-1."""
        module = MagicMock()
        module.params.get.return_value = False
        module.region = None

        result = get_s3_bucket_location(module)

        assert result == "us-east-1"

    def test_ceph_mode_without_region_param(self):
        """Test that ceph mode without region returns None."""
        module = MagicMock()
        module.params = {"ceph": True}

        result = get_s3_bucket_location(module)

        assert result is None

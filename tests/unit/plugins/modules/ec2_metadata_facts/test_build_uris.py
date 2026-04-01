# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


class TestBuildUrisFromEndpoint:
    """Test the _build_uris_from_endpoint staticmethod."""

    def test_build_uris_with_default_endpoint(self):
        """Test URI generation with the default endpoint."""
        endpoint = "http://169.254.169.254"
        uris = ec2_metadata_facts.Ec2Metadata._build_uris_from_endpoint(endpoint)

        assert uris["token"] == "http://169.254.169.254/latest/api/token"
        assert uris["meta"] == "http://169.254.169.254/latest/meta-data/"
        assert uris["instance_tags"] == "http://169.254.169.254/latest/meta-data/tags/instance"
        assert uris["ssh"] == "http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key"
        assert uris["user"] == "http://169.254.169.254/latest/user-data/"
        assert uris["dynamic"] == "http://169.254.169.254/latest/dynamic/"

    def test_build_uris_with_custom_endpoint(self):
        """Test URI generation with a custom endpoint."""
        endpoint = "http://custom.endpoint.local:8080"
        uris = ec2_metadata_facts.Ec2Metadata._build_uris_from_endpoint(endpoint)

        assert uris["token"] == "http://custom.endpoint.local:8080/latest/api/token"
        assert uris["meta"] == "http://custom.endpoint.local:8080/latest/meta-data/"
        assert uris["instance_tags"] == "http://custom.endpoint.local:8080/latest/meta-data/tags/instance"
        assert uris["ssh"] == "http://custom.endpoint.local:8080/latest/meta-data/public-keys/0/openssh-key"
        assert uris["user"] == "http://custom.endpoint.local:8080/latest/user-data/"
        assert uris["dynamic"] == "http://custom.endpoint.local:8080/latest/dynamic/"

    def test_build_uris_with_trailing_slash(self):
        """Test URI generation when endpoint has a trailing slash."""
        endpoint = "http://169.254.169.254/"
        uris = ec2_metadata_facts.Ec2Metadata._build_uris_from_endpoint(endpoint)

        # Should handle trailing slash gracefully (double slashes)
        assert uris["token"] == "http://169.254.169.254//latest/api/token"
        assert uris["meta"] == "http://169.254.169.254//latest/meta-data/"


class TestEc2MetadataInit:
    """Test the Ec2Metadata __init__ method with endpoint parameter."""

    def test_init_with_default_endpoint(self):
        """Test initialization uses class default endpoint when none provided."""
        module = MagicMock()
        ec2_meta = ec2_metadata_facts.Ec2Metadata(module)

        assert ec2_meta.uri_token == "http://169.254.169.254/latest/api/token"
        assert ec2_meta.uri_meta == "http://169.254.169.254/latest/meta-data/"
        assert ec2_meta.uri_instance_tags == "http://169.254.169.254/latest/meta-data/tags/instance"
        assert ec2_meta.uri_ssh == "http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key"
        assert ec2_meta.uri_user == "http://169.254.169.254/latest/user-data/"
        assert ec2_meta.uri_dynamic == "http://169.254.169.254/latest/dynamic/"

    def test_init_with_custom_endpoint(self):
        """Test initialization with a custom endpoint."""
        module = MagicMock()
        custom_endpoint = "http://test.local:9000"
        ec2_meta = ec2_metadata_facts.Ec2Metadata(module, ec2_metadata_endpoint=custom_endpoint)

        assert ec2_meta.uri_token == "http://test.local:9000/latest/api/token"
        assert ec2_meta.uri_meta == "http://test.local:9000/latest/meta-data/"
        assert ec2_meta.uri_instance_tags == "http://test.local:9000/latest/meta-data/tags/instance"
        assert ec2_meta.uri_ssh == "http://test.local:9000/latest/meta-data/public-keys/0/openssh-key"
        assert ec2_meta.uri_user == "http://test.local:9000/latest/user-data/"
        assert ec2_meta.uri_dynamic == "http://test.local:9000/latest/dynamic/"

    def test_init_with_individual_uri_overrides(self):
        """Test that individual URI parameters still work for backward compatibility."""
        module = MagicMock()
        custom_token_uri = "http://custom.local/token"
        custom_meta_uri = "http://custom.local/metadata/"

        ec2_meta = ec2_metadata_facts.Ec2Metadata(
            module, ec2_metadata_token_uri=custom_token_uri, ec2_metadata_uri=custom_meta_uri
        )

        # Custom URIs should be used
        assert ec2_meta.uri_token == custom_token_uri
        assert ec2_meta.uri_meta == custom_meta_uri

        # Others should use default endpoint
        assert ec2_meta.uri_instance_tags == "http://169.254.169.254/latest/meta-data/tags/instance"
        assert ec2_meta.uri_ssh == "http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key"
        assert ec2_meta.uri_user == "http://169.254.169.254/latest/user-data/"
        assert ec2_meta.uri_dynamic == "http://169.254.169.254/latest/dynamic/"

    def test_init_endpoint_with_uri_override(self):
        """Test that URI overrides take precedence over endpoint-generated URIs."""
        module = MagicMock()
        custom_endpoint = "http://endpoint.local"
        custom_token_uri = "http://override.local/token"

        ec2_meta = ec2_metadata_facts.Ec2Metadata(
            module, ec2_metadata_endpoint=custom_endpoint, ec2_metadata_token_uri=custom_token_uri
        )

        # Token URI should use the override
        assert ec2_meta.uri_token == custom_token_uri

        # Others should use the custom endpoint
        assert ec2_meta.uri_meta == "http://endpoint.local/latest/meta-data/"
        assert ec2_meta.uri_instance_tags == "http://endpoint.local/latest/meta-data/tags/instance"
        assert ec2_meta.uri_ssh == "http://endpoint.local/latest/meta-data/public-keys/0/openssh-key"
        assert ec2_meta.uri_user == "http://endpoint.local/latest/user-data/"
        assert ec2_meta.uri_dynamic == "http://endpoint.local/latest/dynamic/"

    def test_init_sets_other_attributes(self):
        """Test that __init__ properly initializes other instance attributes."""
        module = MagicMock()
        ec2_meta = ec2_metadata_facts.Ec2Metadata(module)

        assert ec2_meta.module is module
        assert ec2_meta._data == {}
        assert ec2_meta._token is None
        assert ec2_meta._prefix == "ansible_ec2_%s"

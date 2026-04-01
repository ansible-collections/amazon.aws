# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


@pytest.fixture(name="ec2_instance")
def fixture_ec2_instance():
    module = MagicMock()
    return ec2_metadata_facts.Ec2Metadata(module)


def test_mangle_basic_fields(ec2_instance):
    """Test mangling basic metadata fields."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/ami-id": "ami-12345",
        "http://169.254.169.254/latest/meta-data/instance-id": "i-67890",
    }
    result = ec2_instance._mangle_fields(fields, uri)

    assert result["ansible_ec2_ami-id"] == "ami-12345"
    assert result["ansible_ec2_instance-id"] == "i-67890"


def test_mangle_nested_fields(ec2_instance):
    """Test mangling nested metadata fields."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/placement/availability-zone": "us-east-1a",
        "http://169.254.169.254/latest/meta-data/placement/region": "us-east-1",
    }
    result = ec2_instance._mangle_fields(fields, uri)

    assert result["ansible_ec2_placement-availability-zone"] == "us-east-1a"
    assert result["ansible_ec2_placement-region"] == "us-east-1"


def test_mangle_iam_role(ec2_instance):
    """Test that IAM role name is extracted correctly."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role": "credentials-data",
    }
    result = ec2_instance._mangle_fields(fields, uri)

    assert result["ansible_ec2_iam-instance-profile-role"] == "my-role"
    assert result["ansible_ec2_iam-security-credentials-my-role"] == "credentials-data"


def test_mangle_iam_json_fields(ec2_instance):
    """Test that IAM JSON fields don't create role name entry."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role:AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role:Code": "Success",
    }
    result = ec2_instance._mangle_fields(fields, uri)

    # Should not create iam-instance-profile-role because of colon
    assert "ansible_ec2_iam-instance-profile-role" not in result
    assert result["ansible_ec2_iam-security-credentials-my-role:AccessKeyId"] == "AKIAIOSFODNN7EXAMPLE"
    assert result["ansible_ec2_iam-security-credentials-my-role:Code"] == "Success"


def test_mangle_with_default_filter(ec2_instance):
    """Test that default filter pattern removes public-keys-0."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/ami-id": "ami-12345",
        "http://169.254.169.254/latest/meta-data/public-keys-0": "ssh-rsa ...",
    }
    result = ec2_instance._mangle_fields(fields, uri)

    assert "ansible_ec2_ami-id" in result
    assert "ansible_ec2_public-keys-0" not in result


def test_mangle_with_custom_filter(ec2_instance):
    """Test with custom filter patterns."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/ami-id": "ami-12345",
        "http://169.254.169.254/latest/meta-data/test-field": "test-value",
    }
    result = ec2_instance._mangle_fields(fields, uri, filter_patterns=["test"])

    assert "ansible_ec2_ami-id" in result
    assert "ansible_ec2_test-field" not in result


def test_mangle_empty_filter_patterns(ec2_instance):
    """Test with empty filter patterns list."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/ami-id": "ami-12345",
        "http://169.254.169.254/latest/meta-data/public-keys-0": "ssh-rsa ...",
    }
    result = ec2_instance._mangle_fields(fields, uri, filter_patterns=[])

    # Without filter patterns, everything should remain
    assert "ansible_ec2_ami-id" in result
    assert "ansible_ec2_public-keys-0" in result


def test_mangle_network_interface_fields(ec2_instance):
    """Test mangling complex network interface fields."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {
        "http://169.254.169.254/latest/meta-data/network/interfaces/macs/00:11:22:33:44:55/subnet-id": "subnet-12345",
        "http://169.254.169.254/latest/meta-data/network/interfaces/macs/00:11:22:33:44:55/vpc-id": "vpc-67890",
    }
    result = ec2_instance._mangle_fields(fields, uri)

    assert result["ansible_ec2_network-interfaces-macs-00:11:22:33:44:55-subnet-id"] == "subnet-12345"
    assert result["ansible_ec2_network-interfaces-macs-00:11:22:33:44:55-vpc-id"] == "vpc-67890"


def test_mangle_empty_fields(ec2_instance):
    """Test mangling with empty fields dict."""
    uri = "http://169.254.169.254/latest/meta-data/"
    fields = {}
    result = ec2_instance._mangle_fields(fields, uri)

    assert result == {}

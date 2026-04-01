# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


def test_build_field_uri_with_trailing_slash():
    """Test building URI when base URI has trailing slash."""
    uri = "http://169.254.169.254/latest/meta-data/"
    field = "ami-id"
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/ami-id"


def test_build_field_uri_without_trailing_slash():
    """Test building URI when base URI lacks trailing slash."""
    uri = "http://169.254.169.254/latest/meta-data"
    field = "ami-id"
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/ami-id"


def test_build_field_uri_nested_path():
    """Test building URI with nested path."""
    uri = "http://169.254.169.254/latest/meta-data/placement/"
    field = "availability-zone"
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/placement/availability-zone"


def test_build_field_uri_directory_field():
    """Test building URI when field is a directory (ends with /)."""
    uri = "http://169.254.169.254/latest/meta-data/"
    field = "network/"
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/network/"


def test_build_field_uri_complex_path():
    """Test building URI with complex nested path."""
    uri = "http://169.254.169.254/latest/meta-data/network/interfaces/macs/"
    field = "00:11:22:33:44:55/"
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/network/interfaces/macs/00:11:22:33:44:55/"


def test_build_field_uri_empty_field():
    """Test building URI with empty field."""
    uri = "http://169.254.169.254/latest/meta-data/"
    field = ""
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/"


def test_build_field_uri_field_with_special_chars():
    """Test building URI when field contains special characters."""
    uri = "http://169.254.169.254/latest/meta-data/"
    field = "iam/security-credentials"
    result = ec2_metadata_facts.Ec2Metadata._build_field_uri(uri, field)

    assert result == "http://169.254.169.254/latest/meta-data/iam/security-credentials"

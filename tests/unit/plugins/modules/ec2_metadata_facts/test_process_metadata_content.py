# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


@pytest.fixture(name="ec2_instance")
def fixture_ec2_instance():
    module = MagicMock()
    instance = ec2_metadata_facts.Ec2Metadata(module)
    instance._data = {}
    return instance


def test_process_security_groups(ec2_instance):
    """Test processing security-groups field."""
    new_uri = "http://169.254.169.254/latest/meta-data/security-groups"
    field = "security-groups"
    content = "sg-12345\nsg-67890\nsg-abcde"

    ec2_instance._process_metadata_content(new_uri, field, content)

    assert ec2_instance._data[new_uri] == "sg-12345,sg-67890,sg-abcde"


def test_process_security_group_ids(ec2_instance):
    """Test processing security-group-ids field."""
    new_uri = "http://169.254.169.254/latest/meta-data/security-group-ids"
    field = "security-group-ids"
    content = "sg-11111\nsg-22222"

    ec2_instance._process_metadata_content(new_uri, field, content)

    assert ec2_instance._data[new_uri] == "sg-11111,sg-22222"


def test_process_json_content(ec2_instance):
    """Test processing JSON content."""
    new_uri = "http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name"
    field = "role-name"
    json_data = {
        "Code": "Success",
        "LastUpdated": "2024-01-01T12:00:00Z",
        "Type": "AWS-HMAC",
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "Token": "token-value",
        "Expiration": "2024-01-01T18:00:00Z",
    }
    content = json.dumps(json_data)

    ec2_instance._process_metadata_content(new_uri, field, content)

    # Original content should be stored
    assert ec2_instance._data[new_uri] == content

    # Each JSON key-value should be stored with lowercase keys
    assert ec2_instance._data["{0}:code".format(new_uri)] == "Success"
    assert ec2_instance._data["{0}:lastupdated".format(new_uri)] == "2024-01-01T12:00:00Z"
    assert ec2_instance._data["{0}:type".format(new_uri)] == "AWS-HMAC"
    assert ec2_instance._data["{0}:accesskeyid".format(new_uri)] == "AKIAIOSFODNN7EXAMPLE"


def test_process_plain_text(ec2_instance):
    """Test processing plain text content."""
    new_uri = "http://169.254.169.254/latest/meta-data/ami-id"
    field = "ami-id"
    content = "ami-12345678"

    ec2_instance._process_metadata_content(new_uri, field, content)

    assert ec2_instance._data[new_uri] == "ami-12345678"


def test_process_invalid_json(ec2_instance):
    """Test processing content that looks like JSON but isn't valid."""
    new_uri = "http://169.254.169.254/latest/meta-data/hostname"
    field = "hostname"
    content = "{this is not valid json}"

    ec2_instance._process_metadata_content(new_uri, field, content)

    # Should store as-is when JSON parsing fails
    assert ec2_instance._data[new_uri] == "{this is not valid json}"


def test_process_empty_content(ec2_instance):
    """Test processing empty content."""
    new_uri = "http://169.254.169.254/latest/meta-data/empty"
    field = "empty"
    content = ""

    ec2_instance._process_metadata_content(new_uri, field, content)

    assert ec2_instance._data[new_uri] == ""


def test_process_multiline_plain_text(ec2_instance):
    """Test processing multiline plain text."""
    new_uri = "http://169.254.169.254/latest/user-data"
    field = "user-data"
    content = "#!/bin/bash\necho 'Hello World'\nexit 0"

    ec2_instance._process_metadata_content(new_uri, field, content)

    assert ec2_instance._data[new_uri] == "#!/bin/bash\necho 'Hello World'\nexit 0"


def test_process_json_with_nested_objects(ec2_instance):
    """Test processing JSON with nested objects."""
    new_uri = "http://169.254.169.254/latest/meta-data/test"
    field = "test"
    json_data = {"simple": "value", "nested": {"inner": "data"}, "array": [1, 2, 3]}
    content = json.dumps(json_data)

    ec2_instance._process_metadata_content(new_uri, field, content)

    # Original content stored
    assert ec2_instance._data[new_uri] == content

    # Flat keys stored with lowercase
    assert ec2_instance._data["{0}:simple".format(new_uri)] == "value"
    # Nested objects stored as-is
    assert ec2_instance._data["{0}:nested".format(new_uri)] == {"inner": "data"}
    assert ec2_instance._data["{0}:array".format(new_uri)] == [1, 2, 3]


def test_process_json_with_uppercase_keys(ec2_instance):
    """Test that JSON keys are converted to lowercase."""
    new_uri = "http://169.254.169.254/latest/meta-data/test"
    field = "test"
    json_data = {"UPPERCASE": "value", "MixedCase": "value2", "lowercase": "value3"}
    content = json.dumps(json_data)

    ec2_instance._process_metadata_content(new_uri, field, content)

    assert ec2_instance._data["{0}:uppercase".format(new_uri)] == "value"
    assert ec2_instance._data["{0}:mixedcase".format(new_uri)] == "value2"
    assert ec2_instance._data["{0}:lowercase".format(new_uri)] == "value3"

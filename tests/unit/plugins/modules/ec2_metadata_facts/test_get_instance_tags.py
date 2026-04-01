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


def test_get_single_tag(ec2_instance):
    """Test retrieving a single instance tag."""
    tag_keys = ["Name"]
    data = {"ansible_ec2_tags_instance_Name": "my-instance"}
    result = ec2_instance.get_instance_tags(tag_keys, data)

    assert result == {"Name": "my-instance"}


def test_get_multiple_tags(ec2_instance):
    """Test retrieving multiple instance tags."""
    tag_keys = ["Name", "Environment", "Project"]
    data = {
        "ansible_ec2_tags_instance_Name": "my-instance",
        "ansible_ec2_tags_instance_Environment": "production",
        "ansible_ec2_tags_instance_Project": "web-app",
    }
    result = ec2_instance.get_instance_tags(tag_keys, data)

    assert result == {"Name": "my-instance", "Environment": "production", "Project": "web-app"}


def test_get_missing_tag(ec2_instance):
    """Test retrieving tags when some are missing."""
    tag_keys = ["Name", "Environment", "MissingTag"]
    data = {
        "ansible_ec2_tags_instance_Name": "my-instance",
        "ansible_ec2_tags_instance_Environment": "production",
    }
    result = ec2_instance.get_instance_tags(tag_keys, data)

    # Only existing tags should be included
    assert result == {"Name": "my-instance", "Environment": "production"}
    assert "MissingTag" not in result


def test_get_no_tags(ec2_instance):
    """Test when no tags are available."""
    tag_keys = []
    data = {}
    result = ec2_instance.get_instance_tags(tag_keys, data)

    assert result == {}


def test_get_tags_with_special_characters(ec2_instance):
    """Test retrieving tags with special characters in keys."""
    tag_keys = ["aws:cloudformation:stack-name", "Cost-Center"]
    data = {
        "ansible_ec2_tags_instance_aws:cloudformation:stack-name": "my-stack",
        "ansible_ec2_tags_instance_Cost-Center": "engineering",
    }
    result = ec2_instance.get_instance_tags(tag_keys, data)

    assert result == {"aws:cloudformation:stack-name": "my-stack", "Cost-Center": "engineering"}


def test_get_tags_empty_values(ec2_instance):
    """Test retrieving tags with empty string values."""
    tag_keys = ["Name", "EmptyTag"]
    data = {"ansible_ec2_tags_instance_Name": "my-instance", "ansible_ec2_tags_instance_EmptyTag": ""}
    result = ec2_instance.get_instance_tags(tag_keys, data)

    assert result == {"Name": "my-instance", "EmptyTag": ""}

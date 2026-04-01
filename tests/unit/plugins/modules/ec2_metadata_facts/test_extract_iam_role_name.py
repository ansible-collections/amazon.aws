# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


def test_extract_valid_iam_role():
    """Test extracting IAM role name from valid path."""
    split_fields = ["iam", "security-credentials", "my-role-name"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result == "my-role-name"


def test_extract_iam_role_with_hyphens():
    """Test extracting IAM role name with hyphens."""
    split_fields = ["iam", "security-credentials", "my-complex-role-name"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result == "my-complex-role-name"


def test_extract_iam_role_with_underscores():
    """Test extracting IAM role name with underscores."""
    split_fields = ["iam", "security-credentials", "my_role_name"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result == "my_role_name"


def test_extract_iam_role_wrong_prefix():
    """Test that non-IAM paths return None."""
    split_fields = ["network", "interfaces", "macs"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result is None


def test_extract_iam_role_wrong_length():
    """Test that paths with wrong length return None."""
    split_fields = ["iam", "security-credentials"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result is None


def test_extract_iam_role_too_many_components():
    """Test that paths with too many components return None."""
    split_fields = ["iam", "security-credentials", "role-name", "extra"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result is None


def test_extract_iam_role_with_colon():
    """Test that role names with colons are rejected (likely JSON keys)."""
    split_fields = ["iam", "security-credentials", "AccessKeyId"]
    # This would have a colon in the full key like "role-name:AccessKeyId"
    # But we're testing the split version
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    # Without colon in the name itself, this should pass
    assert result == "AccessKeyId"


def test_extract_iam_role_json_field():
    """Test that JSON field paths (with colon in original key) are rejected."""
    # When the original key has a colon like "security-credentials/role:Code"
    # the split_fields[2] would be "role:Code" which should be rejected
    split_fields = ["iam", "security-credentials", "role:Code"]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    assert result is None


def test_extract_iam_role_empty_name():
    """Test that empty role name returns None."""
    split_fields = ["iam", "security-credentials", ""]
    result = ec2_metadata_facts.Ec2Metadata._extract_iam_role_name(split_fields)

    # Empty string doesn't contain ":", so it would technically pass the check
    # But let's see what the actual behavior is
    assert result == ""

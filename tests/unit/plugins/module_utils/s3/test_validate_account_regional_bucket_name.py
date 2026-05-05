# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import s3


@pytest.mark.parametrize(
    "bucket_name,region,result",
    [
        # Valid account-regional bucket names
        ("my-bucket-111122223333-us-east-1-an", None, None),
        ("my-bucket-111122223333-us-east-1-an", "us-east-1", None),
        ("test-bucket-123456789012-eu-west-1-an", "eu-west-1", None),
        ("prefix-999888777666-ap-south-1-an", None, None),
        ("a-111122223333-us-west-2-an", None, None),  # Minimal prefix
        # Invalid: too short
        ("ab", None, "account-regional bucket name must be at least 3 characters"),
        # Invalid: too long (>63 characters)
        (
            "this-is-a-very-long-bucket-name-prefix-111122223333-us-east-1-an",
            None,
            "account-regional bucket name cannot exceed 63 characters",
        ),
        # Invalid: doesn't end with -an
        ("my-bucket-111122223333-us-east-1", None, "account-regional bucket name must end with '-an'"),
        ("my-bucket-111122223333-us-east-1-xx", None, "account-regional bucket name must end with '-an'"),
        # Invalid: wrong format
        (
            "nobucketname-an",
            None,
            "account-regional bucket name must follow format: prefix-{12-digit-account-id}-{region}-an",
        ),
        (
            "prefix-12345-us-east-1-an",
            None,
            "account-regional bucket name must follow format: prefix-{12-digit-account-id}-{region}-an",
        ),
        (
            "prefix-1234567890123-us-east-1-an",
            None,
            "account-regional bucket name must follow format: prefix-{12-digit-account-id}-{region}-an",
        ),
        # Invalid: no prefix (regex won't match)
        (
            "-111122223333-us-east-1-an",
            None,
            "account-regional bucket name must follow format: prefix-{12-digit-account-id}-{region}-an",
        ),
        # Invalid: region mismatch
        (
            "my-bucket-111122223333-us-east-1-an",
            "us-west-2",
            "bucket name region 'us-east-1' does not match the bucket's configured region 'us-west-2'",
        ),
        (
            "test-bucket-123456789012-eu-west-1-an",
            "eu-central-1",
            "bucket name region 'eu-west-1' does not match the bucket's configured region 'eu-central-1'",
        ),
    ],
)
def test_validate_account_regional_bucket_name(bucket_name, region, result):
    assert result == s3.validate_account_regional_bucket_name(bucket_name, region)

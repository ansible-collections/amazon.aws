# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.plugin_utils.s3 import escape_path
from ansible_collections.amazon.aws.plugins.plugin_utils.s3 import generate_encryption_settings


@pytest.mark.parametrize(
    "bucket_sse_mode,bucket_sse_kms_key_id,args,headers",
    [
        (None, "We do not care about this", {}, {}),
        (
            "sse_no_kms",
            "sse_key_id",
            {"ServerSideEncryption": "sse_no_kms"},
            {"x-amz-server-side-encryption": "sse_no_kms"},
        ),
        ("aws:kms", "", {"ServerSideEncryption": "aws:kms"}, {"x-amz-server-side-encryption": "aws:kms"}),
        ("aws:kms", None, {"ServerSideEncryption": "aws:kms"}, {"x-amz-server-side-encryption": "aws:kms"}),
        (
            "aws:kms",
            "test_kms_id",
            {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": "test_kms_id"},
            {"x-amz-server-side-encryption": "aws:kms", "x-amz-server-side-encryption-aws-kms-key-id": "test_kms_id"},
        ),
    ],
)
def test_generate_encryption_settings(bucket_sse_mode, bucket_sse_kms_key_id, args, headers):
    """Test generate_encryption_settings() with various encryption modes."""
    r_args, r_headers = generate_encryption_settings(bucket_sse_mode, bucket_sse_kms_key_id)
    assert r_args == args
    assert r_headers == headers


@pytest.mark.parametrize(
    "input_path,expected_path",
    [
        ("path/to/file", "path/to/file"),
        ("path\\to\\file", "path/to/file"),
        ("C:\\Users\\test\\file.txt", "C:/Users/test/file.txt"),
        ("mixed/path\\to/file", "mixed/path/to/file"),
        ("already/unix/path", "already/unix/path"),
        ("", ""),
    ],
)
def test_escape_path(input_path, expected_path):
    """Test escape_path() converts backslashes to forward slashes for S3 compatibility."""
    result = escape_path(input_path)
    assert result == expected_path

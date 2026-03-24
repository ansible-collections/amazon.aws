# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Generic S3 utilities for AWS plugins."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Optional
    from typing import Tuple


def escape_path(path: str) -> str:
    """
    Converts a file path to S3-compatible format by replacing backslashes with forward slashes.

    S3 uses forward slashes as path separators regardless of the operating system.
    Windows paths with backslashes must be converted to ensure proper S3 key formatting.

    :param path: The file path to convert
    :returns: The path with forward slashes
    """
    return path.replace("\\", "/")


def generate_encryption_settings(
    bucket_sse_mode: Optional[str], bucket_sse_kms_key_id: Optional[str]
) -> Tuple[Dict, Dict]:
    """
    Generate S3 server-side encryption settings for boto3 and HTTP headers.

    :param bucket_sse_mode: Server-side encryption mode (e.g. 'AES256', 'aws:kms')
    :param bucket_sse_kms_key_id: KMS key ID for aws:kms encryption (optional)
    :returns: Tuple of (boto3_args, http_headers) containing encryption settings
    """
    args = {}
    headers = {}
    if not bucket_sse_mode:
        return args, headers

    args["ServerSideEncryption"] = bucket_sse_mode
    headers["x-amz-server-side-encryption"] = bucket_sse_mode
    if bucket_sse_mode == "aws:kms" and bucket_sse_kms_key_id:
        args["SSEKMSKeyId"] = bucket_sse_kms_key_id
        headers["x-amz-server-side-encryption-aws-kms-key-id"] = bucket_sse_kms_key_id
    return args, headers

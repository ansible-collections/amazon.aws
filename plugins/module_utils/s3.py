# -*- coding: utf-8 -*-

# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import string
import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Tuple
    from .retries import RetryingBotoClientWrapper

from urllib.parse import urlparse

try:
    from hashlib import md5

    HAS_MD5 = True
except ImportError:
    HAS_MD5 = False

try:
    import botocore
except ImportError:
    pass  # Handled by the calling module


from ansible.module_utils.basic import to_text

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

IGNORE_S3_DROP_IN_EXCEPTIONS = ["XNotImplemented", "NotImplemented", "AccessControlListNotSupported"]

from ._s3 import common as _common
from ._s3 import transformations as _transformations
from ._s3 import waiters as _waiters

S3ErrorHandler = _common.S3ErrorHandler

AnsibleS3Error = _common.AnsibleS3Error
AnsibleS3Sigv4RequiredError = _common.AnsibleS3Error
AnsibleS3PermissionsError = _common.AnsibleS3PermissionsError
AnsibleS3SupportError = _common.AnsibleS3SupportError
AnsibleS3RegionSupportError = _common.AnsibleS3RegionSupportError

normalize_s3_bucket_versioning = _transformations.normalize_s3_bucket_versioning
normalize_s3_bucket_public_access = _transformations.normalize_s3_bucket_public_access
normalize_s3_bucket_acls = _transformations.normalize_s3_bucket_acls
s3_acl_to_name = _transformations.s3_acl_to_name
merge_tags = _transformations.merge_tags


def get_s3_waiter(client: RetryingBotoClientWrapper, waiter_name: str) -> Any:
    return _waiters.waiter_factory.get_waiter(client, waiter_name)


@S3ErrorHandler.list_error_handler("get bucket encryption settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_accelerate_configuration(s3_client, bucket_name: str) -> Dict:
    """
    Get transfer accelerate configuration of the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Transfer accelerate status of the S3 bucket.
    """
    try:
        return s3_client.get_bucket_accelerate_configuration(Bucket=bucket_name)
    except is_boto3_error_code(["UnsupportedArgument", "MethodNotAllowed"]) as e:
        # aws-gov throws UnsupportedArgument (consistently)
        # aws throws MethodNotAllowed where acceleration isn't available /yet/
        raise AnsibleS3RegionSupportError(
            message="Failed to get bucket encryption settings (not available in S3 bucket region)", exception=e
        ) from e


@S3ErrorHandler.list_error_handler("get bucket ACLs", [])
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_acl(s3_client, bucket_name: str) -> List:
    """
    Get ACLs of the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Transfer accelerate status of the S3 bucket.
    """
    return s3_client.get_bucket_acl(Bucket=bucket_name)


@S3ErrorHandler.list_error_handler("get bucket encryption settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_encryption(client, bucket_name: str) -> Dict:
    """
    Retrieve the encryption configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Encryption configuration of the bucket.
    """
    return client.get_bucket_encryption(Bucket=bucket_name).get("ServerSideEncryptionConfiguration")


@S3ErrorHandler.list_error_handler("get bucket ownership settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_ownership_controls(client, bucket_name: str) -> Dict:
    """
    Retrieve bucket ownership controls for S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Bucket ownership controls of the bucket.
    """
    return client.get_bucket_ownership_controls(Bucket=bucket_name).get("OwnershipControls")


@S3ErrorHandler.list_error_handler("get bucket policy", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_policy(client, bucket_name: str) -> Dict:
    """
    Retrieve bucket policy for an S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Bucket policy controls of the bucket.
    """
    policy = client.get_bucket_policy(Bucket=bucket_name).get("Policy")
    try:
        return json.loads(policy)
    except ValueError as e:
        raise AnsibleS3Error(exception=e, message="Unable to parse current bucket policy") from e


@S3ErrorHandler.list_error_handler("get bucket request payment settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_request_payment(client, bucket_name: str) -> Dict:
    """
    Retrieve bucket request payment settings for an S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Request payment settings of the bucket.
    """
    return client.get_bucket_request_payment(Bucket=bucket_name).get("Payer")


@S3ErrorHandler.list_error_handler("get bucket tags", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_tagging(client, bucket_name: str) -> Dict:
    """
    Retrieve tagging for an S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The current tags dictionary applied to the bucket.
    """
    current_tags = client.get_bucket_tagging(Bucket=bucket_name).get("TagSet")
    return boto3_tag_list_to_ansible_dict(current_tags)


@S3ErrorHandler.list_error_handler("get bucket versioning settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_versioning(client, bucket_name: str) -> Dict:
    """
    Retrieve bucket versioning settings for an S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Versioning settings of the bucket.
    """
    return client.get_bucket_versioning(Bucket=bucket_name)


@S3ErrorHandler.list_error_handler("get bucket object lock settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_lock_configuration(client, bucket_name: str) -> Dict:
    """
    Retrieve object lock configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The object lock configuration of the bucket.
    """
    return client.get_object_lock_configuration(Bucket=bucket_name).get("ObjectLockConfiguration")


@S3ErrorHandler.list_error_handler("get bucket public access block settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_public_access_block(client, bucket_name: str) -> Dict:
    """
    Get current public access block configuration for a bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The current public access block configuration for the bucket.
    """
    return client.get_public_access_block(Bucket=bucket_name).get("PublicAccessBlockConfiguration")


@S3ErrorHandler.list_error_handler("determine if bucket exisits", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["OperationAborted"])
def head_s3_bucket(client, bucket_name: str) -> Dict:
    """
    Retrieve basic information about an S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Basic information about the bucket.
    """
    return client.head_bucket(Bucket=bucket_name)


def s3_head_objects(client, parts, bucket, obj, versionId):
    args = {"Bucket": bucket, "Key": obj}
    if versionId:
        args["VersionId"] = versionId

    for part in range(1, parts + 1):
        args["PartNumber"] = part
        yield client.head_object(**args)


def calculate_checksum_with_file(client, parts, bucket, obj, versionId, filename):
    digests = []
    with open(filename, "rb") as f:
        for head in s3_head_objects(client, parts, bucket, obj, versionId):
            digests.append(md5(f.read(int(head["ContentLength"]))).digest())

    digest_squared = b"".join(digests)
    return f'"{md5(digest_squared).hexdigest()}-{len(digests)}"'


def calculate_checksum_with_content(client, parts, bucket, obj, versionId, content):
    digests = []
    offset = 0
    for head in s3_head_objects(client, parts, bucket, obj, versionId):
        length = int(head["ContentLength"])
        digests.append(md5(content[offset:offset + length]).digest())  # fmt: skip
        offset += length

    digest_squared = b"".join(digests)
    return f'"{md5(digest_squared).hexdigest()}-{len(digests)}"'


def calculate_etag(module, filename, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if etag is not None and "-" in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split("-")[1])
        try:
            return calculate_checksum_with_file(s3, parts, bucket, obj, version, filename)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get head object")
    else:  # Compute the MD5 sum normally
        return f'"{module.md5(filename)}"'


def calculate_etag_content(module, content, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if etag is not None and "-" in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split("-")[1])
        try:
            return calculate_checksum_with_content(s3, parts, bucket, obj, version, content)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get head object")
    else:  # Compute the MD5 sum normally
        return f'"{md5(content).hexdigest()}"'


def validate_bucket_name(name):
    # See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
    if len(name) < 3:
        return "the length of an S3 bucket must be at least 3 characters"
    if len(name) > 63:
        return "the length of an S3 bucket cannot exceed 63 characters"

    legal_characters = string.ascii_lowercase + ".-" + string.digits
    illegal_characters = [c for c in name if c not in legal_characters]
    if illegal_characters:
        return "invalid character(s) found in the bucket name"
    if name[-1] not in string.ascii_lowercase + string.digits:
        return "bucket names must begin and end with a letter or number"
    return None


# Spot special case of fakes3.
def is_fakes3(url):
    """Return True if endpoint_url has scheme fakes3://"""
    result = False
    if url is not None:
        result = urlparse(url).scheme in ("fakes3", "fakes3s")
    return result


def parse_fakes3_endpoint(url):
    fakes3 = urlparse(url)
    protocol = "http"
    port = fakes3.port or 80
    if fakes3.scheme == "fakes3s":
        protocol = "https"
        port = fakes3.port or 443
    endpoint_url = f"{protocol}://{fakes3.hostname}:{to_text(port)}"
    use_ssl = bool(fakes3.scheme == "fakes3s")
    return {"endpoint": endpoint_url, "use_ssl": use_ssl}


def parse_ceph_endpoint(url):
    ceph = urlparse(url)
    use_ssl = bool(ceph.scheme == "https")
    return {"endpoint": url, "use_ssl": use_ssl}


def parse_s3_endpoint(options):
    endpoint_url = options.get("endpoint_url")
    if options.get("ceph"):
        return False, parse_ceph_endpoint(endpoint_url)
    if is_fakes3(endpoint_url):
        return False, parse_fakes3_endpoint(endpoint_url)
    return True, {"endpoint": endpoint_url}


def s3_extra_params(options, sigv4=False):
    aws, extra_params = parse_s3_endpoint(options)
    if not aws:
        return extra_params
    dualstack = options.get("dualstack")
    if not dualstack and not sigv4:
        return extra_params
    config: dict = {}
    if dualstack:
        config["use_dualstack_endpoint"] = True
    if sigv4:
        config["signature_version"] = "s3v4"
    extra_params["config"] = config
    return extra_params


@S3ErrorHandler.list_error_handler("get bucket inventory settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def _list_bucket_inventory_configurations(client, **params):
    return client.list_bucket_inventory_configurations(**params)


# _list_backup_inventory_configurations is a workaround for a missing paginator for listing
# bucket inventory configuration in boto3:
# https://github.com/boto/botocore/blob/1.34.141/botocore/data/s3/2006-03-01/paginators-1.json
def list_bucket_inventory_configurations(client, bucket_name: str) -> list:
    first_iteration = False
    next_token = None

    response = _list_bucket_inventory_configurations(client, Bucket=bucket_name)
    next_token = response.get("NextToken", None)

    if next_token is None:
        return response.get("InventoryConfigurationList", [])

    entries = []
    while next_token is not None:
        if first_iteration:
            response = _list_bucket_inventory_configurations(client, NextToken=next_token, Bucket=bucket_name)
        first_iteration = True
        entries.extend(response["InventoryConfigurationList"])
        next_token = response.get("NextToken")
    return entries


@AWSRetry.jittered_backoff()
def _list_objects_v2(client, **params):
    params = {k: v for k, v in params.items() if v is not None}
    # For practical purposes, the paginator ignores MaxKeys, if we've been passed MaxKeys we need to
    # explicitly call list_objects_v3 rather than re-use the paginator
    if params.get("MaxKeys", None) is not None:
        return client.list_objects_v2(**params)

    paginator = client.get_paginator("list_objects_v2")
    return paginator.paginate(**params).build_full_result()


def list_bucket_object_keys(client, bucket, prefix=None, max_keys=None, start_after=None):
    response = _list_objects_v2(client, Bucket=bucket, Prefix=prefix, StartAfter=start_after, MaxKeys=max_keys)
    return [c["Key"] for c in response.get("Contents", [])]


def get_s3_bucket_location(module):
    if module.params.get("ceph") is True:
        return module.params.get("region")
    return module.region or "us-east-1"

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
    from typing import Generator
    from typing import List
    from typing import Optional
    from typing import Tuple

    from .botocore import ClientType
    from .modules import AnsibleAWSModule

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
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
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
AnsibleS3ACLSupportError = _common.AnsibleS3ACLSupportError
AnsibleS3RegionSupportError = _common.AnsibleS3RegionSupportError

normalize_s3_bucket_versioning = _transformations.normalize_s3_bucket_versioning
normalize_s3_bucket_public_access = _transformations.normalize_s3_bucket_public_access
normalize_s3_bucket_acls = _transformations.normalize_s3_bucket_acls
s3_acl_to_name = _transformations.s3_acl_to_name
merge_tags = _transformations.merge_tags


# ========================================
# S3 Client Wrappers - Bucket Operations
# ========================================


def get_s3_waiter(client: ClientType, waiter_name: str) -> Any:
    return _waiters.waiter_factory.get_waiter(client, waiter_name)


@S3ErrorHandler.list_error_handler("get bucket accelerate configuration", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_accelerate_configuration(client: ClientType, bucket_name: str) -> Dict:
    """
    Get transfer accelerate configuration of the S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Transfer accelerate status of the S3 bucket.
    """
    try:
        return client.get_bucket_accelerate_configuration(Bucket=bucket_name)
    except is_boto3_error_code(["UnsupportedArgument", "MethodNotAllowed"]) as e:
        # aws-gov throws UnsupportedArgument (consistently)
        # aws throws MethodNotAllowed where acceleration isn't available /yet/
        raise AnsibleS3RegionSupportError(
            message="Failed to get bucket accelerate configuration (not available in S3 bucket region)", exception=e
        ) from e


@S3ErrorHandler.list_error_handler("get bucket ACLs", [])
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_acl(client: ClientType, bucket_name: str) -> List:
    """
    Get ACLs of the S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        ACL configuration of the S3 bucket.
    """
    return client.get_bucket_acl(Bucket=bucket_name)


@S3ErrorHandler.list_error_handler("get bucket encryption settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_encryption(client: ClientType, bucket_name: str) -> Dict:
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
def get_s3_bucket_ownership_controls(client: ClientType, bucket_name: str) -> Dict:
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
def get_s3_bucket_policy(client: ClientType, bucket_name: str) -> Dict:
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


@S3ErrorHandler.list_error_handler("get bucket public access block settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_public_access_block(client: ClientType, bucket_name: str) -> Dict:
    """
    Get current public access block configuration for a bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The current public access block configuration for the bucket.
    """
    return client.get_public_access_block(Bucket=bucket_name).get("PublicAccessBlockConfiguration")


@S3ErrorHandler.list_error_handler("get bucket request payment settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_bucket_request_payment(client: ClientType, bucket_name: str) -> Dict:
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
def get_s3_bucket_tagging(client: ClientType, bucket_name: str) -> Dict:
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
def get_s3_bucket_versioning(client: ClientType, bucket_name: str) -> Dict:
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
def get_s3_object_lock_configuration(client: ClientType, bucket_name: str) -> Dict:
    """
    Retrieve object lock configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The object lock configuration of the bucket.
    """
    return client.get_object_lock_configuration(Bucket=bucket_name).get("ObjectLockConfiguration")


@S3ErrorHandler.list_error_handler("determine if bucket exists", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["OperationAborted"])
def head_s3_bucket(client: ClientType, bucket_name: str) -> Dict:
    """
    Retrieve basic information about an S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Basic information about the bucket.
    """
    return client.head_bucket(Bucket=bucket_name)


@S3ErrorHandler.list_error_handler("get bucket location", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_location(client: ClientType, bucket_name: str) -> Dict:
    """
    Retrieve the AWS region where an S3 bucket is located.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.

    Returns:
        Dict: Bucket location information containing 'LocationConstraint'.
              Returns {} if bucket doesn't exist (404).
              Note: LocationConstraint is None for us-east-1 buckets.

    Raises:
        AnsibleS3PermissionsError: If access is denied (403).
        AnsibleS3Error: For other S3 errors.
    """
    return client.get_bucket_location(Bucket=bucket_name)


@AWSRetry.jittered_backoff()
def s3_bucket_exists(client: ClientType, bucket_name: str) -> bool:
    """
    Check if an S3 bucket exists.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.

    Returns:
        bool: True if bucket exists, False otherwise.

    Raises:
        AnsibleS3PermissionsError: If access is denied (403).
        AnsibleS3Error: For other S3 errors.
    """
    result = head_s3_bucket(client, bucket_name)
    return bool(result)


@S3ErrorHandler.list_error_handler("list buckets", [])
@AWSRetry.jittered_backoff()
def list_s3_buckets(client: ClientType) -> List[Dict]:
    """
    List all S3 buckets in the account.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.

    Returns:
        List[Dict]: List of bucket information dictionaries containing 'Name' and 'CreationDate'.
                    Returns [] on error.

    Raises:
        AnsibleS3PermissionsError: If access is denied (403).
        AnsibleS3Error: For other S3 errors.
    """
    return client.list_buckets().get("Buckets", [])


@S3ErrorHandler.list_error_handler("get bucket inventory settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def _list_bucket_inventory_configurations(client: ClientType, **params) -> Dict:
    return client.list_bucket_inventory_configurations(**params)


# _list_bucket_inventory_configurations is a workaround for a missing paginator for listing
# bucket inventory configuration in boto3:
# https://github.com/boto/botocore/blob/1.34.141/botocore/data/s3/2006-03-01/paginators-1.json
def list_bucket_inventory_configurations(client: ClientType, bucket_name: str) -> list:
    first_iteration_completed = False
    next_token = None

    response = _list_bucket_inventory_configurations(client, Bucket=bucket_name)
    next_token = response.get("NextToken", None)

    if next_token is None:
        return response.get("InventoryConfigurationList", [])

    entries = []
    while next_token is not None:
        if first_iteration_completed:
            response = _list_bucket_inventory_configurations(client, NextToken=next_token, Bucket=bucket_name)
        first_iteration_completed = True
        entries.extend(response["InventoryConfigurationList"])
        next_token = response.get("NextToken")
    return entries


@S3ErrorHandler.common_error_handler("set object lock configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_object_lock_configuration(client: ClientType, bucket_name: str, object_lock_default_retention: str) -> None:
    """
    Set object lock configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_lock_default_retention (dict): A dictionary containing the object
        lock default retention configuration to be set on the bucket.
    Returns:
        None
    """
    conf = {"ObjectLockEnabled": "Enabled", "Rule": {"DefaultRetention": object_lock_default_retention}}
    client.put_object_lock_configuration(Bucket=bucket_name, ObjectLockConfiguration=conf)


@S3ErrorHandler.common_error_handler("set bucket acceleration configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_accelerate_configuration(client: ClientType, bucket_name: str) -> None:
    """
    Enable transfer accelerate for the S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.put_bucket_accelerate_configuration(Bucket=bucket_name, AccelerateConfiguration={"Status": "Enabled"})


@S3ErrorHandler.common_error_handler("set bucket inventory configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_inventory(client: ClientType, bucket_name: str, inventory: dict) -> None:
    """
    Set inventory settings for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        inventory (dict): A dictionary containing the inventory settings to be set on the bucket.
    Returns:
        None
    """
    try:
        client.put_bucket_inventory_configuration(
            Bucket=bucket_name, InventoryConfiguration=inventory, Id=inventory.get("Id")
        )
    except is_boto3_error_code("InvalidS3DestinationBucket") as e:
        raise AnsibleS3Error("Invalid destination bucket ARN") from e


@S3ErrorHandler.common_error_handler("set bucket tagging")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_tagging(client: ClientType, bucket_name: str, tags: dict) -> None:
    """
    Set tags for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        tags (dict): A dictionary containing the tags to be set on the bucket.
    Returns:
        None
    """
    client.put_bucket_tagging(Bucket=bucket_name, Tagging={"TagSet": ansible_dict_to_boto3_tag_list(tags)})


@S3ErrorHandler.common_error_handler("set bucket policy")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_policy(client: ClientType, bucket_name: str, policy: dict) -> None:
    """
    Set the policy for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        policy (dict): A dictionary containing the policy to be set on the bucket.
    Returns:
        None
    """
    client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))


@S3ErrorHandler.common_error_handler("set bucket request payment configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_request_payment(client: ClientType, bucket_name: str, payer: str) -> None:
    """
    Set the request payment configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        payer (str): The entity responsible for charges related to fulfilling the request.
    Returns:
        None
    """
    client.put_bucket_request_payment(Bucket=bucket_name, RequestPaymentConfiguration={"Payer": payer})


@S3ErrorHandler.common_error_handler("set bucket versioning configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_versioning(client: ClientType, bucket_name: str, required_versioning: str) -> None:
    """
    Set the versioning configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        required_versioning (str): The desired versioning state for the bucket ("Enabled", "Suspended").
    Returns:
        None
    """
    client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={"Status": required_versioning})


@S3ErrorHandler.common_error_handler("set bucket encryption")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_encryption(client: ClientType, bucket_name: str, encryption: dict) -> None:
    """
    Set the encryption configuration for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        encryption (dict): A dictionary containing the encryption configuration.
    Returns:
        None
    """
    server_side_encryption_configuration = {"Rules": [{"ApplyServerSideEncryptionByDefault": encryption}]}
    client.put_bucket_encryption(
        Bucket=bucket_name, ServerSideEncryptionConfiguration=server_side_encryption_configuration
    )


@S3ErrorHandler.common_error_handler("set public access block configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_public_access(client: ClientType, bucket_name: str, public_access_config: dict) -> None:
    """
    Put new public access block to S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        public_access_config (dict): The public access block configuration.
    Returns:
        None
    """
    client.put_public_access_block(Bucket=bucket_name, PublicAccessBlockConfiguration=public_access_config)


@S3ErrorHandler.common_error_handler("set bucket ACL")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_acl(client: ClientType, bucket_name: str, acl: str) -> None:
    """
    Applies a canned ACL to an S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        acl (str): The ACL
    Returns:
        None
    """
    client.put_bucket_acl(Bucket=bucket_name, ACL=acl)


@S3ErrorHandler.common_error_handler("set bucket ownership controls")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_ownership(client: ClientType, bucket_name: str, object_ownership: str) -> None:
    """
    Put bucket ownership controls for S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_ownership (str): The object ownership control setting.
    Returns:
        None
    """
    client.put_bucket_ownership_controls(
        Bucket=bucket_name, OwnershipControls={"Rules": [{"ObjectOwnership": object_ownership}]}
    )


@S3ErrorHandler.deletion_error_handler("set bucket acceleration configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_accelerate_configuration(client: ClientType, bucket_name: str) -> None:
    """
    Disable transfer accelerate for the S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.put_bucket_accelerate_configuration(Bucket=bucket_name, AccelerateConfiguration={"Status": "Suspended"})


@S3ErrorHandler.deletion_error_handler("delete bucket inventory configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_inventory(client: ClientType, bucket_name: str, inventory_id: str) -> None:
    """
    Delete the inventory settings for an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        inventory_id (str): The ID used to identify the inventory configuration
    Returns:
        None
    """
    client.delete_bucket_inventory_configuration(Bucket=bucket_name, Id=inventory_id)


@S3ErrorHandler.deletion_error_handler("delete bucket tagging")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_tagging(client: ClientType, bucket_name: str) -> None:
    """
    Delete the tagging configuration of an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.delete_bucket_tagging(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete bucket encryption")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_encryption(client: ClientType, bucket_name: str) -> None:
    """
    Delete the encryption configuration of an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.delete_bucket_encryption(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete bucket")
@AWSRetry.jittered_backoff(max_delay=240, catch_extra_error_codes=["OperationAborted"])
def delete_s3_bucket(client: ClientType, bucket_name: str) -> None:
    """
    Delete an S3 bucket.
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.delete_bucket(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete bucket policy")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_policy(client: ClientType, bucket_name: str) -> None:
    """
    Delete policy from S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.delete_bucket_policy(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete public access block configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_public_access(client: ClientType, bucket_name: str) -> None:
    """
    Delete public access block from S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.delete_public_access_block(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete bucket ownership controls")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_ownership(client: ClientType, bucket_name: str) -> None:
    """
    Delete bucket ownership controls from S3 bucket
    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    client.delete_bucket_ownership_controls(Bucket=bucket_name)


# ========================================
# S3 Client Wrappers - Object Operations
# ========================================


@S3ErrorHandler.list_error_handler("get object metadata", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def head_s3_object(
    client: ClientType, bucket_name: str, object_key: str, version_id: Optional[str] = None, **kwargs
) -> Dict:
    """
    Retrieve metadata about an S3 object without downloading the object itself.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to head_object (e.g., ExpectedBucketOwner).

    Returns:
        Dict: Object metadata including ETag, ContentLength, LastModified, etc.
              Returns {} if object does not exist (404).
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    return client.head_object(**params)


@AWSRetry.jittered_backoff()
def s3_head_objects(
    client: ClientType, parts: int, bucket: str, obj: str, versionId: Optional[str]
) -> Generator[Dict, None, None]:
    """
    Generator that yields HEAD object responses for each part of a multipart upload.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        parts (int): Number of parts in the multipart upload.
        bucket (str): The S3 bucket name.
        obj (str): The S3 object key.
        versionId (str): Optional version ID of the object.

    Yields:
        HEAD object response dict for each part.
    """
    args = {"Bucket": bucket, "Key": obj}
    if versionId:
        args["VersionId"] = versionId

    for part in range(1, parts + 1):
        args["PartNumber"] = part
        yield client.head_object(**args)


@S3ErrorHandler.list_error_handler("get object content", None)
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_content(
    client: ClientType, bucket_name: str, object_key: str, version_id: Optional[str] = None, **kwargs
) -> Optional[bytes]:
    """
    Download the content of an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to get_object.

    Returns:
        bytes: The object content, or None if object does not exist (404).
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    response = client.get_object(**params)
    return response["Body"].read()


@S3ErrorHandler.list_error_handler("get object tags", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_tagging(
    client: ClientType, bucket_name: str, object_key: str, version_id: Optional[str] = None, **kwargs
) -> Dict:
    """
    Retrieve tags for an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to get_object_tagging (e.g., ExpectedBucketOwner).

    Returns:
        Dict: The current tags dictionary applied to the object.
              Returns {} if object has no tags or does not exist.
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    current_tags = client.get_object_tagging(**params).get("TagSet", [])
    return boto3_tag_list_to_ansible_dict(current_tags)


@S3ErrorHandler.list_error_handler("get object ACL", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_acl(
    client: ClientType, bucket_name: str, object_key: str, version_id: Optional[str] = None, **kwargs
) -> Dict:
    """
    Retrieve ACL for an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to get_object_acl.

    Returns:
        Dict: ACL information including Owner and Grants.
              Returns {} if object does not exist.
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    return client.get_object_acl(**params)


@S3ErrorHandler.list_error_handler("get object legal hold status", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_legal_hold(
    client: ClientType, bucket_name: str, object_key: str, version_id: Optional[str] = None, **kwargs
) -> Dict:
    """
    Retrieve legal hold status for an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to get_object_legal_hold.

    Returns:
        Dict: Legal hold configuration.
              Returns {} if not configured or object does not exist.
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    result = client.get_object_legal_hold(**params)
    return result.get("LegalHold", {})


@S3ErrorHandler.list_error_handler("get object retention settings", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_retention(
    client: ClientType, bucket_name: str, object_key: str, version_id: Optional[str] = None, **kwargs
) -> Dict:
    """
    Retrieve retention settings for an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to get_object_retention.

    Returns:
        Dict: Retention configuration.
              Returns {} if not configured or object does not exist.
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    result = client.get_object_retention(**params)
    return result.get("Retention", {})


@S3ErrorHandler.list_error_handler("get object attributes", {})
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_s3_object_attributes(
    client: ClientType,
    bucket_name: str,
    object_key: str,
    object_attributes: List[str],
    version_id: Optional[str] = None,
    **kwargs,
) -> Dict:
    """
    Retrieve specific attributes for an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        object_attributes (list): List of object attributes to retrieve
                                  (e.g., ['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize']).
        version_id (str, optional): The version ID of the object.
        **kwargs: Additional parameters to pass to get_object_attributes.

    Returns:
        Dict: Requested object attributes.
              Returns {} if object does not exist.
    """
    params = {
        "Bucket": bucket_name,
        "Key": object_key,
        "ObjectAttributes": object_attributes,
    }
    if version_id:
        params["VersionId"] = version_id
    params.update(kwargs)
    return client.get_object_attributes(**params)


@AWSRetry.jittered_backoff()
def s3_object_exists(
    client: ClientType,
    bucket_name: str,
    object_key: str,
    version_id: Optional[str] = None,
) -> bool:
    """
    Check if an S3 object exists.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        version_id (str, optional): The version ID of the object.

    Returns:
        bool: True if object exists, False otherwise.

    Raises:
        AnsibleS3PermissionsError: If access is denied (403).
        AnsibleS3Error: For other S3 errors.
    """
    result = head_s3_object(client, bucket_name, object_key, version_id)
    return bool(result)


@S3ErrorHandler.deletion_error_handler("delete object")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_object(client: ClientType, bucket_name: str, object_key: str, **kwargs) -> Dict:
    """
    Delete an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object to delete.
        **kwargs: Additional parameters to pass to delete_object.

    Returns:
        Dict: Response from the delete operation.
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    params.update(kwargs)
    return client.delete_object(**params)


@S3ErrorHandler.common_error_handler("update object tags")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_object_tagging(
    client: ClientType,
    bucket_name: str,
    object_key: str,
    tags: Dict,
    **kwargs,
) -> Dict:
    """
    Set tags on an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        tags (dict): Dictionary of tags to apply (e.g., {'Environment': 'prod', 'Owner': 'team'}).
        **kwargs: Additional parameters to pass to put_object_tagging.

    Returns:
        Dict: Response from the put operation.
    """
    params = {
        "Bucket": bucket_name,
        "Key": object_key,
        "Tagging": {"TagSet": ansible_dict_to_boto3_tag_list(tags)},
    }
    params.update(kwargs)
    return client.put_object_tagging(**params)


@S3ErrorHandler.deletion_error_handler("delete object tags")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_object_tagging(client: ClientType, bucket_name: str, object_key: str, **kwargs) -> Dict:
    """
    Remove all tags from an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        **kwargs: Additional parameters to pass to delete_object_tagging.

    Returns:
        Dict: Response from the delete operation.
    """
    params = {"Bucket": bucket_name, "Key": object_key}
    params.update(kwargs)
    return client.delete_object_tagging(**params)


@S3ErrorHandler.common_error_handler("update object ACL")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_object_acl(client: ClientType, bucket_name: str, object_key: str, acl: str, **kwargs) -> Dict:
    """
    Set ACL on an S3 object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        acl (str): The canned ACL to apply (e.g., 'private', 'public-read', 'authenticated-read').
        **kwargs: Additional parameters to pass to put_object_acl.

    Returns:
        Dict: Response from the put operation.
    """
    params = {"Bucket": bucket_name, "Key": object_key, "ACL": acl}
    params.update(kwargs)
    return client.put_object_acl(**params)


@S3ErrorHandler.common_error_handler("put object")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_object(client: ClientType, **params) -> Dict:
    """
    Upload an object to S3 using put_object.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        **params: Parameters to pass to put_object (must include Bucket, Key, and typically Body).

    Returns:
        Dict: Response from the put operation.
    """
    return client.put_object(**params)


@S3ErrorHandler.common_error_handler("upload file")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def upload_s3_file(
    client: ClientType,
    filename: str,
    bucket_name: str,
    object_key: str,
    extra_args: Optional[Dict] = None,
) -> None:
    """
    Upload a file to S3 using upload_file (transfer manager).

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        filename (str): Path to the file to upload.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key for the S3 object.
        extra_args (dict, optional): Extra arguments for the upload (e.g., ContentType, Metadata).

    Returns:
        None
    """
    if extra_args is None:
        extra_args = {}
    client.upload_file(Filename=filename, Bucket=bucket_name, Key=object_key, ExtraArgs=extra_args)


@S3ErrorHandler.common_error_handler("download file")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def download_s3_file(
    client: ClientType,
    bucket_name: str,
    object_key: str,
    filename: str,
    extra_args: Optional[Dict] = None,
) -> None:
    """
    Download a file from S3 using download_file (transfer manager).

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        filename (str): Path where the file should be saved.
        extra_args (dict, optional): Extra arguments for the download (e.g., VersionId).

    Returns:
        None
    """
    if extra_args is None:
        extra_args = {}
    client.download_file(Bucket=bucket_name, Key=object_key, Filename=filename, ExtraArgs=extra_args)


@S3ErrorHandler.common_error_handler("copy object")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def copy_s3_object(
    client: ClientType,
    copy_source: Dict,
    dest_bucket_name: str,
    dest_object_key: str,
    extra_args: Optional[Dict] = None,
) -> None:
    """
    Copy an object within S3 using managed copy (automatically handles multipart for large objects).

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        copy_source (dict): Source object specification with 'Bucket', 'Key', and optionally 'VersionId'.
        dest_bucket_name (str): The destination bucket name.
        dest_object_key (str): The destination object key.
        extra_args (dict, optional): Extra arguments for the copy operation (e.g., ACL, Metadata).

    Returns:
        None
    """
    if extra_args is None:
        extra_args = {}
    client.copy(copy_source, dest_bucket_name, dest_object_key, ExtraArgs=extra_args)


@AWSRetry.jittered_backoff()
def ensure_s3_object_tags(
    client: ClientType,
    bucket_name: str,
    object_key: str,
    desired_tags: Optional[Dict],
    purge_tags: bool = True,
    _max_attempts: int = 12,
    _sleep_time: float = 5.0,
) -> Tuple[Dict, bool]:
    """
    Ensure S3 object has desired tags, optionally purging unspecified tags.

    This function handles the complete tag management workflow:
    - Retrieves current tags
    - Compares with desired state
    - Updates or deletes tags as needed
    - Waits for tags to be applied

    Handles S3-compatible services that don't support tagging by returning empty tags
    when desired_tags is None.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        desired_tags (dict or None): Dictionary of desired tags. If None, tags are not modified.
        purge_tags (bool): If True, remove tags not in desired_tags. If False, merge with existing tags.
        _max_attempts (int): Maximum retry attempts for eventual consistency (internal/testing parameter).
        _sleep_time (float): Sleep time between retries in seconds (internal/testing parameter).

    Returns:
        Tuple[Dict, bool]: (current_tags, changed) - The current tags and whether changes were made.

    Raises:
        AnsibleS3Error: If tag operations fail and desired_tags is not None.
        AnsibleS3SupportError: If tagging is not supported and desired_tags is not None.
    """
    import time

    # Get current tags, handling S3-compatible services that don't support tagging
    try:
        current_tags_dict = get_s3_object_tagging(client, bucket_name, object_key)
    except AnsibleS3SupportError:
        # If tags weren't requested, silently handle unsupported tagging
        if desired_tags is None:
            return {}, False
        # If tags were requested, re-raise to indicate tagging is not supported
        raise

    # If no tags were requested, return current tags without changes
    if desired_tags is None:
        return current_tags_dict, False

    # Compute final tags using existing merge_tags helper
    final_tags = merge_tags(current_tags_dict, desired_tags, purge_tags)

    # Nothing to change
    if current_tags_dict == final_tags:
        return current_tags_dict, False

    # Apply tag changes
    if final_tags:
        put_s3_object_tagging(client, bucket_name, object_key, final_tags)
    else:
        delete_s3_object_tagging(client, bucket_name, object_key)

    # Wait for tags to be applied (eventual consistency)
    for _attempt in range(_max_attempts):
        current_tags_dict = get_s3_object_tagging(client, bucket_name, object_key)
        if current_tags_dict == final_tags:
            return current_tags_dict, True
        time.sleep(_sleep_time)

    # Tags didn't apply in time, but return what we have
    return current_tags_dict, True


@S3ErrorHandler.common_error_handler("generate presigned URL")
@AWSRetry.jittered_backoff()
def generate_s3_presigned_url(
    client: ClientType,
    bucket_name: str,
    object_key: str,
    client_method: str,
    expiry: int = 600,
    **params,
) -> str:
    """
    Generate a presigned URL for S3 object operations.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the S3 object.
        client_method (str): The boto3 client method name ('get_object', 'put_object', etc.).
        expiry (int): URL expiration time in seconds (default: 600).
        **params: Additional parameters for the presigned URL.

    Returns:
        str: The presigned URL, or empty string on error.

    Raises:
        AnsibleS3Error: If URL generation fails.
    """
    url_params = {"Bucket": bucket_name, "Key": object_key}
    url_params.update(params)

    return client.generate_presigned_url(ClientMethod=client_method, Params=url_params, ExpiresIn=expiry)


@AWSRetry.jittered_backoff()
def _list_objects_v2(client: ClientType, **params) -> Dict:
    params = {k: v for k, v in params.items() if v is not None}
    # For practical purposes, the paginator ignores MaxKeys, if we've been passed MaxKeys we need to
    # explicitly call list_objects_v3 rather than re-use the paginator
    if params.get("MaxKeys", None) is not None:
        return client.list_objects_v2(**params)

    paginator = client.get_paginator("list_objects_v2")
    return paginator.paginate(**params).build_full_result()


@S3ErrorHandler.list_error_handler("list bucket objects", [])
def list_bucket_object_keys(
    client: ClientType,
    bucket: str,
    prefix: Optional[str] = None,
    max_keys: Optional[int] = None,
    start_after: Optional[str] = None,
) -> List[str]:
    """
    List object keys in an S3 bucket with optional filtering.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        bucket (str): The name of the S3 bucket.
        prefix (str, optional): Limits the response to keys that begin with the specified prefix.
        max_keys (int, optional): Maximum number of keys to return.
        start_after (str, optional): StartAfter key for pagination.

    Returns:
        List[str]: List of object keys. Returns [] if bucket has no objects or on 404.

    Raises:
        AnsibleS3PermissionsError: If access is denied (403).
        AnsibleS3Error: For other S3 errors.
    """
    response = _list_objects_v2(client, Bucket=bucket, Prefix=prefix, StartAfter=start_after, MaxKeys=max_keys)
    return [c["Key"] for c in response.get("Contents", [])]


# ==========================================
# Transformation and Helper Functions
# ==========================================


def calculate_checksum_with_file(
    client: ClientType, parts: int, bucket: str, obj: str, versionId: Optional[str], filename: str
) -> str:
    """
    Calculate MD5 checksum for a multipart upload using a local file.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        parts (int): Number of parts in the multipart upload.
        bucket (str): The S3 bucket name.
        obj (str): The S3 object key.
        versionId (str): Optional version ID of the object.
        filename (str): Path to the local file.

    Returns:
        The ETag for the multipart upload in the format "{md5hash}-{parts}".
    """
    digests = []
    with open(filename, "rb") as f:
        for head in s3_head_objects(client, parts, bucket, obj, versionId):
            digests.append(md5(f.read(int(head["ContentLength"]))).digest())

    digest_squared = b"".join(digests)
    return f'"{md5(digest_squared).hexdigest()}-{len(digests)}"'


def calculate_checksum_with_content(
    client: ClientType, parts: int, bucket: str, obj: str, versionId: Optional[str], content: bytes
) -> str:
    """
    Calculate MD5 checksum for a multipart upload using in-memory content.

    Parameters:
        client (boto3.client): The Boto3 S3 client object.
        parts (int): Number of parts in the multipart upload.
        bucket (str): The S3 bucket name.
        obj (str): The S3 object key.
        versionId (str): Optional version ID of the object.
        content (bytes): The content bytes.

    Returns:
        The ETag for the multipart upload in the format "{md5hash}-{parts}".
    """
    digests = []
    offset = 0
    for head in s3_head_objects(client, parts, bucket, obj, versionId):
        length = int(head["ContentLength"])
        digests.append(md5(content[offset:offset + length]).digest())  # fmt: skip
        offset += length

    digest_squared = b"".join(digests)
    return f'"{md5(digest_squared).hexdigest()}-{len(digests)}"'


def calculate_etag(
    module: AnsibleAWSModule,
    filename: str,
    etag: Optional[str],
    client: ClientType,
    bucket: str,
    obj: str,
    version: Optional[str] = None,
) -> Optional[str]:
    """
    Calculate the ETag for a local file, handling both single-part and multipart uploads.

    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        filename (str): Path to the local file.
        etag (str): The ETag from S3 to determine if multipart.
        client (boto3.client): The Boto3 S3 client object.
        bucket (str): The S3 bucket name.
        obj (str): The S3 object key.
        version (str): Optional version ID of the object.

    Returns:
        The calculated ETag string, or None if MD5 is not available.
    """
    if not HAS_MD5:
        return None

    if etag is not None and "-" in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split("-")[1])
        try:
            return calculate_checksum_with_file(client, parts, bucket, obj, version, filename)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise AnsibleS3Error(message="Failed to calculate object ETag", exception=e) from e
    else:  # Compute the MD5 sum normally
        return f'"{module.md5(filename)}"'


def calculate_etag_content(
    module: AnsibleAWSModule,
    content: bytes,
    etag: Optional[str],
    client: ClientType,
    bucket: str,
    obj: str,
    version: Optional[str] = None,
) -> Optional[str]:
    """
    Calculate the ETag for in-memory content, handling both single-part and multipart uploads.

    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        content (bytes): The content bytes.
        etag (str): The ETag from S3 to determine if multipart.
        client (boto3.client): The Boto3 S3 client object.
        bucket (str): The S3 bucket name.
        obj (str): The S3 object key.
        version (str): Optional version ID of the object.

    Returns:
        The calculated ETag string, or None if MD5 is not available.
    """
    if not HAS_MD5:
        return None

    if etag is not None and "-" in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split("-")[1])
        try:
            return calculate_checksum_with_content(client, parts, bucket, obj, version, content)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise AnsibleS3Error(message="Failed to calculate object ETag", exception=e) from e
    else:  # Compute the MD5 sum normally
        return f'"{md5(content).hexdigest()}"'


def validate_bucket_name(name: str) -> Optional[str]:
    """
    Validate S3 bucket name against AWS naming rules.

    Parameters:
        name (str): The bucket name to validate.

    Returns:
        Error message string if validation fails, or None if valid.
    """
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
def is_fakes3(url: Optional[str]) -> bool:
    """Return True if endpoint_url has scheme fakes3://"""
    result = False
    if url is not None:
        result = urlparse(url).scheme in ("fakes3", "fakes3s")
    return result


def parse_fakes3_endpoint(url: str) -> Dict:
    """
    Parse a FakeS3 endpoint URL and extract connection parameters.

    Parameters:
        url (str): The FakeS3 endpoint URL (fakes3:// or fakes3s://).

    Returns:
        Dict with 'endpoint' URL and 'use_ssl' boolean.
    """
    fakes3 = urlparse(url)
    protocol = "http"
    port = fakes3.port or 80
    if fakes3.scheme == "fakes3s":
        protocol = "https"
        port = fakes3.port or 443
    endpoint_url = f"{protocol}://{fakes3.hostname}:{to_text(port)}"
    use_ssl = bool(fakes3.scheme == "fakes3s")
    return {"endpoint": endpoint_url, "use_ssl": use_ssl}


def parse_ceph_endpoint(url: str) -> Dict:
    """
    Parse a Ceph endpoint URL and extract connection parameters.

    Parameters:
        url (str): The Ceph endpoint URL.

    Returns:
        Dict with 'endpoint' URL and 'use_ssl' boolean.
    """
    ceph = urlparse(url)
    use_ssl = bool(ceph.scheme == "https")
    return {"endpoint": url, "use_ssl": use_ssl}


def parse_s3_endpoint(options: Dict) -> Tuple[bool, Dict]:
    """
    Parse S3 endpoint options and determine connection parameters.

    Parameters:
        options (dict): Dictionary containing endpoint_url, ceph flag, etc.

    Returns:
        Tuple of (is_aws_s3, connection_params_dict).
    """
    endpoint_url = options.get("endpoint_url")
    if options.get("ceph"):
        return False, parse_ceph_endpoint(endpoint_url)
    if is_fakes3(endpoint_url):
        return False, parse_fakes3_endpoint(endpoint_url)
    return True, {"endpoint": endpoint_url}


def s3_extra_params(options: Dict, sigv4: bool = False) -> Dict:
    """
    Build extra parameters for S3 client connection.

    Parameters:
        options (dict): Dictionary containing connection options.
        sigv4 (bool): Whether to use signature version 4.

    Returns:
        Dict of extra connection parameters for boto3 client.
    """
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


def get_s3_bucket_location(module: AnsibleAWSModule) -> str:
    """
    Determine the S3 bucket location/region from module parameters.

    Parameters:
        module (AnsibleAWSModule): The Ansible module object.

    Returns:
        The region string for the S3 bucket location.
    """
    if module.params.get("ceph") is True:
        return module.params.get("region")
    return module.region or "us-east-1"

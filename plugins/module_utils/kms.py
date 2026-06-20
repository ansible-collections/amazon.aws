# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import typing

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

# pylint: disable-next=unused-import
from ansible_collections.amazon.aws.plugins.module_utils._kms.common import AnsibleKMSError
from ansible_collections.amazon.aws.plugins.module_utils._kms.common import KMSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


@KMSErrorHandler.common_error_handler("list KMS keys")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_keys(client: ClientType) -> dict:
    paginator = client.get_paginator("list_keys")
    return paginator.paginate().build_full_result()


@KMSErrorHandler.common_error_handler("list KMS aliases")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_aliases(client: ClientType) -> dict:
    paginator = client.get_paginator("list_aliases")
    return paginator.paginate().build_full_result()


def get_kms_aliases_lookup(client: ClientType) -> dict[str, list[str]]:
    """Build a lookup dictionary of key_id -> list of aliases"""
    _aliases = {}
    for alias in get_kms_aliases(client)["Aliases"]:
        # Not all aliases are actually associated with a key
        if "TargetKeyId" in alias:
            # strip off leading 'alias/' and add it to key's aliases
            if alias["TargetKeyId"] in _aliases:
                _aliases[alias["TargetKeyId"]].append(alias["AliasName"][6:])
            else:
                _aliases[alias["TargetKeyId"]] = [alias["AliasName"][6:]]
    return _aliases


@KMSErrorHandler.common_error_handler("list KMS resource tags")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def _list_resource_tags(client: ClientType, key_id: str, **kwargs) -> dict:
    return client.list_resource_tags(KeyId=key_id, **kwargs)


def get_kms_tags(client: ClientType, key_id: str) -> list[dict]:
    """Get all tags for a KMS key, handling pagination"""
    kwargs = {}
    tags = []
    more = True
    while more:
        try:
            tag_response = _list_resource_tags(client, key_id, **kwargs)
            tags.extend(tag_response["Tags"])
        except is_boto3_error_code("AccessDeniedException"):
            tag_response = {}
        if tag_response.get("NextMarker"):
            kwargs["Marker"] = tag_response["NextMarker"]
        else:
            more = False
    return tags


@KMSErrorHandler.common_error_handler("list KMS grants")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_grants(client: ClientType, key_id: str) -> dict:
    params = {"KeyId": key_id}
    paginator = client.get_paginator("list_grants")
    return paginator.paginate(**params).build_full_result()


@KMSErrorHandler.list_error_handler("describe KMS key", default_value=None)
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_metadata(client: ClientType, key_id: str) -> dict | None:
    result = client.describe_key(KeyId=key_id)
    return result.get("KeyMetadata") if result else None


@KMSErrorHandler.common_error_handler("list key policies")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def list_key_policies(client: ClientType, key_id: str) -> dict:
    paginator = client.get_paginator("list_key_policies")
    return paginator.paginate(KeyId=key_id).build_full_result()


@KMSErrorHandler.list_error_handler("get key policy", default_value=None)
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_key_policy(client: ClientType, key_id: str, policy_name: str) -> dict | None:
    return client.get_key_policy(KeyId=key_id, PolicyName=policy_name)


def get_kms_policies(client: ClientType, key_id: str) -> list[str]:
    """Get all policy documents for a KMS key"""
    try:
        policies = list_key_policies(client, key_id)["PolicyNames"]
        return [get_key_policy(client, key_id, policy)["Policy"] for policy in policies]
    except is_boto3_error_code("AccessDeniedException"):
        return []


def camel_to_snake_grant(grant: dict) -> dict:
    """Convert grant dict to snake_case, preserving encryption context"""
    constraints = grant.get("Constraints", {})
    result = camel_dict_to_snake_dict(grant)
    if "EncryptionContextEquals" in constraints:
        result["constraints"]["encryption_context_equals"] = constraints["EncryptionContextEquals"]
    if "EncryptionContextSubset" in constraints:
        result["constraints"]["encryption_context_subset"] = constraints["EncryptionContextSubset"]
    return result


def get_key_details(client: ClientType, key_id: str) -> dict:
    """Get comprehensive details about a KMS key including metadata, grants, tags, and policies"""
    result = get_kms_metadata(client, key_id)
    if not result:
        raise AnsibleKMSError(message=f"Key {key_id} not found")

    result["KeyArn"] = result.pop("Arn")

    try:
        aliases = get_kms_aliases_lookup(client)
    except AnsibleKMSError as e:
        raise AnsibleKMSError(message="Failed to obtain aliases", exception=e.exception) from e

    try:
        current_rotation_status = client.get_key_rotation_status(KeyId=key_id)
        result["enable_key_rotation"] = current_rotation_status.get("KeyRotationEnabled")
    except is_boto3_error_code(["AccessDeniedException", "UnsupportedOperationException"]):
        result["enable_key_rotation"] = None

    result["aliases"] = aliases.get(result["KeyId"], [])
    result = camel_dict_to_snake_dict(result)

    # grants and tags get snakified differently
    result["grants"] = [camel_to_snake_grant(grant) for grant in get_kms_grants(client, key_id)["Grants"]]
    tags = get_kms_tags(client, key_id)
    result["tags"] = boto3_tag_list_to_ansible_dict(tags, "TagKey", "TagValue")
    policies = get_kms_policies(client, key_id)
    result["key_policies"] = [json.loads(policy) for policy in policies]

    return result

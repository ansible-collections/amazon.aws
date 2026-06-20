# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import typing

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

# Intended for general use / re-import
# pylint: disable=unused-import,useless-import-alias
from ._kms.common import AnsibleKMSError as AnsibleKMSError
from ._kms.common import KMSErrorHandler as KMSErrorHandler

# pylint: enable=unused-import,useless-import-alias


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
        current_rotation_status = get_key_rotation_status(client, key_id)
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


# Key rotation operations


@KMSErrorHandler.common_error_handler("get key rotation status")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_key_rotation_status(client: ClientType, key_id: str) -> dict:
    return client.get_key_rotation_status(KeyId=key_id)


@KMSErrorHandler.common_error_handler("enable key rotation")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def enable_key_rotation(client: ClientType, key_id: str) -> dict:
    return client.enable_key_rotation(KeyId=key_id)


@KMSErrorHandler.common_error_handler("disable key rotation")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def disable_key_rotation(client: ClientType, key_id: str) -> dict:
    return client.disable_key_rotation(KeyId=key_id)


# Key state operations


@KMSErrorHandler.common_error_handler("enable key")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def enable_key(client: ClientType, key_id: str) -> dict:
    return client.enable_key(KeyId=key_id)


@KMSErrorHandler.common_error_handler("disable key")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def disable_key(client: ClientType, key_id: str) -> dict:
    return client.disable_key(KeyId=key_id)


@KMSErrorHandler.common_error_handler("schedule key deletion")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def schedule_key_deletion(client: ClientType, key_id: str, pending_window_in_days: int | None = None) -> dict:
    params = {"KeyId": key_id}
    if pending_window_in_days is not None:
        params["PendingWindowInDays"] = pending_window_in_days
    return client.schedule_key_deletion(**params)


@KMSErrorHandler.common_error_handler("cancel key deletion")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def cancel_key_deletion(client: ClientType, key_id: str) -> dict:
    return client.cancel_key_deletion(KeyId=key_id)


# Key creation and modification


@KMSErrorHandler.common_error_handler("create key")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def create_key(client: ClientType, **params) -> dict:
    return client.create_key(**params)


@KMSErrorHandler.common_error_handler("update key description")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def update_key_description(client: ClientType, key_id: str, description: str) -> dict:
    return client.update_key_description(KeyId=key_id, Description=description)


@KMSErrorHandler.common_error_handler("put key policy")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def put_key_policy(client: ClientType, key_id: str, policy_name: str, policy: str) -> dict:
    return client.put_key_policy(KeyId=key_id, PolicyName=policy_name, Policy=policy)


# Alias operations


@KMSErrorHandler.common_error_handler("create alias")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def create_alias(client: ClientType, alias_name: str, target_key_id: str) -> dict:
    return client.create_alias(AliasName=alias_name, TargetKeyId=target_key_id)


# Tag operations


@KMSErrorHandler.common_error_handler("tag resource")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def tag_resource(client: ClientType, key_id: str, tags: list[dict]) -> dict:
    return client.tag_resource(KeyId=key_id, Tags=tags)


@KMSErrorHandler.common_error_handler("untag resource")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def untag_resource(client: ClientType, key_id: str, tag_keys: list[str]) -> dict:
    return client.untag_resource(KeyId=key_id, TagKeys=tag_keys)


# Grant operations


@KMSErrorHandler.common_error_handler("create grant")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def create_grant(client: ClientType, **params) -> dict:
    return client.create_grant(**params)


@KMSErrorHandler.common_error_handler("retire grant")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def retire_grant(client: ClientType, key_id: str, grant_id: str) -> dict:
    return client.retire_grant(KeyId=key_id, GrantId=grant_id)

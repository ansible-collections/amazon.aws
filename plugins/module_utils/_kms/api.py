# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Minimal API wrappers for KMS operations with error handling and retries.

This module contains thin wrappers around boto3 KMS client methods.
Each function is decorated with:
- KMSErrorHandler for consistent error handling and exception conversion
- AWSRetry for automatic retry with exponential backoff

Functions here should be minimal - parameter manipulation is acceptable,
but complex business logic belongs in the parent kms.py module.
"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from .common import KMSErrorHandler

# Key and alias listing


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


# Tag operations


@KMSErrorHandler.common_error_handler("list KMS resource tags")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_tags(client: ClientType, key_id: str) -> dict:
    paginator = client.get_paginator("list_resource_tags")
    return paginator.paginate(KeyId=key_id).build_full_result()


@KMSErrorHandler.common_error_handler("list KMS resource tags")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def list_resource_tags(client: ClientType, key_id: str, **kwargs) -> dict:
    return client.list_resource_tags(KeyId=key_id, **kwargs)


@KMSErrorHandler.common_error_handler("tag resource")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def tag_resource(client: ClientType, key_id: str, tags: list[dict]) -> dict:
    return client.tag_resource(KeyId=key_id, Tags=tags)


@KMSErrorHandler.common_error_handler("untag resource")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def untag_resource(client: ClientType, key_id: str, tag_keys: list[str]) -> dict:
    return client.untag_resource(KeyId=key_id, TagKeys=tag_keys)


# Grant operations


@KMSErrorHandler.common_error_handler("list KMS grants")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_grants(client: ClientType, key_id: str, grant_tokens: list[str] | None = None) -> dict:
    params = {"KeyId": key_id}
    if grant_tokens:
        params["GrantTokens"] = grant_tokens
    paginator = client.get_paginator("list_grants")
    return paginator.paginate(**params).build_full_result()


@KMSErrorHandler.common_error_handler("create grant")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def create_grant(client: ClientType, **params) -> dict:
    return client.create_grant(**params)


@KMSErrorHandler.common_error_handler("retire grant")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def retire_grant(client: ClientType, key_id: str, grant_id: str) -> dict:
    return client.retire_grant(KeyId=key_id, GrantId=grant_id)


# Key metadata and details


@KMSErrorHandler.list_error_handler("describe KMS key", default_value=None)
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_metadata(client: ClientType, key_id: str) -> dict | None:
    result = client.describe_key(KeyId=key_id)
    return result.get("KeyMetadata") if result else None


# Policy operations


@KMSErrorHandler.common_error_handler("list key policies")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def list_key_policies(client: ClientType, key_id: str) -> dict:
    paginator = client.get_paginator("list_key_policies")
    return paginator.paginate(KeyId=key_id).build_full_result()


@KMSErrorHandler.list_error_handler("get key policy", default_value=None)
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_key_policy(client: ClientType, key_id: str, policy_name: str) -> dict | None:
    return client.get_key_policy(KeyId=key_id, PolicyName=policy_name)


@KMSErrorHandler.common_error_handler("put key policy")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def put_key_policy(client: ClientType, key_id: str, policy_name: str, policy: str) -> dict:
    return client.put_key_policy(KeyId=key_id, PolicyName=policy_name, Policy=policy)


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


# Alias operations


@KMSErrorHandler.common_error_handler("create alias")
@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def create_alias(client: ClientType, alias_name: str, target_key_id: str) -> dict:
    return client.create_alias(AliasName=alias_name, TargetKeyId=target_key_id)

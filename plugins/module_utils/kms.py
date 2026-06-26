# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Public API for KMS operations in Ansible modules.

This module provides the main interface for working with AWS KMS from Ansible modules.
It re-exports low-level API functions from _kms.api, exception classes from _kms.common,
and transformation utilities from _kms.transformations.

Primary functions:
- get_key_details(): Get comprehensive key information including metadata, grants, tags, policies
- get_kms_aliases_lookup(): Build key_id -> aliases mapping
- get_kms_policy_as_dict(): Get a single policy as a parsed dictionary
- get_kms_policies(): Get all policies for a key as JSON strings

Low-level API functions (re-exported from _kms.api):
All functions are decorated with error handling (KMSErrorHandler) and automatic retry (AWSRetry).
Paginated operations use build_full_result() for consistency.

Exception hierarchy:
- AnsibleKMSError: Base exception for all KMS errors
  - AnsibleKMSPermissionsError: Permission denied errors (AccessDeniedException)
  - AnsibleKMSUnsupportedError: Unsupported operation errors (UnsupportedOperationException)
"""

from __future__ import annotations

import json
import typing

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

# Not intended for general re-use / re-import
from ._kms import transformations as _transformations

# Intended for general use / re-import
# pylint: disable=unused-import,useless-import-alias
from ._kms.api import cancel_key_deletion as cancel_key_deletion
from ._kms.api import create_alias as create_alias
from ._kms.api import create_grant as create_grant
from ._kms.api import create_key as create_key
from ._kms.api import disable_key as disable_key
from ._kms.api import disable_key_rotation as disable_key_rotation
from ._kms.api import enable_key as enable_key
from ._kms.api import enable_key_rotation as enable_key_rotation
from ._kms.api import get_key_policy as get_key_policy
from ._kms.api import get_key_rotation_status as get_key_rotation_status
from ._kms.api import get_kms_aliases as get_kms_aliases
from ._kms.api import get_kms_grants as get_kms_grants
from ._kms.api import get_kms_keys as get_kms_keys
from ._kms.api import get_kms_metadata as get_kms_metadata
from ._kms.api import get_kms_tags as get_kms_tags
from ._kms.api import list_key_policies as list_key_policies
from ._kms.api import list_resource_tags as list_resource_tags
from ._kms.api import put_key_policy as put_key_policy
from ._kms.api import retire_grant as retire_grant
from ._kms.api import schedule_key_deletion as schedule_key_deletion
from ._kms.api import tag_resource as tag_resource
from ._kms.api import untag_resource as untag_resource
from ._kms.api import update_key_description as update_key_description
from ._kms.common import AnsibleKMSError as AnsibleKMSError
from ._kms.common import AnsibleKMSPermissionsError as AnsibleKMSPermissionsError
from ._kms.common import AnsibleKMSUnsupportedError as AnsibleKMSUnsupportedError
from ._kms.common import KMSErrorHandler as KMSErrorHandler
from ._kms.transformations import canonicalize_alias_name as canonicalize_alias_name
from ._kms.transformations import normalize_kms_key_details as normalize_kms_key_details

# pylint: enable=unused-import,useless-import-alias


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


def get_kms_policy_as_dict(client: ClientType, key_id: str, policy_name: str = "default") -> dict | None:
    """
    Get a single KMS key policy document as a parsed dictionary.

    Args:
        client: boto3 KMS client
        key_id: KMS key ID or ARN
        policy_name: Name of the policy (default: "default")

    Returns:
        Policy document as a dictionary, or None if not found/permission denied

    Raises:
        AnsibleKMSPermissionsError: when permission denied
    """
    result = get_key_policy(client, key_id, policy_name)
    if result is None:
        return None
    return json.loads(result["Policy"])


def get_kms_policies(client: ClientType, key_id: str) -> list[str]:
    """
    Get all policy documents for a KMS key as JSON strings.

    Args:
        client: boto3 KMS client
        key_id: KMS key ID or ARN

    Returns:
        List of policy documents as JSON strings

    Raises:
        AnsibleKMSPermissionsError: when permission denied
    """
    policies = list_key_policies(client, key_id)["PolicyNames"]
    return [get_key_policy(client, key_id, policy)["Policy"] for policy in policies]


def get_key_details(
    client: ClientType, key_id: str, grant_tokens: list[str] | None = None, pending_deletion: bool = False
) -> dict | None:
    """
    Get comprehensive details about a KMS key including metadata, grants, tags, and policies.

    Args:
        client: boto3 KMS client
        key_id: KMS key ID, ARN, or alias
        grant_tokens: optional list of grant tokens to include when fetching grants
        pending_deletion: if True, returns minimal details (metadata only) for keys pending deletion

    Returns:
        Dictionary with key details in Ansible format, or None if key not found

    Raises:
        AnsibleKMSError: when key not found or other errors occur
        AnsibleKMSPermissionsError: when permission denied fetching grants, tags, or policies
                                    (caller should handle and warn user if appropriate)
        AnsibleKMSUnsupportedError: when operation not supported for key type

    Note:
        Permission errors for rotation status are caught and result in enable_key_rotation=None.
        Permission errors for grants, tags, or policies will propagate to the caller.
    """
    result = get_kms_metadata(client, key_id)
    if not result:
        return None

    # Make sure we have the canonical ARN, we might have been passed an alias
    key_id = result["Arn"]
    result["KeyArn"] = result.pop("Arn")

    try:
        aliases = get_kms_aliases_lookup(client)
    except AnsibleKMSError as e:
        raise AnsibleKMSError(message="Failed to obtain aliases", exception=e.exception) from e

    try:
        current_rotation_status = get_key_rotation_status(client, key_id)
        result["enable_key_rotation"] = current_rotation_status.get("KeyRotationEnabled")
    except (AnsibleKMSPermissionsError, AnsibleKMSUnsupportedError):
        result["enable_key_rotation"] = None

    result["aliases"] = aliases.get(result["KeyId"], [])

    # For keys pending deletion, return minimal details (metadata + aliases + rotation only)
    if pending_deletion:
        return _transformations.normalize_kms_key_details(result)

    # Fetch grants, tags, and policies (allow these to raise permission errors to caller)
    result["Grants"] = get_kms_grants(client, key_id, grant_tokens=grant_tokens)["Grants"]
    result["Tags"] = get_kms_tags(client, key_id).get("Tags", [])
    result["KeyPolicies"] = get_kms_policies(client, key_id)

    # Transform everything to Ansible format in one go (includes JSON parsing for policies)
    return _transformations.normalize_kms_key_details(result)

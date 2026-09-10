# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Data transformation functions for converting boto3 responses to Ansible format.

This module handles transformation of KMS resources from AWS API format
(CamelCase, boto3-specific structures) to Ansible format (snake_case,
simplified dictionaries). Uses boto3_resource_to_ansible_dict for consistent
transformation patterns across the collection.

Key transformations:
- Grant constraints with encryption context preservation
- Policy document JSON parsing
- Complete key details normalization
- Alias name canonicalization
"""

from __future__ import annotations

import json

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict


def canonicalize_alias_name(alias: str | None) -> str | None:
    """
    Normalize KMS alias name to always include 'alias/' prefix.

    Args:
        alias: Alias name with or without 'alias/' prefix, or None

    Returns:
        Alias name with 'alias/' prefix, or None if input was None

    Examples:
        >>> canonicalize_alias_name("myalias")
        'alias/myalias'
        >>> canonicalize_alias_name("alias/myalias")
        'alias/myalias'
        >>> canonicalize_alias_name(None)
        None
    """
    if alias is None:
        return None
    if alias.startswith("alias/"):
        return alias
    return f"alias/{alias}"


def _transform_grant_constraints(constraints: dict) -> dict:
    """
    Transform KMS grant constraints to Ansible format.

    Preserves encryption context key-value pairs (user-provided data that should not be transformed).

    Args:
        constraints: Constraints dictionary from a KMS grant

    Returns:
        Transformed constraints with snake_case keys but preserved encryption context values
    """
    result = camel_dict_to_snake_dict(constraints, ignore_list=["EncryptionContextEquals", "EncryptionContextSubset"])
    # Manually add back the encryption context fields with snake_case keys
    if "EncryptionContextEquals" in constraints:
        result["encryption_context_equals"] = constraints["EncryptionContextEquals"]
    if "EncryptionContextSubset" in constraints:
        result["encryption_context_subset"] = constraints["EncryptionContextSubset"]
    return result


def _transform_grants_list(grants: list[dict]) -> list[dict]:
    """
    Transform list of KMS grants to Ansible format.

    Args:
        grants: List of KMS grant dictionaries from boto3

    Returns:
        List of transformed grant dictionaries
    """
    return [
        boto3_resource_to_ansible_dict(
            grant,
            transform_tags=False,
            force_tags=False,
            nested_transforms={"Constraints": _transform_grant_constraints},
        )
        for grant in grants
    ]


def _transform_key_policies(policies: list[str]) -> list[dict]:
    """
    Transform KMS policy documents from JSON strings to dictionaries.

    Args:
        policies: List of policy documents as JSON strings

    Returns:
        List of policy documents as dictionaries
    """
    return [json.loads(policy) for policy in policies]


def camel_to_snake_grant(grant: dict) -> dict:
    """
    Convert KMS grant dict to snake_case Ansible format.

    Preserves encryption context key-value pairs within Constraints field.

    Args:
        grant: KMS grant dictionary from boto3

    Returns:
        Transformed grant dictionary in Ansible format
    """
    return boto3_resource_to_ansible_dict(
        grant, transform_tags=False, force_tags=False, nested_transforms={"Constraints": _transform_grant_constraints}
    )


def normalize_kms_key_details(key_details: dict) -> dict:
    """
    Normalize KMS key details to Ansible dictionary format.

    Transforms the complete key details including metadata, grants, tags, and policies.
    Similar to S3's normalize_* functions, provides consistent transformation.

    Args:
        key_details: KMS key details dictionary from boto3 (can include Grants, Tags, KeyPolicies)

    Returns:
        Normalized key details dictionary in Ansible format
    """
    nested_transforms = {
        "Grants": _transform_grants_list,
        "KeyPolicies": _transform_key_policies,
    }

    tagging_params = {
        "tag_name_key_name": "TagKey",
        "tag_value_key_name": "TagValue",
    }

    return boto3_resource_to_ansible_dict(
        key_details,
        transform_tags=True,
        force_tags=False,
        nested_transforms=nested_transforms,
        tagging_params=tagging_params,
    )

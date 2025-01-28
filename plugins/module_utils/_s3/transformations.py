# -*- coding: utf-8 -*-

# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import copy
import typing

if typing.TYPE_CHECKING:
    from typing import Optional

from ansible.module_utils.basic import to_text

from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict


def normalize_s3_bucket_versioning(versioning_status: Optional[dict]) -> Optional[dict]:
    if not versioning_status:
        return versioning_status
    versioning_result = typing.cast(dict, boto3_resource_to_ansible_dict(versioning_status))
    # Original s3_bucket format, no longer advertised but not officially deprecated
    versioning_result["Versioning"] = versioning_status.get("Status", "Disabled")
    versioning_result["MfaDelete"] = versioning_status.get("MFADelete", "Disabled")
    # Original s3_bucket_info format, no longer advertised but not officially deprecated
    versioning_result["Status"] = versioning_status.get("Status", "Disabled")
    versioning_result["MFADelete"] = versioning_status.get("MFADelete", "Disabled")
    return versioning_result


def normalize_s3_bucket_public_access(public_access_status: Optional[dict]) -> Optional[dict]:
    if not public_access_status:
        return public_access_status
    public_access_result = typing.cast(dict, boto3_resource_to_ansible_dict(public_access_status))
    public_access_result["PublicAccessBlockConfiguration"] = copy.deepcopy(public_access_status)
    public_access_result.update(public_access_status)
    return public_access_result


def normalize_s3_bucket_acls(acls: Optional[dict]) -> Optional[dict]:
    if not acls:
        return acls
    acls_result = typing.cast(dict, boto3_resource_to_ansible_dict(acls))
    return typing.cast(dict, acls_result["grants"])


def _grantee_is_owner(grant, owner_id):
    return grant.get("Grantee", {}).get("ID") == owner_id


def _grantee_is_public(grant):
    return grant.get("Grantee", {}).get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers"


def _grantee_is_authenticated(grant):
    return grant.get("Grantee", {}).get("URI") == "http://acs.amazonaws.com/groups/global/AuthenticatedUsers"


def _acl_permissions(grants):
    if not grants:
        return []
    return [grant.get("Permission") for grant in grants if grant]


def s3_acl_to_name(acl):
    if not acl:
        return None

    try:
        grants = acl["Grants"]
        owner_id = acl["Owner"]["ID"]
        owner_acl = [grant for grant in grants if _grantee_is_owner(grant, owner_id)]
        auth_acl = [grant for grant in grants if _grantee_is_authenticated(grant)]
        public_acl = [grant for grant in grants if _grantee_is_public(grant)]

        if len(grants) > (len(owner_acl) + len(auth_acl) + len(public_acl)):
            raise ValueError("Unrecognised Grantee")
        if public_acl and auth_acl:
            raise ValueError("Public ACLs and Authenticated User ACLs are only used alone in templated ACL")

        if ["FULL_CONTROL"] != _acl_permissions(owner_acl):
            raise ValueError("Owner doesn't have full control")
        if len(grants) == 1:
            return "private"

        if auth_acl:
            if ["READ"] == _acl_permissions(auth_acl):
                return "authenticated-read"
            raise ValueError("Authenticated User ACLs don't match templated ACL")

        permissions = sorted(_acl_permissions(public_acl))
        if permissions == ["READ"]:
            return "public-read"
        if permissions == ["READ", "WRITE"]:
            return "public-read-write"

        raise ValueError("Public ACLs don't match templated ACL")

    except (KeyError, IndexError, ValueError):
        return None


def merge_tags(current_tags: dict, new_tags: dict, purge_tags: bool = True) -> dict:
    """
    Compare and merge two dicts of tags.

    :param current_tags: The current tags
    :param new_tags: The tags passed as a parameter
    :param purge_tags: Whether to remove current tags that aren't in new_tags
    :return: updated_tags: The updated dictionary of tags
    """

    if new_tags is None:
        return current_tags

    updated_tags = copy.deepcopy(current_tags) if not purge_tags else {}
    # Tags are always returned as text
    new_tags = dict((to_text(k), to_text(v)) for k, v in new_tags.items())
    updated_tags.update(new_tags)

    return updated_tags

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Grant comparison and diff logic for idempotent grant management.

This module provides functions to compare existing grants with desired grants
and determine which grants need to be added or removed. Supports purge_grants
parameter for controlling whether unspecified grants should be removed.

Grant comparison considers:
- Grantee principal
- Retiring principal
- Operations (order-independent)
- Constraints (encryption context)
"""

from __future__ import annotations


def different_grant(existing_grant: dict, desired_grant: dict) -> bool:
    """Check if two grants differ in any way"""
    if existing_grant.get("grantee_principal") != desired_grant.get("grantee_principal"):
        return True
    if existing_grant.get("retiring_principal") != desired_grant.get("retiring_principal"):
        return True
    if set(existing_grant.get("operations", [])) != set(desired_grant.get("operations", [])):
        return True
    if existing_grant.get("constraints") != desired_grant.get("constraints"):
        return True
    return False


def compare_grants(
    existing_grants: list[dict], desired_grants: list[dict], purge_grants: bool = False
) -> tuple[list[dict], list[dict]]:
    """
    Compare existing and desired grants to determine which to add/remove.

    Returns:
        tuple: (grants_to_add, grants_to_remove)
    """
    existing_dict = {eg["name"]: eg for eg in existing_grants}
    desired_dict = {dg["name"]: dg for dg in desired_grants}
    to_add_keys = set(desired_dict.keys()) - set(existing_dict.keys())
    if purge_grants:
        to_remove_keys = set(existing_dict.keys()) - set(desired_dict.keys())
    else:
        to_remove_keys = set()
    to_change_candidates = set(existing_dict.keys()) & set(desired_dict.keys())
    for candidate in to_change_candidates:
        if different_grant(existing_dict[candidate], desired_dict[candidate]):
            to_add_keys.add(candidate)
            to_remove_keys.add(candidate)

    to_add = [desired_dict[key] for key in to_add_keys]
    to_remove = [existing_dict[key] for key in to_remove_keys]
    return to_add, to_remove

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Action processing utilities for ELBv2 listener and rule actions.

This module provides helper functions for processing, normalizing, and pruning
action configurations for Application Load Balancer listeners and rules.
"""

from __future__ import annotations

import typing
from copy import deepcopy

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Optional


def _simple_forward_config_arn(config: Dict[str, Any], parent_arn: Optional[str]) -> Optional[str]:
    """
    Extract target group ARN from a simple ForwardConfig.

    Determines if a ForwardConfig represents a simple forward action (single target group,
    no custom stickiness or weights) and returns the target group ARN if so.

    Args:
        config: ForwardConfig dict from action
        parent_arn: Parent-level TargetGroupArn if already set

    Returns:
        Target group ARN if config is simple, None if complex or invalid

    Note:
        A "simple" ForwardConfig has:
        - No custom stickiness (or stickiness disabled)
        - Single target group (or none if parent_arn set)
        - No other non-default configuration
    """
    config = deepcopy(config)

    stickiness = config.pop("TargetGroupStickinessConfig", {"Enabled": False})
    # Stickiness options set, non default value
    if stickiness != {"Enabled": False}:
        return None

    target_groups = config.pop("TargetGroups", [])

    # non-default config left over, probably invalid
    if config:
        return None
    # Multiple TGS, not simple
    if len(target_groups) > 1:
        return None

    if not target_groups:
        # with no TGs defined, but an ARN set, this is one of the minimum possible configs
        return parent_arn

    target_group = target_groups[0]
    # We don't care about the weight with a single TG
    target_group.pop("Weight", None)

    target_group_arn = target_group.pop("TargetGroupArn", None)

    # non-default config left over
    if target_group:
        return None

    # We didn't find an ARN
    if not (target_group_arn or parent_arn):
        return None

    # Only one
    if not parent_arn:
        return target_group_arn
    if not target_group_arn:
        return parent_arn

    if parent_arn != target_group_arn:
        return None

    return target_group_arn


def _prune_ForwardConfig(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove redundant ForwardConfig where TargetGroupArn already set.

    ForwardConfig may be optional if we've got a single TargetGroupArn entry.
    This function simplifies actions for comparison by removing redundant
    ForwardConfig and using the simpler TargetGroupArn format.

    Args:
        action: Action dict potentially containing redundant ForwardConfig

    Returns:
        Action dict with ForwardConfig removed if redundant, otherwise unchanged
    """
    if action.get("Type", "") != "forward":
        return action
    if "ForwardConfig" not in action:
        return action

    parent_arn = action.get("TargetGroupArn", None)
    arn = _simple_forward_config_arn(action["ForwardConfig"], parent_arn)
    if not arn:
        return action

    # Remove the redundant ForwardConfig
    newAction = action.copy()
    del newAction["ForwardConfig"]
    newAction["TargetGroupArn"] = arn
    return newAction


def _prune_secret(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove client secret from OIDC authentication config and add default values.

    AWS won't return the client secret if UseExistingClientSecret is set, so we
    remove it for comparison purposes. Also adds default values for fields not
    explicitly requested.

    Args:
        action: Action dict potentially containing OIDC authentication config

    Returns:
        Action dict with client secret removed and defaults added if OIDC action,
        otherwise unchanged
    """
    if action["Type"] != "authenticate-oidc":
        return action

    if not action["AuthenticateOidcConfig"].get("Scope", False):
        action["AuthenticateOidcConfig"]["Scope"] = "openid"

    if not action["AuthenticateOidcConfig"].get("SessionTimeout", False):
        action["AuthenticateOidcConfig"]["SessionTimeout"] = 604800

    if action["AuthenticateOidcConfig"].get("UseExistingClientSecret", False):
        action["AuthenticateOidcConfig"].pop("ClientSecret", None)

    if not action["AuthenticateOidcConfig"].get("OnUnauthenticatedRequest", False):
        action["AuthenticateOidcConfig"]["OnUnauthenticatedRequest"] = "authenticate"

    if not action["AuthenticateOidcConfig"].get("SessionCookieName", False):
        action["AuthenticateOidcConfig"]["SessionCookieName"] = "AWSELBAuthSessionCookie"

    return action


def _append_use_existing_client_secret(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add UseExistingClientSecret flag to OIDC authentication config for comparison.

    AWS API won't return the UseExistingClientSecret key, but it must be added
    for accurate comparison with user-provided configuration.

    Args:
        action: Action dict potentially containing OIDC authentication config

    Returns:
        Action dict with UseExistingClientSecret flag added if OIDC action,
        otherwise unchanged
    """
    if action["Type"] != "authenticate-oidc":
        return action

    action["AuthenticateOidcConfig"]["UseExistingClientSecret"] = True

    return action

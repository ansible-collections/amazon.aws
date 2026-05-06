# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Rule management utilities for ELBv2 listeners.

This module provides functions and classes for managing Application Load Balancer
listener rules, including comparison, grouping, and CRUD operations.
"""

from __future__ import annotations

import typing
from copy import deepcopy

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Tuple

    from ..modules import AnsibleAWSModule

from ..elb_utils import convert_tg_name_to_arn
from ..elb_utils import create_rule
from ..elb_utils import delete_rule
from ..elb_utils import describe_rules
from ..elb_utils import modify_rule
from ..elb_utils import set_rule_priorities
from . import actions as _actions
from . import transformations as _transformations


def _normalize_condition_values(condition: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize condition values by sorting them for comparison.

    Parameters:
    condition: The condition to normalize

    Returns:
    A deep copy of the condition with sorted values
    """
    compare_keys = (
        "HostHeaderConfig",
        "HttpHeaderConfig",
        "HttpRequestMethodConfig",
        "SourceIpConfig",
        "PathPatternConfig",
    )
    normalized = deepcopy(condition)
    for key in compare_keys:
        if key in normalized:
            normalized[key]["Values"] = sorted(normalized[key]["Values"])
    if "Values" in normalized:
        normalized["Values"] = sorted(normalized["Values"])
    return normalized


def _sorted_values_match(current_config: Dict[str, Any], target_config: Dict[str, Any], config_key: str) -> bool:
    """Compare sorted Values from two config dictionaries.

    Parameters:
    current_config: The current condition configuration
    target_config: The target condition configuration (already normalized)
    config_key: The configuration key to compare

    Returns:
    True if sorted values match, False otherwise
    """
    return sorted(current_config[config_key]["Values"]) == target_config[config_key]["Values"]


def _http_header_name_matches(current_config: Dict[str, Any], target_config: Dict[str, Any], config_key: str) -> bool:
    """Compare HttpHeaderName from HttpHeaderConfig.

    Parameters:
    current_config: The current condition configuration
    target_config: The target condition configuration
    config_key: The configuration key (should be "HttpHeaderConfig")

    Returns:
    True if HttpHeaderName values match, False otherwise
    """
    return current_config[config_key]["HttpHeaderName"] == target_config[config_key]["HttpHeaderName"]


def _conditions_match(current_condition: Dict[str, Any], target_condition: Dict[str, Any]) -> bool:
    """Compare two conditions to check if they match.

    Parameters:
    current_condition: The current condition from AWS
    target_condition: The target condition (already normalized)

    Returns:
    True if conditions match, False otherwise
    """
    # Try config-based comparisons in order of specificity
    # host-header/path-pattern: current_condition includes both *Config AND Values while
    # condition can be defined with either format. Only use *Config comparison if both have it.
    for config_key in ("HostHeaderConfig", "PathPatternConfig"):
        if current_condition.get(config_key) and target_condition.get(config_key):
            return _sorted_values_match(current_condition, target_condition, config_key)

    # HttpHeaderConfig requires both Values and HttpHeaderName to match
    if current_condition.get("HttpHeaderConfig"):
        return (
            _sorted_values_match(current_condition, target_condition, "HttpHeaderConfig")
            and _http_header_name_matches(current_condition, target_condition, "HttpHeaderConfig")
        )

    # QueryStringConfig uses list of dicts, don't sort
    if current_condition.get("QueryStringConfig"):
        return current_condition["QueryStringConfig"]["Values"] == target_condition["QueryStringConfig"]["Values"]

    # Standard config comparisons with sorted values
    for config_key in ("HttpRequestMethodConfig", "SourceIpConfig"):
        if current_condition.get(config_key):
            return _sorted_values_match(current_condition, target_condition, config_key)

    # Fallback: direct Values comparison (legacy host-header/path-pattern format)
    return sorted(current_condition["Values"]) == target_condition["Values"]


def _check_rule_condition(current_conditions: List[Dict[str, Any]], condition: Dict[str, Any]) -> bool:
    """Check if the condition is part of the list of current conditions.

    Parameters:
    current_conditions: The list of conditions
    condition: The condition we are trying to find into the list

    Returns:
    True if the condition is part of the list, False if not.
    """
    normalized_condition = _normalize_condition_values(condition)

    for current_condition in current_conditions:
        # 'Field' should match for the conditions to be equal
        if current_condition["Field"] != normalized_condition["Field"]:
            continue

        if _conditions_match(current_condition, normalized_condition):
            return True

    return False


def _compare_rule_actions(current_actions: List[Dict[str, Any]], new_actions: List[Dict[str, Any]]) -> bool:
    """This function compares current_actions with new_actions.
    Bfore to the comparison, the function will set the default values for some attributes of the new actions
    as these are not part of the module parameters.

    Parameters:
    current_actions: The current AWS rule actions
    new_actions: The rule actions from module parameters.

    Returns:
    True if the current_actions and new_actions are equal, False if not.
    """
    # If the lengths of the actions are the same, we'll have to verify that the
    # contents of those actions are the same
    if len(current_actions) != len(new_actions):
        return False

    # if actions have just one element, compare the contents and then update if
    # they're different
    current_actions_sorted = _transformations._sort_actions(current_actions)
    new_actions_sorted = _transformations._sort_actions(deepcopy(new_actions))

    new_current_actions_sorted = [_actions._append_use_existing_client_secretn(i) for i in current_actions_sorted]
    new_actions_sorted_no_secret = [_actions._prune_secret(i) for i in new_actions_sorted]

    return [_actions._prune_ForwardConfig(i) for i in new_current_actions_sorted] == [
        _actions._prune_ForwardConfig(i) for i in new_actions_sorted_no_secret
    ]


def _compare_rule(current_rule: Dict[str, Any], new_rule: Dict[str, Any]) -> Dict[str, Any]:
    """This function compares rule_a with rule_b and returns differences
    between the two rules as a dictionnary

    Parameters:
    current_rule: The current listener rule stored in AWS.
    new_rule: The new listener rule.

    Returns:
    A dictionnary containing the modified attributes.
    """

    modified_rule = {}

    # Priority
    if int(current_rule["Priority"]) != int(new_rule["Priority"]):
        modified_rule["Priority"] = new_rule["Priority"]

    # Actions
    actions_match = _compare_rule_actions(current_rule["Actions"], new_rule["Actions"])
    if not actions_match:
        modified_rule["Actions"] = new_rule["Actions"]

    # Conditions
    modified_conditions = [
        c for c in new_rule["Conditions"] if not _check_rule_condition(current_rule["Conditions"], c)
    ]
    if modified_conditions:
        modified_rule["Conditions"] = modified_conditions

    return modified_rule


def _process_exact_matches_and_priority_changes(
    current_rules: List[Dict[str, Any]], rules_to_add: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process current rules to find exact matches and priority-only changes.

    Parameters:
    current_rules: The current listener rules stored in AWS (will be copied)
    rules_to_add: List of new rules to add

    Returns:
    A tuple of (remaining_current_rules, remaining_rules_to_add, rules_to_set_priority)
    """
    remaining_current_rules = []
    remaining_rules_to_add = list(rules_to_add)
    rules_to_set_priority = []

    for current_rule in deepcopy(current_rules):
        # Skip the default rule, it can't be modified
        if current_rule.get("IsDefault", False):
            continue

        matched = False
        for new_rule in remaining_rules_to_add[:]:  # Iterate over a shallow copy
            modified_rule = _compare_rule(current_rule, new_rule)

            if not modified_rule:
                # Exact match - rule unchanged
                remaining_rules_to_add.remove(new_rule)
                matched = True
                break

            if list(modified_rule.keys()) == ["Priority"]:
                # Only priority changed
                modified_rule["Priority"] = int(new_rule["Priority"])
                modified_rule["RuleArn"] = current_rule["RuleArn"]
                rules_to_set_priority.append(modified_rule)
                remaining_rules_to_add.remove(new_rule)
                matched = True
                break

        if not matched:
            remaining_current_rules.append(current_rule)

    return remaining_current_rules, remaining_rules_to_add, rules_to_set_priority


def _process_priority_based_modifications(
    remaining_rules: List[Dict[str, Any]], rules_to_add: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Process remaining rules to find modifications based on priority matching.

    Parameters:
    remaining_rules: Rules that didn't match in first pass
    rules_to_add: List of new rules to add

    Returns:
    A tuple of (remaining_rules_to_add, rules_to_modify, rules_to_delete)
    """
    remaining_rules_to_add = list(rules_to_add)
    rules_to_modify = []
    rules_to_delete = []

    for current_rule in remaining_rules:
        matched = False

        for new_rule in remaining_rules_to_add[:]:  # Iterate over a shallow copy
            if current_rule["Priority"] == str(new_rule["Priority"]):
                # Same priority, check what changed
                remaining_rules_to_add.remove(new_rule)
                modified_rule = _compare_rule(current_rule, new_rule)

                if modified_rule:
                    modified_rule["Priority"] = int(current_rule["Priority"])
                    modified_rule["RuleArn"] = current_rule["RuleArn"]
                    modified_rule["Actions"] = new_rule["Actions"]
                    modified_rule["Conditions"] = new_rule["Conditions"]

                    # You cannot both specify a client secret and set UseExistingClientSecret to true
                    for action in modified_rule.get("Actions", []):
                        if action.get("AuthenticateOidcConfig", {}).get("ClientSecret", False):
                            action["AuthenticateOidcConfig"]["UseExistingClientSecret"] = False

                    rules_to_modify.append(modified_rule)

                matched = True
                break

        # If not matched and not default rule, mark for deletion
        if not matched and not current_rule.get("IsDefault", False):
            rules_to_delete.append(current_rule["RuleArn"])

    return remaining_rules_to_add, rules_to_modify, rules_to_delete


def _group_rules(
    current_rules: List[Dict[str, Any]], rules: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Compare listener rules from AWS with module provided listener rules.

    Groups rules into four categories:
        - Rules to add: new rules not currently stored on AWS
        - Rules to set priority: unchanged rules with different priority value
        - Rules to modify: rules where Actions or Conditions changed
        - Rules to delete: current AWS rules not defined in module parameters

    Parameters:
    current_rules: The current listener rules stored in AWS
    rules: The new listener rules

    Returns:
    A tuple of (rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete)
    """
    # Make a working copy of new rules
    rules_to_add = deepcopy(rules)

    # Phase 1: Find exact matches and priority-only changes
    remaining_current_rules, rules_to_add, rules_to_set_priority = _process_exact_matches_and_priority_changes(
        current_rules, rules_to_add
    )

    # Phase 2: Find modifications and deletions based on priority matching
    rules_to_add, rules_to_modify, rules_to_delete = _process_priority_based_modifications(
        remaining_current_rules, rules_to_add
    )

    return rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete


class ELBListenerRules:
    def __init__(
        self,
        connection: Any,
        module: AnsibleAWSModule,
        listener_arn: Optional[str],
        listener_rules: List[Dict[str, Any]],
    ) -> None:
        self.connection = connection
        self.module = module
        self.rules = self._ensure_rules_action_has_arn(listener_rules)
        self.changed = False

        self.listener_arn = listener_arn
        self.current_rules = describe_rules(self.connection, ListenerArn=listener_arn)

    def _ensure_rules_action_has_arn(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        If a rule Action has been passed with a Target Group Name instead of ARN, lookup the ARN and
        replace the name.

        :param rules: a list of rule dicts
        :return: the same list of dicts ensuring that each rule Actions dict has TargetGroupArn key. If a TargetGroupName key exists, it is removed.
        """

        fixed_rules = []
        for rule in rules:
            fixed_actions = []
            for action in rule["Actions"]:
                if "TargetGroupName" in action:
                    action["TargetGroupArn"] = convert_tg_name_to_arn(
                        self.connection, self.module, action["TargetGroupName"]
                    )
                    del action["TargetGroupName"]
                fixed_actions.append(action)
            rule["Actions"] = fixed_actions
            fixed_rules.append(rule)

        return fixed_rules

    def compare_rules(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """This function creates the rule matrix (to add, to set priority, to modify, to delete)
        and prepare them to be ready for AWS API call.

        Returns:
        A tuple with a list of rules to add, a list of rules to set priority, a list of rules to modify and a list of rules to delete
        """
        rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete = _group_rules(
            self.current_rules, self.rules
        )

        # Prepare Rule to create (to add)
        # For rules to create 'UseExistingClientSecret' should be set to False, The 'Priority' need
        # To be an int value and the ListenerArn need to be set
        for rule in rules_to_add:
            for action in rule.get("Actions", []):
                if action.get("AuthenticateOidcConfig", {}).get("UseExistingClientSecret", False):
                    action["AuthenticateOidcConfig"]["UseExistingClientSecret"] = False
            rule["ListenerArn"] = self.listener_arn
            rule["Priority"] = int(rule["Priority"])

        # Prepare Rule to modify: We need to remove the 'Priority' key
        for rule in rules_to_modify:
            del rule["Priority"]

        return rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete


class ELBListenerRule:
    def __init__(self, connection, module) -> None:
        self.connection = connection
        self.module = module

    def create(self, rule: Dict[str, Any]) -> None:
        """
        Create a listener rule

        :return:
        """
        listener_arn = rule.pop("ListenerArn")
        conditions = rule.pop("Conditions")
        priority = rule.pop("Priority")
        actions = rule.pop("Actions")
        tags = rule.pop("Tags", None)
        create_rule(
            self.connection,
            listener_arn=listener_arn,
            conditions=conditions,
            actions=actions,
            tags=tags,
            priority=priority,
        )

    def modify(self, rule: Dict[str, Any]) -> None:
        """
        Modify a listener rule

        :return:
        """
        rule_arn = rule.pop("RuleArn")
        modify_rule(self.connection, rule_arn=rule_arn, **rule)

    def delete(self, rule_arn: str) -> None:
        """
        Delete a listener rule

        :return:
        """
        delete_rule(self.connection, rule_arn)

    def set_rule_priorities(self, rules: List[Dict[str, Any]]) -> None:
        """
        Sets the priorities of the specified rules.

        :return:
        """
        set_rule_priorities(
            self.connection, [{"RuleArn": rule["RuleArn"], "Priority": rule["Priority"]} for rule in rules]
        )

    def process_rules(
        self,
        rules_to_create: List[Dict[str, Any]],
        rules_to_set_priority: List[Dict[str, Any]],
        rules_to_modify: List[Dict[str, Any]],
        rules_to_delete: List[str],
    ) -> bool:
        changed = False
        if rules_to_set_priority:
            self.set_rule_priorities(rules_to_set_priority)
            changed = True
        if self.module.params["purge_rules"]:
            for arn in rules_to_delete:
                self.delete(arn)
                changed = True
        for rule in rules_to_create:
            self.create(rule)
            changed = True
        for rule in rules_to_modify:
            self.modify(rule)
            changed = True
        return changed

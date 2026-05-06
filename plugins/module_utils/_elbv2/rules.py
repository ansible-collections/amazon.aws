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


def _check_rule_condition(current_conditions: List[Dict[str, Any]], condition: Dict[str, Any]) -> bool:
    """This function checks if the condition is part of the list of current condition

    Parameters:
    current_conditions: The list of conditions
    condition: The condition we are trying to find into the list

    Returns:
    True if the condition is part of the list, False if not.
    """

    condition_found = False
    compare_keys = (
        "HostHeaderConfig",
        "HttpHeaderConfig",
        "HttpRequestMethodConfig",
        "SourceIpConfig",
        "PathPatternConfig",
    )
    # Do an initial sorting of condition keys
    s_condition = deepcopy(condition)
    for key in compare_keys:
        if key in s_condition:
            s_condition[key]["Values"] = sorted(s_condition[key]["Values"])
    if "Values" in s_condition:
        s_condition["Values"] = sorted(s_condition["Values"])

    for current_condition in current_conditions:
        # 'Field' should match for the conditions to be equal, compare it once at the begining
        if current_condition["Field"] != s_condition["Field"]:
            continue
        # host-header: current_condition includes both HostHeaderConfig AND Values while
        # condition can be defined with either HostHeaderConfig OR Values. Only use
        # HostHeaderConfig['Values'] comparison if both conditions includes HostHeaderConfig.
        if current_condition.get("HostHeaderConfig") and s_condition.get("HostHeaderConfig"):
            if sorted(current_condition["HostHeaderConfig"]["Values"]) == s_condition["HostHeaderConfig"]["Values"]:
                condition_found = True
                break
        elif current_condition.get("HttpHeaderConfig"):
            if (
                sorted(current_condition["HttpHeaderConfig"]["Values"]) == s_condition["HttpHeaderConfig"]["Values"]
                and current_condition["HttpHeaderConfig"]["HttpHeaderName"]
                == s_condition["HttpHeaderConfig"]["HttpHeaderName"]
            ):
                condition_found = True
                break
        elif current_condition.get("HttpRequestMethodConfig"):
            if (
                sorted(current_condition["HttpRequestMethodConfig"]["Values"])
                == s_condition["HttpRequestMethodConfig"]["Values"]
            ):
                condition_found = True
                break
        # path-pattern: current_condition includes both PathPatternConfig AND Values while
        # condition can be defined with either PathPatternConfig OR Values. Only use
        # PathPatternConfig['Values'] comparison if both conditions includes PathPatternConfig.
        elif current_condition.get("PathPatternConfig") and s_condition.get("PathPatternConfig"):
            if sorted(current_condition["PathPatternConfig"]["Values"]) == s_condition["PathPatternConfig"]["Values"]:
                condition_found = True
                break
        elif current_condition.get("QueryStringConfig"):
            # QueryString Values is not sorted as it is the only list of dicts (not strings).
            if current_condition["QueryStringConfig"]["Values"] == s_condition["QueryStringConfig"]["Values"]:
                condition_found = True
                break
        elif current_condition.get("SourceIpConfig"):
            if sorted(current_condition["SourceIpConfig"]["Values"]) == s_condition["SourceIpConfig"]["Values"]:
                condition_found = True
                break
        # Not all fields are required to have Values list nested within a *Config dict
        # e.g. fields host-header/path-pattern can directly list Values
        elif sorted(current_condition["Values"]) == s_condition["Values"]:
            condition_found = True
            break

    return condition_found


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


def _group_rules(
    current_rules: List[Dict[str, Any]], rules: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """This function compares listener rules from AWS with module provided listener rules and a matrix with the
    following:
        - Rules to add: a rule is added when it is part of the module parameters and not currently stored on AWS
        - Rules to set priority: Any rule with unchanged attributes but with a different priority value
        - Rules to modify: Any rule on which one the following attribute has changed 'Actions', 'Conditions'
        - Rules to delete: Any rule currently stored on AWS and not defined in module parameters.

    Parameters:
    current_rules: The current listener rules stored in AWS.
    rules: The new listener rules.

    Returns:
    A tuple with a list of rules to add, a list of rules to set priority, a list of rules to modify and a list of rules to delete
    """

    rules_to_modify = []
    rules_to_delete = []
    rules_to_add = deepcopy(rules)
    rules_to_set_priority = []

    # List rules to update priority, 'Actions' and 'Conditions' remain the same
    # only the 'Priority' has changed
    _current_rules = deepcopy(current_rules)
    remaining_rules = []
    while _current_rules:
        current_rule = _current_rules.pop(0)
        # Skip the default rule, this one can't be modified
        if current_rule.get("IsDefault", False):
            continue
        to_keep = True
        for new_rule in rules_to_add:
            modified_rule = _compare_rule(current_rule, new_rule)
            if not modified_rule:
                # The current rule has been passed with the same properties to the module
                # Remove it for later comparison
                rules_to_add.remove(new_rule)
                to_keep = False
                break
            if modified_rule and list(modified_rule.keys()) == ["Priority"]:
                # if only the Priority has changed
                modified_rule["Priority"] = int(new_rule["Priority"])
                modified_rule["RuleArn"] = current_rule["RuleArn"]

                rules_to_set_priority.append(modified_rule)
                to_keep = False
                rules_to_add.remove(new_rule)
                break
        if to_keep:
            remaining_rules.append(current_rule)

    for current_rule in remaining_rules:
        current_rule_passed_to_module = False
        for new_rule in rules_to_add:
            if current_rule["Priority"] == str(new_rule["Priority"]):
                current_rule_passed_to_module = True
                # Remove what we match so that what is left can be marked as 'to be added'
                rules_to_add.remove(new_rule)
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
                break

        # If the current rule was not matched against passed rules, mark for removal
        if not current_rule_passed_to_module and not current_rule.get("IsDefault", False):
            rules_to_delete.append(current_rule["RuleArn"])

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

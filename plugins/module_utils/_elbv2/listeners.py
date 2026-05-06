# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Listener management utilities for ELBv2 load balancers.

This module provides functions and classes for managing Application Load Balancer
listeners, including comparison, grouping, and CRUD operations.
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

from ..elb_utils import add_listener_certificates
from ..elb_utils import convert_tg_name_to_arn
from ..elb_utils import create_listener
from ..elb_utils import delete_listener
from ..elb_utils import describe_listeners
from ..elb_utils import modify_listener
from ..transformation import scrub_none_parameters
from . import rules as _rules


def _compare_listener(current_listener: Dict[str, Any], new_listener: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compare two listeners. We do not check the port as the function is expecting that
    the two listeners are passed with the same port value.

    :param current_listener: The current listener attributes as stored into AWS
    :param new_listener: The listener as defined into module parameters
    :return: A dict containing the resulting update to perform on the current listener
    """

    modified_listener = {}

    # Protocol
    current_protocol = current_listener["Protocol"]
    new_protocol = new_listener["Protocol"]
    if current_protocol != new_protocol:
        modified_listener["Protocol"] = new_protocol

    # SslPolicy and Certificates are compared if the new listener protocol is
    # one of the following 'HTTPS', 'TLS'
    if new_protocol in ("HTTPS", "TLS"):
        # SslPolicy
        current_ssl_policy = current_listener.get("SslPolicy")
        new_ssl_policy = new_listener.get("SslPolicy")
        if new_ssl_policy and any(
            (not current_ssl_policy, current_ssl_policy and current_ssl_policy != new_ssl_policy)
        ):
            modified_listener["SslPolicy"] = new_ssl_policy

        # Certificates
        new_certificates = new_listener.get("Certificates")
        current_certificates = current_listener.get("Certificates")
        if new_certificates and any(
            (
                not current_certificates,
                current_certificates
                and current_certificates[0]["CertificateArn"] != new_certificates[0]["CertificateArn"],
            )
        ):
            modified_listener["Certificates"] = [{"CertificateArn": new_certificates[0]["CertificateArn"]}]

    # Default actions
    # If the lengths of the actions are the same, we'll have to verify that the
    # contents of those actions are the same
    current_default_actions = current_listener.get("DefaultActions")
    new_default_actions = new_listener.get("DefaultActions")
    if new_default_actions:
        if current_default_actions and len(current_default_actions) == len(new_default_actions):
            # Use the same comparison logic as _compare_rule_actions for consistency
            if not _rules._compare_rule_actions(current_default_actions, new_default_actions):
                modified_listener["DefaultActions"] = new_default_actions
        # If the action lengths are different, then replace with the new actions
        else:
            modified_listener["DefaultActions"] = new_default_actions

    # AlpnPolicy
    new_alpn_policy = new_listener.get("AlpnPolicy")
    if new_alpn_policy and new_protocol == "TLS":
        current_alpn_policy = current_listener.get("AlpnPolicy")
        if current_listener["Protocol"] != "TLS" or (
            current_listener["Protocol"] == "TLS"
            and (not current_alpn_policy or current_alpn_policy[0] != new_alpn_policy[0])
        ):
            modified_listener["AlpnPolicy"] = new_alpn_policy

    return modified_listener


def _group_listeners(
    current_listeners: List[Dict[str, Any]], new_listeners: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    This function groups listeners.
    - listeners to add: any new listener from module parameters not present of the current listeners stored in AWS resource.
    - listeners to delete: any listener currently stored in AWS resource and not present of the module parameters.
    - listeners to modify: any listener present in both list but with different properties.
    The listener key is the Port value.

    :param current_listeners: The current listeners stored into AWS.
    :param new_listeners: The listeners as defined into module parameters.
    :return: A dict containing 3 lists of listeners groups.
    """
    listeners_to_modify = []
    listeners_to_delete = []
    listeners_to_add = deepcopy(new_listeners)

    # Check each current listener port to see if it's been passed to the module
    for current_listener in current_listeners:
        idx = next(
            (i for i, listener in enumerate(listeners_to_add) if int(listener["Port"]) == current_listener["Port"]), -1
        )
        if idx == -1:
            # The current listener is not present in new_listeners
            listeners_to_delete.append(current_listener["ListenerArn"])
            continue
        # Remove what we match so that what is left can be marked as 'to be added'
        m_listener = listeners_to_add.pop(idx)
        # Now compare the 2 listeners with the same Port value
        modified_listener = _compare_listener(current_listener, m_listener)
        if modified_listener:
            modified_listener.update({"Port": current_listener["Port"], "ListenerArn": current_listener["ListenerArn"]})
            listeners_to_modify.append(modified_listener)

    return listeners_to_add, listeners_to_modify, listeners_to_delete


def _prepare_listeners(
    connection, module: AnsibleAWSModule, listeners: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    # This functions prepare listener defined in module parameters
    # 1. Remove None elements from listener attribute
    # 2. Tranform AlpnPolicy, value is set as string but API is expected a list
    # 3. For listener defining Target group name, replaced them with the corresponding Target group ARN
    updated_listeners = []
    if not listeners:
        return updated_listeners
    target_group_mapping = {}
    for item in listeners:
        listener = deepcopy(item)
        # Remove suboption argspec defaults of None from each listener
        listener = scrub_none_parameters(listener, descend_into_lists=False)
        # Converts 'AlpnPolicy' attribute of listener from string type to list
        if "AlpnPolicy" in listener:
            listener["AlpnPolicy"] = [listener["AlpnPolicy"]]
        # If a listener DefaultAction has been passed with a Target Group Name instead of ARN,
        # lookup the ARN and replace the name.
        for action in listener["DefaultActions"]:
            tg_name = action.pop("TargetGroupName", None)
            if tg_name:
                if tg_name not in target_group_mapping:
                    target_group_mapping[tg_name] = convert_tg_name_to_arn(connection, module, tg_name)
                action["TargetGroupArn"] = target_group_mapping[tg_name]
        updated_listeners.append(listener)
    return updated_listeners


class ELBListeners:
    def __init__(self, connection: Any, module: AnsibleAWSModule, elb_arn: str) -> None:
        self.connection = connection
        self.module = module
        self.elb_arn = elb_arn
        self.listeners = _prepare_listeners(connection, module, module.params.get("listeners"))
        self.update()
        self.purge_listeners = module.params.get("purge_listeners")
        self.changed = False

    def update(self) -> None:
        """
        Update the listeners for the ELB

        :return:
        """
        self.current_listeners = describe_listeners(self.connection, load_balancer_arn=self.elb_arn)

    def get_listener_arn_from_listener_port(self, listener_port: int) -> Optional[str]:
        listener_arn = None
        for listener in self.current_listeners:
            if listener["Port"] == listener_port:
                listener_arn = listener["ListenerArn"]
                break
        return listener_arn

    def compare_listeners(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """This function call the _group_listeners method and update the listeners
        to delete depending on the value set on `purge_listeners` parameter.
        """
        listeners_to_add, listeners_to_modify, listeners_to_delete = _group_listeners(
            self.current_listeners, self.listeners
        )
        # Prepare listeners to add/modify, Remove the key 'Rules' from attributes
        # 'Rules' is not a valid attribute for 'create_listener' and 'modify_listener'
        for listener in listeners_to_add + listeners_to_modify:
            listener.pop("Rules", None)
        # If `purge_listeners` is set to False, we empty the list of listeners to delete
        listeners_to_delete = listeners_to_delete if self.purge_listeners else []
        return listeners_to_add, listeners_to_modify, listeners_to_delete


class ELBListener:
    def __init__(self, connection: Any, module: AnsibleAWSModule, listener: Dict[str, Any], elb_arn: str) -> None:
        """

        :param connection:
        :param module:
        :param listener:
        :param elb_arn:
        """

        self.connection = connection
        self.module = module
        self.listener = listener
        self.elb_arn = elb_arn

    def create_listener(self) -> str:
        return create_listener(self.connection, self.elb_arn, **self.listener)[0]["ListenerArn"]

    def add(self) -> None:
        # handle multiple certs by adding only 1 cert during listener creation and make calls to add_listener_certificates to add other certs
        listener_certificates = self.listener.get("Certificates", [])
        first_certificate, other_certs = [], []
        if len(listener_certificates) > 0:
            first_certificate, other_certs = listener_certificates[0], listener_certificates[1:]
            self.listener["Certificates"] = [first_certificate]
        # create listener
        listener_arn = self.create_listener()
        # only one cert can be specified per call to add_listener_certificates
        for cert in other_certs:
            add_listener_certificates(self.connection, listener_arn=listener_arn, certificates=[cert])

    def modify(self) -> None:
        listener_arn = self.listener.pop("ListenerArn")
        modify_listener(self.connection, listener_arn=listener_arn, **self.listener)

    def delete(self) -> None:
        delete_listener(self.connection, self.listener)

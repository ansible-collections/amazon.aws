# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Dict

from ..waiter import BaseWaiterFactory

# Constants for waiter JMESPath arguments
_LB_STATE_PATH = "LoadBalancers[].State.Code"
_LB_IP_ADDRESS_TYPE_PATH = "LoadBalancers[].IpAddressType"


class ELBv2WaiterFactory(BaseWaiterFactory):
    """Factory for creating ELBv2-specific waiters with improved error handling."""

    @property
    def _waiter_model_data(self) -> Dict:
        """
        Define waiter models for ELBv2 operations.

        Based on botocore waiter definitions from:
        botocore/data/elbv2/2015-12-01/waiters-2.json

        Returns:
            Dictionary containing waiter configurations for ELBv2 operations.
        """
        data = dict(
            load_balancer_exists=dict(
                operation="DescribeLoadBalancers",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(state="success", matcher="status", expected=200),
                    dict(state="retry", matcher="error", expected="LoadBalancerNotFound"),
                ],
            ),
            load_balancer_available=dict(
                operation="DescribeLoadBalancers",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        argument=_LB_STATE_PATH,
                        expected="active",
                    ),
                    dict(
                        state="retry",
                        matcher="pathAny",
                        argument=_LB_STATE_PATH,
                        expected="provisioning",
                    ),
                    dict(state="retry", matcher="error", expected="LoadBalancerNotFound"),
                ],
            ),
            load_balancers_deleted=dict(
                operation="DescribeLoadBalancers",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="retry",
                        matcher="pathAll",
                        argument=_LB_STATE_PATH,
                        expected="active",
                    ),
                    dict(state="success", matcher="error", expected="LoadBalancerNotFound"),
                ],
            ),
            load_balancer_ip_address_type_ipv4=dict(
                operation="DescribeLoadBalancers",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        argument=_LB_IP_ADDRESS_TYPE_PATH,
                        expected="ipv4",
                    ),
                    dict(
                        state="retry",
                        matcher="pathAny",
                        argument=_LB_IP_ADDRESS_TYPE_PATH,
                        expected="dualstack",
                    ),
                    dict(state="failure", matcher="error", expected="LoadBalancerNotFound"),
                ],
            ),
            load_balancer_ip_address_type_dualstack=dict(
                operation="DescribeLoadBalancers",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        argument=_LB_IP_ADDRESS_TYPE_PATH,
                        expected="dualstack",
                    ),
                    dict(
                        state="retry",
                        matcher="pathAny",
                        argument=_LB_IP_ADDRESS_TYPE_PATH,
                        expected="ipv4",
                    ),
                    dict(state="failure", matcher="error", expected="LoadBalancerNotFound"),
                ],
            ),
            target_in_service=dict(
                operation="DescribeTargetHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        argument="TargetHealthDescriptions[].TargetHealth.State",
                        expected="healthy",
                    ),
                    dict(state="retry", matcher="error", expected="InvalidInstance"),
                ],
            ),
            target_deregistered=dict(
                operation="DescribeTargetHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(state="success", matcher="error", expected="InvalidTarget"),
                    dict(
                        state="success",
                        matcher="pathAll",
                        argument="TargetHealthDescriptions[].TargetHealth.State",
                        expected="unused",
                    ),
                ],
            ),
        )

        return data


waiter_factory = ELBv2WaiterFactory()


class DynamicTargetGroupHealthWaiterFactory(BaseWaiterFactory):
    """
    Factory for creating target group health waiters with dynamic minimum target count thresholds.

    Args:
        min_count: Minimum number of healthy targets required in the target group
    """

    def __init__(self, min_count: int):
        self._min_count = min_count
        super().__init__()

    @property
    def _waiter_model_data(self):
        return {
            "min_targets_healthy": {
                "operation": "DescribeTargetHealth",
                "delay": 10,
                "maxAttempts": 60,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "path",
                        "expected": True,
                        "argument": f"length(TargetHealthDescriptions[?TargetHealth.State=='healthy']) >= `{self._min_count}`",
                    },
                    {
                        "state": "retry",
                        "matcher": "error",
                        "expected": "InvalidInstance",
                    },
                ],
            },
        }


def get_waiter_with_min_targets(client, min_count: int):
    """
    Get a waiter that waits for a minimum number of healthy targets in a target group.

    Args:
        client: boto3 ELBv2 client
        min_count: Minimum number of targets in healthy state required

    Returns:
        Waiter instance that checks for minimum healthy targets in the target group
    """
    factory = DynamicTargetGroupHealthWaiterFactory(min_count)
    return factory.get_waiter(client, "min_targets_healthy")

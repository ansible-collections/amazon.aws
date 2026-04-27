# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory


class ELBv2WaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = {
            "target_in_service": {
                "operation": "DescribeTargetHealth",
                "delay": 15,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "pathAll",
                        "expected": "healthy",
                        "argument": "TargetHealthDescriptions[].TargetHealth.State",
                    },
                    {
                        "state": "retry",
                        "matcher": "error",
                        "expected": "InvalidInstance",
                    },
                ],
            },
            "target_deregistered": {
                "operation": "DescribeTargetHealth",
                "delay": 15,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "error",
                        "expected": "InvalidTarget",
                    },
                    {
                        "state": "success",
                        "matcher": "pathAll",
                        "expected": "unused",
                        "argument": "TargetHealthDescriptions[].TargetHealth.State",
                    },
                ],
            },
        }

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

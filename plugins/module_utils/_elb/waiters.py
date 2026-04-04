# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory

# JMESPath constant for instance state matching
_INSTANCE_STATES_PATH = "InstanceStates[].State"


class ELBWaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = {
            "instance_deregistered": {
                "operation": "DescribeInstanceHealth",
                "delay": 15,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "pathAll",
                        "expected": "OutOfService",
                        "argument": _INSTANCE_STATES_PATH,
                    },
                    {
                        "state": "success",
                        "matcher": "error",
                        "expected": "InvalidInstance",
                    },
                ],
            },
            "instance_in_service": {
                "operation": "DescribeInstanceHealth",
                "delay": 15,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "pathAll",
                        "expected": "InService",
                        "argument": _INSTANCE_STATES_PATH,
                    },
                    {
                        "state": "retry",
                        "matcher": "error",
                        "expected": "InvalidInstance",
                    },
                ],
            },
            "any_instance_in_service": {
                "operation": "DescribeInstanceHealth",
                "delay": 15,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "pathAny",
                        "expected": "InService",
                        "argument": _INSTANCE_STATES_PATH,
                    },
                ],
            },
        }

        return data


waiter_factory = ELBWaiterFactory()


class DynamicELBHealthWaiterFactory(BaseWaiterFactory):
    """
    Factory for creating ELB health waiters with dynamic minimum instance count thresholds.

    Args:
        min_count: Minimum number of healthy instances required on the ELB
    """

    def __init__(self, min_count: int):
        self._min_count = min_count
        super().__init__()

    @property
    def _waiter_model_data(self):
        return {
            "min_instances_in_service": {
                "operation": "DescribeInstanceHealth",
                "delay": 10,
                "maxAttempts": 60,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "path",
                        "expected": True,
                        "argument": f"length(InstanceStates[?State=='InService']) >= `{self._min_count}`",
                    },
                    {
                        "state": "retry",
                        "matcher": "error",
                        "expected": "InvalidInstance",
                    },
                ],
            },
        }


def get_waiter_with_min_instances(client, min_count: int):
    """
    Get a waiter that waits for a minimum number of healthy instances on an ELB.

    Args:
        client: boto3 ELB client
        min_count: Minimum number of instances in InService state required

    Returns:
        Waiter instance that checks for minimum healthy instances on the ELB
    """
    factory = DynamicELBHealthWaiterFactory(min_count)
    return factory.get_waiter(client, "min_instances_in_service")

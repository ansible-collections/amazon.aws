# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory

WAITER_MAP = {
    "Standby": "instances_in_standby",
    "Terminated": "instances_terminated",
    "Detached": "instances_detached",
    "InService": "instances_in_service",
    "HEALTHY": "instances_healthy",
    "Healthy": "instances_healthy",
    "UNHEALTHY": "instances_unhealthy",
    "Unhealthy": "instances_unhealthy",
    "Protected": "instances_protected",
    "NotProtected": "instances_not_protected",
}


def _fail_on_instance_lifecycle_states(state):
    return {"state": "failure", "matcher": "pathAny", "expected": state, "argument": "AutoScalingInstances[].LifecycleState"}


def _success_on_instance_lifecycle_states(state):
    return {"state": "success", "matcher": "pathAll", "expected": state, "argument": "AutoScalingInstances[].LifecycleState"}


def _success_on_instance_health(health):
    return {"state": "success", "matcher": "pathAll", "expected": health, "argument": "AutoScalingInstances[].HealthStatus"}


def _success_on_instance_protection(state):
    return {
        "state": "success", "matcher": "pathAll", "expected": state, "argument": "AutoScalingInstances[].ProtectedFromScaleIn"
    }


def _no_instances(result):
    return {"state": result, "matcher": "path", "expected": True, "argument": "length(AutoScalingInstances[]) == `0`"}


def _asg_no_instances(result):
    """Check if ASG has zero instances."""
    return {
        "state": result,
        "matcher": "path",
        "expected": True,
        "argument": "length(AutoScalingGroups[0].Instances[]) == `0`",
    }


class AutoscalingWaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = {
            "instances_healthy": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_health("HEALTHY"),
                    # Terminated Instances can't reach "Healthy"
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                ],
            },
            "instances_unhealthy": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_health("UNHEALTHY"),
                    # Instances in an unhealthy state can end up being automatically terminated
                    _no_instances("success"),
                ],
            },
            "instances_protected": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_protection(True),
                ],
            },
            "instances_not_protected": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_protection(False),
                    # Instances without protection can end up being automatically terminated
                    _no_instances("success"),
                ],
            },
            "instances_in_service": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_lifecycle_states("InService"),
                    # Terminated instances can't reach InService
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                ],
            },
            "instances_in_standby": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_lifecycle_states("Standby"),
                    # Terminated instances can't reach Standby
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                ],
            },
            "instances_detached": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_lifecycle_states("Detached"),
                    _no_instances("success"),
                ],
            },
            "instances_terminated": {
                "operation": "DescribeAutoScalingInstances",
                "delay": 5,
                "maxAttempts": 120,
                "acceptors": [
                    _success_on_instance_lifecycle_states("Terminated"),
                    _no_instances("success"),
                ],
            },
            "group_exists": {
                "operation": "DescribeAutoScalingGroups",
                "delay": 5,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "path",
                        "expected": True,
                        "argument": "length(AutoScalingGroups[]) > `0`",
                    },
                    {
                        "state": "retry",
                        "matcher": "path",
                        "expected": True,
                        "argument": "length(AutoScalingGroups[]) == `0`",
                    },
                ],
            },
            "group_not_exists": {
                "operation": "DescribeAutoScalingGroups",
                "delay": 5,
                "maxAttempts": 40,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "path",
                        "expected": True,
                        "argument": "length(AutoScalingGroups[]) == `0`",
                    },
                    {
                        "state": "retry",
                        "matcher": "path",
                        "expected": True,
                        "argument": "length(AutoScalingGroups[]) > `0`",
                    },
                ],
            },
            "group_instances_terminated": {
                "operation": "DescribeAutoScalingGroups",
                "delay": 10,
                "maxAttempts": 60,
                "acceptors": [
                    _asg_no_instances("success"),
                ],
            },
        }

        return data


waiter_factory = AutoscalingWaiterFactory()


class DynamicASGViableInstanceWaiterFactory(BaseWaiterFactory):
    """
    Factory for creating ASG waiters with dynamic viable instance count thresholds.

    Args:
        min_count: Minimum number of viable instances (Healthy + InService) required
    """

    def __init__(self, min_count: int):
        self._min_count = min_count
        super().__init__()

    @property
    def _waiter_model_data(self):
        return {
            "min_viable_instances": {
                "operation": "DescribeAutoScalingGroups",
                "delay": 10,
                "maxAttempts": 60,
                "acceptors": [
                    {
                        "state": "success",
                        "matcher": "path",
                        "expected": True,
                        "argument": f"length(AutoScalingGroups[0].Instances[?HealthStatus=='Healthy' && LifecycleState=='InService']) >= `{self._min_count}`",
                    },
                ],
            },
        }


def get_waiter_with_min_viable_instances(client, min_count: int):
    """
    Get a waiter that waits for a minimum number of viable instances.

    Args:
        client: boto3 AutoScaling client
        min_count: Minimum number of viable instances (Healthy + InService) required

    Returns:
        Waiter instance that checks for minimum viable instances in an ASG
    """
    factory = DynamicASGViableInstanceWaiterFactory(min_count)
    return factory.get_waiter(client, "min_viable_instances")

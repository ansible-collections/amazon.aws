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
    return dict(state="failure", matcher="pathAny", expected=state, argument="AutoScalingInstances[].LifecycleState")


def _success_on_instance_lifecycle_states(state):
    return dict(state="success", matcher="pathAll", expected=state, argument="AutoScalingInstances[].LifecycleState")


def _success_on_instance_health(health):
    return dict(state="success", matcher="pathAll", expected=health, argument="AutoScalingInstances[].HealthStatus")


def _success_on_instance_protection(state):
    return dict(
        state="success", matcher="pathAll", expected=state, argument="AutoScalingInstances[].ProtectedFromScaleIn"
    )


def _no_instances(result):
    return dict(state=result, matcher="path", expected=True, argument="length(AutoScalingInstances[]) == `0`")


class AutoscalingWaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = dict(
            instances_healthy=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_health("HEALTHY"),
                    # Terminated Instances can't reach "Healthy"
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                ],
            ),
            instances_unhealthy=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_health("UNHEALTHY"),
                    # Instances in an unhealthy state can end up being automatically terminated
                    _no_instances("success"),
                ],
            ),
            instances_protected=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_protection(True),
                ],
            ),
            instances_not_protected=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_protection(False),
                    # Instances without protection can end up being automatically terminated
                    _no_instances("success"),
                ],
            ),
            instances_in_service=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_lifecycle_states("InService"),
                    # Terminated instances can't reach InService
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                ],
            ),
            instances_in_standby=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_lifecycle_states("Standby"),
                    # Terminated instances can't reach Standby
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                ],
            ),
            instances_detached=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_lifecycle_states("Detached"),
                    _no_instances("success"),
                ],
            ),
            instances_terminated=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _success_on_instance_lifecycle_states("Terminated"),
                    _no_instances("success"),
                ],
            ),
        )

        return data


waiter_factory = AutoscalingWaiterFactory()

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory


def _fail_on_instance_lifecycle_states(state):
    return dict(state="failure", matcher="pathAny", expected=state, argument="AutoScalingInstances[].LifecycleState")


def _retry_on_instance_lifecycle_states(state):
    return dict(state="retry", matcher="pathAny", expected=state, argument="AutoScalingInstances[].LifecycleState")


def _success_on_instance_lifecycle_states(state):
    return dict(state="success", matcher="pathAll", expected=state, argument="AutoScalingInstances[].LifecycleState")


def _no_instances(result):
    return dict(state=result, matcher="path", expected=True, argument="length(AutoScalingInstances[]) == `0`")


class AutoscalingWaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = dict(
            instances_in_service=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                    _fail_on_instance_lifecycle_states("Detaching"),
                    _fail_on_instance_lifecycle_states("Detached"),
                    _success_on_instance_lifecycle_states("InService"),
                ],
            ),
            instances_in_standby=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
                    _fail_on_instance_lifecycle_states("Detaching"),
                    _fail_on_instance_lifecycle_states("Detached"),
                    _success_on_instance_lifecycle_states("Standby"),
                ],
            ),
            instances_detached=dict(
                operation="DescribeAutoScalingInstances",
                delay=5,
                maxAttempts=120,
                acceptors=[
                    _fail_on_instance_lifecycle_states("Terminating"),
                    _fail_on_instance_lifecycle_states("Terminated"),
                    _fail_on_instance_lifecycle_states("Terminating:Wait"),
                    _fail_on_instance_lifecycle_states("Terminating:Proceed"),
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

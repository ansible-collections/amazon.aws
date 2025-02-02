#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: autoscaling_instance
version_added: 9.0.0
short_description: manage instances associated with AWS AutoScaling Groups (ASGs)
description:
  - Manage instances associated with AWS AutoScaling Groups (ASGs).
author:
  - "Mark Chappell (@tremble)"
options:
  group_name:
    description:
      - Name of the AutoScaling Group to manage.
    type: str
    required: True
  state:
    description:
      - The expected state of the instances.
      - V(present) - The instance(s) should be attached to the AutoScaling Group and in service.
      - V(attached) - The instance(s) should be attached to the AutoScaling Group.
        Instances in Standby will remain in standby.
      - V(standby) - The instance(s) should be placed into standby.
        Instances must already be part of the AutoScaling Group.
      - V(detached) - The instance(s) will be detached from the AutoScaling Group.
      - V(terminated) - The instance(s) will be terminated.
        By default terminated instances will be replaced with new instances, to reduce the desired
        capacity at the same time as terminating instances set O(decrement_desired_capacity=True).
      - B(Note:) When adding instances to an AutoScaling Group or returning instances to service
        from standby, the desired capacity is B(always) incremented.  If the total number of
        instances would exceed the maximum size of the group then the operation will fail.
    choices: ['present', 'attached', 'terminated', 'detached', 'standby']
    default: present
    type: str
  instance_ids:
    description:
      - The IDs of the EC2 instances.
      - Required if O(state) is one of V(standby), V(detached), V(terminated).
    type: list
    elements: str
  purge_instances:
    description:
      - Ignored unless O(state=present) or O(state=attached).
      - If O(purge_instances=True), any instances not in O(instance_ids) will be scheduled for B(termination).
      - B(Note:) Instances will be scheduled for termination B(after) any new instances are added to
        the AutoScaling Group and, if O(wait=True) and they will be terminated B(after) the new instances
        have reached the expected state.
    default: false
    type: bool
  decrement_desired_capacity:
    description:
      - When O(decrement_desired_capacity=True), detaching instances, terminating instances, or
        placing instances in standby mode will decrement the desired capacity of the AutoScaling Group
    default: false
    type: bool
  health:
    description:
      - Sets the health of an instance to a specific state.
    type: str
    choices: ["Healthy", "Unhealthy"]
  respect_grace_period:
    description:
      - Set O(respect_grace_period=False) to ignore the grace period associated with the AutoScaling
        group when modifying the O(health).
      - Ignored unless O(health) is set.
      - AWS defaults to respecting the grace period when modifying the health state of an instance.
    type: bool
    default: True
  protection:
    description:
      - Sets the scale-in protection attribute.
    type: bool
  wait:
    description:
      - When O(wait=True) will wait for instances to reach the requested state before returning.
    type: bool
    default: True
  wait_timeout:
    description:
      - Maximum time to wait for instances to reach the desired state.
    type: int
    default: 120
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
"""

RETURN = r"""
auto_scaling_instances:
  description: A description of the EC2 instances attached to an Auto Scaling group.
  returned: always
  type: list
  contains:
    availability_zone:
      description: The availability zone that the instance is in.
      returned: always
      type: str
      sample: "us-east-1a"
    health_status:
      description: The last reported health status of the instance.
      returned: always
      type: str
      sample: "Healthy"
    instance_id:
      description: The ID of the instance.
      returned: always
      type: str
      sample: "i-123456789abcdef01"
    instance_type:
      description: The instance type of the instance.
      returned: always
      type: str
      sample: "t3.micro"
    launch_configuration_name:
      description: The name of the launch configuration used when launching the instance.
      returned: When the instance was launched using an Auto Scaling launch configuration.
      type: str
      sample: "ansible-test-49630214-mchappel-thinkpadt14gen3-asg-instance-1"
    launch_template:
      description: A description of the launch template used when launching the instance.
      returned: When the instance was launched using an Auto Scaling launch template.
      type: dict
      contains:
        launch_template_id:
          description: The ID of the launch template used when launching the instance.
          returned: always
          type: str
          sample: "12345678-abcd-ef12-2345-6789abcdef01"
        launch_template_name:
          description: The name of the launch template used when launching the instance.
          returned: always
          type: str
          sample: "example-launch-configuration"
        version:
          description: The version of the launch template used when launching the instance.
          returned: always
          type: str
          sample: "$Default"
    lifecycle_state:
      description: The lifecycle state of the instance.
      returned: always
      type: str
      sample: "InService"
    protected_from_scale_in:
      description: Whether the instance is protected from termination when the Auto Scaling group is scaled in.
      returned: always
      type: bool
      sample: false
"""

import typing
from copy import deepcopy

from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import WAITER_MAP
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AnsibleAutoScalingError
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AutoScalingErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import get_autoscaling_instances
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import get_autoscaling_waiter
from ansible_collections.amazon.aws.plugins.module_utils.errors import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.waiter import custom_waiter_config

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple

    from ansible_collections.amazon.aws.plugins.module_utils.retries import RetryingBotoClientWrapper
    from ansible_collections.amazon.aws.plugins.module_utils.transformations import AnsibleAWSResourceList


# There's also a number of "Warmed" states that we could support with relatively minimal effort, but
# we can't test them (currently)
STATE_MAP = {
    "pending": ["Pending", "Pending:Proceed", "Pending:Wait"],
    "stable": ["InService", "Standby"],
    "entering": ["EnteringStandby"],
    "entering+": ["EnteringStandby", "Standby"],
    "detaching": ["Detaching"],
    "detaching+": ["Detaching", "Detached"],
    "terminating": ["Terminating", "Terminating:Wait", "Terminating:Proceed"],
    "terminating+": ["Terminating", "Terminating:Wait", "Terminating:Proceed", "Terminated"],
}


def _all_instance_ids(instances: List) -> Set[str]:
    return {i.get("instance_id") for i in instances}


def _instance_ids_with_health(instances: List, health: str) -> Set[str]:
    health = health.lower()
    return {i.get("instance_id") for i in instances if i.get("health_status", "").lower() == health}


def _instance_ids_with_protection(instances: List, protection: bool) -> Set[str]:
    return {i.get("instance_id") for i in instances if i.get("protected_from_scale_in", False) == protection}


def _instance_ids_in_states(instances: List, states: List[str]) -> Set[str]:
    states = [s.lower() for s in states]
    return {i.get("instance_id") for i in instances if i.get("lifecycle_state", "").lower() in states}


def _token_instance(instance_id, group_name):
    # Returns the minimum information we need for a new instance when adding a new node in check mode
    return dict(
        instance_id=instance_id,
        auto_scaling_group_name=group_name,
        health_status="Healthy",
    )


@AutoScalingErrorHandler.common_error_handler("set instance health")
@AWSRetry.jittered_backoff()
def _set_instance_health(client: RetryingBotoClientWrapper, instance_id: str, health: str, respect_grace: bool):
    return client.set_instance_health(
        InstanceId=instance_id,
        HealthStatus=health,
        ShouldRespectGracePeriod=respect_grace,
    )


@AutoScalingErrorHandler.common_error_handler("set instance protection")
@AWSRetry.jittered_backoff()
def _set_instance_protection(
    client: RetryingBotoClientWrapper, instance_ids: Set[str], group_name: str, protected: bool
):
    return client.set_instance_protection(
        InstanceIds=list(instance_ids),
        AutoScalingGroupName=group_name,
        ProtectedFromScaleIn=protected,
    )


@AutoScalingErrorHandler.common_error_handler("detach auto scaling instances from group")
@AWSRetry.jittered_backoff()
def _detach_instances(
    client: RetryingBotoClientWrapper, instance_ids: Set[str], group_name: str, decrement_capacity: bool
):
    return client.detach_instances(
        InstanceIds=list(instance_ids),
        AutoScalingGroupName=group_name,
        ShouldDecrementDesiredCapacity=decrement_capacity,
    )


@AutoScalingErrorHandler.common_error_handler("attach auto scaling instances to group")
@AWSRetry.jittered_backoff()
def _attach_instances(client: RetryingBotoClientWrapper, instance_ids: Set[str], group_name: str):
    return client.attach_instances(
        InstanceIds=list(instance_ids),
        AutoScalingGroupName=group_name,
    )


@AutoScalingErrorHandler.common_error_handler("terminate auto scaling instances")
@AWSRetry.jittered_backoff()
def _terminate_instances(
    client: RetryingBotoClientWrapper, instance_ids: Set[str], group_name: str, decrement_capacity: bool
):
    return client.terminate_instance_in_auto_scaling_group(
        InstanceIds=list(instance_ids),
        AutoScalingGroupName=group_name,
        ShouldDecrementDesiredCapacity=decrement_capacity,
    )


@AutoScalingErrorHandler.common_error_handler("place auto scaling instances into standby")
@AWSRetry.jittered_backoff()
def _enter_standby(
    client: RetryingBotoClientWrapper, instance_ids: Set[str], group_name: str, decrement_capacity: bool
):
    return client.enter_standby(
        InstanceIds=list(instance_ids),
        AutoScalingGroupName=group_name,
        ShouldDecrementDesiredCapacity=decrement_capacity,
    )


@AutoScalingErrorHandler.common_error_handler("return auto scaling instances to group from standby")
@AWSRetry.jittered_backoff()
def _leave_standby(client: RetryingBotoClientWrapper, instance_ids: Set[str], group_name: str):
    return client.exit_standby(
        InstanceIds=list(instance_ids),
        AutoScalingGroupName=group_name,
    )


def wait_instance_state(
    client: RetryingBotoClientWrapper,
    state: str,
    check_mode: bool,
    group_name: str,
    instance_ids: Set[str],
    wait: bool,
    wait_timeout: int,
) -> None:
    if not wait:
        return
    if check_mode:
        return
    if not instance_ids:
        return

    waiter_config = custom_waiter_config(timeout=wait_timeout, default_pause=10)

    waiter = get_autoscaling_waiter(client, WAITER_MAP[state])
    AutoScalingErrorHandler.common_error_handler(f"wait for instances to reach {state}")(waiter.wait)(
        InstanceIds=list(instance_ids),
        WaiterConfig=waiter_config,
    )

    return


def _inject_instances(instances, group_name, missing_ids):
    if not missing_ids:
        return instances
    for instance in list(missing_ids):
        instances.append(_token_instance(instance, group_name))
    instances = sorted(instances, key=lambda d: d.get("instance_id", None))
    return instances


def _change_instances(instances, group_name, change_ids, state=None, health=None, protection=None):
    for instance in instances:
        if instance.get("instance_id") in change_ids:
            if state is not None:
                instance["lifecycle_state"] = state
            if health is not None:
                instance["health_status"] = health
            if protection is not None:
                instance["protected_from_scale_in"] = protection
    return instances


def ensure_instance_terminated(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    instance_ids: List[str],
    decrement_desired_capacity: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    instance_ids = set(instance_ids)

    # We don't need to change these instances, we may need to wait for them
    terminating_ids = _instance_ids_in_states(instances_start, STATE_MAP["terminating+"]) & instance_ids

    # We'll need to wait for the in-progress changes to complete
    detaching_ids = _instance_ids_in_states(instances_start, STATE_MAP["detaching"]) & instance_ids
    pending_ids = _instance_ids_in_states(instances_start, STATE_MAP["pending"]) & instance_ids
    entering_ids = _instance_ids_in_states(instances_start, STATE_MAP["entering"]) & instance_ids
    # These instances are ready to terminate
    ready_ids = _instance_ids_in_states(instances_start, STATE_MAP["stable"]) & instance_ids

    if check_mode:
        change_ids = detaching_ids | pending_ids | entering_ids | ready_ids | terminating_ids
        instances_changed = _change_instances(deepcopy(instances_start), group_name, change_ids, state="Terminated")
        return bool(change_ids - terminating_ids), instances_changed

    # We have to wait for instances to transition to their stable states before changing them
    if entering_ids:
        wait_instance_state(client, "Standby", check_mode, group_name, entering_ids, wait, wait_timeout)
    if pending_ids:
        wait_instance_state(client, "InService", check_mode, group_name, pending_ids, wait, wait_timeout)
    ready_ids |= entering_ids | pending_ids

    if ready_ids:
        _terminate_instances(client, ready_ids, group_name, decrement_desired_capacity)

    terminating_ids |= ready_ids
    wait_instance_state(client, "Terminated", check_mode, group_name, terminating_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return bool(ready_ids), instances_complete


def ensure_instance_absent(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    instance_ids: List[str],
    decrement_desired_capacity: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    instance_ids = set(instance_ids)

    # We don't need to change these instances, we may need to wait for them
    detaching_ids = _instance_ids_in_states(instances_start, STATE_MAP["detaching+"]) & instance_ids
    # On the basis of "be conservative in what you do, be liberal in what you accept from others"
    # We'll treat instances that someone else has terminated, as "detached" from the ASG, since
    # they won't be attached to the ASG.
    terminating_ids = _instance_ids_in_states(instances_start, STATE_MAP["terminating+"]) & instance_ids

    # We'll need to wait for the in-progress changes to complete
    pending_ids = _instance_ids_in_states(instances_start, STATE_MAP["pending"]) & instance_ids
    entering_ids = _instance_ids_in_states(instances_start, STATE_MAP["entering"]) & instance_ids
    # These instances are ready to detach
    ready_ids = _instance_ids_in_states(instances_start, STATE_MAP["stable"]) & instance_ids

    if check_mode:
        change_ids = pending_ids | entering_ids | ready_ids | detaching_ids
        instances_changed = _change_instances(deepcopy(instances_start), group_name, change_ids, state="Detached")
        return bool(change_ids - detaching_ids), instances_changed

    # We have to wait for instances to transition to their stable state before changing them
    if entering_ids:
        wait_instance_state(client, "Standby", check_mode, group_name, entering_ids, wait, wait_timeout)
    if pending_ids:
        wait_instance_state(client, "InService", check_mode, group_name, pending_ids, wait, wait_timeout)

    ready_ids |= entering_ids | pending_ids
    if ready_ids:
        _detach_instances(client, ready_ids, group_name, decrement_desired_capacity)
    detaching_ids |= ready_ids

    if terminating_ids:
        wait_instance_state(client, "Terminated", check_mode, group_name, terminating_ids, wait, wait_timeout)
    if detaching_ids:
        wait_instance_state(client, "Detached", check_mode, group_name, detaching_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return bool(ready_ids), instances_complete


def ensure_instance_attached(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    instance_ids: List[str],
    decrement_desired_capacity: bool,
    purge: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    instance_ids = set(instance_ids)
    all_ids = _all_instance_ids(instances_start)

    # These instances need to be attached
    missing_ids = instance_ids - all_ids
    missing_ids |= _instance_ids_in_states(instances_start, ["Detached"]) & instance_ids
    detaching_ids = _instance_ids_in_states(instances_start, STATE_MAP["detaching"]) & instance_ids
    pending_ids = _instance_ids_in_states(instances_start, STATE_MAP["pending"]) & instance_ids
    terminating_ids = _instance_ids_in_states(instances_start, STATE_MAP["terminating+"]) & instance_ids
    # Ids that need to be removed
    purge_ids = (all_ids - instance_ids) if purge else set()

    if check_mode:
        instances_changed = _inject_instances(deepcopy(instances_start), group_name, missing_ids)
        missing_ids |= detaching_ids
        instances_changed = _change_instances(instances_changed, group_name, missing_ids, state="InService")
        instances_changed = _change_instances(instances_changed, group_name, purge_ids, state="Terminated")
        return bool(missing_ids | purge_ids), instances_changed

    if detaching_ids:
        # We have to wait for instances to transition to Detached before we can re-attach them
        wait_instance_state(client, "Detached", check_mode, group_name, detaching_ids, wait, wait_timeout)
    missing_ids |= detaching_ids

    if missing_ids:
        _attach_instances(client, missing_ids, group_name)
    pending_ids |= missing_ids

    # This includes potentially waiting for instances which were Pending when we started
    wait_instance_state(client, "InService", check_mode, group_name, pending_ids, wait, wait_timeout)

    # While, in theory, we could make the ordering of Add/Remove configurable, the logic becomes
    # difficult to test.  As such we're going to hard code the order of operations.
    # Add/Wait/Terminate is the order least likely to result in 0 available
    # instances, so we do any termination after ensuring instances are InService.
    if purge_ids:
        _terminate_instances(client, purge_ids, group_name, decrement_desired_capacity)
        terminating_ids |= purge_ids
        wait_instance_state(client, "Terminated", check_mode, group_name, terminating_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return bool(purge_ids | missing_ids), instances_complete


def ensure_instance_present(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    instance_ids: List[str],
    decrement_desired_capacity: bool,
    purge: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    instance_ids = set(instance_ids)
    all_ids = _all_instance_ids(instances_start)

    # We just need to wait for these
    pending_ids = _instance_ids_in_states(instances_start, STATE_MAP["pending"]) & instance_ids
    # We need to wait for these before we can attach/re-activate them
    detaching_ids = _instance_ids_in_states(instances_start, STATE_MAP["detaching+"]) & instance_ids
    entering_ids = _instance_ids_in_states(instances_start, STATE_MAP["entering"]) & instance_ids
    # These instances need to be brought out of standby
    standby_ids = _instance_ids_in_states(instances_start, ["Standby"]) & instance_ids
    # These instances need to be attached
    missing_ids = instance_ids - all_ids

    # Ids that need to be removed
    purge_ids = (all_ids - instance_ids) if purge else set()

    if check_mode:
        change_ids = detaching_ids | entering_ids | standby_ids | missing_ids
        instances_changed = _inject_instances(deepcopy(instances_start), group_name, missing_ids)
        instances_changed = _change_instances(
            instances_changed, group_name, change_ids | pending_ids, state="InService"
        )
        instances_changed = _change_instances(instances_changed, group_name, purge_ids, state="Terminated")
        return bool(change_ids | purge_ids), instances_changed

    if detaching_ids:
        wait_instance_state(client, "Detached", check_mode, group_name, detaching_ids, wait, wait_timeout)
    missing_ids |= detaching_ids - purge_ids
    # They've left the ASG of their own accord, we'll leave them be...
    purge_ids = purge_ids - detaching_ids

    if missing_ids:
        _attach_instances(client, missing_ids, group_name)

    if entering_ids:
        wait_instance_state(client, "Standby", check_mode, group_name, entering_ids, wait, wait_timeout)
    standby_ids |= entering_ids - purge_ids

    if standby_ids:
        _leave_standby(client, standby_ids, group_name)

    # This includes potentially waiting for instances which were Pending when we started
    wait_instance_state(client, "InService", check_mode, group_name, instance_ids, wait, wait_timeout)

    # While, in theory, we could make the ordering of Add/Remove configurable, the logic becomes
    # difficult to test.  As such we're going to hard code the order of operations.
    # Add/Wait/Terminate is the order least likely to result in 0 available
    # instances, so we do any termination after ensuring instances are InService.
    if purge_ids:
        _terminate_instances(client, purge_ids, group_name, decrement_desired_capacity)
        wait_instance_state(client, "Terminated", check_mode, group_name, detaching_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return bool(purge_ids | standby_ids | missing_ids), instances_complete


def ensure_instance_standby(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    instance_ids: List[str],
    decrement_desired_capacity: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    instance_ids = set(instance_ids)

    # We need to wait for these instances to enter "InService" before we can do anything with them
    pending_ids = _instance_ids_in_states(instances_start, STATE_MAP["pending"]) & instance_ids
    # These instances are ready to move to Standby
    ready_ids = _instance_ids_in_states(instances_start, ["InService"]) & instance_ids
    # These instances are moving into Standby
    entering_ids = _instance_ids_in_states(instances_start, STATE_MAP["entering"]) & instance_ids

    if check_mode:
        change_ids = pending_ids | ready_ids
        instances_changed = _change_instances(deepcopy(instances_start), group_name, change_ids, state="Standby")
        return bool(ready_ids), instances_changed

    if pending_ids:
        # We have to wait for instances to transition to InService
        wait_instance_state(client, "InService", check_mode, group_name, pending_ids, wait, wait_timeout)
    ready_ids |= pending_ids

    if ready_ids:
        _enter_standby(client, ready_ids, group_name, decrement_desired_capacity)
    entering_ids |= ready_ids

    # This includes potentially waiting for instances which were "Entering" Standby when we started
    wait_instance_state(client, "Standby", check_mode, group_name, entering_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return bool(ready_ids), instances_complete


def ensure_instance_health(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    health: Optional[str],
    instance_ids: List[str],
    respect_grace_period: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    # nb. With Health the API documentation's inconsistent:
    # it appears to want Capitalized for set(), but spits out UPPERCASE for get()
    if health is None:
        return False, instances_start
    if instance_ids is None:
        instance_ids = _all_instance_ids(instances_start)
    else:
        instance_ids = set(instance_ids)

    ready_ids = _instance_ids_with_health(instances_start, health) & instance_ids
    changed_ids = instance_ids - ready_ids

    if not changed_ids:
        return False, instances_start

    if check_mode:
        health = health.upper()
        changed_instances = _change_instances(deepcopy(instances_start), group_name, changed_ids, health=health)
        return True, changed_instances

    for instance_id in changed_ids:
        _set_instance_health(client, instance_id, health, respect_grace_period)
    health = health.upper()
    wait_instance_state(client, health.upper(), check_mode, group_name, changed_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return True, instances_complete


def ensure_instance_protection(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    protection: Optional[bool],
    instance_ids: List[str],
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    if protection is None:
        return False, instances_start
    if instance_ids is None:
        instance_ids = _all_instance_ids(instances_start)
    else:
        instance_ids = set(instance_ids)

    ready_ids = _instance_ids_with_protection(instances_start, protection) & instance_ids
    changed_ids = instance_ids - ready_ids

    if not changed_ids:
        return False, instances_start

    if check_mode:
        changed_instances = _change_instances(deepcopy(instances_start), group_name, changed_ids, protection=protection)
        return True, changed_instances

    _set_instance_protection(client, changed_ids, group_name, protection)

    state = "Protected" if protection else "NotProtected"

    wait_instance_state(client, state, check_mode, group_name, changed_ids, wait, wait_timeout)

    instances_complete = get_autoscaling_instances(client, group_name=group_name)
    return True, instances_complete


def ensure_instance_pool(
    client: RetryingBotoClientWrapper,
    check_mode: bool,
    instances_start: AnsibleAWSResourceList,
    group_name: str,
    state: str,
    instance_ids: List[str],
    purge_instances: bool,
    decrement_desired_capacity: bool,
    wait: bool,
    wait_timeout: int,
) -> Tuple[bool, AnsibleAWSResourceList]:
    if state == "standby":
        return ensure_instance_standby(
            client,
            check_mode,
            instances_start,
            group_name,
            instance_ids or [],
            decrement_desired_capacity,
            wait,
            wait_timeout,
        )
    if state == "detached":
        return ensure_instance_absent(
            client,
            check_mode,
            instances_start,
            group_name,
            instance_ids or [],
            decrement_desired_capacity,
            wait,
            wait_timeout,
        )

    # Not valid for standby/terminated/detached
    if instance_ids is None:
        instance_ids = _all_instance_ids(instances_start)

    if state == "attached":
        return ensure_instance_attached(
            client,
            check_mode,
            instances_start,
            group_name,
            instance_ids,
            decrement_desired_capacity,
            purge_instances,
            wait,
            wait_timeout,
        )
    if state == "present":
        return ensure_instance_present(
            client,
            check_mode,
            instances_start,
            group_name,
            instance_ids,
            decrement_desired_capacity,
            purge_instances,
            wait,
            wait_timeout,
        )

    return False, instances_start


def _validate_standby_conditions(params: Dict[str, Any], instances: AnsibleAWSResourceList) -> None:
    instance_ids = set(params.get("instance_ids"))
    all_ids = _all_instance_ids(instances)

    missing_ids = instance_ids - all_ids
    if missing_ids:
        raise AnsibleAutoScalingError(
            message=f"Unable to place instance(s) ({missing_ids}) into Standby - instances not attached to AutoScaling Group ({params['group_name']})",
        )

    # We don't need to change these instances, we may need to wait for them
    standby_ids = _instance_ids_in_states(instances, STATE_MAP["entering+"])
    # We need to wait for these instances to enter "InService" before we can do anything with them
    pending_ids = _instance_ids_in_states(instances, STATE_MAP["pending"])
    # These instances are ready to move to Standby
    ready_ids = _instance_ids_in_states(instances, ["InService"])

    bad_ids = all_ids - standby_ids - pending_ids - ready_ids
    if bad_ids:
        raise AnsibleAutoScalingError(
            message=f"Unable to place instance(s) ({bad_ids}) into Standby - instances not in a state that can transition to Standby or InService",
        )

    if pending_ids and not params.get("wait"):
        raise AnsibleAutoScalingError(
            message=f"Unable to plance instances ({pending_ids}) into Standby - currently in a pending state and wait is disabled",
        )

    return


def _validate_remove_conditions(params: Dict[str, Any], instances: AnsibleAWSResourceList) -> None:
    target_verb = {"detached": "detach", "terminated": "terminate"}[params["state"]]

    if params["health"] is not None:
        raise AnsibleAutoScalingError(message=f"Unable to set instance health when state is {params['state']}")

    instance_ids = set(params.get("instance_ids"))
    pending_ids = _instance_ids_in_states(instances, STATE_MAP["pending"] + STATE_MAP["entering"])

    if (pending_ids & instance_ids) and not params.get("wait"):
        raise AnsibleAutoScalingError(
            message=f"Unable to {target_verb} instances ({pending_ids & instance_ids}) currently in a pending state and wait is disabled",
        )

    return


def _validate_attach_conditions(params: Dict[str, Any], instances: AnsibleAWSResourceList) -> None:
    instance_ids = set(params.get("instance_ids") or [])

    # These instances are terminating, we can't do anything with them.
    terminating_ids = _instance_ids_in_states(instances, STATE_MAP["terminating+"]) & instance_ids
    # We need to wait for these instances to enter "InService" or "Standby" before we can do anything with them
    pending_ids = _instance_ids_in_states(instances, STATE_MAP["entering"]) & instance_ids
    detaching_ids = _instance_ids_in_states(instances, STATE_MAP["detaching"]) & instance_ids

    if terminating_ids:
        raise AnsibleAutoScalingError(
            message=f"Unable to attach instances ({terminating_ids}) to AutoScaling group - instances not in a state that can transition to InService",
        )

    if not params.get("wait"):
        if pending_ids and params.get("state") == "present":
            raise AnsibleAutoScalingError(
                message=f"Unable to plance instances ({pending_ids}) into Service - currently entering standby and wait is disabled",
            )
        if detaching_ids:
            raise AnsibleAutoScalingError(
                message=f"Unable to attach instances ({pending_ids}) to AutoScaling group - currently detaching and wait is disabled",
            )


def validate_params(params: Dict[str, Any], instances: AnsibleAWSResourceList) -> None:
    if params["state"] in ["terminated", "detached"]:
        _validate_remove_conditions(params, instances)
    if params["state"] == "standby":
        _validate_standby_conditions(params, instances)
    if params["state"] in ["attached", "present"]:
        _validate_attach_conditions(params, instances)

    return


def do(module):
    client = module.client("autoscaling", retry_decorator=AWSRetry.jittered_backoff())

    instances_start = get_autoscaling_instances(client, group_name=module.params["group_name"])
    validate_params(module.params, instances_start)

    instances = deepcopy(instances_start)

    changed_pool, instances = ensure_instance_pool(
        client,
        check_mode=module.check_mode,
        instances_start=instances,
        group_name=module.params["group_name"],
        state=module.params["state"],
        instance_ids=module.params["instance_ids"],
        purge_instances=module.params["purge_instances"],
        decrement_desired_capacity=module.params["decrement_desired_capacity"],
        wait=module.params["wait"],
        wait_timeout=module.params["wait_timeout"],
    )

    changed_protection, instances = ensure_instance_protection(
        client,
        check_mode=module.check_mode,
        instances_start=instances,
        group_name=module.params["group_name"],
        protection=module.params["protection"],
        instance_ids=module.params["instance_ids"],
        wait=module.params["wait"],
        wait_timeout=module.params["wait_timeout"],
    )

    changed_health, instances = ensure_instance_health(
        client,
        check_mode=module.check_mode,
        instances_start=instances,
        group_name=module.params["group_name"],
        health=module.params["health"],
        instance_ids=module.params["instance_ids"],
        respect_grace_period=module.params["respect_grace_period"],
        wait=module.params["wait"],
        wait_timeout=module.params["wait_timeout"],
    )

    changed = changed_pool or changed_protection or changed_health

    result = {"changed": changed, "auto_scaling_instances": instances}

    if module._diff:  # pylint: disable=protected-access
        result["diff"] = dict(
            before=dict(auto_scaling_instances=instances_start),
            after=dict(auto_scaling_instances=instances),
        )

    result["changed_pool"] = changed_pool
    result["changed_protection"] = changed_protection
    result["changed_health"] = changed_health

    module.exit_json(**result)


def main():
    argument_spec = dict(
        group_name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "attached", "terminated", "detached", "standby"], default="present"),
        instance_ids=dict(type="list", elements="str"),
        purge_instances=dict(type="bool", default=False),
        decrement_desired_capacity=dict(type="bool", default=False),
        health=dict(type="str", choices=["Healthy", "Unhealthy"]),
        respect_grace_period=dict(type="bool", default=True),
        protection=dict(type="bool"),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=120),
    )

    required_if = [
        ["state", "terminated", ["instance_ids"]],
        ["state", "detached", ["instance_ids"]],
        ["state", "standby", ["instance_ids"]],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
    )

    try:
        do(module)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# It would be nice to be able to use autoscaling.XYZ, but we're bound by Ansible's "empty-init"
# policy: https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/empty-init.html


from __future__ import annotations

import typing

# Not intended for general re-use / re-import
from ._autoscaling import common as _common
from ._autoscaling import groups as _groups
from ._autoscaling import instances as _instances
from ._autoscaling import transformations as _transformations
from ._autoscaling import waiters as _waiters
from .retries import AWSRetry

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional

    from .retries import RetryingBotoClientWrapper
    from .transformation import AnsibleAWSResourceList
    from .transformation import BotoResourceList

# Intended for general use / re-import
AnsibleAutoScalingError = _common.AnsibleAutoScalingError
AutoScalingErrorHandler = _common.AutoScalingErrorHandler
WAITER_MAP = _waiters.WAITER_MAP


def get_autoscaling_groups(
    client: RetryingBotoClientWrapper, group_names: Optional[List[str]] = None
) -> AnsibleAWSResourceList:
    groups = _groups.describe_auto_scaling_groups(client, group_names)
    return _transformations.normalize_autoscaling_groups(groups)


def _get_autoscaling_instances(
    client: RetryingBotoClientWrapper, instance_ids: Optional[List[str]] = None, group_name: Optional[str] = None
) -> BotoResourceList:
    if group_name:
        try:
            groups = _groups.describe_auto_scaling_groups(client, [group_name])
            return groups[0]["Instances"]
        except (KeyError, IndexError):
            return None
    return _instances.describe_auto_scaling_instances(client, instance_ids)


def get_autoscaling_instances(
    client: RetryingBotoClientWrapper, instance_ids: Optional[List[str]] = None, group_name: Optional[str] = None
) -> AnsibleAWSResourceList:
    instances = _get_autoscaling_instances(client, instance_ids=instance_ids, group_name=group_name)
    return _transformations.normalize_autoscaling_instances(instances, group_name=group_name)


def get_autoscaling_waiter(client: RetryingBotoClientWrapper, waiter_name: str) -> Any:
    return _waiters.waiter_factory.get_waiter(client, waiter_name)


# ====================================
# TODO Move these about and refactor
# ====================================


@AutoScalingErrorHandler.list_error_handler("describe InstanceRefreshes", {})
@AWSRetry.jittered_backoff()
def describe_instance_refreshes(
    client,
    auto_scaling_group_name: str,
    instance_refresh_ids: Optional[List[str]] = None,
    next_token: Optional[str] = None,
    max_records: Optional[int] = None,
) -> Dict[str, Any]:
    params = {"AutoScalingGroupName": auto_scaling_group_name}
    if instance_refresh_ids:
        params["InstanceRefreshIds"] = instance_refresh_ids
    if next_token:
        params["NextToken"] = next_token
    if max_records:
        params["MaxRecords"] = max_records
    return client.describe_instance_refreshes(**params)


@AutoScalingErrorHandler.common_error_handler("start InstanceRefresh")
@AWSRetry.jittered_backoff(catch_extra_error_codes=["InstanceRefreshInProgress"])
def start_instance_refresh(client, auto_scaling_group_name: str, **params: Dict[str, Any]) -> str:
    return client.start_instance_refresh(AutoScalingGroupName=auto_scaling_group_name, **params).get(
        "InstanceRefreshId"
    )


@AutoScalingErrorHandler.common_error_handler("cancel InstanceRefresh")
@AWSRetry.jittered_backoff(catch_extra_error_codes=["InstanceRefreshInProgress"])
def cancel_instance_refresh(client, auto_scaling_group_name: str) -> str:
    return client.cancel_instance_refresh(AutoScalingGroupName=auto_scaling_group_name).get("InstanceRefreshId")

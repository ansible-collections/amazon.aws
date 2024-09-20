# -*- coding: utf-8 -*-

# Copyright (c) 2024 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .botocore import is_boto3_error_code
from .errors import AWSErrorHandler
from .exceptions import AnsibleAWSError
from .retries import AWSRetry


class AnsibleAutoScalingError(AnsibleAWSError):
    pass


class AutoScalingErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleAutoScalingError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("")


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

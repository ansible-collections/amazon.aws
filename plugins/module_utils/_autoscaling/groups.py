# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..retries import AWSRetry

# from .common import AnsibleAutoScalingError
from .common import AutoScalingErrorHandler


@AutoScalingErrorHandler.list_error_handler("list auto scaling groups", default_value=[])
@AWSRetry.jittered_backoff()
def describe_auto_scaling_groups(client, group_names=None, filters=None):
    args = {}
    if group_names:
        args["AutoScalingGroupNames"] = group_names
    if filters:
        args["Filters"] = filters

    paginator = client.get_paginator("describe_auto_scaling_groups")
    return paginator.paginate(**args).build_full_result()["AutoScalingGroups"]

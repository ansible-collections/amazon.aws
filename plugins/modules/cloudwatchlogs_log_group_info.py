#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloudwatchlogs_log_group_info
version_added: 5.0.0
short_description: Get information about log_group in CloudWatchLogs
description:
  - Lists the specified log groups. You can list all your log groups or filter the results by prefix.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - Willian Ricardo (@willricardo) <willricardo@gmail.com>
options:
  log_group_name:
    description:
      - The name or prefix of the log group to filter by.
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- amazon.aws.cloudwatchlogs_log_group_info:
    log_group_name: test-log-group
"""

RETURN = r"""
log_groups:
    description: Return the list of complex objects representing log groups
    returned: success
    type: complex
    contains:
        log_group_name:
            description: The name of the log group.
            returned: always
            type: str
        creation_time:
            description: The creation time of the log group.
            returned: always
            type: int
        retention_in_days:
            description: The number of days to retain the log events in the specified log group.
            returned: always
            type: int
        metric_filter_count:
            description: The number of metric filters.
            returned: always
            type: int
        arn:
            description: The Amazon Resource Name (ARN) of the log group.
            returned: always
            type: str
        stored_bytes:
            description: The number of bytes stored.
            returned: always
            type: str
        kms_key_id:
            description: The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.
            returned: always
            type: str
        tags:
            description: A dictionary representing the tags on the log group.
            returned: always
            type: dict
            version_added: 4.0.0
            version_added_collection: community.aws
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.exponential_backoff()
def list_tags_log_group_with_backoff(client, log_group_name):
    return client.list_tags_log_group(logGroupName=log_group_name)


@AWSRetry.exponential_backoff()
def describe_log_groups_with_backoff(client, **kwargs):
    paginator = client.get_paginator("describe_log_groups")
    return paginator.paginate(**kwargs).build_full_result()


def describe_log_group(client, log_group_name, module):
    params = {}
    if log_group_name:
        params["logGroupNamePrefix"] = log_group_name
    try:
        desc_log_group = describe_log_groups_with_backoff(client, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Unable to describe log group {log_group_name}")

    for log_group in desc_log_group["logGroups"]:
        log_group_name = log_group["logGroupName"]
        try:
            tags = list_tags_log_group_with_backoff(client, log_group_name)
        except is_boto3_error_code("AccessDeniedException"):
            tags = {}
            module.warn(f"Permission denied listing tags for log group {log_group_name}")
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg=f"Unable to describe tags for log group {log_group_name}")
        log_group["tags"] = tags.get("tags", {})

    return desc_log_group


def main():
    argument_spec = dict(
        log_group_name=dict(),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        logs = module.client("logs")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    desc_log_group = describe_log_group(client=logs, log_group_name=module.params["log_group_name"], module=module)
    final_log_group_snake = []

    for log_group in desc_log_group["logGroups"]:
        final_log_group_snake.append(camel_dict_to_snake_dict(log_group, ignore_list=["tags"]))

    desc_log_group_result = dict(changed=False, log_groups=final_log_group_snake)
    module.exit_json(**desc_log_group_result)


if __name__ == "__main__":
    main()

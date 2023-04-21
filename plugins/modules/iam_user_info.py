#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_user_info
version_added: 5.0.0
short_description: Gather IAM user(s) facts in AWS
description:
  - This module can be used to gather IAM user(s) facts in AWS.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - Constantin Bugneac (@Constantin07)
  - Abhijeet Kasurde (@Akasurde)
options:
  name:
    description:
      - The name of the IAM user to look for.
    required: false
    type: str
  group:
    description:
      - The group name name of the IAM user to look for. Mutually exclusive with C(path).
    required: false
    type: str
  path:
    description:
      - The path to the IAM user. Mutually exclusive with C(group).
      - If specified, then would get all user names whose path starts with user provided value.
    required: false
    default: '/'
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Gather facts about "test" user.
- name: Get IAM user info
  amazon.aws.iam_user_info:
    name: "test"

# Gather facts about all users in the "dev" group.
- name: Get IAM user info
  amazon.aws.iam_user_info:
    group: "dev"

# Gather facts about all users with "/division_abc/subdivision_xyz/" path.
- name: Get IAM user info
  amazon.aws.iam_user_info:
    path: "/division_abc/subdivision_xyz/"
"""

RETURN = r"""
iam_users:
    description: list of maching iam users
    returned: success
    type: complex
    contains:
        arn:
            description: the ARN of the user
            returned: if user exists
            type: str
            sample: "arn:aws:iam::123456789012:user/dev/test_user"
        create_date:
            description: the datetime user was created
            returned: if user exists
            type: str
            sample: "2016-05-24T12:24:59+00:00"
        password_last_used:
            description: the last datetime the password was used by user
            returned: if password was used at least once
            type: str
            sample: "2016-05-25T13:39:11+00:00"
        path:
            description: the path to user
            returned: if user exists
            type: str
            sample: "/dev/"
        user_id:
            description: the unique user id
            returned: if user exists
            type: str
            sample: "AIDUIOOCQKTUGI6QJLGH2"
        user_name:
            description: the user name
            returned: if user exists
            type: str
            sample: "test_user"
        tags:
            description: User tags.
            type: dict
            returned: if user exists
            sample: '{"Env": "Prod"}'
"""

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


@AWSRetry.exponential_backoff()
def list_iam_users_with_backoff(client, operation, **kwargs):
    paginator = client.get_paginator(operation)
    return paginator.paginate(**kwargs).build_full_result()


def describe_iam_user(user):
    tags = boto3_tag_list_to_ansible_dict(user.pop("Tags", []))
    user = camel_dict_to_snake_dict(user)
    user["tags"] = tags
    return user


def list_iam_users(connection, module):
    name = module.params.get("name")
    group = module.params.get("group")
    path = module.params.get("path")

    params = dict()
    iam_users = []

    if not group and not path:
        if name:
            params["UserName"] = name
        try:
            iam_users.append(connection.get_user(**params)["User"])
        except is_boto3_error_code("NoSuchEntity"):
            pass
        except (ClientError, BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg=f"Couldn't get IAM user info for user {name}")

    if group:
        params["GroupName"] = group
        try:
            iam_users = list_iam_users_with_backoff(connection, "get_group", **params)["Users"]
        except is_boto3_error_code("NoSuchEntity"):
            pass
        except (ClientError, BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg=f"Couldn't get IAM user info for group {group}")
        if name:
            iam_users = [user for user in iam_users if user["UserName"] == name]

    if path and not group:
        params["PathPrefix"] = path
        try:
            iam_users = list_iam_users_with_backoff(connection, "list_users", **params)["Users"]
        except is_boto3_error_code("NoSuchEntity"):
            pass
        except (ClientError, BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg=f"Couldn't get IAM user info for path {path}")
        if name:
            iam_users = [user for user in iam_users if user["UserName"] == name]

    module.exit_json(iam_users=[describe_iam_user(user) for user in iam_users])


def main():
    argument_spec = dict(name=dict(), group=dict(), path=dict(default="/"))

    module = AnsibleAWSModule(
        argument_spec=argument_spec, mutually_exclusive=[["group", "path"]], supports_check_mode=True
    )

    connection = module.client("iam")

    list_iam_users(connection, module)


if __name__ == "__main__":
    main()

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
      - O(user_name) was added as an alias in release 7.2.0.
    required: false
    type: str
    aliases: ["user_name"]
  group:
    description:
      - The group name name of the IAM user to look for. Mutually exclusive with C(path).
      - O(group_name) was added as an alias in release 7.2.0.
    required: false
    type: str
    aliases: ["group_name"]
  path_prefix:
    description:
      - The path to the IAM user. Mutually exclusive with O(group).
      - If specified, then would get all user names whose path starts with user provided value.
    required: false
    default: '/'
    type: str
    aliases: ["path", "prefix"]
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
    description: List of maching iam users.
    returned: always
    type: complex
    contains:
        arn:
            description: The ARN of the user.
            returned: when user exists.
            type: str
            sample: "arn:aws:iam::123456789012:user/dev/test_user"
        create_date:
            description: The datetime user was created.
            returned: when user exists.
            type: str
            sample: "2016-05-24T12:24:59+00:00"
        password_last_used:
            description: The last datetime the password was used by user.
            returned: if password was used at least once
            type: str
            sample: "2016-05-25T13:39:11+00:00"
        path:
            description: The path to user.
            returned: when user exists.
            type: str
            sample: "/dev/"
        user_id:
            description: The unique user id.
            returned: when user exists.
            type: str
            sample: "AIDUIOOCQKTUGI6QJLGH2"
        user_name:
            description: The user name.
            returned: when user exists.
            type: str
            sample: "test_user"
        tags:
            description: User tags.
            type: dict
            returned: when user exists.
            sample: '{"Env": "Prod"}'
        login_profile:
            description:
              - Detailed login profile information if the user has access to log in from AWS default console.
              - Returns an empty object {} if no access.
            returned: when user exists.
            type: dict
            sample: {"create_date": "2024-03-20T12:50:56+00:00", "password_reset_required": false, "user_name": "i_am_a_user"}
            contains:
              create_date:
                description: The date and time, in ISO 8601 date-time format, when the user was created.
                type: str
                returned: always
              password_reset_required:
                description: Specifies whether the user is required to set a new password on next sign-in.
                type: bool
                returned: always
              user_name:
                description: The name of the IAM user
                type: str
                returned: always
"""

from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import IAMErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_group
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_user
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_user_tags
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_users
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_user
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@IAMErrorHandler.list_error_handler("get login profile", {})
@AWSRetry.jittered_backoff()
def check_console_access(connection, user_name):
    return connection.get_login_profile(UserName=user_name)["LoginProfile"]


def _list_users(connection, name, group, path):
    # name but not path or group
    if name and path == "/" and not group:
        return [get_iam_user(connection, name, normalize=False)]

    iam_users = []

    if group:
        iam_group = get_iam_group(connection, group)
        if iam_group:
            iam_users = iam_group["Users"]
    else:
        iam_users = list_iam_users(connection, path=path)

    if not iam_users:
        return []

    # filter by name when a path or group was specified
    if name:
        iam_users = [u for u in iam_users if u["UserName"] == name]

    for user in iam_users:
        user["Tags"] = list_iam_user_tags(connection, user["UserName"])

    return iam_users


def list_users(connection, name, group, path):
    users = _list_users(connection, name, group, path)
    users = [u for u in users if u is not None]
    for user in users:
        user["LoginProfile"] = check_console_access(connection, user["UserName"])
    return [normalize_iam_user(user) for user in users]


def main():
    argument_spec = dict(
        name=dict(aliases=["user_name"]),
        group=dict(aliases=["group_name"]),
        path_prefix=dict(aliases=["path", "prefix"], default="/"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["group", "path_prefix"]],
        supports_check_mode=True,
    )

    name = module.params.get("name")
    group = module.params.get("group")
    path = module.params.get("path_prefix")

    connection = module.client("iam")

    try:
        module.exit_json(changed=False, iam_users=list_users(connection, name, group, path))
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_policy_info
version_added: 5.0.0
short_description: Retrieve inline IAM policies for users, groups, and roles
description:
  - Supports fetching of inline IAM policies for IAM users, groups and roles.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  iam_type:
    description:
      - Type of IAM resource you wish to retrieve inline policies for.
    required: true
    choices: [ "user", "group", "role"]
    type: str
  iam_name:
    description:
      - Name of IAM resource you wish to retrieve inline policies for. In other words, the user name, group name or role name.
    required: true
    type: str
  policy_name:
    description:
      - Name of a specific IAM inline policy you with to retrieve.
    required: false
    type: str
author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Describe all inline IAM policies on an IAM User
  amazon.aws.iam_policy_info:
    iam_type: user
    iam_name: example_user

- name: Describe a specific inline policy on an IAM Role
  amazon.aws.iam_policy_info:
    iam_type: role
    iam_name: example_role
    policy_name: example_policy
"""

RETURN = r"""
policies:
    description: A list containing the matching IAM inline policy names and their data
    returned: success
    type: complex
    contains:
        policy_name:
            description: The Name of the inline policy
            returned: success
            type: str
        policy_document:
            description: The JSON document representing the inline IAM policy
            returned: success
            type: list
policy_names:
    description: A list of matching names of the IAM inline policies on the queried object
    returned: success
    type: list
all_policy_names:
    description: A list of names of all of the IAM inline policies on the queried object
    returned: success
    type: list
"""

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


class Policy:
    def __init__(self, client, name, policy_name):
        self.client = client
        self.name = name
        self.policy_name = policy_name
        self.changed = False

    @staticmethod
    def _iam_type():
        return ""

    def _list(self, name):
        return {}

    def list(self):
        return self._list(self.name).get("PolicyNames", [])

    def _get(self, name, policy_name):
        return "{}"

    def get(self, policy_name):
        return self._get(self.name, policy_name)["PolicyDocument"]

    def get_all(self):
        policies = list()
        for policy in self.list():
            policies.append({"policy_name": policy, "policy_document": self.get(policy)})
        return policies

    def run(self):
        policy_list = self.list()
        ret_val = {"changed": False, self._iam_type() + "_name": self.name, "all_policy_names": policy_list}
        if self.policy_name is None:
            ret_val.update(policies=self.get_all())
            ret_val.update(policy_names=policy_list)
        elif self.policy_name in policy_list:
            ret_val.update(policies=[{"policy_name": self.policy_name, "policy_document": self.get(self.policy_name)}])
            ret_val.update(policy_names=[self.policy_name])
        return ret_val


class UserPolicy(Policy):
    @staticmethod
    def _iam_type():
        return "user"

    def _list(self, name):
        return self.client.list_user_policies(aws_retry=True, UserName=name)

    def _get(self, name, policy_name):
        return self.client.get_user_policy(aws_retry=True, UserName=name, PolicyName=policy_name)


class RolePolicy(Policy):
    @staticmethod
    def _iam_type():
        return "role"

    def _list(self, name):
        return self.client.list_role_policies(aws_retry=True, RoleName=name)

    def _get(self, name, policy_name):
        return self.client.get_role_policy(aws_retry=True, RoleName=name, PolicyName=policy_name)


class GroupPolicy(Policy):
    @staticmethod
    def _iam_type():
        return "group"

    def _list(self, name):
        return self.client.list_group_policies(aws_retry=True, GroupName=name)

    def _get(self, name, policy_name):
        return self.client.get_group_policy(aws_retry=True, GroupName=name, PolicyName=policy_name)


def main():
    argument_spec = dict(
        iam_type=dict(required=True, choices=["user", "group", "role"]),
        iam_name=dict(required=True),
        policy_name=dict(default=None, required=False),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    args = dict(
        client=module.client("iam", retry_decorator=AWSRetry.jittered_backoff()),
        name=module.params.get("iam_name"),
        policy_name=module.params.get("policy_name"),
    )
    iam_type = module.params.get("iam_type")

    try:
        if iam_type == "user":
            policy = UserPolicy(**args)
        elif iam_type == "role":
            policy = RolePolicy(**args)
        elif iam_type == "group":
            policy = GroupPolicy(**args)

        module.exit_json(**(policy.run()))
    except is_boto3_error_code("NoSuchEntity") as e:
        module.exit_json(changed=False, msg=e.response["Error"]["Message"])
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


if __name__ == "__main__":
    main()

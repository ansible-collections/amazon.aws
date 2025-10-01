#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_policy
version_added: 5.0.0
short_description: Manage inline IAM policies for users, groups, and roles
description:
  - Allows uploading or removing inline IAM policies for IAM users, groups or roles.
  - To administer managed policies please see M(community.aws.iam_user), M(community.aws.iam_role),
    M(amazon.aws.iam_group) and M(community.aws.iam_managed_policy).
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  iam_type:
    description:
      - Type of IAM resource.
    required: true
    choices: [ "user", "group", "role"]
    type: str
  iam_name:
    description:
      - Name of IAM resource you wish to target for policy actions. In other words, the user name, group name or role name.
    required: true
    type: str
  policy_name:
    description:
      - The name label for the policy to create or remove.
    required: true
    type: str
  policy_json:
    description:
      - A properly json formatted policy as string.
    type: json
  state:
    description:
      - Whether to create or delete the IAM policy.
    choices: [ "present", "absent"]
    default: present
    type: str
  skip_duplicates:
    description:
      - When O(skip_duplicates=true) the module looks for any policies that match the document you pass in.
        If there is a match it will not make a new policy object with the same rules.
    default: false
    type: bool

author:
  - "Jonathan I. Davila (@defionscode)"
  - "Dennis Podkovyrin (@sbj-ss)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Advanced example, create two new groups and add a READ-ONLY policy to both
# groups.
- name: Create Two Groups, Mario and Luigi
  amazon.aws.iam_group:
    name: "{{ item }}"
    state: present
  loop:
    - Mario
    - Luigi
  register: new_groups

- name: Apply READ-ONLY policy to new groups that have been recently created
  amazon.aws.iam_policy:
    iam_type: group
    iam_name: "{{ item.iam_group.group.group_name }}"
    policy_name: "READ-ONLY"
    policy_json: "{{ lookup('template', 'readonly.json.j2') }}"
    state: present
  loop: "{{ new_groups.results }}"

# Create a new S3 policy with prefix per user
- name: Create S3 policy from template
  amazon.aws.iam_policy:
    iam_type: user
    iam_name: "{{ item.user }}"
    policy_name: "s3_limited_access_{{ item.prefix }}"
    state: present
    policy_json: "{{ lookup('template', 's3_policy.json.j2') }}"
    loop:
      - user: s3_user
        prefix: s3_user_prefix
"""

RETURN = r"""
user_name:
    description: Name of IAM user.
    returned: When I(iam_type=user)
    type: str
    sample: "ExampleUser001"
group_name:
    description: Name of IAM group.
    returned: When I(iam_type=group)
    type: str
    sample: "ExampleGroup001"
role_name:
    description: Name of IAM role.
    returned: When I(iam_type=role)
    type: str
    sample: "ExampleRole001"
policy_names:
    description: A list of names of the inline policies embedded in the specified IAM resource (user, group, or role).
    returned: always
    type: list
    elements: str
    sample: ["READ-ONLY"]
diff:
    description: A dict representing difference between policies applied on IAM resource (user, group, or role).
    returned: always
    type: dict
    contains:
        before:
            description: The policy that exists on IAM resource before new policy is applied.
            returned: always
            type: dict
            sample: {
                        "READ-ONLY": {
                            "Statement": [
                                {
                                    "Action": "ec2:DescribeAccountAttributes",
                                    "Effect": "Deny",
                                    "Resource": "*",
                                    "Sid": "VisualEditor0"
                                }
                            ],
                            "Version": "2012-10-17"
                        }
                    }
        after:
            description: The current policy on IAM resource after new policy is applied.
            returned: always
            type: dict
            sample: {
                        "READ-ONLY": {
                            "Statement": [
                                {
                                    "Action": "ec2:DescribeAccountAttributes",
                                    "Effect": "Allow",
                                    "Resource": "*",
                                    "Sid": "VisualEditor0"
                                }
                            ],
                            "Version": "2012-10-17"
                        }
                    }
"""

import json

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass


from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


class PolicyError(Exception):
    pass


class Policy:
    def __init__(self, client, name, policy_name, policy_json, skip_duplicates, state, check_mode):
        self.client = client
        self.name = name
        self.policy_name = policy_name
        self.policy_json = policy_json
        self.skip_duplicates = skip_duplicates
        self.state = state
        self.check_mode = check_mode
        self.changed = False

        self.original_policies = self.get_all_policies().copy()
        self.updated_policies = {}

    @staticmethod
    def _iam_type():
        return ""

    def _list(self, name):
        return {}

    def list(self):
        try:
            return self._list(self.name).get("PolicyNames", [])
        except is_boto3_error_code("AccessDenied"):
            return []

    def _get(self, name, policy_name):
        return "{}"

    def get(self, policy_name):
        try:
            return self._get(self.name, policy_name)["PolicyDocument"]
        except is_boto3_error_code("AccessDenied"):
            return {}

    def _put(self, name, policy_name, policy_doc):
        pass

    def put(self, policy_doc):
        self.changed = True

        if self.check_mode:
            return

        self._put(self.name, self.policy_name, json.dumps(policy_doc, sort_keys=True))

    def _delete(self, name, policy_name):
        pass

    def delete(self):
        self.updated_policies = self.original_policies.copy()

        if self.policy_name not in self.list():
            self.changed = False
            return

        self.changed = True
        self.updated_policies.pop(self.policy_name, None)

        if self.check_mode:
            return

        self._delete(self.name, self.policy_name)

    def get_policy_text(self):
        try:
            if self.policy_json is not None:
                return self.get_policy_from_json()
        except json.JSONDecodeError as e:
            raise PolicyError(f"Failed to decode the policy as valid JSON: {str(e)}")
        return None

    def get_policy_from_json(self):
        if isinstance(self.policy_json, str):
            pdoc = json.loads(self.policy_json)
        else:
            pdoc = self.policy_json
        return pdoc

    def get_all_policies(self):
        policies = {}
        for pol in self.list():
            policies[pol] = self.get(pol)
        return policies

    def create(self):
        matching_policies = []
        policy_doc = self.get_policy_text()
        policy_match = False
        for pol in self.list():
            if not compare_policies(self.original_policies[pol], policy_doc):
                matching_policies.append(pol)
                policy_match = True

        self.updated_policies = self.original_policies.copy()

        if self.policy_name in matching_policies:
            return
        if self.skip_duplicates and policy_match:
            return

        self.put(policy_doc)
        self.updated_policies[self.policy_name] = policy_doc

    def run(self):
        if self.state == "present":
            self.create()
        elif self.state == "absent":
            self.delete()
        return {
            "changed": self.changed,
            self._iam_type() + "_name": self.name,
            "policy_names": self.list(),
            "diff": dict(
                before=self.original_policies,
                after=self.updated_policies,
            ),
        }


class UserPolicy(Policy):
    @staticmethod
    def _iam_type():
        return "user"

    def _list(self, name):
        return self.client.list_user_policies(aws_retry=True, UserName=name)

    def _get(self, name, policy_name):
        return self.client.get_user_policy(aws_retry=True, UserName=name, PolicyName=policy_name)

    def _put(self, name, policy_name, policy_doc):
        return self.client.put_user_policy(
            aws_retry=True, UserName=name, PolicyName=policy_name, PolicyDocument=policy_doc
        )

    def _delete(self, name, policy_name):
        return self.client.delete_user_policy(aws_retry=True, UserName=name, PolicyName=policy_name)


class RolePolicy(Policy):
    @staticmethod
    def _iam_type():
        return "role"

    def _list(self, name):
        return self.client.list_role_policies(aws_retry=True, RoleName=name)

    def _get(self, name, policy_name):
        return self.client.get_role_policy(aws_retry=True, RoleName=name, PolicyName=policy_name)

    def _put(self, name, policy_name, policy_doc):
        return self.client.put_role_policy(
            aws_retry=True, RoleName=name, PolicyName=policy_name, PolicyDocument=policy_doc
        )

    def _delete(self, name, policy_name):
        return self.client.delete_role_policy(aws_retry=True, RoleName=name, PolicyName=policy_name)


class GroupPolicy(Policy):
    @staticmethod
    def _iam_type():
        return "group"

    def _list(self, name):
        return self.client.list_group_policies(aws_retry=True, GroupName=name)

    def _get(self, name, policy_name):
        return self.client.get_group_policy(aws_retry=True, GroupName=name, PolicyName=policy_name)

    def _put(self, name, policy_name, policy_doc):
        return self.client.put_group_policy(
            aws_retry=True, GroupName=name, PolicyName=policy_name, PolicyDocument=policy_doc
        )

    def _delete(self, name, policy_name):
        return self.client.delete_group_policy(aws_retry=True, GroupName=name, PolicyName=policy_name)


def main():
    argument_spec = dict(
        iam_type=dict(required=True, choices=["user", "group", "role"]),
        state=dict(default="present", choices=["present", "absent"]),
        iam_name=dict(required=True),
        policy_name=dict(required=True),
        policy_json=dict(type="json", default=None, required=False),
        skip_duplicates=dict(type="bool", default=False, required=False),
    )
    required_if = [
        ("state", "present", ("policy_json",), True),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)

    args = dict(
        client=module.client("iam", retry_decorator=AWSRetry.jittered_backoff()),
        name=module.params.get("iam_name"),
        policy_name=module.params.get("policy_name"),
        policy_json=module.params.get("policy_json"),
        skip_duplicates=module.params.get("skip_duplicates"),
        state=module.params.get("state"),
        check_mode=module.check_mode,
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
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)
    except PolicyError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_group
version_added: 1.0.0
version_added_collection: community.aws
short_description: Manage AWS IAM groups
description:
  - Manage AWS IAM groups.
author:
  - Nick Aslanidis (@naslanidis)
  - Maksym Postument (@infectsoldier)
options:
  name:
    description:
      - The name of the group.
      - >-
        Note: Group names are unique within an account.  Paths (I(path)) do B(not) affect
        the uniqueness requirements of I(name).  For example it is not permitted to have both
        C(/Path1/MyGroup) and C(/Path2/MyGroup) in the same account.
      - The alias C(group_name) was added in release 7.2.0.
    required: true
    aliases: ['group_name']
    type: str
  path:
    description:
      - The group path.
      - For more information about IAM paths, see the AWS IAM identifiers documentation
        U(https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    aliases: ['prefix', 'path_prefix']
    version_added: 7.1.0
    type: str
  managed_policies:
    description:
      - A list of managed policy ARNs or friendly names to attach to the role.
      - If known, it is recommended to use ARNs rather than friendly names to avoid additional
        lookups.
      - To embed an inline policy, use M(amazon.aws.iam_policy).
    required: false
    type: list
    elements: str
    default: []
    aliases: ['managed_policy']
  users:
    description:
      - A list of existing users to add as members of the group.
    required: false
    type: list
    elements: str
    default: []
  state:
    description:
      - Create or remove the IAM group.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  purge_policies:
    description:
      - When I(purge_policies=true) any managed policies not listed in I(managed_policies) will be detatched.
    required: false
    default: false
    type: bool
    aliases: ['purge_policy', 'purge_managed_policies']
  purge_users:
    description:
      - When I(purge_users=true) users which are not included in I(users) will be detached.
    required: false
    default: false
    type: bool
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a group
  amazon.aws.iam_group:
    name: testgroup1
    state: present

- name: Create a group and attach a managed policy using its ARN
  amazon.aws.iam_group:
    name: testgroup1
    managed_policies:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    state: present

- name: Create a group with users as members and attach a managed policy using its ARN
  amazon.aws.iam_group:
    name: testgroup1
    managed_policies:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    users:
      - test_user1
      - test_user2
    state: present

- name: Remove all managed policies from an existing group with an empty list
  amazon.aws.iam_group:
    name: testgroup1
    state: present
    purge_policies: true

- name: Remove all group members from an existing group
  amazon.aws.iam_group:
    name: testgroup1
    managed_policies:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    purge_users: true
    state: present

- name: Delete the group
  amazon.aws.iam_group:
    name: testgroup1
    state: absent
"""

RETURN = r"""
iam_group:
    description: dictionary containing all the group information including group membership
    returned: success
    type: complex
    contains:
        group:
            description: dictionary containing all the group information
            returned: success
            type: complex
            contains:
                arn:
                    description: the Amazon Resource Name (ARN) specifying the group
                    type: str
                    sample: "arn:aws:iam::1234567890:group/testgroup1"
                create_date:
                    description: the date and time, in ISO 8601 date-time format, when the group was created
                    type: str
                    sample: "2017-02-08T04:36:28+00:00"
                group_id:
                    description: the stable and unique string identifying the group
                    type: str
                    sample: AGPA12345EXAMPLE54321
                group_name:
                    description: the friendly name that identifies the group
                    type: str
                    sample: testgroup1
                path:
                    description: the path to the group
                    type: str
                    sample: /
        users:
            description: list containing all the group members
            returned: success
            type: complex
            contains:
                arn:
                    description: the Amazon Resource Name (ARN) specifying the user
                    type: str
                    sample: "arn:aws:iam::1234567890:user/test_user1"
                create_date:
                    description: the date and time, in ISO 8601 date-time format, when the user was created
                    type: str
                    sample: "2017-02-08T04:36:28+00:00"
                user_id:
                    description: the stable and unique string identifying the user
                    type: str
                    sample: AIDA12345EXAMPLE54321
                user_name:
                    description: the friendly name that identifies the user
                    type: str
                    sample: testgroup1
                path:
                    description: the path to the user
                    type: str
                    sample: /
        attached_policies:
            version_added: 7.1.0
            description:
                - list containing basic information about managed policies attached to the group.
            returned: success
            type: complex
            contains:
                policy_arn:
                    description: the Amazon Resource Name (ARN) specifying the managed policy.
                    type: str
                    sample: "arn:aws:iam::123456789012:policy/test_policy"
                policy_name:
                    description: the friendly name that identifies the policy.
                    type: str
                    sample: test_policy
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import convert_managed_policy_names_to_arns
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def ensure_path(connection, module, group_info, path):
    if path is None:
        return False

    if group_info["Group"].get("Path") == path:
        return False

    if module.check_mode:
        return True

    connection.update_group(
        aws_retry=True,
        GroupName=group_info["Group"]["GroupName"],
        NewPath=path,
    )
    return True


def detach_policies(connection, module, group_name, policies):
    for policy_arn in policies:
        try:
            connection.detach_group_policy(aws_retry=True, GroupName=group_name, PolicyArn=policy_arn)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't detach policy {policy_arn} from group {group_name}")


def attach_policies(connection, module, group_name, policies):
    for policy_arn in policies:
        try:
            connection.attach_group_policy(aws_retry=True, GroupName=group_name, PolicyArn=policy_arn)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't attach policy {policy_arn} to group {group_name}")


def ensure_managed_policies(connection, module, group_info, managed_policies, purge_policies):
    if managed_policies is None:
        return False

    if managed_policies:
        managed_policies = convert_managed_policy_names_to_arns(connection, managed_policies)

    group_name = group_info["Group"]["GroupName"]

    current_attached_policies_desc = get_attached_policy_list(connection, module, group_name)
    current_attached_policies = [policy["PolicyArn"] for policy in current_attached_policies_desc]

    policies_to_add = list(set(managed_policies) - set(current_attached_policies))
    policies_to_remove = []
    if purge_policies:
        policies_to_remove = list(set(current_attached_policies) - set(managed_policies))

    if not policies_to_add and not policies_to_remove:
        return False

    if module.check_mode:
        return True

    detach_policies(connection, module, group_name, policies_to_remove)
    attach_policies(connection, module, group_name, policies_to_add)

    return True


def add_group_members(connection, module, group_name, members):
    for user in members:
        try:
            connection.add_user_to_group(GroupName=group_name, UserName=user)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't add user {user} to group {group_name}")


def remove_group_members(connection, module, group_name, members):
    for user in members:
        try:
            connection.remove_user_from_group(aws_retry=True, GroupName=group_name, UserName=user)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't remove user {user} from group {group_name}")


def ensure_group_members(connection, module, group_info, users, purge_users):
    if users is None:
        return False

    group_name = group_info["Group"]["GroupName"]
    current_group_members = [member["UserName"] for member in group_info["Users"]]

    members_to_add = list(set(users) - set(current_group_members))
    members_to_remove = []
    if purge_users:
        members_to_remove = list(set(current_group_members) - set(users))

    if not members_to_add and not members_to_remove:
        return False

    if module.check_mode:
        return True

    add_group_members(connection, module, group_name, members_to_add)
    remove_group_members(connection, module, group_name, members_to_remove)

    return True


def get_or_create_group(connection, module, group_name, path):
    # Get group
    try:
        group = get_group(connection, module, group_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get group")

    if group:
        return False, group

    params = {"GroupName": group_name}
    if path is not None:
        params["Path"] = path

    # Check mode means we would create the group
    if module.check_mode:
        module.exit_json(changed=True, create_params=params)

    try:
        group = connection.create_group(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create group")

    if "Users" not in group:
        group["Users"] = []

    return True, group


def create_or_update_group(connection, module):
    changed, group_info = get_or_create_group(connection, module, module.params["name"], module.params["path"])

    # Update the path if necessary
    changed |= ensure_path(
        connection,
        module,
        group_info,
        module.params["path"],
    )

    # Manage managed policies
    changed |= ensure_managed_policies(
        connection,
        module,
        group_info,
        module.params["managed_policies"],
        module.params["purge_policies"],
    )

    # Manage group memberships
    changed |= ensure_group_members(
        connection,
        module,
        group_info,
        module.params["users"],
        module.params["purge_users"],
    )

    if module.check_mode:
        module.exit_json(changed=changed)

    # Get the group again
    try:
        group_info = get_group(connection, module, module.params["name"])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, f"Couldn't get group {module.params['name']}")
    try:
        policies = get_attached_policy_list(connection, module, module.params["name"])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, f"Couldn't get group policies {module.params['name']}")
    group_info["AttachedPolicies"] = policies

    module.exit_json(changed=changed, iam_group=camel_dict_to_snake_dict(group_info))


def destroy_group(connection, module):
    group_name = module.params.get("name")

    try:
        group = get_group(connection, module, group_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, f"Couldn't get group {group_name}")

    if not group:
        module.exit_json(changed=False)

    # Check mode means we would remove this group
    if module.check_mode:
        module.exit_json(changed=True)

    # Remove any attached policies otherwise deletion fails
    current_policies_desc = get_attached_policy_list(connection, module, group_name)
    current_policies = [policy["PolicyArn"] for policy in current_policies_desc]
    detach_policies(connection, module, group_name, current_policies)

    # Remove any users in the group otherwise deletion fails
    current_group_members = [user["UserName"] for user in group["Users"]]
    remove_group_members(connection, module, group_name, current_group_members)

    try:
        connection.delete_group(aws_retry=True, GroupName=group_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, f"Couldn't delete group {group_name}")

    module.exit_json(changed=True)


@AWSRetry.jittered_backoff()
def get_group(connection, module, name):
    try:
        paginator = connection.get_paginator("get_group")
        return paginator.paginate(GroupName=name).build_full_result()
    except is_boto3_error_code("NoSuchEntity"):
        return None


@AWSRetry.jittered_backoff()
def get_attached_policy_list(connection, module, name):
    try:
        paginator = connection.get_paginator("list_attached_group_policies")
        return paginator.paginate(GroupName=name).build_full_result()["AttachedPolicies"]
    except is_boto3_error_code("NoSuchEntity"):
        return None


@AWSRetry.jittered_backoff()
def list_all_policies(connection, module):
    paginator = connection.get_paginator("list_policies")
    return paginator.paginate().build_full_result()["Policies"]


def main():
    argument_spec = dict(
        name=dict(aliases=["group_name"], required=True),
        path=dict(aliases=["prefix", "path_prefix"]),
        managed_policies=dict(default=[], type="list", aliases=["managed_policy"], elements="str"),
        users=dict(default=[], type="list", elements="str"),
        state=dict(choices=["present", "absent"], required=True),
        purge_users=dict(default=False, type="bool"),
        purge_policies=dict(default=False, type="bool", aliases=["purge_policy", "purge_managed_policies"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    identifier_problem = validate_iam_identifiers(
        "group", name=module.params.get("name"), path=module.params.get("path")
    )
    if identifier_problem:
        module.fail_json(msg=identifier_problem)

    connection = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")

    try:
        if state == "present":
            create_or_update_group(connection, module)
        else:
            destroy_group(connection, module)
    except AnsibleIAMError as e:
        if e.exception:
            module.fail_json_aws(e.exception, msg=e.message)
        module.fail_json(msg=e.message)


if __name__ == "__main__":
    main()

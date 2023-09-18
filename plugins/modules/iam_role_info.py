#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_role_info
version_added: 1.0.0
short_description: Gather information on IAM roles
description:
    - Gathers information about IAM roles.
author:
    - "Will Thames (@willthames)"
options:
    name:
        description:
            - Name of a role to search for.
            - Mutually exclusive with I(path_prefix).
        aliases:
            - role_name
        type: str
    path_prefix:
        description:
            - Prefix of role to restrict IAM role search for.
            - Mutually exclusive with I(name).
        type: str
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: find all existing IAM roles
  community.aws.iam_role_info:
  register: result

- name: describe a single role
  community.aws.iam_role_info:
    name: MyIAMRole

- name: describe all roles matching a path prefix
  community.aws.iam_role_info:
    path_prefix: /application/path
"""

RETURN = r"""
iam_roles:
  description: List of IAM roles
  returned: always
  type: complex
  contains:
    arn:
      description: Amazon Resource Name for IAM role.
      returned: always
      type: str
      sample: arn:aws:iam::123456789012:role/AnsibleTestRole
    assume_role_policy_document:
      description:
        - The policy that grants an entity permission to assume the role
        - |
          Note: the case of keys in this dictionary are currently converted from CamelCase to
          snake_case.  In a release after 2023-12-01 this behaviour will change.
      returned: always
      type: dict
    assume_role_policy_document_raw:
      description: The policy document describing what can assume the role.
      returned: always
      type: dict
      version_added: 5.3.0
    create_date:
      description: Date IAM role was created.
      returned: always
      type: str
      sample: '2017-10-23T00:05:08+00:00'
    inline_policies:
      description: List of names of inline policies.
      returned: always
      type: list
      sample: []
    managed_policies:
      description: List of attached managed policies.
      returned: always
      type: complex
      contains:
        policy_arn:
          description: Amazon Resource Name for the policy.
          returned: always
          type: str
          sample: arn:aws:iam::123456789012:policy/AnsibleTestEC2Policy
        policy_name:
          description: Name of managed policy.
          returned: always
          type: str
          sample: AnsibleTestEC2Policy
    instance_profiles:
      description: List of attached instance profiles.
      returned: always
      type: complex
      contains:
        arn:
          description: Amazon Resource Name for the instance profile.
          returned: always
          type: str
          sample: arn:aws:iam::123456789012:instance-profile/AnsibleTestEC2Policy
        create_date:
          description: Date instance profile was created.
          returned: always
          type: str
          sample: '2017-10-23T00:05:08+00:00'
        instance_profile_id:
          description: Amazon Identifier for the instance profile.
          returned: always
          type: str
          sample: AROAII7ABCD123456EFGH
        instance_profile_name:
          description: Name of instance profile.
          returned: always
          type: str
          sample: AnsibleTestEC2Policy
        path:
          description: Path of instance profile.
          returned: always
          type: str
          sample: /
        roles:
          description: List of roles associated with this instance profile.
          returned: always
          type: list
          sample: []
    path:
      description: Path of role.
      returned: always
      type: str
      sample: /
    role_id:
      description: Amazon Identifier for the role.
      returned: always
      type: str
      sample: AROAII7ABCD123456EFGH
    role_name:
      description: Name of the role.
      returned: always
      type: str
      sample: AnsibleTestRole
    tags:
      description: Role tags.
      type: dict
      returned: always
      sample: '{"Env": "Prod"}'
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


@AWSRetry.jittered_backoff()
def list_iam_roles_with_backoff(client, **kwargs):
    paginator = client.get_paginator("list_roles")
    return paginator.paginate(**kwargs).build_full_result()


@AWSRetry.jittered_backoff()
def list_iam_role_policies_with_backoff(client, role_name):
    paginator = client.get_paginator("list_role_policies")
    return paginator.paginate(RoleName=role_name).build_full_result()["PolicyNames"]


@AWSRetry.jittered_backoff()
def list_iam_attached_role_policies_with_backoff(client, role_name):
    paginator = client.get_paginator("list_attached_role_policies")
    return paginator.paginate(RoleName=role_name).build_full_result()["AttachedPolicies"]


@AWSRetry.jittered_backoff()
def list_iam_instance_profiles_for_role_with_backoff(client, role_name):
    paginator = client.get_paginator("list_instance_profiles_for_role")
    return paginator.paginate(RoleName=role_name).build_full_result()["InstanceProfiles"]


def describe_iam_role(module, client, role):
    name = role["RoleName"]
    try:
        role["InlinePolicies"] = list_iam_role_policies_with_backoff(client, name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Couldn't get inline policies for role {name}")
    try:
        role["ManagedPolicies"] = list_iam_attached_role_policies_with_backoff(client, name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Couldn't get managed  policies for role {name}")
    try:
        role["InstanceProfiles"] = list_iam_instance_profiles_for_role_with_backoff(client, name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Couldn't get instance profiles for role {name}")
    try:
        role["tags"] = boto3_tag_list_to_ansible_dict(role["Tags"])
        del role["Tags"]
    except KeyError:
        role["tags"] = {}
    return role


def describe_iam_roles(module, client):
    name = module.params["name"]
    path_prefix = module.params["path_prefix"]
    if name:
        try:
            roles = [client.get_role(RoleName=name, aws_retry=True)["Role"]]
        except is_boto3_error_code("NoSuchEntity"):
            return []
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg=f"Couldn't get IAM role {name}")
    else:
        params = dict()
        if path_prefix:
            if not path_prefix.startswith("/"):
                path_prefix = "/" + path_prefix
            if not path_prefix.endswith("/"):
                path_prefix = path_prefix + "/"
            params["PathPrefix"] = path_prefix
        try:
            roles = list_iam_roles_with_backoff(client, **params)["Roles"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't list IAM roles")
    return [normalize_role(describe_iam_role(module, client, role)) for role in roles]


def normalize_profile(profile):
    new_profile = camel_dict_to_snake_dict(profile)
    if profile.get("Roles"):
        profile["roles"] = [normalize_role(role) for role in profile.get("Roles")]
    return new_profile


def normalize_role(role):
    new_role = camel_dict_to_snake_dict(role, ignore_list=["tags"])
    new_role["assume_role_policy_document_raw"] = role.get("AssumeRolePolicyDocument")
    if role.get("InstanceProfiles"):
        role["instance_profiles"] = [normalize_profile(profile) for profile in role.get("InstanceProfiles")]
    return new_role


def main():
    """
    Module action handler
    """
    argument_spec = dict(
        name=dict(aliases=["role_name"]),
        path_prefix=dict(),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["name", "path_prefix"]],
    )

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    module.deprecate(
        "In a release after 2023-12-01 the contents of assume_role_policy_document "
        "will no longer be converted from CamelCase to snake_case.  The "
        ".assume_role_policy_document_raw return value already returns the "
        "policy document in this future format.",
        date="2023-12-01",
        collection_name="community.aws",
    )

    module.exit_json(changed=False, iam_roles=describe_iam_roles(module, client))


if __name__ == "__main__":
    main()

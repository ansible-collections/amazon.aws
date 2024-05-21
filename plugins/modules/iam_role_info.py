#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_role_info
version_added: 1.0.0
version_added_collection: community.aws
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
            - C(path) and C(prefix) were added as aliases in release 7.2.0.
            - In a release after 2026-05-01 paths must begin and end with C(/).
              Prior to this paths will automatically have C(/) added as appropriate
              to ensure that they start and end with C(/).
        type: str
        aliases: ["path", "prefix"]
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: find all existing IAM roles
  amazon.aws.iam_role_info:
  register: result

- name: describe a single role
  amazon.aws.iam_role_info:
    name: MyIAMRole

- name: describe all roles matching a path prefix
  amazon.aws.iam_role_info:
    path_prefix: /application/path/
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
          Note: the case of keys in this dictionary are no longer converted from CamelCase to
          snake_case.  This behaviour changed in release 8.0.0.
      returned: always
      type: dict
    assume_role_policy_document_raw:
      description:
        - |
          Note: this return value has been deprecated and will be removed in a release after
          2026-05-01.  assume_role_policy_document and assume_role_policy_document_raw now use
          the same format.
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


from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_role
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_instance_profiles
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_role_attached_policies
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_role_policies
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_roles
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_role
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def expand_iam_role(client, role):
    name = role["RoleName"]
    role["InlinePolicies"] = list_iam_role_policies(client, name)
    role["ManagedPolicies"] = list_iam_role_attached_policies(client, name)
    role["InstanceProfiles"] = list_iam_instance_profiles(client, role=name)
    return role


def describe_iam_roles(client, name, path_prefix):
    if name:
        roles = [get_iam_role(client, name)]
    else:
        roles = list_iam_roles(client, path=path_prefix)
    roles = [r for r in roles if r is not None]
    return [normalize_iam_role(expand_iam_role(client, role), _v7_compat=True) for role in roles]


def main():
    """
    Module action handler
    """
    argument_spec = dict(
        name=dict(aliases=["role_name"]),
        path_prefix=dict(aliases=["path", "prefix"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["name", "path_prefix"]],
    )

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())
    name = module.params["name"]
    path_prefix = module.params["path_prefix"]

    module.deprecate(
        "In a release after 2026-05-01 iam_role.assume_role_policy_document_raw "
        "will no longer be returned.  Since release 8.0.0 assume_role_policy_document "
        "has been returned with the same format as iam_role.assume_role_policy_document_raw",
        date="2026-05-01",
        collection_name="amazon.aws",
    )

    # Once the deprecation is over we can merge this into a single call to validate_iam_identifiers
    if name:
        validation_error = validate_iam_identifiers("role", name=name)
        if validation_error:
            module.fail_json(msg=validation_error)
    if path_prefix:
        validation_error = validate_iam_identifiers("role", path=path_prefix)
        if validation_error:
            _prefix = "/" if not path_prefix.startswith("/") else ""
            _suffix = "/" if not path_prefix.endswith("/") else ""
            path_prefix = f"{_prefix}{path_prefix}{_suffix}"
            module.deprecate(
                "In a release after 2026-05-01 paths must begin and end with /.  "
                f"path_prefix has been modified to '{path_prefix}'",
                date="2026-05-01",
                collection_name="amazon.aws",
            )

    try:
        module.exit_json(changed=False, iam_roles=describe_iam_roles(client, name, path_prefix))
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_role
version_added: 1.0.0
version_added_collection: community.aws
short_description: Manage AWS IAM roles
description:
  - Manage AWS IAM roles.
author:
  - "Rob White (@wimnat)"
options:
  path:
    description:
      - The path of the role.
      - For more information about IAM paths, see the AWS IAM identifiers documentation
        U(https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
      - Updating the path on an existing role is not currently supported and will result in a
        warning.
      - O(path_prefix) and O(prefix) were added as aliases in release 7.2.0.
    type: str
    aliases: ["prefix", "path_prefix"]
  name:
    description:
      - The name of the role.
      - >-
        Note: Role names are unique within an account.  Paths (O(path)) do B(not) affect
        the uniqueness requirements of O(name).  For example it is not permitted to have both
        C(/Path1/MyRole) and C(/Path2/MyRole) in the same account.
      - O(role_name) was added as an alias in release 7.2.0.
    required: true
    type: str
    aliases: ["role_name"]
  description:
    description:
      - Provides a description of the role.
    type: str
  boundary:
    description:
      - The ARN of an IAM managed policy to use to restrict the permissions this role can pass on to IAM roles/users that it creates.
      - Boundaries cannot be set on Instance Profiles, as such if this option is specified then O(create_instance_profile) must be V(false).
      - This is intended for roles/users that have permissions to create new IAM objects.
      - For more information on boundaries, see U(https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html).
    aliases: [boundary_policy_arn]
    type: str
  assume_role_policy_document:
    description:
      - The trust relationship policy document that grants an entity permission to assume the role.
      - This parameter is required when O(state=present).
    type: json
  managed_policies:
    description:
      - A list of managed policy ARNs, or friendly names.
      - To remove all policies set O(purge_policies=true) and O(managed_policies=[]).
      - To embed an inline policy, use M(amazon.aws.iam_policy).
    aliases: ['managed_policy']
    type: list
    elements: str
  max_session_duration:
    description:
      - The maximum duration (in seconds) of a session when assuming the role.
      - Valid values are between 1 and 12 hours (3600 and 43200 seconds).
    type: int
  purge_policies:
    description:
      - When O(purge_policies=true) any managed policies not listed in O(managed_policies) will be detatched.
    type: bool
    aliases: ['purge_policy', 'purge_managed_policies']
    default: true
  state:
    description:
      - Create or remove the IAM role.
    default: present
    choices: [ present, absent ]
    type: str
  create_instance_profile:
    description:
      - If no IAM instance profile with the same O(name) exists, setting O(create_instance_profile=True)
        will create an IAM instance profile along with the role.
      - This option has been deprecated and will be removed in a release after 2026-05-01.  The
        M(amazon.aws.iam_instance_profile) module can be used to manage instance profiles.
      - Defaults to V(True)
    type: bool
  delete_instance_profile:
    description:
      - When O(delete_instance_profile=true) and O(state=absent) deleting a role will also delete an
        instance profile with the same O(name) as the role, but only if the instance profile is
        associated with the role.
      - Only applies when O(state=absent).
      - This option has been deprecated and will be removed in a release after 2026-05-01.  The
        M(amazon.aws.iam_instance_profile) module can be used to manage instance profiles.
      - Defaults to V(False)
    type: bool
  wait_timeout:
    description:
      - How long (in seconds) to wait for creation / update to complete.
    default: 120
    type: int
  wait:
    description:
      - When O(wait=True) the module will wait for up to O(wait_timeout) seconds
        for IAM role creation before returning.
    default: True
    type: bool
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a role with description and tags
  amazon.aws.iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    description: This is My New Role
    tags:
      env: dev

- name: "Create a role and attach a managed policy called 'PowerUserAccess'"
  amazon.aws.iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    managed_policies:
      - arn:aws:iam::aws:policy/PowerUserAccess

- name: Keep the role created above but remove all managed policies
  amazon.aws.iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    managed_policies: []

- name: Delete the role
  amazon.aws.iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file', 'policy.json') }}"
    state: absent
"""

RETURN = r"""
iam_role:
    description: Dictionary containing the IAM Role data.
    returned: success
    type: complex
    contains:
        path:
            description: The path to the role.
            type: str
            returned: always
            sample: /
        role_name:
            description: The friendly name that identifies the role.
            type: str
            returned: always
            sample: myrole
        role_id:
            description: The stable and unique string identifying the role.
            type: str
            returned: always
            sample: ABCDEFF4EZ4ABCDEFV4ZC
        arn:
            description: The Amazon Resource Name (ARN) specifying the role.
            type: str
            returned: always
            sample: "arn:aws:iam::1234567890:role/mynewrole"
        create_date:
            description: The date and time, in ISO 8601 date-time format, when the role was created.
            type: str
            returned: always
            sample: "2016-08-14T04:36:28+00:00"
        assume_role_policy_document:
            description:
              - The policy that grants an entity permission to assume the role.
              - |
                Note: the case of keys in this dictionary are no longer converted from CamelCase to
                snake_case. This behaviour changed in release 8.0.0.
            type: dict
            returned: always
            sample: {
                        'statement': [
                            {
                                'action': 'sts:AssumeRole',
                                'effect': 'Allow',
                                'principal': {
                                    'service': 'ec2.amazonaws.com'
                                },
                                'sid': ''
                            }
                        ],
                        'version': '2012-10-17'
                    }
        assume_role_policy_document_raw:
            description:
              - |
                Note: this return value has been deprecated and will be removed in a release after
                2026-05-01. RV(iam_role.assume_role_policy_document) and RV(iam_role.assume_role_policy_document_raw)
                now use the same format.
            type: dict
            returned: always
            sample: {
                        'statement': [
                            {
                                'action': 'sts:AssumeRole',
                                'effect': 'Allow',
                                'principal': {
                                    'service': 'ec2.amazonaws.com'
                                },
                                'sid': ''
                            }
                        ],
                        'version': '2012-10-17'
                    }
            version_added: 5.3.0
        attached_policies:
            description: A list of dicts containing the name and ARN of the managed IAM policies attached to the role.
            type: list
            elements: dict
            returned: always
            sample: [
                {
                    'policy_arn': 'arn:aws:iam::aws:policy/PowerUserAccess',
                    'policy_name': 'PowerUserAccess'
                }
            ]
            contains:
                policy_arn:
                    description: The Amazon Resource Name (ARN) specifying the managed policy.
                    type: str
                    sample: "arn:aws:iam::123456789012:policy/test_policy"
                policy_name:
                    description: The friendly name that identifies the policy.
                    type: str
                    sample: test_policy
        description:
            description: A description of the role.
            type: str
            returned: always
            sample: "This is My New Role"
        max_session_duration:
            description: The maximum duration (in seconds) of a session when assuming the role.
            type: int
            returned: always
            sample: 3600
        role_last_used:
            description: Contains information about the last time that an IAM role was used.
            type: dict
            returned: always
            sample: {
                        "last_used_date": "2023-11-22T21:54:29+00:00",
                        "region": "us-east-2"
                    }
            contains:
                last_used_date:
                    description: The date and time, in  ISO 8601 date-time format that the role was last used.
                    type: str
                    returned: always
                region:
                    description: The name of the Amazon Web Services Region in which the role was last used.
                    type: str
                    returned: always
        tags:
            description: role tags
            type: dict
            returned: always
            sample: '{"Env": "Prod"}'
"""

import json

from ansible_collections.amazon.aws.plugins.module_utils.arn import validate_aws_arn
from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import IAMErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.iam import add_role_to_iam_instance_profile
from ansible_collections.amazon.aws.plugins.module_utils.iam import convert_managed_policy_names_to_arns
from ansible_collections.amazon.aws.plugins.module_utils.iam import create_iam_instance_profile
from ansible_collections.amazon.aws.plugins.module_utils.iam import delete_iam_instance_profile
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_role
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_instance_profiles
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_role_attached_policies
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_role
from ansible_collections.amazon.aws.plugins.module_utils.iam import remove_role_from_iam_instance_profile
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


class AnsibleIAMAlreadyExistsError(AnsibleIAMError):
    pass


@IAMErrorHandler.common_error_handler("wait for role creation")
def wait_iam_exists(client, check_mode, role_name, wait, wait_timeout):
    if check_mode or wait:
        return

    delay = min(wait_timeout, 5)
    max_attempts = wait_timeout // delay

    waiter = client.get_waiter("role_exists")
    waiter.wait(
        WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
        RoleName=role_name,
    )


def attach_policies(client, check_mode, policies_to_attach, role_name):
    if not policies_to_attach:
        return False
    if check_mode:
        return True

    for policy_arn in policies_to_attach:
        IAMErrorHandler.common_error_handler(f"attach policy {policy_arn} to role")(client.attach_role_policy)(
            RoleName=role_name, PolicyArn=policy_arn, aws_retry=True
        )
    return True


def remove_policies(client, check_mode, policies_to_remove, role_name):
    if not policies_to_remove:
        return False
    if check_mode:
        return True

    for policy in policies_to_remove:
        IAMErrorHandler.deletion_error_handler(f"detach policy {policy} from role")(client.detach_role_policy)(
            RoleName=role_name, PolicyArn=policy, aws_retry=True
        )
    return True


def remove_inline_policies(client, role_name):
    current_inline_policies = get_inline_policy_list(client, role_name)
    for policy in current_inline_policies:
        IAMErrorHandler.deletion_error_handler(f"delete policy {policy} embedded in role")(client.delete_role_policy)(
            RoleName=role_name, PolicyName=policy, aws_retry=True
        )


def generate_create_params(module):
    params = dict()
    params["Path"] = module.params.get("path") or "/"
    params["RoleName"] = module.params.get("name")
    params["AssumeRolePolicyDocument"] = module.params.get("assume_role_policy_document")
    if module.params.get("description") is not None:
        params["Description"] = module.params.get("description")
    if module.params.get("max_session_duration") is not None:
        params["MaxSessionDuration"] = module.params.get("max_session_duration")
    if module.params.get("boundary") is not None:
        params["PermissionsBoundary"] = module.params.get("boundary")
    if module.params.get("tags") is not None:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params.get("tags"))

    return params


@IAMErrorHandler.common_error_handler("create role")
def create_basic_role(module, client):
    """
    Perform the Role creation.
    Assumes tests for the role existing have already been performed.
    """
    if module.check_mode:
        module.exit_json(changed=True)

    params = generate_create_params(module)
    role = client.create_role(aws_retry=True, **params)
    # 'Description' is documented as a key of the role returned by create_role
    # but appears to be an AWS bug (the value is not returned using the AWS CLI either).
    # Get the role after creating it.
    # nb. doesn't use get_iam_role because we need to retry if the Role isn't there
    role = _get_role_with_backoff(client, params["RoleName"])

    return role


@IAMErrorHandler.common_error_handler("update assume role policy for role")
def update_role_assumed_policy(client, check_mode, role_name, target_assumed_policy, current_assumed_policy):
    # Check Assumed Policy document
    if target_assumed_policy is None or not compare_policies(current_assumed_policy, json.loads(target_assumed_policy)):
        return False
    if check_mode:
        return True

    client.update_assume_role_policy(RoleName=role_name, PolicyDocument=target_assumed_policy, aws_retry=True)
    return True


@IAMErrorHandler.common_error_handler("update description for role")
def update_role_description(client, check_mode, role_name, target_description, current_description):
    # Check Description update
    if target_description is None or current_description == target_description:
        return False
    if check_mode:
        return True

    client.update_role(RoleName=role_name, Description=target_description, aws_retry=True)
    return True


@IAMErrorHandler.common_error_handler("update maximum session duration for role")
def update_role_max_session_duration(client, check_mode, role_name, target_duration, current_duration):
    # Check MaxSessionDuration update
    if target_duration is None or current_duration == target_duration:
        return False
    if check_mode:
        return True

    client.update_role(RoleName=role_name, MaxSessionDuration=target_duration, aws_retry=True)
    return True


@IAMErrorHandler.common_error_handler("update permission boundary for role")
def _put_role_permissions_boundary(client, **params):
    client.put_role_permissions_boundary(aws_retry=True, **params)


@IAMErrorHandler.deletion_error_handler("remove permission boundary from role")
def _delete_role_permissions_boundary(client, **params):
    client.delete_role_permissions_boundary(**params)


def update_role_permissions_boundary(client, check_mode, role_name, permissions_boundary, current_permissions_boundary):
    # Check PermissionsBoundary
    if permissions_boundary is None or permissions_boundary == current_permissions_boundary:
        return False
    if check_mode:
        return True

    if permissions_boundary == "":
        _delete_role_permissions_boundary(client, RoleName=role_name)
    else:
        _put_role_permissions_boundary(client, RoleName=role_name, PermissionsBoundary=permissions_boundary)
    return True


def update_managed_policies(client, check_mode, role_name, managed_policies, purge_policies):
    # Check Managed Policies
    if managed_policies is None:
        return False

    # Get list of current attached managed policies
    current_attached_policies = list_iam_role_attached_policies(client, role_name)
    current_attached_policies_arn_list = [policy["PolicyArn"] for policy in current_attached_policies]

    if len(managed_policies) == 1 and managed_policies[0] is None:
        managed_policies = []

    policies_to_remove = set(current_attached_policies_arn_list) - set(managed_policies)
    policies_to_remove = policies_to_remove if purge_policies else []
    policies_to_attach = set(managed_policies) - set(current_attached_policies_arn_list)

    changed = False
    if purge_policies and policies_to_remove:
        if check_mode:
            return True
        else:
            changed |= remove_policies(client, check_mode, policies_to_remove, role_name)

    if policies_to_attach:
        if check_mode:
            return True
        else:
            changed |= attach_policies(client, check_mode, policies_to_attach, role_name)

    return changed


def update_basic_role(module, client, role_name, role):
    check_mode = module.check_mode
    assumed_policy = module.params.get("assume_role_policy_document")
    description = module.params.get("description")
    duration = module.params.get("max_session_duration")
    path = module.params.get("path")
    permissions_boundary = module.params.get("boundary")
    purge_tags = module.params.get("purge_tags")
    tags = module.params.get("tags")

    # current attributes
    current_assumed_policy = role.get("AssumeRolePolicyDocument")
    current_description = role.get("Description")
    current_duration = role.get("MaxSessionDuration")
    current_permissions_boundary = role.get("PermissionsBoundary", {}).get("PermissionsBoundaryArn", "")
    current_tags = role.get("Tags", [])

    # As of botocore 1.34.3, the APIs don't support updating the Name or Path
    if update_role_path(client, check_mode, role, path):
        module.warn(
            f"iam_role doesn't support updating the path: current path '{role.get('Path')}', requested path '{path}'"
        )

    changed = False

    # Update attributes
    changed |= update_role_tags(client, check_mode, role_name, tags, purge_tags, current_tags)
    changed |= update_role_assumed_policy(client, check_mode, role_name, assumed_policy, current_assumed_policy)
    changed |= update_role_description(client, check_mode, role_name, description, current_description)
    changed |= update_role_max_session_duration(client, check_mode, role_name, duration, current_duration)
    changed |= update_role_permissions_boundary(
        client, check_mode, role_name, permissions_boundary, current_permissions_boundary
    )

    return changed


def create_or_update_role(module, client, role_name, create_instance_profile):
    check_mode = module.check_mode
    wait = module.params.get("wait")
    wait_timeout = module.params.get("wait_timeout")
    path = module.params.get("path")
    purge_policies = module.params.get("purge_policies")
    managed_policies = module.params.get("managed_policies")
    if managed_policies:
        # Attempt to list the policies early so we don't leave things behind if we can't find them.
        managed_policies = convert_managed_policy_names_to_arns(client, managed_policies)

    changed = False

    # Get role
    role = get_iam_role(client, role_name)

    # If role is None, create it
    if role is None:
        role = create_basic_role(module, client)
        wait_iam_exists(client, check_mode, role_name, wait, wait_timeout)
        changed = True
    else:
        changed = update_basic_role(module, client, role_name, role)
        wait_iam_exists(client, check_mode, role_name, wait, wait_timeout)

    if create_instance_profile:
        try:
            changed |= create_instance_profiles(client, check_mode, role_name, path)
            wait_iam_exists(client, check_mode, role_name, wait, wait_timeout)
        except AnsibleIAMAlreadyExistsError:
            module.warn(f"profile {role_name} already exists and will not be updated")

    changed |= update_managed_policies(client, module.check_mode, role_name, managed_policies, purge_policies)
    wait_iam_exists(client, check_mode, role_name, wait, wait_timeout)

    # Get the role again
    role = get_iam_role(client, role_name)
    role["AttachedPolicies"] = list_iam_role_attached_policies(client, role_name)
    camel_role = normalize_iam_role(role, _v7_compat=True)

    module.exit_json(changed=changed, iam_role=camel_role)


def create_instance_profiles(client, check_mode, role_name, path):
    # Fetch existing Profiles
    role_profiles = list_iam_instance_profiles(client, role=role_name)
    # Profile already exists
    if any(p["InstanceProfileName"] == role_name for p in role_profiles):
        return False

    named_profile = list_iam_instance_profiles(client, name=role_name)
    if named_profile:
        raise AnsibleIAMAlreadyExistsError(f"profile {role_name} already exists")

    if check_mode:
        return True

    path = path or "/"
    # Make sure an instance profile is created
    create_iam_instance_profile(client, role_name, path, {})
    add_role_to_iam_instance_profile(client, role_name, role_name)

    return True


def remove_instance_profiles(client, check_mode, role_name, delete_instance_profile):
    """Removes the role from instance profiles and deletes the instance profile if
    delete_instance_profile is set
    """

    instance_profiles = list_iam_instance_profiles(client, role=role_name)
    if not instance_profiles:
        return False
    if check_mode:
        return True

    # Remove the role from the instance profile(s)
    for profile in instance_profiles:
        profile_name = profile["InstanceProfileName"]
        remove_role_from_iam_instance_profile(client, profile_name, role_name)
        if not delete_instance_profile:
            continue
        # Delete the instance profile if the role and profile names match
        if profile_name == role_name:
            delete_iam_instance_profile(client, profile_name)


@IAMErrorHandler.deletion_error_handler("delete role")
def destroy_role(client, check_mode, role_name, delete_profiles):
    role = get_iam_role(client, role_name)

    if role is None:
        return False

    if check_mode:
        return True

    # Before we try to delete the role we need to remove any
    # - attached instance profiles
    # - attached managed policies
    # - embedded inline policies
    remove_instance_profiles(client, check_mode, role_name, delete_profiles)
    update_managed_policies(client, check_mode, role_name, [], True)
    remove_inline_policies(client, role_name)

    client.delete_role(aws_retry=True, RoleName=role_name)
    return True


@IAMErrorHandler.common_error_handler("get role")
@AWSRetry.jittered_backoff(catch_extra_error_codes=["NoSuchEntity"])
def _get_role_with_backoff(client, name):
    client.get_role(RoleName=name)["Role"]


@IAMErrorHandler.list_error_handler("list attached inline policies for role")
def get_inline_policy_list(client, name):
    return client.list_role_policies(RoleName=name, aws_retry=True)["PolicyNames"]


def update_role_path(client, check_mode, role, path):
    if path is None:
        return False
    if path == role.get("Path"):
        return False
    if check_mode:
        return True

    # Not currently supported by the APIs
    pass
    return True


@IAMErrorHandler.common_error_handler("set tags for role")
def update_role_tags(client, check_mode, role_name, new_tags, purge_tags, existing_tags):
    if new_tags is None:
        return False
    existing_tags = boto3_tag_list_to_ansible_dict(existing_tags)

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)
    if not tags_to_remove and not tags_to_add:
        return False
    if check_mode:
        return True

    if tags_to_remove:
        client.untag_role(RoleName=role_name, TagKeys=tags_to_remove, aws_retry=True)
    if tags_to_add:
        client.tag_role(RoleName=role_name, Tags=ansible_dict_to_boto3_tag_list(tags_to_add), aws_retry=True)

    return True


def validate_params(module):
    if module.params.get("boundary"):
        # We need to handle both None and True
        if module.params.get("create_instance_profile") is not False:
            module.fail_json(msg="When using a boundary policy, `create_instance_profile` must be set to `false`.")
        if not validate_aws_arn(module.params.get("boundary"), service="iam"):
            module.fail_json(msg="Boundary policy must be an ARN")
    if module.params.get("max_session_duration"):
        max_session_duration = module.params.get("max_session_duration")
        if max_session_duration < 3600 or max_session_duration > 43200:
            module.fail_json(msg="max_session_duration must be between 1 and 12 hours (3600 and 43200 seconds)")

    identifier_problem = validate_iam_identifiers(
        "role", name=module.params.get("name"), path=module.params.get("path")
    )
    if identifier_problem:
        module.fail_json(msg=identifier_problem)


def main():
    argument_spec = dict(
        name=dict(type="str", aliases=["role_name"], required=True),
        path=dict(type="str", aliases=["path_prefix", "prefix"]),
        assume_role_policy_document=dict(type="json"),
        managed_policies=dict(type="list", aliases=["managed_policy"], elements="str"),
        max_session_duration=dict(type="int"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        description=dict(type="str"),
        boundary=dict(type="str", aliases=["boundary_policy_arn"]),
        create_instance_profile=dict(type="bool"),
        delete_instance_profile=dict(type="bool"),
        purge_policies=dict(default=True, type="bool", aliases=["purge_policy", "purge_managed_policies"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(default=120, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[("state", "present", ["assume_role_policy_document"])],
        supports_check_mode=True,
    )

    module.deprecate(
        "In a release after 2026-05-01 iam_role.assume_role_policy_document_raw "
        "will no longer be returned.  Since release 8.0.0 assume_role_policy_document "
        "has been returned with the same format as iam_role.assume_role_policy_document_raw",
        date="2026-05-01",
        collection_name="amazon.aws",
    )
    if module.params.get("create_instance_profile") is None:
        module.deprecate(
            "In a release after 2026-05-01 the 'create_instance_profile' option will be removed. "
            "The amazon.aws.iam_instance_profile module can be used to manage instance profiles instead.",
            date="2026-05-01",
            collection_name="amazon.aws",
        )
    if module.params.get("delete_instance_profile") is None:
        module.deprecate(
            "In a release after 2026-05-01 the 'delete_instance_profile' option will be removed. "
            "The amazon.aws.iam_instance_profile module can be used to manage and delete instance "
            "profiles instead.",
            date="2026-05-01",
            collection_name="amazon.aws",
        )

    validate_params(module)

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")
    role_name = module.params.get("name")

    create_profile = module.params.get("create_instance_profile")
    create_profile = True if create_profile is None else create_profile
    delete_profile = module.params.get("delete_instance_profile") or False

    try:
        if state == "present":
            create_or_update_role(module, client, role_name, create_profile)
        elif state == "absent":
            changed = destroy_role(client, module.check_mode, role_name, delete_profile)
            module.exit_json(changed=changed)
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

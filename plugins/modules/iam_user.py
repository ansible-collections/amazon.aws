#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_user
version_added: 5.0.0
short_description: Manage AWS IAM users
description:
  - A module to manage AWS IAM users.
  - The module does not manage groups that users belong to, groups memberships can be managed using M(amazon.aws.iam_group).
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - Josh Souza (@joshsouza)
options:
  name:
    description:
      - The name of the user.
      - >-
        Note: user names are unique within an account.  Paths (I(path)) do B(not) affect
        the uniqueness requirements of I(name).  For example it is not permitted to have both
        C(/Path1/MyUser) and C(/Path2/MyUser) in the same account.
      - C(user_name) was added as an alias in release 7.2.0.
    required: true
    type: str
    aliases: ['user_name']
  path:
    description:
      - The path for the user.
      - For more information about IAM paths, see the AWS IAM identifiers documentation
        U(https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    aliases: ['prefix', 'path_prefix']
    required: false
    type: str
    version_added: 7.2.0
  boundary:
    description:
      - The ARN of an IAM managed policy to apply as a boundary policy for this user.
      - Boundary policies can be used to restrict the permissions a user can excercise, but does not
        grant any policies in and of itself.
      - For more information on boundaries, see
        U(https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html).
      - Set to the empty string C("") to remove the boundary policy.
    aliases: ["boundary_policy_arn", "permissions_boundary"]
    required: false
    type: str
    version_added: 7.2.0
  password:
    description:
      - The password to apply to the user.
    required: false
    type: str
    version_added: 2.2.0
    version_added_collection: community.aws
  password_reset_required:
    description:
      - Defines if the user is required to set a new password when they log in.
      - Ignored unless a new password is set.
    required: false
    type: bool
    default: false
    version_added: 3.1.0
    version_added_collection: community.aws
  update_password:
    default: always
    choices: ['always', 'on_create']
    description:
      - When to update user passwords.
      - I(update_password=always) will ensure the password is set to I(password).
      - I(update_password=on_create) will only set the password for newly created users.
    type: str
    version_added: 2.2.0
    version_added_collection: community.aws
  remove_password:
    description:
      - Option to delete user login passwords.
      - This field is mutually exclusive to I(password).
    type: 'bool'
    version_added: 2.2.0
    version_added_collection: community.aws
  managed_policies:
    description:
      - A list of managed policy ARNs or friendly names to attach to the user.
      - To embed an inline policy, use M(community.aws.iam_policy).
    required: false
    type: list
    default: []
    elements: str
    aliases: ['managed_policy']
  state:
    description:
      - Create or remove the IAM user.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  purge_policies:
    description:
      - When I(purge_policies=true) any managed policies not listed in I(managed_policies) will be detached.
    required: false
    default: false
    type: bool
    aliases: ['purge_policy', 'purge_managed_policies']
  wait:
    description:
      - When I(wait=True) the module will wait for up to I(wait_timeout) seconds
        for IAM user creation before returning.
    default: True
    type: bool
    version_added: 2.2.0
    version_added_collection: community.aws
  wait_timeout:
    description:
      - How long (in seconds) to wait for creation / updates to complete.
    default: 120
    type: int
    version_added: 2.2.0
    version_added_collection: community.aws
notes:
  - Support for I(tags) and I(purge_tags) was added in release 2.1.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Note: This module does not allow management of groups that users belong to.
#       Groups should manage their membership directly using amazon.aws.iam_group,
#       as users belong to them.

- name: Create a user
  amazon.aws.iam_user:
    name: testuser1
    state: present

- name: Create a user with a password
  amazon.aws.iam_user:
    name: testuser1
    password: SomeSecurePassword
    state: present

- name: Create a user and attach a managed policy using its ARN
  amazon.aws.iam_user:
    name: testuser1
    managed_policies:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    state: present

- name: Remove all managed policies from an existing user with an empty list
  amazon.aws.iam_user:
    name: testuser1
    state: present
    purge_policies: true

- name: Create user with tags
  amazon.aws.iam_user:
    name: testuser1
    state: present
    tags:
      Env: Prod

- name: Delete the user
  amazon.aws.iam_user:
    name: testuser1
    state: absent
"""

RETURN = r"""
user:
    description: dictionary containing all the user information
    returned: success
    type: complex
    contains:
        arn:
            description: the Amazon Resource Name (ARN) specifying the user
            type: str
            sample: "arn:aws:iam::123456789012:user/testuser1"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the user was created
            type: str
            sample: "2017-02-08T04:36:28+00:00"
        user_id:
            description: the stable and unique string identifying the user
            type: str
            sample: "AGPA12345EXAMPLE54321"
        user_name:
            description: the friendly name that identifies the user
            type: str
            sample: "testuser1"
        path:
            description: the path to the user
            type: str
            sample: "/"
        tags:
            description: user tags
            type: dict
            returned: always
            sample: {"Env": "Prod"}
        attached_policies:
            version_added: 7.2.0
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

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import IAMErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.iam import convert_managed_policy_names_to_arns
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_user
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_user
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


@IAMErrorHandler.common_error_handler("wait for IAM user creation")
def _wait_user_exists(connection, **params):
    waiter = connection.get_waiter("user_exists")
    waiter.wait(**params)


def wait_iam_exists(connection, module):
    if not module.params.get("wait"):
        return

    user_name = module.params.get("name")
    wait_timeout = module.params.get("wait_timeout")

    delay = min(wait_timeout, 5)
    max_attempts = wait_timeout // delay
    waiter_config = {"Delay": delay, "MaxAttempts": max_attempts}

    _wait_user_exists(connection, WaiterConfig=waiter_config, UserName=user_name)


@IAMErrorHandler.common_error_handler("create user")
def create_user(connection, module, user_name, path, boundary, tags):
    params = {"UserName": user_name}
    if path:
        params["Path"] = path
    if boundary:
        params["PermissionsBoundary"] = boundary
    if tags:
        params["Tags"] = ansible_dict_to_boto3_tag_list(tags)

    if module.check_mode:
        module.exit_json(changed=True, create_params=params)

    user = connection.create_user(aws_retry=True, **params)["User"]

    return normalize_iam_user(user)


@IAMErrorHandler.common_error_handler("create user login profile")
def _create_login_profile(connection, **params):
    return connection.create_login_profile(aws_retry=True, **params)


# Uses the list error handler because we "update" as a quick test for existence
# when our next step would be update or create.
@IAMErrorHandler.list_error_handler("update user login profile")
def _update_login_profile(connection, **params):
    return connection.update_login_profile(aws_retry=True, **params)


def _create_or_update_login_profile(connection, name, password, reset):
    # Apply new password / update password for the user
    user_params = {
        "UserName": name,
        "Password": password,
        "PasswordResetRequired": reset,
    }

    retval = _update_login_profile(connection, **user_params)
    if retval:
        return retval
    return _create_login_profile(connection, **user_params)


def ensure_login_profile(connection, check_mode, user_name, password, update, reset, new_user):
    if password is None:
        return False, None
    if update == "on_create" and not new_user:
        return False, None

    if check_mode:
        return True, None

    return True, _create_or_update_login_profile(connection, user_name, password, reset)


@IAMErrorHandler.list_error_handler("get login profile")
def _get_login_profile(connection, name):
    return connection.get_login_profile(aws_retry=True, UserName=name).get("LoginProfile")


@IAMErrorHandler.deletion_error_handler("delete login profile")
def _delete_login_profile(connection, name):
    connection.delete_login_profile(aws_retry=True, UserName=name)


def remove_login_profile(connection, check_mode, user_name, remove_password, new_user):
    if new_user:
        return False
    if not remove_password:
        return False

    # In theory we could skip this check outside check_mode
    login_profile = _get_login_profile(connection, user_name)
    if not login_profile:
        return False

    if check_mode:
        return True

    _delete_login_profile(connection, user_name)
    return True


@IAMErrorHandler.list_error_handler("get policies for user")
def _list_attached_policies(connection, user_name):
    return connection.list_attached_user_policies(aws_retry=True, UserName=user_name)["AttachedPolicies"]


@IAMErrorHandler.common_error_handler("attach policy to user")
def attach_policies(connection, check_mode, user_name, policies):
    if not policies:
        return False
    if check_mode:
        return True
    for policy_arn in policies:
        connection.attach_user_policy(UserName=user_name, PolicyArn=policy_arn)


@IAMErrorHandler.common_error_handler("detach policy from user")
def detach_policies(connection, check_mode, user_name, policies):
    if not policies:
        return False
    if check_mode:
        return True
    for policy_arn in policies:
        connection.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)


def ensure_managed_policies(connection, check_mode, user_name, managed_policies, purge_policies):
    if managed_policies is None:
        return False

    managed_policies = convert_managed_policy_names_to_arns(connection, managed_policies)

    # Manage managed policies
    attached_policies_desc = _list_attached_policies(connection, user_name)
    current_attached_policies = [policy["PolicyArn"] for policy in attached_policies_desc]

    policies_to_add = list(set(managed_policies) - set(current_attached_policies))
    policies_to_remove = []
    if purge_policies:
        policies_to_remove = list(set(current_attached_policies) - set(managed_policies))

    if not policies_to_add and not policies_to_remove:
        return False

    if check_mode:
        return True

    detach_policies(connection, check_mode, user_name, policies_to_remove)
    attach_policies(connection, check_mode, user_name, policies_to_add)

    return True


@IAMErrorHandler.common_error_handler("set tags for user")
def ensure_user_tags(connection, check_mode, user, user_name, new_tags, purge_tags):
    if new_tags is None:
        return False

    existing_tags = user["tags"]

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)

    if not tags_to_remove and not tags_to_add:
        return False

    if check_mode:
        return True

    if tags_to_remove:
        connection.untag_user(UserName=user_name, TagKeys=tags_to_remove)
    if tags_to_add:
        connection.tag_user(UserName=user_name, Tags=ansible_dict_to_boto3_tag_list(tags_to_add))

    return True


@IAMErrorHandler.deletion_error_handler("remove permissions boundary for user")
def _delete_user_permissions_boundary(connection, check_mode, user_name):
    if check_mode:
        return True
    connection.delete_user_permissions_boundary(aws_retry=True, UserName=user_name)


@IAMErrorHandler.common_error_handler("set permissions boundary for user")
def _put_user_permissions_boundary(connection, check_mode, user_name, boundary):
    if check_mode:
        return True
    connection.put_user_permissions_boundary(aws_retry=True, UserName=user_name, PermissionsBoundary=boundary)


def ensure_permissions_boundary(connection, check_mode, user, user_name, boundary):
    if boundary is None:
        return False

    current_boundary = user.get("permissions_boundary", "") if user else None

    if current_boundary:
        current_boundary = current_boundary.get("permissions_boundary_arn")

    if boundary == current_boundary:
        return False

    if check_mode:
        return True

    if boundary == "":
        _delete_user_permissions_boundary(connection, check_mode, user_name)
    else:
        _put_user_permissions_boundary(connection, check_mode, user_name, boundary)

    return True


@IAMErrorHandler.common_error_handler("set path for user")
def ensure_path(connection, check_mode, user, user_name, path):
    if path is None:
        return False

    current_path = user.get("path", "") if user else None

    if path == current_path:
        return False

    if check_mode:
        return True

    connection.update_user(aws_retry=True, UserName=user_name, NewPath=path)

    return True


def create_or_update_user(connection, module):
    user_name = module.params.get("name")

    changed = False
    new_user = False
    user = get_iam_user(connection, user_name)

    boundary = module.params.get("boundary")
    if boundary:
        boundary = convert_managed_policy_names_to_arns(connection, [module.params.get("boundary")])[0]

    if user is None:
        user = create_user(
            connection,
            module,
            user_name,
            module.params.get("path"),
            boundary,
            module.params.get("tags"),
        )
        changed = True
        # Wait for user to be fully available before continuing
        wait_iam_exists(connection, module)
        new_user = True

    profile_changed, login_profile = ensure_login_profile(
        connection,
        module.check_mode,
        user_name,
        module.params.get("password"),
        module.params.get("update_password"),
        module.params.get("password_reset_required"),
        new_user,
    )
    changed |= profile_changed

    changed |= remove_login_profile(
        connection,
        module.check_mode,
        user_name,
        module.params.get("remove_password"),
        new_user,
    )

    changed |= ensure_permissions_boundary(
        connection,
        module.check_mode,
        user,
        user_name,
        boundary,
    )

    changed |= ensure_path(
        connection,
        module.check_mode,
        user,
        user_name,
        module.params.get("path"),
    )

    changed |= ensure_managed_policies(
        connection,
        module.check_mode,
        user_name,
        module.params.get("managed_policies"),
        module.params.get("purge_policies"),
    )

    changed |= ensure_user_tags(
        connection,
        module.check_mode,
        user,
        user_name,
        module.params.get("tags"),
        module.params.get("purge_tags"),
    )

    if module.check_mode:
        module.exit_json(changed=changed)

    # Get the user again
    user = get_iam_user(connection, user_name)

    if changed and login_profile:
        # `LoginProfile` is only returned on `create_login_profile` method
        user["password_reset_required"] = login_profile.get("LoginProfile", {}).get("PasswordResetRequired", False)

    try:
        # (camel_dict_to_snake_dict doesn't handle lists, so do this as a merge of two dictionaries)
        policies = {"attached_policies": _list_attached_policies(connection, user_name)}
        user.update(camel_dict_to_snake_dict(policies))
    except AnsibleIAMError as e:
        module.warn(
            f"Failed to list attached policies - {str(e.exception)}",
        )
        pass

    module.exit_json(changed=changed, iam_user={"user": user}, user=user)


@IAMErrorHandler.deletion_error_handler("delete access key")
def delete_access_key(connection, check_mode, user_name, key_id):
    if check_mode:
        return True
    connection.delete_access_key(aws_retry=True, UserName=user_name, AccessKeyId=key_id)
    return True


@IAMErrorHandler.list_error_handler("list access keys")
def delete_access_keys(connection, check_mode, user_name):
    access_keys = connection.list_access_keys(aws_retry=True, UserName=user_name)["AccessKeyMetadata"]
    if not access_keys:
        return False
    for access_key in access_keys:
        delete_access_key(connection, check_mode, user_name, access_key["AccessKeyId"])
    return True


@IAMErrorHandler.deletion_error_handler("delete SSH key")
def delete_ssh_key(connection, check_mode, user_name, key_id):
    if check_mode:
        return True
    connection.delete_ssh_public_key(aws_retry=True, UserName=user_name, SSHPublicKeyId=key_id)
    return True


@IAMErrorHandler.list_error_handler("list SSH keys")
def delete_ssh_public_keys(connection, check_mode, user_name):
    public_keys = connection.list_ssh_public_keys(aws_retry=True, UserName=user_name)["SSHPublicKeys"]
    if not public_keys:
        return False
    for public_key in public_keys:
        delete_ssh_key(connection, check_mode, user_name, public_key["SSHPublicKeyId"])
    return True


@IAMErrorHandler.deletion_error_handler("delete service credential")
def delete_service_credential(connection, check_mode, user_name, cred_id):
    if check_mode:
        return True
    connection.delete_ssh_public_key(aws_retry=True, UserName=user_name, SSHPublicKeyId=cred_id)
    return True


@IAMErrorHandler.list_error_handler("list service credentials")
def delete_service_credentials(connection, check_mode, user_name):
    credentials = connection.list_service_specific_credentials(aws_retry=True, UserName=user_name)[
        "ServiceSpecificCredentials"
    ]
    if not credentials:
        return False
    for credential in credentials:
        delete_service_credential(connection, check_mode, user_name, credential["ServiceSpecificCredentialId"])
    return True


@IAMErrorHandler.deletion_error_handler("delete signing certificate")
def delete_signing_certificate(connection, check_mode, user_name, cert_id):
    if check_mode:
        return True
    connection.delete_signing_certificate(aws_retry=True, UserName=user_name, CertificateId=cert_id)
    return True


@IAMErrorHandler.list_error_handler("list signing certificates")
def delete_signing_certificates(connection, check_mode, user_name):
    certificates = connection.list_signing_certificates(aws_retry=True, UserName=user_name)["Certificates"]
    if not certificates:
        return False
    for certificate in certificates:
        delete_signing_certificate(connection, check_mode, user_name, certificate["CertificateId"])
    return True


@IAMErrorHandler.deletion_error_handler("delete MFA device")
def delete_mfa_device(connection, check_mode, user_name, device_id):
    if check_mode:
        return True
    connection.deactivate_mfa_device(aws_retry=True, UserName=user_name, SerialNumber=device_id)
    return True


@IAMErrorHandler.list_error_handler("list MFA devices")
def delete_mfa_devices(connection, check_mode, user_name):
    devices = connection.list_mfa_devices(aws_retry=True, UserName=user_name)["MFADevices"]
    if not devices:
        return False
    for device in devices:
        delete_mfa_device(connection, check_mode, user_name, device["SerialNumber"])
    return True


def detach_all_policies(connection, check_mode, user_name):
    # Remove any attached policies
    attached_policies_desc = _list_attached_policies(connection, user_name)
    current_attached_policies = [policy["PolicyArn"] for policy in attached_policies_desc]
    detach_policies(connection, check_mode, user_name, current_attached_policies)


@IAMErrorHandler.deletion_error_handler("delete inline policy")
def delete_inline_policy(connection, check_mode, user_name, policy):
    if check_mode:
        return True
    connection.delete_user_policy(aws_retry=True, UserName=user_name, PolicyName=policy)
    return True


@IAMErrorHandler.list_error_handler("list inline policies")
def delete_inline_policies(connection, check_mode, user_name):
    inline_policies = connection.list_user_policies(aws_retry=True, UserName=user_name)["PolicyNames"]
    if not inline_policies:
        return False
    for policy_name in inline_policies:
        delete_inline_policy(connection, check_mode, user_name, policy_name)
    return True


@IAMErrorHandler.deletion_error_handler("remove user from group")
def remove_from_group(connection, check_mode, user_name, group_name):
    if check_mode:
        return True
    connection.remove_user_from_group(aws_retry=True, UserName=user_name, GroupName=group_name)
    return True


@IAMErrorHandler.list_error_handler("list groups containing user")
def remove_from_all_groups(connection, check_mode, user_name):
    user_groups = connection.list_groups_for_user(aws_retry=True, UserName=user_name)["Groups"]
    if not user_groups:
        return False
    for group in user_groups:
        remove_from_group(connection, check_mode, user_name, group["GroupName"])
    return True


@IAMErrorHandler.deletion_error_handler("delete user")
def delete_user(connection, check_mode, user_name):
    if check_mode:
        return True
    connection.delete_user(aws_retry=True, UserName=user_name)
    return True


def destroy_user(connection, module):
    user_name = module.params.get("name")

    user = get_iam_user(connection, user_name)
    # User is not present
    if not user:
        module.exit_json(changed=False)

    # Check mode means we would remove this user
    if module.check_mode:
        module.exit_json(changed=True)

    # Prior to removing the user we need to remove all of the related resources, or deletion will
    # fail.
    # Because policies (direct and indrect) can contain Deny rules, order is important here in case
    # we fail during deletion: lock out the user first *then* start removing policies...
    # - Prevent the user from creating new sessions
    #   - Login profile
    #   - Access keys
    #   - SSH keys
    #   - Service Credentials
    #   - Certificates
    #   - MFA Token (last so we don't end up in a state where it's possible still use password/keys)
    # - Remove policies and group membership
    #   - Managed policies
    #   - Inline policies
    #   - Group membership

    remove_login_profile(connection, module.check_mode, user_name, True, False)
    delete_access_keys(connection, module.check_mode, user_name)
    delete_ssh_public_keys(connection, module.check_mode, user_name)
    delete_service_credentials(connection, module.check_mode, user_name)
    delete_signing_certificates(connection, module.check_mode, user_name)
    delete_mfa_devices(connection, module.check_mode, user_name)
    detach_all_policies(connection, module.check_mode, user_name)
    delete_inline_policies(connection, module.check_mode, user_name)
    remove_from_all_groups(connection, module.check_mode, user_name)
    changed = delete_user(connection, module.check_mode, user_name)
    module.exit_json(changed=changed)


def main():
    argument_spec = dict(
        name=dict(required=True, type="str", aliases=["user_name"]),
        path=dict(type="str", aliases=["prefix", "path_prefix"]),
        boundary=dict(type="str", aliases=["boundary_policy_arn", "permissions_boundary"]),
        password=dict(type="str", no_log=True),
        password_reset_required=dict(type="bool", default=False, no_log=False),
        update_password=dict(default="always", choices=["always", "on_create"], no_log=False),
        remove_password=dict(type="bool", no_log=False),
        managed_policies=dict(default=[], type="list", aliases=["managed_policy"], elements="str"),
        state=dict(choices=["present", "absent"], required=True),
        purge_policies=dict(default=False, type="bool", aliases=["purge_policy", "purge_managed_policies"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(default=120, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["password", "remove_password"]],
    )

    module.deprecate(
        "The 'iam_user' return key is deprecated and will be replaced by 'user'. Both values are returned for now.",
        date="2024-05-01",
        collection_name="amazon.aws",
    )

    identifier_problem = validate_iam_identifiers(
        "user", name=module.params.get("name"), path=module.params.get("path")
    )
    if identifier_problem:
        module.fail_json(msg=identifier_problem)

    retry_decorator = AWSRetry.jittered_backoff(catch_extra_error_codes=["EntityTemporarilyUnmodifiable"])
    connection = module.client("iam", retry_decorator=retry_decorator)

    state = module.params.get("state")

    try:
        if state == "present":
            create_or_update_user(connection, module)
        else:
            destroy_user(connection, module)
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

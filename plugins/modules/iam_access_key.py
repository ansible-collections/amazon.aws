#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_access_key
version_added: 2.1.0
version_added_collection: community.aws
short_description: Manage AWS IAM User access keys
description:
  - Manage AWS IAM user access keys.
author:
  - Mark Chappell (@tremble)
options:
  user_name:
    description:
      - The name of the IAM User to which the key belongs.
    required: true
    type: str
    aliases: ['username']
  id:
    description:
      - The ID of the access key.
      - Required when I(state=absent).
      - Mutually exclusive with I(rotate_keys).
    required: false
    type: str
  state:
    description:
      - Create or remove the access key.
      - When I(state=present) and I(id) is not defined a new key will be created.
    required: false
    type: str
    default: 'present'
    choices: [ 'present', 'absent' ]
  active:
    description:
      - Whether the key should be enabled or disabled.
      - Defaults to C(true) when creating a new key.
    required: false
    type: bool
    aliases: ['enabled']
  rotate_keys:
    description:
      - When there are already 2 access keys attached to the IAM user the oldest
        key will be removed and a new key created.
      - Ignored if I(state=absent)
      - Mutually exclusive with I(id).
    required: false
    type: bool
    default: false
notes:
  - For security reasons, this module should be used with B(no_log=true) and (register) functionalities
    when creating new access key.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a new access key
  amazon.aws.iam_access_key:
    user_name: example_user
    state: present
  no_log: true

- name: Delete the access_key
  amazon.aws.iam_access_key:
    user_name: example_user
    id: AKIA1EXAMPLE1EXAMPLE
    state: absent
"""

RETURN = r"""
access_key:
    description: A dictionary containing all the access key information.
    returned: When the key exists.
    type: complex
    contains:
        access_key_id:
            description: The ID for the access key.
            returned: success
            type: str
            sample: AKIA1EXAMPLE1EXAMPLE
        create_date:
            description: The date and time, in ISO 8601 date-time format, when the access key was created.
            returned: success
            type: str
            sample: "2021-10-09T13:25:42+00:00"
        user_name:
            description: The name of the IAM user to which the key is attached.
            returned: success
            type: str
            sample: example_user
        status:
            description:
              - The status of the key.
              - C(Active) means it can be used.
              - C(Inactive) means it can not be used.
            returned: success
            type: str
            sample: Inactive
secret_access_key:
    description:
      - The secret access key.
      - A secret access key is the equivalent of a password which can not be changed and as such should be considered sensitive data.
      - Secret access keys can only be accessed at creation time.
    returned: When a new key is created.
    type: str
    sample:  example/Example+EXAMPLE+example/Example
deleted_access_key_id:
    description:
      - The access key deleted during rotation.
    returned: When a key was deleted during the rotation of access keys
    type: str
    sample: AKIA1EXAMPLE1EXAMPLE
"""

from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import IAMErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_access_keys
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_access_key
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


@IAMErrorHandler.deletion_error_handler("Failed to delete access key for user")
def delete_access_key(access_keys, user, access_key_id):
    if not access_key_id:
        return False
    if access_key_id not in [k["access_key_id"] for k in access_keys]:
        return False

    if module.check_mode:
        return True

    client.delete_access_key(aws_retry=True, UserName=user, AccessKeyId=access_key_id)
    return True


@IAMErrorHandler.common_error_handler("Failed to update access key for user")
def update_access_key_state(access_keys, user, access_key_id, enabled):
    keys = {k["access_key_id"]: k for k in access_keys}

    if access_key_id not in keys:
        raise AnsibleIAMError(message=f'Access key "{access_key_id}" not found attached to User "{user}"')

    if enabled is None:
        return False

    access_key = keys.get(access_key_id)

    desired_status = "Active" if enabled else "Inactive"
    if access_key.get("status") == desired_status:
        return False

    if module.check_mode:
        return True

    client.update_access_key(aws_retry=True, UserName=user, AccessKeyId=access_key_id, Status=desired_status)
    return True


@IAMErrorHandler.common_error_handler("Failed to create access key for user")
def create_access_key(access_keys, user, rotate_keys, enabled):
    changed = False
    oldest_key = False

    if len(access_keys) > 1 and rotate_keys:
        oldest_key = access_keys[0].get("access_key_id")
        changed |= delete_access_key(access_keys, user, oldest_key)

    if module.check_mode:
        if oldest_key:
            return dict(deleted_access_key=oldest_key)
        return dict()

    results = client.create_access_key(aws_retry=True, UserName=user)
    access_key = normalize_iam_access_key(results.get("AccessKey"))

    # Update settings which can't be managed on creation
    if enabled is False:
        access_key_id = access_key["access_key_id"]
        update_access_key_state([access_key], user, access_key_id, enabled)
        access_key["status"] = "Inactive"

    if oldest_key:
        access_key["deleted_access_key"] = oldest_key

    return access_key


def update_access_key(access_keys, user, access_key_id, enabled):
    changed = update_access_key_state(access_keys, user, access_key_id, enabled)
    access_keys = get_iam_access_keys(client, user)
    keys = {k["access_key_id"]: k for k in access_keys}
    return changed, {"access_key": keys.get(access_key_id, None)}


def main():
    global module
    global client

    argument_spec = dict(
        user_name=dict(required=True, type="str", aliases=["username"]),
        id=dict(required=False, type="str"),
        state=dict(required=False, choices=["present", "absent"], default="present"),
        active=dict(required=False, type="bool", aliases=["enabled"]),
        rotate_keys=dict(required=False, type="bool", default=False),
    )

    required_if = [
        ["state", "absent", ("id",)],
    ]
    mutually_exclusive = [
        ["rotate_keys", "id"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")
    user = module.params.get("user_name")
    access_key_id = module.params.get("id")
    rotate_keys = module.params.get("rotate_keys")
    enabled = module.params.get("active")

    access_keys = get_iam_access_keys(client, user)
    results = dict()

    try:
        if state == "absent":
            changed = delete_access_key(access_keys, user, access_key_id)
            module.exit_json(changed=changed)

        if access_key_id:
            changed, results = update_access_key(access_keys, user, access_key_id, enabled)
        else:
            secret_key = create_access_key(access_keys, user, rotate_keys, enabled)
            changed = True
            results = {
                "access_key_id": secret_key.get("access_key_id", None),
                "secret_access_key": secret_key.pop("secret_access_key", None),
                "deleted_access_key_id": secret_key.pop("deleted_access_key", None),
                "access_key": secret_key or None,
            }
            results = scrub_none_parameters(results)

        module.exit_json(changed=changed, **results)
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: iam_access_key
version_added: 2.1.0
short_description: Manage AWS IAM User access keys
description:
  - Manage AWS IAM user access keys.
author: Mark Chappell (@tremble)
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

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a new access key
  community.aws.iam_access_key:
    user_name: example_user
    state: present

- name: Delete the access_key
  community.aws.iam_access_key:
    name: example_user
    access_key_id: AKIA1EXAMPLE1EXAMPLE
    state: absent
'''

RETURN = r'''
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
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.core import scrub_none_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def delete_access_key(access_keys, user, access_key_id):
    if not access_key_id:
        return False

    if access_key_id not in access_keys:
        return False

    if module.check_mode:
        return True

    try:
        client.delete_access_key(
            aws_retry=True,
            UserName=user,
            AccessKeyId=access_key_id,
        )
    except is_boto3_error_code('NoSuchEntityException'):
        # Generally occurs when race conditions have happened and someone
        # deleted the key while we were checking to see if it existed.
        return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(
            e, msg='Failed to delete access key "{0}" for user "{1}"'.format(access_key_id, user)
        )

    return True


def update_access_key(access_keys, user, access_key_id, enabled):
    if access_key_id not in access_keys:
        module.fail_json(
            msg='Access key "{0}" not found attached to User "{1}"'.format(access_key_id, user),
        )

    changes = dict()
    access_key = access_keys.get(access_key_id)

    if enabled is not None:
        desired_status = 'Active' if enabled else 'Inactive'
        if access_key.get('status') != desired_status:
            changes['Status'] = desired_status

    if not changes:
        return False

    if module.check_mode:
        return True

    try:
        client.update_access_key(
            aws_retry=True,
            UserName=user,
            AccessKeyId=access_key_id,
            **changes
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e, changes=changes,
            msg='Failed to update access key "{0}" for user "{1}"'.format(access_key_id, user),
        )
    return True


def create_access_key(access_keys, user, rotate_keys, enabled):
    changed = False
    oldest_key = False

    if len(access_keys) > 1 and rotate_keys:
        sorted_keys = sorted(list(access_keys), key=lambda k: access_keys[k].get('create_date', None))
        oldest_key = sorted_keys[0]
        changed |= delete_access_key(access_keys, user, oldest_key)

    if module.check_mode:
        if changed:
            return dict(deleted_access_key=oldest_key)
        return True

    try:
        results = client.create_access_key(aws_retry=True, UserName=user)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to create access key for user "{0}"'.format(user))
    results = camel_dict_to_snake_dict(results)
    access_key = results.get('access_key')
    access_key = normalize_boto3_result(access_key)

    # Update settings which can't be managed on creation
    if enabled is False:
        access_key_id = access_key['access_key_id']
        access_keys = {access_key_id: access_key}
        update_access_key(access_keys, user, access_key_id, enabled)
        access_key['status'] = 'Inactive'

    if oldest_key:
        access_key['deleted_access_key'] = oldest_key

    return access_key


def get_access_keys(user):
    try:
        results = client.list_access_keys(aws_retry=True, UserName=user)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e, msg='Failed to get access keys for user "{0}"'.format(user)
        )
    if not results:
        return None

    results = camel_dict_to_snake_dict(results)
    access_keys = results.get('access_key_metadata', [])
    if not access_keys:
        return []

    access_keys = normalize_boto3_result(access_keys)
    access_keys = {k['access_key_id']: k for k in access_keys}
    return access_keys


def main():

    global module
    global client

    argument_spec = dict(
        user_name=dict(required=True, type='str', aliases=['username']),
        id=dict(required=False, type='str'),
        state=dict(required=False, choices=['present', 'absent'], default='present'),
        active=dict(required=False, type='bool', aliases=['enabled']),
        rotate_keys=dict(required=False, type='bool', default=False),
    )

    required_if = [
        ['state', 'absent', ('id')],
    ]
    mutually_exclusive = [
        ['rotate_keys', 'id'],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())

    changed = False
    state = module.params.get('state')
    user = module.params.get('user_name')
    access_key_id = module.params.get('id')
    rotate_keys = module.params.get('rotate_keys')
    enabled = module.params.get('active')

    access_keys = get_access_keys(user)
    results = dict()

    if state == 'absent':
        changed |= delete_access_key(access_keys, user, access_key_id)
    else:
        # If we have an ID then we should try to update it
        if access_key_id:
            changed |= update_access_key(access_keys, user, access_key_id, enabled)
            access_keys = get_access_keys(user)
            results['access_key'] = access_keys.get(access_key_id, None)
        # Otherwise we try to create a new one
        else:
            secret_key = create_access_key(access_keys, user, rotate_keys, enabled)
            if isinstance(secret_key, bool):
                changed |= secret_key
            else:
                changed = True
                results['access_key_id'] = secret_key.get('access_key_id', None)
                results['secret_access_key'] = secret_key.pop('secret_access_key', None)
                results['deleted_access_key_id'] = secret_key.pop('deleted_access_key', None)
                if secret_key:
                    results['access_key'] = secret_key
                results = scrub_none_parameters(results)

    module.exit_json(changed=changed, **results)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_user
version_added: 0.9.0
short_description: Manage users in existing Amazon MQ broker
description:
    - Manage Amazon MQ users
author:
- FCO (frank-christian.otto@web.de)
requirements: [ boto3 ]
options:
  broker_id:
    description:
      - "The ID of the MQ broker to work on"
    type: str
  username:
    description:
      - "The name of the user to create/update/delete"
    type: str
  state:
    description:
      - "Create/Update vs Delete of user."
    default: present
    choices: [ 'present', 'absent' ]
  console_access:
    description:
      - "True: user can use MQ Console."
      - "Will not be changed on update unless explicitly defined"
    type: bool
    default: false
  groups:
    description:
      - "Set group memberships for user"
      - "Will not be changed on update unless explicitly defined"
    type: list
    default: empty list
  password:
    description:
      - "Set password for user"
      - "on create: if not defined a random password will be set"
      - "on update: will be ignored unless 'allow_pw_update' is set to true"
    type: str
  allow_pw_update:
    description:
      - "Only used of 'password' parameter set for existing user"
    default: false
    type: bool
extends_documentation_fragment:
- amazon.aws.aws

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# check tests/integration/targets/mq/tasks/test_mq_user.yml for more examples
- name: create/update user - set provided password if user doesn't exist, yet
  amazon.aws.mq_user:
    state: present
    broker_id: "aws-mq-broker-id"
    username: "sample_user1"
    console_access: false
    groups: [ "g1", "g2" ]
    password: "plain-text-password"
- name: allow console access and update group list - relying on default state
  amazon.aws.mq_user:
    broker_id: "aws-mq-broker-id"
    username: "sample_user1"
    console_access: true
    groups: [ "g1", "g2", "g3" ]
- name: remove user
  amazon.aws.mq_user:
    state: absent
    broker_id: "aws-mq-broker-id"
    username: "other_user"
  - name: reboot broker to apply pending user changes
  amazon.aws.mq_broker:
    broker_id: "aws-mq-broker-id"
    operation: "reboot"
'''

RETURN = '''
user:
    description: API response from create or update operation.
    type: complex
'''

# python3.6 or higher
#import secrets
# python2.7
import random
import hashlib

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

#from ansible.module_utils._text import to_text
#from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible.module_utils.core import AnsibleAWSModule

CREATE_DEFAULTS = {
    'console_access': False,
    'groups': [],

}

def _group_change_required(user_response, requested_groups):
    current_groups = []
    if 'Groups' in user_response:
        current_groups = user_response['Groups']
    elif 'Pending' in user_response:
        # to support automatic testing without broker reboot
        current_groups = user_response['Pending']['Groups']
    if len(current_groups) != len(requested_groups):
        return True
    if len(current_groups) != len(set(current_groups) & set(requested_groups)):
        return True
    #
    return False

def _console_access_change_required(user_response, requested_boolean):
    current_boolean = CREATE_DEFAULTS['console_access']
    if 'ConsoleAccess' in user_response:
        current_boolean = user_response['ConsoleAccess']
    elif 'Pending' in user_response:
        # to support automatic testing without broker reboot
        current_boolean = user_response['Pending']['ConsoleAccess']
    #
    return current_boolean != requested_boolean


def generate_password():
    # python3.6 or higher
    #return secrets.token_hex(20)
    # python2.7:
    in_str = ''
    for i in range(0,19):
        in_str += str(random.randint(10000, 99999))
    #
    h = hashlib.md5()
    h.update(in_str)
    return h.hexdigest()

# returns API response object
def _create_user(conn, module):
    kwargs = { 'BrokerId': module.params['broker_id'],
               'Username': module.params['username'] }
    if 'groups' in module.params and module.params['groups'] is not None:
        kwargs['Groups'] = module.params['groups']
    else:
        kwargs['Groups'] = CREATE_DEFAULTS['groups']
    if 'password' in module.params and module.params['password']:
        kwargs['Password'] = module.params['password']
    else:
        kwargs['Password'] = generate_password()
    if 'console_access' in module.params  and module.params['console_access'] is not None:
        kwargs['ConsoleAccess'] = module.params['console_access']
    else:
        kwargs['ConsoleAccess'] = CREATE_DEFAULTS['console_access']
    try:
        response = conn.create_user(**kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create user")
    return response

# returns API response object
def _update_user(conn, module, kwargs):
    try:
        response = conn.update_user(**kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't update user")
    return response

def get_matching_user(conn, module, broker_id, username):
    try:
        return conn.describe_user(BrokerId=broker_id, Username=username)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NotFoundException':
            return None
        else:
            module.fail_json_aws(e, msg="Couldn't get user details")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Couldn't get user details")

def ensure_user_present(conn, module):
    user = get_matching_user(conn, module, module.params['broker_id'], module.params['username'])
    changed = False

    if user is None:
        if not module.check_mode:
            response = _create_user(conn, module)
        changed = True
    else:
        kwargs = {}
        if 'groups' in module.params and module.params['groups'] is not None:
            if _group_change_required(user, module.params['groups']):
                kwargs['Groups'] = module.params['groups']
        if 'console_access' in module.params  and module.params['console_access'] is not None:
            if _console_access_change_required(user, module.params['console_access']):
                kwargs['ConsoleAccess'] = module.params['console_access']
        if 'password' in module.params and module.params['password']:
            if 'allow_pw_update' in module.params and module.params['allow_pw_update']:
                kwargs['Password'] = module.params['password']
        if len(kwargs) == 0:
            changed = False
        else:
            if not module.check_mode:
                kwargs['BrokerId'] = module.params['broker_id']
                kwargs['Username'] = module.params['username']
                response = _update_user(conn, module, kwargs)
            #
            changed = True
    #
    user = get_matching_user(conn, module, module.params['broker_id'], module.params['username'])

    return {
        'changed': changed,
        'user': user
    }

def ensure_user_absent(conn, module):
    user = get_matching_user(conn, module, module.params['broker_id'], module.params['username'])
    if user is None:
        return {'changed': False}
    # better support for testing
    if 'Pending' in user and 'PendingChange' in user['Pending'] \
        and user['Pending']['PendingChange'] == 'DELETE':
        return {'changed': False}
    try:
        if not module.check_mode:
            conn.delete_user(BrokerId=user['BrokerId'], Username=user['Username'])
        return {'changed': True}
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete user")


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type='str'),
        username=dict(required=True, type='str'),
        console_access=dict(required=False, type='bool'),
        groups=dict(required=False, type='list'),
        password=dict(required=False, type='str', no_log=True),
        allow_pw_update=dict(default=False, required=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('mq')

    state = module.params.get('state')

    try:
        if state == 'present':
            result = ensure_user_present(connection, module)
        elif state == 'absent':
            result = ensure_user_absent(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(**result)


if __name__ == '__main__':
    main()

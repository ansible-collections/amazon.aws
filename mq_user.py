#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: mq_user
version_added: 6.0.0
short_description: Manage users in existing Amazon MQ broker
description:
  - Manage Amazon MQ users.
  - Pending changes are taking into account for idempotency.
author:
  - FCO (@fotto)
options:
  broker_id:
    description:
      - The ID of the MQ broker to work on.
    type: str
    required: true
  username:
    description:
      - The name of the user to create/update/delete.
    type: str
    required: true
  state:
    description:
      - Create/Update vs Delete of user.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  console_access:
    description:
      - Whether the user can access the MQ Console.
      - Defaults to C(false) on creation.
    type: bool
  groups:
    description:
      - Set group memberships for user.
      - Defaults to C([]) on creation.
    type: list
    elements: str
  password:
    description:
      - Set password for user.
      - Defaults to a random password on creation.
      - Ignored unless I(allow_pw_update=true).
    type: str
  allow_pw_update:
    description:
      - When I(allow_pw_update=true) and I(password) is set, the password
        will always be updated for the user.
    default: false
    type: bool
extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.modules
  - amazon.aws.region.modules
"""

EXAMPLES = r"""
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
    region: "{{ aws_region }}"
    console_access: true
    groups: [ "g1", "g2", "g3" ]
- name: remove user - setting all credentials explicitly
  amazon.aws.mq_user:
    state: absent
    broker_id: "aws-mq-broker-id"
    username: "other_user"
"""

RETURN = r"""
user:
    description:
      - just echos the username
      - "only present when state=present"
    type: str
    returned: success
"""

import secrets

try:
    import botocore
except ImportError as ex:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code

CREATE_DEFAULTS = {
    "console_access": False,
    "groups": [],
}


def _group_change_required(user_response, requested_groups):
    current_groups = []
    if "Groups" in user_response:
        current_groups = user_response["Groups"]
    elif "Pending" in user_response:
        # to support automatic testing without broker reboot
        current_groups = user_response["Pending"]["Groups"]
    if len(current_groups) != len(requested_groups):
        return True
    if len(current_groups) != len(set(current_groups) & set(requested_groups)):
        return True
    #
    return False


def _console_access_change_required(user_response, requested_boolean):
    current_boolean = CREATE_DEFAULTS["console_access"]
    if "ConsoleAccess" in user_response:
        current_boolean = user_response["ConsoleAccess"]
    elif "Pending" in user_response:
        # to support automatic testing without broker reboot
        current_boolean = user_response["Pending"]["ConsoleAccess"]
    #
    return current_boolean != requested_boolean


def generate_password():
    return secrets.token_hex(20)


# returns API response object
def _create_user(conn, module):
    kwargs = {"BrokerId": module.params["broker_id"], "Username": module.params["username"]}
    if "groups" in module.params and module.params["groups"] is not None:
        kwargs["Groups"] = module.params["groups"]
    else:
        kwargs["Groups"] = CREATE_DEFAULTS["groups"]
    if "password" in module.params and module.params["password"]:
        kwargs["Password"] = module.params["password"]
    else:
        kwargs["Password"] = generate_password()
    if "console_access" in module.params and module.params["console_access"] is not None:
        kwargs["ConsoleAccess"] = module.params["console_access"]
    else:
        kwargs["ConsoleAccess"] = CREATE_DEFAULTS["console_access"]
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
        response = conn.describe_user(BrokerId=broker_id, Username=username)
    except is_boto3_error_code("NotFoundException"):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get user details")
    return response


def ensure_user_present(conn, module):
    user = get_matching_user(conn, module, module.params["broker_id"], module.params["username"])
    changed = False

    if user is None:
        if not module.check_mode:
            _response = _create_user(conn, module)
        changed = True
    else:
        kwargs = {}
        if "groups" in module.params and module.params["groups"] is not None:
            if _group_change_required(user, module.params["groups"]):
                kwargs["Groups"] = module.params["groups"]
        if "console_access" in module.params and module.params["console_access"] is not None:
            if _console_access_change_required(user, module.params["console_access"]):
                kwargs["ConsoleAccess"] = module.params["console_access"]
        if "password" in module.params and module.params["password"]:
            if "allow_pw_update" in module.params and module.params["allow_pw_update"]:
                kwargs["Password"] = module.params["password"]
        if len(kwargs) == 0:
            changed = False
        else:
            if not module.check_mode:
                kwargs["BrokerId"] = module.params["broker_id"]
                kwargs["Username"] = module.params["username"]
                response = _update_user(conn, module, kwargs)
            #
            changed = True
    #
    user = get_matching_user(conn, module, module.params["broker_id"], module.params["username"])

    return {"changed": changed, "user": camel_dict_to_snake_dict(user, ignore_list=["Tags"])}


def ensure_user_absent(conn, module):
    user = get_matching_user(conn, module, module.params["broker_id"], module.params["username"])
    result = {"changed": False}
    if user is None:
        return result
    # better support for testing
    if "Pending" in user and "PendingChange" in user["Pending"] and user["Pending"]["PendingChange"] == "DELETE":
        return result

    result = {"changed": True}
    if module.check_mode:
        return result

    try:
        conn.delete_user(BrokerId=user["BrokerId"], Username=user["Username"])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete user")

    return result


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type="str"),
        username=dict(required=True, type="str"),
        console_access=dict(required=False, type="bool"),
        groups=dict(required=False, type="list", elements="str"),
        password=dict(required=False, type="str", no_log=True),
        allow_pw_update=dict(default=False, required=False, type="bool"),
        state=dict(default="present", choices=["present", "absent"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("mq")

    state = module.params.get("state")

    try:
        if state == "present":
            result = ensure_user_present(connection, module)
        elif state == "absent":
            result = ensure_user_absent(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(**result)


if __name__ == "__main__":
    main()

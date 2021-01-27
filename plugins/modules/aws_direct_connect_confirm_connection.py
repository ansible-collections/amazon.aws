#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_direct_connect_confirm_connection
short_description: Confirms the creation of a hosted DirectConnect connection.
description:
  - Confirms the creation of a hosted DirectConnect, which requires approval before it can be used.
  - DirectConnect connections that require approval would be in the 'ordering'.
  - After confirmation, they will move to the 'pending' state and finally the 'available' state.
author: "Matt Traynham (@mtraynham)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

requirements:
  - boto3
  - botocore
options:
  name:
    description:
      - The name of the Direct Connect connection.
      - One of I(connection_id) or I(name) must be specified.
    type: str
  connection_id:
    description:
      - The ID of the Direct Connect connection.
      - One of I(connection_id) or I(name) must be specified.
    type: str
'''

EXAMPLES = '''

# confirm a Direct Connect by name
- name: confirm the connection id
  aws_direct_connect_confirm_connection:
    name: my_host_direct_connect

# confirm a Direct Connect by connection_id
- name: confirm the connection id
  aws_direct_connect_confirm_connection:
    connection_id: dxcon-xxxxxxxx
'''

RETURN = '''

connection_state:
  description: The state of the connection.
  returned: always
  type: str
  sample: pending
'''

import traceback

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by imported AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.direct_connect import DirectConnectError
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry

retry_params = {"tries": 10, "delay": 5, "backoff": 1.2, "catch_extra_error_codes": ["DirectConnectClientException"]}


@AWSRetry.backoff(**retry_params)
def describe_connections(client, params):
    return client.describe_connections(**params)


def find_connection_id(client, connection_id=None, connection_name=None):
    params = {}
    if connection_id:
        params['connectionId'] = connection_id
    try:
        response = describe_connections(client, params)
    except (BotoCoreError, ClientError) as e:
        if connection_id:
            msg = "Failed to describe DirectConnect ID {0}".format(connection_id)
        else:
            msg = "Failed to describe DirectConnect connections"
        raise DirectConnectError(msg=msg,
                                 last_traceback=traceback.format_exc(),
                                 exception=e)

    match = []
    if len(response.get('connections', [])) == 1 and connection_id:
        if response['connections'][0]['connectionState'] != 'deleted':
            match.append(response['connections'][0]['connectionId'])

    for conn in response.get('connections', []):
        if connection_name == conn['connectionName'] and conn['connectionState'] != 'deleted':
            match.append(conn['connectionId'])

    if len(match) == 1:
        return match[0]
    else:
        raise DirectConnectError(msg="Could not find a valid DirectConnect connection")


def get_connection_state(client, connection_id):
    try:
        response = describe_connections(client, dict(connectionId=connection_id))
        return response['connections'][0]['connectionState']
    except (BotoCoreError, ClientError, IndexError) as e:
        raise DirectConnectError(msg="Failed to describe DirectConnect connection {0} state".format(connection_id),
                                 last_traceback=traceback.format_exc(),
                                 exception=e)


def main():
    argument_spec = dict(
        connection_id=dict(),
        name=dict()
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[['connection_id', 'name']],
                              required_one_of=[['connection_id', 'name']])
    client = module.client('directconnect')

    connection_id = module.params['connection_id']
    connection_name = module.params['name']

    changed = False
    connection_state = None
    try:
        connection_id = find_connection_id(client,
                                           connection_id,
                                           connection_name)
        connection_state = get_connection_state(client, connection_id)
        if connection_state == 'ordering':
            client.confirm_connection(connectionId=connection_id)
            changed = True
            connection_state = get_connection_state(client, connection_id)
    except DirectConnectError as e:
        if e.last_traceback:
            module.fail_json(msg=e.msg, exception=e.last_traceback, **camel_dict_to_snake_dict(e.exception.response))
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, connection_state=connection_state)


if __name__ == '__main__':
    main()

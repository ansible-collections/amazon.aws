#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_user_info
version_added: 0.9.0
short_description: List users of an Amazon MQ broker
description:
    - list users for the specified broker id
    - Pending creations and deletions can be skipped by options
author: FCO (frank-christian.otto@web.de)
requirements:
  - boto3
  - botocore
options:
  broker_id:
    description:
      - "The ID of the MQ broker to work on"
    type: str
  max_results:
    description:
      - "The maximum number of results to return"
    type: int
    default: 100
  skip_pending_create:
    description:
      - "Will skip pending creates from the result set"
    type: bool
    default: false
  skip_pending_delete:
    description:
      - "Will skip pending deletes from the result set"
    type: bool
    default: false
  as_dict:
    description:
      - "convert result into lookup table by username"
    type: bool
    default: false

extends_documentation_fragment:
- amazon.aws.aws

'''


EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
#       or check tests/integration/targets/mq/tasks/test_mq_user_info.yml
- name: get all users as list
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    max_results: 1000
  register: result
- name: show number of users retrieved
  debug:
    msg: "{{ result.users | length }}"
- name: get users as dict - relying on default limit
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    as_dict: true
  register: result
- name: check if some specific user exists
  debug:
    msg: "user sample_user1 exists"
  when: 'sample_user1' in result.users
'''

RETURN = '''
user:
    type: complex
    description: 
    - list of users as array or as dict keyed by username (if as_dict=true)
    - each elements/entry are 1:1 those from the 'Users' list in the API response of list_users()
'''


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.core import AnsibleAWSModule

DEFAULTS = {
    'max_results': 100,
    'skip_pending_create': False,
    'skip_pending_delete': False
}

def get_user_info(conn, module):
    try:
        response = conn.list_users(BrokerId=module.params['broker_id'],
                            MaxResults=module.params['max_results'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe users')
    #
    if not module.params['skip_pending_create'] and not module.params['skip_pending_delete']:
        # we can simply return the sub-object from the response
        records = response['Users']
    else:
        records = []
        for record in response['Users']:
            if 'PendingChange' in record:
                if record['PendingChange'] == 'CREATE' and module.params['skip_pending_create']:
                    continue
                if record['PendingChange'] == 'DELETE' and module.params['skip_pending_delete']:
                    continue
            #
            records.append(record)
    #
    if module.params['as_dict']:
        user_records = {}
        for record in records:
            user_records[record['Username']] = record
        #
        return user_records
    else:
        return records


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type='str'),
        max_results=dict(required=False, type=int, default=DEFAULTS['max_results']),
        skip_pending_create=dict(required=False, type='bool', default=DEFAULTS['skip_pending_create']),
        skip_pending_delete=dict(required=False, type='bool', default=DEFAULTS['skip_pending_delete']),
        as_dict=dict(required=False, type='bool', default=False),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('mq')

    try:
        user_list = get_user_info(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(users=user_list)


if __name__ == '__main__':
    main()

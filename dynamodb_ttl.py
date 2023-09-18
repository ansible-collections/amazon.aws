#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: dynamodb_ttl
version_added: 1.0.0
short_description: Set TTL for a given DynamoDB table
description:
- Uses boto3 to set TTL.
- Requires botocore version 1.5.24 or higher.
options:
  state:
    description:
    - State to set DynamoDB table to.
    choices: ['enable', 'disable']
    required: false
    type: str
  table_name:
    description:
    - Name of the DynamoDB table to work on.
    required: true
    type: str
  attribute_name:
    description:
    - The name of the Time To Live attribute used to store the expiration time for items in the table.
    - This appears to be required by the API even when disabling TTL.
    required: true
    type: str

author: Ted Timmons (@tedder)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

requirements: [ botocore>=1.5.24, boto3 ]
'''

EXAMPLES = '''
- name: enable TTL on my cowfacts table
  community.aws.dynamodb_ttl:
    state: enable
    table_name: cowfacts
    attribute_name: cow_deleted_date

- name: disable TTL on my cowfacts table
  community.aws.dynamodb_ttl:
    state: disable
    table_name: cowfacts
    attribute_name: cow_deleted_date
'''

RETURN = '''
current_status:
  description: current or new TTL specification.
  type: dict
  returned: always
  sample:
  - { "AttributeName": "deploy_timestamp", "TimeToLiveStatus": "ENABLED" }
  - { "AttributeName": "deploy_timestamp", "Enabled": true }
'''

import distutils.version
import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def get_current_ttl_state(c, table_name):
    '''Fetch the state dict for a table.'''
    current_state = c.describe_time_to_live(TableName=table_name)
    return current_state.get('TimeToLiveDescription')


def does_state_need_changing(attribute_name, desired_state, current_spec):
    '''Run checks to see if the table needs to be modified. Basically a dirty check.'''
    if not current_spec:
        # we don't have an entry (or a table?)
        return True

    if desired_state.lower() == 'enable' and current_spec.get('TimeToLiveStatus') not in ['ENABLING', 'ENABLED']:
        return True
    if desired_state.lower() == 'disable' and current_spec.get('TimeToLiveStatus') not in ['DISABLING', 'DISABLED']:
        return True
    if attribute_name != current_spec.get('AttributeName'):
        return True

    return False


def set_ttl_state(c, table_name, state, attribute_name):
    '''Set our specification. Returns the update_time_to_live specification dict,
       which is different than the describe_* call.'''
    is_enabled = False
    if state.lower() == 'enable':
        is_enabled = True

    ret = c.update_time_to_live(
        TableName=table_name,
        TimeToLiveSpecification={
            'Enabled': is_enabled,
            'AttributeName': attribute_name
        }
    )

    return ret.get('TimeToLiveSpecification')


def main():
    argument_spec = dict(
        state=dict(choices=['enable', 'disable']),
        table_name=dict(required=True),
        attribute_name=dict(required=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
    )

    if distutils.version.StrictVersion(botocore.__version__) < distutils.version.StrictVersion('1.5.24'):
        # TTL was added in this version.
        module.fail_json(msg='Found botocore in version {0}, but >= {1} is required for TTL support'.format(botocore.__version__, '1.5.24'))

    try:
        dbclient = module.client('dynamodb')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    result = {'changed': False}
    state = module.params['state']

    # wrap all our calls to catch the standard exceptions. We don't pass `module` in to the
    # methods so it's easier to do here.
    try:
        current_state = get_current_ttl_state(dbclient, module.params['table_name'])

        if does_state_need_changing(module.params['attribute_name'], module.params['state'], current_state):
            # changes needed
            new_state = set_ttl_state(dbclient, module.params['table_name'], module.params['state'], module.params['attribute_name'])
            result['current_status'] = new_state
            result['changed'] = True
        else:
            # no changes needed
            result['current_status'] = current_state

    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="Failed to get or update ttl state")
    except botocore.exceptions.ParamValidationError as e:
        module.fail_json_aws(e, msg="Failed due to invalid parameters")
    except ValueError as e:
        module.fail_json_aws(e, msg="Failed")

    module.exit_json(**result)


if __name__ == '__main__':
    main()

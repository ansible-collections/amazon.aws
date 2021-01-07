#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_broker
version_added: 0.9.0
short_description: MQ broker configurations except user/config changes
description:
    - Get details about a broker
    - reboot a broker
author: FCO (frank-christian.otto@web.de)
requirements:
  - boto3
  - botocore
options:
  broker_id:
    description:
      - "The ID of the MQ broker to work on"
    type: str
  operation:
    description:
      - "Operation to perform: info, reboot"
    type: str
    default: info

extends_documentation_fragment:
- amazon.aws.aws

'''


EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
#       or check tests/integration/targets/mq/tasks/test_mq_broker.yml
- name: get current broker settings - explicitly requesting info operation
  amazon.aws.mq_broker:
    broker_id: "aws-mq-broker-id"
    operation: "info"
  register: broker_info
- name: get current broker settings - relying on default operation
  amazon.aws.mq_broker:
    broker_id: "aws-mq-broker-id"
  register: broker_info 
- name: request broker reboot - does not wait for reboot to finish
  amazon.aws.mq_broker:
    broker_id: "aws-mq-broker-id"
    operation: "reboot"
'''

RETURN = '''
broker:
    description: API response of describe_broker() after operation has been performed
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.core import AnsibleAWSModule


def get_broker_info(conn, module):
    try:
        return conn.describe_broker(BrokerId=module.params['broker_id'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get broker details.")


def reboot_broker(conn, module, broker_id):
    try:
        return conn.reboot_broker(
            BrokerId=broker_id
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't reboot broker.")


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type='str'),
        operation=dict(required=False, type='str', default='info'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('mq')

    if module.params['operation'] == 'info':
        try:
            result = get_broker_info(connection, module)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        #
        module.exit_json(broker=result)
    elif module.params['operation'] == 'reboot':
        try:
            changed = True
            if not module.check_mode:
                reboot_broker(connection, module, module.params['broker_id'])
            #
            result = get_broker_info(connection, module)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        module.exit_json(broker=result, changed=changed)
    else:
        module.fail_json_aws(RuntimeError,
                             msg="Invalid broker operation requested ({}). Valid are: 'info', 'reboot'".format(module.params['operation']))



if __name__ == '__main__':
    main()

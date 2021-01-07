#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_broker_config
version_added: 0.9.0
short_description: Update broker configuration
description:
    - Update configuration for an MQ broker
    - Optionally allows broker reboot to make changes effective immediately
author: FCO (frank-christian.otto@web.de)
requirements:
  - boto3
  - botocore
options:
  broker_id:
    description:
      - "The ID of the MQ broker to work on"
    type: str
  config_xml:
    description:
      - "The maximum number of results to return"
    type: str
  config_description:
    description:
      - "Description to set on new configuration revision"
    type: str
  reboot:
    description:
      - "Reboot broker after new config has been applied"
    type: bool
    default: false

extends_documentation_fragment:
- amazon.aws.aws

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
#       or check tests/integration/targets/mq/tasks/test_mq_broker_config.yml
- name: send new XML config to broker
  amazon.aws.mq_broker_config:
    broker_id: "aws-mq-broker-id"
    config_xml: "{{ lookup('file', 'activemq.xml' )}}"
- name: reboot broker to make new config active
  amazon.aws.mq_broker:
    broker_id: "aws-mq-broker-id"
    operation: "reboot"
'''

RETURN = '''
broker:
    description: API response of describe_broker() after changes have been applied
    type: complex
configuration: 
    description: details about new configuration object
    returned: I(changed=true)
    type: complex
    contains:
        id: 
            description: configuration ID of broker configuration
            type: str
            example: c-386541b8-3139-42c2-9c2c-a4c267c1714f
        revision: 
            description: revision of the configuration that will be active after next reboot
            type: int
            example: 4
'''

import base64
import re
import sys
IS_PYTHON3 = True
if sys.version_info.major < 3:
    IS_PYTHON3 = False

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.core import AnsibleAWSModule

DEFAULTS = {
    'reboot': False
}
FULL_DEBUG = False

# we a simple comparision here: strip down spaces and compare the rest
# TODO: use same XML normalizer on new as used by AWS before comparing strings
def is_same_config(old, new):
    old_stripped = re.sub('\s+',' ', old, flags=re.S).rstrip()
    new_stripped = re.sub('\s+',' ', new, flags=re.S).rstrip()
    return old_stripped == new_stripped

def get_broker_info(conn, module):
    try:
        return conn.describe_broker(BrokerId=module.params['broker_id'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get broker details.")


def get_current_configuration(conn, module, cfg_id, cfg_revision):
    try:
        return conn.describe_configuration_revision(
            ConfigurationId=cfg_id,
            ConfigurationRevision=str(cfg_revision)
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get configuration revision.")


def create_and_assign_config(conn, module, broker_id, cfg_id, cfg_xml_encoded):
    kwargs = {
        'ConfigurationId': cfg_id,
        'Data': cfg_xml_encoded
    }
    if 'config_description' in module.params and module.params['config_description']:
        kwargs['Description'] = module.params['config_description']
    else:
        kwargs['Description'] = 'Updated through amazon.aws.mq_broker_config ansible module'
    #
    try:
        c_response = conn.update_configuration(**kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create new configuration revision.")
    #
    new_config_revision = c_response['LatestRevision']['Revision']
    try:
        b_response = conn.update_broker(BrokerId=broker_id, Configuration={
                      'Id': cfg_id,
                      'Revision': new_config_revision
                  })
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't assign new configuration revision to broker.")
    #
    return (c_response, b_response)

def reboot_broker(conn, module, broker_id):
    try:
        return conn.reboot_broker(
            BrokerId=broker_id
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't reboot broker.")


def ensure_config(conn, module):
    broker_id = module.params['broker_id']
    broker_info = get_broker_info(conn, module)
    changed = False
    current_cfg = broker_info['Configurations']['Current']
    if 'Pending' in broker_info['Configurations']:
        current_cfg = broker_info['Configurations']['Pending']
    current_cfg_encoded = get_current_configuration(conn, module,
                                            current_cfg['Id'], current_cfg['Revision'])['Data']
    if IS_PYTHON3:
        current_cfg_decoded = base64.b64decode(current_cfg_encoded.encode()).decode()
    else:
        current_cfg_decoded = base64.b64decode(current_cfg_encoded)
    if is_same_config(current_cfg_decoded, module.params['config_xml']):
        return {
            'changed': changed,
            'broker': broker_info
        }
    else:
        (c_response, b_response) = (None, None)
        if not module.check_mode:
            if IS_PYTHON3:
                new_cfg_encoded = base64.b64encode(module.params['config_xml'].encode()).decode()
            else:
                new_cfg_encoded = base64.b64encode(module.params['config_xml'])
            (c_response, b_response) = create_and_assign_config(conn, module, broker_id,
                                     current_cfg['Id'], new_cfg_encoded)
        #
        changed = True
    #
    if changed and module.params['reboot'] and not module.check_mode:
        reboot_broker(conn, module, broker_id)
    #
    broker_info = get_broker_info(conn, module)
    return_struct = {
        'changed': changed,
        'broker': broker_info,
        'configuration': {
            'id': c_response['Id'],
            'revision': c_response['LatestRevision']['Revision']
        }
    }
    if FULL_DEBUG:
        return_struct['old_config_xml'] = base64.b64decode(current_cfg_encoded)
        return_struct['new_config_xml'] = module.params['config_xml']
        return_struct['old_config_revision'] = current_cfg['Revision']
    return return_struct


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type='str'),
        config_xml=dict(required=True, type='str'),
        config_description=dict(required=False, type='str'),
        reboot=dict(required=False, type='bool', default=DEFAULTS['reboot']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('mq')

    try:
        result = ensure_config(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(**result)


if __name__ == '__main__':
    main()

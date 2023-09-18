#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cloudwatchlogs_log_group_info
short_description: Get information about log_group in CloudWatchLogs
description:
    - Lists the specified log groups. You can list all your log groups or filter the results by prefix.
    - This module was called C(cloudwatchlogs_log_group_facts) before Ansible 2.9. The usage did not change.
author:
    - Willian Ricardo (@willricardo) <willricardo@gmail.com>
requirements: [ botocore, boto3 ]
options:
    log_group_name:
      description:
        - The name or prefix of the log group to filter by.
      type: str
extends_documentation_fragment:
- ansible.amazon.aws
- ansible.amazon.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- cloudwatchlogs_log_group_info:
    log_group_name: test-log-group
'''

RETURN = '''
log_groups:
    description: Return the list of complex objects representing log groups
    returned: success
    type: complex
    contains:
        log_group_name:
            description: The name of the log group.
            returned: always
            type: str
        creation_time:
            description: The creation time of the log group.
            returned: always
            type: int
        retention_in_days:
            description: The number of days to retain the log events in the specified log group.
            returned: always
            type: int
        metric_filter_count:
            description: The number of metric filters.
            returned: always
            type: int
        arn:
            description: The Amazon Resource Name (ARN) of the log group.
            returned: always
            type: str
        stored_bytes:
            description: The number of bytes stored.
            returned: always
            type: str
        kms_key_id:
            description: The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.
            returned: always
            type: str
'''

import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.amazon.plugins.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def describe_log_group(client, log_group_name, module):
    params = {}
    if log_group_name:
        params['logGroupNamePrefix'] = log_group_name
    try:
        paginator = client.get_paginator('describe_log_groups')
        desc_log_group = paginator.paginate(**params).build_full_result()
        return desc_log_group
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to describe log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to describe log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        log_group_name=dict(),
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'cloudwatchlogs_log_group_facts':
        module.deprecate("The 'cloudwatchlogs_log_group_facts' module has been renamed to 'cloudwatchlogs_log_group_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    logs = boto3_conn(module, conn_type='client', resource='logs', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    desc_log_group = describe_log_group(client=logs,
                                        log_group_name=module.params['log_group_name'],
                                        module=module)
    final_log_group_snake = []

    for log_group in desc_log_group['logGroups']:
        final_log_group_snake.append(camel_dict_to_snake_dict(log_group))

    desc_log_group_result = dict(changed=False, log_groups=final_log_group_snake)
    module.exit_json(**desc_log_group_result)


if __name__ == '__main__':
    main()

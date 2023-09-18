#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = '''
---
module: cloudwatchlogs_log_group_info
version_added: 1.0.0
short_description: Get information about log_group in CloudWatchLogs
description:
    - Lists the specified log groups. You can list all your log groups or filter the results by prefix.
    - This module was called C(cloudwatchlogs_log_group_facts) before Ansible 2.9. The usage did not change.
author:
    - Willian Ricardo (@willricardo) <willricardo@gmail.com>
options:
    log_group_name:
      description:
        - The name or prefix of the log group to filter by.
      type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- community.aws.cloudwatchlogs_log_group_info:
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

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def describe_log_group(client, log_group_name, module):
    params = {}
    if log_group_name:
        params['logGroupNamePrefix'] = log_group_name
    try:
        paginator = client.get_paginator('describe_log_groups')
        desc_log_group = paginator.paginate(**params).build_full_result()
        return desc_log_group
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to describe log group {0}".format(log_group_name))


def main():
    argument_spec = dict(
        log_group_name=dict(),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'cloudwatchlogs_log_group_facts':
        module.deprecate("The 'cloudwatchlogs_log_group_facts' module has been renamed to 'cloudwatchlogs_log_group_info'",
                         date='2021-12-01', collection_name='community.aws')

    try:
        logs = module.client('logs')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

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

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = '''
---
module: cloudwatchlogs_log_group
version_added: 1.0.0
short_description: create or delete log_group in CloudWatchLogs
notes:
    - For details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/logs.html).
description:
    - Create or delete log_group in CloudWatchLogs.
author:
    - Willian Ricardo (@willricardo) <willricardo@gmail.com>
requirements: [ json, botocore, boto3 ]
options:
    state:
      description:
        - Whether the rule is present or absent.
      choices: ["present", "absent"]
      default: present
      required: false
      type: str
    log_group_name:
      description:
        - The name of the log group.
      required: true
      type: str
    kms_key_id:
      description:
        - The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.
      required: false
      type: str
    tags:
      description:
        - The key-value pairs to use for the tags.
      required: false
      type: dict
    retention:
      description:
        - The number of days to retain the log events in the specified log group.
        - "Valid values are: [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]"
        - Mutually exclusive with I(purge_retention_policy).
      required: false
      type: int
    purge_retention_policy:
      description:
        - "Whether to purge the retention policy or not."
        - "Mutually exclusive with I(retention) and I(overwrite)."
      default: false
      required: false
      type: bool
    overwrite:
      description:
        - Whether an existing log group should be overwritten on create.
        - Mutually exclusive with I(purge_retention_policy).
      default: false
      required: false
      type: bool
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- community.aws.cloudwatchlogs_log_group:
    log_group_name: test-log-group

- community.aws.cloudwatchlogs_log_group:
    state: present
    log_group_name: test-log-group
    tags: { "Name": "test-log-group", "Env" : "QA" }

- community.aws.cloudwatchlogs_log_group:
    state: present
    log_group_name: test-log-group
    tags: { "Name": "test-log-group", "Env" : "QA" }
    kms_key_id: arn:aws:kms:region:account-id:key/key-id

- community.aws.cloudwatchlogs_log_group:
    state: absent
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

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def create_log_group(client, log_group_name, kms_key_id, tags, retention, module):
    request = {'logGroupName': log_group_name}
    if kms_key_id:
        request['kmsKeyId'] = kms_key_id
    if tags:
        request['tags'] = tags

    try:
        client.create_log_group(**request)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to create log group: {0}".format(to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to create log group: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    if retention:
        input_retention_policy(client=client,
                               log_group_name=log_group_name,
                               retention=retention, module=module)

    desc_log_group = describe_log_group(client=client,
                                        log_group_name=log_group_name,
                                        module=module)

    if 'logGroups' in desc_log_group:
        for i in desc_log_group['logGroups']:
            if log_group_name == i['logGroupName']:
                return i
    module.fail_json(msg="The aws CloudWatchLogs log group was not created. \n please try again!")


def input_retention_policy(client, log_group_name, retention, module):
    try:
        permited_values = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]

        if retention in permited_values:
            response = client.put_retention_policy(logGroupName=log_group_name,
                                                   retentionInDays=retention)
        else:
            delete_log_group(client=client, log_group_name=log_group_name, module=module)
            module.fail_json(msg="Invalid retention value. Valid values are: [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]")
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to put retention policy for log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to put retention policy for log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def delete_retention_policy(client, log_group_name, module):
    try:
        client.delete_retention_policy(logGroupName=log_group_name)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to delete retention policy for log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to delete retention policy for log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def delete_log_group(client, log_group_name, module):
    desc_log_group = describe_log_group(client=client,
                                        log_group_name=log_group_name,
                                        module=module)

    try:
        if 'logGroups' in desc_log_group:
            for i in desc_log_group['logGroups']:
                if log_group_name == i['logGroupName']:
                    client.delete_log_group(logGroupName=log_group_name)

    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to delete log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to delete log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def describe_log_group(client, log_group_name, module):
    try:
        desc_log_group = client.describe_log_groups(logGroupNamePrefix=log_group_name)
        return desc_log_group
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to describe log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to describe log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def main():
    argument_spec = dict(
        log_group_name=dict(required=True, type='str'),
        state=dict(choices=['present', 'absent'],
                   default='present'),
        kms_key_id=dict(required=False, type='str'),
        tags=dict(required=False, type='dict'),
        retention=dict(required=False, type='int'),
        purge_retention_policy=dict(required=False, type='bool', default=False),
        overwrite=dict(required=False, type='bool', default=False),
    )

    mutually_exclusive = [['retention', 'purge_retention_policy'], ['purge_retention_policy', 'overwrite']]
    module = AnsibleAWSModule(argument_spec=argument_spec, mutually_exclusive=mutually_exclusive)

    try:
        logs = module.client('logs')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    state = module.params.get('state')
    changed = False

    # Determine if the log group exists
    desc_log_group = describe_log_group(client=logs, log_group_name=module.params['log_group_name'], module=module)
    found_log_group = {}
    for i in desc_log_group.get('logGroups', []):
        if module.params['log_group_name'] == i['logGroupName']:
            found_log_group = i
            break

    if state == 'present':
        if found_log_group:
            if module.params['overwrite'] is True:
                changed = True
                delete_log_group(client=logs, log_group_name=module.params['log_group_name'], module=module)
                found_log_group = create_log_group(client=logs,
                                                   log_group_name=module.params['log_group_name'],
                                                   kms_key_id=module.params['kms_key_id'],
                                                   tags=module.params['tags'],
                                                   retention=module.params['retention'],
                                                   module=module)
            elif module.params['purge_retention_policy']:
                if found_log_group.get('retentionInDays'):
                    changed = True
                    delete_retention_policy(client=logs,
                                            log_group_name=module.params['log_group_name'],
                                            module=module)
            elif module.params['retention'] != found_log_group.get('retentionInDays'):
                if module.params['retention'] is not None:
                    changed = True
                    input_retention_policy(client=logs,
                                           log_group_name=module.params['log_group_name'],
                                           retention=module.params['retention'],
                                           module=module)
                    found_log_group['retentionInDays'] = module.params['retention']

        elif not found_log_group:
            changed = True
            found_log_group = create_log_group(client=logs,
                                               log_group_name=module.params['log_group_name'],
                                               kms_key_id=module.params['kms_key_id'],
                                               tags=module.params['tags'],
                                               retention=module.params['retention'],
                                               module=module)

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(found_log_group))

    elif state == 'absent':
        if found_log_group:
            changed = True
            delete_log_group(client=logs,
                             log_group_name=module.params['log_group_name'],
                             module=module)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: cloudwatch_metric_alarm_info
version_added: 5.0.0
short_description: Gather information about the alarms for the specified metric
description:
  - Retrieves the alarms for the specified metric.
author:
  - Mandar Vijay Kulkarni (@mandar242)
options:
  alarm_names:
    description:
      - The name of the metric.
    required: false
    type: list
    elements: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: describe the metric alarm based on metric name and namespace
  amazon.aws.cloudwatch_metric_alarm_info:
    cloudwatch_metric_alarm_info:
        alarm_names:
            - my-test-alarm-1
            - my-test-alarm-2

'''

# RETURN BLOCK IS WIP
RETURN = '''
'''


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


def _describe_alarms(connection, **params):
    paginator = connection.get_paginator('describe_alarms')
    return paginator.paginate(**params).build_full_result()


def describe_metric_alarms_info(connection, module):

    params = {}
    params['AlarmNames'] = module.params.get('alarm_names')

    try:
        describe_metric_alarms_info_response = _describe_alarms(connection, **params)['MetricAlarms']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe cloudwatch metric alarm')

    metric_alarms = []
    for response_list_item in describe_metric_alarms_info_response:
        metric_alarms.append(camel_dict_to_snake_dict(response_list_item))

    if len(metric_alarms) == 0:
        module.exit_json(msg='No metric alarms found for specified options')

    module.exit_json(metric_alarms=metric_alarms)


def main():

    argument_spec = dict(
        alarm_names=dict(type='list', elements='str', required=False),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    try:
        connection = module.client('cloudwatch', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    describe_metric_alarms_info(connection, module)


if __name__ == '__main__':
    main()

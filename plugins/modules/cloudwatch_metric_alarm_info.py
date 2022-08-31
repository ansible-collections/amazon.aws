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

RETURN = '''
metric_alarms:
    description: The gathered information about specified metric alarms.
    returned: when success
    type: list
    elements: dict
    contains:
        actions_enabled:
            description: Indicates whether actions should be executed during any changes to the alarm state.
            returned: always
            type: str
        alarm_arn:
            description: The Amazon Resource Name (ARN) of the alarm.
            returned: always
            type: str
        alarm_configuration_updated_timestamp:
            description: The time stamp of the last update to the alarm configuration.
            returned: always
            type: str
        alarm_description:
            description: The description of the alarm.
            returned: always
            type: str
        alarm_name:
            description: Unique name for the alarm.
            returned: always
            type: str
        comparison_operator:
            description: The arithmetic operation to use when comparing the specified statistic and threshold.
            returned: always
            type: str
        dimensions:
            description: The dimensions for the metric.
            returned: always
            type: list
            elements: dict
            contains:
                name:
                    description: The name of the dimension.
                    returned: always
                    type: str
                value:
                    description: The value of the dimension.
                    returned: always
                    type: str
        evaluation_period:
            description: The number of periods over which data is compared to the specified threshold.
            returned: always
            type: str
        insufficient_data_actions:
            description: The actions to execute when this alarm transitions to the INSUFFICIENT_DATA state from any other state.
            returned: always
            type: str
        metric_name:
            description: Name of the monitored metric (e.g. C(CPUUtilization)).
            returned: always
            type: str
        namespace:
            description:
                - Name of the appropriate namespace (C(AWS/EC2), C(System/Linux), etc.).
                - Determines the category it will appear under in CloudWatch.
            returned: always
            type: str
        ok_actions:
            description: The actions to execute when this alarm transitions to an OK state from any other state.
            returned: always
            type: str
        period:
            description:
                - The length, in seconds, used each time the metric specified in MetricName is evaluated.
                - Valid values are 10, 30, and any multiple of 60.
            returned: always
            type: int
        state_reason:
            description: An explanation for the alarm state, in text format.
            returned: always
            type: str
        state_reason_data:
            description: An explanation for the alarm state, in JSON format.
            returned: always
            type: str
        state_updated_timestamp:
            description: The time stamp of the last update to the alarm state.
            returned: always
            type: str
        state_value:
            description: The state value for the alarm.
            returned: always
            type: str
        statistic:
            description: The statistic for the metric associated with the alarm, other than percentile.
            returned: always
            type: str
        threshold:
            description: The value to compare with the specified statistic.
            returned: always
            type: str
        treat_missing_data:
            description: Sets how alarm is to handle missing data points.
            returned: always
            type: str
        unit:
            description: Unit used when storing the metric
            returned: always
            type: str
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

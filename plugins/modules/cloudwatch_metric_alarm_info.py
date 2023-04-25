#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
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
  alarm_name_prefix:
    description:
      - An alarm name prefix to retrieve information about alarms that have names that start with this prefix.
      - Can not be used with I(alarm_names).
    required: false
    type: str
  alarm_type:
    description:
      - Specify this to return metric alarms or composite alarms.
      - Module is defaulted to return metric alarms but can return composite alarms if I(alarm_type=CompositeAlarm).
    required: false
    type: str
    default: MetricAlarm
    choices: ['CompositeAlarm', 'MetricAlarm']
  children_of_alarm_name:
    description:
      - If specified returns information about the "children" alarms of the alarm name specified.
    required: false
    type: str
  parents_of_alarm_name:
    description:
      - If specified returns information about the "parent" alarms of the alarm name specified.
    required: false
    type: str
  state_value:
    description:
      - If specified returns information only about alarms that are currently in the particular state.
    required: false
    type: str
    choices: ['OK', 'ALARM', 'INSUFFICIENT_DATA']
  action_prefix:
    description:
      - This parameter can be used to filter the results of the operation to only those alarms that use a certain alarm action.
    required: false
    type: str

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: describe the metric alarm based on alarm names
  amazon.aws.cloudwatch_metric_alarm_info:
    alarm_names:
        - my-test-alarm-1
        - my-test-alarm-2

- name: describe the metric alarm based alarm names and state value
  amazon.aws.cloudwatch_metric_alarm_info:
    alarm_names:
        - my-test-alarm-1
        - my-test-alarm-2
    state_value: OK

- name: describe the metric alarm based alarm names prefix
  amazon.aws.cloudwatch_metric_alarm_info:
    alarm_name_prefix: my-test-
"""

RETURN = r"""
metric_alarms:
    description: The gathered information about specified metric alarms.
    returned: when success
    type: list
    elements: dict
    contains:
        alarm_name:
            description: Unique name for the alarm.
            returned: always
            type: str
        alarm_arn:
            description: The Amazon Resource Name (ARN) of the alarm.
            returned: always
            type: str
        alarm_description:
            description: The description of the alarm.
            returned: always
            type: str
        alarm_configuration_updated_timestamp:
            description: The time stamp of the last update to the alarm configuration.
            returned: always
            type: str
        actions_enabled:
            description: Indicates whether actions should be executed during any changes to the alarm state.
            returned: always
            type: bool
        ok_actions:
            description: The actions to execute when this alarm transitions to an OK state from any other state.
            returned: always
            type: list
            elements: str
        alarm_actions:
            description: The actions to execute when this alarm transitions to an ALARM state from any other state.
            returned: always
            type: list
            elements: str
        insufficient_data_actions:
            description: The actions to execute when this alarm transitions to an INSUFFICIENT_DATA state from any other state.
            returned: always
            type: list
            elements: str
        state_value:
            description: The state value for the alarm.
            returned: always
            type: str
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
        statistic:
            description: The statistic for the metric associated with the alarm, other than percentile.
            returned: always
            type: str
        extended_statistic:
            description: The percentile statistic for the metric associated with the alarm.
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
        period:
            description:
                - The length, in seconds, used each time the metric specified in MetricName is evaluated.
                - Valid values are 10, 30, and any multiple of 60.
            returned: always
            type: int
        unit:
            description: Unit used when storing the metric
            returned: always
            type: str
        evaluation_period:
            description: The number of periods over which data is compared to the specified threshold.
            returned: always
            type: int
        datapoints_to_alarm:
            description: The number of data points that must be breaching to trigger the alarm.
            returned: always
            type: int
        threshold:
            description: The value to compare with the specified statistic.
            returned: always
            type: float
        comparison_operator:
            description: The arithmetic operation to use when comparing the specified statistic and threshold.
            returned: always
            type: str
        treat_missing_data:
            description: Sets how alarm is to handle missing data points.
            returned: always
            type: str
        evaluate_low_sample_count_percentile:
            description:
              - Used only for alarms based on percentiles.
              - If I(ignore), the alarm state does not change during periods with too few data points to be statistically significant.
              - If I(evaluate) or this parameter is not used, the alarm is always evaluated and possibly changes state.
            returned: always
            type: str
        metrics:
            description: An array of MetricDataQuery structures, used in an alarm based on a metric math expression.
            returned: always
            type: list
            elements: dict
        threshold_metric_id:
            description: This is the ID of the ANOMALY_DETECTION_BAND function used as the threshold for the alarm.
            returned: always
            type: str
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


@AWSRetry.jittered_backoff(retries=10)
def _describe_alarms(connection, **params):
    paginator = connection.get_paginator("describe_alarms")
    return paginator.paginate(**params).build_full_result()


def describe_metric_alarms_info(connection, module):
    params = build_params(module)

    alarm_type_to_return = module.params.get("alarm_type")

    try:
        describe_metric_alarms_info_response = _describe_alarms(connection, **params)
        # describe_metric_alarms_info_response = describe_metric_alarms_info_response[alarm_type_to_return]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe cloudwatch metric alarm")

    result = []

    if alarm_type_to_return == "CompositeAlarm":
        for response_list_item in describe_metric_alarms_info_response["CompositeAlarms"]:
            result.append(camel_dict_to_snake_dict(response_list_item))
        module.exit_json(composite_alarms=result)

    for response_list_item in describe_metric_alarms_info_response["MetricAlarms"]:
        result.append(camel_dict_to_snake_dict(response_list_item))

    module.exit_json(metric_alarms=result)


def build_params(module):
    params = {}

    if module.params.get("alarm_names"):
        params["AlarmNames"] = module.params.get("alarm_names")

    if module.params.get("alarm_name_prefix"):
        params["AlarmNamePrefix"] = module.params.get("alarm_name_prefix")

    if module.params.get("children_of_alarm_name"):
        params["ChildrenOfAlarmName"] = module.params.get("children_of_alarm_name")

    if module.params.get("parents_of_alarm_name"):
        params["ParentsOfAlarmName"] = module.params.get("parents_of_alarm_name")

    if module.params.get("state_value"):
        params["StateValue"] = module.params.get("state_value")

    if module.params.get("action_prefix"):
        params["ActionPrefix"] = module.params.get("action_prefix")

    return params


def main():
    argument_spec = dict(
        alarm_names=dict(type="list", elements="str", required=False),
        alarm_name_prefix=dict(type="str", required=False),
        alarm_type=dict(type="str", choices=["CompositeAlarm", "MetricAlarm"], default="MetricAlarm", required=False),
        children_of_alarm_name=dict(type="str", required=False),
        parents_of_alarm_name=dict(type="str", required=False),
        state_value=dict(type="str", choices=["OK", "ALARM", "INSUFFICIENT_DATA"], required=False),
        action_prefix=dict(type="str", required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, mutually_exclusive=[["alarm_names", "alarm_name_prefix"]], supports_check_mode=True
    )

    try:
        connection = module.client("cloudwatch", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    describe_metric_alarms_info(connection, module)


if __name__ == "__main__":
    main()

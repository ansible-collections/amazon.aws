#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: cloudwatch_metric_alarm
short_description: "Create/update or delete AWS CloudWatch 'metric alarms'"
version_added: 5.0.0
description:
 - Can create or delete AWS CloudWatch metric alarms.
 - Metrics you wish to alarm on must already exist.
 - Prior to release 5.0.0 this module was called C(community.aws.ec2_metric_alarm).
   The usage did not change.
 - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - "Zacharie Eakin (@Zeekin)"
options:
    state:
        description:
          - Register or deregister the alarm.
        choices: ['present', 'absent']
        default: 'present'
        type: str
    name:
        description:
          - Unique name for the alarm.
        required: true
        type: str
    metric_name:
        description:
          - Name of the monitored metric (e.g. C(CPUUtilization)).
          - Metric must already exist.
        required: false
        type: str
        aliases: ['metric']
    metrics:
        description:
          - An array of MetricDataQuery structures that enable
            you to create an alarm based on the result of a metric math expression.
        type: list
        required: false
        version_added: "5.5.0"
        elements: dict
        default: []
        suboptions:
            id:
                description:
                  - A short name used to tie this object to the results in the response.
                type: str
                required: true
            metric_stat:
                description: The metric to be returned, along with statistics, period, and units.
                type: dict
                required: false
                suboptions:
                    metric:
                        description: The metric to return, including the metric name, namespace, and dimensions.
                        type: dict
                        required: false
                        suboptions:
                            namespace:
                                description: The namespace of the metric.
                                type: str
                                required: false
                            metric_name:
                                description: The name of the metric.
                                type: str
                                required: True
                            dimensions:
                                description: a name/value pair that is part of the identity of a metric.
                                type: list
                                elements: dict
                                required: false
                                suboptions:
                                    name:
                                        description: The name of the dimension.
                                        type: str
                                        required: True
                                    value:
                                        description: The value of the dimension.
                                        type: str
                                        required: True
                    period:
                        description: The granularity, in seconds, of the returned data points.
                        type: int
                        required: True
                    stat:
                        description: The statistic to return. It can include any CloudWatch statistic or extended statistic.
                        type: str
                        required: True
                    unit:
                        description: Unit to use when storing the metric.
                        type: str
                        required: false
            expression:
                description:
                  - This field can contain either a Metrics Insights query,
                    or a metric math expression to be performed on the returned data.
                type: str
                required: false
            label:
                description: A human-readable label for this metric or expression.
                type: str
                required: false
            return_data:
                description: This option indicates whether to return the timestamps and raw data values of this metric.
                type: bool
                required: false
            period:
                description: The granularity, in seconds, of the returned data points.
                type: int
                required: false
            account_id:
                description: The ID of the account where the metrics are located, if this is a cross-account alarm.
                type: str
                required: false
    namespace:
        description:
          - Name of the appropriate namespace (C(AWS/EC2), C(System/Linux), etc.), which determines the category it will appear under in CloudWatch.
        required: false
        type: str
    statistic:
        description:
          - Operation applied to the metric.
          - Works in conjunction with I(period) and I(evaluation_periods) to determine the comparison value.
        required: false
        choices: ['SampleCount','Average','Sum','Minimum','Maximum']
        type: str
    extended_statistic:
        description: The percentile statistic for the metric specified in the metric name.
        type: str
        required: false
        version_added: "5.5.0"
    comparison:
        description:
          - Determines how the threshold value is compared
        required: false
        type: str
        choices:
          - 'GreaterThanOrEqualToThreshold'
          - 'GreaterThanThreshold'
          - 'LessThanThreshold'
          - 'LessThanOrEqualToThreshold'
    threshold:
        description:
          - Sets the min/max bound for triggering the alarm.
        required: false
        type: float
    period:
        description:
          - The time (in seconds) between metric evaluations.
        required: false
        type: int
    evaluation_periods:
        description:
          - The number of times in which the metric is evaluated before final calculation.
        required: false
        type: int
    unit:
        description:
          - The threshold's unit of measurement.
        required: false
        type: str
        choices:
          - 'Seconds'
          - 'Microseconds'
          - 'Milliseconds'
          - 'Bytes'
          - 'Kilobytes'
          - 'Megabytes'
          - 'Gigabytes'
          - 'Terabytes'
          - 'Bits'
          - 'Kilobits'
          - 'Megabits'
          - 'Gigabits'
          - 'Terabits'
          - 'Percent'
          - 'Count'
          - 'Bytes/Second'
          - 'Kilobytes/Second'
          - 'Megabytes/Second'
          - 'Gigabytes/Second'
          - 'Terabytes/Second'
          - 'Bits/Second'
          - 'Kilobits/Second'
          - 'Megabits/Second'
          - 'Gigabits/Second'
          - 'Terabits/Second'
          - 'Count/Second'
          - 'None'
    description:
        description:
          - A longer description of the alarm.
        required: false
        type: str
    dimensions:
        description:
          - A dictionary describing which metric the alarm is applied to.
          - 'For more information see the AWS documentation:'
          - U(https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#Dimension)
        required: false
        type: dict
    alarm_actions:
        description:
          - A list of the names action(s) taken when the alarm is in the C(alarm) status, denoted as Amazon Resource Name(s).
        required: false
        type: list
        elements: str
        default: []
    insufficient_data_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the C(insufficient_data) status.
        required: false
        type: list
        elements: str
        default: []
    ok_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the C(ok) status, denoted as Amazon Resource Name(s).
        required: false
        type: list
        elements: str
        default: []
    treat_missing_data:
        description:
          - Sets how the alarm handles missing data points.
        required: false
        type: str
        choices:
          - 'breaching'
          - 'notBreaching'
          - 'ignore'
          - 'missing'
        default: 'missing'
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

RETURN = r""" # """

EXAMPLES = r"""
- name: create alarm
  amazon.aws.cloudwatch_metric_alarm:
    state: present
    region: ap-southeast-2
    name: "cpu-low"
    metric_name: "CPUUtilization"
    namespace: "AWS/EC2"
    statistic: Average
    comparison: "LessThanOrEqualToThreshold"
    threshold: 5.0
    period: 300
    evaluation_periods: 3
    unit: "Percent"
    description: "This will alarm when a instance's CPU usage average is lower than 5% for 15 minutes"
    dimensions: {'InstanceId': 'i-XXX'}
    alarm_actions: ["action1", "action2"]

- name: create alarm with metrics
  amazon.aws.cloudwatch_metric_alarm:
    state: present
    region: ap-southeast-2
    name: "cpu-low"
    metrics:
      - id: 'CPU'
        metric_stat:
          metric:
            dimensions:
              name: "InstanceId"
              value: "i-xx"
            metric_name: "CPUUtilization"
            namespace: "AWS/EC2"
          period: "300"
          stat: "Average"
          unit: "Percent"
        return_data: false
    alarm_actions: ["action1", "action2"]

- name: Create an alarm to recover a failed instance
  amazon.aws.cloudwatch_metric_alarm:
    state: present
    region: us-west-1
    name: "recover-instance"
    metric: "StatusCheckFailed_System"
    namespace: "AWS/EC2"
    statistic: "Minimum"
    comparison: "GreaterThanOrEqualToThreshold"
    threshold: 1.0
    period: 60
    evaluation_periods: 2
    unit: "Count"
    description: "This will recover an instance when it fails"
    dimensions: {"InstanceId":'i-XXX'}
    alarm_actions: ["arn:aws:automate:us-west-1:ec2:recover"]
"""

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # protected by AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def create_metric_alarm(connection, module, params):
    alarms = connection.describe_alarms(AlarmNames=[params["AlarmName"]])
    if params.get("Dimensions"):
        if not isinstance(params["Dimensions"], list):
            fixed_dimensions = []
            for key, value in params["Dimensions"].items():
                fixed_dimensions.append({"Name": key, "Value": value})
            params["Dimensions"] = fixed_dimensions

    if not alarms["MetricAlarms"]:
        try:
            if not module.check_mode:
                connection.put_metric_alarm(**params)
            changed = True
        except ClientError as e:
            module.fail_json_aws(e)

    else:
        changed = False
        alarm = alarms["MetricAlarms"][0]

        # Workaround for alarms created before TreatMissingData was introduced
        if "TreatMissingData" not in alarm.keys():
            alarm["TreatMissingData"] = "missing"

        # Exclude certain props from change detection
        for key in [
            "ActionsEnabled",
            "StateValue",
            "StateReason",
            "StateReasonData",
            "StateUpdatedTimestamp",
            "StateTransitionedTimestamp",
            "AlarmArn",
            "AlarmConfigurationUpdatedTimestamp",
            "Metrics",
        ]:
            alarm.pop(key, None)
        if alarm != params:
            changed = True
            alarm = params

        try:
            if changed:
                if not module.check_mode:
                    connection.put_metric_alarm(**alarm)
        except ClientError as e:
            module.fail_json_aws(e)

    try:
        alarms = connection.describe_alarms(AlarmNames=[params["AlarmName"]])
    except ClientError as e:
        module.fail_json_aws(e)

    result = {}
    if alarms["MetricAlarms"]:
        if alarms["MetricAlarms"][0].get("Metrics"):
            metric_list = []
            for metric_element in alarms["MetricAlarms"][0]["Metrics"]:
                metric_list.append(camel_dict_to_snake_dict(metric_element))
            alarms["MetricAlarms"][0]["Metrics"] = metric_list
        result = alarms["MetricAlarms"][0]

    module.exit_json(
        changed=changed,
        name=result.get("AlarmName"),
        actions_enabled=result.get("ActionsEnabled"),
        alarm_actions=result.get("AlarmActions"),
        alarm_arn=result.get("AlarmArn"),
        comparison=result.get("ComparisonOperator"),
        description=result.get("AlarmDescription"),
        dimensions=result.get("Dimensions"),
        evaluation_periods=result.get("EvaluationPeriods"),
        insufficient_data_actions=result.get("InsufficientDataActions"),
        last_updated=result.get("AlarmConfigurationUpdatedTimestamp"),
        metric=result.get("MetricName"),
        metric_name=result.get("MetricName"),
        metrics=result.get("Metrics"),
        namespace=result.get("Namespace"),
        ok_actions=result.get("OKActions"),
        period=result.get("Period"),
        state_reason=result.get("StateReason"),
        state_value=result.get("StateValue"),
        statistic=result.get("Statistic"),
        threshold=result.get("Threshold"),
        treat_missing_data=result.get("TreatMissingData"),
        unit=result.get("Unit"),
    )


def delete_metric_alarm(connection, module, params):
    alarms = connection.describe_alarms(AlarmNames=[params["AlarmName"]])

    if alarms["MetricAlarms"]:
        try:
            if not module.check_mode:
                connection.delete_alarms(AlarmNames=[params["AlarmName"]])
            module.exit_json(changed=True)
        except ClientError as e:
            module.fail_json_aws(e)
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = dict(
        name=dict(required=True, type="str"),
        metric_name=dict(type="str", aliases=["metric"]),
        namespace=dict(type="str"),
        statistic=dict(type="str", choices=["SampleCount", "Average", "Sum", "Minimum", "Maximum"]),
        comparison=dict(
            type="str",
            choices=[
                "LessThanOrEqualToThreshold",
                "LessThanThreshold",
                "GreaterThanThreshold",
                "GreaterThanOrEqualToThreshold",
            ],
        ),
        threshold=dict(type="float"),
        period=dict(type="int"),
        unit=dict(
            type="str",
            choices=[
                "Seconds",
                "Microseconds",
                "Milliseconds",
                "Bytes",
                "Kilobytes",
                "Megabytes",
                "Gigabytes",
                "Terabytes",
                "Bits",
                "Kilobits",
                "Megabits",
                "Gigabits",
                "Terabits",
                "Percent",
                "Count",
                "Bytes/Second",
                "Kilobytes/Second",
                "Megabytes/Second",
                "Gigabytes/Second",
                "Terabytes/Second",
                "Bits/Second",
                "Kilobits/Second",
                "Megabits/Second",
                "Gigabits/Second",
                "Terabits/Second",
                "Count/Second",
                "None",
            ],
        ),
        evaluation_periods=dict(type="int"),
        extended_statistic=dict(type="str"),
        description=dict(type="str"),
        dimensions=dict(type="dict"),
        alarm_actions=dict(type="list", default=[], elements="str"),
        insufficient_data_actions=dict(type="list", default=[], elements="str"),
        ok_actions=dict(type="list", default=[], elements="str"),
        treat_missing_data=dict(
            type="str", choices=["breaching", "notBreaching", "ignore", "missing"], default="missing"
        ),
        state=dict(default="present", choices=["present", "absent"]),
        metrics=dict(type="list", elements="dict", default=[]),
    )

    mutually_exclusive = [
        ["metric_name", "metrics"],
        ["dimensions", "metrics"],
        ["period", "metrics"],
        ["namespace", "metrics"],
        ["statistic", "metrics"],
        ["extended_statistic", "metrics"],
        ["unit", "metrics"],
        ["statistic", "extended_statistic"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
    )

    state = module.params.get("state")

    params = dict()
    params["AlarmName"] = module.params.get("name")
    params["MetricName"] = module.params.get("metric_name")
    params["Namespace"] = module.params.get("namespace")
    params["Statistic"] = module.params.get("statistic")
    params["ComparisonOperator"] = module.params.get("comparison")
    params["Threshold"] = module.params.get("threshold")
    params["Period"] = module.params.get("period")
    params["EvaluationPeriods"] = module.params.get("evaluation_periods")
    if module.params.get("unit"):
        params["Unit"] = module.params.get("unit")
    params["AlarmDescription"] = module.params.get("description")
    params["Dimensions"] = module.params.get("dimensions")
    params["AlarmActions"] = module.params.get("alarm_actions", [])
    params["InsufficientDataActions"] = module.params.get("insufficient_data_actions", [])
    params["OKActions"] = module.params.get("ok_actions", [])
    params["TreatMissingData"] = module.params.get("treat_missing_data")
    if module.params.get("metrics"):
        params["Metrics"] = snake_dict_to_camel_dict(module.params["metrics"], capitalize_first=True)
    if module.params.get("extended_statistic"):
        params["ExtendedStatistic"] = module.params.get("extended_statistic")

    for key, value in list(params.items()):
        if value is None:
            del params[key]

    connection = module.client("cloudwatch")

    if state == "present":
        create_metric_alarm(connection, module, params)
    elif state == "absent":
        delete_metric_alarm(connection, module, params)


if __name__ == "__main__":
    main()

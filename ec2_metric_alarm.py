#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_metric_alarm
short_description: "Create/update or delete AWS Cloudwatch 'metric alarms'"
version_added: 1.0.0
description:
 - Can create or delete AWS metric alarms.
 - Metrics you wish to alarm on must already exist.
author: "Zacharie Eakin (@Zeekin)"
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
    metric:
        description:
          - Name of the monitored metric (e.g. C(CPUUtilization)).
          - Metric must already exist.
        required: false
        type: str
    namespace:
        description:
          - Name of the appropriate namespace (C(AWS/EC2), C(System/Linux), etc.), which determines the category it will appear under in cloudwatch.
        required: false
        type: str
    statistic:
        description:
          - Operation applied to the metric.
          - Works in conjunction with I(period) and I(evaluation_periods) to determine the comparison value.
        required: false
        choices: ['SampleCount','Average','Sum','Minimum','Maximum']
        type: str
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
    insufficient_data_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the C(insufficient_data) status.
        required: false
        type: list
        elements: str
    ok_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the C(ok) status, denoted as Amazon Resource Name(s).
        required: false
        type: list
        elements: str
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
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
  - name: create alarm
    community.aws.ec2_metric_alarm:
      state: present
      region: ap-southeast-2
      name: "cpu-low"
      metric: "CPUUtilization"
      namespace: "AWS/EC2"
      statistic: Average
      comparison: "LessThanOrEqualToThreshold"
      threshold: 5.0
      period: 300
      evaluation_periods: 3
      unit: "Percent"
      description: "This will alarm when a instance's CPU usage average is lower than 5% for 15 minutes"
      dimensions: {'InstanceId':'i-XXX'}
      alarm_actions: ["action1","action2"]

  - name: Create an alarm to recover a failed instance
    community.aws.ec2_metric_alarm:
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

'''

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # protected by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def create_metric_alarm(connection, module, params):
    alarms = connection.describe_alarms(AlarmNames=[params['AlarmName']])

    if not isinstance(params['Dimensions'], list):
        fixed_dimensions = []
        for key, value in params['Dimensions'].items():
            fixed_dimensions.append({'Name': key, 'Value': value})
        params['Dimensions'] = fixed_dimensions

    if not alarms['MetricAlarms']:
        try:
            if not module.check_mode:
                connection.put_metric_alarm(**params)
            changed = True
        except ClientError as e:
            module.fail_json_aws(e)

    else:
        changed = False
        alarm = alarms['MetricAlarms'][0]

        # Workaround for alarms created before TreatMissingData was introduced
        if 'TreatMissingData' not in alarm.keys():
            alarm['TreatMissingData'] = 'missing'

        for key in ['ActionsEnabled', 'StateValue', 'StateReason',
                    'StateReasonData', 'StateUpdatedTimestamp',
                    'AlarmArn', 'AlarmConfigurationUpdatedTimestamp']:
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
        alarms = connection.describe_alarms(AlarmNames=[params['AlarmName']])
    except ClientError as e:
        module.fail_json_aws(e)

    result = {}
    if alarms['MetricAlarms']:
        result = alarms['MetricAlarms'][0]

    module.exit_json(changed=changed,
                     name=result.get('AlarmName'),
                     actions_enabled=result.get('ActionsEnabled'),
                     alarm_actions=result.get('AlarmActions'),
                     alarm_arn=result.get('AlarmArn'),
                     comparison=result.get('ComparisonOperator'),
                     description=result.get('AlarmDescription'),
                     dimensions=result.get('Dimensions'),
                     evaluation_periods=result.get('EvaluationPeriods'),
                     insufficient_data_actions=result.get('InsufficientDataActions'),
                     last_updated=result.get('AlarmConfigurationUpdatedTimestamp'),
                     metric=result.get('MetricName'),
                     namespace=result.get('Namespace'),
                     ok_actions=result.get('OKActions'),
                     period=result.get('Period'),
                     state_reason=result.get('StateReason'),
                     state_value=result.get('StateValue'),
                     statistic=result.get('Statistic'),
                     threshold=result.get('Threshold'),
                     treat_missing_data=result.get('TreatMissingData'),
                     unit=result.get('Unit'))


def delete_metric_alarm(connection, module, params):
    alarms = connection.describe_alarms(AlarmNames=[params['AlarmName']])

    if alarms['MetricAlarms']:
        try:
            if not module.check_mode:
                connection.delete_alarms(AlarmNames=[params['AlarmName']])
            module.exit_json(changed=True)
        except (ClientError) as e:
            module.fail_json_aws(e)
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        metric=dict(type='str'),
        namespace=dict(type='str'),
        statistic=dict(type='str', choices=['SampleCount', 'Average', 'Sum', 'Minimum', 'Maximum']),
        comparison=dict(type='str', choices=['LessThanOrEqualToThreshold', 'LessThanThreshold', 'GreaterThanThreshold',
                                             'GreaterThanOrEqualToThreshold']),
        threshold=dict(type='float'),
        period=dict(type='int'),
        unit=dict(type='str', choices=['Seconds', 'Microseconds', 'Milliseconds', 'Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes',
                                       'Terabytes', 'Bits', 'Kilobits', 'Megabits', 'Gigabits', 'Terabits', 'Percent', 'Count',
                                       'Bytes/Second', 'Kilobytes/Second', 'Megabytes/Second', 'Gigabytes/Second',
                                       'Terabytes/Second', 'Bits/Second', 'Kilobits/Second', 'Megabits/Second', 'Gigabits/Second',
                                       'Terabits/Second', 'Count/Second', 'None']),
        evaluation_periods=dict(type='int'),
        description=dict(type='str'),
        dimensions=dict(type='dict', default={}),
        alarm_actions=dict(type='list', default=[], elements='str'),
        insufficient_data_actions=dict(type='list', default=[], elements='str'),
        ok_actions=dict(type='list', default=[], elements='str'),
        treat_missing_data=dict(type='str', choices=['breaching', 'notBreaching', 'ignore', 'missing'], default='missing'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    state = module.params.get('state')

    params = dict()
    params['AlarmName'] = module.params.get('name')
    params['MetricName'] = module.params.get('metric')
    params['Namespace'] = module.params.get('namespace')
    params['Statistic'] = module.params.get('statistic')
    params['ComparisonOperator'] = module.params.get('comparison')
    params['Threshold'] = module.params.get('threshold')
    params['Period'] = module.params.get('period')
    params['EvaluationPeriods'] = module.params.get('evaluation_periods')
    if module.params.get('unit'):
        params['Unit'] = module.params.get('unit')
    params['AlarmDescription'] = module.params.get('description')
    params['Dimensions'] = module.params.get('dimensions')
    params['AlarmActions'] = module.params.get('alarm_actions', [])
    params['InsufficientDataActions'] = module.params.get('insufficient_data_actions', [])
    params['OKActions'] = module.params.get('ok_actions', [])
    params['TreatMissingData'] = module.params.get('treat_missing_data')

    connection = module.client('cloudwatch')

    if state == 'present':
        create_metric_alarm(connection, module, params)
    elif state == 'absent':
        delete_metric_alarm(connection, module, params)


if __name__ == '__main__':
    main()

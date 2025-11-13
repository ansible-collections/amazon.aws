#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025
from __future__ import absolute_import, division, print_function
__metaclass__ = type

# Import statements must come before DOCUMENTATION
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleAWSModule

DOCUMENTATION = r'''
---
module: ec2_health_report
short_description: Generate health reports for EC2 instances
description:
  - Collects health metrics for EC2 instances including CPU utilization, status checks, and instance information.
  - Can send the report via email or return as structured data.
  - Supports filtering instances by tags, state, and instance type.
version_added: "8.0.0"
author:
  - "Your Name (@yourgithub)"
options:
  region:
    description:
      - The AWS region to query for EC2 instances.
    type: str
    required: false
  filters:
    description:
      - Filters to apply when gathering EC2 instances.
      - Uses the same filter format as ec2_instance_info module.
    type: dict
    required: false
    default: {}
  metric_period:
    description:
      - CloudWatch metric period in seconds.
      - Must be 60, 300, 3600, 86400, or a multiple of 60.
    type: int
    required: false
    default: 300
  metric_duration:
    description:
      - How far back to look for metrics in hours.
    type: int
    required: false
    default: 1
  include_metrics:
    description:
      - List of CloudWatch metrics to include in the report.
      - Valid options are CPUUtilization, NetworkIn, NetworkOut, DiskReadBytes, DiskWriteBytes, StatusCheckFailed.
    type: list
    elements: str
    required: false
    default: ['CPUUtilization', 'StatusCheckFailed']
  send_email:
    description:
      - Whether to send the report via email.
    type: bool
    required: false
    default: false
  email_config:
    description:
      - Email configuration when send_email is true.
    type: dict
    required: false
    suboptions:
      smtp_host:
        description: SMTP server hostname.
        type: str
        required: true
      smtp_port:
        description: SMTP server port.
        type: int
        required: false
        default: 587
      smtp_username:
        description: SMTP username for authentication.
        type: str
        required: true
      smtp_password:
        description: SMTP password for authentication.
        type: str
        required: true
        no_log: true
      from_addr:
        description: Email sender address.
        type: str
        required: true
      to_addrs:
        description: List of recipient email addresses.
        type: list
        elements: str
        required: true
      subject:
        description: Email subject line.
        type: str
        required: false
        default: "AWS EC2 Health Report"
      use_tls:
        description: Use TLS for SMTP connection.
        type: bool
        required: false
        default: true
  format:
    description:
      - Output format for the report.
    type: str
    choices: ['json', 'text', 'html']
    required: false
    default: 'json'
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
requirements:
  - python >= 3.6
  - boto3 >= 1.26.0
  - botocore >= 1.29.0
notes:
  - If parameters are not set within the module, the following environment variables can be used in decreasing order of precedence
    C(AWS_URL) or C(EC2_URL), C(AWS_PROFILE) or C(AWS_DEFAULT_PROFILE), C(AWS_ACCESS_KEY_ID) or C(EC2_ACCESS_KEY),
    C(AWS_SECRET_ACCESS_KEY) or C(EC2_SECRET_KEY), C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN), C(AWS_REGION) or C(EC2_REGION),
    C(AWS_CA_BUNDLE)
  - Credentials can also be set by using the C(~/.aws/credentials) file.
'''

EXAMPLES = r'''
- name: Generate health report for all running instances
  community.aws.ec2_health_report:
    region: us-east-1
    filters:
      instance-state-name: running
  register: health_report

- name: Generate detailed health report with multiple metrics
  community.aws.ec2_health_report:
    region: us-west-2
    include_metrics:
      - CPUUtilization
      - NetworkIn
      - NetworkOut
      - StatusCheckFailed
    metric_duration: 24
    format: html
  register: detailed_report

- name: Generate and email health report
  community.aws.ec2_health_report:
    region: eu-west-1
    send_email: true
    email_config:
      smtp_host: smtp.gmail.com
      smtp_port: 587
      smtp_username: monitoring@example.com
      smtp_password: "{{ vault_smtp_password }}"
      from_addr: monitoring@example.com
      to_addrs:
        - ops@example.com
        - admin@example.com
      subject: "Daily AWS EC2 Health Report"
      use_tls: true
    format: html

- name: Filter instances by tag
  community.aws.ec2_health_report:
    region: ap-southeast-1
    filters:
      tag:Environment: production
      instance-state-name: running
  register: prod_health
'''

RETURN = r'''
report:
  description: The generated health report data.
  returned: always
  type: dict
  contains:
    timestamp:
      description: ISO 8601 timestamp when report was generated.
      type: str
      sample: "2025-11-13T10:30:00Z"
    region:
      description: AWS region queried.
      type: str
      sample: "us-east-1"
    instance_count:
      description: Total number of instances in the report.
      type: int
      sample: 5
    instances:
      description: List of instance health data.
      type: list
      elements: dict
      contains:
        instance_id:
          description: EC2 instance ID.
          type: str
          sample: "i-1234567890abcdef0"
        instance_type:
          description: Instance type.
          type: str
          sample: "t3.medium"
        state:
          description: Current instance state.
          type: str
          sample: "running"
        launch_time:
          description: Instance launch time.
          type: str
          sample: "2025-01-15T08:30:00Z"
        private_ip:
          description: Private IP address.
          type: str
          sample: "10.0.1.25"
        public_ip:
          description: Public IP address if available.
          type: str
          sample: "54.123.45.67"
        tags:
          description: Instance tags.
          type: dict
          sample: {"Name": "web-server-01", "Environment": "production"}
        metrics:
          description: CloudWatch metrics for the instance.
          type: dict
          sample: {"CPUUtilization": {"average": 45.2, "maximum": 78.5}}
email_sent:
  description: Whether email was successfully sent.
  returned: when send_email is true
  type: bool
  sample: true
formatted_report:
  description: The formatted report content.
  returned: when format is text or html
  type: str
'''


def get_ec2_instances(module, client):
    """Retrieve EC2 instances based on filters."""
    try:
        filters_list = []
        if module.params.get('filters'):
            for key, value in module.params['filters'].items():
                if key.startswith('tag:'):
                    filters_list.append({'Name': key, 'Values': [value]})
                else:
                    filters_list.append({'Name': key, 'Values': [value] if isinstance(value, str) else value})

        paginator = client.get_paginator('describe_instances')
        page_iterator = paginator.paginate(Filters=filters_list)

        instances = []
        for page in page_iterator:
            for reservation in page['Reservations']:
                instances.extend(reservation['Instances'])

        return instances
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe EC2 instances")


def get_cloudwatch_metrics(module, cloudwatch_client, instance_id, metric_name, namespace='AWS/EC2'):
    """Retrieve CloudWatch metrics for an instance."""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=module.params['metric_duration'])

        response = cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=module.params['metric_period'],
            Statistics=['Average', 'Maximum', 'Minimum']
        )

        datapoints = response.get('Datapoints', [])
        if not datapoints:
            return None

        avg = sum(d['Average'] for d in datapoints) / len(datapoints)
        max_val = max(d['Maximum'] for d in datapoints)
        min_val = min(d['Minimum'] for d in datapoints)

        return {
            'average': round(avg, 2),
            'maximum': round(max_val, 2),
            'minimum': round(min_val, 2),
            'datapoints': len(datapoints)
        }
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.warn(f"Failed to get metric {metric_name} for instance {instance_id}: {str(e)}")
        return None


def collect_instance_health(module, ec2_client, cloudwatch_client, instance):
    """Collect health information for a single instance."""
    instance_id = instance['InstanceId']

    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

    health_data = {
        'instance_id': instance_id,
        'instance_type': instance['InstanceType'],
        'state': instance['State']['Name'],
        'launch_time': instance['LaunchTime'].isoformat(),
        'private_ip': instance.get('PrivateIpAddress', 'N/A'),
        'public_ip': instance.get('PublicIpAddress', 'N/A'),
        'availability_zone': instance['Placement']['AvailabilityZone'],
        'tags': tags,
        'metrics': {}
    }

    for metric_name in module.params['include_metrics']:
        metric_data = get_cloudwatch_metrics(module, cloudwatch_client, instance_id, metric_name)
        if metric_data:
            health_data['metrics'][metric_name] = metric_data

    return health_data


def format_report_text(report_data):
    """Format report as plain text."""
    lines = [
        "=" * 70,
        "AWS EC2 HEALTH REPORT",
        "=" * 70,
        f"Generated: {report_data['timestamp']}",
        f"Region: {report_data['region']}",
        f"Total Instances: {report_data['instance_count']}",
        "=" * 70,
        ""
    ]

    for instance in report_data['instances']:
        lines.extend([
            f"Instance ID: {instance['instance_id']}",
            f"  Name: {instance['tags'].get('Name', 'N/A')}",
            f"  Type: {instance['instance_type']}",
            f"  State: {instance['state']}",
            f"  Private IP: {instance['private_ip']}",
            f"  Public IP: {instance['public_ip']}",
            f"  Launch Time: {instance['launch_time']}",
            "  Metrics:",
        ])

        for metric_name, metric_data in instance['metrics'].items():
            lines.append(f"    {metric_name}: Avg={metric_data['average']}, Max={metric_data['maximum']}, Min={metric_data['minimum']}")

        lines.append("")

    return "\n".join(lines)


def format_report_html(report_data):
    """Format report as HTML."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #232F3E; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #232F3E; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .metric {{ background-color: #e8f4f8; padding: 5px; margin: 3px 0; }}
            .healthy {{ color: green; }}
            .warning {{ color: orange; }}
            .critical {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>AWS EC2 Health Report</h1>
        <p><strong>Generated:</strong> {report_data['timestamp']}</p>
        <p><strong>Region:</strong> {report_data['region']}</p>
        <p><strong>Total Instances:</strong> {report_data['instance_count']}</p>

        <table>
            <tr>
                <th>Instance ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>State</th>
                <th>IPs</th>
                <th>Metrics</th>
            </tr>
    """

    for instance in report_data['instances']:
        name = instance['tags'].get('Name', 'N/A')
        metrics_html = ""

        for metric_name, metric_data in instance['metrics'].items():
            cpu_class = ""
            if metric_name == "CPUUtilization":
                if metric_data['average'] > 80:
                    cpu_class = "critical"
                elif metric_data['average'] > 60:
                    cpu_class = "warning"
                else:
                    cpu_class = "healthy"

            metrics_html += f'<div class="metric {cpu_class}">{metric_name}: Avg={metric_data["average"]}%</div>'

        html += f"""
            <tr>
                <td>{instance['instance_id']}</td>
                <td>{name}</td>
                <td>{instance['instance_type']}</td>
                <td>{instance['state']}</td>
                <td>Private: {instance['private_ip']}<br>Public: {instance['public_ip']}</td>
                <td>{metrics_html}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html


def send_email_report(module, report_content, report_format):
    """Send the report via email."""
    email_config = module.params['email_config']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_config['subject']
        msg['From'] = email_config['from_addr']
        msg['To'] = ', '.join(email_config['to_addrs'])

        if report_format == 'html':
            part = MIMEText(report_content, 'html')
        else:
            part = MIMEText(report_content, 'plain')

        msg.attach(part)

        server = smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port'])
        if email_config['use_tls']:
            server.starttls()

        server.login(email_config['smtp_username'], email_config['smtp_password'])
        server.sendmail(email_config['from_addr'], email_config['to_addrs'], msg.as_string())
        server.quit()

        return True
    except Exception as e:
        module.fail_json(msg=f"Failed to send email: {str(e)}")


def main():
    argument_spec = dict(
        region=dict(type='str', required=False),
        filters=dict(type='dict', default={}),
        metric_period=dict(type='int', default=300),
        metric_duration=dict(type='int', default=1),
        include_metrics=dict(
            type='list',
            elements='str',
            default=['CPUUtilization', 'StatusCheckFailed'],
            choices=['CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadBytes', 'DiskWriteBytes', 'StatusCheckFailed']
        ),
        send_email=dict(type='bool', default=False),
        email_config=dict(
            type='dict',
            options=dict(
                smtp_host=dict(type='str', required=True),
                smtp_port=dict(type='int', default=587),
                smtp_username=dict(type='str', required=True),
                smtp_password=dict(type='str', required=True, no_log=True),
                from_addr=dict(type='str', required=True),
                to_addrs=dict(type='list', elements='str', required=True),
                subject=dict(type='str', default="AWS EC2 Health Report"),
                use_tls=dict(type='bool', default=True)
            )
        ),
        format=dict(type='str', choices=['json', 'text', 'html'], default='json')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('send_email', True, ['email_config'])
        ]
    )

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode - no actions performed")

    region = module.params.get('region') or module.region

    try:
        ec2_client = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
        cloudwatch_client = module.client('cloudwatch', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    instances = get_ec2_instances(module, ec2_client)

    if not instances:
        module.exit_json(
            changed=False,
            report={
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'region': region,
                'instance_count': 0,
                'instances': []
            },
            msg="No instances found matching the filters"
        )

    health_data = []
    for instance in instances:
        instance_health = collect_instance_health(module, ec2_client, cloudwatch_client, instance)
        health_data.append(instance_health)

    report_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'region': region,
        'instance_count': len(health_data),
        'instances': health_data
    }

    result = {
        'changed': False,
        'report': report_data
    }

    report_format = module.params['format']
    if report_format == 'text':
        result['formatted_report'] = format_report_text(report_data)
    elif report_format == 'html':
        result['formatted_report'] = format_report_html(report_data)

    if module.params['send_email']:
        if report_format == 'json':
            report_content = format_report_html(report_data)
            actual_format = 'html'
        else:
            report_content = result['formatted_report']
            actual_format = report_format

        email_sent = send_email_report(module, report_content, actual_format)
        result['email_sent'] = email_sent
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_target_group
version_added: 1.0.0
short_description: Manage a target group for an Application or Network load balancer
description:
    - Manage an AWS Elastic Load Balancer target group. See
      U(https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html) or
      U(https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-target-groups.html) for details.
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  deregistration_delay_timeout:
    description:
      - The amount time for Elastic Load Balancing to wait before changing the state of a deregistering target from draining to unused.
        The range is 0-3600 seconds.
    type: int
  health_check_protocol:
    description:
      - The protocol the load balancer uses when performing health checks on targets.
    required: false
    choices: [ 'http', 'https', 'tcp', 'tls', 'udp', 'tcp_udp', 'HTTP', 'HTTPS', 'TCP', 'TLS', 'UDP', 'TCP_UDP']
    type: str
  health_check_port:
    description:
      - The port the load balancer uses when performing health checks on targets.
        Can be set to 'traffic-port' to match target port.
      - When not defined will default to the port on which each target receives traffic from the load balancer.
    required: false
    type: str
  health_check_path:
    description:
      - The ping path that is the destination on the targets for health checks. The path must be defined in order to set a health check.
      - Requires the I(health_check_protocol) parameter to be set.
    required: false
    type: str
  health_check_interval:
    description:
      - The approximate amount of time, in seconds, between health checks of an individual target.
    required: false
    type: int
  health_check_timeout:
    description:
      - The amount of time, in seconds, during which no response from a target means a failed health check.
    required: false
    type: int
  healthy_threshold_count:
    description:
      - The number of consecutive health checks successes required before considering an unhealthy target healthy.
    required: false
    type: int
  modify_targets:
    description:
      - Whether or not to alter existing targets in the group to match what is passed with the module
    required: false
    default: yes
    type: bool
  name:
    description:
      - The name of the target group.
    required: true
    type: str
  port:
    description:
      - The port on which the targets receive traffic. This port is used unless you specify a port override when registering the target. Required if
        I(state) is C(present).
    required: false
    type: int
  protocol:
    description:
      - The protocol to use for routing traffic to the targets. Required when I(state) is C(present).
    required: false
    choices: [ 'http', 'https', 'tcp', 'tls', 'udp', 'tcp_udp', 'HTTP', 'HTTPS', 'TCP', 'TLS', 'UDP', 'TCP_UDP']
    type: str
  purge_tags:
    description:
      - If yes, existing tags will be purged from the resource to match exactly what is defined by I(tags) parameter. If the tag parameter is not set then
        tags will not be modified.
    required: false
    default: yes
    type: bool
  state:
    description:
      - Create or destroy the target group.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  stickiness_enabled:
    description:
      - Indicates whether sticky sessions are enabled.
    type: bool
  stickiness_lb_cookie_duration:
    description:
      - The time period, in seconds, during which requests from a client should be routed to the same target. After this time period expires, the load
        balancer-generated cookie is considered stale. The range is 1 second to 1 week (604800 seconds).
    type: int
  stickiness_type:
    description:
      - The type of sticky sessions.
      - If not set AWS will default to C(lb_cookie) for Application Load Balancers or C(source_ip) for Network Load Balancers.
    type: str
  successful_response_codes:
    description:
      - The HTTP codes to use when checking for a successful response from a target.
      - Accepts multiple values (for example, "200,202") or a range of values (for example, "200-299").
      - Requires the I(health_check_protocol) parameter to be set.
    required: false
    type: str
  tags:
    description:
      - A dictionary of one or more tags to assign to the target group.
    required: false
    type: dict
  target_type:
    description:
      - The type of target that you must specify when registering targets with this target group. The possible values are
        C(instance) (targets are specified by instance ID), C(ip) (targets are specified by IP address) or C(lambda) (target is specified by ARN).
        Note that you can't specify targets for a target group using more than one type. Target type lambda only accept one target. When more than
        one target is specified, only the first one is used. All additional targets are ignored.
        If the target type is ip, specify IP addresses from the subnets of the virtual private cloud (VPC) for the target
        group, the RFC 1918 range (10.0.0.0/8, 172.16.0.0/12, and 192.168.0.0/16), and the RFC 6598 range (100.64.0.0/10).
        You can't specify publicly routable IP addresses.
      - The default behavior is C(instance).
    required: false
    choices: ['instance', 'ip', 'lambda']
    type: str
  targets:
    description:
      - A list of targets to assign to the target group. This parameter defaults to an empty list. Unless you set the 'modify_targets' parameter then
        all existing targets will be removed from the group. The list should be an Id and a Port parameter. See the Examples for detail.
    required: false
    type: list
    elements: dict
  unhealthy_threshold_count:
    description:
      - The number of consecutive health check failures required before considering a target unhealthy.
    required: false
    type: int
  vpc_id:
    description:
      - The identifier of the virtual private cloud (VPC). Required when I(state) is C(present).
    required: false
    type: str
  wait:
    description:
      - Whether or not to wait for the target group.
    type: bool
    default: false
  wait_timeout:
    description:
      - The time to wait for the target group.
    default: 200
    type: int
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

notes:
  - Once a target group has been created, only its health check can then be modified using subsequent calls
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a target group with a default health check
  community.aws.elb_target_group:
    name: mytargetgroup
    protocol: http
    port: 80
    vpc_id: vpc-01234567
    state: present

- name: Modify the target group with a custom health check
  community.aws.elb_target_group:
    name: mytargetgroup
    protocol: http
    port: 80
    vpc_id: vpc-01234567
    health_check_protocol: http
    health_check_path: /health_check
    health_check_port: 80
    successful_response_codes: 200
    health_check_interval: 15
    health_check_timeout: 3
    healthy_threshold_count: 4
    unhealthy_threshold_count: 3
    state: present

- name: Delete a target group
  community.aws.elb_target_group:
    name: mytargetgroup
    state: absent

- name: Create a target group with instance targets
  community.aws.elb_target_group:
    name: mytargetgroup
    protocol: http
    port: 81
    vpc_id: vpc-01234567
    health_check_protocol: http
    health_check_path: /
    successful_response_codes: "200,250-260"
    targets:
      - Id: i-01234567
        Port: 80
      - Id: i-98765432
        Port: 80
    state: present
    wait_timeout: 200
    wait: True

- name: Create a target group with IP address targets
  community.aws.elb_target_group:
    name: mytargetgroup
    protocol: http
    port: 81
    vpc_id: vpc-01234567
    health_check_protocol: http
    health_check_path: /
    successful_response_codes: "200,250-260"
    target_type: ip
    targets:
      - Id: 10.0.0.10
        Port: 80
        AvailabilityZone: all
      - Id: 10.0.0.20
        Port: 80
    state: present
    wait_timeout: 200
    wait: True

# Using lambda as targets require that the target group
# itself is allow to invoke the lambda function.
# therefore you need first to create an empty target group
# to receive its arn, second, allow the target group
# to invoke the lambda function and third, add the target
# to the target group
- name: first, create empty target group
  community.aws.elb_target_group:
    name: my-lambda-targetgroup
    target_type: lambda
    state: present
    modify_targets: False
  register: out

- name: second, allow invoke of the lambda
  community.aws.lambda_policy:
    state: "{{ state | default('present') }}"
    function_name: my-lambda-function
    statement_id: someID
    action: lambda:InvokeFunction
    principal: elasticloadbalancing.amazonaws.com
    source_arn: "{{ out.target_group_arn }}"

- name: third, add target
  community.aws.elb_target_group:
    name: my-lambda-targetgroup
    target_type: lambda
    state: present
    targets:
        - Id: arn:aws:lambda:eu-central-1:123456789012:function:my-lambda-function

'''

RETURN = r'''
deregistration_delay_timeout_seconds:
    description: The amount time for Elastic Load Balancing to wait before changing the state of a deregistering target from draining to unused.
    returned: when state present
    type: int
    sample: 300
health_check_interval_seconds:
    description: The approximate amount of time, in seconds, between health checks of an individual target.
    returned: when state present
    type: int
    sample: 30
health_check_path:
    description: The destination for the health check request.
    returned: when state present
    type: str
    sample: /index.html
health_check_port:
    description: The port to use to connect with the target.
    returned: when state present
    type: str
    sample: traffic-port
health_check_protocol:
    description: The protocol to use to connect with the target.
    returned: when state present
    type: str
    sample: HTTP
health_check_timeout_seconds:
    description: The amount of time, in seconds, during which no response means a failed health check.
    returned: when state present
    type: int
    sample: 5
healthy_threshold_count:
    description: The number of consecutive health checks successes required before considering an unhealthy target healthy.
    returned: when state present
    type: int
    sample: 5
load_balancer_arns:
    description: The Amazon Resource Names (ARN) of the load balancers that route traffic to this target group.
    returned: when state present
    type: list
    sample: []
matcher:
    description: The HTTP codes to use when checking for a successful response from a target.
    returned: when state present
    type: dict
    sample: {
        "http_code": "200"
    }
port:
    description: The port on which the targets are listening.
    returned: when state present
    type: int
    sample: 80
protocol:
    description: The protocol to use for routing traffic to the targets.
    returned: when state present
    type: str
    sample: HTTP
stickiness_enabled:
    description: Indicates whether sticky sessions are enabled.
    returned: when state present
    type: bool
    sample: true
stickiness_lb_cookie_duration_seconds:
    description: The time period, in seconds, during which requests from a client should be routed to the same target.
    returned: when state present
    type: int
    sample: 86400
stickiness_type:
    description: The type of sticky sessions.
    returned: when state present
    type: str
    sample: lb_cookie
tags:
    description: The tags attached to the target group.
    returned: when state present
    type: dict
    sample: "{
        'Tag': 'Example'
    }"
target_group_arn:
    description: The Amazon Resource Name (ARN) of the target group.
    returned: when state present
    type: str
    sample: "arn:aws:elasticloadbalancing:ap-southeast-2:01234567890:targetgroup/mytargetgroup/aabbccddee0044332211"
target_group_name:
    description: The name of the target group.
    returned: when state present
    type: str
    sample: mytargetgroup
unhealthy_threshold_count:
    description: The number of consecutive health check failures required before considering the target unhealthy.
    returned: when state present
    type: int
    sample: 2
vpc_id:
    description: The ID of the VPC for the targets.
    returned: when state present
    type: str
    sample: vpc-0123456
'''

import time

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (camel_dict_to_snake_dict,
                                                                     boto3_tag_list_to_ansible_dict,
                                                                     compare_aws_tags,
                                                                     ansible_dict_to_boto3_tag_list,
                                                                     )
from distutils.version import LooseVersion


def get_tg_attributes(connection, module, tg_arn):
    try:
        tg_attributes = boto3_tag_list_to_ansible_dict(connection.describe_target_group_attributes(TargetGroupArn=tg_arn)['Attributes'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get target group attributes")

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    return dict((k.replace('.', '_'), v) for k, v in tg_attributes.items())


def get_target_group_tags(connection, module, target_group_arn):
    try:
        return connection.describe_tags(ResourceArns=[target_group_arn])['TagDescriptions'][0]['Tags']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get target group tags")


def get_target_group(connection, module):
    try:
        target_group_paginator = connection.get_paginator('describe_target_groups')
        return (target_group_paginator.paginate(Names=[module.params.get("name")]).build_full_result())['TargetGroups'][0]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if e.response['Error']['Code'] == 'TargetGroupNotFound':
            return None
        else:
            module.fail_json_aws(e, msg="Couldn't get target group")


def wait_for_status(connection, module, target_group_arn, targets, status):
    polling_increment_secs = 5
    max_retries = (module.params.get('wait_timeout') // polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        try:
            response = connection.describe_target_health(TargetGroupArn=target_group_arn, Targets=targets)
            if response['TargetHealthDescriptions'][0]['TargetHealth']['State'] == status:
                status_achieved = True
                break
            else:
                time.sleep(polling_increment_secs)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't describe target health")

    result = response
    return status_achieved, result


def fail_if_ip_target_type_not_supported(module):
    if LooseVersion(botocore.__version__) < LooseVersion('1.7.2'):
        module.fail_json(msg="target_type ip requires botocore version 1.7.2 or later. Version %s is installed" %
                         botocore.__version__)


def create_or_update_target_group(connection, module):

    changed = False
    new_target_group = False
    params = dict()
    target_type = module.params.get("target_type")
    params['Name'] = module.params.get("name")
    params['TargetType'] = target_type
    if target_type != "lambda":
        params['Protocol'] = module.params.get("protocol").upper()
        params['Port'] = module.params.get("port")
        params['VpcId'] = module.params.get("vpc_id")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    deregistration_delay_timeout = module.params.get("deregistration_delay_timeout")
    stickiness_enabled = module.params.get("stickiness_enabled")
    stickiness_lb_cookie_duration = module.params.get("stickiness_lb_cookie_duration")
    stickiness_type = module.params.get("stickiness_type")

    health_option_keys = [
        "health_check_path", "health_check_protocol", "health_check_interval", "health_check_timeout",
        "healthy_threshold_count", "unhealthy_threshold_count", "successful_response_codes"
    ]
    health_options = any([module.params[health_option_key] is not None for health_option_key in health_option_keys])

    # Set health check if anything set
    if health_options:

        if module.params.get("health_check_protocol") is not None:
            params['HealthCheckProtocol'] = module.params.get("health_check_protocol").upper()

        if module.params.get("health_check_port") is not None:
            params['HealthCheckPort'] = module.params.get("health_check_port")

        if module.params.get("health_check_interval") is not None:
            params['HealthCheckIntervalSeconds'] = module.params.get("health_check_interval")

        if module.params.get("health_check_timeout") is not None:
            params['HealthCheckTimeoutSeconds'] = module.params.get("health_check_timeout")

        if module.params.get("healthy_threshold_count") is not None:
            params['HealthyThresholdCount'] = module.params.get("healthy_threshold_count")

        if module.params.get("unhealthy_threshold_count") is not None:
            params['UnhealthyThresholdCount'] = module.params.get("unhealthy_threshold_count")

        # Only need to check response code and path for http(s) health checks
        protocol = module.params.get("health_check_protocol")
        if protocol is not None and protocol.upper() in ['HTTP', 'HTTPS']:

            if module.params.get("health_check_path") is not None:
                params['HealthCheckPath'] = module.params.get("health_check_path")

            if module.params.get("successful_response_codes") is not None:
                params['Matcher'] = {}
                params['Matcher']['HttpCode'] = module.params.get("successful_response_codes")

    # Get target type
    if target_type == 'ip':
        fail_if_ip_target_type_not_supported(module)

    # Get target group
    tg = get_target_group(connection, module)

    if tg:
        diffs = [param for param in ('Port', 'Protocol', 'VpcId')
                 if tg.get(param) != params.get(param)]
        if diffs:
            module.fail_json(msg="Cannot modify %s parameter(s) for a target group" %
                             ", ".join(diffs))
        # Target group exists so check health check parameters match what has been passed
        health_check_params = dict()

        # Modify health check if anything set
        if health_options:

            # Health check protocol
            if 'HealthCheckProtocol' in params and tg['HealthCheckProtocol'] != params['HealthCheckProtocol']:
                health_check_params['HealthCheckProtocol'] = params['HealthCheckProtocol']

            # Health check port
            if 'HealthCheckPort' in params and tg['HealthCheckPort'] != params['HealthCheckPort']:
                health_check_params['HealthCheckPort'] = params['HealthCheckPort']

            # Health check interval
            if 'HealthCheckIntervalSeconds' in params and tg['HealthCheckIntervalSeconds'] != params['HealthCheckIntervalSeconds']:
                health_check_params['HealthCheckIntervalSeconds'] = params['HealthCheckIntervalSeconds']

            # Health check timeout
            if 'HealthCheckTimeoutSeconds' in params and tg['HealthCheckTimeoutSeconds'] != params['HealthCheckTimeoutSeconds']:
                health_check_params['HealthCheckTimeoutSeconds'] = params['HealthCheckTimeoutSeconds']

            # Healthy threshold
            if 'HealthyThresholdCount' in params and tg['HealthyThresholdCount'] != params['HealthyThresholdCount']:
                health_check_params['HealthyThresholdCount'] = params['HealthyThresholdCount']

            # Unhealthy threshold
            if 'UnhealthyThresholdCount' in params and tg['UnhealthyThresholdCount'] != params['UnhealthyThresholdCount']:
                health_check_params['UnhealthyThresholdCount'] = params['UnhealthyThresholdCount']

            # Only need to check response code and path for http(s) health checks
            if tg['HealthCheckProtocol'] in ['HTTP', 'HTTPS']:
                # Health check path
                if 'HealthCheckPath' in params and tg['HealthCheckPath'] != params['HealthCheckPath']:
                    health_check_params['HealthCheckPath'] = params['HealthCheckPath']

                # Matcher (successful response codes)
                # TODO: required and here?
                if 'Matcher' in params:
                    current_matcher_list = tg['Matcher']['HttpCode'].split(',')
                    requested_matcher_list = params['Matcher']['HttpCode'].split(',')
                    if set(current_matcher_list) != set(requested_matcher_list):
                        health_check_params['Matcher'] = {}
                        health_check_params['Matcher']['HttpCode'] = ','.join(requested_matcher_list)

            try:
                if health_check_params:
                    connection.modify_target_group(TargetGroupArn=tg['TargetGroupArn'], **health_check_params)
                    changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't update target group")

        # Do we need to modify targets?
        if module.params.get("modify_targets"):
            # get list of current target instances. I can't see anything like a describe targets in the doco so
            # describe_target_health seems to be the only way to get them
            try:
                current_targets = connection.describe_target_health(
                    TargetGroupArn=tg['TargetGroupArn'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't get target group health")

            if module.params.get("targets"):

                if target_type != "lambda":
                    params['Targets'] = module.params.get("targets")

                    # Correct type of target ports
                    for target in params['Targets']:
                        target['Port'] = int(target.get('Port', module.params.get('port')))

                    current_instance_ids = []

                    for instance in current_targets['TargetHealthDescriptions']:
                        current_instance_ids.append(instance['Target']['Id'])

                    new_instance_ids = []
                    for instance in params['Targets']:
                        new_instance_ids.append(instance['Id'])

                    add_instances = set(new_instance_ids) - set(current_instance_ids)

                    if add_instances:
                        instances_to_add = []
                        for target in params['Targets']:
                            if target['Id'] in add_instances:
                                instances_to_add.append({'Id': target['Id'], 'Port': target['Port']})

                        changed = True
                        try:
                            connection.register_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=instances_to_add)
                        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                            module.fail_json_aws(e, msg="Couldn't register targets")

                        if module.params.get("wait"):
                            status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], instances_to_add, 'healthy')
                            if not status_achieved:
                                module.fail_json(msg='Error waiting for target registration to be healthy - please check the AWS console')

                    remove_instances = set(current_instance_ids) - set(new_instance_ids)

                    if remove_instances:
                        instances_to_remove = []
                        for target in current_targets['TargetHealthDescriptions']:
                            if target['Target']['Id'] in remove_instances:
                                instances_to_remove.append({'Id': target['Target']['Id'], 'Port': target['Target']['Port']})

                        changed = True
                        try:
                            connection.deregister_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=instances_to_remove)
                        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                            module.fail_json_aws(e, msg="Couldn't remove targets")

                        if module.params.get("wait"):
                            status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], instances_to_remove, 'unused')
                            if not status_achieved:
                                module.fail_json(msg='Error waiting for target deregistration - please check the AWS console')

                # register lambda target
                else:
                    try:
                        changed = False
                        target = module.params.get("targets")[0]
                        if len(current_targets["TargetHealthDescriptions"]) == 0:
                            changed = True
                        else:
                            for item in current_targets["TargetHealthDescriptions"]:
                                if target["Id"] != item["Target"]["Id"]:
                                    changed = True
                                    break  # only one target is possible with lambda

                        if changed:
                            if target.get("Id"):
                                response = connection.register_targets(
                                    TargetGroupArn=tg['TargetGroupArn'],
                                    Targets=[
                                        {
                                            "Id": target['Id']
                                        }
                                    ]
                                )

                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(
                            e, msg="Couldn't register targets")
            else:
                if target_type != "lambda":

                    current_instances = current_targets['TargetHealthDescriptions']

                    if current_instances:
                        instances_to_remove = []
                        for target in current_targets['TargetHealthDescriptions']:
                            instances_to_remove.append({'Id': target['Target']['Id'], 'Port': target['Target']['Port']})

                        changed = True
                        try:
                            connection.deregister_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=instances_to_remove)
                        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                            module.fail_json_aws(e, msg="Couldn't remove targets")

                        if module.params.get("wait"):
                            status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], instances_to_remove, 'unused')
                            if not status_achieved:
                                module.fail_json(msg='Error waiting for target deregistration - please check the AWS console')

                # remove lambda targets
                else:
                    changed = False
                    if current_targets["TargetHealthDescriptions"]:
                        changed = True
                        # only one target is possible with lambda
                        target_to_remove = current_targets["TargetHealthDescriptions"][0]["Target"]["Id"]
                    if changed:
                        connection.deregister_targets(
                            TargetGroupArn=tg['TargetGroupArn'], Targets=[{"Id": target_to_remove}])
    else:
        try:
            connection.create_target_group(**params)
            changed = True
            new_target_group = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create target group")

        tg = get_target_group(connection, module)

        if module.params.get("targets"):
            if target_type != "lambda":
                params['Targets'] = module.params.get("targets")
                try:
                    connection.register_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=params['Targets'])
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Couldn't register targets")

                if module.params.get("wait"):
                    status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], params['Targets'], 'healthy')
                    if not status_achieved:
                        module.fail_json(msg='Error waiting for target registration to be healthy - please check the AWS console')

            else:
                try:
                    target = module.params.get("targets")[0]
                    response = connection.register_targets(
                        TargetGroupArn=tg['TargetGroupArn'],
                        Targets=[
                            {
                                "Id": target["Id"]
                            }
                        ]
                    )
                    changed = True
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(
                        e, msg="Couldn't register targets")

    # Now set target group attributes
    update_attributes = []

    # Get current attributes
    current_tg_attributes = get_tg_attributes(connection, module, tg['TargetGroupArn'])

    if deregistration_delay_timeout is not None:
        if str(deregistration_delay_timeout) != current_tg_attributes['deregistration_delay_timeout_seconds']:
            update_attributes.append({'Key': 'deregistration_delay.timeout_seconds', 'Value': str(deregistration_delay_timeout)})
    if stickiness_enabled is not None:
        if stickiness_enabled and current_tg_attributes['stickiness_enabled'] != "true":
            update_attributes.append({'Key': 'stickiness.enabled', 'Value': 'true'})
    if stickiness_lb_cookie_duration is not None:
        if str(stickiness_lb_cookie_duration) != current_tg_attributes['stickiness_lb_cookie_duration_seconds']:
            update_attributes.append({'Key': 'stickiness.lb_cookie.duration_seconds', 'Value': str(stickiness_lb_cookie_duration)})
    if stickiness_type is not None:
        if stickiness_type != current_tg_attributes.get('stickiness_type'):
            update_attributes.append({'Key': 'stickiness.type', 'Value': stickiness_type})

    if update_attributes:
        try:
            connection.modify_target_group_attributes(TargetGroupArn=tg['TargetGroupArn'], Attributes=update_attributes)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            # Something went wrong setting attributes. If this target group was created during this task, delete it to leave a consistent state
            if new_target_group:
                connection.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])
            module.fail_json_aws(e, msg="Couldn't delete target group")

    # Tags - only need to play with tags if tags parameter has been set to something
    if tags:
        # Get tags
        current_tags = get_target_group_tags(connection, module, tg['TargetGroupArn'])

        # Delete necessary tags
        tags_need_modify, tags_to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(current_tags), tags, purge_tags)
        if tags_to_delete:
            try:
                connection.remove_tags(ResourceArns=[tg['TargetGroupArn']], TagKeys=tags_to_delete)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't delete tags from target group")
            changed = True

        # Add/update tags
        if tags_need_modify:
            try:
                connection.add_tags(ResourceArns=[tg['TargetGroupArn']], Tags=ansible_dict_to_boto3_tag_list(tags_need_modify))
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't add tags to target group")
            changed = True

    # Get the target group again
    tg = get_target_group(connection, module)

    # Get the target group attributes again
    tg.update(get_tg_attributes(connection, module, tg['TargetGroupArn']))

    # Convert tg to snake_case
    snaked_tg = camel_dict_to_snake_dict(tg)

    snaked_tg['tags'] = boto3_tag_list_to_ansible_dict(get_target_group_tags(connection, module, tg['TargetGroupArn']))

    module.exit_json(changed=changed, **snaked_tg)


def delete_target_group(connection, module):
    changed = False
    tg = get_target_group(connection, module)

    if tg:
        try:
            connection.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete target group")

    module.exit_json(changed=changed)


def main():
    protocols_list = ['http', 'https', 'tcp', 'tls', 'udp', 'tcp_udp', 'HTTP',
                      'HTTPS', 'TCP', 'TLS', 'UDP', 'TCP_UDP']
    argument_spec = dict(
        deregistration_delay_timeout=dict(type='int'),
        health_check_protocol=dict(choices=protocols_list),
        health_check_port=dict(),
        health_check_path=dict(),
        health_check_interval=dict(type='int'),
        health_check_timeout=dict(type='int'),
        healthy_threshold_count=dict(type='int'),
        modify_targets=dict(default=True, type='bool'),
        name=dict(required=True),
        port=dict(type='int'),
        protocol=dict(choices=protocols_list),
        purge_tags=dict(default=True, type='bool'),
        stickiness_enabled=dict(type='bool'),
        stickiness_type=dict(),
        stickiness_lb_cookie_duration=dict(type='int'),
        state=dict(required=True, choices=['present', 'absent']),
        successful_response_codes=dict(),
        tags=dict(default={}, type='dict'),
        target_type=dict(choices=['instance', 'ip', 'lambda']),
        targets=dict(type='list', elements='dict'),
        unhealthy_threshold_count=dict(type='int'),
        vpc_id=dict(),
        wait_timeout=dict(type='int', default=200),
        wait=dict(type='bool', default=False)
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ['target_type', 'instance', ['protocol', 'port', 'vpc_id']],
                                  ['target_type', 'ip', ['protocol', 'port', 'vpc_id']],
                              ]
                              )

    if module.params.get('target_type') is None:
        module.params['target_type'] = 'instance'

    connection = module.client('elbv2')

    if module.params.get('state') == 'present':
        create_or_update_target_group(connection, module)
    else:
        delete_target_group(connection, module)


if __name__ == '__main__':
    main()

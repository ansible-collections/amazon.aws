#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_classic_lb_info
version_added: 1.0.0
short_description: Gather information about EC2 Elastic Load Balancers in AWS
description:
    - Gather information about EC2 Elastic Load Balancers in AWS
author:
  - "Michael Schultz (@mjschultz)"
  - "Fernando Jose Pando (@nand0p)"
options:
  names:
    description:
      - List of ELB names to gather information about. Pass this option to gather information about a set of ELBs, otherwise, all ELBs are returned.
    type: list
    elements: str
    default: []
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Output format tries to match amazon.aws.ec2_elb_lb module input parameters

# Gather information about all ELBs
- community.aws.elb_classic_lb_info:
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

# Gather information about a particular ELB
- community.aws.elb_classic_lb_info:
    names: frontend-prod-elb
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ elb_info.elbs.0.dns_name }}"

# Gather information about a set of ELBs
- community.aws.elb_classic_lb_info:
    names:
    - frontend-prod-elb
    - backend-prod-elb
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

'''

RETURN = r'''
elbs:
  description: a list of load balancers
  returned: always
  type: list
  sample:
    elbs:
      - attributes:
          access_log:
            enabled: false
          connection_draining:
            enabled: true
            timeout: 300
          connection_settings:
            idle_timeout: 60
          cross_zone_load_balancing:
            enabled: true
        availability_zones:
          - "us-east-1a"
          - "us-east-1b"
          - "us-east-1c"
          - "us-east-1d"
          - "us-east-1e"
        backend_server_description: []
        canonical_hosted_zone_name: test-lb-XXXXXXXXXXXX.us-east-1.elb.amazonaws.com
        canonical_hosted_zone_name_id: XXXXXXXXXXXXXX
        created_time: '2017-08-23T18:25:03.280000+00:00'
        dns_name: test-lb-XXXXXXXXXXXX.us-east-1.elb.amazonaws.com
        health_check:
          healthy_threshold: 10
          interval: 30
          target: HTTP:80/index.html
          timeout: 5
          unhealthy_threshold: 2
        instances: []
        instances_inservice: []
        instances_inservice_count: 0
        instances_outofservice: []
        instances_outofservice_count: 0
        instances_unknownservice: []
        instances_unknownservice_count: 0
        listener_descriptions:
          - listener:
              instance_port: 80
              instance_protocol: HTTP
              load_balancer_port: 80
              protocol: HTTP
            policy_names: []
        load_balancer_name: test-lb
        policies:
          app_cookie_stickiness_policies: []
          lb_cookie_stickiness_policies: []
          other_policies: []
        scheme: internet-facing
        security_groups:
          - sg-29d13055
        source_security_group:
          group_name: default
          owner_alias: XXXXXXXXXXXX
        subnets:
          - subnet-XXXXXXXX
          - subnet-XXXXXXXX
        tags: {}
        vpc_id: vpc-c248fda4
'''

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule, is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (
    AWSRetry,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict
)

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

MAX_AWS_RETRIES = 5
MAX_AWS_DELAY = 5


def list_elbs(connection, load_balancer_names):
    results = []

    if not load_balancer_names:
        for lb in get_all_lb(connection):
            results.append(describe_elb(connection, lb))

    for load_balancer_name in load_balancer_names:
        lb = get_lb(connection, load_balancer_name)
        if not lb:
            continue
        results.append(describe_elb(connection, lb))
    return results


def describe_elb(connection, lb):
    description = camel_dict_to_snake_dict(lb)
    name = lb['LoadBalancerName']
    instances = lb.get('Instances', [])
    description['tags'] = get_tags(connection, name)
    description['instances_inservice'], description['instances_inservice_count'] = lb_instance_health(connection, name, instances, 'InService')
    description['instances_outofservice'], description['instances_outofservice_count'] = lb_instance_health(connection, name, instances, 'OutOfService')
    description['instances_unknownservice'], description['instances_unknownservice_count'] = lb_instance_health(connection, name, instances, 'Unknown')
    description['attributes'] = get_lb_attributes(connection, name)
    return description


@AWSRetry.jittered_backoff()
def get_all_lb(connection):
    paginator = connection.get_paginator('describe_load_balancers')
    return paginator.paginate().build_full_result()['LoadBalancerDescriptions']


def get_lb(connection, load_balancer_name):
    try:
        return connection.describe_load_balancers(aws_retry=True, LoadBalancerNames=[load_balancer_name])['LoadBalancerDescriptions'][0]
    except is_boto3_error_code('LoadBalancerNotFound'):
        return []


def get_lb_attributes(connection, load_balancer_name):
    attributes = connection.describe_load_balancer_attributes(aws_retry=True, LoadBalancerName=load_balancer_name).get('LoadBalancerAttributes', {})
    return camel_dict_to_snake_dict(attributes)


def get_tags(connection, load_balancer_name):
    tags = connection.describe_tags(aws_retry=True, LoadBalancerNames=[load_balancer_name])['TagDescriptions']
    if not tags:
        return {}
    return boto3_tag_list_to_ansible_dict(tags[0]['Tags'])


def lb_instance_health(connection, load_balancer_name, instances, state):
    instance_states = connection.describe_instance_health(LoadBalancerName=load_balancer_name, Instances=instances).get('InstanceStates', [])
    instate = [instance['InstanceId'] for instance in instance_states if instance['State'] == state]
    return instate, len(instate)


def main():
    argument_spec = dict(
        names=dict(default=[], type='list', elements='str')
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    connection = module.client('elb', retry_decorator=AWSRetry.jittered_backoff(retries=MAX_AWS_RETRIES, delay=MAX_AWS_DELAY))

    try:
        elbs = list_elbs(connection, module.params.get('names'))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get load balancer information.")

    module.exit_json(elbs=elbs)


if __name__ == '__main__':
    main()

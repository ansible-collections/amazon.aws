#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_target_group_info
version_added: 1.0.0
short_description: Gather information about ELB target groups in AWS
description:
    - Gather information about ELB target groups in AWS
    - This module was called C(elb_target_group_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
author: Rob White (@wimnat)
options:
  load_balancer_arn:
    description:
      - The Amazon Resource Name (ARN) of the load balancer.
    required: false
    type: str
  target_group_arns:
    description:
      - The Amazon Resource Names (ARN) of the target groups.
    required: false
    type: list
    elements: str
  names:
    description:
      - The names of the target groups.
    required: false
    type: list
    elements: str
  collect_targets_health:
    description:
      - When set to "yes", output contains targets health description
    required: false
    default: no
    type: bool

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all target groups
  community.aws.elb_target_group_info:

- name: Gather information about the target group attached to a particular ELB
  community.aws.elb_target_group_info:
    load_balancer_arn: "arn:aws:elasticloadbalancing:ap-southeast-2:001122334455:loadbalancer/app/my-elb/aabbccddeeff"

- name: Gather information about a target groups named 'tg1' and 'tg2'
  community.aws.elb_target_group_info:
    names:
      - tg1
      - tg2

'''

RETURN = r'''
target_groups:
    description: a list of target groups
    returned: always
    type: complex
    contains:
        deregistration_delay_timeout_seconds:
            description: The amount time for Elastic Load Balancing to wait before changing the state of a deregistering target from draining to unused.
            returned: always
            type: int
            sample: 300
        health_check_interval_seconds:
            description: The approximate amount of time, in seconds, between health checks of an individual target.
            returned: always
            type: int
            sample: 30
        health_check_path:
            description: The destination for the health check request.
            returned: always
            type: str
            sample: /index.html
        health_check_port:
            description: The port to use to connect with the target.
            returned: always
            type: str
            sample: traffic-port
        health_check_protocol:
            description: The protocol to use to connect with the target.
            returned: always
            type: str
            sample: HTTP
        health_check_timeout_seconds:
            description: The amount of time, in seconds, during which no response means a failed health check.
            returned: always
            type: int
            sample: 5
        healthy_threshold_count:
            description: The number of consecutive health checks successes required before considering an unhealthy target healthy.
            returned: always
            type: int
            sample: 5
        load_balancer_arns:
            description: The Amazon Resource Names (ARN) of the load balancers that route traffic to this target group.
            returned: always
            type: list
            sample: []
        matcher:
            description: The HTTP codes to use when checking for a successful response from a target.
            returned: always
            type: dict
            sample: {
                "http_code": "200"
            }
        port:
            description: The port on which the targets are listening.
            returned: always
            type: int
            sample: 80
        protocol:
            description: The protocol to use for routing traffic to the targets.
            returned: always
            type: str
            sample: HTTP
        stickiness_enabled:
            description: Indicates whether sticky sessions are enabled.
            returned: always
            type: bool
            sample: true
        stickiness_lb_cookie_duration_seconds:
            description: Indicates whether sticky sessions are enabled.
            returned: always
            type: int
            sample: 86400
        stickiness_type:
            description: The type of sticky sessions.
            returned: always
            type: str
            sample: lb_cookie
        tags:
            description: The tags attached to the target group.
            returned: always
            type: dict
            sample: "{
                'Tag': 'Example'
            }"
        target_group_arn:
            description: The Amazon Resource Name (ARN) of the target group.
            returned: always
            type: str
            sample: "arn:aws:elasticloadbalancing:ap-southeast-2:01234567890:targetgroup/mytargetgroup/aabbccddee0044332211"
        targets_health_description:
            description: Targets health description.
            returned: when collect_targets_health is enabled
            type: complex
            contains:
                health_check_port:
                    description: The port to check target health.
                    returned: always
                    type: str
                    sample: '80'
                target:
                    description: The target metadata.
                    returned: always
                    type: complex
                    contains:
                        id:
                            description: The ID of the target.
                            returned: always
                            type: str
                            sample: i-0123456789
                        port:
                            description: The port to use to connect with the target.
                            returned: always
                            type: int
                            sample: 80
                target_health:
                    description: The target health status.
                    returned: always
                    type: complex
                    contains:
                        state:
                            description: The state of the target health.
                            returned: always
                            type: str
                            sample: healthy
        target_group_name:
            description: The name of the target group.
            returned: always
            type: str
            sample: mytargetgroup
        unhealthy_threshold_count:
            description: The number of consecutive health check failures required before considering the target unhealthy.
            returned: always
            type: int
            sample: 2
        vpc_id:
            description: The ID of the VPC for the targets.
            returned: always
            type: str
            sample: vpc-0123456
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def get_target_group_attributes(connection, module, target_group_arn):

    try:
        target_group_attributes = boto3_tag_list_to_ansible_dict(connection.describe_target_group_attributes(TargetGroupArn=target_group_arn)['Attributes'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe target group attributes")

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    return dict((k.replace('.', '_'), v)
                for (k, v) in target_group_attributes.items())


def get_target_group_tags(connection, module, target_group_arn):

    try:
        return boto3_tag_list_to_ansible_dict(connection.describe_tags(ResourceArns=[target_group_arn])['TagDescriptions'][0]['Tags'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe group tags")


def get_target_group_targets_health(connection, module, target_group_arn):

    try:
        return connection.describe_target_health(TargetGroupArn=target_group_arn)['TargetHealthDescriptions']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get target health")


def list_target_groups(connection, module):

    load_balancer_arn = module.params.get("load_balancer_arn")
    target_group_arns = module.params.get("target_group_arns")
    names = module.params.get("names")
    collect_targets_health = module.params.get("collect_targets_health")

    try:
        target_group_paginator = connection.get_paginator('describe_target_groups')
        if not load_balancer_arn and not target_group_arns and not names:
            target_groups = target_group_paginator.paginate().build_full_result()
        if load_balancer_arn:
            target_groups = target_group_paginator.paginate(LoadBalancerArn=load_balancer_arn).build_full_result()
        if target_group_arns:
            target_groups = target_group_paginator.paginate(TargetGroupArns=target_group_arns).build_full_result()
        if names:
            target_groups = target_group_paginator.paginate(Names=names).build_full_result()
    except is_boto3_error_code('TargetGroupNotFound'):
        module.exit_json(target_groups=[])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to list target groups")

    # Get the attributes and tags for each target group
    for target_group in target_groups['TargetGroups']:
        target_group.update(get_target_group_attributes(connection, module, target_group['TargetGroupArn']))

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_target_groups = [camel_dict_to_snake_dict(target_group) for target_group in target_groups['TargetGroups']]

    # Get tags for each target group
    for snaked_target_group in snaked_target_groups:
        snaked_target_group['tags'] = get_target_group_tags(connection, module, snaked_target_group['target_group_arn'])
        if collect_targets_health:
            snaked_target_group['targets_health_description'] = [camel_dict_to_snake_dict(
                target) for target in get_target_group_targets_health(connection, module, snaked_target_group['target_group_arn'])]

    module.exit_json(target_groups=snaked_target_groups)


def main():

    argument_spec = dict(
        load_balancer_arn=dict(type='str'),
        target_group_arns=dict(type='list', elements='str'),
        names=dict(type='list', elements='str'),
        collect_targets_health=dict(default=False, type='bool', required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['load_balancer_arn', 'target_group_arns', 'names']],
        supports_check_mode=True,
    )
    if module._name == 'elb_target_group_facts':
        module.deprecate("The 'elb_target_group_facts' module has been renamed to 'elb_target_group_info'", date='2021-12-01', collection_name='community.aws')

    try:
        connection = module.client('elbv2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    list_target_groups(connection, module)


if __name__ == '__main__':
    main()

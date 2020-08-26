#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_application_lb_info
version_added: 1.0.0
short_description: Gather information about application ELBs in AWS
description:
    - Gather information about application ELBs in AWS
    - This module was called C(elb_application_lb_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
author: Rob White (@wimnat)
options:
  load_balancer_arns:
    description:
      - The Amazon Resource Names (ARN) of the load balancers. You can specify up to 20 load balancers in a single call.
    required: false
    type: list
    elements: str
  names:
    description:
      - The names of the load balancers.
    required: false
    type: list
    elements: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all target groups
  community.aws.elb_application_lb_info:

- name: Gather information about the target group attached to a particular ELB
  community.aws.elb_application_lb_info:
    load_balancer_arns:
      - "arn:aws:elasticloadbalancing:ap-southeast-2:001122334455:loadbalancer/app/my-elb/aabbccddeeff"

- name: Gather information about a target groups named 'tg1' and 'tg2'
  community.aws.elb_application_lb_info:
    names:
      - elb1
      - elb2

- name: Gather information about specific ALB
  community.aws.elb_application_lb_info:
    names: "alb-name"
    region: "aws-region"
  register: alb_info
- ansible.builtin.debug:
    var: alb_info
'''

RETURN = r'''
load_balancers:
    description: a list of load balancers
    returned: always
    type: complex
    contains:
        access_logs_s3_bucket:
            description: The name of the S3 bucket for the access logs.
            returned: when status is present
            type: str
            sample: mys3bucket
        access_logs_s3_enabled:
            description: Indicates whether access logs stored in Amazon S3 are enabled.
            returned: when status is present
            type: str
            sample: true
        access_logs_s3_prefix:
            description: The prefix for the location in the S3 bucket.
            returned: when status is present
            type: str
            sample: /my/logs
        availability_zones:
            description: The Availability Zones for the load balancer.
            returned: when status is present
            type: list
            sample: "[{'subnet_id': 'subnet-aabbccddff', 'zone_name': 'ap-southeast-2a'}]"
        canonical_hosted_zone_id:
            description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
            returned: when status is present
            type: str
            sample: ABCDEF12345678
        created_time:
            description: The date and time the load balancer was created.
            returned: when status is present
            type: str
            sample: "2015-02-12T02:14:02+00:00"
        deletion_protection_enabled:
            description: Indicates whether deletion protection is enabled.
            returned: when status is present
            type: str
            sample: true
        dns_name:
            description: The public DNS name of the load balancer.
            returned: when status is present
            type: str
            sample: internal-my-elb-123456789.ap-southeast-2.elb.amazonaws.com
        idle_timeout_timeout_seconds:
            description: The idle timeout value, in seconds.
            returned: when status is present
            type: str
            sample: 60
        ip_address_type:
            description:  The type of IP addresses used by the subnets for the load balancer.
            returned: when status is present
            type: str
            sample: ipv4
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            returned: when status is present
            type: str
            sample: arn:aws:elasticloadbalancing:ap-southeast-2:0123456789:loadbalancer/app/my-elb/001122334455
        load_balancer_name:
            description: The name of the load balancer.
            returned: when status is present
            type: str
            sample: my-elb
        scheme:
            description: Internet-facing or internal load balancer.
            returned: when status is present
            type: str
            sample: internal
        security_groups:
            description: The IDs of the security groups for the load balancer.
            returned: when status is present
            type: list
            sample: ['sg-0011223344']
        state:
            description: The state of the load balancer.
            returned: when status is present
            type: dict
            sample: "{'code': 'active'}"
        tags:
            description: The tags attached to the load balancer.
            returned: when status is present
            type: dict
            sample: "{
                'Tag': 'Example'
            }"
        type:
            description: The type of load balancer.
            returned: when status is present
            type: str
            sample: application
        vpc_id:
            description: The ID of the VPC for the load balancer.
            returned: when status is present
            type: str
            sample: vpc-0011223344
'''

import traceback

try:
    import boto3
    import botocore
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def get_elb_listeners(connection, module, elb_arn):

    try:
        return connection.describe_listeners(LoadBalancerArn=elb_arn)['Listeners']
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to describe elb listeners")


def get_listener_rules(connection, module, listener_arn):

    try:
        return connection.describe_rules(ListenerArn=listener_arn)['Rules']
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to describe listener rules")


def get_load_balancer_attributes(connection, module, load_balancer_arn):

    try:
        load_balancer_attributes = boto3_tag_list_to_ansible_dict(connection.describe_load_balancer_attributes(LoadBalancerArn=load_balancer_arn)['Attributes'])
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to describe load balancer attributes")

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    for k, v in list(load_balancer_attributes.items()):
        load_balancer_attributes[k.replace('.', '_')] = v
        del load_balancer_attributes[k]

    return load_balancer_attributes


def get_load_balancer_tags(connection, module, load_balancer_arn):

    try:
        return boto3_tag_list_to_ansible_dict(connection.describe_tags(ResourceArns=[load_balancer_arn])['TagDescriptions'][0]['Tags'])
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to describe load balancer tags")


def list_load_balancers(connection, module):

    load_balancer_arns = module.params.get("load_balancer_arns")
    names = module.params.get("names")

    try:
        load_balancer_paginator = connection.get_paginator('describe_load_balancers')
        if not load_balancer_arns and not names:
            load_balancers = load_balancer_paginator.paginate().build_full_result()
        if load_balancer_arns:
            load_balancers = load_balancer_paginator.paginate(LoadBalancerArns=load_balancer_arns).build_full_result()
        if names:
            load_balancers = load_balancer_paginator.paginate(Names=names).build_full_result()
    except is_boto3_error_code('LoadBalancerNotFound'):
        module.exit_json(load_balancers=[])
    except ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to list load balancers")
    except NoCredentialsError as e:
        module.fail_json(msg="AWS authentication problem. " + to_native(e), exception=traceback.format_exc())

    for load_balancer in load_balancers['LoadBalancers']:
        # Get the attributes for each elb
        load_balancer.update(get_load_balancer_attributes(connection, module, load_balancer['LoadBalancerArn']))

        # Get the listeners for each elb
        load_balancer['listeners'] = get_elb_listeners(connection, module, load_balancer['LoadBalancerArn'])

        # For each listener, get listener rules
        for listener in load_balancer['listeners']:
            listener['rules'] = get_listener_rules(connection, module, listener['ListenerArn'])

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_load_balancers = [camel_dict_to_snake_dict(load_balancer) for load_balancer in load_balancers['LoadBalancers']]

    # Get tags for each load balancer
    for snaked_load_balancer in snaked_load_balancers:
        snaked_load_balancer['tags'] = get_load_balancer_tags(connection, module, snaked_load_balancer['load_balancer_arn'])

    module.exit_json(load_balancers=snaked_load_balancers)


def main():

    argument_spec = dict(
        load_balancer_arns=dict(type='list', elements='str'),
        names=dict(type='list', elements='str')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['load_balancer_arns', 'names']],
        supports_check_mode=True,
    )
    if module._name == 'elb_application_lb_facts':
        module.deprecate("The 'elb_application_lb_facts' module has been renamed to 'elb_application_lb_info'",
                         date='2021-12-01', collection_name='community.aws')

    try:
        connection = module.client('elbv2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    list_load_balancers(connection, module)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_application_lb_info
version_added: 1.0.0
short_description: Gather information about Application Load Balancers in AWS
description:
    - Gather information about Application Load Balancers in AWS
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

- name: Gather information about all ALBs
  community.aws.elb_application_lb_info:

- name: Gather information about a particular ALB given its ARN
  community.aws.elb_application_lb_info:
    load_balancer_arns:
      - "arn:aws:elasticloadbalancing:ap-southeast-2:001122334455:loadbalancer/app/my-alb/aabbccddeeff"

- name: Gather information about ALBs named 'alb1' and 'alb2'
  community.aws.elb_application_lb_info:
    names:
      - alb1
      - alb2

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
            type: str
            sample: "mys3bucket"
        access_logs_s3_enabled:
            description: Indicates whether access logs stored in Amazon S3 are enabled.
            type: bool
            sample: true
        access_logs_s3_prefix:
            description: The prefix for the location in the S3 bucket.
            type: str
            sample: "my/logs"
        availability_zones:
            description: The Availability Zones for the load balancer.
            type: list
            sample: [{ "load_balancer_addresses": [], "subnet_id": "subnet-aabbccddff", "zone_name": "ap-southeast-2a" }]
        canonical_hosted_zone_id:
            description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
            type: str
            sample: "ABCDEF12345678"
        created_time:
            description: The date and time the load balancer was created.
            type: str
            sample: "2015-02-12T02:14:02+00:00"
        deletion_protection_enabled:
            description: Indicates whether deletion protection is enabled.
            type: bool
            sample: true
        dns_name:
            description: The public DNS name of the load balancer.
            type: str
            sample: "internal-my-alb-123456789.ap-southeast-2.elb.amazonaws.com"
        idle_timeout_timeout_seconds:
            description: The idle timeout value, in seconds.
            type: int
            sample: 60
        ip_address_type:
            description: The type of IP addresses used by the subnets for the load balancer.
            type: str
            sample: "ipv4"
        listeners:
            description: Information about the listeners.
            type: complex
            contains:
                listener_arn:
                    description: The Amazon Resource Name (ARN) of the listener.
                    type: str
                    sample: ""
                load_balancer_arn:
                    description: The Amazon Resource Name (ARN) of the load balancer.
                    type: str
                    sample: ""
                port:
                    description: The port on which the load balancer is listening.
                    type: int
                    sample: 80
                protocol:
                    description: The protocol for connections from clients to the load balancer.
                    type: str
                    sample: "HTTPS"
                certificates:
                    description: The SSL server certificate.
                    type: complex
                    contains:
                        certificate_arn:
                            description: The Amazon Resource Name (ARN) of the certificate.
                            type: str
                            sample: ""
                ssl_policy:
                    description: The security policy that defines which ciphers and protocols are supported.
                    type: str
                    sample: ""
                default_actions:
                    description: The default actions for the listener.
                    type: str
                    contains:
                        type:
                            description: The type of action.
                            type: str
                            sample: ""
                        target_group_arn:
                            description: The Amazon Resource Name (ARN) of the target group.
                            type: str
                            sample: ""
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            type: str
            sample: "arn:aws:elasticloadbalancing:ap-southeast-2:0123456789:loadbalancer/app/my-alb/001122334455"
        load_balancer_name:
            description: The name of the load balancer.
            type: str
            sample: "my-alb"
        routing_http2_enabled:
            description: Indicates whether HTTP/2 is enabled.
            type: bool
            sample: true
        routing_http_desync_mitigation_mode:
            description: Determines how the load balancer handles requests that might pose a security risk to an application.
            type: str
            sample: "defensive"
        routing_http_drop_invalid_header_fields_enabled:
            description: Indicates whether HTTP headers with invalid header fields are removed by the load balancer (true) or routed to targets (false).
            type: bool
            sample: false
        routing_http_x_amzn_tls_version_and_cipher_suite_enabled:
            description: Indicates whether the two headers are added to the client request before sending it to the target.
            type: bool
            sample: false
        routing_http_xff_client_port_enabled:
            description: Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer.
            type: bool
            sample: false
        scheme:
            description: Internet-facing or internal load balancer.
            type: str
            sample: "internal"
        security_groups:
            description: The IDs of the security groups for the load balancer.
            type: list
            sample: ['sg-0011223344']
        state:
            description: The state of the load balancer.
            type: dict
            sample: {'code': 'active'}
        tags:
            description: The tags attached to the load balancer.
            type: dict
            sample: {
                'Tag': 'Example'
            }
        type:
            description: The type of load balancer.
            type: str
            sample: "application"
        vpc_id:
            description: The ID of the VPC for the load balancer.
            type: str
            sample: "vpc-0011223344"
        waf_fail_open_enabled:
            description: Indicates whether to allow a AWS WAF-enabled load balancer to route requests to targets
                if it is unable to forward the request to AWS WAF.
            type: bool
            sample: false
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict


@AWSRetry.jittered_backoff()
def get_paginator(connection, **kwargs):
    paginator = connection.get_paginator('describe_load_balancers')
    return paginator.paginate(**kwargs).build_full_result()


def get_alb_listeners(connection, module, alb_arn):

    try:
        return connection.describe_listeners(LoadBalancerArn=alb_arn)['Listeners']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe alb listeners")


def get_listener_rules(connection, module, listener_arn):

    try:
        return connection.describe_rules(ListenerArn=listener_arn)['Rules']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe listener rules")


def get_load_balancer_attributes(connection, module, load_balancer_arn):

    try:
        load_balancer_attributes = boto3_tag_list_to_ansible_dict(connection.describe_load_balancer_attributes(LoadBalancerArn=load_balancer_arn)['Attributes'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe load balancer attributes")

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    for k, v in list(load_balancer_attributes.items()):
        load_balancer_attributes[k.replace('.', '_')] = v
        del load_balancer_attributes[k]

    return load_balancer_attributes


def get_load_balancer_tags(connection, module, load_balancer_arn):

    try:
        return boto3_tag_list_to_ansible_dict(connection.describe_tags(ResourceArns=[load_balancer_arn])['TagDescriptions'][0]['Tags'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe load balancer tags")


def get_load_balancer_ipaddresstype(connection, module, load_balancer_arn):
    try:
        return connection.describe_load_balancers(LoadBalancerArns=[load_balancer_arn])['LoadBalancers'][0]['IpAddressType']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe load balancer ip address type")


def list_load_balancers(connection, module):
    load_balancer_arns = module.params.get("load_balancer_arns")
    names = module.params.get("names")

    try:
        if not load_balancer_arns and not names:
            load_balancers = get_paginator(connection)
        if load_balancer_arns:
            load_balancers = get_paginator(connection, LoadBalancerArns=load_balancer_arns)
        if names:
            load_balancers = get_paginator(connection, Names=names)
    except is_boto3_error_code('LoadBalancerNotFound'):
        module.exit_json(load_balancers=[])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to list load balancers")

    for load_balancer in load_balancers['LoadBalancers']:
        # Get the attributes for each alb
        load_balancer.update(get_load_balancer_attributes(connection, module, load_balancer['LoadBalancerArn']))

        # Get the listeners for each alb
        load_balancer['listeners'] = get_alb_listeners(connection, module, load_balancer['LoadBalancerArn'])

        # For each listener, get listener rules
        for listener in load_balancer['listeners']:
            listener['rules'] = get_listener_rules(connection, module, listener['ListenerArn'])

        # Get ALB ip address type
        load_balancer['IpAddressType'] = get_load_balancer_ipaddresstype(connection, module, load_balancer['LoadBalancerArn'])

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

    try:
        connection = module.client('elbv2', retry_decorator=AWSRetry.jittered_backoff(retries=10))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    list_load_balancers(connection, module)


if __name__ == '__main__':
    main()

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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_application_lb
version_added: 1.0.0
short_description: Manage an Application Load Balancer
description:
  - Manage an AWS Application Elastic Load Balancer. See U(https://aws.amazon.com/blogs/aws/new-aws-application-load-balancer/) for details.
author:
  - "Rob White (@wimnat)"
options:
  access_logs_enabled:
    description:
      - Whether or not to enable access logs.
      - When set, I(access_logs_s3_bucket) must also be set.
    type: bool
  access_logs_s3_bucket:
    description:
      - The name of the S3 bucket for the access logs.
      - The bucket must exist in the same
        region as the load balancer and have a bucket policy that grants Elastic Load Balancing permission to write to the bucket.
      - Required if access logs in Amazon S3 are enabled.
      - When set, I(access_logs_enabled) must also be set.
    type: str
  access_logs_s3_prefix:
    description:
      - The prefix for the log location in the S3 bucket.
      - If you don't specify a prefix, the access logs are stored in the root of the bucket.
      - Cannot begin or end with a slash.
    type: str
  deletion_protection:
    description:
      - Indicates whether deletion protection for the ALB is enabled.
      - Defaults to C(False).
    type: bool
  http2:
    description:
      - Indicates whether to enable HTTP2 routing.
      - Defaults to C(True).
    type: bool
  http_desync_mitigation_mode:
    description:
      - Determines how the load balancer handles requests that might pose a security risk to an application.
      - Defaults to C('defensive')
    type: str
    choices: ['monitor', 'defensive', 'strictest']
    version_added: 3.2.0
  http_drop_invalid_header_fields:
    description:
      - Indicates whether HTTP headers with invalid header fields are removed by the load balancer C(True) or routed to targets C(False).
      - Defaults to C(False).
    type: bool
    version_added: 3.2.0
  http_x_amzn_tls_version_and_cipher_suite:
    description:
      - Indicates whether the two headers are added to the client request before sending it to the target.
      - Defaults to C(False).
    type: bool
    version_added: 3.2.0
  http_xff_client_port:
    description:
      - Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer.
      - Defaults to C(False).
    type: bool
    version_added: 3.2.0
  idle_timeout:
    description:
      - The number of seconds to wait before an idle connection is closed.
    type: int
  listeners:
    description:
      - A list of dicts containing listeners to attach to the ALB. See examples for detail of the dict required. Note that listener keys
        are CamelCased.
    type: list
    elements: dict
    suboptions:
        Port:
            description: The port on which the load balancer is listening.
            required: true
            type: int
        Protocol:
            description: The protocol for connections from clients to the load balancer.
            required: true
            type: str
        Certificates:
            description: The SSL server certificate.
            type: list
            elements: dict
            suboptions:
                CertificateArn:
                    description: The Amazon Resource Name (ARN) of the certificate.
                    type: str
        SslPolicy:
            description: The security policy that defines which ciphers and protocols are supported.
            type: str
        DefaultActions:
            description: The default actions for the listener.
            required: true
            type: list
            elements: dict
            suboptions:
                Type:
                    description: The type of action.
                    type: str
                TargetGroupArn:
                    description: The Amazon Resource Name (ARN) of the target group.
                    type: str
        Rules:
            type: list
            elements: dict
            description:
              - A list of ALB Listener Rules.
              - 'For the complete documentation of possible Conditions and Actions please see the boto3 documentation:'
              - 'https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_rule'
            suboptions:
                Conditions:
                    type: list
                    description: Conditions which must be met for the actions to be applied.
                    elements: dict
                Priority:
                    type: int
                    description: The rule priority.
                Actions:
                    type: list
                    description: Actions to apply if all of the rule's conditions are met.
                    elements: dict
  name:
    description:
      - The name of the load balancer. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric
        characters or hyphens, and must not begin or end with a hyphen.
    required: true
    type: str
  purge_listeners:
    description:
      - If C(yes), existing listeners will be purged from the ALB to match exactly what is defined by I(listeners) parameter.
      - If the I(listeners) parameter is not set then listeners will not be modified.
    default: yes
    type: bool
  subnets:
    description:
      - A list of the IDs of the subnets to attach to the load balancer. You can specify only one subnet per Availability Zone. You must specify subnets from
        at least two Availability Zones.
      - Required if I(state=present).
    type: list
    elements: str
  security_groups:
    description:
      - A list of the names or IDs of the security groups to assign to the load balancer.
      - Required if I(state=present).
      - If C([]), the VPC's default security group will be used.
    type: list
    elements: str
  scheme:
    description:
      - Internet-facing or internal load balancer. An ALB scheme can not be modified after creation.
    default: internet-facing
    choices: [ 'internet-facing', 'internal' ]
    type: str
  state:
    description:
      - Create or destroy the load balancer.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  wait:
    description:
      - Wait for the load balancer to have a state of 'active' before completing. A status check is
        performed every 15 seconds until a successful state is reached. An error is returned after 40 failed checks.
    default: no
    type: bool
  wait_timeout:
    description:
      - The time in seconds to use in conjunction with I(wait).
    type: int
  purge_rules:
    description:
      - When set to C(no), keep the existing load balancer rules in place. Will modify and add, but will not delete.
    default: yes
    type: bool
  ip_address_type:
    description:
      - Sets the type of IP addresses used by the subnets of the specified Application Load Balancer.
    choices: [ 'ipv4', 'dualstack' ]
    type: str
  waf_fail_open:
    description:
      - Indicates whether to allow a AWS WAF-enabled load balancer to route requests to targets if it is unable to forward the request to AWS WAF.
      - Defaults to C(False).
    type: bool
    version_added: 3.2.0
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags

notes:
  - Listeners are matched based on port. If a listener's port is changed then a new listener will be created.
  - Listener rules are matched based on priority. If a rule's priority is changed then a new rule will be created.
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ALB and attach a listener
- community.aws.elb_application_lb:
    name: myalb
    security_groups:
      - sg-12345678
      - my-sec-group
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - Protocol: HTTP # Required. The protocol for connections from clients to the load balancer (HTTP or HTTPS) (case-sensitive).
        Port: 80 # Required. The port on which the load balancer is listening.
        # The security policy that defines which ciphers and protocols are supported. The default is the current predefined security policy.
        SslPolicy: ELBSecurityPolicy-2015-05
        Certificates: # The ARN of the certificate (only one certficate ARN should be provided)
          - CertificateArn: arn:aws:iam::12345678987:server-certificate/test.domain.com
        DefaultActions:
          - Type: forward # Required.
            TargetGroupName: # Required. The name of the target group
    state: present

# Create an ALB and attach a listener with logging enabled
- community.aws.elb_application_lb:
    access_logs_enabled: yes
    access_logs_s3_bucket: mybucket
    access_logs_s3_prefix: "logs"
    name: myalb
    security_groups:
      - sg-12345678
      - my-sec-group
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - Protocol: HTTP # Required. The protocol for connections from clients to the load balancer (HTTP or HTTPS) (case-sensitive).
        Port: 80 # Required. The port on which the load balancer is listening.
        # The security policy that defines which ciphers and protocols are supported. The default is the current predefined security policy.
        SslPolicy: ELBSecurityPolicy-2015-05
        Certificates: # The ARN of the certificate (only one certficate ARN should be provided)
          - CertificateArn: arn:aws:iam::12345678987:server-certificate/test.domain.com
        DefaultActions:
          - Type: forward # Required.
            TargetGroupName: # Required. The name of the target group
    state: present

# Create an ALB with listeners and rules
- community.aws.elb_application_lb:
    name: test-alb
    subnets:
      - subnet-12345678
      - subnet-87654321
    security_groups:
      - sg-12345678
    scheme: internal
    listeners:
      - Protocol: HTTPS
        Port: 443
        DefaultActions:
          - Type: forward
            TargetGroupName: test-target-group
        Certificates:
          - CertificateArn: arn:aws:iam::12345678987:server-certificate/test.domain.com
        SslPolicy: ELBSecurityPolicy-2015-05
        Rules:
          - Conditions:
              - Field: path-pattern
                Values:
                  - '/test'
            Priority: '1'
            Actions:
              - TargetGroupName: test-target-group
                Type: forward
          - Conditions:
              - Field: path-pattern
                Values:
                  - "/redirect-path/*"
            Priority: '2'
            Actions:
              - Type: redirect
                RedirectConfig:
                  Host: "#{host}"
                  Path: "/example/redir" # or /#{path}
                  Port: "#{port}"
                  Protocol: "#{protocol}"
                  Query: "#{query}"
                  StatusCode: "HTTP_302" # or HTTP_301
          - Conditions:
              - Field: path-pattern
                Values:
                  - "/fixed-response-path/"
            Priority: '3'
            Actions:
              - Type: fixed-response
                FixedResponseConfig:
                  ContentType: "text/plain"
                  MessageBody: "This is the page you're looking for"
                  StatusCode: "200"
          - Conditions:
              - Field: host-header
                Values:
                  - "hostname.domain.com"
                  - "alternate.domain.com"
            Priority: '4'
            Actions:
              - TargetGroupName: test-target-group
                Type: forward
    state: present

# Remove an ALB
- community.aws.elb_application_lb:
    name: myalb
    state: absent

'''

RETURN = r'''
access_logs_s3_bucket:
    description: The name of the S3 bucket for the access logs.
    returned: when state is present
    type: str
    sample: "mys3bucket"
access_logs_s3_enabled:
    description: Indicates whether access logs stored in Amazon S3 are enabled.
    returned: when state is present
    type: bool
    sample: true
access_logs_s3_prefix:
    description: The prefix for the location in the S3 bucket.
    returned: when state is present
    type: str
    sample: "my/logs"
availability_zones:
    description: The Availability Zones for the load balancer.
    returned: when state is present
    type: list
    sample: [{ "load_balancer_addresses": [], "subnet_id": "subnet-aabbccddff", "zone_name": "ap-southeast-2a" }]
canonical_hosted_zone_id:
    description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
    returned: when state is present
    type: str
    sample: "ABCDEF12345678"
changed:
    description: Whether an ALB was created/updated/deleted
    returned: always
    type: bool
    sample: true
created_time:
    description: The date and time the load balancer was created.
    returned: when state is present
    type: str
    sample: "2015-02-12T02:14:02+00:00"
deletion_protection_enabled:
    description: Indicates whether deletion protection is enabled.
    returned: when state is present
    type: bool
    sample: true
dns_name:
    description: The public DNS name of the load balancer.
    returned: when state is present
    type: str
    sample: "internal-my-elb-123456789.ap-southeast-2.elb.amazonaws.com"
idle_timeout_timeout_seconds:
    description: The idle timeout value, in seconds.
    returned: when state is present
    type: int
    sample: 60
ip_address_type:
    description: The type of IP addresses used by the subnets for the load balancer.
    returned: when state is present
    type: str
    sample: "ipv4"
listeners:
    description: Information about the listeners.
    returned: when state is present
    type: complex
    contains:
        listener_arn:
            description: The Amazon Resource Name (ARN) of the listener.
            returned: when state is present
            type: str
            sample: ""
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            returned: when state is present
            type: str
            sample: ""
        port:
            description: The port on which the load balancer is listening.
            returned: when state is present
            type: int
            sample: 80
        protocol:
            description: The protocol for connections from clients to the load balancer.
            returned: when state is present
            type: str
            sample: "HTTPS"
        certificates:
            description: The SSL server certificate.
            returned: when state is present
            type: complex
            contains:
                certificate_arn:
                    description: The Amazon Resource Name (ARN) of the certificate.
                    returned: when state is present
                    type: str
                    sample: ""
        ssl_policy:
            description: The security policy that defines which ciphers and protocols are supported.
            returned: when state is present
            type: str
            sample: ""
        default_actions:
            description: The default actions for the listener.
            returned: when state is present
            type: str
            contains:
                type:
                    description: The type of action.
                    returned: when state is present
                    type: str
                    sample: ""
                target_group_arn:
                    description: The Amazon Resource Name (ARN) of the target group.
                    returned: when state is present
                    type: str
                    sample: ""
load_balancer_arn:
    description: The Amazon Resource Name (ARN) of the load balancer.
    returned: when state is present
    type: str
    sample: "arn:aws:elasticloadbalancing:ap-southeast-2:0123456789:loadbalancer/app/my-alb/001122334455"
load_balancer_name:
    description: The name of the load balancer.
    returned: when state is present
    type: str
    sample: "my-alb"
routing_http2_enabled:
    description: Indicates whether HTTP/2 is enabled.
    returned: when state is present
    type: bool
    sample: true
routing_http_desync_mitigation_mode:
    description: Determines how the load balancer handles requests that might pose a security risk to an application.
    returned: when state is present
    type: str
    sample: "defensive"
routing_http_drop_invalid_header_fields_enabled:
    description: Indicates whether HTTP headers with invalid header fields are removed by the load balancer (true) or routed to targets (false).
    returned: when state is present
    type: bool
    sample: false
routing_http_x_amzn_tls_version_and_cipher_suite_enabled:
    description: Indicates whether the two headers are added to the client request before sending it to the target.
    returned: when state is present
    type: bool
    sample: false
routing_http_xff_client_port_enabled:
    description: Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer.
    returned: when state is present
    type: bool
    sample: false
scheme:
    description: Internet-facing or internal load balancer.
    returned: when state is present
    type: str
    sample: "internal"
security_groups:
    description: The IDs of the security groups for the load balancer.
    returned: when state is present
    type: list
    sample: ['sg-0011223344']
state:
    description: The state of the load balancer.
    returned: when state is present
    type: dict
    sample: {'code': 'active'}
tags:
    description: The tags attached to the load balancer.
    returned: when state is present
    type: dict
    sample: {
        'Tag': 'Example'
    }
type:
    description: The type of load balancer.
    returned: when state is present
    type: str
    sample: "application"
vpc_id:
    description: The ID of the VPC for the load balancer.
    returned: when state is present
    type: str
    sample: "vpc-0011223344"
waf_fail_open_enabled:
    description: Indicates whether to allow a AWS WAF-enabled load balancer to route requests to targets if it is unable to forward the request to AWS WAF.
    returned: when state is present
    type: bool
    sample: false
'''
try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import (
    ApplicationLoadBalancer,
    ELBListener,
    ELBListenerRule,
    ELBListenerRules,
    ELBListeners,
)
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import get_elb_listener_rules


@AWSRetry.jittered_backoff()
def describe_sgs_with_backoff(connection, **params):
    paginator = connection.get_paginator('describe_security_groups')
    return paginator.paginate(**params).build_full_result()['SecurityGroups']


def find_default_sg(connection, module, vpc_id):
    """
    Finds the default security group for the given VPC ID.
    """
    filters = ansible_dict_to_boto3_filter_list({'vpc-id': vpc_id, 'group-name': 'default'})
    try:
        sg = describe_sgs_with_backoff(connection, Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='No default security group found for VPC {0}'.format(vpc_id))
    if len(sg) == 1:
        return sg[0]['GroupId']
    elif len(sg) == 0:
        module.fail_json(msg='No default security group found for VPC {0}'.format(vpc_id))
    else:
        module.fail_json(msg='Multiple security groups named "default" found for VPC {0}'.format(vpc_id))


def create_or_update_alb(alb_obj):
    """Create ALB or modify main attributes. json_exit here"""
    if alb_obj.elb:
        # ALB exists so check subnets, security groups and tags match what has been passed
        # Subnets
        if not alb_obj.compare_subnets():
            if alb_obj.module.check_mode:
                alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')
            alb_obj.modify_subnets()

        # Security Groups
        if not alb_obj.compare_security_groups():
            if alb_obj.module.check_mode:
                alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')
            alb_obj.modify_security_groups()

        # ALB attributes
        if not alb_obj.compare_elb_attributes():
            if alb_obj.module.check_mode:
                alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')
            alb_obj.update_elb_attributes()
            alb_obj.modify_elb_attributes()

        # Tags - only need to play with tags if tags parameter has been set to something
        if alb_obj.tags is not None:

            tags_need_modify, tags_to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(alb_obj.elb['tags']),
                                                                boto3_tag_list_to_ansible_dict(alb_obj.tags), alb_obj.purge_tags)

            # Exit on check_mode
            if alb_obj.module.check_mode and (tags_need_modify or tags_to_delete):
                alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')

            # Delete necessary tags
            if tags_to_delete:
                alb_obj.delete_tags(tags_to_delete)

            # Add/update tags
            if tags_need_modify:
                alb_obj.modify_tags()

    else:
        # Create load balancer
        if alb_obj.module.check_mode:
            alb_obj.module.exit_json(changed=True, msg='Would have created ALB if not in check mode.')
        alb_obj.create_elb()

    # Listeners
    listeners_obj = ELBListeners(alb_obj.connection, alb_obj.module, alb_obj.elb['LoadBalancerArn'])
    listeners_to_add, listeners_to_modify, listeners_to_delete = listeners_obj.compare_listeners()

    # Exit on check_mode
    if alb_obj.module.check_mode and (listeners_to_add or listeners_to_modify or listeners_to_delete):
        alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')

    # Delete listeners
    for listener_to_delete in listeners_to_delete:
        listener_obj = ELBListener(alb_obj.connection, alb_obj.module, listener_to_delete, alb_obj.elb['LoadBalancerArn'])
        listener_obj.delete()
        listeners_obj.changed = True

    # Add listeners
    for listener_to_add in listeners_to_add:
        listener_obj = ELBListener(alb_obj.connection, alb_obj.module, listener_to_add, alb_obj.elb['LoadBalancerArn'])
        listener_obj.add()
        listeners_obj.changed = True

    # Modify listeners
    for listener_to_modify in listeners_to_modify:
        listener_obj = ELBListener(alb_obj.connection, alb_obj.module, listener_to_modify, alb_obj.elb['LoadBalancerArn'])
        listener_obj.modify()
        listeners_obj.changed = True

    # If listeners changed, mark ALB as changed
    if listeners_obj.changed:
        alb_obj.changed = True

    # Rules of each listener
    for listener in listeners_obj.listeners:
        if 'Rules' in listener:
            rules_obj = ELBListenerRules(alb_obj.connection, alb_obj.module, alb_obj.elb['LoadBalancerArn'], listener['Rules'], listener['Port'])
            rules_to_add, rules_to_modify, rules_to_delete = rules_obj.compare_rules()

            # Exit on check_mode
            if alb_obj.module.check_mode and (rules_to_add or rules_to_modify or rules_to_delete):
                alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')

            # Delete rules
            if alb_obj.module.params['purge_rules']:
                for rule in rules_to_delete:
                    rule_obj = ELBListenerRule(alb_obj.connection, alb_obj.module, {'RuleArn': rule}, rules_obj.listener_arn)
                    rule_obj.delete()
                    alb_obj.changed = True

            # Add rules
            for rule in rules_to_add:
                rule_obj = ELBListenerRule(alb_obj.connection, alb_obj.module, rule, rules_obj.listener_arn)
                rule_obj.create()
                alb_obj.changed = True

            # Modify rules
            for rule in rules_to_modify:
                rule_obj = ELBListenerRule(alb_obj.connection, alb_obj.module, rule, rules_obj.listener_arn)
                rule_obj.modify()
                alb_obj.changed = True

    # Update ALB ip address type only if option has been provided
    if alb_obj.module.params.get('ip_address_type') and alb_obj.elb_ip_addr_type != alb_obj.module.params.get('ip_address_type'):
        # Exit on check_mode
        if alb_obj.module.check_mode:
            alb_obj.module.exit_json(changed=True, msg='Would have updated ALB if not in check mode.')

        alb_obj.modify_ip_address_type(alb_obj.module.params.get('ip_address_type'))

    # Exit on check_mode - no changes
    if alb_obj.module.check_mode:
        alb_obj.module.exit_json(changed=False, msg='IN CHECK MODE - no changes to make to ALB specified.')

    # Get the ALB again
    alb_obj.update()

    # Get the ALB listeners again
    listeners_obj.update()

    # Update the ALB attributes
    alb_obj.update_elb_attributes()

    # Convert to snake_case and merge in everything we want to return to the user
    snaked_alb = camel_dict_to_snake_dict(alb_obj.elb)
    snaked_alb.update(camel_dict_to_snake_dict(alb_obj.elb_attributes))
    snaked_alb['listeners'] = []
    for listener in listeners_obj.current_listeners:
        # For each listener, get listener rules
        listener['rules'] = get_elb_listener_rules(alb_obj.connection, alb_obj.module, listener['ListenerArn'])
        snaked_alb['listeners'].append(camel_dict_to_snake_dict(listener))

    # Change tags to ansible friendly dict
    snaked_alb['tags'] = boto3_tag_list_to_ansible_dict(snaked_alb['tags'])

    # ip address type
    snaked_alb['ip_address_type'] = alb_obj.get_elb_ip_address_type()

    alb_obj.module.exit_json(changed=alb_obj.changed, **snaked_alb)


def delete_alb(alb_obj):

    if alb_obj.elb:

        # Exit on check_mode
        if alb_obj.module.check_mode:
            alb_obj.module.exit_json(changed=True, msg='Would have deleted ALB if not in check mode.')

        listeners_obj = ELBListeners(alb_obj.connection, alb_obj.module, alb_obj.elb['LoadBalancerArn'])
        for listener_to_delete in [i['ListenerArn'] for i in listeners_obj.current_listeners]:
            listener_obj = ELBListener(alb_obj.connection, alb_obj.module, listener_to_delete, alb_obj.elb['LoadBalancerArn'])
            listener_obj.delete()

        alb_obj.delete()

    else:

        # Exit on check_mode - no changes
        if alb_obj.module.check_mode:
            alb_obj.module.exit_json(changed=False, msg='IN CHECK MODE - ALB already absent.')

    alb_obj.module.exit_json(changed=alb_obj.changed)


def main():

    argument_spec = dict(
        access_logs_enabled=dict(type='bool'),
        access_logs_s3_bucket=dict(type='str'),
        access_logs_s3_prefix=dict(type='str'),
        deletion_protection=dict(type='bool'),
        http2=dict(type='bool'),
        http_desync_mitigation_mode=dict(type='str', choices=['monitor', 'defensive', 'strictest']),
        http_drop_invalid_header_fields=dict(type='bool'),
        http_x_amzn_tls_version_and_cipher_suite=dict(type='bool'),
        http_xff_client_port=dict(type='bool'),
        idle_timeout=dict(type='int'),
        listeners=dict(type='list',
                       elements='dict',
                       options=dict(
                           Protocol=dict(type='str', required=True),
                           Port=dict(type='int', required=True),
                           SslPolicy=dict(type='str'),
                           Certificates=dict(type='list', elements='dict'),
                           DefaultActions=dict(type='list', required=True, elements='dict'),
                           Rules=dict(type='list', elements='dict')
                       )
                       ),
        name=dict(required=True, type='str'),
        purge_listeners=dict(default=True, type='bool'),
        purge_tags=dict(default=True, type='bool'),
        subnets=dict(type='list', elements='str'),
        security_groups=dict(type='list', elements='str'),
        scheme=dict(default='internet-facing', choices=['internet-facing', 'internal']),
        state=dict(choices=['present', 'absent'], default='present'),
        tags=dict(type='dict', aliases=['resource_tags']),
        waf_fail_open=dict(type='bool'),
        wait_timeout=dict(type='int'),
        wait=dict(default=False, type='bool'),
        purge_rules=dict(default=True, type='bool'),
        ip_address_type=dict(type='str', choices=['ipv4', 'dualstack'])
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ('state', 'present', ['subnets', 'security_groups'])
                              ],
                              required_together=[
                                  ['access_logs_enabled', 'access_logs_s3_bucket']
                              ],
                              supports_check_mode=True,
                              )

    # Quick check of listeners parameters
    listeners = module.params.get("listeners")
    if listeners is not None:
        for listener in listeners:
            for key in listener.keys():
                if key == 'Protocol' and listener[key] == 'HTTPS':
                    if listener.get('SslPolicy') is None:
                        module.fail_json(msg="'SslPolicy' is a required listener dict key when Protocol = HTTPS")

                    if listener.get('Certificates') is None:
                        module.fail_json(msg="'Certificates' is a required listener dict key when Protocol = HTTPS")

    connection = module.client('elbv2')
    connection_ec2 = module.client('ec2')

    state = module.params.get("state")

    alb = ApplicationLoadBalancer(connection, connection_ec2, module)

    # Update security group if default is specified
    if alb.elb and module.params.get('security_groups') == []:
        module.params['security_groups'] = [find_default_sg(connection_ec2, module, alb.elb['VpcId'])]
        alb = ApplicationLoadBalancer(connection, connection_ec2, module)

    if state == 'present':
        create_or_update_alb(alb)
    elif state == 'absent':
        delete_alb(alb)


if __name__ == '__main__':
    main()

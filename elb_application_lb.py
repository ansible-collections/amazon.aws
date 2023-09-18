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
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
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
      - Indicates whether deletion protection for the ELB is enabled.
      - Defaults to C(false).
    type: bool
  http2:
    description:
      - Indicates whether to enable HTTP2 routing.
      - Defaults to C(false).
    type: bool
  idle_timeout:
    description:
      - The number of seconds to wait before an idle connection is closed.
    type: int
  listeners:
    description:
      - A list of dicts containing listeners to attach to the ELB. See examples for detail of the dict required. Note that listener keys
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
                Priority:
                    type: int
                    description: The rule priority.
                Actions:
                    type: list
                    description: Actions to apply if all of the rule's conditions are met.
  name:
    description:
      - The name of the load balancer. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric
        characters or hyphens, and must not begin or end with a hyphen.
    required: true
    type: str
  purge_listeners:
    description:
      - If C(yes), existing listeners will be purged from the ELB to match exactly what is defined by I(listeners) parameter.
      - If the I(listeners) parameter is not set then listeners will not be modified.
    default: yes
    type: bool
  purge_tags:
    description:
      - If yes, existing tags will be purged from the resource to match exactly what is defined by I(tags) parameter.
      - If the I(tags) parameter is not set then tags will not be modified.
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
    default: []
    type: list
    elements: str
  scheme:
    description:
      - Internet-facing or internal load balancer. An ELB scheme can not be modified after creation.
    default: internet-facing
    choices: [ 'internet-facing', 'internal' ]
    type: str
  state:
    description:
      - Create or destroy the load balancer.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  tags:
    description:
      - A dictionary of one or more tags to assign to the load balancer.
    type: dict
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
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

notes:
  - Listeners are matched based on port. If a listener's port is changed then a new listener will be created.
  - Listener rules are matched based on priority. If a rule's priority is changed then a new rule will be created.
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ELB and attach a listener
- community.aws.elb_application_lb:
    name: myelb
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

# Create an ELB and attach a listener with logging enabled
- community.aws.elb_application_lb:
    access_logs_enabled: yes
    access_logs_s3_bucket: mybucket
    access_logs_s3_prefix: "logs"
    name: myelb
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

# Remove an ELB
- community.aws.elb_application_lb:
    name: myelb
    state: absent

'''

RETURN = r'''
access_logs_s3_bucket:
    description: The name of the S3 bucket for the access logs.
    returned: when state is present
    type: str
    sample: mys3bucket
access_logs_s3_enabled:
    description: Indicates whether access logs stored in Amazon S3 are enabled.
    returned: when state is present
    type: str
    sample: true
access_logs_s3_prefix:
    description: The prefix for the location in the S3 bucket.
    returned: when state is present
    type: str
    sample: my/logs
availability_zones:
    description: The Availability Zones for the load balancer.
    returned: when state is present
    type: list
    sample: "[{'subnet_id': 'subnet-aabbccddff', 'zone_name': 'ap-southeast-2a'}]"
canonical_hosted_zone_id:
    description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
    returned: when state is present
    type: str
    sample: ABCDEF12345678
created_time:
    description: The date and time the load balancer was created.
    returned: when state is present
    type: str
    sample: "2015-02-12T02:14:02+00:00"
deletion_protection_enabled:
    description: Indicates whether deletion protection is enabled.
    returned: when state is present
    type: str
    sample: true
dns_name:
    description: The public DNS name of the load balancer.
    returned: when state is present
    type: str
    sample: internal-my-elb-123456789.ap-southeast-2.elb.amazonaws.com
idle_timeout_timeout_seconds:
    description: The idle timeout value, in seconds.
    returned: when state is present
    type: int
    sample: 60
ip_address_type:
    description:  The type of IP addresses used by the subnets for the load balancer.
    returned: when state is present
    type: str
    sample: ipv4
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
            sample: HTTPS
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
    sample: arn:aws:elasticloadbalancing:ap-southeast-2:0123456789:loadbalancer/app/my-elb/001122334455
load_balancer_name:
    description: The name of the load balancer.
    returned: when state is present
    type: str
    sample: my-elb
routing_http2_enabled:
    description: Indicates whether HTTP/2 is enabled.
    returned: when state is present
    type: str
    sample: true
scheme:
    description: Internet-facing or internal load balancer.
    returned: when state is present
    type: str
    sample: internal
security_groups:
    description: The IDs of the security groups for the load balancer.
    returned: when state is present
    type: list
    sample: ['sg-0011223344']
state:
    description: The state of the load balancer.
    returned: when state is present
    type: dict
    sample: "{'code': 'active'}"
tags:
    description: The tags attached to the load balancer.
    returned: when state is present
    type: dict
    sample: "{
        'Tag': 'Example'
    }"
type:
    description: The type of load balancer.
    returned: when state is present
    type: str
    sample: application
vpc_id:
    description: The ID of the VPC for the load balancer.
    returned: when state is present
    type: str
    sample: vpc-0011223344
'''

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict, compare_aws_tags

from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import (
    ApplicationLoadBalancer,
    ELBListener,
    ELBListenerRule,
    ELBListenerRules,
    ELBListeners,
)
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import get_elb_listener_rules


def create_or_update_elb(elb_obj):
    """Create ELB or modify main attributes. json_exit here"""

    if elb_obj.elb:
        # ELB exists so check subnets, security groups and tags match what has been passed

        # Subnets
        if not elb_obj.compare_subnets():
            elb_obj.modify_subnets()

        # Security Groups
        if not elb_obj.compare_security_groups():
            elb_obj.modify_security_groups()

        # Tags - only need to play with tags if tags parameter has been set to something
        if elb_obj.tags is not None:

            # Delete necessary tags
            tags_need_modify, tags_to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(elb_obj.elb['tags']),
                                                                boto3_tag_list_to_ansible_dict(elb_obj.tags), elb_obj.purge_tags)
            if tags_to_delete:
                elb_obj.delete_tags(tags_to_delete)

            # Add/update tags
            if tags_need_modify:
                elb_obj.modify_tags()

    else:
        # Create load balancer
        elb_obj.create_elb()

    # ELB attributes
    elb_obj.update_elb_attributes()
    elb_obj.modify_elb_attributes()

    # Listeners
    listeners_obj = ELBListeners(elb_obj.connection, elb_obj.module, elb_obj.elb['LoadBalancerArn'])

    listeners_to_add, listeners_to_modify, listeners_to_delete = listeners_obj.compare_listeners()

    # Delete listeners
    for listener_to_delete in listeners_to_delete:
        listener_obj = ELBListener(elb_obj.connection, elb_obj.module, listener_to_delete, elb_obj.elb['LoadBalancerArn'])
        listener_obj.delete()
        listeners_obj.changed = True

    # Add listeners
    for listener_to_add in listeners_to_add:
        listener_obj = ELBListener(elb_obj.connection, elb_obj.module, listener_to_add, elb_obj.elb['LoadBalancerArn'])
        listener_obj.add()
        listeners_obj.changed = True

    # Modify listeners
    for listener_to_modify in listeners_to_modify:
        listener_obj = ELBListener(elb_obj.connection, elb_obj.module, listener_to_modify, elb_obj.elb['LoadBalancerArn'])
        listener_obj.modify()
        listeners_obj.changed = True

    # If listeners changed, mark ELB as changed
    if listeners_obj.changed:
        elb_obj.changed = True

    # Rules of each listener
    for listener in listeners_obj.listeners:
        if 'Rules' in listener:
            rules_obj = ELBListenerRules(elb_obj.connection, elb_obj.module, elb_obj.elb['LoadBalancerArn'], listener['Rules'], listener['Port'])

            rules_to_add, rules_to_modify, rules_to_delete = rules_obj.compare_rules()

            # Delete rules
            if elb_obj.module.params['purge_rules']:
                for rule in rules_to_delete:
                    rule_obj = ELBListenerRule(elb_obj.connection, elb_obj.module, {'RuleArn': rule}, rules_obj.listener_arn)
                    rule_obj.delete()
                    elb_obj.changed = True

            # Add rules
            for rule in rules_to_add:
                rule_obj = ELBListenerRule(elb_obj.connection, elb_obj.module, rule, rules_obj.listener_arn)
                rule_obj.create()
                elb_obj.changed = True

            # Modify rules
            for rule in rules_to_modify:
                rule_obj = ELBListenerRule(elb_obj.connection, elb_obj.module, rule, rules_obj.listener_arn)
                rule_obj.modify()
                elb_obj.changed = True

    # Get the ELB again
    elb_obj.update()

    # Get the ELB listeners again
    listeners_obj.update()

    # Update the ELB attributes
    elb_obj.update_elb_attributes()

    # Convert to snake_case and merge in everything we want to return to the user
    snaked_elb = camel_dict_to_snake_dict(elb_obj.elb)
    snaked_elb.update(camel_dict_to_snake_dict(elb_obj.elb_attributes))
    snaked_elb['listeners'] = []
    for listener in listeners_obj.current_listeners:
        # For each listener, get listener rules
        listener['rules'] = get_elb_listener_rules(elb_obj.connection, elb_obj.module, listener['ListenerArn'])
        snaked_elb['listeners'].append(camel_dict_to_snake_dict(listener))

    # Change tags to ansible friendly dict
    snaked_elb['tags'] = boto3_tag_list_to_ansible_dict(snaked_elb['tags'])

    elb_obj.module.exit_json(changed=elb_obj.changed, **snaked_elb)


def delete_elb(elb_obj):

    if elb_obj.elb:
        elb_obj.delete()

    elb_obj.module.exit_json(changed=elb_obj.changed)


def main():

    argument_spec = dict(
        access_logs_enabled=dict(type='bool'),
        access_logs_s3_bucket=dict(type='str'),
        access_logs_s3_prefix=dict(type='str'),
        deletion_protection=dict(type='bool'),
        http2=dict(type='bool'),
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
        tags=dict(type='dict'),
        wait_timeout=dict(type='int'),
        wait=dict(default=False, type='bool'),
        purge_rules=dict(default=True, type='bool')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ('state', 'present', ['subnets', 'security_groups'])
                              ],
                              required_together=[
                                  ['access_logs_enabled', 'access_logs_s3_bucket']
                              ]
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

    elb = ApplicationLoadBalancer(connection, connection_ec2, module)

    if state == 'present':
        create_or_update_elb(elb)
    else:
        delete_elb(elb)


if __name__ == '__main__':
    main()

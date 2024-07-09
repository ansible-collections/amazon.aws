#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: elb_application_lb
version_added: 5.0.0
short_description: Manage an Application Load Balancer
description:
  - Manage an AWS Application Elastic Load Balancer. See U(https://aws.amazon.com/blogs/aws/new-aws-application-load-balancer/) for details.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - "Rob White (@wimnat)"
options:
  access_logs_enabled:
    description:
      - Whether or not to enable access logs.
      - When set, O(access_logs_s3_bucket) must also be set.
    type: bool
  access_logs_s3_bucket:
    description:
      - The name of the S3 bucket for the access logs.
      - The bucket must exist in the same
        region as the load balancer and have a bucket policy that grants Elastic Load Balancing permission to write to the bucket.
      - Required if access logs in Amazon S3 are enabled.
      - When set, O(access_logs_enabled) must also be set.
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
      - Defaults to V(false).
    type: bool
  http2:
    description:
      - Indicates whether to enable HTTP2 routing.
      - Defaults to V(True).
    type: bool
  http_desync_mitigation_mode:
    description:
      - Determines how the load balancer handles requests that might pose a security risk to an application.
      - Defaults to V(defensive).
    type: str
    choices: ['monitor', 'defensive', 'strictest']
    version_added: 3.2.0
    version_added_collection: community.aws
  http_drop_invalid_header_fields:
    description:
      - Indicates whether HTTP headers with invalid header fields are removed by the load balancer V(true) or routed to targets V(false).
      - Defaults to V(false).
    type: bool
    version_added: 3.2.0
    version_added_collection: community.aws
  http_x_amzn_tls_version_and_cipher_suite:
    description:
      - Indicates whether the two headers are added to the client request before sending it to the target.
      - Defaults to V(false).
    type: bool
    version_added: 3.2.0
    version_added_collection: community.aws
  http_xff_client_port:
    description:
      - Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer.
      - Defaults to V(false).
    type: bool
    version_added: 3.2.0
    version_added_collection: community.aws
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
                    description:
                      - The Amazon Resource Name (ARN) of the target group.
                      - Mutually exclusive with O(listeners.DefaultActions.TargetGroupName).
                    type: str
                TargetGroupName:
                    description:
                      - The name of the target group.
                      - Mutually exclusive with O(listeners.DefaultActions.TargetGroupArn).
        Rules:
            type: list
            elements: dict
            description:
              - A list of ALB Listener Rules.
              - 'For the complete documentation of possible Conditions and Actions please see the boto3 documentation:'
              - 'U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_rule)'
              - >
                Keep in mind that AWS uses default values for parameters that are not requested. For example for V(Scope)
                and V(SessionTimeout) when the action type is V(authenticate-oidc).
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
      - If V(true), existing listeners will be purged from the ALB to match exactly what is defined by O(listeners) parameter.
      - If the O(listeners) parameter is not set then listeners will not be modified.
    default: true
    type: bool
  subnets:
    description:
      - A list of the IDs of the subnets to attach to the load balancer. You can specify only one subnet per Availability Zone. You must specify subnets from
        at least two Availability Zones.
      - Required if O(state=present).
    type: list
    elements: str
  security_groups:
    description:
      - A list of the names or IDs of the security groups to assign to the load balancer.
      - Required if O(state=present).
      - If V([]), the VPC's default security group will be used.
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
    default: false
    type: bool
  wait_timeout:
    description:
      - The time in seconds to use in conjunction with O(wait).
    type: int
  purge_rules:
    description:
      - When set to V(false), keep the existing load balancer rules in place. Will modify and add, but will not delete.
    default: true
    type: bool
  ip_address_type:
    description:
      - Sets the type of IP addresses used by the subnets of the specified Application Load Balancer.
    choices: [ 'ipv4', 'dualstack' ]
    type: str
  waf_fail_open:
    description:
      - Indicates whether to allow a AWS WAF-enabled load balancer to route requests to targets if it is unable to forward the request to AWS WAF.
      - Defaults to V(false).
    type: bool
    version_added: 3.2.0
    version_added_collection: community.aws
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3

notes:
  - Listeners are matched based on port. If a listener's port is changed then a new listener will be created.
  - Listener rules are matched based on priority. If a rule's priority is changed then a new rule will be created.
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ALB and attach a listener
- amazon.aws.elb_application_lb:
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
        Certificates: # The ARN of the certificate
          - CertificateArn: arn:aws:iam::123456789012:server-certificate/test.domain.com
        DefaultActions:
          - Type: forward # Required.
            TargetGroupName: # Required. The name of the target group
    state: present

# Create an ALB and attach a listener with logging enabled
- amazon.aws.elb_application_lb:
    access_logs_enabled: true
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
        Certificates: # The ARN of the certificate
          - CertificateArn: arn:aws:iam::123456789012:server-certificate/test.domain.com
        DefaultActions:
          - Type: forward # Required.
            TargetGroupName: # Required. The name of the target group
    state: present

# Create an ALB with listeners and rules
- amazon.aws.elb_application_lb:
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
          - CertificateArn: arn:aws:iam::123456789012:server-certificate/test.domain.com
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

# Create an ALB with a listener having multiple listener certificates
- amazon.aws.elb_application_lb:
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
        Certificates: # The ARN of the certificate (first certificate in the list will be set as default certificate)
          - CertificateArn: arn:aws:iam::123456789012:server-certificate/test.domain.com
          - CertificateArn: arn:aws:iam::123456789012:server-certificate/secondtest.domain.com
          - CertificateArn: arn:aws:iam::123456789012:server-certificate/thirdtest.domain.com
        DefaultActions:
          - Type: forward # Required.
            TargetGroupName: # Required. The name of the target group
    state: present

# Remove an ALB
- amazon.aws.elb_application_lb:
    name: myalb
    state: absent
"""

RETURN = r"""
access_logs_s3_bucket:
    description: The name of the S3 bucket for the access logs.
    returned: when O(state=present)
    type: str
    sample: "mys3bucket"
access_logs_s3_enabled:
    description: Indicates whether access logs stored in Amazon S3 are enabled.
    returned: when O(state=present)
    type: str
    sample: "true"
access_logs_s3_prefix:
    description: The prefix for the location in the S3 bucket.
    returned: when O(state=present)
    type: str
    sample: "my/logs"
availability_zones:
    description: The Availability Zones for the load balancer.
    returned: when O(state=present)
    type: list
    elements: dict
    contains:
        load_balancer_addresses:
            description: Information about static IP addresses for a load balancer.
            returned: when O(state=present)
            type: list
            elements: dict
            contains:
                ip_address:
                    description: The static IP address.
                    returned: when O(state=present)
                    type: str
                allocation_id:
                    description: The allocation ID of the Elastic IP address for an internal-facing load balancer.
                    returned: when O(state=present)
                    type: str
                private_ipv4_address:
                    returned: when O(state=present)
                    description: The private IPv4 address for an internal load balancer.
                    type: str
                ipv6_address:
                    returned: when O(state=present)
                    description: The IPv6 address.
                    type: str
        subnet_id:
            description: The ID of the subnet.
            returned: when O(state=present)
            type: str
        zone_name:
            description: The name of the Availability Zone.
            returned: when O(state=present)
            type: str
    sample: [{ "load_balancer_addresses": [], "subnet_id": "subnet-aabbccddff", "zone_name": "ap-southeast-2a" }]
canonical_hosted_zone_id:
    description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
    returned: when O(state=present)
    type: str
    sample: "ABCDEF12345678"
changed:
    description: Whether an ALB was created/updated/deleted.
    returned: always
    type: bool
    sample: true
created_time:
    description: The date and time the load balancer was created.
    returned: when O(state=present)
    type: str
    sample: "2015-02-12T02:14:02+00:00"
client_keep_alive_seconds:
    description: The client keep alive value, in seconds.
    returned: when O(state=present)
    type: str
    sample: "3600"
connection_logs_s3_bucket:
    description: The name of the S3 bucket for the connection logs.
    returned: when O(state=present)
    type: str
    sample: ""
connection_logs_s3_enabled:
    description: Indicates whether connection logs are enabled.
    returned: when O(state=present)
    type: str
    sample: "false"
connection_logs_s3_prefix:
    description: The prefix for the location in the S3 bucket for the connection logs.
    returned: when O(state=present)
    type: str
    sample: ""
deletion_protection_enabled:
    description: Indicates whether deletion protection is enabled.
    returned: when O(state=present)
    type: str
    sample: "true"
dns_name:
    description: The public DNS name of the load balancer.
    returned: when O(state=present)
    type: str
    sample: "internal-my-elb-123456789.ap-southeast-2.elb.amazonaws.com"
idle_timeout_timeout_seconds:
    description: The idle timeout value, in seconds.
    returned: when O(state=present)
    type: str
    sample: "60"
ip_address_type:
    description: The type of IP addresses used by the subnets for the load balancer.
    returned: when O(state=present)
    type: str
    sample: "ipv4"
ipv6_deny_all_igw_traffic:
    description: Locks internet gateway (IGW) access to the load balancer.
    returned: when O(state=present)
    type: str
    sample: "false"
listeners:
    description: Information about the listeners.
    returned: when O(state=present)
    type: list
    elements: dict
    contains:
        listener_arn:
            description: The Amazon Resource Name (ARN) of the listener.
            returned: when O(state=present)
            type: str
            sample: "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/alb-test-169eb5ba/1659336d4100d496/8367c4262cc1d0cc"
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            returned: when O(state=present)
            type: str
            sample: "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/alb-test-169eb5ba/1659336d4100d496"
        port:
            description: The port on which the load balancer is listening.
            returned: when O(state=present)
            type: int
            sample: 80
        protocol:
            description: The protocol for connections from clients to the load balancer.
            returned: when O(state=present)
            type: str
            sample: "HTTPS"
        rules:
            description: List of listener rules.
            returned: when O(state=present)
            type: list
            elements: dict
            contains:
                rule_arn:
                    description: The Amazon Resource Name (ARN) of the rule.
                    returned: when O(state=present)
                    type: str
                    sample: ""
                priority:
                    description: The priority.
                    returned: when O(state=present)
                    type: str
                    sample: "default"
                is_default:
                    description: Indicates whether this is the default rule.
                    returned: when O(state=present)
                    type: bool
                    sample: false
                conditions:
                    description: The conditions.
                    returned: when O(state=present)
                    type: list
                    sample: []
                actions:
                    description: The actions.
                    returned: when O(state=present)
                    type: list
                    elements: dict
                    contains:
                        type:
                            description: The type of action.
                            returned: when O(state=present)
                            type: str
                        target_group_arn:
                            description: The Amazon Resource Name (ARN) of the target group.
                            returned: when O(state=present)
                            type: str
                        forward_config:
                            description: Information for creating an action that distributes requests among one or more target groups.
                            returned: when O(state=present)
                            type: dict
                            contains:
                                target_groups:
                                    description: The target groups.
                                    returned: when O(state=present)
                                    type: dict
                                    contains:
                                        target_group_arn:
                                            description: The Amazon Resource Name (ARN) of the target group.
                                            returned: when O(state=present)
                                            type: str
                                        weight:
                                            description: The weight.
                                            returned: when O(state=present)
                                            type: int
                                target_group_stickiness_config:
                                    description: The target group stickiness for the rule.
                                    returned: when O(state=present)
                                    type: dict
                                    contains:
                                        enabled:
                                            description: Indicates whether target group stickiness is enabled.
                                            returned: when O(state=present)
                                            type: bool
                    sample: [
                        {
                            "forward_config": {
                                "target_group_stickiness_config": {
                                    "enabled": false
                                },
                                "target_groups": [
                                    {
                                        "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test-169eb/09ba111f8079fb83",
                                        "weight": 1
                                    }
                                ]
                            },
                            "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test-169eb/09ba111f8079fb83",
                            "type": "forward"
                        }
                    ]
        certificates:
            description: The SSL server certificate.
            returned: when O(state=present)
            type: list
            elements: dict
            contains:
                certificate_arn:
                    description: The Amazon Resource Name (ARN) of the certificate.
                    returned: when O(state=present)
                    type: str
                    sample: "arn:aws:acm:us-east-1:123456789012:certificate/28d2f3d9-cb2f-4033-a9aa-e75e704125a2"
        ssl_policy:
            description: The security policy that defines which ciphers and protocols are supported.
            returned: when O(state=present)
            type: str
            sample: "ELBSecurityPolicy-2016-08"
        default_actions:
            description: The default actions for the listener.
            returned: when O(state=present)
            type: str
            contains:
                type:
                    description: The type of action.
                    returned: when O(state=present)
                    type: str
                    sample: "forward"
                target_group_arn:
                    description: The Amazon Resource Name (ARN) of the target group.
                    returned: when O(state=present)
                    type: str
                    sample: "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test-169eb5ba/09ba111f8079fb83"
                forward_config:
                    description: Information for creating an action that distributes requests among one or more target groups.
                    returned: when O(state=present)
                    type: dict
                    contains:
                        target_groups:
                            description: The target groups.
                            returned: when O(state=present)
                            type: dict
                            contains:
                                target_group_arn:
                                    description: The Amazon Resource Name (ARN) of the target group.
                                    returned: when O(state=present)
                                    type: str
                                weight:
                                    description: The weight.
                                    returned: when O(state=present)
                                    type: int
                        target_group_stickiness_config:
                            description: The target group stickiness for the rule.
                            returned: when O(state=present)
                            type: dict
                            contains:
                                enabled:
                                    description: Indicates whether target group stickiness is enabled.
                                    returned: when O(state=present)
                                    type: bool
            sample: [
                {
                    "forward_config": {
                        "target_group_stickiness_config": {
                            "enabled": false
                        },
                        "target_groups": [
                            {
                                "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test-2-98b7f374/bf43c68602c51c02",
                                "weight": 1
                            }
                        ]
                    },
                    "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test-2-98b7f374/bf43c68602c51c02",
                    "type": "forward"
                }
            ]
load_balancer_arn:
    description: The Amazon Resource Name (ARN) of the load balancer.
    returned: when O(state=present)
    type: str
    sample: "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:loadbalancer/app/my-alb/001122334455"
load_balancer_name:
    description: The name of the load balancer.
    returned: when O(state=present)
    type: str
    sample: "my-alb"
load_balancing_cross_zone_enabled:
    description: Indicates whether cross-zone load balancing is enabled.
    returned: when O(state=present)
    type: str
    sample: "true"
routing_http2_enabled:
    description: Indicates whether HTTP/2 is enabled.
    returned: when O(state=present)
    type: str
    sample: "true"
routing_http_desync_mitigation_mode:
    description: Determines how the load balancer handles requests that might pose a security risk to an application.
    returned: when O(state=present)
    type: str
    sample: "defensive"
routing_http_drop_invalid_header_fields_enabled:
    description: Indicates whether HTTP headers with invalid header fields are removed by the load balancer (true) or routed to targets (false).
    returned: when O(state=present)
    type: str
    sample: "false"
routing_http_preserve_host_header_enabled:
    description:
      - Indicates whether the Application Load Balancer should preserve the Host header in the HTTP request and send it to the target without any change.
    returned: when O(state=present)
    type: str
    sample: "false"
routing_http_x_amzn_tls_version_and_cipher_suite_enabled:
    description: Indicates whether the two headers are added to the client request before sending it to the target.
    returned: when O(state=present)
    type: str
    sample: "false"
routing_http_xff_client_port_enabled:
    description: Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer.
    returned: when O(state=present)
    type: str
    sample: "false"
routing_http_xff_header_processing_mode:
    description:
      - Enables you to modify, preserve, or remove the X-Forwarded-For header in the HTTP request before the Application Load Balancer sends the
        request to the target.
    returned: when O(state=present)
    type: str
    sample: "append"
scheme:
    description: Internet-facing or internal load balancer.
    returned: when O(state=present)
    type: str
    sample: "internal"
security_groups:
    description: The IDs of the security groups for the load balancer.
    returned: when O(state=present)
    type: list
    elements: str
    sample: ["sg-0011223344"]
state:
    description: The state of the load balancer.
    returned: when O(state=present)
    type: dict
    contains:
        code:
            description: The state code.
            type: str
        reason:
            description: A description of the state.
            returned: when available
            type: str
    sample: {"code": "active"}
tags:
    description: The tags attached to the load balancer.
    returned: when O(state=present)
    type: dict
    sample: {
        "Tag": "Example"
    }
type:
    description: The type of load balancer.
    returned: when O(state=present)
    type: str
    sample: "application"
vpc_id:
    description: The ID of the VPC for the load balancer.
    returned: when O(state=present)
    type: str
    sample: "vpc-0011223344"
waf_fail_open_enabled:
    description: Indicates whether to allow a AWS WAF-enabled load balancer to route requests to targets if it is unable to forward the request to AWS WAF.
    returned: when O(state=present)
    type: str
    sample: "false"
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import AnsibleELBv2Error
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import get_elb_listener_rules
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import ApplicationLoadBalancer
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import ELBListener
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import ELBListenerRule
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import ELBListenerRules
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import ELBListeners
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


@AWSRetry.jittered_backoff()
def describe_sgs_with_backoff(connection, **params):
    paginator = connection.get_paginator("describe_security_groups")
    return paginator.paginate(**params).build_full_result()["SecurityGroups"]


def find_default_sg(connection, module, vpc_id):
    """
    Finds the default security group for the given VPC ID.
    """
    filters = ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id, "group-name": "default"})
    try:
        sg = describe_sgs_with_backoff(connection, Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"No default security group found for VPC {vpc_id}")
    if len(sg) == 1:
        return sg[0]["GroupId"]
    elif len(sg) == 0:
        module.fail_json(msg=f"No default security group found for VPC {vpc_id}")
    else:
        module.fail_json(msg=f'Multiple security groups named "default" found for VPC {vpc_id}')


def create_or_update_alb(alb_obj: ApplicationLoadBalancer) -> None:
    """Create ALB or modify main attributes. json_exit here"""
    if alb_obj.elb:
        # ALB exists so check subnets, security groups and tags match what has been passed
        # Subnets
        if not alb_obj.compare_subnets():
            if alb_obj.check_mode:
                alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")
            alb_obj.modify_subnets()

        # Security Groups
        if not alb_obj.compare_security_groups():
            if alb_obj.check_mode:
                alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")
            alb_obj.modify_security_groups()

        # ALB attributes
        if not alb_obj.compare_elb_attributes():
            if alb_obj.check_mode:
                alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")
            alb_obj.update_elb_attributes()
            alb_obj.modify_elb_attributes()

        # Tags - only need to play with tags if tags parameter has been set to something
        if alb_obj.tags is not None:
            tags_need_modify, tags_to_delete = compare_aws_tags(
                boto3_tag_list_to_ansible_dict(alb_obj.elb["tags"]),
                boto3_tag_list_to_ansible_dict(alb_obj.tags),
                alb_obj.purge_tags,
            )

            # Exit on check_mode
            if alb_obj.check_mode and (tags_need_modify or tags_to_delete):
                alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")

            # Delete necessary tags
            if tags_to_delete:
                alb_obj.delete_tags(tags_to_delete)

            # Add/update tags
            if tags_need_modify:
                alb_obj.modify_tags()

    else:
        # Create load balancer
        if alb_obj.check_mode:
            alb_obj.exit_json(changed=True, msg="Would have created ALB if not in check mode.")
        alb_obj.create_elb()

        # Add ALB attributes
        alb_obj.update_elb_attributes()
        alb_obj.modify_elb_attributes()

    # Listeners
    listeners_obj = ELBListeners(alb_obj.connection, alb_obj.module, alb_obj.elb["LoadBalancerArn"])
    listeners_to_add, listeners_to_modify, listeners_to_delete = listeners_obj.compare_listeners()

    # Exit on check_mode
    if alb_obj.check_mode and (listeners_to_add or listeners_to_modify or listeners_to_delete):
        alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")

    # Delete listeners
    for listener_to_delete in listeners_to_delete:
        listener_obj = ELBListener(
            alb_obj.connection, alb_obj.module, listener_to_delete, alb_obj.elb["LoadBalancerArn"]
        )
        listener_obj.delete()
        listeners_obj.changed = True

    # Add listeners
    for listener_to_add in listeners_to_add:
        listener_obj = ELBListener(alb_obj.connection, alb_obj.module, listener_to_add, alb_obj.elb["LoadBalancerArn"])
        listener_obj.add()
        listeners_obj.changed = True

    # Modify listeners
    for listener_to_modify in listeners_to_modify:
        listener_obj = ELBListener(
            alb_obj.connection, alb_obj.module, listener_to_modify, alb_obj.elb["LoadBalancerArn"]
        )
        listener_obj.modify()
        listeners_obj.changed = True

    # If listeners changed, mark ALB as changed
    if listeners_obj.changed:
        alb_obj.changed = True

    # Rules of each listener
    for listener in listeners_obj.listeners:
        if "Rules" in listener:
            rules_obj = ELBListenerRules(
                connection=alb_obj.connection,
                module=alb_obj.module,
                listener_arn=listeners_obj.get_listener_arn_from_listener_port(listener["Port"]),
                listener_rules=listener["Rules"],
            )
            rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete = rules_obj.compare_rules()

            # Exit on check_mode
            if alb_obj.check_mode and (
                rules_to_add
                or rules_to_modify
                or rules_to_set_priority
                or (alb_obj.params["purge_rules"] and rules_to_delete)
            ):
                alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")

            # Create/Update/Delete Listener Rules
            rule_obj = ELBListenerRule(alb_obj.connection, alb_obj.module)
            alb_obj.changed |= rule_obj.process_rules(
                rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete
            )

    # Update ALB ip address type only if option has been provided
    if alb_obj.params.get("ip_address_type") and alb_obj.elb_ip_addr_type != alb_obj.params.get("ip_address_type"):
        # Exit on check_mode
        if alb_obj.check_mode:
            alb_obj.exit_json(changed=True, msg="Would have updated ALB if not in check mode.")

        alb_obj.modify_ip_address_type(alb_obj.params.get("ip_address_type"))

    # Exit on check_mode - no changes
    if alb_obj.check_mode:
        alb_obj.exit_json(changed=False, msg="IN CHECK MODE - no changes to make to ALB specified.")

    # Get the ALB again
    alb_obj.update()

    # Get the ALB listeners again
    listeners_obj.update()

    # Update the ALB attributes
    alb_obj.update_elb_attributes()

    # Convert to snake_case and merge in everything we want to return to the user
    snaked_alb = camel_dict_to_snake_dict(alb_obj.elb)
    snaked_alb.update(camel_dict_to_snake_dict(alb_obj.elb_attributes))
    snaked_alb["listeners"] = []
    for listener in listeners_obj.current_listeners:
        # For each listener, get listener rules
        listener["rules"] = get_elb_listener_rules(alb_obj.connection, alb_obj.module, listener["ListenerArn"])
        snaked_alb["listeners"].append(camel_dict_to_snake_dict(listener))

    # Change tags to ansible friendly dict
    snaked_alb["tags"] = boto3_tag_list_to_ansible_dict(snaked_alb["tags"])

    # ip address type
    snaked_alb["ip_address_type"] = alb_obj.get_elb_ip_address_type()

    alb_obj.exit_json(changed=alb_obj.changed, **snaked_alb)


def delete_alb(alb_obj: ApplicationLoadBalancer) -> None:
    if alb_obj.elb:
        # Exit on check_mode
        if alb_obj.check_mode:
            alb_obj.exit_json(changed=True, msg="Would have deleted ALB if not in check mode.")

        listeners_obj = ELBListeners(alb_obj.connection, alb_obj.module, alb_obj.elb["LoadBalancerArn"])
        for listener_to_delete in [i["ListenerArn"] for i in listeners_obj.current_listeners]:
            listener_obj = ELBListener(
                alb_obj.connection, alb_obj.module, listener_to_delete, alb_obj.elb["LoadBalancerArn"]
            )
            listener_obj.delete()

        alb_obj.delete()

    else:
        # Exit on check_mode - no changes
        if alb_obj.check_mode:
            alb_obj.exit_json(changed=False, msg="IN CHECK MODE - ALB already absent.")

    alb_obj.exit_json(changed=alb_obj.changed)


def main():
    argument_spec = dict(
        access_logs_enabled=dict(type="bool"),
        access_logs_s3_bucket=dict(type="str"),
        access_logs_s3_prefix=dict(type="str"),
        deletion_protection=dict(type="bool"),
        http2=dict(type="bool"),
        http_desync_mitigation_mode=dict(type="str", choices=["monitor", "defensive", "strictest"]),
        http_drop_invalid_header_fields=dict(type="bool"),
        http_x_amzn_tls_version_and_cipher_suite=dict(type="bool"),
        http_xff_client_port=dict(type="bool"),
        idle_timeout=dict(type="int"),
        listeners=dict(
            type="list",
            elements="dict",
            options=dict(
                Protocol=dict(type="str", required=True),
                Port=dict(type="int", required=True),
                SslPolicy=dict(type="str"),
                Certificates=dict(type="list", elements="dict"),
                DefaultActions=dict(type="list", required=True, elements="dict"),
                Rules=dict(type="list", elements="dict"),
            ),
        ),
        name=dict(required=True, type="str"),
        purge_listeners=dict(default=True, type="bool"),
        purge_tags=dict(default=True, type="bool"),
        subnets=dict(type="list", elements="str"),
        security_groups=dict(type="list", elements="str"),
        scheme=dict(default="internet-facing", choices=["internet-facing", "internal"]),
        state=dict(choices=["present", "absent"], default="present"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        waf_fail_open=dict(type="bool"),
        wait_timeout=dict(type="int"),
        wait=dict(default=False, type="bool"),
        purge_rules=dict(default=True, type="bool"),
        ip_address_type=dict(type="str", choices=["ipv4", "dualstack"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[("state", "present", ["subnets", "security_groups"])],
        required_together=[["access_logs_enabled", "access_logs_s3_bucket"]],
        supports_check_mode=True,
    )

    # Quick check of listeners parameters
    listeners = module.params.get("listeners")
    if listeners is not None:
        for listener in listeners:
            for key in listener.keys():
                if key == "Protocol" and listener[key] == "HTTPS":
                    if listener.get("SslPolicy") is None:
                        module.fail_json(msg="'SslPolicy' is a required listener dict key when Protocol = HTTPS")

                    if listener.get("Certificates") is None:
                        module.fail_json(msg="'Certificates' is a required listener dict key when Protocol = HTTPS")

    connection = module.client("elbv2")
    connection_ec2 = module.client("ec2")

    state = module.params.get("state")

    try:
        alb = ApplicationLoadBalancer(connection, connection_ec2, module)

        # Update security group if default is specified
        if alb.elb and module.params.get("security_groups") == []:
            module.params["security_groups"] = [find_default_sg(connection_ec2, module, alb.elb["VpcId"])]
            alb = ApplicationLoadBalancer(connection, connection_ec2, module)

        if state == "present":
            create_or_update_alb(alb)
        elif state == "absent":
            delete_alb(alb)
    except AnsibleELBv2Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

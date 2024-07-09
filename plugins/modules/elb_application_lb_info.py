#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: elb_application_lb_info
version_added: 5.0.0
short_description: Gather information about Application Load Balancers in AWS
description:
  - Gather information about Application Load Balancers in AWS.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - Rob White (@wimnat)
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
  include_attributes:
    description:
      - Whether or not to include load balancer attributes in the response.
    required: false
    type: bool
    default: true
    version_added: 7.0.0
  include_listeners:
    description:
      - Whether or not to include load balancer listeners in the response.
    required: false
    type: bool
    default: true
    version_added: 7.0.0
  include_listener_rules:
    description:
      - Whether or not to include load balancer listener rules in the response.
      - Implies O(include_listeners=true)
    required: false
    type: bool
    default: true
    version_added: 7.0.0

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all ALBs
  amazon.aws.elb_application_lb_info:

# Equivalent to aws elbv2 describe-load-balancers
- name: Gather minimal information about all ALBs
  amazon.aws.elb_application_lb_info:
    include_attributes: false
    include_listeners: false
    include_listener_rules: false

- name: Gather information about a particular ALB given its ARN
  amazon.aws.elb_application_lb_info:
    load_balancer_arns:
      - "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:loadbalancer/app/my-alb/aabbccddeeff"

- name: Gather information about ALBs named 'alb1' and 'alb2'
  amazon.aws.elb_application_lb_info:
    names:
      - alb1
      - alb2

- name: Gather information about specific ALB
  amazon.aws.elb_application_lb_info:
    names: "alb-name"
    region: "aws-region"
  register: alb_info
- ansible.builtin.debug:
    var: alb_info
"""

RETURN = r"""
load_balancers:
    description: A list of load balancers.
    returned: always
    type: complex
    contains:
        access_logs_s3_bucket:
            description: The name of the S3 bucket for the access logs.
            returned: when O(include_attributes=true)
            type: str
            sample: "mys3bucket"
        access_logs_s3_enabled:
            description: Indicates whether access logs stored in Amazon S3 are enabled.
            returned: when O(include_attributes=true)
            type: str
            sample: "true"
        access_logs_s3_prefix:
            description: The prefix for the location in the S3 bucket.
            returned: when O(include_attributes=true)
            type: str
            sample: "my/logs"
        availability_zones:
            description: The Availability Zones for the load balancer.
            type: list
            elements: dict
            sample: [{ "load_balancer_addresses": [], "subnet_id": "subnet-aabbccddff", "zone_name": "ap-southeast-2a" }]
            contains:
                load_balancer_addresses:
                    description: Information about static IP addresses for a load balancer.
                    type: list
                    elements: dict
                    contains:
                        ip_address:
                            description: The static IP address.
                            type: str
                        allocation_id:
                            description: The allocation ID of the Elastic IP address for an internal-facing load balancer.
                            type: str
                        private_ipv4_address:
                            description: The private IPv4 address for an internal load balancer.
                            type: str
                        ipv6_address:
                            description: The IPv6 address.
                            type: str
                subnet_id:
                    description: The ID of the subnet.
                    type: str
                zone_name:
                    description: The name of the Availability Zone.
                    type: str
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
            returned: when O(include_attributes=true)
            type: bool
            sample: true
        dns_name:
            description: The public DNS name of the load balancer.
            type: str
            sample: "internal-my-alb-123456789.ap-southeast-2.elb.amazonaws.com"
        idle_timeout_timeout_seconds:
            description: The idle timeout value, in seconds.
            returned: when O(include_attributes=true)
            type: int
            sample: 60
        ip_address_type:
            description: The type of IP addresses used by the subnets for the load balancer.
            type: str
            sample: "ipv4"
        listeners:
            description: Information about the listeners.
            returned: when O(include_listeners=true) or O(include_listener_rules=true)
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
                rules:
                    description: List of listener rules.
                    returned: when O(include_listener_rules=true)
                    type: list
                    elements: dict
                    contains:
                        rule_arn:
                            description: The Amazon Resource Name (ARN) of the rule.
                            type: str
                            sample: ""
                        priority:
                            description: The priority.
                            type: str
                            sample: "default"
                        is_default:
                            description: Indicates whether this is the default rule.
                            type: bool
                            sample: false
                        conditions:
                            description: The conditions.
                            type: list
                            sample: []
                        actions:
                            description: The actions.
                            type: list
                            elements: dict
                            contains:
                                type:
                                    description: The type of action.
                                    type: str
                                target_group_arn:
                                    description: The Amazon Resource Name (ARN) of the target group.
                                    type: str
                                forward_config:
                                    description: Information for creating an action that distributes requests among one or more target groups.
                                    type: dict
                                    contains:
                                        target_groups:
                                            description: The target groups.
                                            type: dict
                                            contains:
                                                target_group_arn:
                                                    description: The Amazon Resource Name (ARN) of the target group.
                                                    type: str
                                                weight:
                                                    description: The weight.
                                                    type: int
                                        target_group_stickiness_config:
                                            description: The target group stickiness for the rule.
                                            type: dict
                                            contains:
                                                enabled:
                                                    description: Indicates whether target group stickiness is enabled.
                                                    type: bool
                            sample: [
                                {
                                    "forward_config": {
                                        "target_group_stickiness_config": {
                                            "enabled": false
                                        },
                                        "target_groups": [
                                            {
                                                "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test/09ba111f8079fb83",
                                                "weight": 1
                                            }
                                        ]
                                    },
                                    "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test/09ba111f8079fb83",
                                    "type": "forward"
                                }
                            ]
                certificates:
                    description: The SSL server certificate.
                    type: list
                    elements: dict
                    contains:
                        certificate_arn:
                            description: The Amazon Resource Name (ARN) of the certificate.
                            type: str
                            sample: "arn:aws:acm:us-east-1:123456789012:certificate/28d2f3d9-cb2f-4033-a9aa-e75e704125a2"
                ssl_policy:
                    description: The security policy that defines which ciphers and protocols are supported.
                    type: str
                    sample: "ELBSecurityPolicy-2016-08"
                default_actions:
                    description: The default actions for the listener.
                    type: str
                    contains:
                        type:
                            description: The type of action.
                            type: str
                        target_group_arn:
                            description: The Amazon Resource Name (ARN) of the target group.
                            type: str
                        forward_config:
                            description: Information for creating an action that distributes requests among one or more target groups.
                            type: dict
                            contains:
                                target_groups:
                                    description: The target groups.
                                    type: dict
                                    contains:
                                        target_groups:
                                            description: The Amazon Resource Name (ARN) of the target group.
                                            type: str
                                        weight:
                                            description: The weight.
                                            type: int
                                target_group_stickiness_config:
                                    description: The target group stickiness for the rule.
                                    type: dict
                                    contains:
                                        enabled:
                                            description: Indicates whether target group stickiness is enabled.
                                            type: bool
                    sample: [
                        {
                            "forward_config": {
                                "target_group_stickiness_config": {
                                    "enabled": false
                                },
                                "target_groups": [
                                    {
                                        "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test/bf43c68602c51c02",
                                        "weight": 1
                                    }
                                ]
                            },
                            "target_group_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/alb-test/bf43c68602c51c02",
                            "type": "forward"
                        }
                    ]
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            type: str
            sample: "arn:aws:elasticloadbalancing:ap-southeast-2:123456789012:loadbalancer/app/my-alb/001122334455"
        load_balancer_name:
            description: The name of the load balancer.
            type: str
            sample: "my-alb"
        load_balancing_cross_zone_enabled:
            description: Indicates whether or not cross-zone load balancing is enabled.
            returned: when O(include_attributes=true)
            type: str
            sample: "true"
        routing_http2_enabled:
            description: Indicates whether HTTP/2 is enabled.
            returned: when O(include_attributes=true)
            type: str
            sample: "true"
        routing_http_desync_mitigation_mode:
            description: Determines how the load balancer handles requests that might pose a security risk to an application.
            returned: when O(include_attributes=true)
            type: str
            sample: "defensive"
        routing_http_drop_invalid_header_fields_enabled:
            description: Indicates whether HTTP headers with invalid header fields are removed by the load balancer (true) or routed to targets (false).
            returned: when O(include_attributes=true)
            type: str
            sample: "false"
        routing_http_x_amzn_tls_version_and_cipher_suite_enabled:
            description: Indicates whether the two headers are added to the client request before sending it to the target.
            returned: when O(include_attributes=true)
            type: str
            sample: "false"
        routing_http_xff_client_port_enabled:
            description: Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer.
            returned: when O(include_attributes=true)
            type: str
            sample: "false"
        scheme:
            description: Internet-facing or internal load balancer.
            type: str
            sample: "internal"
        security_groups:
            description: The IDs of the security groups for the load balancer.
            type: list
            sample: ["sg-0011223344"]
        state:
            description: The state of the load balancer.
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
            type: dict
            sample: {
                "Tag": "Example"
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
            returned: when O(include_attributes=true)
            type: str
            sample: "false"
"""

from typing import Dict

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import AnsibleELBv2Error
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_listeners
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_load_balancer_attributes
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_load_balancers
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_rules
from ansible_collections.amazon.aws.plugins.module_utils.elb_utils import describe_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def get_load_balancer_attributes(connection, module: AnsibleAWSModule, load_balancer_arn: str) -> Dict[str, str]:
    try:
        attributes = describe_load_balancer_attributes(connection, load_balancer_arn)
    except AnsibleELBv2Error as e:
        module.fail_json_aws(e, msg="Failed to describe load balancer attributes")
    load_balancer_attributes = boto3_tag_list_to_ansible_dict(attributes)

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    for k, v in list(load_balancer_attributes.items()):
        load_balancer_attributes[k.replace(".", "_")] = v
        del load_balancer_attributes[k]

    return load_balancer_attributes


def get_load_balancer_tags(connection, load_balancer_arn: str) -> Dict[str, str]:
    tag_descriptions = describe_tags(connection, [load_balancer_arn])
    return boto3_tag_list_to_ansible_dict(tag_descriptions[0]["Tags"])


def list_load_balancers(connection, module: AnsibleAWSModule) -> None:
    load_balancer_arns = module.params.get("load_balancer_arns")
    names = module.params.get("names")
    include_attributes = module.params.get("include_attributes")
    include_listeners = module.params.get("include_listeners")
    include_listener_rules = module.params.get("include_listener_rules")

    try:
        load_balancers = describe_load_balancers(connection, load_balancer_arns=load_balancer_arns, names=names)
        for load_balancer in load_balancers:
            # Get the attributes for each alb
            if include_attributes:
                load_balancer.update(get_load_balancer_attributes(connection, module, load_balancer["LoadBalancerArn"]))

            # Get the listeners for each alb
            if include_listeners or include_listener_rules:
                load_balancer["listeners"] = describe_listeners(
                    connection, load_balancer_arn=load_balancer["LoadBalancerArn"]
                )

            # For each listener, get listener rules
            if include_listener_rules:
                for listener in load_balancer["listeners"]:
                    listener["rules"] = describe_rules(connection, ListenerArn=listener["ListenerArn"])

        # Turn the boto3 result in to ansible_friendly_snaked_names
        snaked_load_balancers = [camel_dict_to_snake_dict(load_balancer) for load_balancer in load_balancers]

        # Get tags for each load balancer
        for snaked_load_balancer in snaked_load_balancers:
            snaked_load_balancer["tags"] = get_load_balancer_tags(connection, snaked_load_balancer["load_balancer_arn"])
    except AnsibleELBv2Error as e:
        module.fail_json_aws_error(e)

    module.exit_json(load_balancers=snaked_load_balancers)


def main():
    argument_spec = dict(
        load_balancer_arns=dict(type="list", elements="str"),
        names=dict(type="list", elements="str"),
        include_attributes=dict(default=True, type="bool"),
        include_listeners=dict(default=True, type="bool"),
        include_listener_rules=dict(default=True, type="bool"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["load_balancer_arns", "names"]],
        supports_check_mode=True,
    )

    try:
        connection = module.client("elbv2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e)

    list_load_balancers(connection, module)


if __name__ == "__main__":
    main()

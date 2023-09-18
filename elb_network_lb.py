#!/usr/bin/python

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_network_lb
version_added: 1.0.0
short_description: Manage a Network Load Balancer
description:
    - Manage an AWS Network Elastic Load Balancer. See
      U(https://aws.amazon.com/blogs/aws/new-network-load-balancer-effortless-scaling-to-millions-of-requests-per-second/) for details.
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  cross_zone_load_balancing:
    description:
      - Indicates whether cross-zone load balancing is enabled.
      - Defaults to C(false).
    type: bool
  deletion_protection:
    description:
      - Indicates whether deletion protection for the ELB is enabled.
      - Defaults to C(false).
    type: bool
  listeners:
    description:
      - A list of dicts containing listeners to attach to the ELB. See examples for detail of the dict required. Note that listener keys
        are CamelCased.
    type: list
    elements: dict
    suboptions:
        Port:
            description: The port on which the load balancer is listening.
            type: int
            required: true
        Protocol:
            description: The protocol for connections from clients to the load balancer.
            type: str
            required: true
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
  name:
    description:
      - The name of the load balancer. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric
        characters or hyphens, and must not begin or end with a hyphen.
    required: true
    type: str
  purge_listeners:
    description:
      - If I(purge_listeners=true), existing listeners will be purged from the ELB to match exactly what is defined by I(listeners) parameter.
      - If the I(listeners) parameter is not set then listeners will not be modified.
    default: true
    type: bool
  purge_tags:
    description:
      - If I(purge_tags=true), existing tags will be purged from the resource to match exactly what is defined by I(tags) parameter.
      - If the I(tags) parameter is not set then tags will not be modified.
    default: true
    type: bool
  subnet_mappings:
    description:
      - A list of dicts containing the IDs of the subnets to attach to the load balancer. You can also specify the allocation ID of an Elastic IP
        to attach to the load balancer. You can specify one Elastic IP address per subnet.
      - This parameter is mutually exclusive with I(subnets).
    type: list
    elements: dict
  subnets:
    description:
      - A list of the IDs of the subnets to attach to the load balancer. You can specify only one subnet per Availability Zone. You must specify subnets from
        at least two Availability Zones.
      - Required when I(state=present).
      - This parameter is mutually exclusive with I(subnet_mappings).
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
      - The current default is C(absent).  However, this behavior is inconsistent with other modules
        and as such the default will change to C(present) in 2.14.
        To maintain the existing behavior explicitly set I(state=absent).
    choices: [ 'present', 'absent' ]
    type: str
  tags:
    description:
      - A dictionary of one or more tags to assign to the load balancer.
    type: dict
  wait:
    description:
      - Whether or not to wait for the network load balancer to reach the desired state.
    type: bool
  wait_timeout:
    description:
      - The duration in seconds to wait, used in conjunction with I(wait).
    type: int
  ip_address_type:
    description:
      - Sets the type of IP addresses used by the subnets of the specified Application Load Balancer.
    choices: [ 'ipv4', 'dualstack' ]
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

notes:
  - Listeners are matched based on port. If a listener's port is changed then a new listener will be created.
  - Listener rules are matched based on priority. If a rule's priority is changed then a new rule will be created.
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create an ELB and attach a listener
  community.aws.elb_network_lb:
    name: myelb
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - Protocol: TCP # Required. The protocol for connections from clients to the load balancer (TCP, TLS, UDP or TCP_UDP) (case-sensitive).
        Port: 80 # Required. The port on which the load balancer is listening.
        DefaultActions:
          - Type: forward # Required. Only 'forward' is accepted at this time
            TargetGroupName: mytargetgroup # Required. The name of the target group
    state: present

- name: Create an ELB with an attached Elastic IP address
  community.aws.elb_network_lb:
    name: myelb
    subnet_mappings:
      - SubnetId: subnet-012345678
        AllocationId: eipalloc-aabbccdd
    listeners:
      - Protocol: TCP # Required. The protocol for connections from clients to the load balancer (TCP, TLS, UDP or TCP_UDP) (case-sensitive).
        Port: 80 # Required. The port on which the load balancer is listening.
        DefaultActions:
          - Type: forward # Required. Only 'forward' is accepted at this time
            TargetGroupName: mytargetgroup # Required. The name of the target group
    state: present

- name: Remove an ELB
  community.aws.elb_network_lb:
    name: myelb
    state: absent

'''

RETURN = r'''
availability_zones:
    description: The Availability Zones for the load balancer.
    returned: when state is present
    type: list
    sample: "[{'subnet_id': 'subnet-aabbccddff', 'zone_name': 'ap-southeast-2a', 'load_balancer_addresses': []}]"
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
    type: str
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
load_balancing_cross_zone_enabled:
    description: Indicates whether cross-zone load balancing is enabled.
    returned: when state is present
    type: str
    sample: true
scheme:
    description: Internet-facing or internal load balancer.
    returned: when state is present
    type: str
    sample: internal
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
    sample: network
vpc_id:
    description: The ID of the VPC for the load balancer.
    returned: when state is present
    type: str
    sample: vpc-0011223344
'''

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict, compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.elbv2 import NetworkLoadBalancer, ELBListeners, ELBListener


def create_or_update_elb(elb_obj):
    """Create ELB or modify main attributes. json_exit here"""
    if elb_obj.elb:
        # ELB exists so check subnets, security groups and tags match what has been passed

        # Subnets
        if not elb_obj.compare_subnets():
            elb_obj.modify_subnets()

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

    # Get the ELB again
    elb_obj.update()

    # Get the ELB listeners again
    listeners_obj.update()

    # Update the ELB attributes
    elb_obj.update_elb_attributes()

    # Update ELB ip address type only if option has been provided
    if elb_obj.module.params.get('ip_address_type') is not None:
        elb_obj.modify_ip_address_type(elb_obj.module.params.get('ip_address_type'))

    # Convert to snake_case and merge in everything we want to return to the user
    snaked_elb = camel_dict_to_snake_dict(elb_obj.elb)
    snaked_elb.update(camel_dict_to_snake_dict(elb_obj.elb_attributes))
    snaked_elb['listeners'] = []
    for listener in listeners_obj.current_listeners:
        snaked_elb['listeners'].append(camel_dict_to_snake_dict(listener))

    # Change tags to ansible friendly dict
    snaked_elb['tags'] = boto3_tag_list_to_ansible_dict(snaked_elb['tags'])

    # ip address type
    snaked_elb['ip_address_type'] = elb_obj.get_elb_ip_address_type()

    elb_obj.module.exit_json(changed=elb_obj.changed, **snaked_elb)


def delete_elb(elb_obj):

    if elb_obj.elb:
        elb_obj.delete()

    elb_obj.module.exit_json(changed=elb_obj.changed)


def main():

    argument_spec = (
        dict(
            cross_zone_load_balancing=dict(type='bool'),
            deletion_protection=dict(type='bool'),
            listeners=dict(type='list',
                           elements='dict',
                           options=dict(
                               Protocol=dict(type='str', required=True),
                               Port=dict(type='int', required=True),
                               SslPolicy=dict(type='str'),
                               Certificates=dict(type='list', elements='dict'),
                               DefaultActions=dict(type='list', required=True, elements='dict')
                           )
                           ),
            name=dict(required=True, type='str'),
            purge_listeners=dict(default=True, type='bool'),
            purge_tags=dict(default=True, type='bool'),
            subnets=dict(type='list', elements='str'),
            subnet_mappings=dict(type='list', elements='dict'),
            scheme=dict(default='internet-facing', choices=['internet-facing', 'internal']),
            state=dict(choices=['present', 'absent'], type='str'),
            tags=dict(type='dict'),
            wait_timeout=dict(type='int'),
            wait=dict(type='bool'),
            ip_address_type=dict(type='str', choices=['ipv4', 'dualstack'])
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[['subnets', 'subnet_mappings']])

    # Check for subnets or subnet_mappings if state is present
    state = module.params.get("state")
    if state == 'present':
        if module.params.get("subnets") is None and module.params.get("subnet_mappings") is None:
            module.fail_json(msg="'subnets' or 'subnet_mappings' is required when state=present")

    if state is None:
        # See below, unless state==present we delete.  Ouch.
        module.deprecate('State currently defaults to absent.  This is inconsistent with other modules'
                         ' and the default will be changed to `present` in Ansible 2.14',
                         date='2022-06-01', collection_name='community.aws')

    # Quick check of listeners parameters
    listeners = module.params.get("listeners")
    if listeners is not None:
        for listener in listeners:
            for key in listener.keys():
                protocols_list = ['TCP', 'TLS', 'UDP', 'TCP_UDP']
                if key == 'Protocol' and listener[key] not in protocols_list:
                    module.fail_json(msg="'Protocol' must be either " + ", ".join(protocols_list))

    connection = module.client('elbv2')
    connection_ec2 = module.client('ec2')

    elb = NetworkLoadBalancer(connection, connection_ec2, module)

    if state == 'present':
        create_or_update_elb(elb)
    else:
        delete_elb(elb)


if __name__ == '__main__':
    main()

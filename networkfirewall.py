#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: networkfirewall
short_description: manage AWS Network Firewall firewalls
version_added: 4.0.0
description:
  - A module for creating, updating and deleting AWS Network Firewall firewalls.
options:
  arn:
    description:
      - The ARN of the firewall.
      - Exactly one of I(arn) or I(name) must be provided.
    required: false
    type: str
    aliases: ['firewall_arn']
  name:
    description:
      - The name of the firewall.
      - Cannot be updated after creation.
      - Exactly one of I(arn) or I(name) must be provided.
    required: false
    type: str
    aliases: ['firewall_name']
  state:
    description:
      - Create or remove the firewall.
    required: false
    choices: ['present', 'absent']
    default: 'present'
    type: str
  description:
    description:
      - A description for the firewall.
    required: false
    type: str
  delete_protection:
    description:
      - When I(delete_protection=True), the firewall is protected from deletion.
      - Defaults to C(false) when not provided on creation.
    type: bool
    required: false
  policy_change_protection:
    description:
      - When I(policy_change_protection=True), the firewall is protected from
        changes to which policy is attached to the firewall.
      - Defaults to C(false) when not provided on creation.
    type: bool
    required: false
    aliases: ['firewall_policy_change_protection']
  subnet_change_protection:
    description:
      - When I(subnet_change_protection=True), the firewall is protected from
        changes to which subnets is attached to the firewall.
      - Defaults to C(false) when not provided on creation.
    type: bool
    required: false
  wait:
    description:
      - On creation, whether to wait for the firewall to reach the C(READY)
        state.
      - On deletion, whether to wait for the firewall to reach the C(DELETED)
        state.
      - On update, whether to wait for the firewall to reach the C(IN_SYNC)
        configuration synchronization state.
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - Maximum time, in seconds, to wait for the firewall to reach the
        expected state.
      - Defaults to 600 seconds.
    type: int
    required: false
  subnets:
    description:
      - The ID of the subnets to which the firewall will be associated.
      - Required when creating a new firewall.
    type: list
    elements: str
    required: false
  purge_subnets:
    description:
      - If I(purge_subnets=true), existing subnets will be removed from the
        firewall as necessary to match exactly what is defined by I(subnets).
    type: bool
    required: false
    default: true
  policy:
    description:
      - The ARN of the Network Firewall policy to use for the firewall.
      - Required when creating a new firewall.
    type: str
    required: false
    aliases: ['firewall_policy_arn']

author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
'''

EXAMPLES = '''
# Create an AWS Network Firewall
- community.aws.networkfirewall:
    name: 'ExampleFirewall'
    state: present
    policy: 'ExamplePolicy'
    subnets:
    - 'subnet-123456789abcdef01'

# Create an AWS Network Firewall with various options, don't wait for creation
# to finish.
- community.aws.networkfirewall:
    name: 'ExampleFirewall'
    state: present
    delete_protection: True
    description: "An example Description"
    policy: 'ExamplePolicy'
    policy_change_protection: True
    subnets:
    - 'subnet-123456789abcdef01'
    - 'subnet-abcdef0123456789a'
    subnet_change_protection: True
    tags:
      ExampleTag: Example Value
      another_tag: another_example
    wait: false


# Delete an AWS Network Firewall
- community.aws.networkfirewall:
    state: absent
    name: 'ExampleFirewall'
'''

RETURN = '''
firewall:
  description: The full details of the firewall
  returned: success
  type: dict
  contains:
    firewall:
      description: The details of the firewall
      type: dict
      returned: success
      contains:
        delete_protection:
          description: A flag indicating whether it is possible to delete the firewall.
          type: str
          returned: success
          example: true
        description:
          description: A description of the firewall.
          type: str
          returned: success
          example: "Description"
        firewall_arn:
          description: The ARN of the firewall.
          type: str
          returned: success
          example: "arn:aws:network-firewall:us-east-1:123456789012:firewall/ExampleFirewall"
        firewall_id:
          description: A unique ID for the firewall.
          type: str
          returned: success
          example: "12345678-abcd-1234-abcd-123456789abc"
        firewall_name:
          description: The name of the firewall.
          type: str
          returned: success
          example: "ExampleFirewall"
        firewall_policy_arn:
          description:  The ARN of the firewall policy used by the firewall.
          type: str
          returned: success
          example: "arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/ExamplePolicy"
        firewall_policy_change_protection:
          description:
            - A flag indicating whether it is possible to change which firewall
              policy is used by the firewall.
          type: bool
          returned: success
          example: false
        subnet_change_protection:
          description:
            - A flag indicating whether it is possible to change which subnets
              the firewall endpoints are in.
          type: bool
          returned: success
          example: true
        subnets:
          description: A list of the subnets the firewall endpoints are in.
          type: list
          elements: str
          example: ["subnet-12345678", "subnet-87654321"]
        subnet_mappings:
          description: A list representing the subnets the firewall endpoints are in.
          type: list
          elements: dict
          contains:
            subnet_id:
              description: The ID of the subnet.
              type: str
              returned: success
              example: "subnet-12345678"
        tags:
          description: The tags associated with the firewall.
          type: dict
          returned: success
          example: '{"SomeTag": "SomeValue"}'
        vpc_id:
          description: The ID of the VPC that the firewall is used by.
          type: str
          returned: success
          example: "vpc-0123456789abcdef0"
    firewall_metadata:
      description: Metadata about the firewall
      type: dict
      returned: success
      contains:
        configuration_sync_state_summary:
          description:
            - A short summary of the synchronization status of the
              policy and rule groups.
          type: str
          returned: success
          example: "IN_SYNC"
        status:
          description:
            - A short summary of the status of the firewall endpoints.
          type: str
          returned: success
          example: "READY"
        sync_states:
          description:
            - A description, broken down by availability zone, of the status
              of the firewall endpoints as well as the synchronization status
              of the policies and rule groups.
          type: dict
          returned: success
          example:
            {
              "us-east-1a": {
                "attachment": {
                  "endpoint_id": "vpce-123456789abcdef01",
                  "status": "READY",
                  "subnet_id": "subnet-12345678"
                },
                "config": {
                  "arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/Ansible-Example": {
                    "sync_status": "IN_SYNC",
                    "update_token": "abcdef01-0000-0000-0000-123456789abc"
                  },
                  "arn:aws:network-firewall:us-east-1:123456789012:stateful-rulegroup/ExampleDomainList": {
                    "sync_status": "IN_SYNC",
                    "update_token": "12345678-0000-0000-0000-abcdef012345"
                  }
                }
              }
            }
'''


from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.community.aws.plugins.module_utils.networkfirewall import NetworkFirewallManager


def main():

    argument_spec = dict(
        name=dict(type='str', required=False, aliases=['firewall_name']),
        arn=dict(type='str', required=False, aliases=['firewall_arn']),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        description=dict(type='str', required=False),
        tags=dict(type='dict', required=False, aliases=['resource_tags']),
        purge_tags=dict(type='bool', required=False, default=True),
        wait=dict(type='bool', required=False, default=True),
        wait_timeout=dict(type='int', required=False),
        subnet_change_protection=dict(type='bool', required=False),
        policy_change_protection=dict(type='bool', required=False, aliases=['firewall_policy_change_protection']),
        delete_protection=dict(type='bool', required=False),
        subnets=dict(type='list', elements='str', required=False),
        purge_subnets=dict(type='bool', required=False, default=True),
        policy=dict(type='str', required=False, aliases=['firewall_policy_arn']),
    )

    mutually_exclusive = [
        ('arn', 'name',)
    ]
    required_one_of = [
        ('arn', 'name',)
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
        required_one_of=required_one_of,
    )

    arn = module.params.get('arn')
    name = module.params.get('name')
    state = module.params.get('state')

    manager = NetworkFirewallManager(module, name=name, arn=arn)
    manager.set_wait(module.params.get('wait', None))
    manager.set_wait_timeout(module.params.get('wait_timeout', None))

    if state == 'absent':
        manager.set_delete_protection(module.params.get('delete_protection', None))
        manager.delete()
    else:
        if not manager.original_resource:
            if not module.params.get('subnets', None):
                module.fail_json('The subnets parameter must be provided on creation.')
            if not module.params.get('policy', None):
                module.fail_json('The policy parameter must be provided on creation.')
        manager.set_description(module.params.get('description', None))
        manager.set_tags(module.params.get('tags', None), module.params.get('purge_tags', None))
        manager.set_subnet_change_protection(module.params.get('subnet_change_protection', None))
        manager.set_policy_change_protection(module.params.get('policy_change_protection', None))
        manager.set_delete_protection(module.params.get('delete_protection', None))
        manager.set_subnets(module.params.get('subnets', None), module.params.get('purge_subnets', None))
        manager.set_policy(module.params.get('policy', None))
        manager.flush_changes()

    results = dict(
        changed=manager.changed,
        firewall=manager.updated_resource,
    )
    if manager.changed:
        diff = dict(
            before=manager.original_resource,
            after=manager.updated_resource,
        )
        results['diff'] = diff
    module.exit_json(**results)


if __name__ == '__main__':
    main()

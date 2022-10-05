#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: networkfirewall_policy
short_description: manage AWS Network Firewall policies
version_added: 4.0.0
description:
  - A module for creating, updating and deleting AWS Network Firewall policies.
options:
  arn:
    description:
      - The ARN of the Network Firewall policy.
      - Exactly one of I(arn) or I(name) must be provided.
    required: false
    type: str
  name:
    description:
      - The name of the Network Firewall policy.
      - Cannot be updated after creation.
      - Exactly one of I(arn) or I(name) must be provided.
    required: false
    type: str
  state:
    description:
      - Create or remove the Network Firewall policy.
    required: false
    choices: ['present', 'absent']
    default: 'present'
    type: str
  description:
    description:
      - A description for the Network Firewall policy.
    required: false
    type: str
  stateful_rule_groups:
    description:
      - A list of names or ARNs of stateful firewall rule groups.
    required: false
    type: list
    elements: str
    aliases: ['stateful_groups']
  stateless_rule_groups:
    description:
      - A list of names or ARNs of stateless firewall rule groups.
    required: false
    type: list
    elements: str
    aliases: ['stateless_groups']
  stateless_default_actions:
    description:
      - Actions to take on a packet if it doesn't match any of the stateless
        rules in the policy.
      - Common actions are C(aws:pass), C(aws:drop) and C(aws:forward_to_sfe).
      - When creating a new policy defaults to C(aws:forward_to_sfe).
    required: false
    type: list
    elements: str
  stateless_fragment_default_actions:
    description:
      - Actions to take on a fragmented UDP packet if it doesn't match any
        of the stateless rules in the policy.
      - Common actions are C(aws:pass), C(aws:drop) and C(aws:forward_to_sfe).
      - When creating a new policy defaults to C(aws:forward_to_sfe).
    required: false
    type: list
    elements: str
  stateful_default_actions:
    description:
      - Actions to take on a packet if it doesn't match any of the stateful
        rules in the policy.
      - Common actions are C(aws:drop_strict), C(aws:drop_established),
        C(aws:alert_strict) and C(aws:alert_established).
      - Only valid for policies where I(strict_rule_order=true).
      - When creating a new policy defaults to C(aws:drop_strict).
      - I(stateful_default_actions) requires botocore>=1.21.52.
    required: false
    type: list
    elements: str
  stateful_rule_order:
    description:
      - Indicates how to manage the order of stateful rule evaluation for the policy.
      - When I(strict_rule_order='strict') rules and rule groups are evaluated in
        the order that they're defined.
      - Cannot be updated after creation.
      - I(stateful_rule_order) requires botocore>=1.21.52.
    required: false
    type: str
    choices: ['default', 'strict']
    aliases: ['rule_order']
  stateless_custom_actions:
    description:
      - A list of dictionaries defining custom actions which can be used in
        I(stateless_default_actions) and I(stateless_fragment_default_actions).
    required: false
    type: list
    elements: dict
    aliases: ['custom_stateless_actions']
    suboptions:
      name:
        description:
          - The name of the custom action.
        required: true
        type: str
      publish_metric_dimension_value:
        description:
          - When the custom action is used, metrics will have a dimension of
            C(CustomAction) the value of which is set to
            I(publish_metric_dimension_value).
        required: false
        type: str
        aliases: ['publish_metric_dimension_values']
  purge_stateless_custom_actions:
    description:
      - If I(purge_stateless_custom_actions=true), existing custom actions will
        be purged from the resource to match exactly what is defined by
        the I(stateless_custom_actions) parameter.
    type: bool
    required: false
    default: True
    aliases: ['purge_custom_stateless_actions']
  wait:
    description:
      - Whether to wait for the firewall policy to reach the
        C(ACTIVE) or C(DELETED) state before the module returns.
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - Maximum time, in seconds, to wait for the firewall policy
        to reach the expected state.
      - Defaults to 600 seconds.
    type: int
    required: false


author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
  - amazon.aws.tags
'''

EXAMPLES = '''
# Create an AWS Network Firewall Policy with default rule order
- community.aws.networkfirewall_policy:
    stateful_rule_order: 'default'
    state: present
    name: 'ExamplePolicy'

# Create an AWS Network Firewall Policy with strict rule order
- community.aws.networkfirewall_policy:
    stateful_rule_order: 'strict'
    state: present
    name: 'ExampleStrictPolicy'


# Create an AWS Network Firewall Policy that defaults to dropping all packets
- community.aws.networkfirewall_policy:
    stateful_rule_order: 'strict'
    state: present
    name: 'ExampleDropPolicy'
    stateful_default_actions:
      - 'aws:drop_strict'
    stateful_rule_groups:
      - 'ExampleStrictRuleGroup'
      - 'arn:aws:network-firewall:us-east-1:aws-managed:stateful-rulegroup/BotNetCommandAndControlDomainsStrictOrder'

# Delete an AWS Network Firewall Policy
- community.aws.networkfirewall_policy:
    state: absent
    name: 'ExampleDropPolicy'
'''

RETURN = '''
policy:
  description: The details of the policy
  type: dict
  returned: success
  contains:
    policy:
      description: The details of the policy
      type: dict
      returned: success
      contains:
        stateful_engine_options:
          description:
            - Extra options describing how the stateful rules should be handled.
          type: dict
          returned: success
          contains:
            rule_order:
              description:
                - How rule group evaluation will be ordered.
                - For more information on rule evaluation ordering see the AWS documentation
                  U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/suricata-rule-evaluation-order.html).
              type: str
              returned: success
              example: 'DEFAULT_ACTION_ORDER'
        stateful_rule_group_references:
          description: Information about the stateful rule groups attached to the policy.
          type: list
          elements: dict
          returned: success
          contains:
            resource_arn:
              description: The ARN of the rule group.
              type: str
              returned: success
              example: 'arn:aws:network-firewall:us-east-1:aws-managed:stateful-rulegroup/AbusedLegitMalwareDomainsActionOrder'
            priority:
              description:
                - An integer that indicates the order in which to run the stateful rule groups in a single policy.
                - This only applies to policies that specify the STRICT_ORDER rule order in the stateful engine options settings.
              type: int
              returned: success
              example: 1234
        stateless_custom_actions:
          description:
            - A description of additional custom actions available for use as
              default rules to apply to stateless packets.
          type: list
          elements: dict
          returned: success
          contains:
            action_name:
              description: A name for the action.
              type: str
              returned: success
              example: 'ExampleAction'
            action_definition:
              description: The action to perform.
              type: dict
              returned: success
              contains:
                publish_metric_action:
                  description:
                    - Definition of a custom metric to be published to CloudWatch.
                    - U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/monitoring-cloudwatch.html)
                  type: dict
                  returned: success
                  contains:
                    dimensions:
                      description:
                        - The values of the CustomAction dimension to set on the metrics.
                        - The dimensions of a metric are used to identify unique
                          streams of data.
                      type: list
                      elements: dict
                      returned: success
                      contains:
                        value:
                          description: A value of the CustomAction dimension to set on the metrics.
                          type: str
                          returned: success
                          example: 'ExampleRule'
        stateless_default_actions:
          description: The default actions to take on a packet that doesn't match any stateful rules.
          type: list
          elements: str
          returned: success
          example: ['aws:alert_strict']
        stateless_fragment_default_actions:
          description: The actions to take on a packet if it doesn't match any of the stateless rules in the policy.
          type: list
          elements: str
          returned: success
          example: ['aws:pass']
        stateless_rule_group_references:
          description: Information about the stateful rule groups attached to the policy.
          type: list
          elements: dict
          returned: success
          contains:
            resource_arn:
              description: The ARN of the rule group.
              type: str
              returned: success
              example: 'arn:aws:network-firewall:us-east-1:123456789012:stateless-rulegroup/ExampleGroup'
            priority:
              description:
                - An integer that indicates the order in which to run the stateless rule groups in a single policy.
              type: str
              returned: success
              example: 12345
    policy_metadata:
      description: Metadata about the policy
      type: dict
      returned: success
      contains:
        consumed_stateful_rule_capacity:
          description: The total number of capacity units used by the stateful rule groups.
          type: int
          returned: success
          example: 165
        consumed_stateless_rule_capacity:
          description: The total number of capacity units used by the stateless rule groups.
          type: int
          returned: success
          example: 2010
        firewall_policy_arn:
          description: The ARN of the policy.
          type: str
          returned: success
          example: arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/ExamplePolicy
        firewall_policy_id:
          description: The unique ID of the policy.
          type: str
          returned: success
          example: 12345678-abcd-1234-5678-123456789abc
        firewall_policy_name:
          description: The name of the policy.
          type: str
          returned: success
          example: ExamplePolicy
        firewall_policy_status:
          description: The current status of the policy.
          type: str
          returned: success
          example: ACTIVE
        number_of_associations:
          description: The number of firewalls the policy is associated to.
          type: int
          returned: success
          example: 1
        tags:
          description: A dictionary representing the tags associated with the policy.
          type: dict
          returned: success
          example: {'tagName': 'Some Value'}
'''


from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.community.aws.plugins.module_utils.networkfirewall import NetworkFirewallPolicyManager


def main():

    custom_action_options = dict(
        name=dict(type='str', required=True),
        # Poorly documented, but "publishMetricAction.dimensions ... must have length less than or equal to 1"
        publish_metric_dimension_value=dict(type='str', required=False, aliases=['publish_metric_dimension_values']),
        # NetworkFirewallPolicyManager can cope with a list for future-proofing
        # publish_metric_dimension_values=dict(type='list', elements='str', required=False, aliases=['publish_metric_dimension_value']),
    )

    argument_spec = dict(
        name=dict(type='str', required=False),
        arn=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        description=dict(type='str', required=False),
        tags=dict(type='dict', required=False, aliases=['resource_tags']),
        purge_tags=dict(type='bool', required=False, default=True),
        stateful_rule_groups=dict(type='list', elements='str', required=False, aliases=['stateful_groups']),
        stateless_rule_groups=dict(type='list', elements='str', required=False, aliases=['stateless_groups']),
        stateful_default_actions=dict(type='list', elements='str', required=False),
        stateless_default_actions=dict(type='list', elements='str', required=False),
        stateless_fragment_default_actions=dict(type='list', elements='str', required=False),
        stateful_rule_order=dict(type='str', required=False, choices=['strict', 'default'], aliases=['rule_order']),
        stateless_custom_actions=dict(type='list', elements='dict', required=False,
                                      options=custom_action_options, aliases=['custom_stateless_actions']),
        purge_stateless_custom_actions=dict(type='bool', required=False, default=True, aliases=['purge_custom_stateless_actions']),
        wait=dict(type='bool', required=False, default=True),
        wait_timeout=dict(type='int', required=False),
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

    manager = NetworkFirewallPolicyManager(module, name=name, arn=arn)
    manager.set_wait(module.params.get('wait', None))
    manager.set_wait_timeout(module.params.get('wait_timeout', None))

    rule_order = module.params.get('stateful_rule_order')
    if rule_order and rule_order != "default":
        module.require_botocore_at_least('1.21.52', reason='to set the rule order')
    if module.params.get('stateful_default_actions'):
        module.require_botocore_at_least(
            '1.21.52', reason='to set the default actions for stateful flows')

    if state == 'absent':
        manager.delete()
    else:
        manager.set_description(module.params.get('description', None))
        manager.set_tags(module.params.get('tags', None), module.params.get('purge_tags', None))
        # Actions need to be defined before potentially consuming them
        manager.set_custom_stateless_actions(
            module.params.get('stateless_custom_actions', None),
            module.params.get('purge_stateless_custom_actions', True)),
        manager.set_stateful_rule_order(module.params.get('stateful_rule_order', None))
        manager.set_stateful_rule_groups(module.params.get('stateful_rule_groups', None))
        manager.set_stateless_rule_groups(module.params.get('stateless_rule_groups', None))
        manager.set_stateful_default_actions(module.params.get('stateful_default_actions', None))
        manager.set_stateless_default_actions(module.params.get('stateless_default_actions', None))
        manager.set_stateless_fragment_default_actions(module.params.get('stateless_fragment_default_actions', None))

        manager.flush_changes()

    results = dict(
        changed=manager.changed,
        policy=manager.updated_resource,
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

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: networkfirewall_rule_group_info
short_description: describe AWS Network Firewall rule groups
version_added: 4.0.0
description:
  - A module for describing AWS Network Firewall rule groups.
options:
  arn:
    description:
      - The ARN of the Network Firewall rule group.
      - At time of writing AWS does not support describing Managed Rules.
    required: false
    type: str
  name:
    description:
      - The name of the Network Firewall rule group.
    required: false
    type: str
  rule_type:
    description:
      - Indicates whether the rule group is stateless or stateful.
      - Required if I(name) is provided.
    required: false
    aliases: ['type' ]
    choices: ['stateful', 'stateless']
    type: str
  scope:
    description:
      - The scope of the request.
      - When I(scope='account') returns a description of all rule groups in the account.
      - When I(scope='managed') returns a list of available managed rule group arns.
      - By default searches only at the account scope.
      - I(scope='managed') requires botocore>=1.23.23.
    required: false
    choices: ['managed', 'account']
    type: str

author: Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
'''

EXAMPLES = '''

# Describe all Rule Groups in an account (excludes managed groups)
- community.aws.networkfirewall_rule_group_info: {}

# List the available Managed Rule groups (AWS doesn't support describing the
# groups)
- community.aws.networkfirewall_rule_group_info:
    scope: managed

# Describe a Rule Group by ARN
- community.aws.networkfirewall_rule_group_info:
    arn: arn:aws:network-firewall:us-east-1:123456789012:stateful-rulegroup/ExampleRuleGroup

# Describe a Rule Group by name
- community.aws.networkfirewall_rule_group_info:
    name: ExampleRuleGroup
    type: stateful

'''

RETURN = '''
rule_list:
  description: A list of ARNs of the matching rule groups.
  type: list
  elements: str
  returned: When a rule name isn't specified

rule_groups:
  description: The details of the rule groups
  returned: success
  type: list
  elements: dict
  contains:
    rule_group:
      description: Details of the rules in the rule group
      type: dict
      returned: success
      contains:
        rule_variables:
          description: Settings that are available for use in the rules in the rule group.
          returned: When rule variables are attached to the rule group.
          type: complex
          contains:
            ip_sets:
              description: A dictionary mapping variable names to IP addresses in CIDR format.
              returned: success
              type: dict
              example: ['192.0.2.0/24']
            port_sets:
              description: A dictionary mapping variable names to ports
              returned: success
              type: dict
              example: ['42']
        stateful_rule_options:
          description: Additional options governing how Network Firewall handles stateful rules.
          returned: When the rule group is either "rules string" or "rules list" based.
          type: dict
          contains:
            rule_order:
              description: The order in which rules will be evaluated.
              returned: success
              type: str
              example: 'DEFAULT_ACTION_ORDER'
        rules_source:
          description: DEFAULT_ACTION_ORDER
          returned: success
          type: dict
          contains:
            stateful_rules:
              description: A list of dictionaries describing the rules that the rule group is comprised of.
              returned: When the rule group is "rules list" based.
              type: list
              elements: dict
              contains:
                action:
                  description: What action to perform when a flow matches the rule criteria.
                  returned: success
                  type: str
                  example: 'PASS'
                header:
                  description: A description of the criteria used for the rule.
                  returned: success
                  type: dict
                  contains:
                    protocol:
                      description: The protocol to inspect for.
                      returned: success
                      type: str
                      example: 'IP'
                    source:
                      description: The source address or range of addresses to inspect for.
                      returned: success
                      type: str
                      example: '203.0.113.98'
                    source_port:
                      description: The source port to inspect for.
                      returned: success
                      type: str
                      example: '42'
                    destination:
                      description: The destination address or range of addresses to inspect for.
                      returned: success
                      type: str
                      example: '198.51.100.0/24'
                    destination_port:
                      description: The destination port to inspect for.
                      returned: success
                      type: str
                      example: '6666:6667'
                    direction:
                      description: The direction of traffic flow to inspect.
                      returned: success
                      type: str
                      example: 'FORWARD'
                rule_options:
                  description: Additional Suricata RuleOptions settings for the rule.
                  returned: success
                  type: list
                  elements: dict
                  contains:
                    keyword:
                      description: The keyword for the setting.
                      returned: success
                      type: str
                      example: 'sid:1'
                    settings:
                      description: A list of values passed to the setting.
                      returned: When values are available
                      type: list
                      elements: str
            rules_string:
              description: A string describing the rules that the rule group is comprised of.
              returned: When the rule group is "rules string" based.
              type: str
            rules_source_list:
              description: A description of the criteria for a domain list rule group.
              returned: When the rule group is "domain list" based.
              type: dict
              contains:
                targets:
                  description: A list of domain names to be inspected for.
                  returned: success
                  type: list
                  elements: str
                  example: ['abc.example.com', '.example.net']
                target_types:
                  description: The protocols to be inspected by the rule group.
                  returned: success
                  type: list
                  elements: str
                  example: ['TLS_SNI', 'HTTP_HOST']
                generated_rules_type:
                  description: Whether the rule group allows or denies access to the domains in the list.
                  returned: success
                  type: str
                  example: 'ALLOWLIST'
            stateless_rules_and_custom_actions:
              description: A description of the criteria for a stateless rule group.
              returned: When the rule group is a stateless rule group.
              type: dict
              contains:
                stateless_rules:
                  description: A list of stateless rules for use in a stateless rule group.
                  type: list
                  elements: dict
                  contains:
                    rule_definition:
                      description: Describes the stateless 5-tuple inspection criteria and actions for the rule.
                      returned: success
                      type: dict
                      contains:
                        match_attributes:
                          description: Describes the stateless 5-tuple inspection criteria for the rule.
                          returned: success
                          type: dict
                          contains:
                            sources:
                              description: The source IP addresses and address ranges to inspect for.
                              returned: success
                              type: list
                              elements: dict
                              contains:
                                address_definition:
                                  description: An IP address or a block of IP addresses in CIDR notation.
                                  returned: success
                                  type: str
                                  example: '192.0.2.3'
                            destinations:
                              description: The destination IP addresses and address ranges to inspect for.
                              returned: success
                              type: list
                              elements: dict
                              contains:
                                address_definition:
                                  description: An IP address or a block of IP addresses in CIDR notation.
                                  returned: success
                                  type: str
                                  example: '192.0.2.3'
                            source_ports:
                              description: The source port ranges to inspect for.
                              returned: success
                              type: list
                              elements: dict
                              contains:
                                from_port:
                                  description: The lower limit of the port range.
                                  returned: success
                                  type: int
                                to_port:
                                  description: The upper limit of the port range.
                                  returned: success
                                  type: int
                            destination_ports:
                              description: The destination port ranges to inspect for.
                              returned: success
                              type: list
                              elements: dict
                              contains:
                                from_port:
                                  description: The lower limit of the port range.
                                  returned: success
                                  type: int
                                to_port:
                                  description: The upper limit of the port range.
                                  returned: success
                                  type: int
                            protocols:
                              description: The IANA protocol numbers of the protocols to inspect for.
                              returned: success
                              type: list
                              elements: int
                              example: [6]
                            tcp_flags:
                              description: The TCP flags and masks to inspect for.
                              returned: success
                              type: list
                              elements: dict
                              contains:
                                flags:
                                  description: Used with masks to define the TCP flags that flows are inspected for.
                                  returned: success
                                  type: list
                                  elements: str
                                masks:
                                  description: The set of flags considered during inspection.
                                  returned: success
                                  type: list
                                  elements: str
                        actions:
                          description: The actions to take when a flow matches the rule.
                          returned: success
                          type: list
                          elements: str
                          example: ['aws:pass', 'CustomActionName']
                    priority:
                      description: Indicates the order in which to run this rule relative to all of the rules that are defined for a stateless rule group.
                      returned: success
                      type: int
                custom_actions:
                  description: A list of individual custom action definitions that are available for use in stateless rules.
                  type: list
                  elements: dict
                  contains:
                    action_name:
                      description: The name for the custom action.
                      returned: success
                      type: str
                    action_definition:
                      description: The custom action associated with the action name.
                      returned: success
                      type: dict
                      contains:
                        publish_metric_action:
                          description: The description of an action which publishes to CloudWatch.
                          returned: When the action publishes to CloudWatch.
                          type: dict
                          contains:
                            dimensions:
                              description: The value to use in an Amazon CloudWatch custom metric dimension.
                              returned: success
                              type: list
                              elements: dict
                              contains:
                                value:
                                  description: The value to use in the custom metric dimension.
                                  returned: success
                                  type: str
    rule_group_metadata:
      description: Details of the rules in the rule group
      type: dict
      returned: success
      contains:
        capacity:
          description: The maximum operating resources that this rule group can use.
          type: int
          returned: success
        consumed_capacity:
          description: The number of capacity units currently consumed by the rule group rules.
          type: int
          returned: success
        description:
          description: A description of the rule group.
          type: str
          returned: success
        number_of_associations:
          description: The number of firewall policies that use this rule group.
          type: int
          returned: success
        rule_group_arn:
          description: The ARN for the rule group
          type: int
          returned: success
          example: 'arn:aws:network-firewall:us-east-1:123456789012:stateful-rulegroup/ExampleGroup'
        rule_group_id:
          description: A unique identifier for the rule group.
          type: int
          returned: success
          example: '12345678-abcd-1234-abcd-123456789abc'
        rule_group_name:
          description: The name of the rule group.
          type: str
          returned: success
        rule_group_status:
          description: The current status of a rule group.
          type: str
          returned: success
          example: 'DELETING'
        tags:
          description: A dictionary representing the tags associated with the rule group.
          type: dict
          returned: success
        type:
          description: Whether the rule group is stateless or stateful.
          type: str
          returned: success
          example: 'STATEFUL'
'''


from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.community.aws.plugins.module_utils.networkfirewall import NetworkFirewallRuleManager


def main():

    argument_spec = dict(
        name=dict(type='str', required=False),
        rule_type=dict(type='str', required=False, aliases=['type'], choices=['stateless', 'stateful']),
        arn=dict(type='str', required=False),
        scope=dict(type='str', required=False, choices=['managed', 'account']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('arn', 'name',),
            ('arn', 'rule_type'),
        ],
        required_together=[
            ('name', 'rule_type'),
        ]
    )

    module.require_botocore_at_least('1.19.20')

    arn = module.params.get('arn')
    name = module.params.get('name')
    rule_type = module.params.get('rule_type')
    scope = module.params.get('scope')

    if module.params.get('scope') == 'managed':
        module.require_botocore_at_least('1.23.23', reason='to list managed rules')

    manager = NetworkFirewallRuleManager(module, name=name, rule_type=rule_type)

    results = dict(changed=False)

    if name or arn:
        rule = manager.get_rule_group(name=name, rule_type=rule_type, arn=arn)
        if rule:
            results['rule_groups'] = [rule]
        else:
            results['rule_groups'] = []
    else:
        rule_list = manager.list(scope=scope)
        results['rule_list'] = rule_list
        if scope != 'managed':
            rules = [manager.get_rule_group(arn=r) for r in rule_list]
            results['rule_groups'] = rules

    module.exit_json(**results)


if __name__ == '__main__':
    main()

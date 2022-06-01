#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: networkfirewall_rule_group
short_description: create, delete and modify AWS Network Firewall rule groups
version_added: 4.0.0
description:
  - A module for managing AWS Network Firewall rule groups.
  - U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/index.html)
  - Currently only supports C(stateful) firewall groups.
options:
  arn:
    description:
      - The ARN of the Network Firewall rule group.
      - Exactly one of I(arn) and I(name) must be provided.
    required: false
    type: str
  name:
    description:
      - The name of the Network Firewall rule group.
      - When I(name) is set, I(rule_type) must also be set.
    required: false
    type: str
  rule_type:
    description:
      - Indicates whether the rule group is stateless or stateful.
      - Stateless rulesets are currently not supported.
      - Required if I(name) is set.
    required: false
    aliases: ['type' ]
    choices: ['stateful']
#    choices: ['stateful', 'stateless']
    type: str
  state:
    description:
      - Create or remove the Network Firewall rule group.
    required: false
    choices: ['present', 'absent']
    default: 'present'
    type: str
  capacity:
    description:
      - The maximum operating resources that this rule group can use.
      - Once a rule group is created this parameter is immutable.
      - See also the AWS documentation about how capacityis calculated
        U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/nwfw-rule-group-capacity.html)
      - This option is mandatory when creating a new rule group.
    type: int
    required: false
  rule_order:
    description:
      - Indicates how to manage the order of the rule evaluation for the rule group.
      - Once a rule group is created this parameter is immutable.
      - Mutually exclusive with I(rule_type=stateless).
      - For more information on how rules are evaluated read the AWS documentation
        U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/suricata-rule-evaluation-order.html).
      - I(rule_order) requires botocore>=1.23.23.
    type: str
    required: false
    choices: ['default', 'strict']
    aliases: ['stateful_rule_order']
  description:
    description:
      - A description of the AWS Network Firewall rule group.
    type: str
  ip_variables:
    description:
      - A dictionary mapping variable names to a list of IP addresses and address ranges, in CIDR notation.
      - For example C({EXAMPLE_HOSTS:["192.0.2.0/24", "203.0.113.42"]}).
      - Mutually exclusive with I(domain_list).
    type: dict
    required: false
    aliases: ['ip_set_variables']
  purge_ip_variables:
    description:
      - Whether to purge variable names not mentioned in the I(ip_variables)
        dictionary.
      - To remove all IP Set Variables it is necessary to explicitly set I(ip_variables={})
        and I(purge_port_variables=true).
    type: bool
    default: true
    required: false
    aliases: ['purge_ip_set_variables']
  port_variables:
    description:
      - A dictionary mapping variable names to a list of ports.
      - For example C({SECURE_PORTS:["22", "443"]}).
    type: dict
    required: false
    aliases: ['port_set_variables']
  purge_port_variables:
    description:
      - Whether to purge variable names not mentioned in the I(port_variables)
        dictionary.
      - To remove all Port Set Variables it is necessary to explicitly set I(port_variables={})
        and I(purge_port_variables=true).
    type: bool
    required: false
    default: true
    aliases: ['purge_port_set_variables']
  rule_strings:
    description:
      - Rules in Suricata format.
      - If I(rule_strings) is specified, it must include at least one entry.
      - For more information read the AWS documentation
        U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/suricata-limitations-caveats.html)
        and the Suricata documentation
        U(https://suricata.readthedocs.io/en/suricata-6.0.0/rules/intro.html).
      - Mutually exclusive with I(rule_type=stateless).
      - Mutually exclusive with I(domain_list) and I(rule_list).
      - Exactly one of I(rule_strings), I(domain_list) or I(rule_list) must be
        specified at creation time.
    type: list
    elements: str
    required: false
  domain_list:
    description:
      - Inspection criteria for a domain list rule group.
      - When set overwrites all Domain List settings with the new configuration.
      - For more information about domain name based filtering
        read the AWS documentation
        U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/stateful-rule-groups-domain-names.html).
      - Mutually exclusive with I(rule_type=stateless).
      - Mutually exclusive with I(ip_variables), I(rule_list) and I(rule_strings).
      - Exactly one of I(rule_strings), I(domain_list) or I(rule_list) must be
        specified at creation time.
    type: dict
    required: false
    suboptions:
      domain_names:
        description:
          - A list of domain names to look for in the traffic flow.
        type: list
        elements: str
        required: true
      filter_http:
        description:
          - Whether HTTP traffic should be inspected (uses the host header).
        type: bool
        required: false
        default: false
      filter_https:
        description:
          - Whether HTTPS traffic should be inspected (uses the SNI).
        type: bool
        required: false
        default: false
      action:
        description:
          - Action to perform on traffic that matches the rule match settings.
        type: str
        required: true
        choices: ['allow', 'deny']
      source_ips:
        description:
          - Used to expand the local network definition beyond the CIDR range
            of the VPC where you deploy Network Firewall.
        type: list
        elements: str
        required: false
  rule_list:
    description:
      - Inspection criteria to be used for a 5-tuple based rule group.
      - When set overwrites all existing 5-tuple rules with the new configuration.
      - Mutually exclusive with I(domain_list) and I(rule_strings).
      - Mutually exclusive with I(rule_type=stateless).
      - Exactly one of I(rule_strings), I(domain_list) or I(rule_list) must be
        specified at creation time.
      - For more information about valid values see the AWS documentation
        U(https://docs.aws.amazon.com/network-firewall/latest/APIReference/API_StatefulRule.html)
        and
        U(https://docs.aws.amazon.com/network-firewall/latest/APIReference/API_Header.html).
      - 'Note: Idempotency when comparing AWS Web UI and Ansiible managed rules can not be guaranteed'
    type: list
    elements: dict
    required: false
    aliases: ['stateful_rule_list']
    suboptions:
      action:
        description:
          - What Network Firewall should do with the packets in a traffic flow when the flow matches.
        type: str
        required: true
        choices: ['pass', 'drop', 'alert']
      protocol:
        description:
          - The protocol to inspect for. To specify all, you can use C(IP), because all traffic on AWS is C(IP).
        type: str
        required: true
      source:
        description:
          - The source IP address or address range to inspect for, in CIDR notation.
          - To match with any address, specify C(ANY).
        type: str
        required: true
      source_port:
        description:
          - The source port to inspect for.
          - To match with any port, specify C(ANY).
        type: str
        required: true
      direction:
        description:
          - The direction of traffic flow to inspect.
          - If set to C(any), the inspection matches both traffic going from the
            I(source) to the I(destination) and from the I(destination) to the
            I(source).
          - If set to C(forward), the inspection only matches traffic going from the
            I(source) to the I(destination).
        type: str
        required: false
        default: 'forward'
        choices: ['forward', 'any']
      destination:
        description:
          - The destination IP address or address range to inspect for, in CIDR notation.
          - To match with any address, specify C(ANY).
        type: str
        required: true
      destination_port:
        description:
          - The source port to inspect for.
          - To match with any port, specify C(ANY).
        type: str
        required: true
      sid:
        description:
          - The signature ID of the rule.
          - A unique I(sid) must be passed for all rules.
        type: int
        required: true
      rule_options:
        description:
          - Additional options for the rule.
          - 5-tuple based rules are converted by AWS into Suricata rules, for more
            complex options requirements where order matters consider using I(rule_strings).
          - A dictionary mapping Suricata RuleOptions names to a list of values.
          - The examples section contains some examples of using rule_options.
          - For more information read the AWS documentation
            U(https://docs.aws.amazon.com/network-firewall/latest/developerguide/suricata-limitations-caveats.html)
            and the Suricata documentation
            U(https://suricata.readthedocs.io/en/suricata-6.0.0/rules/intro.html).
        type: dict
        required: false
  wait:
    description:
      - Whether to wait for the firewall rule group to reach the
        C(ACTIVE) or C(DELETED) state before the module returns.
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - Maximum time, in seconds, to wait for the firewall rule group
        to reach the expected state.
      - Defaults to 600 seconds.
    type: int
    required: false


author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
'''

EXAMPLES = '''
# Create a rule group
- name: Create a minimal AWS Network Firewall Rule Group
  community.aws.networkfirewall_rule_group:
    name: 'MinimalGroup'
    type: 'stateful'
    capacity: 200
    rule_strings:
      - 'pass tcp any any -> any any (sid:1000001;)'

# Create an example rule group using rule_list
- name: Create 5-tuple Rule List based rule group
  community.aws.networkfirewall_rule_group:
    name: 'ExampleGroup'
    type: 'stateful'
    description: 'My description'
    rule_order: default
    capacity: 100
    rule_list:
      - sid: 1
        direction: forward
        action: pass
        protocol: IP
        source: any
        source_port: any
        destination: any
        destination_port: any

# Create an example rule group using rule_list
- name: Create 5-tuple Rule List based rule group
  community.aws.networkfirewall_rule_group:
    name: 'ExampleGroup'
    type: 'stateful'
    description: 'My description'
    ip_variables:
      SOURCE_IPS: ['203.0.113.0/24', '198.51.100.42']
      DESTINATION_IPS: ['192.0.2.0/24', '198.51.100.48']
    port_variables:
      HTTP_PORTS: [80, 8080]
    rule_order: default
    capacity: 100
    rule_list:
      # Allow 'Destination Unreachable' traffic
      - sid: 1
        action: pass
        protocol: icmp
        source: any
        source_port: any
        destination: any
        destination_port: any
        rule_options:
          itype: 3
      - sid: 2
        action: drop
        protocol: tcp
        source: "$SOURCE_IPS"
        source_port: any
        destination: "$DESTINATION_IPS"
        destination_port: "$HTTP_PORTS"
        rule_options:
          urilen: ["20<>40"]
          # Where only a keyword is needed, add the keword, but no value
          http_uri:
          # Settings where Suricata expects raw strings (like the content
          # keyword) will need to have the double-quotes explicitly escaped and
          # passed because there's no practical way to distinguish between them
          # and flags.
          content: '"index.php"'

# Create an example rule group using Suricata rule strings
- name: Create Suricata rule string based rule group
  community.aws.networkfirewall_rule_group:
    name: 'ExampleSuricata'
    type: 'stateful'
    description: 'My description'
    capacity: 200
    ip_variables:
      EXAMPLE_IP: ['203.0.113.0/24', '198.51.100.42']
      ANOTHER_EXAMPLE: ['192.0.2.0/24', '198.51.100.48']
    port_variables:
      EXAMPLE_PORT: [443, 22]
    rule_strings:
      - 'pass tcp any any -> $EXAMPLE_IP $EXAMPLE_PORT (sid:1000001;)'
      - 'pass udp any any -> $ANOTHER_EXAMPLE any (sid:1000002;)'

# Create an example Domain List based rule group
- name: Create Domain List based rule group
  community.aws.networkfirewall_rule_group:
    name: 'ExampleDomainList'
    type: 'stateful'
    description: 'My description'
    capacity: 100
    domain_list:
      domain_names:
        - 'example.com'
        - '.example.net'
      filter_https: True
      filter_http: True
      action: allow
      source_ips: '192.0.2.0/24'

# Update the description of a rule group
- name: Update the description of a rule group
  community.aws.networkfirewall_rule_group:
    name: 'MinimalGroup'
    type: 'stateful'
    description: 'Another description'

# Update IP Variables for a rule group
- name: Update IP Variables
  community.aws.networkfirewall_rule_group:
    name: 'ExampleGroup'
    type: 'stateful'
    ip_variables:
      EXAMPLE_IP: ['192.0.2.0/24', '203.0.113.0/24', '198.51.100.42']
    purge_ip_variables: false

# Delete a rule group
- name: Delete a rule group
  community.aws.networkfirewall_rule_group:
    name: 'MinimalGroup'
    type: 'stateful'
    state: absent

'''

RETURN = '''
rule_group:
  description: Details of the rules in the rule group
  type: dict
  returned: success
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
          description: Inspection criteria used for a 5-tuple based rule group.
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

    domain_list_spec = dict(
        domain_names=dict(type='list', elements='str', required=True),
        filter_http=dict(type='bool', required=False, default=False),
        filter_https=dict(type='bool', required=False, default=False),
        action=dict(type='str', required=True, choices=['allow', 'deny']),
        source_ips=dict(type='list', elements='str', required=False),
    )

    rule_list_spec = dict(
        action=dict(type='str', required=True, choices=['pass', 'drop', 'alert']),
        protocol=dict(type='str', required=True),
        source=dict(type='str', required=True),
        source_port=dict(type='str', required=True),
        direction=dict(type='str', required=False, default='forward', choices=['forward', 'any']),
        destination=dict(type='str', required=True),
        destination_port=dict(type='str', required=True),
        sid=dict(type='int', required=True),
        rule_options=dict(type='dict', required=False),
    )

    argument_spec = dict(
        arn=dict(type='str', required=False),
        name=dict(type='str', required=False),
        rule_type=dict(type='str', required=False, aliases=['type'], choices=['stateful']),
        # rule_type=dict(type='str', required=True, aliases=['type'], choices=['stateless', 'stateful']),
        state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
        capacity=dict(type='int', required=False),
        rule_order=dict(type='str', required=False, aliases=['stateful_rule_order'], choices=['default', 'strict']),
        description=dict(type='str', required=False),
        ip_variables=dict(type='dict', required=False, aliases=['ip_set_variables']),
        purge_ip_variables=dict(type='bool', required=False, aliases=['purge_ip_set_variables'], default=True),
        port_variables=dict(type='dict', required=False, aliases=['port_set_variables']),
        purge_port_variables=dict(type='bool', required=False, aliases=['purge_port_set_variables'], default=True),
        rule_strings=dict(type='list', elements='str', required=False),
        domain_list=dict(type='dict', options=domain_list_spec, required=False),
        rule_list=dict(type='list', elements='dict', aliases=['stateful_rule_list'], options=rule_list_spec, required=False),
        tags=dict(type='dict', required=False, aliases=['resource_tags']),
        purge_tags=dict(type='bool', required=False, default=True),
        wait=dict(type='bool', required=False, default=True),
        wait_timeout=dict(type='int', required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('name', 'arn'),
            ('rule_strings', 'domain_list', 'rule_list'),
            ('domain_list', 'ip_variables'),
        ],
        required_together=[
            ('name', 'rule_type'),
        ],
        required_one_of=[
            ('name', 'arn'),
        ],
    )

    module.require_botocore_at_least('1.19.20')

    state = module.params.get('state')
    name = module.params.get('name')
    arn = module.params.get('arn')
    rule_type = module.params.get('rule_type')

    if rule_type == 'stateless':
        if module.params.get('rule_order'):
            module.fail_json('rule_order can not be set for stateless rule groups')
        if module.params.get('rule_strings'):
            module.fail_json('rule_strings can only be used for stateful rule groups')
        if module.params.get('rule_list'):
            module.fail_json('rule_list can only be used for stateful rule groups')
        if module.params.get('domain_list'):
            module.fail_json('domain_list can only be used for stateful rule groups')

    if module.params.get('rule_order'):
        module.require_botocore_at_least('1.23.23', reason='to set the rule order')

    manager = NetworkFirewallRuleManager(module, arn=arn, name=name, rule_type=rule_type)
    manager.set_wait(module.params.get('wait', None))
    manager.set_wait_timeout(module.params.get('wait_timeout', None))

    if state == 'absent':
        manager.delete()
    else:
        manager.set_description(module.params.get('description'))
        manager.set_capacity(module.params.get('capacity'))
        manager.set_rule_order(module.params.get('rule_order'))
        manager.set_ip_variables(module.params.get('ip_variables'), module.params.get('purge_ip_variables'))
        manager.set_port_variables(module.params.get('port_variables'), module.params.get('purge_port_variables'))
        manager.set_rule_string(module.params.get('rule_strings'))
        manager.set_domain_list(module.params.get('domain_list'))
        manager.set_rule_list(module.params.get('rule_list'))
        manager.set_tags(module.params.get('tags'), module.params.get('purge_tags'))

        manager.flush_changes()

    results = dict(
        changed=manager.changed,
        rule_group=manager.updated_resource,
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

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: networkfirewall_policy_info
short_description: describe AWS Network Firewall policies
version_added: 4.0.0
description:
  - A module for describing AWS Network Firewall policies.
options:
  arn:
    description:
      - The ARN of the Network Firewall policy.
      - Mutually exclusive with I(name).
    required: false
    type: str
  name:
    description:
      - The name of the Network Firewall policy.
      - Mutually exclusive with I(arn).
    required: false
    type: str

author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""

# Describe all Firewall policies in an account
- community.aws.networkfirewall_policy_info: {}

# Describe a Firewall policy by ARN
- community.aws.networkfirewall_policy_info:
    arn: arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/ExamplePolicy

# Describe a Firewall policy by name
- community.aws.networkfirewall_policy_info:
    name: ExamplePolicy
"""

RETURN = r"""
policy_list:
  description: A list of ARNs of the matching policies.
  type: list
  elements: str
  returned: When a policy name isn't specified
  example: ['arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/Example1',
            'arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/Example2']

policies:
  description: The details of the policies
  returned: success
  type: list
  elements: dict
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
"""

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule
from ansible_collections.community.aws.plugins.module_utils.networkfirewall import NetworkFirewallPolicyManager


def main():
    argument_spec = dict(
        name=dict(type="str", required=False),
        arn=dict(type="str", required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ["arn", "name"],
        ],
    )

    arn = module.params.get("arn")
    name = module.params.get("name")

    manager = NetworkFirewallPolicyManager(module)

    results = dict(changed=False)

    if name or arn:
        policy = manager.get_policy(name=name, arn=arn)
        if policy:
            results["policies"] = [policy]
        else:
            results["policies"] = []
    else:
        policy_list = manager.list()
        results["policy_list"] = policy_list
        policies = [manager.get_policy(arn=p) for p in policy_list]
        results["policies"] = policies

    module.exit_json(**results)


if __name__ == "__main__":
    main()

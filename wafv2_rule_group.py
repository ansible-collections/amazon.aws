#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_rule_group
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_web_acl
description:
  - Create, modify and delete wafv2 rule groups.
options:
    state:
      description:
        - Whether the rule is present or absent.
      choices: ["present", "absent"]
      required: true
      type: str
    name:
      description:
        - The name of the rule group.
      required: true
      type: str
    rules:
      description:
        - The Rule statements used to identify the web requests that you want to allow, block, or count.
      type: list
      elements: dict
    scope:
      description:
        - Scope of wafv2 rule group.
      required: true
      choices: ["CLOUDFRONT","REGIONAL"]
      type: str
    description:
      description:
        - Description of wafv2 rule group.
      type: str
    sampled_requests:
      description:
        - Sampled requests, true or false.
      type: bool
      default: false
    cloudwatch_metrics:
      description:
        - Enable cloudwatch metric for wafv2 rule group
      type: bool
      default: true
    metric_name:
      description:
        - Name of cloudwatch metrics.
        - If not given and cloudwatch_metrics is enabled, the name of the rule group itself will be taken.
      type: str
    capacity:
      description:
        - capacity of wafv2 rule group.
      type: int
    purge_rules:
      description:
        - When set to C(no), keep the existing load balancer rules in place. Will modify and add, but will not delete.
      default: yes
      type: bool

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.tags

'''

EXAMPLES = '''
- name: change description
  community.aws.wafv2_rule_group:
    name: test02
    state: present
    description: hallo eins zwei
    scope: REGIONAL
    capacity: 500
    rules:
      - name: eins
        priority: 1
        action:
          allow: {}
        visibility_config:
          sampled_requests_enabled: yes
          cloud_watch_metrics_enabled: yes
          metric_name: fsd
        statement:
          ip_set_reference_statement:
            arn: "{{ IPSET.arn }}"
    cloudwatch_metrics: yes
    tags:
      A: B
      C: D
  register: out

- name: add rule
  community.aws.wafv2_rule_group:
    name: test02
    state: present
    description: hallo eins zwei
    scope: REGIONAL
    capacity: 500
    rules:
      - name: eins
        priority: 1
        action:
          allow: {}
        visibility_config:
          sampled_requests_enabled: yes
          cloud_watch_metrics_enabled: yes
          metric_name: fsd
        statement:
          ip_set_reference_statement:
            arn: "{{ IPSET.arn }}"
      - name: zwei
        priority: 2
        action:
          block: {}
        visibility_config:
          sampled_requests_enabled: yes
          cloud_watch_metrics_enabled: yes
          metric_name: ddos
        statement:
          or_statement:
            statements:
              - byte_match_statement:
                  search_string: ansible.com
                  positional_constraint: CONTAINS
                  field_to_match:
                    single_header:
                      name: host
                  text_transformations:
                    - type: LOWERCASE
                      priority: 0
              - xss_match_statement:
                  field_to_match:
                    body: {}
                  text_transformations:
                    - type: NONE
                      priority: 0
    cloudwatch_metrics: yes
    tags:
      A: B
      C: D
  register: out
'''

RETURN = """
arn:
    description: Rule group arn
    sample: arn:aws:wafv2:eu-central-1:11111111:regional/rulegroup/test02/6e90c01a-e4eb-43e5-b6aa-b1604cedf7d7
    type: str
    returned: Always, as long as the web acl exists
description:
    description: Description of the rule group
    sample: Some rule group description
    returned: Always, as long as the web acl exists
    type: str
capacity:
    description: Current capacity of the rule group
    sample: 500
    returned: Always, as long as the rule group exists
    type: int
name:
    description: Rule group name
    sample: test02
    returned: Always, as long as the rule group exists
    type: str
rules:
    description: Current rules of the rule group
    returned: Always, as long as the rule group exists
    type: list
    sample:
        - action:
             allow: {}
          name: eins
          priority: 1
          statement:
              ip_set_reference_statement:
                  arn: arn:aws:wafv2:eu-central-1:11111111:regional/ipset/test02/b6978915-c67b-4d1c-8832-2b1bb452143a
          visibility_config:
              cloud_watch_metrics_enabled: True
              metric_name: fsd
              sampled_requests_enabled: True
visibility_config:
    description: Visibility config of the rule group
    returned: Always, as long as the rule group exists
    type: dict
    sample:
        cloud_watch_metrics_enabled: True
        metric_name: blub
        sampled_requests_enabled: False
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict
from ansible_collections.community.aws.plugins.module_utils.wafv2 import compare_priority_rules
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_rule_groups
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_snake_dict_to_camel_dict
from ansible_collections.community.aws.plugins.module_utils.wafv2 import describe_wafv2_tags
from ansible_collections.community.aws.plugins.module_utils.wafv2 import ensure_wafv2_tags


class RuleGroup:
    def __init__(self, wafv2, name, scope, fail_json_aws):
        self.wafv2 = wafv2
        self.id = None
        self.name = name
        self.scope = scope
        self.fail_json_aws = fail_json_aws
        self.existing_group = self.get_group()

    def update(self, description, rules, sampled_requests, cloudwatch_metrics, metric_name):
        req_obj = {
            'Name': self.name,
            'Scope': self.scope,
            'Id': self.id,
            'Rules': rules,
            'LockToken': self.locktoken,
            'VisibilityConfig': {
                'SampledRequestsEnabled': sampled_requests,
                'CloudWatchMetricsEnabled': cloudwatch_metrics,
                'MetricName': metric_name
            }
        }

        if description:
            req_obj['Description'] = description

        try:
            response = self.wafv2.update_rule_group(**req_obj)
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to update wafv2 rule group.")
        return self.refresh_group()

    def get_group(self):
        if self.id is None:
            response = self.list()

            for item in response.get('RuleGroups'):
                if item.get('Name') == self.name:
                    self.id = item.get('Id')
                    self.locktoken = item.get('LockToken')
                    self.arn = item.get('ARN')

        return self.refresh_group()

    def refresh_group(self):
        existing_group = None
        if self.id:
            try:
                response = self.wafv2.get_rule_group(
                    Name=self.name,
                    Scope=self.scope,
                    Id=self.id
                )
                existing_group = response.get('RuleGroup')
                self.locktoken = response.get('LockToken')
            except (BotoCoreError, ClientError) as e:
                self.fail_json_aws(e, msg="Failed to get wafv2 rule group.")

            tags = describe_wafv2_tags(self.wafv2, self.arn, self.fail_json_aws)
            existing_group['tags'] = tags or {}

        return existing_group

    def list(self):
        return wafv2_list_rule_groups(self.wafv2, self.scope, self.fail_json_aws)

    def get(self):
        if self.existing_group:
            return self.existing_group
        return None

    def remove(self):
        try:
            response = self.wafv2.delete_rule_group(
                Name=self.name,
                Scope=self.scope,
                Id=self.id,
                LockToken=self.locktoken
            )
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to delete wafv2 rule group.")
        return response

    def create(self, capacity, description, rules, sampled_requests, cloudwatch_metrics, metric_name, tags):
        req_obj = {
            'Name': self.name,
            'Scope': self.scope,
            'Capacity': capacity,
            'Rules': rules,
            'VisibilityConfig': {
                'SampledRequestsEnabled': sampled_requests,
                'CloudWatchMetricsEnabled': cloudwatch_metrics,
                'MetricName': metric_name
            }
        }

        if description:
            req_obj['Description'] = description

        if tags:
            req_obj['Tags'] = ansible_dict_to_boto3_tag_list(tags)

        try:
            response = self.wafv2.create_rule_group(**req_obj)
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to create wafv2 rule group.")

        self.existing_group = self.get_group()

        return self.existing_group


def main():

    arg_spec = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        name=dict(type='str', required=True),
        scope=dict(type='str', required=True, choices=['CLOUDFRONT', 'REGIONAL']),
        capacity=dict(type='int'),
        description=dict(type='str'),
        rules=dict(type='list', elements='dict'),
        sampled_requests=dict(type='bool', default=False),
        cloudwatch_metrics=dict(type='bool', default=True),
        metric_name=dict(type='str'),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
        purge_rules=dict(default=True, type='bool'),
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['capacity', 'rules']]]
    )

    state = module.params.get("state")
    name = module.params.get("name")
    scope = module.params.get("scope")
    capacity = module.params.get("capacity")
    description = module.params.get("description")
    rules = module.params.get("rules")
    sampled_requests = module.params.get("sampled_requests")
    cloudwatch_metrics = module.params.get("cloudwatch_metrics")
    metric_name = module.params.get("metric_name")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    purge_rules = module.params.get("purge_rules")
    check_mode = module.check_mode

    if rules:
        rules = []
        for rule in module.params.get("rules"):
            rules.append(wafv2_snake_dict_to_camel_dict(snake_dict_to_camel_dict(rule, capitalize_first=True)))

    if not metric_name:
        metric_name = name

    wafv2 = module.client('wafv2')
    rule_group = RuleGroup(wafv2, name, scope, module.fail_json_aws)

    change = False
    retval = {}

    if state == 'present':
        if rule_group.get():
            tagging_change = ensure_wafv2_tags(wafv2, rule_group.arn, tags, purge_tags,
                                               module.fail_json_aws, module.check_mode)
            rules_change, rules = compare_priority_rules(rule_group.get().get('Rules'), rules, purge_rules, state)
            description_change = bool(description) and (rule_group.get().get('Description') != description)
            change = tagging_change or rules_change or description_change
            retval = rule_group.get()
            if module.check_mode:
                # In check mode nothing changes...
                pass
            elif rules_change or description_change:
                retval = rule_group.update(
                    description,
                    rules,
                    sampled_requests,
                    cloudwatch_metrics,
                    metric_name
                )
            elif tagging_change:
                retval = rule_group.refresh_group()

        else:
            change = True
            if not check_mode:
                retval = rule_group.create(
                    capacity,
                    description,
                    rules,
                    sampled_requests,
                    cloudwatch_metrics,
                    metric_name,
                    tags
                )

    elif state == 'absent':
        if rule_group.get():
            if rules:
                if len(rules) > 0:
                    change, rules = compare_priority_rules(rule_group.get().get('Rules'), rules, purge_rules, state)
                    if change and not check_mode:
                        retval = rule_group.update(
                            description,
                            rules,
                            sampled_requests,
                            cloudwatch_metrics,
                            metric_name
                        )
            else:
                change = True
                if not check_mode:
                    retval = rule_group.remove()

    module.exit_json(changed=change, **camel_dict_to_snake_dict(retval, ignore_list=['tags']))


if __name__ == '__main__':
    main()

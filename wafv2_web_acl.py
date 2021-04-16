#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_web_acl
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_web_acl
description:
  - Create, modify or delete a wafv2 web acl.
requirements:
  - boto3
  - botocore
options:
    state:
      description:
        - Whether the rule is present or absent.
      choices: ["present", "absent"]
      required: true
      type: str
    name:
      description:
        - The name of the web acl.
      required: true
      type: str
    scope:
      description:
        - Scope of wafv2 web acl.
      required: true
      choices: ["CLOUDFRONT","REGIONAL"]
      type: str
    description:
      description:
        - Description of wafv2 web acl.
      type: str
    default_action:
      description:
        - Default action of the wafv2 web acl.
      choices: ["Block","Allow"]
      type: str
    sampled_requests:
      description:
        - Whether to store a sample of the web requests, true or false.
      type: bool
      default: false
    cloudwatch_metrics:
      description:
        - Enable cloudwatch metric for wafv2 web acl.
      type: bool
      default: true
    metric_name:
      description:
        - Name of cloudwatch metrics.
        - If not given and cloudwatch_metrics is enabled, the name of the web acl itself will be taken.
      type: str
    tags:
      description:
        - tags for wafv2 web acl.
      type: dict
    rules:
      description:
        - The Rule statements used to identify the web requests that you want to allow, block, or count.
      type: list
      elements: dict
      suboptions:
        name:
          description:
            - The name of the wafv2 rule
          type: str
        priority:
          description:
            - The rule priority
          type: int
        action:
          description:
            - Wether a rule is blocked, allowed or counted.
          type: dict
        visibility_config:
          description:
            - Visibility of single wafv2 rule.
          type: dict
        statement:
          description:
            - Rule configuration.
          type: dict
    purge_rules:
      description:
        - When set to C(no), keep the existing load balancer rules in place. Will modify and add, but will not delete.
      default: yes
      type: bool

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: create web acl
  community.aws.wafv2_web_acl:
    name: test05
    state: present
    description: hallo eins
    scope: REGIONAL
    default_action: Allow
    sampled_requests: no
    cloudwatch_metrics: yes
    metric_name: blub
    rules:
      - name: zwei
        priority: 2
        action:
          block: {}
        visibility_config:
          sampled_requests_enabled: yes
          cloud_watch_metrics_enabled: yes
          metric_name: ddos
        statement:
          xss_match_statement:
            field_to_match:
              body: {}
            text_transformations:
              - type: NONE
                priority: 0
      - name: admin_protect
        priority: 1
        override_action:
          none: {}
        visibility_config:
          sampled_requests_enabled: yes
          cloud_watch_metrics_enabled: yes
          metric_name: fsd
        statement:
          managed_rule_group_statement:
            vendor_name: AWS
            name: AWSManagedRulesAdminProtectionRuleSet
    tags:
      A: B
      C: D
  register: out
'''

RETURN = """
arn:
  description: web acl arn
  sample: arn:aws:wafv2:eu-central-1:11111111:regional/webacl/test05/318c1ab9-fa74-4b3b-a974-f92e25106f61
  type: str
  returned: Always, as long as the web acl exists
description:
  description: Description of the web acl
  sample: Some web acl description
  returned: Always, as long as the web acl exists
  type: str
capacity:
  description: Current capacity of the web acl
  sample: 140
  returned: Always, as long as the web acl exists
  type: int
name:
  description: Web acl name
  sample: test02
  returned: Always, as long as the web acl exists
  type: str
rules:
  description: Current rules of the web acl
  returned: Always, as long as the web acl exists
  type: list
  sample:
    - name: admin_protect
      override_action:
        none: {}
      priority: 1
      statement:
        managed_rule_group_statement:
          name: AWSManagedRulesAdminProtectionRuleSet
          vendor_name: AWS
      visibility_config:
        cloud_watch_metrics_enabled: true
        metric_name: admin_protect
        sampled_requests_enabled: true
visibility_config:
  description: Visibility config of the web acl
  returned: Always, as long as the web acl exists
  type: dict
  sample:
    cloud_watch_metrics_enabled: true
    metric_name: blub
    sampled_requests_enabled: false
"""
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_web_acls, compare_priority_rules, wafv2_snake_dict_to_camel_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


class WebACL:
    def __init__(self, wafv2, name, scope, fail_json_aws):
        self.wafv2 = wafv2
        self.name = name
        self.scope = scope
        self.fail_json_aws = fail_json_aws
        self.existing_acl, self.id, self.locktoken = self.get_web_acl()

    def update(self, default_action, description, rules, sampled_requests, cloudwatch_metrics, metric_name):
        try:
            response = self.wafv2.update_web_acl(
                Name=self.name,
                Scope=self.scope,
                Id=self.id,
                DefaultAction=default_action,
                Description=description,
                Rules=rules,
                VisibilityConfig={
                    'SampledRequestsEnabled': sampled_requests,
                    'CloudWatchMetricsEnabled': cloudwatch_metrics,
                    'MetricName': metric_name
                },
                LockToken=self.locktoken
            )
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to update wafv2 web acl.")
        return response

    def remove(self):
        try:
            response = self.wafv2.delete_web_acl(
                Name=self.name,
                Scope=self.scope,
                Id=self.id,
                LockToken=self.locktoken
            )
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to remove wafv2 web acl.")
        return response

    def get(self):
        if self.existing_acl:
            return self.existing_acl
        return None

    def get_web_acl(self):
        id = None
        locktoken = None
        arn = None
        existing_acl = None
        response = self.list()

        for item in response.get('WebACLs'):
            if item.get('Name') == self.name:
                id = item.get('Id')
                locktoken = item.get('LockToken')
                arn = item.get('ARN')

        if id:
            try:
                existing_acl = self.wafv2.get_web_acl(
                    Name=self.name,
                    Scope=self.scope,
                    Id=id
                )
            except (BotoCoreError, ClientError) as e:
                self.fail_json_aws(e, msg="Failed to get wafv2 web acl.")
        return existing_acl, id, locktoken

    def list(self):
        return wafv2_list_web_acls(self.wafv2, self.scope, self.fail_json_aws)

    def create(self, default_action, rules, sampled_requests, cloudwatch_metrics, metric_name, tags, description):
        req_obj = {
            'Name': self.name,
            'Scope': self.scope,
            'DefaultAction': default_action,
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
            response = self.wafv2.create_web_acl(**req_obj)
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to create wafv2 web acl.")

        self.existing_acl, self.id, self.locktoken = self.get_web_acl()
        return self.existing_acl


def main():

    arg_spec = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        name=dict(type='str', required=True),
        scope=dict(type='str', required=True, choices=['CLOUDFRONT', 'REGIONAL']),
        description=dict(type='str'),
        default_action=dict(type='str', choices=['Block', 'Allow']),
        rules=dict(type='list', elements='dict'),
        sampled_requests=dict(type='bool', default=False),
        cloudwatch_metrics=dict(type='bool', default=True),
        metric_name=dict(type='str'),
        tags=dict(type='dict'),
        purge_rules=dict(default=True, type='bool')
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['default_action', 'rules']]]
    )

    state = module.params.get("state")
    name = module.params.get("name")
    scope = module.params.get("scope")
    description = module.params.get("description")
    default_action = module.params.get("default_action")
    rules = module.params.get("rules")
    sampled_requests = module.params.get("sampled_requests")
    cloudwatch_metrics = module.params.get("cloudwatch_metrics")
    metric_name = module.params.get("metric_name")
    tags = module.params.get("tags")
    purge_rules = module.params.get("purge_rules")
    check_mode = module.check_mode

    if default_action == 'Block':
        default_action = {'Block': {}}
    elif default_action == 'Allow':
        default_action = {'Allow': {}}

    if rules:
        rules = []
        for rule in module.params.get("rules"):
            rules.append(wafv2_snake_dict_to_camel_dict(snake_dict_to_camel_dict(rule, capitalize_first=True)))

    if not metric_name:
        metric_name = name

    web_acl = WebACL(module.client('wafv2'), name, scope, module.fail_json_aws)
    change = False
    retval = {}

    if state == 'present':
        if web_acl.get():
            change, rules = compare_priority_rules(web_acl.get().get('WebACL').get('Rules'), rules, purge_rules, state)
            change = change or web_acl.get().get('WebACL').get('Description') != description
            change = change or web_acl.get().get('WebACL').get('DefaultAction') != default_action

            if change and not check_mode:
                retval = web_acl.update(
                    default_action,
                    description,
                    rules,
                    sampled_requests,
                    cloudwatch_metrics,
                    metric_name
                )

            else:
                retval = web_acl.get().get('WebACL')

        else:
            change = True
            if not check_mode:
                retval = web_acl.create(
                    default_action,
                    rules,
                    sampled_requests,
                    cloudwatch_metrics,
                    metric_name,
                    tags,
                    description
                )

    elif state == 'absent':
        if web_acl.get():
            if rules:
                if len(rules) > 0:
                    change, rules = compare_priority_rules(web_acl.get().get('WebACL').get('Rules'), rules, purge_rules, state)
                    if change and not check_mode:
                        retval = web_acl.update(
                            default_action,
                            description,
                            rules,
                            sampled_requests,
                            cloudwatch_metrics,
                            metric_name
                        )
            else:
                change = True
                if not check_mode:
                    retval = web_acl.remove()

    module.exit_json(changed=change, **camel_dict_to_snake_dict(retval))


if __name__ == '__main__':
    main()

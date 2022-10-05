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
short_description: Create and delete WAF Web ACLs
description:
  - Create, modify or delete AWS WAF v2 web ACLs (not for classic WAF).
  - See docs at U(https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)
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
        - Geographical scope of the web acl.
      required: true
      choices: ["CLOUDFRONT", "REGIONAL"]
      type: str
    description:
      description:
        - Description of wafv2 web acl.
      type: str
    default_action:
      description:
        - Default action of the wafv2 web acl.
      choices: ["Block", "Allow"]
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
    rules:
      description:
        - The Rule statements used to identify the web requests that you want to allow, block, or count.
        - For a list of managed rules see U(https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html).
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
    custom_response_bodies:
      description:
        - A map of custom response keys and content bodies. Define response bodies here and reference them in the rules by providing
        - the key of the body dictionary element.
        - Each element must have a unique dict key and in the dict two keys for I(content_type) and I(content).
        - Requires botocore >= 1.20.40
      type: dict
      version_added: 3.1.0
    purge_rules:
      description:
        - When set to C(no), keep the existing load balancer rules in place. Will modify and add, but will not delete.
      default: true
      type: bool

notes:
  - Support for the I(purge_tags) parameter was added in release 4.0.0.

extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
  - amazon.aws.boto3

'''

EXAMPLES = '''
- name: Create test web acl
  community.aws.wafv2_web_acl:
    name: test05
    description: hallo eins
    scope: REGIONAL
    default_action: Allow
    sampled_requests: false
    cloudwatch_metrics: true
    metric_name: test05-acl-metric
    rules:
      - name: zwei
        priority: 0
        action:
          block: {}
        visibility_config:
          sampled_requests_enabled: true
          cloud_watch_metrics_enabled: true
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
          sampled_requests_enabled: true
          cloud_watch_metrics_enabled: true
          metric_name: fsd
        statement:
          managed_rule_group_statement:
            vendor_name: AWS
            name: AWSManagedRulesAdminProtectionRuleSet

      # AWS Managed Bad Input Rule Set
      # but allow PROPFIND_METHOD used e.g. by webdav
      - name: bad_input_protect_whitelist_webdav
        priority: 2
        override_action:
          none: {}
        visibility_config:
          sampled_requests_enabled: true
          cloud_watch_metrics_enabled: true
          metric_name: bad_input_protect
        statement:
          managed_rule_group_statement:
            vendor_name: AWS
            name: AWSManagedRulesKnownBadInputsRuleSet
            excluded_rules:
              - name: PROPFIND_METHOD

      # Rate Limit example. 1500 req/5min
      # counted for two domains via or_statement. login.mydomain.tld and api.mydomain.tld
      - name: rate_limit_example
        priority: 3
        action:
          block: {}
        visibility_config:
          sampled_requests_enabled: true
          cloud_watch_metrics_enabled: true
          metric_name: mydomain-ratelimit
        statement:
          rate_based_statement:
            limit: 1500
            aggregate_key_type: IP
            scope_down_statement:
              or_statement:
                statements:
                  - byte_match_statement:
                      search_string: login.mydomain.tld
                      positional_constraint: CONTAINS
                      field_to_match:
                        single_header:
                          name: host
                      text_transformations:
                        - type: LOWERCASE
                          priority: 0
                  - byte_match_dtatement:
                      search_string: api.mydomain.tld
                      positional_constraint: CONTAINS
                      field_to_match:
                        single_header:
                          name: host
                      text_transformations:
                        - type: LOWERCASE
                          priority: 0
    purge_rules: true
    tags:
      A: B
      C: D
    state: present

- name: Create IP filtering web ACL
  community.aws.wafv2_web_acl:
    name: ip-filtering-traffic
    description: ACL that filters web traffic based on rate limits and whitelists some IPs
    scope: REGIONAL
    default_action: Allow
    sampled_requests: true
    cloudwatch_metrics: true
    metric_name: ip-filtering-traffic
    rules:
      - name: whitelist-own-IPs
        priority: 0
        action:
          allow: {}
        statement:
          ip_set_reference_statement:
            arn: 'arn:aws:wafv2:us-east-1:123456789012:regional/ipset/own-public-ips/1c4bdfc4-0f77-3b23-5222-123123123'
        visibility_config:
          sampled_requests_enabled: true
          cloud_watch_metrics_enabled: true
          metric_name: waf-acl-rule-whitelist-own-IPs
      - name: rate-limit-per-IP
        priority: 1
        action:
          block:
            custom_response:
              response_code: 429
              custom_response_body_key: too_many_requests
        statement:
          rate_based_statement:
            limit: 5000
            aggregate_key_type: IP
        visibility_config:
          sampled_requests_enabled: true
          cloud_watch_metrics_enabled: true
          metric_name: waf-acl-rule-rate-limit-per-IP
        purge_rules: true
    custom_response_bodies:
      too_many_requests:
        content_type: APPLICATION_JSON
        content: '{ message: "Your request has been blocked due to too many HTTP requests coming from your IP" }'
    region: us-east-1
    state: present

'''

RETURN = """
arn:
  description: web acl arn
  sample: arn:aws:wafv2:eu-central-1:123456789012:regional/webacl/test05/318c1ab9-fa74-4b3b-a974-f92e25106f61
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
default_action:
  description: Default action of ACL
  returned: Always, as long as the web acl exists
  sample:
    allow: {}
  type: dict
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
custom_response_bodies:
  description: Custom response body configurations to be used in rules
  type: dict
  sample:
    too_many_requests:
      content_type: APPLICATION_JSON
      content: '{ message: "Your request has been blocked due to too many HTTP requests coming from your IP" }'
  returned: Always, as long as the web acl exists
visibility_config:
  description: Visibility config of the web acl
  returned: Always, as long as the web acl exists
  type: dict
  sample:
    cloud_watch_metrics_enabled: true
    metric_name: blub
    sampled_requests_enabled: false
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
from ansible_collections.community.aws.plugins.module_utils.wafv2 import describe_wafv2_tags
from ansible_collections.community.aws.plugins.module_utils.wafv2 import ensure_wafv2_tags
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_web_acls
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_snake_dict_to_camel_dict


class WebACL:
    def __init__(self, wafv2, name, scope, fail_json_aws):
        self.wafv2 = wafv2
        self.name = name
        self.scope = scope
        self.fail_json_aws = fail_json_aws
        self.existing_acl, self.id, self.locktoken = self.get_web_acl()

    def update(self, default_action, description, rules, sampled_requests, cloudwatch_metrics, metric_name, custom_response_bodies):
        req_obj = {
            'Name': self.name,
            'Scope': self.scope,
            'Id': self.id,
            'DefaultAction': default_action,
            'Rules': rules,
            'VisibilityConfig': {
                'SampledRequestsEnabled': sampled_requests,
                'CloudWatchMetricsEnabled': cloudwatch_metrics,
                'MetricName': metric_name
            },
            'LockToken': self.locktoken
        }

        if description:
            req_obj['Description'] = description

        if custom_response_bodies:
            req_obj['CustomResponseBodies'] = custom_response_bodies

        try:
            response = self.wafv2.update_web_acl(**req_obj)
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to update wafv2 web acl.")

        self.existing_acl, self.id, self.locktoken = self.get_web_acl()
        return self.existing_acl

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
            tags = describe_wafv2_tags(self.wafv2, arn, self.fail_json_aws)
            existing_acl['tags'] = tags
        return existing_acl, id, locktoken

    def list(self):
        return wafv2_list_web_acls(self.wafv2, self.scope, self.fail_json_aws)

    def create(self, default_action, rules, sampled_requests, cloudwatch_metrics, metric_name, tags, description, custom_response_bodies):
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

        if custom_response_bodies:
            req_obj['CustomResponseBodies'] = custom_response_bodies
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


def format_result(result):

    # We were returning details of the Web ACL inside a "web_acl"  parameter on
    # creation, keep returning it to avoid breaking existing playbooks, but also
    # return what the docs said we return (and returned when no change happened)
    retval = dict(result)
    if "WebACL" in retval:
        retval.update(retval["WebACL"])

    return camel_dict_to_snake_dict(retval, ignore_list=['tags'])


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
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
        custom_response_bodies=dict(type='dict'),
        purge_rules=dict(default=True, type='bool'),
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
    purge_tags = module.params.get("purge_tags")
    purge_rules = module.params.get("purge_rules")
    check_mode = module.check_mode

    custom_response_bodies = module.params.get("custom_response_bodies")
    if custom_response_bodies:
        module.require_botocore_at_least('1.20.40', reason='to set custom response bodies')
        custom_response_bodies = {}

        for custom_name, body in module.params.get("custom_response_bodies").items():
            custom_response_bodies[custom_name] = snake_dict_to_camel_dict(body, capitalize_first=True)

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

    wafv2 = module.client('wafv2')
    web_acl = WebACL(wafv2, name, scope, module.fail_json_aws)
    change = False
    retval = {}

    if state == 'present':
        if web_acl.get():
            tags_changed = ensure_wafv2_tags(wafv2, web_acl.get().get('WebACL').get('ARN'), tags, purge_tags, module.fail_json_aws, module.check_mode)
            change, rules = compare_priority_rules(web_acl.get().get('WebACL').get('Rules'), rules, purge_rules, state)
            change = change or (description and web_acl.get().get('WebACL').get('Description') != description)
            change = change or (default_action and web_acl.get().get('WebACL').get('DefaultAction') != default_action)

            if change and not check_mode:
                retval = web_acl.update(
                    default_action,
                    description,
                    rules,
                    sampled_requests,
                    cloudwatch_metrics,
                    metric_name,
                    custom_response_bodies
                )
            elif tags_changed:
                retval, id, locktoken = web_acl.get_web_acl()
            else:
                retval = web_acl.get()

            change |= tags_changed

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
                    description,
                    custom_response_bodies
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
                            metric_name,
                            custom_response_bodies
                        )
            else:
                change = True
                if not check_mode:
                    retval = web_acl.remove()

    module.exit_json(changed=change, **format_result(retval))


if __name__ == '__main__':
    main()

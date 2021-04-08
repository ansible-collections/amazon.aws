#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_rule_group_info
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_web_acl_info
description:
  - Get informations about existing wafv2 rule groups.
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
        - The name of the rule group.
      required: true
      type: str
    scope:
      description:
        - Scope of wafv2 rule group.
      required: true
      choices: ["CLOUDFRONT","REGIONAL"]
      type: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: rule group info
  community.aws.wafv2_rule_group_info:
    name: test02
    state: present
    scope: REGIONAL
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
                  arn: arn:aws:wafv2:eu-central-1:111111111:regional/ipset/test02/b6978915-c67b-4d1c-8832-2b1bb452143a
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
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_rule_groups

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_rule_group(wafv2, name, scope, id, fail_json_aws):
    try:
        response = wafv2.get_rule_group(
            Name=name,
            Scope=scope,
            Id=id
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to get wafv2 rule group.")
    return response


def main():
    arg_spec = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        name=dict(type='str', required=True),
        scope=dict(type='str', required=True, choices=['CLOUDFRONT', 'REGIONAL'])
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    state = module.params.get("state")
    name = module.params.get("name")
    scope = module.params.get("scope")

    wafv2 = module.client('wafv2')

    # check if rule group exists
    response = wafv2_list_rule_groups(wafv2, scope, module.fail_json_aws)
    id = None
    retval = {}

    for item in response.get('RuleGroups'):
        if item.get('Name') == name:
            id = item.get('Id')

    existing_group = None
    if id:
        existing_group = get_rule_group(wafv2, name, scope, id, module.fail_json_aws)
        retval = camel_dict_to_snake_dict(existing_group.get('RuleGroup'))

    module.exit_json(**retval)


if __name__ == '__main__':
    main()

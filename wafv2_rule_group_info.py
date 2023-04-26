#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: wafv2_rule_group_info
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_web_acl_info
description:
  - Get informations about existing wafv2 rule groups.
options:
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
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: rule group info
  community.aws.wafv2_rule_group_info:
    name: test02
    scope: REGIONAL
"""

RETURN = r"""
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

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule
from ansible_collections.community.aws.plugins.module_utils.wafv2 import describe_wafv2_tags
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_rule_groups


def get_rule_group(wafv2, name, scope, id, fail_json_aws):
    try:
        response = wafv2.get_rule_group(Name=name, Scope=scope, Id=id)
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to get wafv2 rule group.")
    return response


def main():
    arg_spec = dict(
        name=dict(type="str", required=True),
        scope=dict(type="str", required=True, choices=["CLOUDFRONT", "REGIONAL"]),
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
    )

    name = module.params.get("name")
    scope = module.params.get("scope")

    wafv2 = module.client("wafv2")

    # check if rule group exists
    response = wafv2_list_rule_groups(wafv2, scope, module.fail_json_aws)
    id = None
    retval = {}

    for item in response.get("RuleGroups"):
        if item.get("Name") == name:
            id = item.get("Id")
            arn = item.get("ARN")

    existing_group = None
    if id:
        existing_group = get_rule_group(wafv2, name, scope, id, module.fail_json_aws)
        retval = camel_dict_to_snake_dict(existing_group.get("RuleGroup"))
        tags = describe_wafv2_tags(wafv2, arn, module.fail_json_aws)
        retval["tags"] = tags or {}

    module.exit_json(**retval)


if __name__ == "__main__":
    main()

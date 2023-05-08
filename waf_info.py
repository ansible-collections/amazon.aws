#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: waf_info
short_description: Retrieve information for WAF ACLs, Rules, Conditions and Filters
version_added: 1.0.0
description:
  - Retrieve information for WAF ACLs, Rules, Conditions and Filters.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_waf_info).
    The usage did not change.
options:
  name:
    description:
      - The name of a Web Application Firewall.
    type: str
  waf_regional:
    description: Whether to use the C(waf-regional) module.
    default: false
    required: false
    type: bool

author:
  - Mike Mochan (@mmochan)
  - Will Thames (@willthames)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: obtain all WAF information
  community.aws.waf_info:

- name: obtain all information for a single WAF
  community.aws.waf_info:
    name: test_waf

- name: obtain all information for a single WAF Regional
  community.aws.waf_info:
    name: test_waf
    waf_regional: true
"""

RETURN = r"""
wafs:
  description: The WAFs that match the passed arguments.
  returned: success
  type: complex
  contains:
    name:
      description: A friendly name or description of the WebACL.
      returned: always
      type: str
      sample: test_waf
    default_action:
      description: The action to perform if none of the Rules contained in the WebACL match.
      returned: always
      type: int
      sample: BLOCK
    metric_name:
      description: A friendly name or description for the metrics for this WebACL.
      returned: always
      type: str
      sample: test_waf_metric
    rules:
      description: An array that contains the action for each Rule in a WebACL , the priority of the Rule.
      returned: always
      type: complex
      contains:
        action:
          description: The action to perform if the Rule matches.
          returned: always
          type: str
          sample: BLOCK
        metric_name:
          description: A friendly name or description for the metrics for this Rule.
          returned: always
          type: str
          sample: ipblockrule
        name:
          description: A friendly name or description of the Rule.
          returned: always
          type: str
          sample: ip_block_rule
        predicates:
          description: The Predicates list contains a Predicate for each
            ByteMatchSet, IPSet, SizeConstraintSet, SqlInjectionMatchSet or XssMatchSet
            object in a Rule.
          returned: always
          type: list
          sample:
            [
              {
                "byte_match_set_id": "47b822b5-abcd-1234-faaf-1234567890",
                "byte_match_tuples": [
                  {
                    "field_to_match": {
                      "type": "QUERY_STRING"
                    },
                    "positional_constraint": "STARTS_WITH",
                    "target_string": "bobbins",
                    "text_transformation": "NONE"
                  }
                ],
                "name": "bobbins",
                "negated": false,
                "type": "ByteMatch"
              }
            ]
"""

from ansible_collections.amazon.aws.plugins.module_utils.waf import get_web_acl
from ansible_collections.amazon.aws.plugins.module_utils.waf import list_web_acls

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def main():
    argument_spec = dict(
        name=dict(required=False),
        waf_regional=dict(type="bool", default=False),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    resource = "waf" if not module.params["waf_regional"] else "waf-regional"
    client = module.client(resource)
    web_acls = list_web_acls(client, module)
    name = module.params["name"]
    if name:
        web_acls = [web_acl for web_acl in web_acls if web_acl["Name"] == name]
        if not web_acls:
            module.fail_json(msg=f"WAF named {name} not found")
    module.exit_json(wafs=[get_web_acl(client, module, web_acl["WebACLId"]) for web_acl in web_acls])


if __name__ == "__main__":
    main()

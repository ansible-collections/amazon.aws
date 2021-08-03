#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_resources_info
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_resources_info
description:
  - List web acl resources.
options:
    name:
      description:
        - The name wafv2 acl of interest.
      type: str
      required: true
    scope:
      description:
        - Scope of wafv2 web acl.
      required: true
      choices: ["CLOUDFRONT","REGIONAL"]
      type: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: get web acl
  community.aws.wafv2_resources_info:
    name: string03
    scope: REGIONAL
'''

RETURN = """
resource_arns:
  description: Current resources where the wafv2 is applied on
  sample:
    - "arn:aws:elasticloadbalancing:eu-central-1:111111111:loadbalancer/app/test03/dd83ea041ba6f933"
  returned: Always, as long as the wafv2 exists
  type: list
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_web_acls


def get_web_acl(wafv2, name, scope, id, fail_json_aws):
    try:
        response = wafv2.get_web_acl(
            Name=name,
            Scope=scope,
            Id=id
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to get wafv2 web acl.")
    return response


def list_web_acls(wafv2, scope, fail_json_aws):
    return wafv2_list_web_acls(wafv2, scope, fail_json_aws)


def list_wafv2_resources(wafv2, arn, fail_json_aws):
    try:
        response = wafv2.list_resources_for_web_acl(
            WebACLArn=arn
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to list wafv2 resources.")
    return response


def main():

    arg_spec = dict(
        name=dict(type='str', required=True),
        scope=dict(type='str', required=True, choices=['CLOUDFRONT', 'REGIONAL'])
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
    )

    name = module.params.get("name")
    scope = module.params.get("scope")

    wafv2 = module.client('wafv2')
    # check if web acl exists
    response = list_web_acls(wafv2, scope, module.fail_json_aws)

    id = None
    retval = {}

    for item in response.get('WebACLs'):
        if item.get('Name') == name:
            id = item.get('Id')

    if id:
        existing_acl = get_web_acl(wafv2, name, scope, id, module.fail_json_aws)
        arn = existing_acl.get('WebACL').get('ARN')

        retval = camel_dict_to_snake_dict(list_wafv2_resources(wafv2, arn, module.fail_json_aws))

    module.exit_json(**retval)


if __name__ == '__main__':
    main()

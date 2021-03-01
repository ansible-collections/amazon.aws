#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_web_acl_info
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_web_acl
description:
  - Info about web acl
requirements:
  - boto3
  - botocore
options:
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

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: get web acl
  community.aws.wafv2_web_acl_info:
    name: test05
    scope: REGIONAL
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
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_web_acls

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_web_acl(wafv2, name, scope, id):
    response = wafv2.get_web_acl(
        Name=name,
        Scope=scope,
        Id=id
    )
    return response


def main():

    arg_spec = dict(
        name=dict(type='str', required=True),
        scope=dict(type='str', required=True, choices=['CLOUDFRONT', 'REGIONAL'])
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec
    )

    state = module.params.get("state")
    name = module.params.get("name")
    scope = module.params.get("scope")

    wafv2 = module.client('wafv2')
    # check if web acl exists
    response = wafv2_list_web_acls(wafv2, scope)

    id = None
    retval = {}

    for item in response.get('WebACLs'):
        if item.get('Name') == name:
            id = item.get('Id')

    if id:
        existing_acl = get_web_acl(wafv2, name, scope, id)
        retval = camel_dict_to_snake_dict(existing_acl.get('WebACL'))

    module.exit_json(**retval)


if __name__ == '__main__':
    main()

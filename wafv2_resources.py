#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_resources
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_web_acl
description:
  - Apply or remove wafv2 to other aws resources.
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
      type: str
    scope:
      description:
        - Scope of waf
      choices: ["CLOUDFRONT","REGIONAL"]
      type: str
    arn:
      description:
        - AWS resources (ALB, API Gateway or AppSync GraphQL API) ARN
      type: str
      required: true

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: add test alb to waf string03
  community.aws.wafv2_resources:
    name: string03
    scope: REGIONAL
    state: present
    arn: "arn:aws:elasticloadbalancing:eu-central-1:111111111:loadbalancer/app/test03/dd83ea041ba6f933"
'''

RETURN = """
resource_arns:
  description: Current resources where the wafv2 is applied on
  sample:
    - "arn:aws:elasticloadbalancing:eu-central-1:111111111:loadbalancer/app/test03/dd83ea041ba6f933"
  returned: Always, as long as the wafv2 exists
  type: list
"""
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list
from ansible_collections.community.aws.plugins.module_utils.wafv2 import wafv2_list_web_acls

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


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


def list_wafv2_resources(wafv2, arn, fail_json_aws):
    try:
        response = wafv2.list_resources_for_web_acl(
            WebACLArn=arn
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to list wafv2 web acl.")
    return response


def add_wafv2_resources(wafv2, waf_arn, arn, fail_json_aws):
    try:
        response = wafv2.associate_web_acl(
            WebACLArn=waf_arn,
            ResourceArn=arn
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to add wafv2 web acl.")
    return response


def remove_resources(wafv2, arn, fail_json_aws):
    try:
        response = wafv2.disassociate_web_acl(
            ResourceArn=arn
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to remove wafv2 web acl.")
    return response


def main():

    arg_spec = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        name=dict(type='str'),
        scope=dict(type='str', choices=['CLOUDFRONT', 'REGIONAL']),
        arn=dict(type='str', required=True)
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['name', 'scope']]]
    )

    state = module.params.get("state")
    name = module.params.get("name")
    scope = module.params.get("scope")
    arn = module.params.get("arn")
    check_mode = module.check_mode

    wafv2 = module.client('wafv2')

    # check if web acl exists

    response = wafv2_list_web_acls(wafv2, scope, module.fail_json_aws)

    id = None
    retval = {}
    change = False

    for item in response.get('WebACLs'):
        if item.get('Name') == name:
            id = item.get('Id')

    if id:
        existing_acl = get_web_acl(wafv2, name, scope, id, module.fail_json_aws)
        waf_arn = existing_acl.get('WebACL').get('ARN')

        retval = list_wafv2_resources(wafv2, waf_arn, module.fail_json_aws)

    if state == 'present':
        if retval:
            if arn not in retval.get('ResourceArns'):
                change = True
                if not check_mode:
                    retval = add_wafv2_resources(wafv2, waf_arn, arn, module.fail_json_aws)

    elif state == 'absent':
        if retval:
            if arn in retval.get('ResourceArns'):
                change = True
                if not check_mode:
                    retval = remove_resources(wafv2, arn, module.fail_json_aws)

    module.exit_json(changed=change, **camel_dict_to_snake_dict(retval))


if __name__ == '__main__':
    main()

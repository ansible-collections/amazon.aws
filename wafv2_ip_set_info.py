#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_ip_set_info
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: Get information about wafv2 ip sets
description:
  - Get information about existing wafv2 ip sets.
options:
    name:
      description:
        - The name of the IP set.
      required: true
      type: str
    scope:
      description:
        - Specifies whether this is for an AWS CloudFront distribution or for a regional application.
      choices: ["CLOUDFRONT","REGIONAL"]
      required: true
      type: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = '''
- name: test ip set
  wafv2_ip_set_info:
    name: test02
    scope: REGIONAL
'''

RETURN = """
addresses:
  description: Current addresses of the ip set
  sample:
    - 8.8.8.8/32
    - 8.8.4.4/32
  returned: Always, as long as the ip set exists
  type: list
arn:
  description: IP set arn
  sample: "arn:aws:wafv2:eu-central-1:11111111:regional/ipset/test02/4b007330-2934-4dc5-af24-82dcb3aeb127"
  type: str
  returned: Always, as long as the ip set exists
description:
  description: Description of the ip set
  sample: Some IP set description
  returned: Always, as long as the ip set exists
  type: str
ip_address_version:
  description: IP version of the ip set
  sample: IPV4
  type: str
  returned: Always, as long as the ip set exists
name:
  description: IP set name
  sample: test02
  returned: Always, as long as the ip set exists
  type: str
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.community.aws.plugins.module_utils.wafv2 import describe_wafv2_tags


def list_ip_sets(wafv2, scope, fail_json_aws, Nextmarker=None):
    # there is currently no paginator for wafv2
    req_obj = {
        'Scope': scope,
        'Limit': 100
    }
    if Nextmarker:
        req_obj['NextMarker'] = Nextmarker

    try:
        response = wafv2.list_ip_sets(**req_obj)
        if response.get('NextMarker'):
            response['IPSets'] += list_ip_sets(wafv2, scope, fail_json_aws, Nextmarker=response.get('NextMarker')).get('IPSets')
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to list wafv2 ip set")
    return response


def get_ip_set(wafv2, name, scope, id, fail_json_aws):
    try:
        response = wafv2.get_ip_set(
            Name=name,
            Scope=scope,
            Id=id
        )
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to get wafv2 ip set")
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

    # check if ip set exist
    response = list_ip_sets(wafv2, scope, module.fail_json_aws)

    id = None

    for item in response.get('IPSets'):
        if item.get('Name') == name:
            id = item.get('Id')
            arn = item.get('ARN')

    retval = {}
    existing_set = None
    if id:
        existing_set = get_ip_set(wafv2, name, scope, id, module.fail_json_aws)
        retval = camel_dict_to_snake_dict(existing_set.get('IPSet'))
        retval['tags'] = describe_wafv2_tags(wafv2, arn, module.fail_json_aws) or {}
    module.exit_json(**retval)


if __name__ == '__main__':
    main()

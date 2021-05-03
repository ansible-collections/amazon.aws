#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_tag_info
version_added: 1.0.0
short_description: list tags on ec2 resources
description:
    - Lists tags for any EC2 resource.
    - Resources are referenced by their resource id (e.g. an instance being i-XXXXXXX, a vpc being vpc-XXXXXX).
    - Resource tags can be managed using the M(amazon.aws.ec2_tag) module.
requirements: [ "boto3", "botocore" ]
options:
  resource:
    description:
      - The EC2 resource id (for example i-XXXXXX or vpc-XXXXXX).
    required: true
    type: str

author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: Retrieve all tags on an instance
  amazon.aws.ec2_tag_info:
    region: eu-west-1
    resource: i-xxxxxxxxxxxxxxxxx
  register: instance_tags

- name: Retrieve all tags on a VPC
  amazon.aws.ec2_tag_info:
    region: eu-west-1
    resource: vpc-xxxxxxxxxxxxxxxxx
  register: vpc_tags
'''

RETURN = '''
tags:
  description: A dict containing the tags on the resource
  returned: always
  type: dict
'''

try:
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    pass    # Handled by AnsibleAWSModule

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import describe_ec2_tags


def main():
    argument_spec = dict(
        resource=dict(required=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    resource = module.params['resource']
    ec2 = module.client('ec2')

    current_tags = describe_ec2_tags(ec2, module, resource)

    module.exit_json(changed=False, tags=current_tags)


if __name__ == '__main__':
    main()

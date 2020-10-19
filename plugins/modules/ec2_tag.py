#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_tag
version_added: 1.0.0
short_description: create and remove tags on ec2 resources
description:
    - Creates, modifies and removes tags for any EC2 resource.
    - Resources are referenced by their resource id (for example, an instance being i-XXXXXXX, a VPC being vpc-XXXXXXX).
    - This module is designed to be used with complex args (tags), see the examples.
requirements: [ "boto3", "botocore" ]
options:
  resource:
    description:
      - The EC2 resource id.
    required: true
    type: str
  state:
    description:
      - Whether the tags should be present or absent on the resource.
      - The use of I(state=list) to interrogate the tags of an instance has been
        deprecated and will be removed after 2022-06-01.  The 'list'
        functionality has been moved to a dedicated module M(amazon.aws.ec2_tag_info).
    default: present
    choices: ['present', 'absent', 'list']
    type: str
  tags:
    description:
      - A dictionary of tags to add or remove from the resource.
      - If the value provided for a key is not set and I(state=absent), the tag will be removed regardless of its current value.
      - Required when I(state=present) or I(state=absent).
    type: dict
  purge_tags:
    description:
      - Whether unspecified tags should be removed from the resource.
      - Note that when combined with I(state=absent), specified tags with non-matching values are not purged.
    type: bool
    default: false

author:
  - Lester Wade (@lwade)
  - Paul Arthur (@flowerysong)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: Ensure tags are present on a resource
  amazon.aws.ec2_tag:
    region: eu-west-1
    resource: vol-XXXXXX
    state: present
    tags:
      Name: ubervol
      env: prod

- name: Ensure all volumes are tagged
  amazon.aws.ec2_tag:
    region:  eu-west-1
    resource: '{{ item.id }}'
    state: present
    tags:
      Name: dbserver
      Env: production
  loop: '{{ ec2_vol.volumes }}'

- name: Remove the Env tag
  amazon.aws.ec2_tag:
    region: eu-west-1
    resource: i-xxxxxxxxxxxxxxxxx
    tags:
      Env:
    state: absent

- name: Remove the Env tag if it's currently 'development'
  amazon.aws.ec2_tag:
    region: eu-west-1
    resource: i-xxxxxxxxxxxxxxxxx
    tags:
      Env: development
    state: absent

- name: Remove all tags except for Name from an instance
  amazon.aws.ec2_tag:
    region: eu-west-1
    resource: i-xxxxxxxxxxxxxxxxx
    tags:
        Name: ''
    state: absent
    purge_tags: true
'''

RETURN = '''
tags:
  description: A dict containing the tags on the resource
  returned: always
  type: dict
added_tags:
  description: A dict of tags that were added to the resource
  returned: If tags were added
  type: dict
removed_tags:
  description: A dict of tags that were removed from the resource
  returned: If tags were removed
  type: dict
'''

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ..module_utils.ec2 import compare_aws_tags


def get_tags(ec2, module, resource):
    filters = [{'Name': 'resource-id', 'Values': [resource]}]
    try:
        result = AWSRetry.jittered_backoff()(ec2.describe_tags)(Filters=filters)
        return boto3_tag_list_to_ansible_dict(result['Tags'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to fetch tags for resource {0}'.format(resource))


def main():
    argument_spec = dict(
        resource=dict(required=True),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent', 'list']),
    )
    required_if = [('state', 'present', ['tags']), ('state', 'absent', ['tags'])]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)

    resource = module.params['resource']
    tags = module.params['tags']
    state = module.params['state']
    purge_tags = module.params['purge_tags']

    result = {'changed': False}

    ec2 = module.client('ec2')

    current_tags = get_tags(ec2, module, resource)

    if state == 'list':
        module.deprecate(
            'Using the "list" state has been deprecated.  Please use the ec2_tag_info module instead', date='2022-06-01', collection_name='amazon.aws')
        module.exit_json(changed=False, tags=current_tags)

    add_tags, remove = compare_aws_tags(current_tags, tags, purge_tags=purge_tags)

    remove_tags = {}
    if state == 'absent':
        for key in tags:
            if key in current_tags and (tags[key] is None or current_tags[key] == tags[key]):
                remove_tags[key] = current_tags[key]

    for key in remove:
        remove_tags[key] = current_tags[key]

    if remove_tags:
        result['changed'] = True
        result['removed_tags'] = remove_tags
        if not module.check_mode:
            try:
                AWSRetry.jittered_backoff()(ec2.delete_tags)(Resources=[resource], Tags=ansible_dict_to_boto3_tag_list(remove_tags))
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg='Failed to remove tags {0} from resource {1}'.format(remove_tags, resource))

    if state == 'present' and add_tags:
        result['changed'] = True
        result['added_tags'] = add_tags
        current_tags.update(add_tags)
        if not module.check_mode:
            try:
                AWSRetry.jittered_backoff()(ec2.create_tags)(Resources=[resource], Tags=ansible_dict_to_boto3_tag_list(add_tags))
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg='Failed to set tags {0} on resource {1}'.format(add_tags, resource))

    result['tags'] = get_tags(ec2, module, resource)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_ami_copy
version_added: 1.0.0
short_description: copies AMI between AWS regions, return new image id
description:
  - Copies AMI from a source region to a destination region. B(Since version 2.3 this module depends on boto3.)
options:
  source_region:
    description:
      - The source region the AMI should be copied from.
    required: true
    type: str
  source_image_id:
    description:
      - The ID of the AMI in source region that should be copied.
    required: true
    type: str
  name:
    description:
      - The name of the new AMI to copy. (As of 2.3 the default is C(default), in prior versions it was C(null).)
    default: "default"
    type: str
  description:
    description:
      - An optional human-readable string describing the contents and purpose of the new AMI.
    type: str
  encrypted:
    description:
      - Whether or not the destination snapshots of the copied AMI should be encrypted.
    type: bool
    default: false
  kms_key_id:
    description:
      - KMS key id used to encrypt the image. If not specified, uses default EBS Customer Master Key (CMK) for your account.
    type: str
  wait:
    description:
      - Wait for the copied AMI to be in state C(available) before returning.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
      - Prior to 2.3 the default was C(1200).
      - From 2.3-2.5 this option was deprecated in favor of boto3 waiter defaults.
      - This was reenabled in 2.6 to allow timeouts greater than 10 minutes.
    default: 600
    type: int
  tags:
    description:
      - 'A hash/dictionary of tags to add to the new copied AMI: C({"key":"value"}) and C({"key":"value","key":"value"})'
    type: dict
    aliases: ['resource_tags']
  tag_equality:
    description:
      - Whether to use tags if the source AMI already exists in the target region. If this is set, and all tags match
        in an existing AMI, the AMI will not be copied again.
    default: false
    type: bool
author:
  - Amir Moulavi (@amir343) <amir.moulavi@gmail.com>
  - Tim C (@defunctio) <defunct@defunct.io>
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = '''
- name: Basic AMI Copy
  community.aws.ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx

- name: AMI copy wait until available
  community.aws.ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    wait: true
    wait_timeout: 1200  # Default timeout is 600
  register: image_id

- name: Named AMI copy
  community.aws.ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    name: My-Awesome-AMI
    description: latest patch

- name: Tagged AMI copy (will not copy the same AMI twice)
  community.aws.ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    tags:
        Name: My-Super-AMI
        Patch: 1.2.3
    tag_equality: true

- name: Encrypted AMI copy
  community.aws.ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    encrypted: true

- name: Encrypted AMI copy with specified key
  community.aws.ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    encrypted: true
    kms_key_id: arn:aws:kms:us-east-1:XXXXXXXXXXXX:key/746de6ea-50a4-4bcb-8fbc-e3b29f2d367b
'''

RETURN = '''
image_id:
  description: AMI ID of the copied AMI
  returned: always
  type: str
  sample: ami-e689729e
'''

try:
    from botocore.exceptions import ClientError, WaiterError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list


def copy_image(module, ec2):
    """
    Copies an AMI

    module : AnsibleAWSModule object
    ec2: ec2 connection object
    """

    image = None
    changed = False
    tags = module.params.get('tags')

    params = {'SourceRegion': module.params.get('source_region'),
              'SourceImageId': module.params.get('source_image_id'),
              'Name': module.params.get('name'),
              'Description': module.params.get('description'),
              'Encrypted': module.params.get('encrypted'),
              }
    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')

    try:
        if module.params.get('tag_equality'):
            filters = [{'Name': 'tag:%s' % k, 'Values': [v]} for (k, v) in module.params.get('tags').items()]
            filters.append(dict(Name='state', Values=['available', 'pending']))
            images = ec2.describe_images(Filters=filters)
            if len(images['Images']) > 0:
                image = images['Images'][0]
        if not image:
            image = ec2.copy_image(**params)
            image_id = image['ImageId']
            if tags:
                ec2.create_tags(Resources=[image_id],
                                Tags=ansible_dict_to_boto3_tag_list(tags))
            changed = True

        if module.params.get('wait'):
            delay = 15
            max_attempts = module.params.get('wait_timeout') // delay
            image_id = image.get('ImageId')
            ec2.get_waiter('image_available').wait(
                ImageIds=[image_id],
                WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts}
            )

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(image))
    except WaiterError as e:
        module.fail_json_aws(e, msg='An error occurred waiting for the image to become available')
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Could not copy AMI")
    except Exception as e:
        module.fail_json(msg='Unhandled exception. (%s)' % to_native(e))


def main():
    argument_spec = dict(
        source_region=dict(required=True),
        source_image_id=dict(required=True),
        name=dict(default='default'),
        description=dict(default=''),
        encrypted=dict(type='bool', default=False, required=False),
        kms_key_id=dict(type='str', required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        tags=dict(type='dict', aliases=['resource_tags']),
        tag_equality=dict(type='bool', default=False))

    module = AnsibleAWSModule(argument_spec=argument_spec)
    ec2 = module.client('ec2')
    copy_image(module, ec2)


if __name__ == '__main__':
    main()

#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: s3_object_info
version_added: 5.0.0
short_description: Gather information about objects in s3
description:
  - Describes the objects in s3.
author:
  - Mandar Vijay Kulkarni (@mandar242)
options:
  name:
    description:
      - Name of the S3 bucket containing the object.extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.s3_object
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Get access control list (ACL) of an object.
    amazon.aws.s3_object_info:
      bucket_name: MyTestBucket
      object_key: MyTestObjectKey
      mode: acl

- name: Get all the metadata from an object without returning the object itself.
    amazon.aws.s3_object_info:
      bucket_name: MyTestBucket
      object_key: MyTestObjectKey
      object_attributes:
          - ObjectSize
      mode: attributes

- name: Get current legal hold of an object.
    amazon.aws.s3_object_info:
      bucket_name: MyTestBucket
      object_key: MyTestObjectKey
      mode: legal_hold
'''

RETURN = '''
pass
'''
try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def _describe_s3_object_acl(connection, module, **params):
    try:
        describe_s3_object_acl_response = connection.get_object_acl(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe s3 object')

    return describe_s3_object_acl_response


def describe_s3_object_acl(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_acl_info = _describe_s3_object_acl(connection, module, **params)

    # Remove ResponseMetadata from object_acl_info, convert to snake_case
    del(object_acl_info['ResponseMetadata'])
    object_acl_info = camel_dict_to_snake_dict(object_acl_info)

    module.exit_json(object_acl_info=object_acl_info)


def _describe_s3_object_attributes(connection, module, **params):
    try:
        describe_s3_object_attributes_response = connection.get_object_attributes(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe s3 object')

    return describe_s3_object_attributes_response


def describe_s3_object_attributes(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key
    params['ObjectAttributes'] = module.params.get('object_attributes')

    object_attributes_info = _describe_s3_object_attributes(connection, module, **params)

    # Remove ResponseMetadata from object_attributes_info, convert to snake_case
    del(object_attributes_info['ResponseMetadata'])
    object_attributes_info = camel_dict_to_snake_dict(object_attributes_info)

    module.exit_json(object_attributes_info=object_attributes_info)


def _describe_s3_object_legal_hold(connection, module, **params):
    try:
        describe_s3_object_legal_hold_response = connection.get_object_legal_hold(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe s3 object')
    return describe_s3_object_legal_hold_response


def describe_s3_object_legal_hold(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_legal_hold_info = _describe_s3_object_legal_hold(connection, module, **params)

    # Remove ResponseMetadata from object_legal_hold_info, convert to snake_case
    del(object_legal_hold_info['ResponseMetadata'])
    object_legal_hold_info = camel_dict_to_snake_dict(object_legal_hold_info)

    module.exit_json(object_legal_hold_info=object_legal_hold_info)


def main():

    argument_spec = dict(
        bucket_name=dict(required=True, type='str'),
        object_key=dict(required=True, type='str'),
        mode=dict(required=True, type='str', choices=['acl', 'attributes', 'legal_hold', 'lock_configuration']),
        object_attributes=dict(type='list', choices=['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        connection = module.client('s3', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    bucket_name = module.params.get('bucket_name')
    object_key = module.params.get('object_key')
    mode = module.params.get('mode')

    required_if = [['mode', 'attributes', ['object_attributes']]],

    if mode == 'acl':
        describe_s3_object_acl(connection, module, bucket_name, object_key)
    elif mode == 'attributes':
        describe_s3_object_attributes(connection, module, bucket_name, object_key)
    elif mode == 'legal_hold':
        describe_s3_object_legal_hold(connection, module, bucket_name, object_key)


if __name__ == '__main__':
    main()

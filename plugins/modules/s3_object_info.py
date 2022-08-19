#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

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

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.s3_object
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Retrieve detailed bucket information
  amazon.aws.s3_object_info:
    bucket_name: mandkulk-test-bucket
    object_key: trying.yml
    object_details:
      object_acl: true
      object_tagging: true
      object_legal_hold: true
      object_attributes: true
    object_attributes:
      - ETag
      - ObjectSize
'''

RETURN = '''
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def describe_s3_object_acl(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_acl_info = []

    try:
        object_acl_info = connection.get_object_acl(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_acl_info) != 0:
        # Remove ResponseMetadata from object_acl_info, convert to snake_case
        del(object_acl_info['ResponseMetadata'])
        object_acl_info = camel_dict_to_snake_dict(object_acl_info)

        return object_acl_info

    else:
        return


def describe_s3_object_attributes(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key
    params['ObjectAttributes'] = module.params.get('object_attributes')

    object_attributes_info = []

    try:
        object_attributes_info = connection.get_object_attributes(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_attributes_info) != 0:
        # Remove ResponseMetadata from object_attributes_info, convert to snake_case
        del(object_attributes_info['ResponseMetadata'])
        object_attributes_info = camel_dict_to_snake_dict(object_attributes_info)

        return object_attributes_info

    else:
        return


def describe_s3_object_legal_hold(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_legal_hold_info = []

    try:
        object_legal_hold_info = connection.get_object_legal_hold(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_legal_hold_info) != 0:
        # Remove ResponseMetadata from object_legal_hold_info, convert to snake_case
        del(object_legal_hold_info['ResponseMetadata'])
        object_legal_hold_info = camel_dict_to_snake_dict(object_legal_hold_info)

        return object_legal_hold_info

    else:
        return


def describe_s3_object_lock_configuration(connection, module, bucket_name):
    params = {}
    params['Bucket'] = bucket_name

    object_legal_lock_configuration_info = []

    try:
        object_legal_lock_configuration_info = connection.get_object_lock_configuration(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_legal_lock_configuration_info) != 0:
        # Remove ResponseMetadata from object_legal_lock_configuration_info, convert to snake_case
        del(object_legal_lock_configuration_info['ResponseMetadata'])
        object_legal_lock_configuration_info = camel_dict_to_snake_dict(object_legal_lock_configuration_info)

        return object_legal_lock_configuration_info

    else:
        return


def describe_s3_object_retention(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_retention_info = []

    try:
        object_retention_info = connection.get_object_retention(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_retention_info) != 0:
        # Remove ResponseMetadata from object_retention_info, convert to snake_case
        del(object_retention_info['ResponseMetadata'])
        object_retention_info = camel_dict_to_snake_dict(object_retention_info)

        return object_retention_info

    else:
        return


def describe_s3_object_tagging(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_tagging_info = []

    try:
        object_tagging_info = connection.get_object_tagging(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_tagging_info) != 0:
        # Remove ResponseMetadata from object_tagging_info, convert to snake_case
        del(object_tagging_info['ResponseMetadata'])
        object_tagging_info = boto3_tag_list_to_ansible_dict(object_tagging_info['TagSet'])

        return object_tagging_info

    else:
        return


def get_object_details(connection, module, bucket_name, object_key, requested_facts):

    all_facts = {}

    # Remove non-requested facts
    requested_facts = {fact: value for fact, value in requested_facts.items() if value is True}

    for key in requested_facts:
        if key == 'object_acl':
            all_facts[key] = {}
            try:
                all_facts[key] = describe_s3_object_acl(connection, module, bucket_name, object_key)
            except botocore.exceptions.ClientError:
                pass
        elif key == 'object_attributes':
            all_facts[key] = {}
            try:
                all_facts[key] = describe_s3_object_attributes(connection, module, bucket_name, object_key)
            except botocore.exceptions.ClientError:
                pass
        elif key == 'object_legal_hold':
            all_facts[key] = {}
            try:
                all_facts[key] = describe_s3_object_legal_hold(connection, module, bucket_name, object_key)
            except botocore.exceptions.ClientError:
                pass
        elif key == 'object_lock_configuration':
            all_facts[key] = {}
            try:
                all_facts[key] = describe_s3_object_lock_configuration(connection, module, bucket_name)
            except botocore.exceptions.ClientError:
                pass
        elif key == 'object_retention':
            all_facts[key] = {}
            try:
                all_facts[key] = describe_s3_object_retention(connection, module, bucket_name, object_key)
            except botocore.exceptions.ClientError:
                pass
        elif key == 'object_tagging':
            all_facts[key] = {}
            try:
                all_facts[key] = describe_s3_object_tagging(connection, module, bucket_name, object_key)
            except botocore.exceptions.ClientError:
                pass

    return all_facts


def main():

    argument_spec = dict(
        object_details=dict(type='dict', options=dict(
            object_acl=dict(type='bool', default=False),
            object_attributes=dict(type='bool', default=False),
            object_legal_hold=dict(type='bool', default=False),
            object_lock_configuration=dict(type='bool', default=False),
            object_retention=dict(type='bool', default=False),
            object_tagging=dict(type='bool', default=False),
        )),
        bucket_name=dict(required=True, type='str'),
        object_key=dict(required=False, type='str'),
        object_attributes=dict(type='list', choices=['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        connection = module.client('s3', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    result = {}

    bucket_name = module.params.get('bucket_name')
    object_key = module.params.get('object_key')
    requested_facts = module.params.get("object_details")

    if requested_facts['object_attributes'] is True:
        if not module.params.get('object_attributes'):
            module.fail_json(msg='Please provide object_attributes list to retrieve s3 object_attributes.')

    if requested_facts:
        result['object_info'] = get_object_details(connection, module, bucket_name, object_key, requested_facts)

    module.exit_json(msg="Retrieved s3 object info: ", **result)


if __name__ == '__main__':
    main()

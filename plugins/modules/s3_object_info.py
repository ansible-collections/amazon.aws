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
  bucket_name:
    description:
      - The bucket name that contains the object.
    type: str
    required: true
  object_key:
    description:
      - The key of the object.
    type: str
    required: true
  object_details:
    description:
      - Retrieve requested S3 object detailed information.
    suboptions:
      object_acl
        description: Retrive S3 object acl.
        type: bool
        default: False
      object_attributes:
        description: Retrive S3 object attributes.
        type: bool
        default: False
      object_legal_hold:
        description: Retrive S3 object legal_hold.
        type: bool
        default: False
      object_lock_configuration:
        description: Retrive S3 object lock_configuration.
        type: bool
        default: False
      object_retention:
        description: Retrive S3 object retention.
        type: bool
        default: False
      object_tagging:
        description: Retrive S3 object tagging.
        type: bool
        default: False
  object_attributes:
    description:
      - The fields/details that should be returned.
      - Required when I(object_attributes) is C(true) in I(object_details).
    choices: ['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize']
    type: list
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.s3_object
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Retrieve object metadata without object itself
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    object_key: MyTestObjectKey

- name: Retrieve detailed s3 object information
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    object_key: MyTestObjectKey
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
object_info:
  description: "S3 object details"
  returned: always
  type: complex
  contains:
    object_acl:
      description: Access control list (ACL) of an object.
      returned: when I(object_acl) is set to I(true).
      type: complex
      contains:
        owner:
          description: bucket owner's display name and ID.
          returned: always
          type: complex
          contains:
            id:
              description: bucket owner's ID.
              returned: always
              type: str
              sample: '0xxxxxxxxxbc0f7172xxxxxxxxxaa4xxxxxxxxxa301812fb644xxxxxxxxx'
            display_name:
              description: bucket owner's display name.
              returned: always
              type: str
              sample: 'abcdegfhi'
        grants:
          description: A list of grants.
          returned: always
          type: complex
          contains:
            grantee:
              description: The person being granted permissions.
              returned: always
              type: complex
              contains:
                id:
                  description: The canonical user ID of the grantee.
                  returned: always
                  type: str
                  sample: '0xxxxxxxxxbc0f7172xxxxxxxxxaa4xxxxxxxxxa301812fb644xxxxxxxxx'
                type:
                  description: Type of grantee.
                  returned: always
                  type: str
                  sample: "CanonicalUser"
            permission:
              description: Specifies the permission given to the grantee.
              returned: always
              type: str
              sample: "FULL_CONTROL"
    object_attributes:
      description: Object attributes.
      returned: when I(object_attributes) is set to I(true).
      type: complex
      contains:
        etag:
          description: An ETag is an opaque identifier assigned by a web server to a specific version of a resource found at a URL.
          returned: always
          type: str
          sample: "8fa34xxxxxxxxxxxxxxxxxxxxx35c6f3b"
        last_modified:
          description: The creation date of the object.
          returned: always
          type: datetime
          sample: "2022-08-10T01:11:03+00:00""
        object_size:
          description: The size of the object in bytes.
          returned: alwayS
          type: int
          sample: 819
        checksum:
          description: The checksum or digest of the object.
          returned: always
          type: complex
          contains:
            checksum_crc32:
              description: The base64-encoded, 32-bit CRC32 checksum of the object.
              returned: if it was upload with the object.
              type: str
              sample: "xxxxxxxxxxxx"
            checksum_crc32c:
              description: The base64-encoded, 32-bit CRC32C checksum of the object.
              returned: if it was upload with the object.
              type: str
              sample: "xxxxxxxxxxxx"
            checksum_sha1:
              description: The base64-encoded, 160-bit SHA-1 digest of the object.
              returned: if it was upload with the object.
              type: str
              sample: "xxxxxxxxxxxx"
            checksum_sha256:
              description: The base64-encoded, 256-bit SHA-256 digest of the object.
              returned: if it was upload with the object.
              type: str
              sample: "xxxxxxxxxxxx"
        object_parts:
          description: A collection of parts associated with a multipart upload.
          returned: always
          type: complex
          contains:
            total_parts_count:
              description: The total number of parts.
              returned: always
              type: int
            part_number_marker:
              description: The marker for the current part.
              returned: always
              type: int
            next_part_number_marker:
              description: When a list is truncated, this element specifies the last part in the list, as well as the value to use for the PartNumberMarker request parameter in a subsequent request.
              returned: always
              type: int
            max_parts:
              description: The maximum number of parts allowed in the response.
              returned: always
              type: int
            is_truncated:
              description: Indicates whether the returned list of parts is truncated.
              returned: always
              type: bool
            parts:
              description: A container for elements related to an individual part.
              returned: always
              type: complex
              contains:
                part_number:
                  description: The part number identifying the part. This value is a positive integer between 1 and 10,000.
                  returned: always
                  type: int
                size:
                  description: The size of the uploaded part in bytes.
                  returned: always
                  type: int
                checksum_crc32:
                  description: The base64-encoded, 32-bit CRC32 checksum of the object.
                  returned: if it was upload with the object.
                  type: str
                  sample: "xxxxxxxxxxxx"
                checksum_crc32c:
                  description: The base64-encoded, 32-bit CRC32C checksum of the object.
                  returned: if it was upload with the object.
                  type: str
                  sample: "xxxxxxxxxxxx"
                checksum_sha1:
                  description: The base64-encoded, 160-bit SHA-1 digest of the object.
                  returned: if it was upload with the object.
                  type: str
                  sample: "xxxxxxxxxxxx"
                checksum_sha256:
                  description: The base64-encoded, 256-bit SHA-256 digest of the object.
                  returned: if it was upload with the object.
                  type: str
                  sample: "xxxxxxxxxxxx"
        storage_class:
          description: The storage class information of the object.
          returned: always
          type: str
          sample: "STANDARD"
    object_legal_hold:
      description: Object's current legal hold status
      returned: when I(object_legal_hold) is set to I(true) and required configuration is set on bucket.
      type: complex
      contains:
        legal_hold:
          description: The current legal hold status for the specified object.
          returned: always
          type: complex
          contains:
            status:
              description: Indicates whether the specified object has a legal hold in place.
              returned: always
              type: str
              sample: "ON"
    object_lock_configuration:
      description: Object Lock configuration for a bucket.
      returned: when I(object_lock_configuration) is set to I(true) and required configuration is set on bucket.
      type: complex
      contains:
        object_lock_enabled:
          description: Indicates whether this bucket has an Object Lock configuration enabled.
          returned: always
          type: str
        rule:
          description: Specifies the Object Lock rule for the specified object.
          returned: always
          type: complex
          contains:
            default_retention:
              description: The default Object Lock retention mode and period that you want to apply to new objects placed in the specified bucket.
              returned: always
              type: complex
              contains:
                mode:
                  description: The default Object Lock retention mode you want to apply to new objects placed in the specified bucket. Must be used with either Days or Years.
                  returned: always
                  type: str
                days:
                  description: The number of days that you want to specify for the default retention period.
                  returned: always
                  type: int
                years:
                  description: The number of years that you want to specify for the default retention period.
                  returned: always
                  type: int
    object_retention:
      description: Object's retention settings.
      returned: when I(object_retention) is set to I(true) and required configuration is set on bucket.
      type: complex
      contains:
        retention:
          description: The container element for an object's retention settings.
          returned: always
          type: complex
          contains:
            mode:
              description: Indicates the Retention mode for the specified object.
              returned: always
              type: str
            retain_until_date:
              description: The date on which this Object Lock Retention will expire.
              returned: always
              type: datetime
    object_tagging:
      description: The tag-set of an object
      returned: when I(object_tagging) is set to I(true).
      type: complex
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

    object_acl_info = {}

    try:
        object_acl_info = connection.get_object_acl(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_acl_info['msg'] = 'Object ACL not found, are you sure the bucket/object configuration exist?'

    if len(object_acl_info) != 0 and 'msg' not in object_acl_info.keys():
        # Remove ResponseMetadata from object_acl_info, convert to snake_case
        del(object_acl_info['ResponseMetadata'])
        object_acl_info = camel_dict_to_snake_dict(object_acl_info)

    return object_acl_info


def describe_s3_object_attributes(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key
    params['ObjectAttributes'] = module.params.get('object_attributes')

    object_attributes_info = {}

    try:
        object_attributes_info = connection.get_object_attributes(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_attributes_info['msg'] = 'Object attributes not found, are you sure the bucket/object configuration exist?'

    if len(object_attributes_info) != 0 and 'msg' not in object_attributes_info.keys():
        # Remove ResponseMetadata from object_attributes_info, convert to snake_case
        del(object_attributes_info['ResponseMetadata'])
        object_attributes_info = camel_dict_to_snake_dict(object_attributes_info)

    return object_attributes_info


def describe_s3_object_legal_hold(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_legal_hold_info = {}

    try:
        object_legal_hold_info = connection.get_object_legal_hold(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_legal_hold_info['msg'] = 'Object legal hold info not found, are you sure the bucket/object configuration exist?'

    if len(object_legal_hold_info) != 0 and 'msg' not in object_legal_hold_info.keys():
        # Remove ResponseMetadata from object_legal_hold_info, convert to snake_case
        del(object_legal_hold_info['ResponseMetadata'])
        object_legal_hold_info = camel_dict_to_snake_dict(object_legal_hold_info)

    return object_legal_hold_info


def describe_s3_object_lock_configuration(connection, module, bucket_name):
    params = {}
    params['Bucket'] = bucket_name

    object_legal_lock_configuration_info = {}

    try:
        object_legal_lock_configuration_info = connection.get_object_lock_configuration(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_legal_lock_configuration_info['msg'] = 'Object lock configuration not found, are you sure the bucket/object configuration exist?'

    if len(object_legal_lock_configuration_info) != 0 and 'msg' not in object_legal_lock_configuration_info.keys():
        # Remove ResponseMetadata from object_legal_lock_configuration_info, convert to snake_case
        del(object_legal_lock_configuration_info['ResponseMetadata'])
        object_legal_lock_configuration_info = camel_dict_to_snake_dict(object_legal_lock_configuration_info)

    return object_legal_lock_configuration_info


def describe_s3_object_retention(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_retention_info = {}

    try:
        object_retention_info = connection.get_object_retention(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_retention_info['msg'] = 'Object retention info not found, are you sure the bucket/object configuration exist?'

    if len(object_retention_info) != 0 and 'msg' not in object_retention_info.keys():
        # Remove ResponseMetadata from object_retention_info, convert to snake_case
        del(object_retention_info['ResponseMetadata'])
        object_retention_info = camel_dict_to_snake_dict(object_retention_info)

    return object_retention_info


def describe_s3_object_tagging(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_tagging_info = {}

    try:
        object_tagging_info = connection.get_object_tagging(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_tagging_info['msg'] = 'Object tags not found, are you sure the bucket/object tags exist?'

    if len(object_tagging_info) != 0 and 'msg' not in object_tagging_info.keys():
        # Remove ResponseMetadata from object_tagging_info, convert to snake_case
        del(object_tagging_info['ResponseMetadata'])
        object_tagging_info = boto3_tag_list_to_ansible_dict(object_tagging_info['TagSet'])

    return object_tagging_info


def get_object_details(connection, module, bucket_name, object_key, requested_facts):

    all_facts = {}

    # Remove non-requested facts
    requested_facts = {fact: value for fact, value in requested_facts.items() if value is True}

    for key in requested_facts:
        if key == 'object_acl':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_acl(connection, module, bucket_name, object_key)
        elif key == 'object_attributes':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_attributes(connection, module, bucket_name, object_key)
        elif key == 'object_legal_hold':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_legal_hold(connection, module, bucket_name, object_key)
        elif key == 'object_lock_configuration':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_lock_configuration(connection, module, bucket_name)
        elif key == 'object_retention':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_retention(connection, module, bucket_name, object_key)
        elif key == 'object_tagging':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_tagging(connection, module, bucket_name, object_key)

    return all_facts


def get_object(connection, module, bucket_name, object_key):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_key

    object_info = {}

    try:
        object_info = connection.get_object(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_info) != 0:
        # Remove Body, ResponseMetadata from object_info, convert to snake_case
        del(object_info['Body'])
        del(object_info['ResponseMetadata'])
        object_info = camel_dict_to_snake_dict(object_info)

    return object_info


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
        object_attributes=dict(type='list', choices=['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize']),
        s3_url=dict(),
        dualstack=dict(default='no', type='bool'),
        rgw=dict(default='no', type='bool'),
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
    requested_details = module.params.get('object_details')

    if requested_details and requested_details['object_attributes'] is True:
        if not module.params.get('object_attributes'):
            module.fail_json(msg='Please provide object_attributes list to retrieve s3 object_attributes.')

    if requested_details:
        result['object_info'] = get_object_details(connection, module, bucket_name, object_key, requested_details)
    else:
        #if specific details are not requested, return object metadata
        result['object_info'] = get_object(connection, module, bucket_name, object_key)

    module.exit_json(msg="Retrieved s3 object info ", **result)


if __name__ == '__main__':
    main()

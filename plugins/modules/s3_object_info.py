#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: s3_object_info
version_added: 5.0.0
short_description: Gather information about objects in S3
description:
    - Describes objects in S3.
author:
  - Mandar Vijay Kulkarni (@mandar242)
options:
  bucket_name:
    description:
      - The name of the bucket that contains the object.
    required: true
    type: str
  object_name:
    description:
      - The name of the object.
    required: false
    type: str
  object_details:
    description:
      - Retrieve requested S3 object detailed information.
    required: false
    type: dict
    suboptions:
      object_acl:
        description:
          - Retreive S3 object ACL.
        required: false
        type: bool
        default: false
      object_legal_hold:
        description:
          - Retreive S3 object legal_hold.
        required: false
        type: bool
        default: false
      object_lock_configuration:
        description:
          - Retreive S3 object lock_configuration.
        required: false
        type: bool
        default: false
      object_retention:
        description:
          - Retreive S3 object retention.
        required: false
        type: bool
        default: false
      object_tagging:
        description:
          - Retreive S3 object Tags.
        required: false
        type: bool
        default: false
      object_attributes:
        description:
          - Retreive S3 object attributes.
        required: false
        type: bool
        default: false
      attributes_list:
        description:
          - The fields/details that should be returned.
          - Required when I(object_attributes) is C(true) in I(object_details).
        type: list
        elements: str
        choices: ['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize']

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Retrieve a list of objects in S3 bucket
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket

- name: Retrieve object metadata without object itself
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    object_name: MyTestObjectKey

- name: Retrieve detailed S3 object information
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    object_name: MyTestObjectKey
    object_details:
      object_acl: true
      object_tagging: true
      object_legal_hold: true
      object_attributes: true
      attributes_list:
        - ETag
        - ObjectSize

'''

RETURN = r'''
s3_keys:
  description: List of object keys.
  returned: when only I(bucket_name) is specified and I(object_name), I(object_details) are not specified.
  type: list
  elements: str
  sample:
  - prefix1/
  - prefix1/key1
  - prefix1/key2
object_info:
    description: S3 object details.
    returned: always
    type: list
    elements: dict
    contains:
        object_data:
            description: A dict containing the metadata of S3 object.
            returned: when I(bucket_name) and I(object_name) are specified but I(object_details) is not specified.
            type: dict
            elements: str
            contains:
                accept_ranges:
                    description: Indicates that a range of bytes was specified.
                    returned: always
                    type: str
                content_length:
                    description: Size of the body (object data) in bytes.
                    returned: always
                    type: int
                content_type:
                    description: A standard MIME type describing the format of the object data.
                    returned: always
                    type: str
                e_tag:
                    description: A opaque identifier assigned by a web server to a specific version of a resource found at a URL.
                    returned: always
                    type: str
                last_modified:
                    description: Creation date of the object.
                    returned: always
                    type: str
                metadata:
                    description: A map of metadata to store with the object in S3.
                    returned: always
                    type: dict
                server_side_encryption:
                    description: The server-side encryption algorithm used when storing this object in Amazon S3.
                    returned: always
                    type: str
                tag_count:
                    description: The number of tags, if any, on the object.
                    returned: always
                    type: int
        object_acl:
            description: Access control list (ACL) of an object.
            returned: when I(object_acl) is set to I(true).
            type: complex
            contains:
                owner:
                    description: Bucket owner's display ID and name.
                    returned: always
                    type: complex
                    contains:
                        id:
                            description: Bucket owner's ID.
                            returned: always
                            type: str
                            sample: "xxxxxxxxxxxxxxxxxxxxx"
                        display_name:
                            description: Bucket owner's display name.
                            returned: always
                            type: str
                            sample: 'abcd'
                grants:
                    description: A list of grants.
                    returned: always
                    type: complex
                    contains:
                        grantee:
                            description: The entity being granted permissions.
                            returned: always
                            type: complex
                            contains:
                                id:
                                    description: The canonical user ID of the grantee.
                                    returned: always
                                    type: str
                                    sample: "xxxxxxxxxxxxxxxxxxx"
                                type:
                                    description: type of grantee.
                                    returned: always
                                    type: str
                                    sample: "CanonicalUser"
                        permission:
                            description: Specifies the permission given to the grantee.
                            returned: always
                            type: str
                            sample: "FULL CONTROL"
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
                                    description:
                                      - The default Object Lock retention mode you want to apply to new objects placed in the specified bucket.
                                      - Must be used with either Days or Years.
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
                            type: str
        object_tagging:
            description: The tag-set of an object
            returned: when I(object_tagging) is set to I(true).
            type: dict
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
                    type: str
                    sample: "2022-08-10T01:11:03+00:00"
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
                            description:
                              - When a list is truncated, this element specifies the last part in the list
                              - As well as the value to use for the PartNumberMarker request parameter in a subsequent request.
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
                storage_class:
                    description: The storage class information of the object.
                    returned: always
                    type: str
                    sample: "STANDARD"
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
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def describe_s3_object_acl(connection, bucket_name, object_name):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_name

    object_acl_info = {}

    try:
        object_acl_info = connection.get_object_acl(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_acl_info) != 0:
        # Remove ResponseMetadata from object_acl_info, convert to snake_case
        del(object_acl_info['ResponseMetadata'])
        object_acl_info = camel_dict_to_snake_dict(object_acl_info)

    return object_acl_info


def describe_s3_object_attributes(connection, module, bucket_name, object_name):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_name
    params['ObjectAttributes'] = module.params.get('object_details')['attributes_list']

    object_attributes_info = {}

    try:
        object_attributes_info = connection.get_object_attributes(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        object_attributes_info['msg'] = 'Object attributes not found'

    if len(object_attributes_info) != 0 and 'msg' not in object_attributes_info.keys():
        # Remove ResponseMetadata from object_attributes_info, convert to snake_case
        del(object_attributes_info['ResponseMetadata'])
        object_attributes_info = camel_dict_to_snake_dict(object_attributes_info)

    return object_attributes_info


def describe_s3_object_legal_hold(connection, bucket_name, object_name):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_name

    object_legal_hold_info = {}

    try:
        object_legal_hold_info = connection.get_object_legal_hold(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_legal_hold_info) != 0:
        # Remove ResponseMetadata from object_legal_hold_info, convert to snake_case
        del(object_legal_hold_info['ResponseMetadata'])
        object_legal_hold_info = camel_dict_to_snake_dict(object_legal_hold_info)

    return object_legal_hold_info


def describe_s3_object_lock_configuration(connection, bucket_name):
    params = {}
    params['Bucket'] = bucket_name

    object_legal_lock_configuration_info = {}

    try:
        object_legal_lock_configuration_info = connection.get_object_lock_configuration(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_legal_lock_configuration_info) != 0:
        # Remove ResponseMetadata from object_legal_lock_configuration_info, convert to snake_case
        del(object_legal_lock_configuration_info['ResponseMetadata'])
        object_legal_lock_configuration_info = camel_dict_to_snake_dict(object_legal_lock_configuration_info)

    return object_legal_lock_configuration_info


def describe_s3_object_retention(connection, bucket_name, object_name):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_name

    object_retention_info = {}

    try:
        object_retention_info = connection.get_object_retention(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_retention_info) != 0:
        # Remove ResponseMetadata from object_retention_info, convert to snake_case
        del(object_retention_info['ResponseMetadata'])
        object_retention_info = camel_dict_to_snake_dict(object_retention_info)

    return object_retention_info


def describe_s3_object_tagging(connection, bucket_name, object_name):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_name

    object_tagging_info = {}

    try:
        object_tagging_info = connection.get_object_tagging(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(object_tagging_info) != 0:
        # Remove ResponseMetadata from object_tagging_info, convert to snake_case
        del(object_tagging_info['ResponseMetadata'])
        object_tagging_info = boto3_tag_list_to_ansible_dict(object_tagging_info['TagSet'])

    return object_tagging_info


def get_object_details(connection, module, bucket_name, object_name, requested_facts):

    all_facts = {}

    # Remove non-requested facts
    requested_facts = {fact: value for fact, value in requested_facts.items() if value is True}

    all_facts['object_data'] = get_object(connection, bucket_name, object_name)['object_data']

    for key in requested_facts:
        if key == 'object_acl':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_acl(connection, bucket_name, object_name)
        elif key == 'object_attributes':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_attributes(connection, module, bucket_name, object_name)
        elif key == 'object_legal_hold':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_legal_hold(connection, bucket_name, object_name)
        elif key == 'object_lock_configuration':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_lock_configuration(connection, bucket_name)
        elif key == 'object_retention':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_retention(connection, bucket_name, object_name)
        elif key == 'object_tagging':
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_tagging(connection, bucket_name, object_name)

    return all_facts


def get_object(connection, bucket_name, object_name):
    params = {}
    params['Bucket'] = bucket_name
    params['Key'] = object_name

    result = {}
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

    result['object_data'] = object_info

    return result


@AWSRetry.jittered_backoff(retries=10)
def _list_bucket_objects(connection, **params):
    paginator = connection.get_paginator('list_objects')
    return paginator.paginate(**params).build_full_result()


def list_bucket_objects(connection, module, bucket_name):
    params = {}
    params['Bucket'] = bucket_name

    result = []
    list_objects_response = {}

    try:
        list_objects_response = _list_bucket_objects(connection, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        pass

    if len(list_objects_response) != 0:
        # convert to snake_case
        for response_list_item in list_objects_response['Contents']:
            result.append(response_list_item['Key'])

    module.exit_json(s3_keys=result)


def main():

    argument_spec = dict(
        object_details=dict(type='dict', options=dict(
            object_acl=dict(type='bool', default=False),
            object_legal_hold=dict(type='bool', default=False),
            object_lock_configuration=dict(type='bool', default=False),
            object_retention=dict(type='bool', default=False),
            object_tagging=dict(type='bool', default=False),
            object_attributes=dict(type='bool', default=False),
            attributes_list=dict(type='list', elements='str', choices=['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize']),
        )),
        bucket_name=dict(required=True, type='str'),
        object_name=dict(type='str'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        connection = module.client('s3', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    result = []

    bucket_name = module.params.get('bucket_name')
    object_name = module.params.get('object_name')
    requested_details = module.params.get('object_details')

    if requested_details and len(requested_details['attributes_list']) != 0:
        module.require_botocore_at_least('1.24.8', reason='required for s3.get_object_attributes')
        if not requested_details['attributes_list']:
            module.fail_json(msg='Please provide attributes_list list to retrieve s3 object_attributes.')

    if requested_details:
        object_details = get_object_details(connection, module, bucket_name, object_name, requested_details)
        result.append(object_details)
    elif not requested_details and object_name:
        # if specific details are not requested, return object metadata
        object_details = get_object(connection, bucket_name, object_name)
        result.append(object_details)
    else:
        # return list of all objects in a bucket if object name and object details not specified
        list_bucket_objects(connection, module, bucket_name)

    module.exit_json(object_info=result)


if __name__ == '__main__':
    main()

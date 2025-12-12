#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: s3_object_info
version_added: 5.0.0
short_description: Gather information about objects in S3
description:
    - Describes objects in S3.
    - Compatible with AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID (only supports list_keys currently).
    - When using non-AWS services, O(endpoint_url) should be specified.
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
      - If not specified, a list of all objects in the specified bucket will be returned.
      - Mutually exclusive with O(prefix).
    required: false
    type: str
  endpoint_url:
    description:
      - S3 URL endpoint for usage with Ceph, Eucalyptus and fakes3 etc. Otherwise assumes AWS.
    type: str
  dualstack:
    description:
      - Enables Amazon S3 Dual-Stack Endpoints, allowing S3 communications using both IPv4 and IPv6.
      - Mutually exclusive with O(endpoint_url).
    type: bool
    default: false
  ceph:
    description:
      - Enable API compatibility with Ceph RGW.
      - It takes into account the S3 API subset working with Ceph in order to provide the same module
        behaviour where possible.
      - Requires O(endpoint_url) if O(ceph=true).
    aliases: ['rgw']
    default: false
    type: bool
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
          - Required when O(object_details.object_attributes=true).
        type: list
        elements: str
        choices: ['ETag', 'Checksum', 'ObjectParts', 'StorageClass', 'ObjectSize']
  marker:
    description:
      - Specifies the Object key to start with.  Object keys are returned in alphabetical order, starting with key
        after the marker in order.
    type: str
    version_added: 9.0.0
  max_keys:
    description:
      - Max number of results to return.  Set this if you want to retrieve only partial results.
    type: int
    version_added: 9.0.0
  prefix:
    description:
      - Limits the response to keys that begin with the specified prefix.
      - Mutually exclusive with O(object_name).
    type: str
    version_added: 9.2.0
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Retrieve a list of objects in S3 bucket
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket

- name: Retrieve a list of objects in Ceph RGW S3
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    ceph: true
    endpoint_url: "http://localhost:8000"

- name: Retrieve object metadata without object itself
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    object_name: MyTestObjectKey

- name: Retrieve detailed S3 information for all objects in the bucket
  amazon.aws.s3_object_info:
    bucket_name: MyTestBucket
    object_details:
      object_acl: true
      object_attributes: true
      attributes_list:
        - ETag
        - ObjectSize
        - StorageClass

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

- name: Retrieve keys that begin with the prefix /my/desired/
  amazon.aws.s3_object_info:
    bucket: mybucket
    prefix: /my/desired/
"""

RETURN = r"""
s3_keys:
  description: List of object keys.
  returned: when only O(bucket_name) is specified and O(object_name), O(object_details) are not specified.
  type: list
  elements: str
  sample:
  - prefix1/
  - prefix1/key1
  - prefix1/key2
object_info:
    description: S3 object details.
    returned: when O(bucket_name) and O(object_name) are specified.
    type: list
    elements: dict
    contains:
        object_data:
            description: A dict containing the metadata of S3 object.
            returned: when O(bucket_name) and O(object_name) are specified but O(object_details) is not specified.
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
            returned: when O(object_details.object_acl=true).
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
            returned: when O(object_details.object_legal_hold=true) and object legal hold is set on the bucket.
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
            returned: when O(object_details.object_lock_configuration=true) and object lock configuration is set on the bucket.
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
            returned: when O(object_details.object_retention=true) and object retention is set on the bucket.
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
            returned: when O(object_details.object_tagging=true).
            type: dict
        object_attributes:
            description: Object attributes.
            returned: when O(object_details.object_attributes=true).
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
"""

import typing

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import List

    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3Error
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3SupportError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_acl
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_attributes
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_legal_hold
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_lock_configuration
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_retention
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_tagging
from ansible_collections.amazon.aws.plugins.module_utils.s3 import head_s3_object
from ansible_collections.amazon.aws.plugins.module_utils.s3 import list_bucket_object_keys
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_bucket_exists
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_extra_params
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_object_exists


def describe_s3_object_acl(connection: ClientType, bucket_name: str, object_name: str) -> Dict:
    """Get object ACL."""
    try:
        acl_info = get_s3_object_acl(connection, bucket_name, object_name)
        if acl_info:
            return camel_dict_to_snake_dict(acl_info)
        return {}
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {}
    except AnsibleS3Error:
        # Silent failure to maintain backward compatibility
        return {}


def describe_s3_object_attributes(
    connection: ClientType, module: AnsibleAWSModule, bucket_name: str, object_name: str
) -> Dict:
    """Get object attributes."""
    try:
        attributes_list = module.params.get("object_details", {}).get("attributes_list", [])
        if not attributes_list:
            return {}

        attrs = get_s3_object_attributes(connection, bucket_name, object_name, object_attributes=attributes_list)
        if attrs:
            return camel_dict_to_snake_dict(attrs)
        return {}
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {"msg": "Object attributes not found"}
    except AnsibleS3Error:
        return {"msg": "Object attributes not found"}


def describe_s3_object_legal_hold(connection: ClientType, bucket_name: str, object_name: str) -> Dict:
    """Get object legal hold status."""
    try:
        legal_hold = get_s3_object_legal_hold(connection, bucket_name, object_name)
        if legal_hold:
            return {"legal_hold": camel_dict_to_snake_dict(legal_hold)}
        return {}
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {}
    except AnsibleS3Error:
        # Silent failure to maintain backward compatibility
        return {}


def describe_s3_object_lock_configuration(connection: ClientType, bucket_name: str) -> Dict:
    """Get bucket-level object lock configuration."""
    try:
        lock_config = get_s3_object_lock_configuration(connection, bucket_name)
        if lock_config:
            return camel_dict_to_snake_dict(lock_config)
        return {}
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {}
    except AnsibleS3Error:
        # Silent failure to maintain backward compatibility
        return {}


def describe_s3_object_retention(connection: ClientType, bucket_name: str, object_name: str) -> Dict:
    """Get object retention settings."""
    try:
        retention = get_s3_object_retention(connection, bucket_name, object_name)
        if retention:
            return {"retention": camel_dict_to_snake_dict(retention)}
        return {}
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {}
    except AnsibleS3Error:
        # Silent failure to maintain backward compatibility
        return {}


def describe_s3_object_tagging(connection: ClientType, bucket_name: str, object_name: str) -> Dict:
    """Get object tags."""
    try:
        return get_s3_object_tagging(connection, bucket_name, object_name)
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {}
    except AnsibleS3Error:
        # Silent failure to maintain backward compatibility
        return {}


def get_object_details(
    connection: ClientType, module: AnsibleAWSModule, bucket_name: str, object_name: str, requested_facts: Dict
) -> Dict:
    all_facts = {}

    # Remove non-requested facts
    requested_facts = {fact: value for fact, value in requested_facts.items() if value is True}

    all_facts["object_data"] = get_object(connection, bucket_name, object_name)["object_data"]

    # Below APIs do not return object_name, need to add it manually
    all_facts["object_name"] = object_name

    for key in requested_facts:
        if key == "object_acl":
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_acl(connection, bucket_name, object_name)
        elif key == "object_attributes":
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_attributes(connection, module, bucket_name, object_name)
        elif key == "object_legal_hold":
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_legal_hold(connection, bucket_name, object_name)
        elif key == "object_lock_configuration":
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_lock_configuration(connection, bucket_name)
        elif key == "object_retention":
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_retention(connection, bucket_name, object_name)
        elif key == "object_tagging":
            all_facts[key] = {}
            all_facts[key] = describe_s3_object_tagging(connection, bucket_name, object_name)

    return all_facts


def get_object(connection: ClientType, bucket_name: str, object_name: str) -> Dict:
    """Get basic object metadata."""
    try:
        object_info = head_s3_object(connection, bucket_name, object_name)
        if object_info:
            object_info = camel_dict_to_snake_dict(object_info)
        return {"object_data": object_info}
    except AnsibleS3SupportError:
        # Silent failure for unsupported operations on S3 drop-ins
        return {"object_data": {}}
    except AnsibleS3Error:
        # Silent failure to maintain backward compatibility
        return {"object_data": {}}


def list_bucket_objects(connection: ClientType, module: AnsibleAWSModule, bucket_name: str) -> List[str]:
    keys = list_bucket_object_keys(
        connection,
        bucket=bucket_name,
        max_keys=module.params["max_keys"],
        start_after=module.params["marker"],
        prefix=module.params["prefix"],
    )
    return keys


def bucket_check(connection: ClientType, module: AnsibleAWSModule, bucket_name: str) -> None:
    """Check if bucket exists and is accessible."""
    if not s3_bucket_exists(connection, bucket_name):
        module.fail_json(msg=f"The bucket {bucket_name} does not exist.")


def object_check(connection: ClientType, module: AnsibleAWSModule, bucket_name: str, object_name: str) -> None:
    """Check if object exists and is accessible."""
    if not s3_object_exists(connection, bucket_name, object_name):
        module.fail_json(msg=f"The object {object_name} does not exist.")


def main() -> None:
    argument_spec = dict(
        object_details=dict(
            type="dict",
            options=dict(
                object_acl=dict(type="bool", default=False),
                object_legal_hold=dict(type="bool", default=False),
                object_lock_configuration=dict(type="bool", default=False),
                object_retention=dict(type="bool", default=False),
                object_tagging=dict(type="bool", default=False),
                object_attributes=dict(type="bool", default=False),
                attributes_list=dict(
                    type="list",
                    elements="str",
                    choices=["ETag", "Checksum", "ObjectParts", "StorageClass", "ObjectSize"],
                ),
            ),
            required_if=[
                ("object_attributes", True, ["attributes_list"]),
            ],
        ),
        bucket_name=dict(required=True, type="str"),
        object_name=dict(type="str"),
        dualstack=dict(default=False, type="bool"),
        ceph=dict(default=False, type="bool", aliases=["rgw"]),
        marker=dict(),
        max_keys=dict(type="int", no_log=False),
        prefix=dict(type="str", required=False),
    )

    required_if = [
        ["ceph", True, ["endpoint_url"]],
    ]

    mutually_exclusive = [
        ["object_name", "prefix"],
        ["dualstack", "endpoint_url"],
    ]
    mutually_exclusive = [["object_name", "prefix"], ["dualstack", "endpoint_url"]]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
    )

    bucket_name = module.params.get("bucket_name")
    object_name = module.params.get("object_name")
    requested_object_details = module.params.get("object_details")

    result = []
    extra_params = s3_extra_params(module.params)
    retry_decorator = AWSRetry.jittered_backoff()
    connection = module.client("s3", retry_decorator=retry_decorator, **extra_params)

    # check if specified bucket exists
    bucket_check(connection, module, bucket_name)
    # check if specified object exists
    if object_name:
        object_check(connection, module, bucket_name, object_name)

    if requested_object_details:
        if object_name:
            object_details = get_object_details(connection, module, bucket_name, object_name, requested_object_details)
            result.append(object_details)
        elif object_name is None:
            object_list = list_bucket_objects(connection, module, bucket_name)
            for bucket_object in object_list:
                result.append(
                    get_object_details(connection, module, bucket_name, bucket_object, requested_object_details)
                )

    elif not requested_object_details and object_name:
        # if specific details are not requested, return object metadata
        object_details = get_object(connection, bucket_name, object_name)
        result.append(object_details)
    else:
        # return list of all objects in a bucket if object name and object details not specified
        object_list = list_bucket_objects(connection, module, bucket_name)
        module.exit_json(s3_keys=object_list)

    module.exit_json(object_info=result)


if __name__ == "__main__":
    main()

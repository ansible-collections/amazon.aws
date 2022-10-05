#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: s3_object
version_added: 1.0.0
short_description: Manage objects in S3
description:
  - This module allows the user to manage the objects and directories within S3 buckets. Includes
    support for creating and deleting objects and directories, retrieving objects as files or
    strings, generating download links and copying objects that are already stored in Amazon S3.
  - Support for creating or deleting S3 buckets with this module has been deprecated and will be
    removed in release 6.0.0.
  - S3 buckets can be created or deleted using the M(amazon.aws.s3_bucket) module.
  - Compatible with AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID.
  - When using non-AWS services, I(endpoint_url) should be specified.
options:
  bucket:
    description:
      - Bucket name.
    required: true
    type: str
  dest:
    description:
      - The destination file path when downloading an object/key when I(mode=get).
      - Ignored when I(mode) is not C(get).
    type: path
  encrypt:
    description:
      - Asks for server-side encryption of the objects when I(mode=put) or I(mode=copy).
      - Ignored when I(mode) is neither C(put) nor C(copy).
    default: true
    type: bool
  encryption_mode:
    description:
      - The encryption mode to use if I(encrypt=true).
    default: AES256
    choices:
      - AES256
      - aws:kms
    type: str
  expiry:
    description:
      - Time limit (in seconds) for the URL generated and returned by S3/Walrus when performing a
        I(mode=put) or I(mode=geturl) operation.
      - Ignored when I(mode) is neither C(put) nor C(geturl).
    default: 600
    aliases: ['expiration']
    type: int
  headers:
    description:
      - Custom headers to use when I(mode=put) as a dictionary of key value pairs.
      - Ignored when I(mode) is not C(put).
    type: dict
  marker:
    description:
      - Specifies the key to start with when using list mode. Object keys are returned in
        alphabetical order, starting with key after the marker in order.
    type: str
  max_keys:
    description:
      - Max number of results to return when I(mode=list), set this if you want to retrieve fewer
        than the default 1000 keys.
      - Ignored when I(mode) is not C(list).
    default: 1000
    type: int
  metadata:
    description:
      - Metadata to use when I(mode=put) or I(mode=copy) as a dictionary of key value pairs.
    type: dict
  mode:
    description:
      - Switches the module behaviour between
      - 'C(put): upload'
      - 'C(get): download'
      - 'C(geturl): return download URL'
      - 'C(getstr): download object as string'
      - 'C(list): list keys'
      - 'C(create): create bucket directories'
      - 'C(delete): delete bucket directories'
      - 'C(delobj): delete object'
      - 'C(copy): copy object that is already stored in another bucket'
      - Support for creating and deleting buckets has been deprecated and will
        be removed in release 6.0.0.  To create and manage the bucket itself
        please use the M(amazon.aws.s3_bucket) module.
    required: true
    choices: ['get', 'put', 'delete', 'create', 'geturl', 'getstr', 'delobj', 'list', 'copy']
    type: str
  object:
    description:
      - Keyname of the object inside the bucket.
      - Can be used to create "virtual directories", see examples.
    type: str
  sig_v4:
    description:
      - Forces the Boto SDK to use Signature Version 4.
      - Only applies to get modes, I(mode=get), I(mode=getstr), I(mode=geturl).
    default: true
    type: bool
    version_added: 5.0.0
  permission:
    description:
      - This option lets the user set the canned permissions on the object/bucket that are created.
        The permissions that can be set are C(private), C(public-read), C(public-read-write),
        C(authenticated-read) for a bucket or C(private), C(public-read), C(public-read-write),
        C(aws-exec-read), C(authenticated-read), C(bucket-owner-read), C(bucket-owner-full-control)
        for an object. Multiple permissions can be specified as a list; although only the first one
        will be used during the initial upload of the file.
      - For a full list of permissions see the AWS documentation
        U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl).
    default: ['private']
    type: list
    elements: str
  prefix:
    description:
      - Limits the response to keys that begin with the specified prefix for list mode.
    default: ""
    type: str
  version:
    description:
      - Version ID of the object inside the bucket. Can be used to get a specific version of a file
        if versioning is enabled in the target bucket.
    type: str
  overwrite:
    description:
      - Force overwrite either locally on the filesystem or remotely with the object/key.
      - Used when I(mode=put) or I(mode=get).
      - Ignored when when I(mode) is neither C(put) nor C(get).
      - Must be a Boolean, C(always), C(never), C(different) or C(latest).
      - C(true) is the same as C(always).
      - C(false) is equal to C(never).
      - When this is set to C(different) the MD5 sum of the local file is compared with the 'ETag'
        of the object/key in S3.  The ETag may or may not be an MD5 digest of the object data. See
        the ETag response header here
        U(https://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonResponseHeaders.html).
      - When I(mode=get) and I(overwrite=latest) the last modified timestamp of local file
        is compared with the 'LastModified' of the object/key in S3.
    default: 'different'
    aliases: ['force']
    type: str
  retries:
    description:
     - On recoverable failure, how many times to retry before actually failing.
    default: 0
    type: int
    aliases: ['retry']
  dualstack:
    description:
      - Enables Amazon S3 Dual-Stack Endpoints, allowing S3 communications using both IPv4 and IPv6.
    type: bool
    default: false
  ceph:
    description:
      - Enable API compatibility with Ceph RGW.
      - It takes into account the S3 API subset working with Ceph in order to provide the same module
        behaviour where possible.
      - Requires I(endpoint_url) if I(ceph=true).
    aliases: ['rgw']
    default: false
    type: bool
  src:
    description:
      - The source file path when performing a C(put) operation.
      - One of I(content), I(content_base64) or I(src) must be specified when I(mode=put)
        otherwise ignored.
    type: path
  content:
    description:
      - The content to C(put) into an object.
      - The parameter value will be treated as a string and converted to UTF-8 before sending it to
        S3.
      - To send binary data, use the I(content_base64) parameter instead.
      - One of I(content), I(content_base64) or I(src) must be specified when I(mode=put)
        otherwise ignored.
    version_added: "1.3.0"
    type: str
  content_base64:
    description:
      - The base64-encoded binary data to C(put) into an object.
      - Use this if you need to put raw binary data, and don't forget to encode in base64.
      - One of I(content), I(content_base64) or I(src) must be specified when I(mode=put)
        otherwise ignored.
    version_added: "1.3.0"
    type: str
  ignore_nonexistent_bucket:
    description:
      - Overrides initial bucket lookups in case bucket or IAM policies are restrictive.
      - This can be useful when a user may have the C(GetObject) permission but no other
        permissions.  In which case using I(mode=get) will fail unless
        I(ignore_nonexistent_bucket=true) is specified.
    type: bool
    default: false
  encryption_kms_key_id:
    description:
      - KMS key id to use when encrypting objects using I(encrypting=aws:kms).
      - Ignored if I(encryption) is not C(aws:kms).
    type: str
  copy_src:
    description:
    - The source details of the object to copy.
    - Required if I(mode=copy).
    type: dict
    version_added: 2.0.0
    suboptions:
      bucket:
        type: str
        description:
        - The name of the source bucket.
        required: true
      object:
        type: str
        description:
        - key name of the source object.
        required: true
      version_id:
        type: str
        description:
        - version ID of the source object.
  validate_bucket_name:
    description:
      - Whether the bucket name should be validated to conform to AWS S3 naming rules.
      - On by default, this may be disabled for S3 backends that do not enforce these rules.
      - See the Amazon documentation for more information about bucket naming rules
        U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html).
    type: bool
    version_added: 3.1.0
    default: True
author:
  - "Lester Wade (@lwade)"
  - "Sloane Hertel (@s-hertel)"
  - "Alina Buzachis (@alinabuzachis)"
notes:
  - Support for I(tags) and I(purge_tags) was added in release 2.0.0.
  - In release 5.0.0 the I(s3_url) parameter was merged into the I(endpoint_url) parameter,
    I(s3_url) remains as an alias for I(endpoint_url).
  - For Walrus I(endpoint_url) should be set to the FQDN of the endpoint with neither scheme nor path.
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
  - amazon.aws.boto3
'''

EXAMPLES = '''
- name: Simple PUT operation
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put

- name: PUT operation from a rendered template
  amazon.aws.s3_object:
    bucket: mybucket
    object: /object.yaml
    content: "{{ lookup('template', 'templates/object.yaml.j2') }}"
    mode: put

- name: Simple PUT operation in Ceph RGW S3
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    ceph: true
    endpoint_url: "http://localhost:8000"

- name: Simple GET operation
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    dest: /usr/local/myfile.txt
    mode: get

- name: Get a specific version of an object.
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    version: 48c9ee5131af7a716edc22df9772aa6f
    dest: /usr/local/myfile.txt
    mode: get

- name: PUT/upload with metadata
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    metadata: 'Content-Encoding=gzip,Cache-Control=no-cache'

- name: PUT/upload with custom headers
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    headers: 'x-amz-grant-full-control=emailAddress=owner@example.com'

- name: List keys simple
  amazon.aws.s3_object:
    bucket: mybucket
    mode: list

- name: List keys all options
  amazon.aws.s3_object:
    bucket: mybucket
    mode: list
    prefix: /my/desired/
    marker: /my/desired/0023.txt
    max_keys: 472

- name: Create an empty bucket
  amazon.aws.s3_object:
    bucket: mybucket
    mode: create
    permission: public-read

- name: Create a bucket with key as directory, in the EU region
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/directory/path
    mode: create
    region: eu-west-1

- name: Delete a bucket and all contents
  amazon.aws.s3_object:
    bucket: mybucket
    mode: delete

- name: GET an object but don't download if the file checksums match. New in 2.0
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    dest: /usr/local/myfile.txt
    mode: get
    overwrite: different

- name: Delete an object from a bucket
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    mode: delobj

- name: Copy an object already stored in another bucket
  amazon.aws.s3_object:
    bucket: mybucket
    object: /my/desired/key.txt
    mode: copy
    copy_src:
        bucket: srcbucket
        object: /source/key.txt
'''

RETURN = '''
msg:
  description: Message indicating the status of the operation.
  returned: always
  type: str
  sample: PUT operation complete
url:
  description: URL of the object.
  returned: (for put and geturl operations)
  type: str
  sample: https://my-bucket.s3.amazonaws.com/my-key.txt?AWSAccessKeyId=<access-key>&Expires=1506888865&Signature=<signature>
expiry:
  description: Number of seconds the presigned url is valid for.
  returned: (for geturl operation)
  type: int
  sample: 600
contents:
  description: Contents of the object as string.
  returned: (for getstr operation)
  type: str
  sample: "Hello, world!"
s3_keys:
  description: List of object keys.
  returned: (for list operation)
  type: list
  elements: str
  sample:
  - prefix1/
  - prefix1/key1
  - prefix1/key2
'''

import mimetypes
import os
import io
from ssl import SSLError
import base64
import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.basic import to_text
from ansible.module_utils.basic import to_native
from ansible.module_utils.six.moves.urllib.parse import urlparse

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_conn
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.s3 import HAS_MD5
from ansible_collections.amazon.aws.plugins.module_utils.s3 import calculate_etag
from ansible_collections.amazon.aws.plugins.module_utils.s3 import calculate_etag_content
from ansible_collections.amazon.aws.plugins.module_utils.s3 import validate_bucket_name

IGNORE_S3_DROP_IN_EXCEPTIONS = ['XNotImplemented', 'NotImplemented']


class Sigv4Required(Exception):
    pass


def key_check(module, s3, bucket, obj, version=None, validate=True):
    try:
        if version:
            s3.head_object(Bucket=bucket, Key=obj, VersionId=version)
        else:
            s3.head_object(Bucket=bucket, Key=obj)
    except is_boto3_error_code('404'):
        return False
    except is_boto3_error_code('403') as e:  # pylint: disable=duplicate-except
        if validate is True:
            module.fail_json_aws(e, msg="Failed while looking up object (during key check) %s." % obj)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while looking up object (during key check) %s." % obj)

    return True


def etag_compare(module, s3, bucket, obj, version=None, local_file=None, content=None):
    s3_etag = get_etag(s3, bucket, obj, version=version)
    if local_file is not None:
        local_etag = calculate_etag(module, local_file, s3_etag, s3, bucket, obj, version)
    else:
        local_etag = calculate_etag_content(module, content, s3_etag, s3, bucket, obj, version)

    return s3_etag == local_etag


def get_etag(s3, bucket, obj, version=None):
    try:
        if version:
            key_check = s3.head_object(Bucket=bucket, Key=obj, VersionId=version)
        else:
            key_check = s3.head_object(Bucket=bucket, Key=obj)
        if not key_check:
            return None
        return key_check['ETag']
    except is_boto3_error_code('404'):
        return None


def get_s3_last_modified_timestamp(s3, bucket, obj, version=None):
    if version:
        key_check = s3.head_object(Bucket=bucket, Key=obj, VersionId=version)
    else:
        key_check = s3.head_object(Bucket=bucket, Key=obj)
    if not key_check:
        return None
    return key_check['LastModified'].timestamp()


def is_local_object_latest(module, s3, bucket, obj, version=None, local_file=None):
    s3_last_modified = get_s3_last_modified_timestamp(s3, bucket, obj, version)
    if os.path.exists(local_file) is False:
        return False
    else:
        local_last_modified = os.path.getmtime(local_file)

    return s3_last_modified <= local_last_modified


def bucket_check(module, s3, bucket, validate=True):
    exists = True
    try:
        s3.head_bucket(Bucket=bucket)
    except is_boto3_error_code('404'):
        return False
    except is_boto3_error_code('403') as e:  # pylint: disable=duplicate-except
        if validate is True:
            module.fail_json_aws(e, msg="Failed while looking up bucket (during bucket_check) %s." % bucket)
    except botocore.exceptions.EndpointConnectionError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Invalid endpoint provided")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while looking up bucket (during bucket_check) %s." % bucket)
    return exists


def create_bucket(module, s3, bucket, location=None):
    module.deprecate('Support for creating S3 buckets using the s3_object module'
                     ' has been deprecated.  Please use the ``s3_bucket`` module'
                     ' instead.', version='6.0.0', collection_name='amazon.aws')
    if module.check_mode:
        module.exit_json(msg="CREATE operation skipped - running in check mode", changed=True)
    configuration = {}
    if location not in ('us-east-1', None):
        configuration['LocationConstraint'] = location
    try:
        if len(configuration) > 0:
            s3.create_bucket(Bucket=bucket, CreateBucketConfiguration=configuration)
        else:
            s3.create_bucket(Bucket=bucket)
        if module.params.get('permission'):
            # Wait for the bucket to exist before setting ACLs
            s3.get_waiter('bucket_exists').wait(Bucket=bucket)
        for acl in module.params.get('permission'):
            AWSRetry.jittered_backoff(
                max_delay=120, catch_extra_error_codes=['NoSuchBucket']
            )(s3.put_bucket_acl)(ACL=acl, Bucket=bucket)
    except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS):
        module.warn("PutBucketAcl is not implemented by your storage provider. Set the permission parameters to the empty list to avoid this warning")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while creating bucket or setting acl (check that you have CreateBucket and PutBucketAcl permission).")

    if bucket:
        return True


def paginated_list(s3, **pagination_params):
    pg = s3.get_paginator('list_objects_v2')
    for page in pg.paginate(**pagination_params):
        yield [data['Key'] for data in page.get('Contents', [])]


def paginated_versioned_list_with_fallback(s3, **pagination_params):
    try:
        versioned_pg = s3.get_paginator('list_object_versions')
        for page in versioned_pg.paginate(**pagination_params):
            delete_markers = [{'Key': data['Key'], 'VersionId': data['VersionId']} for data in page.get('DeleteMarkers', [])]
            current_objects = [{'Key': data['Key'], 'VersionId': data['VersionId']} for data in page.get('Versions', [])]
            yield delete_markers + current_objects
    except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS + ['AccessDenied']):
        for page in paginated_list(s3, **pagination_params):
            yield [{'Key': data['Key']} for data in page]


def list_keys(module, s3, bucket, prefix, marker, max_keys):
    pagination_params = {'Bucket': bucket}
    for param_name, param_value in (('Prefix', prefix), ('StartAfter', marker), ('MaxKeys', max_keys)):
        pagination_params[param_name] = param_value
    try:
        keys = sum(paginated_list(s3, **pagination_params), [])
        module.exit_json(msg="LIST operation complete", s3_keys=keys)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while listing the keys in the bucket {0}".format(bucket))


def delete_bucket(module, s3, bucket):
    module.deprecate('Support for deleting S3 buckets using the s3_object module'
                     ' has been deprecated.  Please use the ``s3_bucket`` module'
                     ' instead.', version='6.0.0', collection_name='amazon.aws')
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        exists = bucket_check(module, s3, bucket)
        if exists is False:
            return False
        # if there are contents then we need to delete them before we can delete the bucket
        for keys in paginated_versioned_list_with_fallback(s3, Bucket=bucket):
            if keys:
                s3.delete_objects(Bucket=bucket, Delete={'Objects': keys})
        s3.delete_bucket(Bucket=bucket)
        return True
    except is_boto3_error_code('NoSuchBucket'):
        return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while deleting bucket %s." % bucket)


def delete_key(module, s3, bucket, obj):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        s3.delete_object(Bucket=bucket, Key=obj)
        module.exit_json(msg="Object deleted from bucket %s." % (bucket), changed=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while trying to delete %s." % obj)


def create_dirkey(module, s3, bucket, obj, encrypt, expiry):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        params = {'Bucket': bucket, 'Key': obj, 'Body': b''}
        if encrypt:
            params['ServerSideEncryption'] = module.params['encryption_mode']
        if module.params['encryption_kms_key_id'] and module.params['encryption_mode'] == 'aws:kms':
            params['SSEKMSKeyId'] = module.params['encryption_kms_key_id']

        s3.put_object(**params)
        for acl in module.params.get('permission'):
            s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
    except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS):
        module.warn("PutObjectAcl is not implemented by your storage provider. Set the permissions parameters to the empty list to avoid this warning")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while creating object %s." % obj)

    # Tags
    tags, _changed = ensure_tags(s3, module, bucket, obj)

    try:
        url = s3.generate_presigned_url(ClientMethod='put_object',
                                        Params={'Bucket': bucket, 'Key': obj},
                                        ExpiresIn=expiry)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to generate presigned URL")

    url = put_download_url(module, s3, bucket, obj, expiry)

    module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket), url=url, tags=tags, changed=True)


def path_check(path):
    if os.path.exists(path):
        return True
    else:
        return False


def option_in_extra_args(option):
    temp_option = option.replace('-', '').lower()

    allowed_extra_args = {'acl': 'ACL', 'cachecontrol': 'CacheControl', 'contentdisposition': 'ContentDisposition',
                          'contentencoding': 'ContentEncoding', 'contentlanguage': 'ContentLanguage',
                          'contenttype': 'ContentType', 'expires': 'Expires', 'grantfullcontrol': 'GrantFullControl',
                          'grantread': 'GrantRead', 'grantreadacp': 'GrantReadACP', 'grantwriteacp': 'GrantWriteACP',
                          'metadata': 'Metadata', 'requestpayer': 'RequestPayer', 'serversideencryption': 'ServerSideEncryption',
                          'storageclass': 'StorageClass', 'ssecustomeralgorithm': 'SSECustomerAlgorithm', 'ssecustomerkey': 'SSECustomerKey',
                          'ssecustomerkeymd5': 'SSECustomerKeyMD5', 'ssekmskeyid': 'SSEKMSKeyId', 'websiteredirectlocation': 'WebsiteRedirectLocation'}

    if temp_option in allowed_extra_args:
        return allowed_extra_args[temp_option]


def upload_s3file(module, s3, bucket, obj, expiry, metadata, encrypt, headers, src=None, content=None, acl_disabled=False):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        extra = {}
        if encrypt:
            extra['ServerSideEncryption'] = module.params['encryption_mode']
        if module.params['encryption_kms_key_id'] and module.params['encryption_mode'] == 'aws:kms':
            extra['SSEKMSKeyId'] = module.params['encryption_kms_key_id']
        if metadata:
            extra['Metadata'] = {}

            # determine object metadata and extra arguments
            for option in metadata:
                extra_args_option = option_in_extra_args(option)
                if extra_args_option is not None:
                    extra[extra_args_option] = metadata[option]
                else:
                    extra['Metadata'][option] = metadata[option]

        if module.params.get('permission'):
            permissions = module.params['permission']
            if isinstance(permissions, str):
                extra['ACL'] = permissions
            elif isinstance(permissions, list):
                extra['ACL'] = permissions[0]

        if 'ContentType' not in extra:
            content_type = None
            if src is not None:
                content_type = mimetypes.guess_type(src)[0]
            if content_type is None:
                # s3 default content type
                content_type = 'binary/octet-stream'
            extra['ContentType'] = content_type

        if src is not None:
            s3.upload_file(Filename=src, Bucket=bucket, Key=obj, ExtraArgs=extra)
        else:
            f = io.BytesIO(content)
            s3.upload_fileobj(Fileobj=f, Bucket=bucket, Key=obj, ExtraArgs=extra)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to complete PUT operation.")
    if not acl_disabled:
        try:
            for acl in module.params.get('permission'):
                s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
        except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS):
            module.warn("PutObjectAcl is not implemented by your storage provider. Set the permission parameters to the empty list to avoid this warning")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Unable to set object ACL")

    # Tags
    tags, _changed = ensure_tags(s3, module, bucket, obj)

    url = put_download_url(module, s3, bucket, obj, expiry)

    module.exit_json(msg="PUT operation complete", url=url, tags=tags, changed=True)


def download_s3file(module, s3, bucket, obj, dest, retries, version=None):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    # retries is the number of loops; range/xrange needs to be one
    # more to get that count of loops.
    try:
        # Note: Something of a permissions related hack
        # get_object returns the HEAD information, plus a *stream* which can be read.
        # because the stream's dropped on the floor, we never pull the data and this is the
        # functional equivalent of calling get_head which still relying on the 'GET' permission
        if version:
            s3.get_object(Bucket=bucket, Key=obj, VersionId=version)
        else:
            s3.get_object(Bucket=bucket, Key=obj)
    except is_boto3_error_code(['404', '403']) as e:
        # AccessDenied errors may be triggered if 1) file does not exist or 2) file exists but
        # user does not have the s3:GetObject permission. 404 errors are handled by download_file().
        module.fail_json_aws(e, msg="Could not find the key %s." % obj)
    except is_boto3_error_message('require AWS Signature Version 4'):  # pylint: disable=duplicate-except
        raise Sigv4Required()
    except is_boto3_error_code('InvalidArgument') as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Could not find the key %s." % obj)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Could not find the key %s." % obj)

    optional_kwargs = {'ExtraArgs': {'VersionId': version}} if version else {}
    for x in range(0, retries + 1):
        try:
            s3.download_file(bucket, obj, dest, **optional_kwargs)
            module.exit_json(msg="GET operation complete", changed=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json_aws(e, msg="Failed while downloading %s." % obj)
            # otherwise, try again, this may be a transient timeout.
        except SSLError as e:  # will ClientError catch SSLError?
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json_aws(e, msg="s3 download failed")
            # otherwise, try again, this may be a transient timeout.


def download_s3str(module, s3, bucket, obj, version=None, validate=True):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    try:
        if version:
            contents = to_native(s3.get_object(Bucket=bucket, Key=obj, VersionId=version)["Body"].read())
        else:
            contents = to_native(s3.get_object(Bucket=bucket, Key=obj)["Body"].read())
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except is_boto3_error_message('require AWS Signature Version 4'):
        raise Sigv4Required()
    except is_boto3_error_code('InvalidArgument') as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while getting contents of object %s as a string." % obj)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while getting contents of object %s as a string." % obj)


def get_download_url(module, s3, bucket, obj, expiry, tags=None, changed=True):
    try:
        url = s3.generate_presigned_url(ClientMethod='get_object',
                                        Params={'Bucket': bucket, 'Key': obj},
                                        ExpiresIn=expiry)
        module.exit_json(msg="Download url:", url=url, tags=tags, expiry=expiry, changed=changed)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while getting download url.")


def put_download_url(module, s3, bucket, obj, expiry):
    try:
        url = s3.generate_presigned_url(ClientMethod='put_object',
                                        Params={'Bucket': bucket, 'Key': obj},
                                        ExpiresIn=expiry)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to generate presigned URL")
    return url


def copy_object_to_bucket(module, s3, bucket, obj, encrypt, metadata, validate, d_etag):
    if module.check_mode:
        module.exit_json(msg="COPY operation skipped - running in check mode", changed=True)
    try:
        params = {'Bucket': bucket, 'Key': obj}
        bucketsrc = {'Bucket': module.params['copy_src'].get('bucket'), 'Key': module.params['copy_src'].get('object')}
        version = None
        if module.params['copy_src'].get('version_id') is not None:
            version = module.params['copy_src'].get('version_id')
            bucketsrc.update({'VersionId': version})
        if not key_check(module, s3, bucketsrc['Bucket'], bucketsrc['Key'], version=version, validate=validate):
            # Key does not exist in source bucket
            module.exit_json(msg="Key %s does not exist in bucket %s." % (bucketsrc['Key'], bucketsrc['Bucket']), changed=False)

        s_etag = get_etag(s3, bucketsrc['Bucket'], bucketsrc['Key'], version=version)
        if s_etag == d_etag:
            # Tags
            tags, changed = ensure_tags(s3, module, bucket, obj)
            if not changed:
                module.exit_json(msg="ETag from source and destination are the same", changed=False)
            else:
                module.exit_json(msg="tags successfully updated.", changed=changed, tags=tags)
        else:
            params.update({'CopySource': bucketsrc})
            if encrypt:
                params['ServerSideEncryption'] = module.params['encryption_mode']
            if module.params['encryption_kms_key_id'] and module.params['encryption_mode'] == 'aws:kms':
                params['SSEKMSKeyId'] = module.params['encryption_kms_key_id']
            if metadata:
                params['Metadata'] = {}
                # determine object metadata and extra arguments
                for option in metadata:
                    extra_args_option = option_in_extra_args(option)
                    if extra_args_option is not None:
                        params[extra_args_option] = metadata[option]
                    else:
                        params['Metadata'][option] = metadata[option]
            s3.copy_object(**params)
            for acl in module.params.get('permission'):
                s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
            # Tags
            tags, changed = ensure_tags(s3, module, bucket, obj)
            module.exit_json(msg="Object copied from bucket %s to bucket %s." % (bucketsrc['Bucket'], bucket), tags=tags, changed=True)
    except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS):
        module.warn("PutObjectAcl is not implemented by your storage provider. Set the permissions parameters to the empty list to avoid this warning")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed while copying object %s from bucket %s." % (obj, module.params['copy_src'].get('Bucket')))


def is_fakes3(endpoint_url):
    """ Return True if endpoint_url has scheme fakes3:// """
    if endpoint_url is not None:
        return urlparse(endpoint_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def get_s3_connection(module, aws_connect_kwargs, location, ceph, endpoint_url, sig_4=False):
    if ceph:  # TODO - test this
        ceph = urlparse(endpoint_url)
        params = dict(module=module, conn_type='client', resource='s3', use_ssl=ceph.scheme == 'https',
                      region=location, endpoint=endpoint_url, **aws_connect_kwargs)
    elif is_fakes3(endpoint_url):
        fakes3 = urlparse(endpoint_url)
        port = fakes3.port
        if fakes3.scheme == 'fakes3s':
            protocol = "https"
            if port is None:
                port = 443
        else:
            protocol = "http"
            if port is None:
                port = 80
        params = dict(module=module, conn_type='client', resource='s3', region=location,
                      endpoint="%s://%s:%s" % (protocol, fakes3.hostname, to_text(port)),
                      use_ssl=fakes3.scheme == 'fakes3s', **aws_connect_kwargs)
    else:
        params = dict(module=module, conn_type='client', resource='s3', region=location, endpoint=endpoint_url, **aws_connect_kwargs)
        if module.params['mode'] == 'put' and module.params['encryption_mode'] == 'aws:kms':
            params['config'] = botocore.client.Config(signature_version='s3v4')
        elif module.params['mode'] in ('get', 'getstr', 'geturl') and sig_4:
            params['config'] = botocore.client.Config(signature_version='s3v4')
        if module.params['dualstack']:
            dualconf = botocore.client.Config(s3={'use_dualstack_endpoint': True})
            if 'config' in params:
                params['config'] = params['config'].merge(dualconf)
            else:
                params['config'] = dualconf
    return boto3_conn(**params)


def get_current_object_tags_dict(s3, bucket, obj, version=None):
    try:
        if version:
            current_tags = s3.get_object_tagging(Bucket=bucket, Key=obj, VersionId=version).get('TagSet')
        else:
            current_tags = s3.get_object_tagging(Bucket=bucket, Key=obj).get('TagSet')
    except is_boto3_error_code('NoSuchTagSet'):
        return {}
    except is_boto3_error_code('NoSuchTagSetError'):  # pylint: disable=duplicate-except
        return {}

    return boto3_tag_list_to_ansible_dict(current_tags)


@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_object_tagging(s3, bucket, obj, tags):
    s3.put_object_tagging(Bucket=bucket, Key=obj, Tagging={'TagSet': ansible_dict_to_boto3_tag_list(tags)})


@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def delete_object_tagging(s3, bucket, obj):
    s3.delete_object_tagging(Bucket=bucket, Key=obj)


def wait_tags_are_applied(module, s3, bucket, obj, expected_tags_dict, version=None):
    for dummy in range(0, 12):
        try:
            current_tags_dict = get_current_object_tags_dict(s3, bucket, obj, version)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to get object tags.")
        if current_tags_dict != expected_tags_dict:
            time.sleep(5)
        else:
            return current_tags_dict

    module.fail_json(msg="Object tags failed to apply in the expected time.",
                     requested_tags=expected_tags_dict, live_tags=current_tags_dict)


def ensure_tags(client, module, bucket, obj):
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    changed = False

    try:
        current_tags_dict = get_current_object_tags_dict(client, bucket, obj)
    except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS):
        module.warn("GetObjectTagging is not implemented by your storage provider. Set the permission parameters to the empty list to avoid this warning.")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get object tags.")
    else:
        if tags is not None:
            if not purge_tags:
                # Ensure existing tags that aren't updated by desired tags remain
                current_copy = current_tags_dict.copy()
                current_copy.update(tags)
                tags = current_copy
            if current_tags_dict != tags:
                if tags:
                    try:
                        put_object_tagging(client, bucket, obj, tags)
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to update object tags.")
                else:
                    if purge_tags:
                        try:
                            delete_object_tagging(client, bucket, obj)
                        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                            module.fail_json_aws(e, msg="Failed to delete object tags.")
                current_tags_dict = wait_tags_are_applied(module, client, bucket, obj, tags)
                changed = True
    return current_tags_dict, changed


def main():
    # Beware: this module uses an action plugin (plugins/action/s3_object.py)
    # so that src parameter can be either in 'files/' lookup path on the
    # controller, *or* on the remote host that the task is executed on.

    argument_spec = dict(
        bucket=dict(required=True),
        dest=dict(default=None, type='path'),
        encrypt=dict(default=True, type='bool'),
        encryption_mode=dict(choices=['AES256', 'aws:kms'], default='AES256'),
        expiry=dict(default=600, type='int', aliases=['expiration']),
        headers=dict(type='dict'),
        marker=dict(default=""),
        max_keys=dict(default=1000, type='int', no_log=False),
        metadata=dict(type='dict'),
        mode=dict(choices=['get', 'put', 'delete', 'create', 'geturl', 'getstr', 'delobj', 'list', 'copy'], required=True),
        sig_v4=dict(default=True, type='bool'),
        object=dict(),
        permission=dict(type='list', elements='str', default=['private']),
        version=dict(default=None),
        overwrite=dict(aliases=['force'], default='different'),
        prefix=dict(default=""),
        retries=dict(aliases=['retry'], type='int', default=0),
        dualstack=dict(default=False, type='bool'),
        ceph=dict(default=False, type='bool', aliases=['rgw']),
        src=dict(type='path'),
        content=dict(),
        content_base64=dict(),
        ignore_nonexistent_bucket=dict(default=False, type='bool'),
        encryption_kms_key_id=dict(),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
        copy_src=dict(type='dict', options=dict(bucket=dict(required=True), object=dict(required=True), version_id=dict())),
        validate_bucket_name=dict(type='bool', default=True),
    )

    required_if = [
        ['ceph', True, ['endpoint_url']],
        ['mode', 'put', ['object']],
        ['mode', 'get', ['dest', 'object']],
        ['mode', 'getstr', ['object']],
        ['mode', 'geturl', ['object']],
        ['mode', 'copy', ['copy_src']],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        mutually_exclusive=[['content', 'content_base64', 'src']],
    )

    bucket = module.params.get('bucket')
    encrypt = module.params.get('encrypt')
    expiry = module.params.get('expiry')
    dest = module.params.get('dest', '')
    headers = module.params.get('headers')
    marker = module.params.get('marker')
    max_keys = module.params.get('max_keys')
    metadata = module.params.get('metadata')
    mode = module.params.get('mode')
    obj = module.params.get('object')
    version = module.params.get('version')
    overwrite = module.params.get('overwrite')
    sig_v4 = module.params.get('sig_v4')
    prefix = module.params.get('prefix')
    retries = module.params.get('retries')
    endpoint_url = module.params.get('endpoint_url')
    dualstack = module.params.get('dualstack')
    ceph = module.params.get('ceph')
    src = module.params.get('src')
    content = module.params.get('content')
    content_base64 = module.params.get('content_base64')
    ignore_nonexistent_bucket = module.params.get('ignore_nonexistent_bucket')

    object_canned_acl = ["private", "public-read", "public-read-write", "aws-exec-read", "authenticated-read", "bucket-owner-read", "bucket-owner-full-control"]
    bucket_canned_acl = ["private", "public-read", "public-read-write", "authenticated-read"]

    if module.params.get('validate_bucket_name'):
        validate_bucket_name(module, bucket)

    if overwrite not in ['always', 'never', 'different', 'latest']:
        if module.boolean(overwrite):
            overwrite = 'always'
        else:
            overwrite = 'never'

    if overwrite == 'different' and not HAS_MD5:
        module.fail_json(msg='overwrite=different is unavailable: ETag calculation requires MD5 support')

    region, _ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if region in ('us-east-1', '', None):
        # default to US Standard region
        location = 'us-east-1'
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    if module.params.get('object'):
        obj = module.params['object']
        # If there is a top level object, do nothing - if the object starts with /
        # remove the leading character to maintain compatibility with Ansible versions < 2.4
        if obj.startswith('/'):
            obj = obj[1:]

    # Bucket deletion does not require obj.  Prevents ambiguity with delobj.
    if obj and mode == "delete":
        module.fail_json(msg='Parameter obj cannot be used with mode=delete')

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not endpoint_url and 'S3_URL' in os.environ:
        endpoint_url = os.environ['S3_URL']

    if dualstack and endpoint_url is not None and 'amazonaws.com' not in endpoint_url:
        module.fail_json(msg='dualstack only applies to AWS S3')

    # Look at endpoint_url and tweak connection settings
    # if connecting to RGW, Walrus or fakes3
    if endpoint_url:
        for key in ['validate_certs', 'security_token', 'profile_name']:
            aws_connect_kwargs.pop(key, None)
    s3 = get_s3_connection(module, aws_connect_kwargs, location, ceph, endpoint_url, sig_v4)

    validate = not ignore_nonexistent_bucket

    # check if bucket exists, if yes, check if ACL is disabled
    acl_disabled = False
    exists = bucket_check(module, s3, bucket)
    if exists:
        try:
            ownership_controls = s3.get_bucket_ownership_controls(Bucket=bucket)['OwnershipControls']
            if ownership_controls.get('Rules'):
                object_ownership = ownership_controls['Rules'][0]['ObjectOwnership']
                if object_ownership == 'BucketOwnerEnforced':
                    acl_disabled = True
        # if bucket ownership controls are not found
        except botocore.exceptions.ClientError:
            pass

    # separate types of ACLs
    if not acl_disabled:
        bucket_acl = [acl for acl in module.params.get('permission') if acl in bucket_canned_acl]
        object_acl = [acl for acl in module.params.get('permission') if acl in object_canned_acl]
        error_acl = [acl for acl in module.params.get('permission') if acl not in bucket_canned_acl and acl not in object_canned_acl]
        if error_acl:
            module.fail_json(msg='Unknown permission specified: %s' % error_acl)

    # First, we check to see if the bucket exists, we get "bucket" returned.
    bucketrtn = bucket_check(module, s3, bucket, validate=validate)

    if validate and mode not in ('create', 'put', 'delete', 'copy') and not bucketrtn:
        module.fail_json(msg="Source bucket cannot be found.")

    if mode == 'get':
        keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        if keyrtn is False:
            if version:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

        if dest and path_check(dest) and overwrite != 'always':
            if overwrite == 'never':
                module.exit_json(msg="Local object already exists and overwrite is disabled.", changed=False)
            if overwrite == 'different' and etag_compare(module, s3, bucket, obj, version=version, local_file=dest):
                module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite=always parameter to force.", changed=False)
            if overwrite == 'latest' and is_local_object_latest(module, s3, bucket, obj, version=version, local_file=dest):
                module.exit_json(msg="Local object is latest, ignoreing. Use overwrite=always parameter to force.", changed=False)

        try:
            download_s3file(module, s3, bucket, obj, dest, retries, version=version)
        except Sigv4Required:
            s3 = get_s3_connection(module, aws_connect_kwargs, location, ceph, endpoint_url, sig_4=True)
            download_s3file(module, s3, bucket, obj, dest, retries, version=version)

    if mode == 'put':

        # if putting an object in a bucket yet to be created, acls for the bucket and/or the object may be specified
        # these were separated into the variables bucket_acl and object_acl above

        if content is None and content_base64 is None and src is None:
            module.fail_json(msg='Either content, content_base64 or src must be specified for PUT operations')
        if src is not None and not path_check(src):
            module.fail_json(msg='Local object "%s" does not exist for PUT operation' % (src))

        keyrtn = None
        if bucketrtn:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        else:
            # If the bucket doesn't exist we should create it.
            # only use valid bucket acls for create_bucket function
            module.params['permission'] = bucket_acl
            create_bucket(module, s3, bucket, location)

        # the content will be uploaded as a byte string, so we must encode it first
        bincontent = None
        if content is not None:
            bincontent = content.encode('utf-8')
        if content_base64 is not None:
            bincontent = base64.standard_b64decode(content_base64)

        if keyrtn and overwrite != 'always':
            if overwrite == 'never' or etag_compare(module, s3, bucket, obj, version=version, local_file=src, content=bincontent):
                # Return the download URL for the existing object and ensure tags are updated
                tags, tags_update = ensure_tags(s3, module, bucket, obj)
                get_download_url(module, s3, bucket, obj, expiry, tags, changed=tags_update)

        # only use valid object acls for the upload_s3file function
        if not acl_disabled:
            module.params['permission'] = object_acl
        upload_s3file(module, s3, bucket, obj, expiry, metadata, encrypt, headers, src=src, content=bincontent, acl_disabled=acl_disabled)

    # Delete an object from a bucket, not the entire bucket
    if mode == 'delobj':
        if obj is None:
            module.fail_json(msg="object parameter is required")
        if bucket:
            deletertn = delete_key(module, s3, bucket, obj)
            if deletertn is True:
                module.exit_json(msg="Object deleted from bucket %s." % bucket, changed=True)
        else:
            module.fail_json(msg="Bucket parameter is required.")

    # Delete an entire bucket, including all objects in the bucket
    if mode == 'delete':
        if bucket:
            deletertn = delete_bucket(module, s3, bucket)
            if deletertn is True:
                module.exit_json(msg="Bucket %s and all keys have been deleted." % bucket, changed=True)
        else:
            module.fail_json(msg="Bucket parameter is required.")

    # Support for listing a set of keys
    if mode == 'list':

        # If the bucket does not exist then bail out
        if not bucketrtn:
            module.fail_json(msg="Target bucket (%s) cannot be found" % bucket)

        list_keys(module, s3, bucket, prefix, marker, max_keys)

    # Need to research how to create directories without "populating" a key, so this should just do bucket creation for now.
    # WE SHOULD ENABLE SOME WAY OF CREATING AN EMPTY KEY TO CREATE "DIRECTORY" STRUCTURE, AWS CONSOLE DOES THIS.
    if mode == 'create':

        # if both creating a bucket and putting an object in it, acls for the bucket and/or the object may be specified
        # these were separated above into the variables bucket_acl and object_acl

        if bucket and not obj:
            if bucketrtn:
                module.exit_json(msg="Bucket already exists.", changed=False)
            else:
                # only use valid bucket acls when creating the bucket
                module.params['permission'] = bucket_acl
                module.exit_json(msg="Bucket created successfully", changed=create_bucket(module, s3, bucket, location))
        if bucket and obj:
            if obj.endswith('/'):
                dirobj = obj
            else:
                dirobj = obj + "/"
            if bucketrtn:
                if key_check(module, s3, bucket, dirobj):
                    module.exit_json(msg="Bucket %s and key %s already exists." % (bucket, obj), changed=False)
                else:
                    # setting valid object acls for the create_dirkey function
                    module.params['permission'] = object_acl
                    create_dirkey(module, s3, bucket, dirobj, encrypt, expiry)
            else:
                # only use valid bucket acls for the create_bucket function
                module.params['permission'] = bucket_acl
                create_bucket(module, s3, bucket, location)
                # only use valid object acls for the create_dirkey function
                module.params['permission'] = object_acl
                create_dirkey(module, s3, bucket, dirobj, encrypt, expiry)

    # Support for grabbing the time-expired URL for an object in S3/Walrus.
    if mode == 'geturl':
        if not bucket and not obj:
            module.fail_json(msg="Bucket and Object parameters must be set")

        keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        if keyrtn:
            tags = get_current_object_tags_dict(s3, bucket, obj, version=version)
            get_download_url(module, s3, bucket, obj, expiry, tags)
        else:
            module.fail_json(msg="Key %s does not exist." % obj)

    if mode == 'getstr':
        if bucket and obj:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
            if keyrtn:
                try:
                    download_s3str(module, s3, bucket, obj, version=version)
                except Sigv4Required:
                    s3 = get_s3_connection(module, aws_connect_kwargs, location, ceph, endpoint_url, sig_4=True)
                    download_s3str(module, s3, bucket, obj, version=version)
            elif version is not None:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

    if mode == 'copy':
        # if copying an object in a bucket yet to be created, acls for the bucket and/or the object may be specified
        # these were separated into the variables bucket_acl and object_acl above
        d_etag = None
        if bucketrtn:
            d_etag = get_etag(s3, bucket, obj)
        else:
            # If the bucket doesn't exist we should create it.
            # only use valid bucket acls for create_bucket function
            module.params['permission'] = bucket_acl
            create_bucket(module, s3, bucket, location)
        # only use valid object acls for the copy operation
        module.params['permission'] = object_acl
        copy_object_to_bucket(module, s3, bucket, obj, encrypt, metadata, validate, d_etag)

    module.exit_json(failed=False)


if __name__ == '__main__':
    main()

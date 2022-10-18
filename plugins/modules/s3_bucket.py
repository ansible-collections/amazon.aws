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


DOCUMENTATION = r'''
---
module: s3_bucket
version_added: 1.0.0
short_description: Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID
description:
  - Manage S3 buckets.
  - Compatible with AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID.
  - When using non-AWS services, I(endpoint_url) should be specified.
author:
  - Rob White (@wimnat)
  - Aubin Bikouo (@abikouo)
options:
  force:
    description:
      - When trying to delete a bucket, delete all keys (including versions and delete markers)
        in the bucket first (an S3 bucket must be empty for a successful deletion).
    type: bool
    default: false
  name:
    description:
      - Name of the S3 bucket.
    required: true
    type: str
  policy:
    description:
      - The JSON policy as a string. Set to the string C("null") to force the absence of a policy.
    type: json
  ceph:
    description:
      - Enable API compatibility with Ceph RGW.
      - It takes into account the S3 API subset working with Ceph in order to provide the same module
        behaviour where possible.
      - Requires I(endpoint_url) if I(ceph=true).
    aliases: ['rgw']
    type: bool
    default: false
  requester_pays:
    description:
      - With Requester Pays buckets, the requester instead of the bucket owner pays the cost
        of the request and the data download from the bucket.
    type: bool
  state:
    description:
      - Create or remove the S3 bucket.
    required: false
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  versioning:
    description:
      - Whether versioning is enabled or disabled (note that once versioning is enabled, it can only be suspended).
    type: bool
  encryption:
    description:
      - Describes the default server-side encryption to apply to new objects in the bucket.
        In order to remove the server-side encryption, the encryption needs to be set to 'none' explicitly.
    choices: [ 'none', 'AES256', 'aws:kms' ]
    type: str
  encryption_key_id:
    description: KMS master key ID to use for the default encryption. This parameter is allowed if I(encryption) is C(aws:kms). If
                 not specified then it will default to the AWS provided KMS key.
    type: str
  bucket_key_enabled:
    description:
      - Enable S3 Bucket Keys for SSE-KMS on new objects.
      - See the AWS documentation for more information
        U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html).
      - Bucket Key encryption is only supported if I(encryption=aws:kms).
    required: false
    type: bool
    version_added: 4.1.0
  public_access:
    description:
      - Configure public access block for S3 bucket.
      - This option cannot be used together with I(delete_public_access).
    suboptions:
      block_public_acls:
        description: Sets BlockPublicAcls value.
        type: bool
        default: False
      block_public_policy:
        description: Sets BlockPublicPolicy value.
        type: bool
        default: False
      ignore_public_acls:
        description: Sets IgnorePublicAcls value.
        type: bool
        default: False
      restrict_public_buckets:
        description: Sets RestrictPublicAcls value.
        type: bool
        default: False
    type: dict
    version_added: 1.3.0
  delete_public_access:
    description:
      - Delete public access block configuration from bucket.
      - This option cannot be used together with a I(public_access) definition.
    default: false
    type: bool
    version_added: 1.3.0
  object_ownership:
    description:
      - Allow bucket's ownership controls.
      - C(BucketOwnerEnforced) - ACLs are disabled and no longer affect access permissions to your
        bucket. Requests to set or update ACLs fail. However, requests to read ACLs are supported.
        Bucket owner has full ownership and control. Object writer no longer has full ownership and
        control.
      - C(BucketOwnerPreferred) - Objects uploaded to the bucket change ownership to the bucket owner
        if the objects are uploaded with the bucket-owner-full-control canned ACL.
      - C(ObjectWriter) - The uploading account will own the object
        if the object is uploaded with the bucket-owner-full-control canned ACL.
      - This option cannot be used together with a I(delete_object_ownership) definition.
      - C(BucketOwnerEnforced) has been added in version 3.2.0.
    choices: [ 'BucketOwnerEnforced', 'BucketOwnerPreferred', 'ObjectWriter' ]
    type: str
    version_added: 2.0.0
  delete_object_ownership:
    description:
      - Delete bucket's ownership controls.
      - This option cannot be used together with a I(object_ownership) definition.
    default: false
    type: bool
    version_added: 2.0.0
  acl:
    description:
      - The canned ACL to apply to the bucket.
      - If your bucket uses the bucket owner enforced setting for S3 Object Ownership,
        ACLs are disabled and no longer affect permissions.
    choices: [ 'private', 'public-read', 'public-read-write', 'authenticated-read' ]
    type: str
    version_added: 3.1.0
  validate_bucket_name:
    description:
      - Whether the bucket name should be validated to conform to AWS S3 naming rules.
      - On by default, this may be disabled for S3 backends that do not enforce these rules.
      - See https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
    type: bool
    version_added: 3.1.0
    default: True

extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
  - amazon.aws.boto3

notes:
  - If C(requestPayment), C(policy), C(tagging) or C(versioning)
    operations/API aren't implemented by the endpoint, module doesn't fail
    if each parameter satisfies the following condition.
    I(requester_pays) is C(False), I(policy), I(tags), and I(versioning) are C(None).
  - In release 5.0.0 the I(s3_url) parameter was merged into the I(endpoint_url) parameter,
    I(s3_url) remains as an alias for I(endpoint_url).
  - For Walrus I(endpoint_url) should be set to the FQDN of the endpoint with neither scheme nor path.
  - Support for the C(S3_URL) environment variable has been
    deprecated and will be removed in a release after 2024-12-01, please use the I(endpoint_url) parameter
    or the C(AWS_URL) environment variable.
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple S3 bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present

# Create a simple S3 bucket on Ceph Rados Gateway
- amazon.aws.s3_bucket:
    name: mys3bucket
    endpoint_url: http://your-ceph-rados-gateway-server.xxx
    ceph: true

# Remove an S3 bucket and any keys it contains
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: absent
    force: true

# Create a bucket, add a policy from a file, enable requester pays, enable versioning and tag
- amazon.aws.s3_bucket:
    name: mys3bucket
    policy: "{{ lookup('file','policy.json') }}"
    requester_pays: true
    versioning: true
    tags:
      example: tag1
      another: tag2

# Create a simple DigitalOcean Spaces bucket using their provided regional endpoint
- amazon.aws.s3_bucket:
    name: mydobucket
    endpoint_url: 'https://nyc3.digitaloceanspaces.com'

# Create a bucket with AES256 encryption
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "AES256"

# Create a bucket with aws:kms encryption, KMS key
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "aws:kms"
    encryption_key_id: "arn:aws:kms:us-east-1:1234/5678example"

# Create a bucket with aws:kms encryption, Bucket key
- amazon.aws.s3_bucket:
    name: mys3bucket
    bucket_key_enabled: true
    encryption: "aws:kms"

# Create a bucket with aws:kms encryption, default key
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "aws:kms"

# Create a bucket with public policy block configuration
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    public_access:
        block_public_acls: true
        ignore_public_acls: true
        ## keys == 'false' can be omitted, undefined keys defaults to 'false'
        # block_public_policy: false
        # restrict_public_buckets: false

# Delete public policy block from bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    delete_public_access: true

# Create a bucket with object ownership controls set to ObjectWriter
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    object_ownership: ObjectWriter

# Delete onwership controls from bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    delete_object_ownership: true

# Delete a bucket policy from bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    policy: "null"

# This example grants public-read to everyone on bucket using ACL
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    acl: public-read
'''

RETURN = r'''
encryption:
    description:
        - Server-side encryption of the objects in the S3 bucket.
    type: str
    returned: I(state=present)
    sample: ''
name:
    description: Name of the S3 bucket.
    type: str
    returned: I(state=present)
    sample: "2d3ce10a8210d36d6b4d23b822892074complex"
object_ownership:
    description: S3 bucket's ownership controls.
    type: str
    returned: I(state=present)
    sample: "BucketOwnerPreferred"
policy:
    description: S3 bucket's policy.
    type: dict
    returned: I(state=present)
    sample: {
        "Statement": [
            {
                "Action": "s3:GetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Resource": "arn:aws:s3:::2d3ce10a8210d36d6b4d23b822892074complex/*",
                "Sid": "AddPerm"
            }
        ],
        "Version": "2012-10-17"
    }
requester_pays:
    description:
        - Indicates that the requester was successfully charged for the request.
    type: str
    returned: I(state=present)
    sample: ''
tags:
    description: S3 bucket's tags.
    type: dict
    returned: I(state=present)
    sample: {
        "Tag1": "tag1",
        "Tag2": "tag2"
    }
versioning:
    description: S3 bucket's versioning configuration.
    type: dict
    returned: I(state=present)
    sample: {
        "MfaDelete": "Disabled",
        "Versioning": "Enabled"
    }
acl:
    description: S3 bucket's canned ACL.
    type: dict
    returned: I(state=present)
    sample: 'public-read'
'''

import json
import os
import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.basic import to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.urllib.parse import urlparse

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_conn
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict
from ansible_collections.amazon.aws.plugins.module_utils.s3 import validate_bucket_name


def create_or_update_bucket(s3_client, module, location):

    policy = module.params.get("policy")
    name = module.params.get("name")
    requester_pays = module.params.get("requester_pays")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    versioning = module.params.get("versioning")
    encryption = module.params.get("encryption")
    encryption_key_id = module.params.get("encryption_key_id")
    bucket_key_enabled = module.params.get("bucket_key_enabled")
    public_access = module.params.get("public_access")
    delete_public_access = module.params.get("delete_public_access")
    delete_object_ownership = module.params.get("delete_object_ownership")
    object_ownership = module.params.get("object_ownership")
    acl = module.params.get("acl")
    changed = False
    result = {}

    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided: %s" % to_text(e))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        try:
            bucket_changed = create_bucket(s3_client, name, location)
            s3_client.get_waiter('bucket_exists').wait(Bucket=name)
            changed = changed or bucket_changed
        except botocore.exceptions.WaiterError as e:
            module.fail_json_aws(e, msg='An error occurred waiting for the bucket to become available')
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed while creating bucket")

    # Versioning
    try:
        versioning_status = get_bucket_versioning(s3_client, name)
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if versioning is not None:
            module.fail_json_aws(e, msg="Failed to get bucket versioning")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket versioning")
    else:
        if versioning is not None:
            required_versioning = None
            if versioning and versioning_status.get('Status') != "Enabled":
                required_versioning = 'Enabled'
            elif not versioning and versioning_status.get('Status') == "Enabled":
                required_versioning = 'Suspended'

            if required_versioning:
                try:
                    put_bucket_versioning(s3_client, name, required_versioning)
                    changed = True
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket versioning")

                versioning_status = wait_versioning_is_applied(module, s3_client, name, required_versioning)

        # This output format is there to ensure compatibility with previous versions of the module
        result['versioning'] = {
            'Versioning': versioning_status.get('Status', 'Disabled'),
            'MfaDelete': versioning_status.get('MFADelete', 'Disabled'),
        }

    # Requester pays
    try:
        requester_pays_status = get_bucket_request_payment(s3_client, name)
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if requester_pays is not None:
            module.fail_json_aws(e, msg="Failed to get bucket request payment")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket request payment")
    else:
        if requester_pays is not None:
            payer = 'Requester' if requester_pays else 'BucketOwner'
            if requester_pays_status != payer:
                put_bucket_request_payment(s3_client, name, payer)
                requester_pays_status = wait_payer_is_applied(module, s3_client, name, payer, should_fail=False)
                if requester_pays_status is None:
                    # We have seen that it happens quite a lot of times that the put request was not taken into
                    # account, so we retry one more time
                    put_bucket_request_payment(s3_client, name, payer)
                    requester_pays_status = wait_payer_is_applied(module, s3_client, name, payer, should_fail=True)
                changed = True

        result['requester_pays'] = requester_pays

    # Policy
    try:
        current_policy = get_bucket_policy(s3_client, name)
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if policy is not None:
            module.fail_json_aws(e, msg="Failed to get bucket policy")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket policy")
    else:
        if policy is not None:
            if isinstance(policy, string_types):
                policy = json.loads(policy)

            if not policy and current_policy:
                try:
                    delete_bucket_policy(s3_client, name)
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to delete bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy)
                changed = True
            elif compare_policies(current_policy, policy):
                try:
                    put_bucket_policy(s3_client, name, policy)
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy, should_fail=False)
                if current_policy is None:
                    # As for request payement, it happens quite a lot of times that the put request was not taken into
                    # account, so we retry one more time
                    put_bucket_policy(s3_client, name, policy)
                    current_policy = wait_policy_is_applied(module, s3_client, name, policy, should_fail=True)
                changed = True

        result['policy'] = current_policy

    # Tags
    try:
        current_tags_dict = get_current_bucket_tags_dict(s3_client, name)
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if tags is not None:
            module.fail_json_aws(e, msg="Failed to get bucket tags")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket tags")
    else:
        if tags is not None:
            # Tags are always returned as text
            tags = dict((to_text(k), to_text(v)) for k, v in tags.items())
            if not purge_tags:
                # Ensure existing tags that aren't updated by desired tags remain
                current_copy = current_tags_dict.copy()
                current_copy.update(tags)
                tags = current_copy
            if current_tags_dict != tags:
                if tags:
                    try:
                        put_bucket_tagging(s3_client, name, tags)
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to update bucket tags")
                else:
                    if purge_tags:
                        try:
                            delete_bucket_tagging(s3_client, name)
                        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                            module.fail_json_aws(e, msg="Failed to delete bucket tags")
                current_tags_dict = wait_tags_are_applied(module, s3_client, name, tags)
                changed = True

        result['tags'] = current_tags_dict

    # Encryption
    try:
        current_encryption = get_bucket_encryption(s3_client, name)
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if encryption is not None:
            module.fail_json_aws(e, msg="Failed to get bucket encryption settings")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket encryption settings")
    else:
        if encryption is not None:
            current_encryption_algorithm = current_encryption.get('SSEAlgorithm') if current_encryption else None
            current_encryption_key = current_encryption.get('KMSMasterKeyID') if current_encryption else None
            if encryption == 'none':
                if current_encryption_algorithm is not None:
                    try:
                        delete_bucket_encryption(s3_client, name)
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to delete bucket encryption")
                    current_encryption = wait_encryption_is_applied(module, s3_client, name, None)
                    changed = True
            else:
                if (encryption != current_encryption_algorithm) or (encryption == 'aws:kms' and current_encryption_key != encryption_key_id):
                    expected_encryption = {'SSEAlgorithm': encryption}
                    if encryption == 'aws:kms' and encryption_key_id is not None:
                        expected_encryption.update({'KMSMasterKeyID': encryption_key_id})
                    current_encryption = put_bucket_encryption_with_retry(module, s3_client, name, expected_encryption)
                    changed = True

        if bucket_key_enabled is not None:
            current_encryption_algorithm = current_encryption.get('SSEAlgorithm') if current_encryption else None
            if current_encryption_algorithm == 'aws:kms':
                if get_bucket_key(s3_client, name) != bucket_key_enabled:
                    if bucket_key_enabled:
                        expected_encryption = True
                    else:
                        expected_encryption = False
                    current_encryption = put_bucket_key_with_retry(module, s3_client, name, expected_encryption)
                    changed = True
        result['encryption'] = current_encryption
    # Public access clock configuration
    current_public_access = {}

    try:
        current_public_access = get_bucket_public_access(s3_client, name)
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if public_access is not None:
            module.fail_json_aws(e, msg="Failed to get bucket public access configuration")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket public access configuration")
    else:
        # -- Create / Update public access block
        if public_access is not None:
            camel_public_block = snake_dict_to_camel_dict(public_access, capitalize_first=True)

            if current_public_access == camel_public_block:
                result['public_access_block'] = current_public_access
            else:
                put_bucket_public_access(s3_client, name, camel_public_block)
                changed = True
                result['public_access_block'] = camel_public_block

        # -- Delete public access block
        if delete_public_access:
            if current_public_access == {}:
                result['public_access_block'] = current_public_access
            else:
                delete_bucket_public_access(s3_client, name)
                changed = True
                result['public_access_block'] = {}

    # -- Bucket ownership
    try:
        bucket_ownership = get_bucket_ownership_cntrl(s3_client, name)
        result['object_ownership'] = bucket_ownership
    except KeyError as e:
        # Some non-AWS providers appear to return policy documents that aren't
        # compatible with AWS, cleanly catch KeyError so users can continue to use
        # other features.
        if delete_object_ownership or object_ownership is not None:
            module.fail_json_aws(e, msg="Failed to get bucket object ownership settings")
    except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
        if delete_object_ownership or object_ownership is not None:
            module.fail_json_aws(e, msg="Failed to get bucket object ownership settings")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket object ownership settings")
    else:
        if delete_object_ownership:
            # delete S3 buckect ownership
            if bucket_ownership is not None:
                delete_bucket_ownership(s3_client, name)
                changed = True
                result['object_ownership'] = None
        elif object_ownership is not None:
            # update S3 bucket ownership
            if bucket_ownership != object_ownership:
                put_bucket_ownership(s3_client, name, object_ownership)
                changed = True
                result['object_ownership'] = object_ownership

    # -- Bucket ACL
    if acl:
        try:
            s3_client.put_bucket_acl(Bucket=name, ACL=acl)
            result['acl'] = acl
            changed = True
        except KeyError as e:
            # Some non-AWS providers appear to return policy documents that aren't
            # compatible with AWS, cleanly catch KeyError so users can continue to use
            # other features.
            module.fail_json_aws(e, msg="Failed to get bucket acl block")
        except is_boto3_error_code(['NotImplemented', 'XNotImplemented']) as e:
            module.fail_json_aws(e, msg="Failed to update bucket ACL")
        except is_boto3_error_code('AccessDenied') as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Access denied trying to update bucket ACL")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to update bucket ACL")

    # Module exit
    module.exit_json(changed=changed, name=name, **result)


def bucket_exists(s3_client, bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        bucket_exists = True
    except is_boto3_error_code('404'):
        bucket_exists = False
    return bucket_exists


@AWSRetry.exponential_backoff(max_delay=120)
def create_bucket(s3_client, bucket_name, location):
    try:
        configuration = {}
        if location not in ('us-east-1', None):
            configuration['LocationConstraint'] = location
        if len(configuration) > 0:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=configuration)
        else:
            s3_client.create_bucket(Bucket=bucket_name)
        return True
    except is_boto3_error_code('BucketAlreadyOwnedByYou'):
        # We should never get here since we check the bucket presence before calling the create_or_update_bucket
        # method. However, the AWS Api sometimes fails to report bucket presence, so we catch this exception
        return False


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_tagging(s3_client, bucket_name, tags):
    s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': ansible_dict_to_boto3_tag_list(tags)})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_policy(s3_client, bucket_name, policy):
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def delete_bucket_policy(s3_client, bucket_name):
    s3_client.delete_bucket_policy(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def get_bucket_policy(s3_client, bucket_name):
    try:
        current_policy = json.loads(s3_client.get_bucket_policy(Bucket=bucket_name).get('Policy'))
    except is_boto3_error_code('NoSuchBucketPolicy'):
        return None

    return current_policy


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_request_payment(s3_client, bucket_name, payer):
    s3_client.put_bucket_request_payment(Bucket=bucket_name, RequestPaymentConfiguration={'Payer': payer})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def get_bucket_request_payment(s3_client, bucket_name):
    return s3_client.get_bucket_request_payment(Bucket=bucket_name).get('Payer')


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def get_bucket_versioning(s3_client, bucket_name):
    return s3_client.get_bucket_versioning(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_versioning(s3_client, bucket_name, required_versioning):
    s3_client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': required_versioning})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def get_bucket_encryption(s3_client, bucket_name):
    try:
        result = s3_client.get_bucket_encryption(Bucket=bucket_name)
        return result.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])[0].get('ApplyServerSideEncryptionByDefault')
    except is_boto3_error_code('ServerSideEncryptionConfigurationNotFoundError'):
        return None
    except (IndexError, KeyError):
        return None


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def get_bucket_key(s3_client, bucket_name):
    try:
        result = s3_client.get_bucket_encryption(Bucket=bucket_name)
        return result.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])[0].get('BucketKeyEnabled')
    except is_boto3_error_code('ServerSideEncryptionConfigurationNotFoundError'):
        return None
    except (IndexError, KeyError):
        return None


def put_bucket_encryption_with_retry(module, s3_client, name, expected_encryption):
    max_retries = 3
    for retries in range(1, max_retries + 1):
        try:
            put_bucket_encryption(s3_client, name, expected_encryption)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to set bucket encryption")
        current_encryption = wait_encryption_is_applied(module, s3_client, name, expected_encryption,
                                                        should_fail=(retries == max_retries), retries=5)
        if current_encryption == expected_encryption:
            return current_encryption

    # We shouldn't get here, the only time this should happen is if
    # current_encryption != expected_encryption and retries == max_retries
    # Which should use module.fail_json and fail out first.
    module.fail_json(msg='Failed to apply bucket encryption',
                     current=current_encryption, expected=expected_encryption, retries=retries)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_encryption(s3_client, bucket_name, encryption):
    server_side_encryption_configuration = {'Rules': [{'ApplyServerSideEncryptionByDefault': encryption}]}
    s3_client.put_bucket_encryption(Bucket=bucket_name, ServerSideEncryptionConfiguration=server_side_encryption_configuration)


def put_bucket_key_with_retry(module, s3_client, name, expected_encryption):
    max_retries = 3
    for retries in range(1, max_retries + 1):
        try:
            put_bucket_key(s3_client, name, expected_encryption)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to set bucket Key")
        current_encryption = wait_bucket_key_is_applied(module, s3_client, name, expected_encryption,
                                                        should_fail=(retries == max_retries), retries=5)
        if current_encryption == expected_encryption:
            return current_encryption

    # We shouldn't get here, the only time this should happen is if
    # current_encryption != expected_encryption and retries == max_retries
    # Which should use module.fail_json and fail out first.
    module.fail_json(msg='Failed to set bucket key',
                     current=current_encryption, expected=expected_encryption, retries=retries)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_key(s3_client, bucket_name, encryption):
    # server_side_encryption_configuration ={'Rules': [{'BucketKeyEnabled': encryption}]}
    encryption_status = s3_client.get_bucket_encryption(Bucket=bucket_name)
    encryption_status['ServerSideEncryptionConfiguration']['Rules'][0]['BucketKeyEnabled'] = encryption
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration=encryption_status[
            'ServerSideEncryptionConfiguration']
    )


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def delete_bucket_tagging(s3_client, bucket_name):
    s3_client.delete_bucket_tagging(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def delete_bucket_encryption(s3_client, bucket_name):
    s3_client.delete_bucket_encryption(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=240, catch_extra_error_codes=['OperationAborted'])
def delete_bucket(s3_client, bucket_name):
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
    except is_boto3_error_code('NoSuchBucket'):
        # This means bucket should have been in a deleting state when we checked it existence
        # We just ignore the error
        pass


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_public_access(s3_client, bucket_name, public_acces):
    '''
    Put new public access block to S3 bucket
    '''
    s3_client.put_public_access_block(Bucket=bucket_name, PublicAccessBlockConfiguration=public_acces)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def delete_bucket_public_access(s3_client, bucket_name):
    '''
    Delete public access block from S3 bucket
    '''
    s3_client.delete_public_access_block(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def delete_bucket_ownership(s3_client, bucket_name):
    '''
    Delete bucket ownership controls from S3 bucket
    '''
    s3_client.delete_bucket_ownership_controls(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket', 'OperationAborted'])
def put_bucket_ownership(s3_client, bucket_name, target):
    '''
    Put bucket ownership controls for S3 bucket
    '''
    s3_client.put_bucket_ownership_controls(
        Bucket=bucket_name,
        OwnershipControls={
            'Rules': [{'ObjectOwnership': target}]
        })


def wait_policy_is_applied(module, s3_client, bucket_name, expected_policy, should_fail=True):
    for dummy in range(0, 12):
        try:
            current_policy = get_bucket_policy(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket policy")

        if compare_policies(current_policy, expected_policy):
            time.sleep(5)
        else:
            return current_policy
    if should_fail:
        module.fail_json(msg="Bucket policy failed to apply in the expected time",
                         requested_policy=expected_policy, live_policy=current_policy)
    else:
        return None


def wait_payer_is_applied(module, s3_client, bucket_name, expected_payer, should_fail=True):
    for dummy in range(0, 12):
        try:
            requester_pays_status = get_bucket_request_payment(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket request payment")
        if requester_pays_status != expected_payer:
            time.sleep(5)
        else:
            return requester_pays_status
    if should_fail:
        module.fail_json(msg="Bucket request payment failed to apply in the expected time",
                         requested_status=expected_payer, live_status=requester_pays_status)
    else:
        return None


def wait_encryption_is_applied(module, s3_client, bucket_name, expected_encryption, should_fail=True, retries=12):
    for dummy in range(0, retries):
        try:
            encryption = get_bucket_encryption(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated encryption for bucket")
        if encryption != expected_encryption:
            time.sleep(5)
        else:
            return encryption

    if should_fail:
        module.fail_json(msg="Bucket encryption failed to apply in the expected time",
                         requested_encryption=expected_encryption, live_encryption=encryption)

    return encryption


def wait_bucket_key_is_applied(module, s3_client, bucket_name, expected_encryption, should_fail=True, retries=12):
    for dummy in range(0, retries):
        try:
            encryption = get_bucket_key(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated encryption for bucket")
        if encryption != expected_encryption:
            time.sleep(5)
        else:
            return encryption

    if should_fail:
        module.fail_json(msg="Bucket Key failed to apply in the expected time",
                         requested_encryption=expected_encryption, live_encryption=encryption)
    return encryption


def wait_versioning_is_applied(module, s3_client, bucket_name, required_versioning):
    for dummy in range(0, 24):
        try:
            versioning_status = get_bucket_versioning(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated versioning for bucket")
        if versioning_status.get('Status') != required_versioning:
            time.sleep(8)
        else:
            return versioning_status
    module.fail_json(msg="Bucket versioning failed to apply in the expected time",
                     requested_versioning=required_versioning, live_versioning=versioning_status)


def wait_tags_are_applied(module, s3_client, bucket_name, expected_tags_dict):
    for dummy in range(0, 12):
        try:
            current_tags_dict = get_current_bucket_tags_dict(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket policy")
        if current_tags_dict != expected_tags_dict:
            time.sleep(5)
        else:
            return current_tags_dict
    module.fail_json(msg="Bucket tags failed to apply in the expected time",
                     requested_tags=expected_tags_dict, live_tags=current_tags_dict)


def get_current_bucket_tags_dict(s3_client, bucket_name):
    try:
        current_tags = s3_client.get_bucket_tagging(Bucket=bucket_name).get('TagSet')
    except is_boto3_error_code('NoSuchTagSet'):
        return {}
    # The Ceph S3 API returns a different error code to AWS
    except is_boto3_error_code('NoSuchTagSetError'):  # pylint: disable=duplicate-except
        return {}

    return boto3_tag_list_to_ansible_dict(current_tags)


def get_bucket_public_access(s3_client, bucket_name):
    '''
    Get current bucket public access block
    '''
    try:
        bucket_public_access_block = s3_client.get_public_access_block(Bucket=bucket_name)
        return bucket_public_access_block['PublicAccessBlockConfiguration']
    except is_boto3_error_code('NoSuchPublicAccessBlockConfiguration'):
        return {}


def get_bucket_ownership_cntrl(s3_client, bucket_name):
    '''
    Get current bucket public access block
    '''
    try:
        bucket_ownership = s3_client.get_bucket_ownership_controls(Bucket=bucket_name)
        return bucket_ownership['OwnershipControls']['Rules'][0]['ObjectOwnership']
    except is_boto3_error_code(['OwnershipControlsNotFoundError', 'NoSuchOwnershipControls']):
        return None


def paginated_list(s3_client, **pagination_params):
    pg = s3_client.get_paginator('list_objects_v2')
    for page in pg.paginate(**pagination_params):
        yield [data['Key'] for data in page.get('Contents', [])]


def paginated_versions_list(s3_client, **pagination_params):
    try:
        pg = s3_client.get_paginator('list_object_versions')
        for page in pg.paginate(**pagination_params):
            # We have to merge the Versions and DeleteMarker lists here, as DeleteMarkers can still prevent a bucket deletion
            yield [(data['Key'], data['VersionId']) for data in (page.get('Versions', []) + page.get('DeleteMarkers', []))]
    except is_boto3_error_code('NoSuchBucket'):
        yield []


def destroy_bucket(s3_client, module):

    force = module.params.get("force")
    name = module.params.get("name")
    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided: %s" % to_text(e))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        module.exit_json(changed=False)

    if force:
        # if there are contents then we need to delete them (including versions) before we can delete the bucket
        try:
            for key_version_pairs in paginated_versions_list(s3_client, Bucket=name):
                formatted_keys = [{'Key': key, 'VersionId': version} for key, version in key_version_pairs]
                for fk in formatted_keys:
                    # remove VersionId from cases where they are `None` so that
                    # unversioned objects are deleted using `DeleteObject`
                    # rather than `DeleteObjectVersion`, improving backwards
                    # compatibility with older IAM policies.
                    if not fk.get('VersionId'):
                        fk.pop('VersionId')

                if formatted_keys:
                    resp = s3_client.delete_objects(Bucket=name, Delete={'Objects': formatted_keys})
                    if resp.get('Errors'):
                        module.fail_json(
                            msg='Could not empty bucket before deleting. Could not delete objects: {0}'.format(
                                ', '.join([k['Key'] for k in resp['Errors']])
                            ),
                            errors=resp['Errors'], response=resp
                        )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed while deleting bucket")

    try:
        delete_bucket(s3_client, name)
        s3_client.get_waiter('bucket_not_exists').wait(Bucket=name, WaiterConfig=dict(Delay=5, MaxAttempts=60))
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg='An error occurred waiting for the bucket to be deleted.')
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete bucket")

    module.exit_json(changed=True)


def is_fakes3(endpoint_url):
    """ Return True if endpoint_url has scheme fakes3:// """
    if endpoint_url is not None:
        return urlparse(endpoint_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def get_s3_client(module, aws_connect_kwargs, location, ceph, endpoint_url):
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
    return boto3_conn(**params)


def main():

    argument_spec = dict(
        force=dict(default=False, type='bool'),
        policy=dict(type='json'),
        name=dict(required=True),
        requester_pays=dict(type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
        versioning=dict(type='bool'),
        ceph=dict(default=False, type='bool', aliases=['rgw']),
        encryption=dict(choices=['none', 'AES256', 'aws:kms']),
        encryption_key_id=dict(),
        bucket_key_enabled=dict(type='bool'),
        public_access=dict(type='dict', options=dict(
            block_public_acls=dict(type='bool', default=False),
            ignore_public_acls=dict(type='bool', default=False),
            block_public_policy=dict(type='bool', default=False),
            restrict_public_buckets=dict(type='bool', default=False))),
        delete_public_access=dict(type='bool', default=False),
        object_ownership=dict(type='str', choices=['BucketOwnerEnforced', 'BucketOwnerPreferred', 'ObjectWriter']),
        delete_object_ownership=dict(type='bool', default=False),
        acl=dict(type='str', choices=['private', 'public-read', 'public-read-write', 'authenticated-read']),
        validate_bucket_name=dict(type='bool', default=True),
    )

    required_by = dict(
        encryption_key_id=('encryption',),
    )

    mutually_exclusive = [
        ['public_access', 'delete_public_access'],
        ['delete_object_ownership', 'object_ownership']
    ]

    required_if = [
        ['ceph', True, ['endpoint_url']],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_by=required_by,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive
    )

    region, _ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if module.params.get('validate_bucket_name'):
        validate_bucket_name(module, module.params["name"])

    if region in ('us-east-1', '', None):
        # default to US Standard region
        location = 'us-east-1'
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    endpoint_url = module.params.get('endpoint_url')
    ceph = module.params.get('ceph')

    # Look at endpoint_url and tweak connection settings
    # allow eucarc environment variables to be used if ansible vars aren't set
    if not endpoint_url and 'S3_URL' in os.environ:
        endpoint_url = os.environ['S3_URL']
        module.deprecate(
            "Support for the 'S3_URL' environment variable has been "
            "deprecated.  We recommend using the 'endpoint_url' module "
            "parameter.  Alternatively, the 'AWS_URL' environment variable can"
            "be used instead.",
            date='2024-12-01', collection_name='amazon.aws',
        )

    # if connecting to Ceph RGW, Walrus or fakes3
    if endpoint_url:
        for key in ['validate_certs', 'security_token', 'profile_name']:
            aws_connect_kwargs.pop(key, None)
    s3_client = get_s3_client(module, aws_connect_kwargs, location, ceph, endpoint_url)

    if s3_client is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create s3 connection, no information available.')

    state = module.params.get("state")
    encryption = module.params.get("encryption")
    encryption_key_id = module.params.get("encryption_key_id")

    # Parameter validation
    if encryption_key_id is not None and encryption != 'aws:kms':
        module.fail_json(msg="Only 'aws:kms' is a valid option for encryption parameter when you specify encryption_key_id.")

    if state == 'present':
        create_or_update_bucket(s3_client, module, location)
    elif state == 'absent':
        destroy_bucket(s3_client, module)


if __name__ == '__main__':
    main()

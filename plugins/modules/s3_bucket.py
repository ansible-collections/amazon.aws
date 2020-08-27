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
module: s3_bucket
version_added: 1.0.0
short_description: Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID
description:
    - Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  force:
    description:
      - When trying to delete a bucket, delete all keys (including versions and delete markers)
        in the bucket first (an s3 bucket must be empty for a successful deletion)
    type: bool
    default: 'no'
  name:
    description:
      - Name of the s3 bucket
    required: true
    type: str
  policy:
    description:
      - The JSON policy as a string.
    type: json
  s3_url:
    description:
      - S3 URL endpoint for usage with DigitalOcean, Ceph, Eucalyptus and fakes3 etc.
      - Assumes AWS if not specified.
      - For Walrus, use FQDN of the endpoint without scheme nor path.
    aliases: [ S3_URL ]
    type: str
  ceph:
    description:
      - Enable API compatibility with Ceph. It takes into account the S3 API subset working
        with Ceph in order to provide the same module behaviour where possible.
    type: bool
  requester_pays:
    description:
      - With Requester Pays buckets, the requester instead of the bucket owner pays the cost
        of the request and the data download from the bucket.
    type: bool
    default: False
  state:
    description:
      - Create or remove the s3 bucket
    required: false
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  tags:
    description:
      - tags dict to apply to bucket
    type: dict
  purge_tags:
    description:
      - whether to remove tags that aren't present in the C(tags) parameter
    type: bool
    default: True
  versioning:
    description:
      - Whether versioning is enabled or disabled (note that once versioning is enabled, it can only be suspended)
    type: bool
  encryption:
    description:
      - Describes the default server-side encryption to apply to new objects in the bucket.
        In order to remove the server-side encryption, the encryption needs to be set to 'none' explicitly.
    choices: [ 'none', 'AES256', 'aws:kms' ]
    type: str
  encryption_key_id:
    description: KMS master key ID to use for the default encryption. This parameter is allowed if encryption is aws:kms. If
                 not specified then it will default to the AWS provided KMS key.
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

notes:
    - If C(requestPayment), C(policy), C(tagging) or C(versioning)
      operations/API aren't implemented by the endpoint, module doesn't fail
      if each parameter satisfies the following condition.
      I(requester_pays) is C(False), I(policy), I(tags), and I(versioning) are C(None).
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple s3 bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present

# Create a simple s3 bucket on Ceph Rados Gateway
- amazon.aws.s3_bucket:
    name: mys3bucket
    s3_url: http://your-ceph-rados-gateway-server.xxx
    ceph: true

# Remove an s3 bucket and any keys it contains
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: absent
    force: yes

# Create a bucket, add a policy from a file, enable requester pays, enable versioning and tag
- amazon.aws.s3_bucket:
    name: mys3bucket
    policy: "{{ lookup('file','policy.json') }}"
    requester_pays: yes
    versioning: yes
    tags:
      example: tag1
      another: tag2

# Create a simple DigitalOcean Spaces bucket using their provided regional endpoint
- amazon.aws.s3_bucket:
    name: mydobucket
    s3_url: 'https://nyc3.digitaloceanspaces.com'

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

# Create a bucket with aws:kms encryption, default key
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "aws:kms"
'''

import json
import os
import time

try:
    from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError, WaiterError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.basic import to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.urllib.parse import urlparse

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.core import is_boto3_error_code
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ..module_utils.ec2 import boto3_conn
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ..module_utils.ec2 import compare_policies
from ..module_utils.ec2 import get_aws_connection_info


def create_or_update_bucket(s3_client, module, location):

    policy = module.params.get("policy")
    name = module.params.get("name")
    requester_pays = module.params.get("requester_pays")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    versioning = module.params.get("versioning")
    encryption = module.params.get("encryption")
    encryption_key_id = module.params.get("encryption_key_id")
    changed = False
    result = {}

    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided: %s" % to_text(e))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        try:
            bucket_changed = create_bucket(s3_client, name, location)
            s3_client.get_waiter('bucket_exists').wait(Bucket=name)
            changed = changed or bucket_changed
        except WaiterError as e:
            module.fail_json_aws(e, msg='An error occurred waiting for the bucket to become available')
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed while creating bucket")

    # Versioning
    try:
        versioning_status = get_bucket_versioning(s3_client, name)
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket versioning")
    except ClientError as exp:
        if exp.response['Error']['Code'] != 'NotImplemented' or versioning is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket versioning")
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
                except (BotoCoreError, ClientError) as e:
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
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket request payment")
    except ClientError as exp:
        if exp.response['Error']['Code'] not in ('NotImplemented', 'XNotImplemented') or requester_pays:
            module.fail_json_aws(exp, msg="Failed to get bucket request payment")
    else:
        if requester_pays:
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
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket policy")
    except ClientError as exp:
        if exp.response['Error']['Code'] != 'NotImplemented' or policy is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket policy")
    else:
        if policy is not None:
            if isinstance(policy, string_types):
                policy = json.loads(policy)

            if not policy and current_policy:
                try:
                    delete_bucket_policy(s3_client, name)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to delete bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy)
                changed = True
            elif compare_policies(current_policy, policy):
                try:
                    put_bucket_policy(s3_client, name, policy)
                except (BotoCoreError, ClientError) as e:
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
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket tags")
    except ClientError as exp:
        if exp.response['Error']['Code'] not in ('NotImplemented', 'XNotImplemented') or tags is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket tags")
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
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to update bucket tags")
                else:
                    if purge_tags:
                        try:
                            delete_bucket_tagging(s3_client, name)
                        except (BotoCoreError, ClientError) as e:
                            module.fail_json_aws(e, msg="Failed to delete bucket tags")
                current_tags_dict = wait_tags_are_applied(module, s3_client, name, tags)
                changed = True

        result['tags'] = current_tags_dict

    # Encryption
    try:
        current_encryption = get_bucket_encryption(s3_client, name)
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get bucket encryption")

    if encryption is not None:
        current_encryption_algorithm = current_encryption.get('SSEAlgorithm') if current_encryption else None
        current_encryption_key = current_encryption.get('KMSMasterKeyID') if current_encryption else None
        if encryption == 'none' and current_encryption_algorithm is not None:
            try:
                delete_bucket_encryption(s3_client, name)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Failed to delete bucket encryption")
            current_encryption = wait_encryption_is_applied(module, s3_client, name, None)
            changed = True
        elif encryption != 'none' and (encryption != current_encryption_algorithm) or (encryption == 'aws:kms' and current_encryption_key != encryption_key_id):
            expected_encryption = {'SSEAlgorithm': encryption}
            if encryption == 'aws:kms' and encryption_key_id is not None:
                expected_encryption.update({'KMSMasterKeyID': encryption_key_id})
            current_encryption = put_bucket_encryption_with_retry(module, s3_client, name, expected_encryption)
            changed = True

        result['encryption'] = current_encryption

    module.exit_json(changed=changed, name=name, **result)


def bucket_exists(s3_client, bucket_name):
    # head_bucket appeared to be really inconsistent, so we use list_buckets instead,
    # and loop over all the buckets, even if we know it's less performant :(
    all_buckets = s3_client.list_buckets(Bucket=bucket_name)['Buckets']
    return any(bucket['Name'] == bucket_name for bucket in all_buckets)


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
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyOwnedByYou':
            # We should never get there since we check the bucket presence before calling the create_or_update_bucket
            # method. However, the AWS Api sometimes fails to report bucket presence, so we catch this exception
            return False
        else:
            raise e


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
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            current_policy = None
        else:
            raise e
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
    if not hasattr(s3_client, "get_bucket_encryption"):
        return None

    try:
        result = s3_client.get_bucket_encryption(Bucket=bucket_name)
        return result.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])[0].get('ApplyServerSideEncryptionByDefault')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
            return None
        else:
            raise e
    except (IndexError, KeyError):
        return None


def put_bucket_encryption_with_retry(module, s3_client, name, expected_encryption):
    max_retries = 3
    for retries in range(1, max_retries + 1):
        try:
            put_bucket_encryption(s3_client, name, expected_encryption)
        except (BotoCoreError, ClientError) as e:
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
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            # This means bucket should have been in a deleting state when we checked it existence
            # We just ignore the error
            pass
        else:
            raise e


def wait_policy_is_applied(module, s3_client, bucket_name, expected_policy, should_fail=True):
    for dummy in range(0, 12):
        try:
            current_policy = get_bucket_policy(s3_client, bucket_name)
        except (ClientError, BotoCoreError) as e:
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
        except (BotoCoreError, ClientError) as e:
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
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated encryption for bucket")
        if encryption != expected_encryption:
            time.sleep(5)
        else:
            return encryption

    if should_fail:
        module.fail_json(msg="Bucket encryption failed to apply in the expected time",
                         requested_encryption=expected_encryption, live_encryption=encryption)

    return encryption


def wait_versioning_is_applied(module, s3_client, bucket_name, required_versioning):
    for dummy in range(0, 24):
        try:
            versioning_status = get_bucket_versioning(s3_client, bucket_name)
        except (BotoCoreError, ClientError) as e:
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
        except (ClientError, BotoCoreError) as e:
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
    except EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided: %s" % to_text(e))
    except (BotoCoreError, ClientError) as e:
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
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed while deleting bucket")

    try:
        delete_bucket(s3_client, name)
        s3_client.get_waiter('bucket_not_exists').wait(Bucket=name, WaiterConfig=dict(Delay=5, MaxAttempts=60))
    except WaiterError as e:
        module.fail_json_aws(e, msg='An error occurred waiting for the bucket to be deleted.')
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete bucket")

    module.exit_json(changed=True)


def is_fakes3(s3_url):
    """ Return True if s3_url has scheme fakes3:// """
    if s3_url is not None:
        return urlparse(s3_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def get_s3_client(module, aws_connect_kwargs, location, ceph, s3_url):
    if s3_url and ceph:  # TODO - test this
        ceph = urlparse(s3_url)
        params = dict(module=module, conn_type='client', resource='s3', use_ssl=ceph.scheme == 'https', region=location, endpoint=s3_url, **aws_connect_kwargs)
    elif is_fakes3(s3_url):
        fakes3 = urlparse(s3_url)
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
        params = dict(module=module, conn_type='client', resource='s3', region=location, endpoint=s3_url, **aws_connect_kwargs)
    return boto3_conn(**params)


def main():

    argument_spec = dict(
        force=dict(default=False, type='bool'),
        policy=dict(type='json'),
        name=dict(required=True),
        requester_pays=dict(default=False, type='bool'),
        s3_url=dict(aliases=['S3_URL']),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=True),
        versioning=dict(type='bool'),
        ceph=dict(default=False, type='bool'),
        encryption=dict(choices=['none', 'AES256', 'aws:kms']),
        encryption_key_id=dict()
    )

    required_by = dict(
        encryption_key_id=('encryption',),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, required_by=required_by
    )

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if region in ('us-east-1', '', None):
        # default to US Standard region
        location = 'us-east-1'
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    s3_url = module.params.get('s3_url')
    ceph = module.params.get('ceph')

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not s3_url and 'S3_URL' in os.environ:
        s3_url = os.environ['S3_URL']

    if ceph and not s3_url:
        module.fail_json(msg='ceph flavour requires s3_url')

    # Look at s3_url and tweak connection settings
    # if connecting to Ceph RGW, Walrus or fakes3
    if s3_url:
        for key in ['validate_certs', 'security_token', 'profile_name']:
            aws_connect_kwargs.pop(key, None)
    s3_client = get_s3_client(module, aws_connect_kwargs, location, ceph, s3_url)

    if s3_client is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create s3 connection, no information from boto.')

    state = module.params.get("state")
    encryption = module.params.get("encryption")
    encryption_key_id = module.params.get("encryption_key_id")

    if not hasattr(s3_client, "get_bucket_encryption"):
        if encryption is not None:
            module.fail_json(msg="Using bucket encryption requires botocore version >= 1.7.41")

    # Parameter validation
    if encryption_key_id is not None and encryption != 'aws:kms':
        module.fail_json(msg="Only 'aws:kms' is a valid option for encryption parameter when you specify encryption_key_id.")

    if state == 'present':
        create_or_update_bucket(s3_client, module, location)
    elif state == 'absent':
        destroy_bucket(s3_client, module)


if __name__ == '__main__':
    main()

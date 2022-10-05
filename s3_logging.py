#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: s3_logging
version_added: 1.0.0
short_description: Manage logging facility of an s3 bucket in AWS
description:
    - Manage logging facility of an s3 bucket in AWS
author: Rob White (@wimnat)
options:
  name:
    description:
      - "Name of the s3 bucket."
    required: true
    type: str
  state:
    description:
      - "Enable or disable logging."
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  target_bucket:
    description:
      - "The bucket to log to. Required when state=present."
    type: str
  target_prefix:
    description:
      - "The prefix that should be prepended to the generated log files written to the target_bucket."
    default: ""
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Enable logging of s3 bucket mywebsite.com to s3 bucket mylogs
  community.aws.s3_logging:
    name: mywebsite.com
    target_bucket: mylogs
    target_prefix: logs/mywebsite.com
    state: present

- name: Remove logging on an s3 bucket
  community.aws.s3_logging:
    name: mywebsite.com
    state: absent

'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def compare_bucket_logging(bucket_logging, target_bucket, target_prefix):

    if not bucket_logging.get('LoggingEnabled', False):
        if target_bucket:
            return True
        return False

    logging = bucket_logging['LoggingEnabled']
    if logging['TargetBucket'] != target_bucket:
        return True
    if logging['TargetPrefix'] != target_prefix:
        return True
    return False


def verify_acls(connection, module, target_bucket):
    try:
        current_acl = connection.get_bucket_acl(aws_retry=True, Bucket=target_bucket)
        current_grants = current_acl['Grants']
    except is_boto3_error_code('NoSuchBucket'):
        module.fail_json(msg="Target Bucket '{0}' not found".format(target_bucket))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to fetch target bucket ACL")

    required_grant = {
        'Grantee': {
            'URI': "http://acs.amazonaws.com/groups/s3/LogDelivery",
            'Type': 'Group'
        },
        'Permission': 'FULL_CONTROL'
    }

    for grant in current_grants:
        if grant == required_grant:
            return False

    if module.check_mode:
        return True

    updated_acl = dict(current_acl)
    updated_grants = list(current_grants)
    updated_grants.append(required_grant)
    updated_acl['Grants'] = updated_grants
    del updated_acl['ResponseMetadata']
    try:
        connection.put_bucket_acl(aws_retry=True, Bucket=target_bucket, AccessControlPolicy=updated_acl)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update target bucket ACL to allow log delivery")

    return True


def enable_bucket_logging(connection, module):

    bucket_name = module.params.get("name")
    target_bucket = module.params.get("target_bucket")
    target_prefix = module.params.get("target_prefix")
    changed = False

    try:
        bucket_logging = connection.get_bucket_logging(aws_retry=True, Bucket=bucket_name)
    except is_boto3_error_code('NoSuchBucket'):
        module.fail_json(msg="Bucket '{0}' not found".format(bucket_name))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to fetch current logging status")

    try:
        changed |= verify_acls(connection, module, target_bucket)

        if not compare_bucket_logging(bucket_logging, target_bucket, target_prefix):
            bucket_logging = camel_dict_to_snake_dict(bucket_logging)
            module.exit_json(changed=changed, **bucket_logging)

        if module.check_mode:
            module.exit_json(changed=True)

        result = connection.put_bucket_logging(
            aws_retry=True,
            Bucket=bucket_name,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': target_bucket,
                    'TargetPrefix': target_prefix,
                }
            })

    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to enable bucket logging")

    result = camel_dict_to_snake_dict(result)
    module.exit_json(changed=True, **result)


def disable_bucket_logging(connection, module):

    bucket_name = module.params.get("name")
    changed = False

    try:
        bucket_logging = connection.get_bucket_logging(aws_retry=True, Bucket=bucket_name)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to fetch current logging status")

    if not compare_bucket_logging(bucket_logging, None, None):
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        response = AWSRetry.jittered_backoff(
            catch_extra_error_codes=['InvalidTargetBucketForLogging']
        )(connection.put_bucket_logging)(
            Bucket=bucket_name, BucketLoggingStatus={}
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to disable bucket logging")

    module.exit_json(changed=True)


def main():

    argument_spec = dict(
        name=dict(required=True),
        target_bucket=dict(required=False, default=None),
        target_prefix=dict(required=False, default=""),
        state=dict(required=False, default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('s3', retry_decorator=AWSRetry.jittered_backoff())
    state = module.params.get("state")

    if state == 'present':
        enable_bucket_logging(connection, module)
    elif state == 'absent':
        disable_bucket_logging(connection, module)


if __name__ == '__main__':
    main()

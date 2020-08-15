# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

try:
    import botocore
except ImportError:
    pass

from ansible.module_utils._text import to_native

from .ec2 import AWSRetry
from .core import is_boto3_error_code


def get_aws_account_id(module):
    """ Given an AnsibleAWSModule instance, get the active AWS account ID
    """

    return get_aws_account_info(module)[0]


def get_aws_account_info(module):
    """Given an AnsibleAWSModule instance, return the account information
    (account id and partition) we are currently working on

    get_account_info tries too find out the account that we are working
    on.  It's not guaranteed that this will be easy so we try in
    several different ways.  Giving either IAM or STS privileges to
    the account should be enough to permit this.

    Tries:
    - sts:GetCallerIdentity
    - iam:GetUser
    - sts:DecodeAuthorizationMessage
    """
    account_id = None
    partition = None
    try:
        sts_client = module.client('sts', retry_decorator=AWSRetry.jittered_backoff())
        caller_id = sts_client.get_caller_identity(aws_retry=True)
        account_id = caller_id.get('Account')
        partition = caller_id.get('Arn').split(':')[1]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError):
        try:
            iam_client = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())
            arn, partition, service, reg, account_id, resource = iam_client.get_user(aws_retry=True)['User']['Arn'].split(':')
        except is_boto3_error_code('AccessDenied') as e:
            try:
                except_msg = to_native(e.message)
            except AttributeError:
                except_msg = to_native(e)
            m = re.search(r"arn:(aws(-([a-z\-]+))?):iam::([0-9]{12,32}):\w+/", except_msg)
            if m is None:
                module.fail_json_aws(
                    e,
                    msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions."
                )
            account_id = m.group(4)
            partition = m.group(1)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(
                e,
                msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions."
            )

    if account_id is None or partition is None:
        module.fail_json(
            msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions."
        )

    return (to_native(account_id), to_native(partition))

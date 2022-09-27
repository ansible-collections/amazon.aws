#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: aws_caller_info
version_added: 1.0.0
short_description: Get information about the user and account being used to make AWS calls
description:
    - This module returns information about the account and user / role from which the AWS access tokens originate.
    - The primary use of this is to get the account id for templating into ARNs or similar to avoid needing to specify this information in inventory.

author:
    - Ed Costello (@orthanc)
    - Stijn Dubrul (@sdubrul)

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Get the current caller identity information
  amazon.aws.aws_caller_info:
  register: caller_info
'''

RETURN = '''
account:
    description: The account id the access credentials are associated with.
    returned: success
    type: str
    sample: "123456789012"
account_alias:
    description: The account alias the access credentials are associated with.
    returned: when caller has the iam:ListAccountAliases permission
    type: str
    sample: "acme-production"
arn:
    description: The arn identifying the user the credentials are associated with.
    returned: success
    type: str
    sample: arn:aws:sts::123456789012:federated-user/my-federated-user-name
user_id:
    description: |
        The user id the access credentials are associated with. Note that this may not correspond to
        anything you can look up in the case of roles or federated identities.
    returned: success
    type: str
    sample: 123456789012:my-federated-user-name
'''

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def main():
    module = AnsibleAWSModule(
        argument_spec={},
        supports_check_mode=True,
    )

    client = module.client('sts', retry_decorator=AWSRetry.jittered_backoff())

    try:
        caller_info = client.get_caller_identity(aws_retry=True)
        caller_info.pop('ResponseMetadata', None)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to retrieve caller identity')

    iam_client = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())

    try:
        # Although a list is returned by list_account_aliases AWS supports maximum one alias per account.
        # If an alias is defined it will be returned otherwise a blank string is filled in as account_alias.
        # see https://docs.aws.amazon.com/cli/latest/reference/iam/list-account-aliases.html#output
        response = iam_client.list_account_aliases(aws_retry=True)
        if response and response['AccountAliases']:
            caller_info['account_alias'] = response['AccountAliases'][0]
        else:
            caller_info['account_alias'] = ''
    except (BotoCoreError, ClientError):
        # The iam:ListAccountAliases permission is required for this operation to succeed.
        # Lacking this permission is handled gracefully by not returning the account_alias.
        pass

    module.exit_json(
        changed=False,
        **camel_dict_to_snake_dict(caller_info))


if __name__ == '__main__':
    main()

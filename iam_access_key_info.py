#!/usr/bin/python
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: iam_access_key_info
version_added: 2.1.0
short_description: fetch information about AWS IAM User access keys
description:
  - 'Fetches information AWS IAM user access keys.'
  - 'Note: It is not possible to fetch the secret access key.'
author: Mark Chappell (@tremble)
options:
  user_name:
    description:
      - The name of the IAM User to which the keys belong.
    required: true
    type: str
    aliases: ['username']

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Fetch Access keys for a user
  community.aws.iam_access_key_info:
    user_name: example_user
'''

RETURN = r'''
access_key:
    description: A dictionary containing all the access key information.
    returned: When the key exists.
    type: list
    elements: dict
    contains:
        access_key_id:
            description: The ID for the access key.
            returned: success
            type: str
            sample: AKIA1EXAMPLE1EXAMPLE
        create_date:
            description: The date and time, in ISO 8601 date-time format, when the access key was created.
            returned: success
            type: str
            sample: "2021-10-09T13:25:42+00:00"
        user_name:
            description: The name of the IAM user to which the key is attached.
            returned: success
            type: str
            sample: example_user
        status:
            description:
              - The status of the key.
              - C(Active) means it can be used.
              - C(Inactive) means it can not be used.
            returned: success
            type: str
            sample: Inactive
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def get_access_keys(user):
    try:
        results = client.list_access_keys(aws_retry=True, UserName=user)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e, msg='Failed to get access keys for user "{0}"'.format(user)
        )
    if not results:
        return None

    results = camel_dict_to_snake_dict(results)
    access_keys = results.get('access_key_metadata', [])
    if not access_keys:
        return []

    access_keys = normalize_boto3_result(access_keys)
    access_keys = sorted(access_keys, key=lambda d: d.get('create_date', None))
    return access_keys


def main():

    global module
    global client

    argument_spec = dict(
        user_name=dict(required=True, type='str', aliases=['username']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())

    changed = False
    user = module.params.get('user_name')
    access_keys = get_access_keys(user)

    module.exit_json(changed=changed, access_keys=access_keys)


if __name__ == '__main__':
    main()

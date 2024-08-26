#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_access_key_info
version_added: 2.1.0
version_added_collection: community.aws
short_description: fetch information about AWS IAM User access keys
description:
  - Fetches information AWS IAM user access keys.
  - 'Note: It is not possible to fetch the secret access key.'
author:
  - Mark Chappell (@tremble)
options:
  user_name:
    description:
      - The name of the IAM User to which the keys belong.
    required: true
    type: str
    aliases: ['username']

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Fetch Access keys for a user
  amazon.aws.iam_access_key_info:
    user_name: example_user
"""

RETURN = r"""
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
"""

from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_access_keys
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        user_name=dict(required=True, type="str", aliases=["username"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    try:
        access_keys = get_iam_access_keys(client, module.params.get("user_name"))
        module.exit_json(changed=False, access_keys=access_keys)
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

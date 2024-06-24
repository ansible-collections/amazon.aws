#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_mfa_device_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: List the MFA (Multi-Factor Authentication) devices registered for a user
description:
  - List the MFA (Multi-Factor Authentication) devices registered for a user.
author:
  - Victor Costan (@pwnall)
options:
  user_name:
    description:
      - The name of the user whose MFA devices will be listed.
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

RETURN = r"""
mfa_devices:
    description: The MFA devices registered for the given user.
    returned: always
    type: list
    sample:
      - enable_date: "2016-03-11T23:25:36+00:00"
        serial_number: arn:aws:iam::123456789012:mfa/example
        user_name: example
      - enable_date: "2016-03-11T23:25:37+00:00"
        serial_number: arn:aws:iam::123456789012:mfa/example
        user_name: example
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# more details: https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListMFADevices.html
- name: List MFA devices
  amazon.aws.iam_mfa_device_info:
  register: mfa_devices

# more details: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
- name: Assume an existing role
  community.aws.sts_assume_role:
    mfa_serial_number: "{{ mfa_devices.mfa_devices[0].serial_number }}"
    role_arn: "arn:aws:iam::123456789012:role/someRole"
    role_session_name: "someRoleSession"
  register: assumed_role
"""

from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_mfa_devices
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_mfa_devices
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def list_mfa_devices(connection, module):
    user_name = module.params.get("user_name")
    devices = list_iam_mfa_devices(connection, user_name)
    module.exit_json(changed=False, mfa_devices=normalize_iam_mfa_devices(devices))


def main():
    argument_spec = dict(
        user_name=dict(required=False, default=None),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    connection = module.client("iam")
    try:
        list_mfa_devices(connection, module)
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

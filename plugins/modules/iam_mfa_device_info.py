#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: iam_mfa_device_info
version_added: 1.0.0
short_description: List the MFA (Multi-Factor Authentication) devices registered for a user
description:
    - List the MFA (Multi-Factor Authentication) devices registered for a user
    - This module was called C(iam_mfa_device_facts) before Ansible 2.9. The usage did not change.
author: Victor Costan (@pwnall)
options:
  user_name:
    description:
      - The name of the user whose MFA devices will be listed
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

requirements:
    - boto3
    - botocore
'''

RETURN = """
mfa_devices:
    description: The MFA devices registered for the given user
    returned: always
    type: list
    sample:
      - enable_date: "2016-03-11T23:25:36+00:00"
        serial_number: arn:aws:iam::085120003701:mfa/pwnall
        user_name: pwnall
      - enable_date: "2016-03-11T23:25:37+00:00"
        serial_number: arn:aws:iam::085120003702:mfa/pwnall
        user_name: pwnall
"""

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# more details: https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListMFADevices.html
- name: List MFA devices
  community.aws.iam_mfa_device_info:
  register: mfa_devices

# more details: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
- name: Assume an existing role
  community.aws.sts_assume_role:
    mfa_serial_number: "{{ mfa_devices.mfa_devices[0].serial_number }}"
    role_arn: "arn:aws:iam::123456789012:role/someRole"
    role_session_name: "someRoleSession"
  register: assumed_role
'''

try:
    import botocore
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def list_mfa_devices(connection, module):
    user_name = module.params.get('user_name')
    changed = False

    args = {}
    if user_name is not None:
        args['UserName'] = user_name
    try:
        response = connection.list_mfa_devices(**args)
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to list MFA devices")

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


def main():
    argument_spec = dict(
        user_name=dict(required=False, default=None),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    if module._name == 'iam_mfa_device_facts':
        module.deprecate("The 'iam_mfa_device_facts' module has been renamed to 'iam_mfa_device_info'", date='2021-12-01', collection_name='community.aws')

    try:
        connection = module.client('iam')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    list_mfa_devices(connection, module)


if __name__ == '__main__':
    main()

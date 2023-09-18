#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: sts_session_token
version_added: 1.0.0
short_description: Obtain a session token from the AWS Security Token Service
description:
    - Obtain a session token from the AWS Security Token Service.
author: Victor Costan (@pwnall)
options:
  duration_seconds:
    description:
      - The duration, in seconds, of the session token.
        See U(https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html#API_GetSessionToken_RequestParameters)
        for acceptable and default values.
    type: int
  mfa_serial_number:
    description:
      - The identification number of the MFA device that is associated with the user who is making the GetSessionToken call.
    type: str
  mfa_token:
    description:
      - The value provided by the MFA device, if the trust policy of the user requires MFA.
    type: str
notes:
  - In order to use the session token in a following playbook task you must pass the I(access_key), I(access_secret) and I(access_token).
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

requirements:
    - boto3
    - botocore
    - python >= 2.6
'''

RETURN = """
sts_creds:
    description: The Credentials object returned by the AWS Security Token Service
    returned: always
    type: list
    sample:
      access_key: ASXXXXXXXXXXXXXXXXXX
      expiration: "2016-04-08T11:59:47+00:00"
      secret_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      session_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
changed:
    description: True if obtaining the credentials succeeds
    type: bool
    returned: always
"""


EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# (more details: https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html)
- name: Get a session token
  community.aws.sts_session_token:
    duration_seconds: 3600
  register: session_credentials

- name: Use the session token obtained above to tag an instance in account 123456789012
  amazon.aws.ec2_tag:
    aws_access_key: "{{ session_credentials.sts_creds.access_key }}"
    aws_secret_key: "{{ session_credentials.sts_creds.secret_key }}"
    security_token: "{{ session_credentials.sts_creds.session_token }}"
    resource: i-xyzxyz01
    state: present
    tags:
        MyNewTag: value

'''

try:
    import botocore
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def normalize_credentials(credentials):
    access_key = credentials.get('AccessKeyId', None)
    secret_key = credentials.get('SecretAccessKey', None)
    session_token = credentials.get('SessionToken', None)
    expiration = credentials.get('Expiration', None)
    return {
        'access_key': access_key,
        'secret_key': secret_key,
        'session_token': session_token,
        'expiration': expiration
    }


def get_session_token(connection, module):
    duration_seconds = module.params.get('duration_seconds')
    mfa_serial_number = module.params.get('mfa_serial_number')
    mfa_token = module.params.get('mfa_token')
    changed = False

    args = {}
    if duration_seconds is not None:
        args['DurationSeconds'] = duration_seconds
    if mfa_serial_number is not None:
        args['SerialNumber'] = mfa_serial_number
    if mfa_token is not None:
        args['TokenCode'] = mfa_token

    try:
        response = connection.get_session_token(**args)
        changed = True
    except ClientError as e:
        module.fail_json(msg=e)

    credentials = normalize_credentials(response.get('Credentials', {}))
    module.exit_json(changed=changed, sts_creds=credentials)


def main():
    argument_spec = dict(
        duration_seconds=dict(required=False, default=None, type='int'),
        mfa_serial_number=dict(required=False, default=None),
        mfa_token=dict(required=False, default=None, no_log=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    try:
        connection = module.client('sts')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    get_session_token(connection, module)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sts_assume_role
version_added: 1.0.0
version_added_collection: community.aws
short_description: Assume a role using AWS Security Token Service and obtain temporary credentials
description:
  - Assume a role using AWS Security Token Service and obtain temporary credentials.
author:
  - Boris Ekelchik (@bekelchik)
  - Marek Piatek (@piontas)
options:
  role_arn:
    description:
      - The Amazon Resource Name (ARN) of the role that the caller is
        assuming U(https://docs.aws.amazon.com/IAM/latest/UserGuide/Using_Identifiers.html#Identifiers_ARNs).
    required: true
    type: str
  role_session_name:
    description:
      - Name of the role's session - will be used by CloudTrail.
    required: true
    type: str
  policy:
    description:
      - Supplemental policy to use in addition to assumed role's policies.
    type: str
  duration_seconds:
    description:
      - The duration, in seconds, of the role session. The value can range from 900 seconds (15 minutes) to 43200 seconds (12 hours).
      - The max depends on the IAM role's sessions duration setting.
      - By default, the value is set to 3600 seconds.
    type: int
  external_id:
    description:
      - A unique identifier that is used by third parties to assume a role in their customers' accounts.
    type: str
  mfa_serial_number:
    description:
      - The identification number of the MFA device that is associated with the user who is making the AssumeRole call.
    type: str
  mfa_token:
    description:
      - The value provided by the MFA device, if the trust policy of the role being assumed requires MFA.
    type: str
notes:
  - In order to use the assumed role in a following playbook task you must pass the I(access_key),
    I(secret_key) and I(session_token) parameters to modules that should use the assumed credentials.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

RETURN = r"""
sts_creds:
    description: The temporary security credentials, which include an access key ID, a secret access key, and a security (or session) token
    returned: always
    type: dict
    sample:
      access_key: XXXXXXXXXXXXXXXXXXXX
      expiration: '2017-11-11T11:11:11+00:00'
      secret_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      session_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
sts_user:
    description: The Amazon Resource Name (ARN) and the assumed role ID
    returned: always
    type: dict
    sample:
      assumed_role_id: arn:aws:sts::123456789012:assumed-role/demo/Bob
      arn: ARO123EXAMPLE123:Bob
changed:
    description: True if obtaining the credentials succeeds
    type: bool
    returned: always
"""

EXAMPLES = r"""
# Assume an existing role (more details: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- amazon.aws.sts_assume_role:
    access_key: AKIA1EXAMPLE1EXAMPLE
    secret_key: 123456789abcdefghijklmnopqrstuvwxyzABCDE
    role_arn: "arn:aws:iam::123456789012:role/someRole"
    role_session_name: "someRoleSession"
  register: assumed_role

# Use the assumed role above to tag an instance in account 123456789012
- amazon.aws.ec2_tag:
    access_key: "{{ assumed_role.sts_creds.access_key }}"
    secret_key: "{{ assumed_role.sts_creds.secret_key }}"
    session_token: "{{ assumed_role.sts_creds.session_token }}"
    resource: i-xyzxyz01
    state: present
    tags:
      MyNewTag: value
"""

try:
    from botocore.exceptions import ClientError
    from botocore.exceptions import ParamValidationError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def _parse_response(response):
    credentials = response.get("Credentials", {})
    user = response.get("AssumedRoleUser", {})

    sts_cred = {
        "access_key": credentials.get("AccessKeyId"),
        "secret_key": credentials.get("SecretAccessKey"),
        "session_token": credentials.get("SessionToken"),
        "expiration": credentials.get("Expiration"),
    }
    sts_user = camel_dict_to_snake_dict(user)
    return sts_cred, sts_user


def assume_role_policy(connection, module):
    params = {
        "RoleArn": module.params.get("role_arn"),
        "RoleSessionName": module.params.get("role_session_name"),
        "Policy": module.params.get("policy"),
        "DurationSeconds": module.params.get("duration_seconds"),
        "ExternalId": module.params.get("external_id"),
        "SerialNumber": module.params.get("mfa_serial_number"),
        "TokenCode": module.params.get("mfa_token"),
    }
    changed = False

    kwargs = dict((k, v) for k, v in params.items() if v is not None)

    try:
        response = connection.assume_role(**kwargs)
        changed = True
    except (ClientError, ParamValidationError) as e:
        module.fail_json_aws(e)

    sts_cred, sts_user = _parse_response(response)
    module.exit_json(changed=changed, sts_creds=sts_cred, sts_user=sts_user)


def main():
    argument_spec = dict(
        role_arn=dict(required=True),
        role_session_name=dict(required=True),
        duration_seconds=dict(required=False, default=None, type="int"),
        external_id=dict(required=False, default=None),
        policy=dict(required=False, default=None),
        mfa_serial_number=dict(required=False, default=None),
        mfa_token=dict(required=False, default=None, no_log=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    connection = module.client("sts")

    assume_role_policy(connection, module)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: aws_kms
version_added: 1.0.0
short_description: Perform various KMS management tasks.
description:
     - Manage role/user access to a KMS key. Not designed for encrypting/decrypting.
options:
  alias:
    description: An alias for a key. For safety, even though KMS does not require keys
      to have an alias, this module expects all new keys to be given an alias
      to make them easier to manage. Existing keys without an alias may be
      referred to by I(key_id). Use M(community.aws.aws_kms_info) to find key ids. Required
      if I(key_id) is not given. Note that passing a I(key_id) and I(alias)
      will only cause a new alias to be added, an alias will never be renamed.
      The 'alias/' prefix is optional.
    required: false
    aliases:
      - key_alias
    type: str
  key_id:
    description:
    - Key ID or ARN of the key.
    - One of I(alias) or I(key_id) are required.
    required: false
    aliases:
      - key_arn
    type: str
  enable_key_rotation:
    description:
    - Whether the key should be automatically rotated every year.
    required: false
    type: bool
  policy_mode:
    description:
    - (deprecated) Grant or deny access.
    - Used for modifying the Key Policy rather than modifying a grant and only
      works on the default policy created through the AWS Console.
    - This option has been deprecated, and will be removed in a release after 2021-12-01. Use I(policy) instead.
    default: grant
    choices: [ grant, deny ]
    aliases:
    - mode
    type: str
  policy_role_name:
    description:
    - (deprecated) Role to allow/deny access.
    - One of I(policy_role_name) or I(policy_role_arn) are required.
    - Used for modifying the Key Policy rather than modifying a grant and only
      works on the default policy created through the AWS Console.
    - This option has been deprecated, and will be removed in a release after 2021-12-01. Use I(policy) instead.
    required: false
    aliases:
    - role_name
    type: str
  policy_role_arn:
    description:
    - (deprecated) ARN of role to allow/deny access.
    - One of I(policy_role_name) or I(policy_role_arn) are required.
    - Used for modifying the Key Policy rather than modifying a grant and only
      works on the default policy created through the AWS Console.
    - This option has been deprecated, and will be removed in a release after 2021-12-01. Use I(policy) instead.
    type: str
    required: false
    aliases:
    - role_arn
  policy_grant_types:
    description:
    - (deprecated) List of grants to give to user/role. Likely "role,role grant" or "role,role grant,admin".
    - Required when I(policy_mode=grant).
    - Used for modifying the Key Policy rather than modifying a grant and only
      works on the default policy created through the AWS Console.
    - This option has been deprecated, and will be removed in a release after 2021-12-01. Use I(policy) instead.
    required: false
    aliases:
    - grant_types
    type: list
    elements: str
  policy_clean_invalid_entries:
    description:
    - (deprecated) If adding/removing a role and invalid grantees are found, remove them. These entries will cause an update to fail in all known cases.
    - Only cleans if changes are being made.
    - Used for modifying the Key Policy rather than modifying a grant and only
      works on the default policy created through the AWS Console.
    - This option has been deprecated, and will be removed in a release after 2021-12-01. Use I(policy) instead.
    type: bool
    default: true
    aliases:
    - clean_invalid_entries
  state:
    description: Whether a key should be present or absent. Note that making an
      existing key absent only schedules a key for deletion.  Passing a key that
      is scheduled for deletion with state present will cancel key deletion.
    required: False
    choices:
      - present
      - absent
    default: present
    type: str
  enabled:
    description: Whether or not a key is enabled
    default: True
    type: bool
  description:
    description:
      A description of the CMK. Use a description that helps you decide
      whether the CMK is appropriate for a task.
    type: str
  tags:
    description: A dictionary of tags to apply to a key.
    type: dict
  pending_window:
    description:
    - The number of days between requesting deletion of the CMK and when it will actually be deleted.
    - Only used when I(state=absent) and the CMK has not yet been deleted.
    - Valid values are between 7 and 30 (inclusive).
    - 'See also: U(https://docs.aws.amazon.com/kms/latest/APIReference/API_ScheduleKeyDeletion.html#KMS-ScheduleKeyDeletion-request-PendingWindowInDays)'
    type: int
    aliases: ['deletion_delay']
    version_added: 1.4.0
  purge_tags:
    description: Whether the I(tags) argument should cause tags not in the list to
      be removed
    default: False
    type: bool
  purge_grants:
    description: Whether the I(grants) argument should cause grants not in the list to
      be removed
    default: False
    type: bool
  grants:
    description:
      - A list of grants to apply to the key. Each item must contain I(grantee_principal).
        Each item can optionally contain I(retiring_principal), I(operations), I(constraints),
        I(name).
      - I(grantee_principal) and I(retiring_principal) must be ARNs
      - 'For full documentation of suboptions see the boto3 documentation:'
      - 'U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.create_grant)'
    type: list
    elements: dict
    suboptions:
        grantee_principal:
            description: The full ARN of the principal being granted permissions.
            required: true
            type: str
        retiring_principal:
            description: The full ARN of the principal permitted to revoke/retire the grant.
            type: str
        operations:
            type: list
            elements: str
            description:
              - A list of operations that the grantee may perform using the CMK.
            choices: ['Decrypt', 'Encrypt', 'GenerateDataKey', 'GenerateDataKeyWithoutPlaintext', 'ReEncryptFrom', 'ReEncryptTo',
                      'CreateGrant', 'RetireGrant', 'DescribeKey', 'Verify', 'Sign']
        constraints:
            description:
              - Constraints is a dict containing C(encryption_context_subset) or C(encryption_context_equals),
                either or both being a dict specifying an encryption context match.
                See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html) or
                U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.create_grant)
            type: dict
  policy:
    description:
      - policy to apply to the KMS key.
      - See U(https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
    type: json
  key_spec:
    aliases:
      - customer_master_key_spec
    description:
      - Specifies the type of KMS key to create.
      - The specification is not changeable once the key is created.
    type: str
    default: SYMMETRIC_DEFAULT
    choices: ['SYMMETRIC_DEFAULT', 'RSA_2048', 'RSA_3072', 'RSA_4096', 'ECC_NIST_P256', 'ECC_NIST_P384', 'ECC_NIST_P521', 'ECC_SECG_P256K1']
    version_added: 2.1.0
  key_usage:
    description:
      - Determines the cryptographic operations for which you can use the KMS key.
      - The usage is not changeable once the key is created.
    type: str
    default: ENCRYPT_DECRYPT
    choices: ['ENCRYPT_DECRYPT', 'SIGN_VERIFY']
    version_added: 2.1.0
author:
  - Ted Timmons (@tedder)
  - Will Thames (@willthames)
  - Mark Chappell (@tremble)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Managing the KMS IAM Policy via policy_mode and policy_grant_types is fragile
# and has been deprecated in favour of the policy option.
- name: grant user-style access to production secrets
  community.aws.aws_kms:
  args:
    alias: "alias/my_production_secrets"
    policy_mode: grant
    policy_role_name: "prod-appServerRole-1R5AQG2BSEL6L"
    policy_grant_types: "role,role grant"
- name: remove access to production secrets from role
  community.aws.aws_kms:
  args:
    alias: "alias/my_production_secrets"
    policy_mode: deny
    policy_role_name: "prod-appServerRole-1R5AQG2BSEL6L"

# Create a new KMS key
- community.aws.aws_kms:
    alias: mykey
    tags:
      Name: myKey
      Purpose: protect_stuff

# Update previous key with more tags
- community.aws.aws_kms:
    alias: mykey
    tags:
      Name: myKey
      Purpose: protect_stuff
      Owner: security_team

# Update a known key with grants allowing an instance with the billing-prod IAM profile
# to decrypt data encrypted with the environment: production, application: billing
# encryption context
- community.aws.aws_kms:
    key_id: abcd1234-abcd-1234-5678-ef1234567890
    grants:
      - name: billing_prod
        grantee_principal: arn:aws:iam::1234567890123:role/billing_prod
        constraints:
          encryption_context_equals:
            environment: production
            application: billing
        operations:
          - Decrypt
          - RetireGrant

- name: Update IAM policy on an existing KMS key
  community.aws.aws_kms:
    alias: my-kms-key
    policy: '{"Version": "2012-10-17", "Id": "my-kms-key-permissions", "Statement": [ { <SOME STATEMENT> } ]}'
    state: present

- name: Example using lookup for policy json
  community.aws.aws_kms:
    alias: my-kms-key
    policy: "{{ lookup('template', 'kms_iam_policy_template.json.j2') }}"
    state: present
'''

RETURN = r'''
key_id:
  description: ID of key
  type: str
  returned: always
  sample: abcd1234-abcd-1234-5678-ef1234567890
key_arn:
  description: ARN of key
  type: str
  returned: always
  sample: arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890
key_state:
  description: The state of the key
  type: str
  returned: always
  sample: PendingDeletion
key_usage:
  description: The cryptographic operations for which you can use the key.
  type: str
  returned: always
  sample: ENCRYPT_DECRYPT
origin:
  description: The source of the key's key material. When this value is C(AWS_KMS),
    AWS KMS created the key material. When this value is C(EXTERNAL), the
    key material was imported or the CMK lacks key material.
  type: str
  returned: always
  sample: AWS_KMS
aws_account_id:
  description: The AWS Account ID that the key belongs to
  type: str
  returned: always
  sample: 1234567890123
creation_date:
  description: Date of creation of the key
  type: str
  returned: always
  sample: "2017-04-18T15:12:08.551000+10:00"
description:
  description: Description of the key
  type: str
  returned: always
  sample: "My Key for Protecting important stuff"
enabled:
  description: Whether the key is enabled. True if C(KeyState) is true.
  type: str
  returned: always
  sample: false
aliases:
  description: list of aliases associated with the key
  type: list
  returned: always
  sample:
    - aws/acm
    - aws/ebs
policies:
  description: list of policy documents for the keys. Empty when access is denied even if there are policies.
  type: list
  returned: always
  sample:
    Version: "2012-10-17"
    Id: "auto-ebs-2"
    Statement:
    - Sid: "Allow access through EBS for all principals in the account that are authorized to use EBS"
      Effect: "Allow"
      Principal:
        AWS: "*"
      Action:
      - "kms:Encrypt"
      - "kms:Decrypt"
      - "kms:ReEncrypt*"
      - "kms:GenerateDataKey*"
      - "kms:CreateGrant"
      - "kms:DescribeKey"
      Resource: "*"
      Condition:
        StringEquals:
          kms:CallerAccount: "111111111111"
          kms:ViaService: "ec2.ap-southeast-2.amazonaws.com"
    - Sid: "Allow direct access to key metadata to the account"
      Effect: "Allow"
      Principal:
        AWS: "arn:aws:iam::111111111111:root"
      Action:
      - "kms:Describe*"
      - "kms:Get*"
      - "kms:List*"
      - "kms:RevokeGrant"
      Resource: "*"
tags:
  description: dictionary of tags applied to the key
  type: dict
  returned: always
  sample:
    Name: myKey
    Purpose: protecting_stuff
grants:
  description: list of grants associated with a key
  type: complex
  returned: always
  contains:
    constraints:
      description: Constraints on the encryption context that the grant allows.
        See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html) for further details
      type: dict
      returned: always
      sample:
        encryption_context_equals:
           "aws:lambda:_function_arn": "arn:aws:lambda:ap-southeast-2:012345678912:function:xyz"
    creation_date:
      description: Date of creation of the grant
      type: str
      returned: always
      sample: "2017-04-18T15:12:08+10:00"
    grant_id:
      description: The unique ID for the grant
      type: str
      returned: always
      sample: abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234
    grantee_principal:
      description: The principal that receives the grant's permissions
      type: str
      returned: always
      sample: arn:aws:sts::0123456789012:assumed-role/lambda_xyz/xyz
    issuing_account:
      description: The AWS account under which the grant was issued
      type: str
      returned: always
      sample: arn:aws:iam::01234567890:root
    key_id:
      description: The key ARN to which the grant applies.
      type: str
      returned: always
      sample: arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890
    name:
      description: The friendly name that identifies the grant
      type: str
      returned: always
      sample: xyz
    operations:
      description: The list of operations permitted by the grant
      type: list
      returned: always
      sample:
        - Decrypt
        - RetireGrant
    retiring_principal:
      description: The principal that can retire the grant
      type: str
      returned: always
      sample: arn:aws:sts::0123456789012:assumed-role/lambda_xyz/xyz
changes_needed:
  description: grant types that would be changed/were changed.
  type: dict
  returned: always
  sample: { "role": "add", "role grant": "add" }
had_invalid_entries:
  description: there are invalid (non-ARN) entries in the KMS entry. These don't count as a change, but will be removed if any changes are being made.
  type: bool
  returned: always
'''

# these mappings are used to go from simple labels to the actual 'Sid' values returned
# by get_policy. They seem to be magic values.
statement_label = {
    'role': 'Allow use of the key',
    'role grant': 'Allow attachment of persistent resources',
    'admin': 'Allow access for Key Administrators'
}

import json
import re

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_policies


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_iam_roles_with_backoff(connection):
    paginator = connection.get_paginator('list_roles')
    return paginator.paginate().build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_keys_with_backoff(connection):
    paginator = connection.get_paginator('list_keys')
    return paginator.paginate().build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_aliases_with_backoff(connection):
    paginator = connection.get_paginator('list_aliases')
    return paginator.paginate().build_full_result()


def get_kms_aliases_lookup(connection):
    _aliases = dict()
    for alias in get_kms_aliases_with_backoff(connection)['Aliases']:
        # Not all aliases are actually associated with a key
        if 'TargetKeyId' in alias:
            # strip off leading 'alias/' and add it to key's aliases
            if alias['TargetKeyId'] in _aliases:
                _aliases[alias['TargetKeyId']].append(alias['AliasName'][6:])
            else:
                _aliases[alias['TargetKeyId']] = [alias['AliasName'][6:]]
    return _aliases


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_tags_with_backoff(connection, key_id, **kwargs):
    return connection.list_resource_tags(KeyId=key_id, **kwargs)


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_grants_with_backoff(connection, key_id):
    params = dict(KeyId=key_id)
    paginator = connection.get_paginator('list_grants')
    return paginator.paginate(**params).build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_metadata_with_backoff(connection, key_id):
    return connection.describe_key(KeyId=key_id)


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def list_key_policies_with_backoff(connection, key_id):
    paginator = connection.get_paginator('list_key_policies')
    return paginator.paginate(KeyId=key_id).build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_key_policy_with_backoff(connection, key_id, policy_name):
    return connection.get_key_policy(KeyId=key_id, PolicyName=policy_name)


def get_kms_tags(connection, module, key_id):
    # Handle pagination here as list_resource_tags does not have
    # a paginator
    kwargs = {}
    tags = []
    more = True
    while more:
        try:
            tag_response = get_kms_tags_with_backoff(connection, key_id, **kwargs)
            tags.extend(tag_response['Tags'])
        except is_boto3_error_code('AccessDeniedException'):
            tag_response = {}
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to obtain key tags")
        if tag_response.get('NextMarker'):
            kwargs['Marker'] = tag_response['NextMarker']
        else:
            more = False
    return tags


def get_kms_policies(connection, module, key_id):
    try:
        policies = list_key_policies_with_backoff(connection, key_id)['PolicyNames']
        return [get_key_policy_with_backoff(connection, key_id, policy)['Policy'] for
                policy in policies]
    except is_boto3_error_code('AccessDeniedException'):
        return []
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain key policies")


def camel_to_snake_grant(grant):
    ''' camel_to_snake_grant snakifies everything except the encryption context '''
    constraints = grant.get('Constraints', {})
    result = camel_dict_to_snake_dict(grant)
    if 'EncryptionContextEquals' in constraints:
        result['constraints']['encryption_context_equals'] = constraints['EncryptionContextEquals']
    if 'EncryptionContextSubset' in constraints:
        result['constraints']['encryption_context_subset'] = constraints['EncryptionContextSubset']
    return result


def get_key_details(connection, module, key_id):
    try:
        result = get_kms_metadata_with_backoff(connection, key_id)['KeyMetadata']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain key metadata")
    result['KeyArn'] = result.pop('Arn')

    try:
        aliases = get_kms_aliases_lookup(connection)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain aliases")

    try:
        current_rotation_status = connection.get_key_rotation_status(KeyId=key_id)
        result['enable_key_rotation'] = current_rotation_status.get('KeyRotationEnabled')
    except is_boto3_error_code(['AccessDeniedException', 'UnsupportedOperationException']) as e:
        result['enable_key_rotation'] = None
    result['aliases'] = aliases.get(result['KeyId'], [])

    result = camel_dict_to_snake_dict(result)

    # grants and tags get snakified differently
    try:
        result['grants'] = [camel_to_snake_grant(grant) for grant in
                            get_kms_grants_with_backoff(connection, key_id)['Grants']]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain key grants")
    tags = get_kms_tags(connection, module, key_id)
    result['tags'] = boto3_tag_list_to_ansible_dict(tags, 'TagKey', 'TagValue')
    result['policies'] = get_kms_policies(connection, module, key_id)
    return result


def get_kms_facts(connection, module):
    try:
        keys = get_kms_keys_with_backoff(connection)['Keys']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain keys")

    return [get_key_details(connection, module, key['KeyId']) for key in keys]


def convert_grant_params(grant, key):
    grant_params = dict(KeyId=key['key_arn'],
                        GranteePrincipal=grant['grantee_principal'])
    if grant.get('operations'):
        grant_params['Operations'] = grant['operations']
    if grant.get('retiring_principal'):
        grant_params['RetiringPrincipal'] = grant['retiring_principal']
    if grant.get('name'):
        grant_params['Name'] = grant['name']
    if grant.get('constraints'):
        grant_params['Constraints'] = dict()
        if grant['constraints'].get('encryption_context_subset'):
            grant_params['Constraints']['EncryptionContextSubset'] = grant['constraints']['encryption_context_subset']
        if grant['constraints'].get('encryption_context_equals'):
            grant_params['Constraints']['EncryptionContextEquals'] = grant['constraints']['encryption_context_equals']
    return grant_params


def different_grant(existing_grant, desired_grant):
    if existing_grant.get('grantee_principal') != desired_grant.get('grantee_principal'):
        return True
    if existing_grant.get('retiring_principal') != desired_grant.get('retiring_principal'):
        return True
    if set(existing_grant.get('operations', [])) != set(desired_grant.get('operations')):
        return True
    if existing_grant.get('constraints') != desired_grant.get('constraints'):
        return True
    return False


def compare_grants(existing_grants, desired_grants, purge_grants=False):
    existing_dict = dict((eg['name'], eg) for eg in existing_grants)
    desired_dict = dict((dg['name'], dg) for dg in desired_grants)
    to_add_keys = set(desired_dict.keys()) - set(existing_dict.keys())
    if purge_grants:
        to_remove_keys = set(existing_dict.keys()) - set(desired_dict.keys())
    else:
        to_remove_keys = set()
    to_change_candidates = set(existing_dict.keys()) & set(desired_dict.keys())
    for candidate in to_change_candidates:
        if different_grant(existing_dict[candidate], desired_dict[candidate]):
            to_add_keys.add(candidate)
            to_remove_keys.add(candidate)

    to_add = []
    to_remove = []
    for key in to_add_keys:
        grant = desired_dict[key]
        to_add.append(grant)
    for key in to_remove_keys:
        grant = existing_dict[key]
        to_remove.append(grant)
    return to_add, to_remove


def start_key_deletion(connection, module, key_metadata):
    if key_metadata['KeyState'] == 'PendingDeletion':
        return False

    if module.check_mode:
        return True

    deletion_params = {'KeyId': key_metadata['Arn']}
    if module.params.get('pending_window'):
        deletion_params['PendingWindowInDays'] = module.params.get('pending_window')

    try:
        connection.schedule_key_deletion(**deletion_params)
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to schedule key for deletion")


def cancel_key_deletion(connection, module, key):
    key_id = key['key_arn']
    if key['key_state'] != 'PendingDeletion':
        return False

    if module.check_mode:
        return True

    try:
        connection.cancel_key_deletion(KeyId=key_id)
        # key is disabled after deletion cancellation
        # set this so that ensure_enabled_disabled works correctly
        key['key_state'] = 'Disabled'
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to cancel key deletion")

    return True


def ensure_enabled_disabled(connection, module, key, enabled):
    desired_state = 'Enabled'
    if not enabled:
        desired_state = 'Disabled'

    if key['key_state'] == desired_state:
        return False

    key_id = key['key_arn']
    if not module.check_mode:
        if enabled:
            try:
                connection.enable_key(KeyId=key_id)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to enable key")
        else:
            try:
                connection.disable_key(KeyId=key_id)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to disable key")

    return True


def update_alias(connection, module, key, alias):
    alias = canonicalize_alias_name(alias)

    if alias is None:
        return False

    key_id = key['key_arn']
    aliases = get_kms_aliases_with_backoff(connection)['Aliases']
    # We will only add new aliases, not rename existing ones
    if alias in [_alias['AliasName'] for _alias in aliases]:
        return False

    if not module.check_mode:
        try:
            connection.create_alias(TargetKeyId=key_id, AliasName=alias)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed create key alias")

    return True


def update_description(connection, module, key, description):
    if description is None:
        return False
    if key['description'] == description:
        return False

    key_id = key['key_arn']
    if not module.check_mode:
        try:
            connection.update_key_description(KeyId=key_id, Description=description)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to update key description")

    return True


def update_tags(connection, module, key, desired_tags, purge_tags):
    # purge_tags needs to be explicitly set, so an empty tags list means remove
    # all tags

    to_add, to_remove = compare_aws_tags(key['tags'], desired_tags, purge_tags)
    if not (bool(to_add) or bool(to_remove)):
        return False

    key_id = key['key_arn']
    if not module.check_mode:
        if to_remove:
            try:
                connection.untag_resource(KeyId=key_id, TagKeys=to_remove)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to remove tag")
        if to_add:
            try:
                tags = ansible_dict_to_boto3_tag_list(module.params['tags'], tag_name_key_name='TagKey', tag_value_key_name='TagValue')
                connection.tag_resource(KeyId=key_id, Tags=tags)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to add tag to key")

    return True


def update_policy(connection, module, key, policy):
    if policy is None:
        return False
    try:
        new_policy = json.loads(policy)
    except ValueError as e:
        module.fail_json_aws(e, msg="Unable to parse new policy as JSON")

    key_id = key['key_arn']
    try:
        keyret = connection.get_key_policy(KeyId=key_id, PolicyName='default')
        original_policy = json.loads(keyret['Policy'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        # If we can't fetch the current policy assume we're making a change
        # Could occur if we have PutKeyPolicy without GetKeyPolicy
        original_policy = {}

    if not compare_policies(original_policy, new_policy):
        return False

    if not module.check_mode:
        try:
            connection.put_key_policy(KeyId=key_id, PolicyName='default', Policy=policy)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to update key policy")

    return True


def update_key_rotation(connection, module, key, enable_key_rotation):
    if enable_key_rotation is None:
        return False
    key_id = key['key_arn']

    try:
        current_rotation_status = connection.get_key_rotation_status(KeyId=key_id)
        if current_rotation_status.get('KeyRotationEnabled') == enable_key_rotation:
            return False
    except is_boto3_error_code('AccessDeniedException'):
        pass
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Unable to get current key rotation status")

    try:
        if enable_key_rotation:
            connection.enable_key_rotation(KeyId=key_id)
        else:
            connection.disable_key_rotation(KeyId=key_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to enable/disable key rotation")
    return True


def update_grants(connection, module, key, desired_grants, purge_grants):
    existing_grants = key['grants']

    to_add, to_remove = compare_grants(existing_grants, desired_grants, purge_grants)
    if not (bool(to_add) or bool(to_remove)):
        return False

    key_id = key['key_arn']
    if not module.check_mode:
        for grant in to_remove:
            try:
                connection.retire_grant(KeyId=key_id, GrantId=grant['grant_id'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to retire grant")
        for grant in to_add:
            grant_params = convert_grant_params(grant, key)
            try:
                connection.create_grant(**grant_params)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to create grant")

    return True


def update_key(connection, module, key):
    changed = False

    changed |= cancel_key_deletion(connection, module, key)
    changed |= ensure_enabled_disabled(connection, module, key, module.params['enabled'])
    changed |= update_alias(connection, module, key, module.params['alias'])
    changed |= update_description(connection, module, key, module.params['description'])
    changed |= update_tags(connection, module, key, module.params['tags'], module.params.get('purge_tags'))
    changed |= update_policy(connection, module, key, module.params.get('policy'))
    changed |= update_grants(connection, module, key, module.params.get('grants'), module.params.get('purge_grants'))
    changed |= update_key_rotation(connection, module, key, module.params.get('enable_key_rotation'))

    # make results consistent with kms_facts before returning
    result = get_key_details(connection, module, key['key_arn'])
    result['changed'] = changed
    return result


def create_key(connection, module):
    key_usage = module.params.get('key_usage')
    key_spec = module.params.get('key_spec')
    params = dict(BypassPolicyLockoutSafetyCheck=False,
                  Tags=ansible_dict_to_boto3_tag_list(module.params['tags'], tag_name_key_name='TagKey', tag_value_key_name='TagValue'),
                  KeyUsage=key_usage,
                  CustomerMasterKeySpec=key_spec,
                  Origin='AWS_KMS')

    if module.check_mode:
        return {'changed': True}

    if module.params.get('description'):
        params['Description'] = module.params['description']
    if module.params.get('policy'):
        params['Policy'] = module.params['policy']

    try:
        result = connection.create_key(**params)['KeyMetadata']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create initial key")

    key = get_key_details(connection, module, result['KeyId'])
    update_alias(connection, module, key, module.params['alias'])
    update_key_rotation(connection, module, key, module.params.get('enable_key_rotation'))

    ensure_enabled_disabled(connection, module, key, module.params.get('enabled'))
    update_grants(connection, module, key, module.params.get('grants'), False)

    # make results consistent with kms_facts
    result = get_key_details(connection, module, key['key_id'])
    result['changed'] = True
    return result


def delete_key(connection, module, key_metadata):
    changed = False

    changed |= start_key_deletion(connection, module, key_metadata)

    result = get_key_details(connection, module, key_metadata['Arn'])
    result['changed'] = changed
    return result


def get_arn_from_role_name(iam, rolename):
    ret = iam.get_role(RoleName=rolename)
    if ret.get('Role') and ret['Role'].get('Arn'):
        return ret['Role']['Arn']
    raise Exception('could not find arn for name {0}.'.format(rolename))


def _clean_statement_principals(statement, clean_invalid_entries):

    # create Principal and 'AWS' so we can safely use them later.
    if not isinstance(statement.get('Principal'), dict):
        statement['Principal'] = dict()

    # If we have a single AWS Principal, ensure we still have a list (to manipulate)
    if 'AWS' in statement['Principal'] and isinstance(statement['Principal']['AWS'], string_types):
        statement['Principal']['AWS'] = [statement['Principal']['AWS']]
    if not isinstance(statement['Principal'].get('AWS'), list):
        statement['Principal']['AWS'] = list()

    valid_princ = re.compile('^arn:aws:(iam|sts)::')

    invalid_entries = [item for item in statement['Principal']['AWS'] if not valid_princ.match(item)]
    valid_entries = [item for item in statement['Principal']['AWS'] if valid_princ.match(item)]

    if bool(invalid_entries) and clean_invalid_entries:
        statement['Principal']['AWS'] = valid_entries
        return True

    return False


def _do_statement_grant(statement, role_arn, grant_types, mode, grant_type):

    if mode == 'grant':
        if grant_type in grant_types:
            if role_arn not in statement['Principal']['AWS']:  # needs to be added.
                statement['Principal']['AWS'].append(role_arn)
                return 'add'
        elif role_arn in statement['Principal']['AWS']:  # not one the places the role should be
            statement['Principal']['AWS'].remove(role_arn)
            return 'remove'
        return None

    if mode == 'deny' and role_arn in statement['Principal']['AWS']:
        # we don't selectively deny. that's a grant with a
        # smaller list. so deny=remove all of this arn.
        statement['Principal']['AWS'].remove(role_arn)
        return 'remove'
    return None


def do_policy_grant(module, kms, keyarn, role_arn, grant_types, mode='grant', dry_run=True, clean_invalid_entries=True):
    ret = {}
    policy = json.loads(get_key_policy_with_backoff(kms, keyarn, 'default')['Policy'])

    changes_needed = {}
    assert_policy_shape(module, policy)
    had_invalid_entries = False
    for statement in policy['Statement']:
        # We already tested that these are the only types in the statements
        for grant_type in statement_label:
            # Are we on this grant type's statement?
            if statement['Sid'] != statement_label[grant_type]:
                continue

            had_invalid_entries |= _clean_statement_principals(statement, clean_invalid_entries)
            change = _do_statement_grant(statement, role_arn, grant_types, mode, grant_type)
            if change:
                changes_needed[grant_type] = change

    ret['changes_needed'] = changes_needed
    ret['had_invalid_entries'] = had_invalid_entries
    ret['new_policy'] = policy
    ret['changed'] = bool(changes_needed)

    if dry_run or not ret['changed']:
        return ret

    try:
        policy_json_string = json.dumps(policy)
        kms.put_key_policy(KeyId=keyarn, PolicyName='default', Policy=policy_json_string)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not update key_policy', new_policy=policy_json_string)

    return ret


def assert_policy_shape(module, policy):
    '''Since the policy seems a little, uh, fragile, make sure we know approximately what we're looking at.'''
    errors = []
    if policy['Version'] != "2012-10-17":
        errors.append('Unknown version/date ({0}) of policy. Things are probably different than we assumed they were.'.format(policy['Version']))

    found_statement_type = {}
    for statement in policy['Statement']:
        for label, sidlabel in statement_label.items():
            if statement['Sid'] == sidlabel:
                found_statement_type[label] = True

    for statementtype in statement_label:
        if not found_statement_type.get(statementtype):
            errors.append('Policy is missing {0}.'.format(statementtype))

    if errors:
        module.fail_json(msg='Problems asserting policy shape. Cowardly refusing to modify it', errors=errors, policy=policy)


def canonicalize_alias_name(alias):
    if alias is None:
        return None
    if alias.startswith('alias/'):
        return alias
    return 'alias/' + alias


def fetch_key_metadata(connection, module, key_id, alias):

    alias = canonicalize_alias_name(module.params.get('alias'))

    try:
        # Fetch by key_id where possible
        if key_id:
            return get_kms_metadata_with_backoff(connection, key_id)['KeyMetadata']
        # Or try alias as a backup
        return get_kms_metadata_with_backoff(connection, alias)['KeyMetadata']

    except connection.exceptions.NotFoundException:
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, 'Failed to fetch key metadata.')


def update_policy_grants(connection, module, key_metadata, mode):
    iam = module.client('iam')
    key_id = key_metadata['Arn']

    if module.params.get('policy_role_name') and not module.params.get('policy_role_arn'):
        module.params['policy_role_arn'] = get_arn_from_role_name(iam, module.params['policy_role_name'])
    if not module.params.get('policy_role_arn'):
        module.fail_json(msg='policy_role_arn or policy_role_name is required to {0}'.format(module.params['policy_mode']))

    # check the grant types for 'grant' only.
    if mode == 'grant':
        for grant_type in module.params['policy_grant_types']:
            if grant_type not in statement_label:
                module.fail_json(msg='{0} is an unknown grant type.'.format(grant_type))

    return do_policy_grant(module, connection,
                           key_id,
                           module.params['policy_role_arn'],
                           module.params['policy_grant_types'],
                           mode=mode,
                           dry_run=module.check_mode,
                           clean_invalid_entries=module.params['policy_clean_invalid_entries'])


def main():
    argument_spec = dict(
        alias=dict(aliases=['key_alias']),
        policy_mode=dict(aliases=['mode'], choices=['grant', 'deny'], default='grant'),
        policy_role_name=dict(aliases=['role_name']),
        policy_role_arn=dict(aliases=['role_arn']),
        policy_grant_types=dict(aliases=['grant_types'], type='list', elements='str'),
        policy_clean_invalid_entries=dict(aliases=['clean_invalid_entries'], type='bool', default=True),
        pending_window=dict(aliases=['deletion_delay'], type='int'),
        key_id=dict(aliases=['key_arn']),
        description=dict(),
        enabled=dict(type='bool', default=True),
        tags=dict(type='dict', default={}),
        purge_tags=dict(type='bool', default=False),
        grants=dict(type='list', default=[], elements='dict'),
        policy=dict(type='json'),
        purge_grants=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent']),
        enable_key_rotation=(dict(type='bool')),
        key_spec=dict(type='str', default='SYMMETRIC_DEFAULT', aliases=['customer_master_key_spec'],
                      choices=['SYMMETRIC_DEFAULT', 'RSA_2048', 'RSA_3072', 'RSA_4096', 'ECC_NIST_P256', 'ECC_NIST_P384', 'ECC_NIST_P521', 'ECC_SECG_P256K1']),
        key_usage=dict(type='str', default='ENCRYPT_DECRYPT', choices=['ENCRYPT_DECRYPT', 'SIGN_VERIFY']),
    )

    module = AnsibleAWSModule(
        supports_check_mode=True,
        argument_spec=argument_spec,
        required_one_of=[['alias', 'key_id']],
    )

    mode = module.params['policy_mode']

    kms = module.client('kms')

    key_metadata = fetch_key_metadata(kms, module, module.params.get('key_id'), module.params.get('alias'))
    # We can't create keys with a specific ID, if we can't access the key we'll have to fail
    if module.params.get('state') == 'present' and module.params.get('key_id') and not key_metadata:
        module.fail_json(msg="Could not find key with id %s to update")

    if module.params.get('policy_grant_types') or mode == 'deny':
        module.deprecate('Managing the KMS IAM Policy via policy_mode and policy_grant_types is fragile'
                         ' and has been deprecated in favour of the policy option.', date='2021-12-01', collection_name='community.aws')
        result = update_policy_grants(kms, module, key_metadata, mode)
        module.exit_json(**result)

    if module.params.get('state') == 'absent':
        if key_metadata is None:
            module.exit_json(changed=False)
        result = delete_key(kms, module, key_metadata)
        module.exit_json(**result)

    if key_metadata:
        key_details = get_key_details(kms, module, key_metadata['Arn'])
        result = update_key(kms, module, key_details)
        module.exit_json(**result)

    result = create_key(kms, module)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

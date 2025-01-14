#!/usr/bin/python
# -*- coding: utf-8 -*

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: kms_key
version_added: 5.0.0
short_description: Perform various KMS key management tasks
description:
  - Manage role/user access to a KMS key.
  - Not designed for encrypting/decrypting.
  - Prior to release 5.0.0 this module was called M(community.aws.aws_kms).
    The usage did not change.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  alias:
    description:
      - An alias for a key.
      - For safety, even though KMS does not require keys to have an alias, this module expects all
        new keys to be given an alias to make them easier to manage. Existing keys without an alias
        may be referred to by O(key_id). Use M(amazon.aws.kms_key_info) to find key ids.
      - Note that passing a O(key_id) and O(alias) will only cause a new alias to be added, an alias will never be renamed.
      - The V(alias/) prefix is optional.
      - Required if O(key_id) is not given.
    required: false
    aliases:
      - key_alias
    type: str
  key_id:
    description:
      - Key ID or ARN of the key.
      - One of O(alias) or O(key_id) are required.
    required: false
    aliases:
      - key_arn
    type: str
  enable_key_rotation:
    description:
      - Whether the key should be automatically rotated every year.
    required: false
    type: bool
  state:
    description:
      - Whether a key should be present or absent.
      - Note that making an existing key V(absent) only schedules a key for deletion.
      - Passing a key that is scheduled for deletion with O(state=present) will cancel key deletion.
    required: false
    choices:
      - present
      - absent
    default: present
    type: str
  enabled:
    description: Whether or not a key is enabled.
    default: true
    type: bool
  description:
    description:
      - A description of the CMK.
      - Use a description that helps you decide whether the CMK is appropriate for a task.
    type: str
  multi_region:
    description:
      -  Whether to create a multi-Region primary key or not.
    default: false
    type: bool
    version_added: 5.5.0
  pending_window:
    description:
      - The number of days between requesting deletion of the CMK and when it will actually be deleted.
      - Only used when O(state=absent) and the CMK has not yet been deleted.
      - Valid values are between V(7) and V(30) (inclusive).
      - 'See also: U(https://docs.aws.amazon.com/kms/latest/APIReference/API_ScheduleKeyDeletion.html#KMS-ScheduleKeyDeletion-request-PendingWindowInDays)'
    type: int
    aliases: ['deletion_delay']
    version_added: 1.4.0
    version_added_collection: community.aws
  purge_grants:
    description:
      - Whether the O(grants) argument should cause grants not in the list to be removed.
    default: false
    type: bool
  grants:
    description:
      - A list of grants to apply to the key. Each item must contain O(grants.grantee_principal).
        Each item can optionally contain O(grants.retiring_principal), O(grants.operations), O(grants.constraints),
        O(grants.name).
      - O(grants.grantee_principal) and O(grants.retiring_principal) must be ARNs.
      - 'For full documentation of suboptions see the boto3 documentation:'
      - 'U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.create_grant)'
    type: list
    elements: dict
    default: []
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
              - Constraints is a dict containing V(encryption_context_subset) or V(encryption_context_equals),
                either or both being a dict specifying an encryption context match.
                See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html) or
                U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.create_grant)
            type: dict
        name:
            description:
              - A friendly name for the grant.
              - Use this value to prevent the unintended creation of duplicate grants when retrying this request.
            type: str
  policy:
    description:
      - Policy to apply to the KMS key.
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
    version_added_collection: community.aws
  key_usage:
    description:
      - Determines the cryptographic operations for which you can use the KMS key.
      - The usage is not changeable once the key is created.
    type: str
    default: ENCRYPT_DECRYPT
    choices: ['ENCRYPT_DECRYPT', 'SIGN_VERIFY']
    version_added: 2.1.0
    version_added_collection: community.aws
author:
  - Ted Timmons (@tedder)
  - Will Thames (@willthames)
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3

notes:
  - There are known inconsistencies in the amount of time required for updates of KMS keys to be fully reflected on AWS.
    This can cause issues when running duplicate tasks in succession or using the M(amazon.aws.kms_key_info) module to fetch key metadata
    shortly after modifying keys.
    For this reason, it is recommended to use the return data from this module (M(amazon.aws.kms_key)) to fetch a key's metadata.
  - The C(policies) return key was removed in amazon.aws release 8.0.0.
"""

EXAMPLES = r"""
# Create a new KMS key
- amazon.aws.kms_key:
    alias: mykey
    tags:
      Name: myKey
      Purpose: protect_stuff

# Create a new multi-region KMS key
- amazon.aws.kms_key:
    alias: mykey
    multi_region: true
    tags:
      Name: myKey
      Purpose: protect_stuff

# Update previous key with more tags
- amazon.aws.kms_key:
    alias: mykey
    tags:
      Name: myKey
      Purpose: protect_stuff
      Owner: security_team

# Update a known key with grants allowing an instance with the billing-prod IAM profile
# to decrypt data encrypted with the environment: production, application: billing
# encryption context
- amazon.aws.kms_key:
    key_id: abcd1234-abcd-1234-5678-ef1234567890
    grants:
      - name: billing_prod
        grantee_principal: arn:aws:iam::123456789012:role/billing_prod
        constraints:
          encryption_context_equals:
            environment: production
            application: billing
        operations:
          - Decrypt
          - RetireGrant

- name: Update IAM policy on an existing KMS key
  amazon.aws.kms_key:
    alias: my-kms-key
    policy: '{"Version": "2012-10-17", "Id": "my-kms-key-permissions", "Statement": [ { <SOME STATEMENT> } ]}'
    state: present

- name: Example using lookup for policy json
  amazon.aws.kms_key:
    alias: my-kms-key
    policy: "{{ lookup('template', 'kms_iam_policy_template.json.j2') }}"
    state: present
"""

RETURN = r"""
key_id:
  description: ID of key.
  type: str
  returned: always
  sample: "abcd1234-abcd-1234-5678-ef1234567890"
key_arn:
  description: ARN of key.
  type: str
  returned: always
  sample: "arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890"
key_state:
  description:
    - The state of the key.
    - Will be one of C('Creating'), C('Enabled'), C('Disabled'), C('PendingDeletion'), C('PendingImport'),
      C('PendingReplicaDeletion'), C('Unavailable'), or C('Updating').
  type: str
  returned: always
  sample: "PendingDeletion"
key_usage:
  description: The cryptographic operations for which you can use the key.
  type: str
  returned: always
  sample: "ENCRYPT_DECRYPT"
origin:
  description: The source of the key's key material. When this value is C(AWS_KMS),
    AWS KMS created the key material. When this value is C(EXTERNAL), the
    key material was imported or the CMK lacks key material.
  type: str
  returned: always
  sample: "AWS_KMS"
aws_account_id:
  description: The AWS Account ID that the key belongs to.
  type: str
  returned: always
  sample: "1234567890123"
creation_date:
  description: Date and time of creation of the key.
  type: str
  returned: always
  sample: "2017-04-18T15:12:08.551000+10:00"
deletion_date:
  description: Date and time after which KMS deletes this KMS key.
  type: str
  returned: when RV(key_state) is PendingDeletion
  sample: "2017-04-18T15:12:08.551000+10:00"
  version_added: 3.3.0
  version_added_collection: community.aws
description:
  description: Description of the key.
  type: str
  returned: always
  sample: "My Key for Protecting important stuff"
enabled:
  description: Whether the key is enabled. True if RV(key_state) is V(Enabled).
  type: bool
  returned: always
  sample: false
enable_key_rotation:
  description: Whether the automatic annual key rotation is enabled. Returns None if key rotation status can't be determined.
  type: bool
  returned: always
  sample: false
aliases:
  description: List of aliases associated with the key.
  type: list
  returned: always
  sample:
    - aws/acm
    - aws/ebs
key_policies:
  description: List of policy documents for the key. Empty when access is denied even if there are policies.
  type: list
  returned: always
  elements: dict
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
          kms:CallerAccount: "123456789012"
          kms:ViaService: "ec2.ap-southeast-2.amazonaws.com"
    - Sid: "Allow direct access to key metadata to the account"
      Effect: "Allow"
      Principal:
        AWS: "arn:aws:iam::123456789012:root"
      Action:
      - "kms:Describe*"
      - "kms:Get*"
      - "kms:List*"
      - "kms:RevokeGrant"
      Resource: "*"
  version_added: 3.3.0
  version_added_collection: community.aws
tags:
  description: Dictionary of tags applied to the key. Empty when access is denied even if there are tags.
  type: dict
  returned: always
  sample:
    Name: myKey
    Purpose: protecting_stuff
grants:
  description: List of grants associated with a key.
  type: list
  elements: dict
  returned: always
  contains:
    constraints:
      description: Constraints on the encryption context that the grant allows.
        See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html) for further details
      type: dict
      returned: always
      sample:
        encryption_context_equals:
           "aws:lambda:_function_arn": "arn:aws:lambda:ap-southeast-2:123456789012:function:xyz"
    creation_date:
      description: Date of creation of the grant.
      type: str
      returned: always
      sample: "2017-04-18T15:12:08+10:00"
    grant_id:
      description: The unique ID for the grant.
      type: str
      returned: always
      sample: "abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234"
    grantee_principal:
      description: The principal that receives the grant's permissions.
      type: str
      returned: always
      sample: "arn:aws:sts::123456789012:assumed-role/lambda_xyz/xyz"
    issuing_account:
      description: The AWS account under which the grant was issued.
      type: str
      returned: always
      sample: "arn:aws:iam::123456789012:root"
    key_id:
      description: The key ARN to which the grant applies.
      type: str
      returned: always
      sample: "arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890"
    name:
      description: The friendly name that identifies the grant.
      type: str
      returned: always
      sample: "xyz"
    operations:
      description: The list of operations permitted by the grant.
      type: list
      returned: always
      sample:
        - Decrypt
        - RetireGrant
    retiring_principal:
      description: The principal that can retire the grant.
      type: str
      returned: always
      sample: "arn:aws:sts::123456789012:assumed-role/lambda_xyz/xyz"
changes_needed:
  description: Grant types that would be changed/were changed.
  type: dict
  returned: always
  sample: { "role": "add", "role grant": "add" }
had_invalid_entries:
  description: Whether there are invalid (non-ARN) entries in the KMS entry. These don't count as a change, but will be removed if any changes are being made.
  type: bool
  returned: always
multi_region:
  description:
    - Indicates whether the CMK is a multi-Region C(True) or regional C(False) key.
    - This value is True for multi-Region primary and replica CMKs and False for regional CMKs.
  type: bool
  version_added: 5.5.0
  returned: always
  sample: False
customer_master_key_spec:
  description: Specifies the type of KMS key to create.
  type: str
  returned: always
  sample: "SYMMETRIC_DEFAULT"
encryption_algorithms:
  description: The encryption algorithms that the KMS key supports.
  type: list
  elements: str
  returned: always
  sample: ["SYMMETRIC_DEFAULT"]
key_manager:
  description: The manager of the KMS key.
  type: str
  returned: always
  sample: "AWS"
key_spec:
  description: Specifies the type of KMS key to create.
  type: str
  returned: always
  sample: "SYMMETRIC_DEFAULT"
"""

import json

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_keys_with_backoff(connection):
    paginator = connection.get_paginator("list_keys")
    return paginator.paginate().build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_aliases_with_backoff(connection):
    paginator = connection.get_paginator("list_aliases")
    return paginator.paginate().build_full_result()


def get_kms_aliases_lookup(connection):
    _aliases = dict()
    for alias in get_kms_aliases_with_backoff(connection)["Aliases"]:
        # Not all aliases are actually associated with a key
        if "TargetKeyId" in alias:
            # strip off leading 'alias/' and add it to key's aliases
            if alias["TargetKeyId"] in _aliases:
                _aliases[alias["TargetKeyId"]].append(alias["AliasName"][6:])
            else:
                _aliases[alias["TargetKeyId"]] = [alias["AliasName"][6:]]
    return _aliases


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_tags_with_backoff(connection, key_id, **kwargs):
    return connection.list_resource_tags(KeyId=key_id, **kwargs)


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_grants_with_backoff(connection, key_id):
    params = dict(KeyId=key_id)
    paginator = connection.get_paginator("list_grants")
    return paginator.paginate(**params).build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_metadata_with_backoff(connection, key_id):
    return connection.describe_key(KeyId=key_id)


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def list_key_policies_with_backoff(connection, key_id):
    paginator = connection.get_paginator("list_key_policies")
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
            tags.extend(tag_response["Tags"])
        except is_boto3_error_code("AccessDeniedException"):
            tag_response = {}
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to obtain key tags")
        if tag_response.get("NextMarker"):
            kwargs["Marker"] = tag_response["NextMarker"]
        else:
            more = False
    return tags


def get_kms_policies(connection, module, key_id):
    try:
        policies = list_key_policies_with_backoff(connection, key_id)["PolicyNames"]
        return [get_key_policy_with_backoff(connection, key_id, policy)["Policy"] for policy in policies]
    except is_boto3_error_code("AccessDeniedException"):
        return []
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain key policies")


def camel_to_snake_grant(grant):
    """camel_to_snake_grant snakifies everything except the encryption context"""
    constraints = grant.get("Constraints", {})
    result = camel_dict_to_snake_dict(grant)
    if "EncryptionContextEquals" in constraints:
        result["constraints"]["encryption_context_equals"] = constraints["EncryptionContextEquals"]
    if "EncryptionContextSubset" in constraints:
        result["constraints"]["encryption_context_subset"] = constraints["EncryptionContextSubset"]
    return result


def get_key_details(connection, module, key_id):
    try:
        result = get_kms_metadata_with_backoff(connection, key_id)["KeyMetadata"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain key metadata")
    result["KeyArn"] = result.pop("Arn")

    try:
        aliases = get_kms_aliases_lookup(connection)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain aliases")

    try:
        current_rotation_status = connection.get_key_rotation_status(KeyId=key_id)
        result["enable_key_rotation"] = current_rotation_status.get("KeyRotationEnabled")
    except is_boto3_error_code(["AccessDeniedException", "UnsupportedOperationException"]):
        result["enable_key_rotation"] = None
    result["aliases"] = aliases.get(result["KeyId"], [])

    result = camel_dict_to_snake_dict(result)

    # grants and tags get snakified differently
    try:
        result["grants"] = [
            camel_to_snake_grant(grant) for grant in get_kms_grants_with_backoff(connection, key_id)["Grants"]
        ]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain key grants")
    tags = get_kms_tags(connection, module, key_id)
    result["tags"] = boto3_tag_list_to_ansible_dict(tags, "TagKey", "TagValue")
    policies = get_kms_policies(connection, module, key_id)
    result["key_policies"] = [json.loads(policy) for policy in policies]
    return result


def convert_grant_params(grant, key):
    grant_params = dict(KeyId=key["key_arn"], GranteePrincipal=grant["grantee_principal"])
    if grant.get("operations"):
        grant_params["Operations"] = grant["operations"]
    if grant.get("retiring_principal"):
        grant_params["RetiringPrincipal"] = grant["retiring_principal"]
    if grant.get("name"):
        grant_params["Name"] = grant["name"]
    if grant.get("constraints"):
        grant_params["Constraints"] = dict()
        if grant["constraints"].get("encryption_context_subset"):
            grant_params["Constraints"]["EncryptionContextSubset"] = grant["constraints"]["encryption_context_subset"]
        if grant["constraints"].get("encryption_context_equals"):
            grant_params["Constraints"]["EncryptionContextEquals"] = grant["constraints"]["encryption_context_equals"]
    return grant_params


def different_grant(existing_grant, desired_grant):
    if existing_grant.get("grantee_principal") != desired_grant.get("grantee_principal"):
        return True
    if existing_grant.get("retiring_principal") != desired_grant.get("retiring_principal"):
        return True
    if set(existing_grant.get("operations", [])) != set(desired_grant.get("operations")):
        return True
    if existing_grant.get("constraints") != desired_grant.get("constraints"):
        return True
    return False


def compare_grants(existing_grants, desired_grants, purge_grants=False):
    existing_dict = dict((eg["name"], eg) for eg in existing_grants)
    desired_dict = dict((dg["name"], dg) for dg in desired_grants)
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
    if key_metadata["KeyState"] == "PendingDeletion":
        return False

    if module.check_mode:
        return True

    deletion_params = {"KeyId": key_metadata["Arn"]}
    if module.params.get("pending_window"):
        deletion_params["PendingWindowInDays"] = module.params.get("pending_window")

    try:
        connection.schedule_key_deletion(**deletion_params)
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to schedule key for deletion")


def cancel_key_deletion(connection, module, key):
    key_id = key["key_arn"]
    if key["key_state"] != "PendingDeletion":
        return False

    if module.check_mode:
        return True

    try:
        connection.cancel_key_deletion(KeyId=key_id)
        # key is disabled after deletion cancellation
        # set this so that ensure_enabled_disabled works correctly
        key["key_state"] = "Disabled"
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to cancel key deletion")

    return True


def ensure_enabled_disabled(connection, module, key, enabled):
    desired_state = "Enabled"
    if not enabled:
        desired_state = "Disabled"

    if key["key_state"] == desired_state:
        return False

    key_id = key["key_arn"]
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

    key_id = key["key_arn"]
    aliases = get_kms_aliases_with_backoff(connection)["Aliases"]
    # We will only add new aliases, not rename existing ones
    if alias in [_alias["AliasName"] for _alias in aliases]:
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
    if key["description"] == description:
        return False

    key_id = key["key_arn"]
    if not module.check_mode:
        try:
            connection.update_key_description(KeyId=key_id, Description=description)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to update key description")

    return True


def update_tags(connection, module, key, desired_tags, purge_tags):
    if desired_tags is None:
        return False

    to_add, to_remove = compare_aws_tags(key["tags"], desired_tags, purge_tags)
    if not (bool(to_add) or bool(to_remove)):
        return False

    key_id = key["key_arn"]
    if not module.check_mode:
        if to_remove:
            try:
                connection.untag_resource(KeyId=key_id, TagKeys=to_remove)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to remove tag")
        if to_add:
            try:
                tags = ansible_dict_to_boto3_tag_list(
                    module.params["tags"],
                    tag_name_key_name="TagKey",
                    tag_value_key_name="TagValue",
                )
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

    key_id = key["key_arn"]
    try:
        keyret = connection.get_key_policy(KeyId=key_id, PolicyName="default")
        original_policy = json.loads(keyret["Policy"])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        # If we can't fetch the current policy assume we're making a change
        # Could occur if we have PutKeyPolicy without GetKeyPolicy
        original_policy = {}

    if not compare_policies(original_policy, new_policy):
        return False

    if not module.check_mode:
        try:
            connection.put_key_policy(KeyId=key_id, PolicyName="default", Policy=policy)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to update key policy")

    return True


def update_key_rotation(connection, module, key, enable_key_rotation):
    if enable_key_rotation is None:
        return False
    key_id = key["key_arn"]

    try:
        current_rotation_status = connection.get_key_rotation_status(KeyId=key_id)
        if current_rotation_status.get("KeyRotationEnabled") == enable_key_rotation:
            return False
    except is_boto3_error_code("AccessDeniedException"):
        pass
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Unable to get current key rotation status")

    if not module.check_mode:
        try:
            if enable_key_rotation:
                connection.enable_key_rotation(KeyId=key_id)
            else:
                connection.disable_key_rotation(KeyId=key_id)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to enable/disable key rotation")

    return True


def update_grants(connection, module, key, desired_grants, purge_grants):
    existing_grants = key["grants"]

    to_add, to_remove = compare_grants(existing_grants, desired_grants, purge_grants)
    if not (bool(to_add) or bool(to_remove)):
        return False

    key_id = key["key_arn"]
    if not module.check_mode:
        for grant in to_remove:
            try:
                connection.retire_grant(KeyId=key_id, GrantId=grant["grant_id"])
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
    changed |= ensure_enabled_disabled(connection, module, key, module.params["enabled"])
    changed |= update_alias(connection, module, key, module.params["alias"])
    changed |= update_description(connection, module, key, module.params["description"])
    changed |= update_tags(connection, module, key, module.params["tags"], module.params.get("purge_tags"))
    changed |= update_policy(connection, module, key, module.params.get("policy"))
    changed |= update_grants(connection, module, key, module.params.get("grants"), module.params.get("purge_grants"))
    changed |= update_key_rotation(connection, module, key, module.params.get("enable_key_rotation"))

    # make results consistent with kms_facts before returning
    result = get_key_details(connection, module, key["key_arn"])
    result["changed"] = changed
    return result


def create_key(connection, module):
    key_usage = module.params.get("key_usage")
    key_spec = module.params.get("key_spec")
    multi_region = module.params.get("multi_region")
    tags_list = ansible_dict_to_boto3_tag_list(
        module.params["tags"] or {},
        # KMS doesn't use 'Key' and 'Value' as other APIs do.
        tag_name_key_name="TagKey",
        tag_value_key_name="TagValue",
    )
    params = dict(
        BypassPolicyLockoutSafetyCheck=False,
        Tags=tags_list,
        KeyUsage=key_usage,
        CustomerMasterKeySpec=key_spec,
        Origin="AWS_KMS",
        MultiRegion=multi_region,
    )

    if module.check_mode:
        return {"changed": True}

    if module.params.get("description"):
        params["Description"] = module.params["description"]
    if module.params.get("policy"):
        params["Policy"] = module.params["policy"]
    try:
        result = connection.create_key(**params)["KeyMetadata"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create initial key")

    key = get_key_details(connection, module, result["KeyId"])
    update_alias(connection, module, key, module.params["alias"])
    update_key_rotation(connection, module, key, module.params.get("enable_key_rotation"))

    ensure_enabled_disabled(connection, module, key, module.params.get("enabled"))
    update_grants(connection, module, key, module.params.get("grants"), False)

    # make results consistent with kms_facts
    result = get_key_details(connection, module, key["key_id"])
    result["changed"] = True
    return result


def delete_key(connection, module, key_metadata):
    changed = False

    changed |= start_key_deletion(connection, module, key_metadata)

    result = get_key_details(connection, module, key_metadata["Arn"])
    result["changed"] = changed
    return result


def canonicalize_alias_name(alias):
    if alias is None:
        return None
    if alias.startswith("alias/"):
        return alias
    return "alias/" + alias


def fetch_key_metadata(connection, module, key_id, alias):
    # Note - fetching a key's metadata is very inconsistent shortly after any sort of update to a key has occurred.
    # Combinations of manual waiters, checking expecting key values to actual key value, and static sleeps
    #        have all been exhausted, but none of those available options have solved the problem.
    # Integration tests will wait for 10 seconds to combat this issue.
    # See https://github.com/ansible-collections/community.aws/pull/1052.

    alias = canonicalize_alias_name(module.params.get("alias"))

    try:
        # Fetch by key_id where possible
        if key_id:
            return get_kms_metadata_with_backoff(connection, key_id)["KeyMetadata"]
        # Or try alias as a backup
        return get_kms_metadata_with_backoff(connection, alias)["KeyMetadata"]

    except connection.exceptions.NotFoundException:
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to fetch key metadata.")


def validate_params(module, key_metadata):
    # We can't create keys with a specific ID, if we can't access the key we'll have to fail
    if module.params.get("state") == "present" and module.params.get("key_id") and not key_metadata:
        module.fail_json(msg=f"Could not find key with id {module.params.get('key_id')} to update")
    if module.params.get("multi_region") and key_metadata and module.params.get("state") == "present":
        module.fail_json(msg="You cannot change the multi-region property on an existing key.")


def main():
    argument_spec = dict(
        alias=dict(aliases=["key_alias"]),
        pending_window=dict(aliases=["deletion_delay"], type="int"),
        key_id=dict(aliases=["key_arn"]),
        description=dict(),
        enabled=dict(type="bool", default=True),
        multi_region=dict(type="bool", default=False),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        grants=dict(type="list", default=[], elements="dict"),
        policy=dict(type="json"),
        purge_grants=dict(type="bool", default=False),
        state=dict(default="present", choices=["present", "absent"]),
        enable_key_rotation=(dict(type="bool")),
        key_spec=dict(
            type="str",
            default="SYMMETRIC_DEFAULT",
            aliases=["customer_master_key_spec"],
            choices=[
                "SYMMETRIC_DEFAULT",
                "RSA_2048",
                "RSA_3072",
                "RSA_4096",
                "ECC_NIST_P256",
                "ECC_NIST_P384",
                "ECC_NIST_P521",
                "ECC_SECG_P256K1",
            ],
        ),
        key_usage=dict(
            type="str",
            default="ENCRYPT_DECRYPT",
            choices=["ENCRYPT_DECRYPT", "SIGN_VERIFY"],
        ),
    )

    module = AnsibleAWSModule(
        supports_check_mode=True,
        argument_spec=argument_spec,
        required_one_of=[["alias", "key_id"]],
    )

    kms = module.client("kms")

    key_metadata = fetch_key_metadata(kms, module, module.params.get("key_id"), module.params.get("alias"))
    validate_params(module, key_metadata)

    if module.params.get("state") == "absent":
        if key_metadata is None:
            module.exit_json(changed=False)
        result = delete_key(kms, module, key_metadata)
        module.exit_json(**result)

    if key_metadata:
        key_details = get_key_details(kms, module, key_metadata["Arn"])
        result = update_key(kms, module, key_details)
        module.exit_json(**result)

    result = create_key(kms, module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: kms_key_info
version_added: 5.0.0
short_description: Gather information about AWS KMS keys
description:
  - Gather information about AWS KMS keys including tags and grants.
  - Prior to release 5.0.0 this module was called M(community.aws.aws_kms_info).
    The usage did not change.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - "Will Thames (@willthames)"
options:
  alias:
    description:
      - Alias for key.
      - Mutually exclusive with O(key_id) and O(filters).
    required: false
    aliases:
      - key_alias
    type: str
    version_added: 1.4.0
    version_added_collection: community.aws
  key_id:
    description:
      - Key ID or ARN of the key.
      - Mutually exclusive with O(alias) and O(filters).
    required: false
    aliases:
      - key_arn
    type: str
    version_added: 1.4.0
    version_added_collection: community.aws
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        The filters aren't natively supported by boto3, but are supported to provide similar
        functionality to other modules. Standard tag filters (V(tag-key), V(tag-value) and
        V(tag:tagName)) are available, as are V(key-id) and V(alias)
      - Mutually exclusive with O(alias) and O(key_id).
    type: dict
  pending_deletion:
    description: Whether to get full details (tags, grants etc.) of keys pending deletion.
    default: false
    type: bool
notes:
  - The C(policies) return key was removed in amazon.aws release 8.0.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all KMS keys
- amazon.aws.kms_key_info:

# Gather information about all keys with a Name tag
- amazon.aws.kms_key_info:
    filters:
      tag-key: Name

# Gather information about all keys with a specific name
- amazon.aws.kms_key_info:
    filters:
      "tag:Name": Example
"""

RETURN = r"""
kms_keys:
  description: List of keys.
  type: complex
  returned: always
  contains:
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
      sample: "123456789012"
    creation_date:
      description: Date and time of creation of the key.
      type: str
      returned: always
      sample: "2017-04-18T15:12:08.551000+10:00"
    deletion_date:
      description: Date and time after which KMS deletes this KMS key.
      type: str
      returned: when RV(kms_keys.key_state) is PendingDeletion
      sample: "2017-04-18T15:12:08.551000+10:00"
      version_added: 3.3.0
      version_added_collection: community.aws
    description:
      description: Description of the key.
      type: str
      returned: always
      sample: "My Key for Protecting important stuff"
    enabled:
      description: Whether the key is enabled. True if RV(kms_keys.key_state) is V(Enabled).
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
    tags:
      description: Dictionary of tags applied to the key. Empty when access is denied even if there are tags.
      type: dict
      returned: always
      sample:
        Name: myKey
        Purpose: protecting_stuff
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
          elements: str
          returned: always
          sample: [
                      "Decrypt",
                      "GenerateDataKey"
                  ]
        retiring_principal:
          description: The principal that can retire the grant.
          type: str
          returned: always
          sample: "arn:aws:sts::123456789012:assumed-role/lambda_xyz/xyz"
    customer_master_key_spec:
      description: Describes the type of key material in the KMS key.
      type: str
      returned: always
      sample: "SYMMETRIC_DEFAULT"
    encryption_algorithms:
      description: The encryption algorithms that the KMS key supports.
      type: list
      elements: str
      returned: always
      sample: ["SYMMETRIC_DEFAULT"]
    multi_region:
      description: Indicates whether the KMS key is a multi-Region (True) or regional (False) key.
      type: bool
      returned: always
      sample: false
"""

from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSError
from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSPermissionsError
from ansible_collections.amazon.aws.plugins.module_utils.kms import canonicalize_alias_name
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_key_details as _get_key_details
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_kms_keys
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def key_matches_filter(key, filtr):
    if filtr[0] == "key-id":
        return filtr[1] == key["key_id"]
    if filtr[0] == "tag-key":
        return filtr[1] in key["tags"]
    if filtr[0] == "tag-value":
        return filtr[1] in key["tags"].values()
    if filtr[0] == "alias":
        return filtr[1] in key["aliases"]
    if filtr[0].startswith("tag:"):
        tag_key = filtr[0][4:]
        if tag_key not in key["tags"]:
            return False
        return key["tags"].get(tag_key) == filtr[1]


def key_matches_filters(key, filters):
    if not filters:
        return True
    else:
        return all(key_matches_filter(key, filtr) for filtr in filters.items())


def get_key_details(connection, module, key_id, tokens=None):
    """
    Wrapper around module_utils get_key_details that handles permission errors with module warnings.

    Args:
        connection: boto3 KMS client
        module: AnsibleAWSModule instance for warnings
        key_id: KMS key ID, ARN, or alias
        tokens: optional list of grant tokens

    Returns:
        Dictionary with key details or None if not found/permission denied
    """
    if not tokens:
        tokens = None  # Normalize empty list to None

    try:
        return _get_key_details(
            connection, key_id, grant_tokens=tokens, pending_deletion=module.params.get("pending_deletion", False)
        )
    except AnsibleKMSPermissionsError as e:
        module.warn(str(e))
        return None


def get_kms_info(connection, module):
    if module.params.get("key_id"):
        key_id = module.params.get("key_id")
        details = get_key_details(connection, module, key_id)
        if details:
            return [details]
        return []
    elif module.params.get("alias"):
        alias = canonicalize_alias_name(module.params.get("alias"))
        details = get_key_details(connection, module, alias)
        if details:
            return [details]
        return []
    else:
        keys = get_kms_keys(connection)["Keys"]
        return [get_key_details(connection, module, key["KeyId"]) for key in keys]


def main():
    argument_spec = dict(
        alias=dict(aliases=["key_alias"]),
        key_id=dict(aliases=["key_arn"]),
        filters=dict(type="dict"),
        pending_deletion=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, mutually_exclusive=[["alias", "filters", "key_id"]], supports_check_mode=True
    )

    try:
        connection = module.client("kms")

        all_keys = get_kms_info(connection, module)
        filtered_keys = [key for key in all_keys if key_matches_filters(key, module.params["filters"])]
        ret_params = dict(kms_keys=filtered_keys)

        module.exit_json(**ret_params)
    except AnsibleKMSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

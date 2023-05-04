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
  - Prior to release 5.0.0 this module was called C(community.aws.aws_kms_info).
    The usage did not change.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - "Will Thames (@willthames)"
options:
  alias:
    description:
      - Alias for key.
      - Mutually exclusive with I(key_id) and I(filters).
    required: false
    aliases:
      - key_alias
    type: str
    version_added: 1.4.0
    version_added_collection: community.aws
  key_id:
    description:
      - Key ID or ARN of the key.
      - Mutually exclusive with I(alias) and I(filters).
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
        functionality to other modules. Standard tag filters (C(tag-key), C(tag-value) and
        C(tag:tagName)) are available, as are C(key-id) and C(alias)
      - Mutually exclusive with I(alias) and I(key_id).
    type: dict
  pending_deletion:
    description: Whether to get full details (tags, grants etc.) of keys pending deletion.
    default: False
    type: bool
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
      sample: abcd1234-abcd-1234-5678-ef1234567890
    key_arn:
      description: ARN of key.
      type: str
      returned: always
      sample: arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890
    key_state:
      description:
        - The state of the key.
        - Will be one of C('Creating'), C('Enabled'), C('Disabled'), C('PendingDeletion'), C('PendingImport'),
          C('PendingReplicaDeletion'), C('Unavailable'), or C('Updating').
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
      description: The AWS Account ID that the key belongs to.
      type: str
      returned: always
      sample: 123456789012
    creation_date:
      description: Date and time of creation of the key.
      type: str
      returned: always
      sample: "2017-04-18T15:12:08.551000+10:00"
    deletion_date:
      description: Date and time after which KMS deletes this KMS key.
      type: str
      returned: when key_state is PendingDeletion
      sample: "2017-04-18T15:12:08.551000+10:00"
      version_added: 3.3.0
      version_added_collection: community.aws
    description:
      description: Description of the key.
      type: str
      returned: always
      sample: "My Key for Protecting important stuff"
    enabled:
      description: Whether the key is enabled. True if I(key_state) is C(Enabled).
      type: bool
      returned: always
      sample: false
    enable_key_rotation:
      description: Whether the automatic annual key rotation is enabled. Returns None if key rotation status can't be determined.
      type: bool
      returned: always
      sample: false
    aliases:
      description: list of aliases associated with the key.
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
    policies:
      description: List of policy documents for the key. Empty when access is denied even if there are policies.
      type: list
      returned: always
      elements: str
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
          sample: abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234
        grantee_principal:
          description: The principal that receives the grant's permissions.
          type: str
          returned: always
          sample: arn:aws:sts::123456789012:assumed-role/lambda_xyz/xyz
        issuing_account:
          description: The AWS account under which the grant was issued.
          type: str
          returned: always
          sample: arn:aws:iam::123456789012:root
        key_id:
          description: The key ARN to which the grant applies.
          type: str
          returned: always
          sample: arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890
        name:
          description: The friendly name that identifies the grant.
          type: str
          returned: always
          sample: xyz
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
          sample: arn:aws:sts::123456789012:assumed-role/lambda_xyz/xyz
"""

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

# Caching lookup for aliases
_aliases = dict()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_keys_with_backoff(connection):
    paginator = connection.get_paginator("list_keys")
    return paginator.paginate().build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_kms_aliases_with_backoff(connection):
    paginator = connection.get_paginator("list_aliases")
    return paginator.paginate().build_full_result()


def get_kms_aliases_lookup(connection):
    if not _aliases:
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
def get_kms_grants_with_backoff(connection, key_id, **kwargs):
    params = dict(KeyId=key_id)
    if kwargs.get("tokens"):
        params["GrantTokens"] = kwargs["tokens"]
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


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def get_enable_key_rotation_with_backoff(connection, key_id):
    try:
        current_rotation_status = connection.get_key_rotation_status(KeyId=key_id)
    except is_boto3_error_code(["AccessDeniedException", "UnsupportedOperationException"]):
        return None

    return current_rotation_status.get("KeyRotationEnabled")


def canonicalize_alias_name(alias):
    if alias is None:
        return None
    if alias.startswith("alias/"):
        return alias
    return "alias/" + alias


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
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
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
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain key policies")


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
    if not tokens:
        tokens = []
    try:
        result = get_kms_metadata_with_backoff(connection, key_id)["KeyMetadata"]
        # Make sure we have the canonical ARN, we might have been passed an alias
        key_id = result["Arn"]
    except is_boto3_error_code("NotFoundException"):
        return None
    except is_boto3_error_code("AccessDeniedException"):  # pylint: disable=duplicate-except
        module.warn(f"Permission denied fetching key metadata ({key_id})")
        return None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain key metadata")
    result["KeyArn"] = result.pop("Arn")

    try:
        aliases = get_kms_aliases_lookup(connection)
    except is_boto3_error_code("AccessDeniedException"):
        module.warn("Permission denied fetching key aliases")
        aliases = {}
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain aliases")
    # We can only get aliases for our own account, so we don't need the full ARN
    result["aliases"] = aliases.get(result["KeyId"], [])
    result["enable_key_rotation"] = get_enable_key_rotation_with_backoff(connection, key_id)

    if module.params.get("pending_deletion"):
        return camel_dict_to_snake_dict(result)

    try:
        result["grants"] = get_kms_grants_with_backoff(connection, key_id, tokens=tokens)["Grants"]
    except is_boto3_error_code("AccessDeniedException"):
        module.warn(f"Permission denied fetching key grants ({key_id})")
        result["grants"] = []
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain key grants")

    tags = get_kms_tags(connection, module, key_id)

    result = camel_dict_to_snake_dict(result)
    result["tags"] = boto3_tag_list_to_ansible_dict(tags, "TagKey", "TagValue")
    result["policies"] = get_kms_policies(connection, module, key_id)
    result["key_policies"] = [json.loads(policy) for policy in result["policies"]]
    return result


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
        try:
            keys = get_kms_keys_with_backoff(connection)["Keys"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to obtain keys")
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
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    module.deprecate(
        (
            "The 'policies' return key is deprecated and will be replaced by 'key_policies'. Both values are returned"
            " for now."
        ),
        date="2024-05-01",
        collection_name="amazon.aws",
    )

    all_keys = get_kms_info(connection, module)
    filtered_keys = [key for key in all_keys if key_matches_filters(key, module.params["filters"])]
    ret_params = dict(kms_keys=filtered_keys)

    module.exit_json(**ret_params)


if __name__ == "__main__":
    main()

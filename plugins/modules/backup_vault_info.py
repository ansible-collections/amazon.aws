#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_vault_info
version_added: 6.0.0
short_description: Describe AWS Backup Vaults
description:
  - Lists info about Backup Vault configuration.
author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
options:
  backup_vault_names:
    type: list
    elements: str
    default: []
    description:
      - Specifies a list of vault names.
      - If an empty list is specified, information for the backup vaults in the current region is returned.

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all backup vaults
- amazon.aws.backup_vault_info

# Gather information about a particular backup vault
- amazon.aws.backup_vault_info:
    backup vault_names:
      - "arn:aws:backup_vault:us-east-2:123456789012:backup_vault/defaultvault"
"""

RETURN = r"""
backup_vaults:
    description: List of backup vault objects. Each element consists of a dict with all the information related to that backup vault.
    type: list
    elements: dict
    returned: always
    contains:
        backup_vault_name:
            description: Name of the backup vault.
            type: str
            sample: "default vault"
        backup_vault_arn:
            description: ARN of the backup vault.
            type: str
            sample: "arn:aws:backup:us-west-2:111122223333:vault/1234abcd-12ab-34cd-56ef-1234567890ab"
        encryption_key_arn:
            description: The server-side encryption key that is used to protect the backups.
            type: str
            sample: "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
        creation_date:
            description: The date and time a backup vault is created, in Unix format and Coordinated Universal Time (UTC).
            type: str
            sample: "1516925490.087 (represents Friday, January 26, 2018 12:11:30.087 AM)."
        creator_request_id:
            description:
              - A unique string that identifies the request and allows failed requests to be retried without the risk of running the operation twice.
            type: str
        number_of_recovery_points:
            description: The number of recovery points that are stored in a backup vault.
            type: int
        locked:
            description:
            - Indicates whether Backup Vault Lock is currently protecting the backup vault.
            - True means that Vault Lock causes delete or update operations on the recovery points stored in the vault to fail.
            type: bool
            sample: true
        min_retention_days:
            description:
            - The minimum retention period that the vault retains its recovery points.
            - If this parameter is not specified, Vault Lock does not enforce a minimum retention period.
            type: int
            sample: 120
        max_retention_days:
            description:
            - The maximum retention period that the vault retains its recovery points.
            - If this parameter is not specified, Vault Lock does not enforce a maximum retention period (allowing indefinite storage).
            type: int
            sample: 123
        lock_date:
            description: The date and time when Backup Vault Lock configuration cannot be changed or deleted.
            type: str
            sample: "1516925490.087 represents Friday, January 26, 2018 12:11:30.087 AM."

"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_backup_resource_tags


def get_backup_vaults(connection, module):
    all_backup_vaults = []
    try:
        result = connection.get_paginator("list_backup_vaults")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get the backup vaults.")
    for backup_vault in result.paginate():
        all_backup_vaults.extend(list_backup_vaults(backup_vault))
    return all_backup_vaults


def list_backup_vaults(backup_vault_dict):
    return [x["BackupVaultName"] for x in backup_vault_dict["BackupVaultList"]]


def get_backup_vault_detail(connection, module):
    output = []
    result = {}
    backup_vault_name_list = module.params.get("backup_vault_names")
    if not backup_vault_name_list:
        backup_vault_name_list = get_backup_vaults(connection, module)
    for name in backup_vault_name_list:
        try:
            output.append(connection.describe_backup_vault(BackupVaultName=name, aws_retry=True))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Failed to describe vault {name}")
    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_backup_vault = []
    for backup_vault in output:
        try:
            resource = backup_vault.get("BackupVaultArn", None)
            tag_dict = get_backup_resource_tags(module, connection, resource)
            backup_vault.update({"tags": tag_dict})
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.warn(f"Failed to get the backup vault tags - {e}")
        snaked_backup_vault.append(camel_dict_to_snake_dict(backup_vault))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for v in snaked_backup_vault:
        if "tags_list" in v:
            v["tags"] = boto3_tag_list_to_ansible_dict(v["tags_list"], "key", "value")
            del v["tags_list"]
        if "response_metadata" in v:
            del v["response_metadata"]
    result["backup_vaults"] = snaked_backup_vault
    return result


def main():
    argument_spec = dict(
        backup_vault_names=dict(type="list", elements="str", default=[]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        connection = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")
    result = get_backup_vault_detail(connection, module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

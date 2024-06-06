#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_vault
version_added: 6.0.0
short_description: Manage AWS Backup Vaults
description:
  - Creates, deletes, or lists Backup Vault configuration.
author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
options:
  state:
    description:
      - Add or remove Backup Vault configuration.
    type: str
    choices: ['present', 'absent']
    default: present
  backup_vault_name:
    description:
      - Name for the Backup Vault.
      - Names are  unique to the account used to create them and the Amazon Web Services Region where they are created.
      - They consist of letters, numbers, and hyphens.
    type: str
    required: true
  encryption_key_arn:
    description:
      - The server-side encryption key that is used to protect the backups.
    type: str
  creator_request_id:
    description:
      - A unique string that identifies the request and allows failed requests to be retried without the risk of running the operation twice.
      - If used, this parameter must contain 1 to 50 alphanumeric or "-_." characters.
    type: str

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
- name: create backup vault
  amazon.aws.backup_vault:
    state: present
    backup_vault_name: default-vault
    encryption_key_arn: arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab
    tags:
      environment: dev
      Name: default
"""

RETURN = r"""
exists:
    description: Whether the Backup Vault exists.
    returned: always
    type: bool
    sample: true
vault:
    description: Backup Vault details.
    returned: always
    type: complex
    sample: hash/dictionary of values
    contains:
        backup_vault_name:
            description: The name of a logical container where backups are stored.
            returned: always
            type: str
            sample: default-name
        backup_vault_arn:
            description: An Amazon Resource Name (ARN) that uniquely identifies a backup vault.
            returned: always
            type: str
            sample: arn:aws:backup:us-east-1:123456789012:vault:aBackupVault
        creation_date:
            description: The date and time a backup vault is created, in Unix format and Coordinated Universal Time (UTC).
            returned: always
            type: str
            sample: "2024-05-21T13:21:10.062000-07:00"
        encryption_key_arn:
            description: The server-side encryption key that is used to protect your backups.
            returned: always
            type: str
            sample: "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
        locked:
            description:
                - A Boolean that indicates whether Backup Vault Lock is currently protecting the backup vault.
                - True means that Vault Lock causes delete or update operations on the recovery points stored in the vault to fail.
            returned: always
            type: bool
            sample: false
        number_of_recovery_points:
            description: The number of recovery points that are stored in a backup vault.
            returned: always
            type: int
            sample: 0
        tags:
            description: Tags of the backup vault.
            returned: on create/update
            type: str
            sample: {
                        "TagKey1": "TagValue1",
                        "TagKey2": "TagValue2"
                    }
"""


from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.backup import get_backup_resource_tags
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule


def create_backup_vault(module, client, params):
    """
    Creates a Backup Vault

    module : AnsibleAWSModule object
    client : boto3 client connection object
    params : The parameters to create a backup vault
    """
    resp = {}
    params = {k: v for k, v in params.items() if v is not None}
    try:
        resp = client.create_backup_vault(**params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create Backup Vault")
    return resp


def tag_vault(module, client, tags, vault_arn, curr_tags=None, purge_tags=True):
    """
    Creates, updates, removes tags on a Backup Vault resource

    module : AnsibleAWSModule object
    client : boto3 client connection object
    tags : Dict of tags converted from ansible_dict to boto3 list of dicts
    vault_arn : The ARN of the Backup Vault to operate on
    curr_tags : Dict of the current tags on resource, if any
    purge_tags : true/false to determine if current tags will be retained or not
    """

    if tags is None:
        return False

    curr_tags = curr_tags or {}
    tags_to_add, tags_to_remove = compare_aws_tags(curr_tags, tags, purge_tags=purge_tags)

    if not tags_to_add and not tags_to_remove:
        return False

    if module.check_mode:
        return True

    if tags_to_remove:
        try:
            client.untag_resource(ResourceArn=vault_arn, TagKeyList=tags_to_remove)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to remove tags from the vault")

    if tags_to_add:
        try:
            client.tag_resource(ResourceArn=vault_arn, Tags=tags_to_add)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to add tags to Vault")

    return True


def get_vault_facts(module, client, vault_name):
    """
    Describes existing vault in an account

    module : AnsibleAWSModule object
    client : boto3 client connection object
    vault_name : Name of the backup vault
    """
    resp = None
    # get Backup Vault info
    try:
        resp = client.describe_backup_vault(BackupVaultName=vault_name)
    except is_boto3_error_code("AccessDeniedException"):
        module.warn("Access Denied trying to describe backup vault")
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Unable to get vault facts")

    # Now check to see if our vault exists and get status and tags
    if resp:
        if resp.get("BackupVaultArn"):
            resource = resp.get("BackupVaultArn")
            resp["tags"] = get_backup_resource_tags(module, client, resource)

        return resp

    else:
        # vault doesn't exist return None
        return None


def delete_backup_vault(module, client, vault_name):
    """
    Delete a Backup Vault

    module : AnsibleAWSModule object
    client : boto3 client connection object
    vault_name : Backup Vault Name
    """
    try:
        client.delete_backup_vault(BackupVaultName=vault_name)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to delete the Backup Vault")


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent"]),
        backup_vault_name=dict(required=True, type="str"),
        encryption_key_arn=dict(type="str", no_log=False),
        creator_request_id=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )

    required_if = [
        ("state", "present", ["backup_vault_name"]),
        ("state", "enabled", ["backup_vault_name"]),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)

    # collect parameters
    if module.params["state"] in ("present", "enabled"):
        state = "present"
    elif module.params["state"] in ("absent", "disabled"):
        state = "absent"
    tags = module.params["tags"]
    purge_tags = module.params["purge_tags"]
    ct_params = dict(
        BackupVaultName=module.params["backup_vault_name"],
        BackupVaultTags=module.params["tags"],
        EncryptionKeyArn=module.params["encryption_key_arn"],
        CreatorRequestId=module.params["creator_request_id"],
    )

    client = module.client("backup")
    results = dict(changed=False, exists=False)

    # Get existing backup vault facts
    try:
        vault = get_vault_facts(module, client, ct_params["BackupVaultName"])
    except (BotoCoreError, ClientError) as err:
        module.debug(f"Unable to get vault facts {err}")

    # If the vault exists set the result exists variable
    if vault is not None:
        results["exists"] = True

    if state == "absent" and results["exists"]:
        # If Trail exists go ahead and delete
        results["changed"] = True
        results["exists"] = False
        results["backupvault"] = dict()
        if not module.check_mode:
            delete_backup_vault(module, client, vault["BackupVaultName"])

    elif state == "present" and not results["exists"]:
        # Backup Vault doesn't exist just go create it
        results["changed"] = True
        results["exists"] = True
        if not module.check_mode:
            if tags:
                ct_params["BackupVaultTags"] = tags
            # If we aren't in check_mode then actually create it
            create_backup_vault(module, client, ct_params)

            # Get facts for newly created Backup Vault
            vault = get_vault_facts(module, client, ct_params["BackupVaultName"])

        # If we are in check mode create a fake return structure for the newly created vault
        if module.check_mode:
            vault = dict()
            vault.update(ct_params)
            vault["EncryptionKeyArn"] = ""
            vault["tags"] = tags

    elif state == "present" and results["exists"]:
        # Check if we need to update tags on resource
        tags_changed = tag_vault(
            module,
            client,
            tags=tags,
            vault_arn=vault["BackupVaultArn"],
            curr_tags=vault["tags"],
            purge_tags=purge_tags,
        )
        if tags_changed:
            updated_tags = dict()
            if not purge_tags:
                updated_tags = vault["tags"]
            updated_tags.update(tags)
            results["changed"] = True
            vault["tags"] = updated_tags

    # Populate backup vault facts in output

    if vault:
        results["vault"] = camel_dict_to_snake_dict(vault, ignore_list=["tags"])
    module.exit_json(**results)


if __name__ == "__main__":
    main()

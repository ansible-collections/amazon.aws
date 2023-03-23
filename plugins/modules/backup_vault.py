#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

DOCUMENTATION = r"""
---
module: backup_vault
version_added: 6.0.0
short_description: manage BackupVault create, delete, list
description:
  - Creates, deletes, or lists Backup Vault configuration.
author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
options:
  state:
    description:
      - Add or remove Backup Vault configuration.
      - 'The following states have been preserved for backwards compatibility: I(state=enabled) and I(state=disabled).'
      - I(state=enabled) is equivalet to I(state=present).
      - I(state=disabled) is equivalet to I(state=absent).
    type: str
    choices: ['present', 'absent', 'enabled', 'disabled']
    default: present
  backup_vault_name:
    description:
      - Name for the Backup Vault.
      - Names are  unique to the account used to create them and the Amazon Web Services Region where they are created.
      - They consist of letters, numbers, and hyphens.
    type: str
    required: true
  backup_vault_tags:
    description:
      - Metadata that you can assign to help organize the resources that you create.
      - A dictionary of tags to add or remove from the resource.
      - If the value provided for a tag key is null and I(state=absent), the tag will be removed regardless of its current value.
    type: dict
    aliases: ['tags']
  encryption_key_arn:
    description:
      - The server-side encryption key that is used to protect the backups.
    type: str
  creator_request_id:
    description:
      - A unique string that identifies the request and allows failed requests to be retried without the risk of running the operation twice.
      - If used, this parameter must contain 1 to 50 alphanumeric or ‘-_.’ characters.
    type: str
notes:
  - The I(purge_tags) option was added in release 4.0.0

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: create single region cloudtrail
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
    description: whether the resource exists
    returned: always
    type: bool
    sample: true
backup_vault:
    description: BackupVault resource details
    returned: always
    type: complex
    sample: hash/dictionary of values
    contains:
        backup_vault_name:
            description: The name of a logical container where backups are stored.
            returned: success
            type: str
            sample: default-name
        backup_vault_arn:
            description: An Amazon Resource Name (ARN) that uniquely identifies a backup vault.
            returned: success
            type: str
            sample: arn:aws:backup:us-east-1:123456789012:vault:aBackupVault
        creation_date:
            description: The date and time a backup vault is created, in Unix format and Coordinated Universal Time (UTC).
            returned: success
            type: datetime
            sample: 1516925490.087 (represents Friday, January 26, 2018 12:11:30.087 AM).
        tags:
            description: hash/dictionary of tags applied to this resource
            returned: success
            type: dict
            sample: {'environment': 'dev', 'Name': 'default'}
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
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
    try:
        resp = client.create_backup_vault(**params)
    except (
        client.Client.exceptions.InvalidParameterValueException,
        client.Client.exceptions.InvalidParameterValueException,
        client.Client.exceptions.InvalidParameterValueException,
        client.exceptions.MissingParameterValueException,
        client.Client.exceptions.ServiceUnavailableException,
        client.Client.exceptions.LimitExceededException,
        client.Client.exceptions.AlreadyExistsException,
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
    dry_run : true/false to determine if changes will be made if needed
    """

    if tags is None:
        return False

    curr_tags = curr_tags or {}

    tags_to_add, tags_to_remove = compare_aws_tags(
        curr_tags, tags, purge_tags=purge_tags)
    if not tags_to_add and not tags_to_remove:
        return False

    if module.check_mode:
        return True

    if tags_to_remove:
        remove = {k: curr_tags[k] for k in tags_to_remove}
        tags_to_remove = ansible_dict_to_boto3_tag_list(remove)
        try:
            client.remove_tags(ResourceId=vault_arn, TagsList=tags_to_remove)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(
                err, msg="Failed to remove tags from the vault")

    if tags_to_add:
        tags_to_add = ansible_dict_to_boto3_tag_list(tags_to_add)
        try:
            client.add_tags(ResourceId=vault_arn, TagsList=tags_to_add)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to add tags to Vault")

    return True


def get_tag_list(keys, tags):
    """
    Returns a list of dicts with tags to act on
    keys : set of keys to get the values for
    tags : the dict of tags to turn into a list
    """
    tag_list = []
    for k in keys:
        tag_list.append({"Key": k, "Value": tags[k]})

    return tag_list


def get_vault_facts(module, client, vault_name):
    """
    Describes existing vault in an account

    module : AnsibleAWSModule object
    client : boto3 client connection object
    name : Name of the backup vault
    """
    # get Backup Vault info
    try:
        resp = client.describe_backup_vault(vault_name)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to describe the Backup Vault")

    # Now check to see if our vault exists and get status and tags
    if resp:
        try:
            tags_list = client.list_tags(
                ResourceIdList=[resp["BackupVaultArn"]])
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(
                err, msg="Failed to describe the Backup Vault")

        resp["tags"] = boto3_tag_list_to_ansible_dict(
            tags_list["ResourceTagList"][0]["TagsList"])
        # Check for non-existent values and populate with None
        optional_vals = set(["S3KeyPrefix", "SnsTopicName", "SnsTopicARN",
                            "CloudWatchLogsLogGroupArn", "CloudWatchLogsRoleArn", "KmsKeyId"])
        for v in optional_vals - set(resp.keys()):
            resp[v] = None
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
        client.delete_backup_vault(Name=vault_name)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to delete the Backup Vault")


def main():
    argument_spec = dict(
        state=dict(default="present", choices=[
                   "present", "absent", "enabled", "disabled"]),
        backup_vault_name=dict(default="default", type="str"),
        encryption_key_arn=dict(type="str"),
        creator_request_id=dict(default="default", type="str"),
        backup_vault_tags=dict(type="dict", aliases=["tags"]),
        purge_tags=dict(default=True, type="bool"),
    )

    required_if = [("state", "present", ["backup_vault_name"]),
                   ("state", "enabled", ["backup_vault_name"])]

    module = AnsibleAWSModule(
        argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)

    # collect parameters
    if module.params["state"] in ("present", "enabled"):
        state = "present"
    elif module.params["state"] in ("absent", "disabled"):
        state = "absent"
    tags = module.params["tags"]
    purge_tags = module.params["purge_tags"]
    ct_params = dict(
        BackupVaultName=module.params["backup_vault_name"],
        BackupVaultTags=module.params["backup_vault_tags"],
        EncryptionKeyArn=module.params["encryption_key_arn"],
        CreatorRequestId=module.params["creator_request_id"],
        CreationDate=module.params["creation_date"],
    )

    client = module.client("backup")
    region = module.region

    results = dict(changed=False, exists=False)

    # Get existing backup vault facts
    vault = get_vault_facts(module, client, ct_params["BackupVaultName"])

    # If the vault exists set the result exists variable
    if vault is not None:
        results["exists"] = True

    if state == "absent" and results["exists"]:
        # If Trail exists go ahead and delete
        results["changed"] = True
        results["exists"] = False
        results["backupvault"] = dict()
        if not module.check_mode:
            delete_backup_vault(module, client, trail["BackupVaultName"])

    elif state == "present" and not results["exists"]:
        # Backup Vault doesn't exist just go create it
        results["changed"] = True
        results["exists"] = True
        if not module.check_mode:
            if tags:
                ct_params["TagsList"] = ansible_dict_to_boto3_tag_list(tags)
            # If we aren't in check_mode then actually create it
            created_vault = create_backup_vault(module, client, ct_params)

            # Get facts for newly created Backup Vault
            vault = get_vault_facts(module, client, ct_params["Name"])

        # If we are in check mode create a fake return structure for the newly created vault
        if module.check_mode:
            acct_id = "123456789012"
            try:
                sts_client = module.client("sts")
                acct_id = sts_client.get_caller_identity()["Account"]
            except (BotoCoreError, ClientError):
                pass
            vault = dict()
            vault.update(ct_params)

            fake_key_arn = "arn:aws:kms:" + region + ":" + \
                acct_id + ":key/" + ct_params["BackupVaultName"]

            vault["EncryptionKeyArn"] = fake_key_arn
            vault["tags"] = tags
        # Populate trail facts in output
        results["vault"] = camel_dict_to_snake_dict(
            vault, ignore_list=["tags"])

    module.exit_json(**results)


if __name__ == "__main__":
    main()

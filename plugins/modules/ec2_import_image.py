#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: ec2_import_image
version_added: 6.5.0
short_description: Manage AWS EC2 import image tasks
description:
  - Import single or multi-volume disk images or EBS snapshots into an Amazon Machine Image (AMI).
  - Cancel an in-process import virtual machine task.
options:
  state:
    description:
      - Use I(state=present) to import single or multi-volume disk images or EBS snapshots into an Amazon Machine Image (AMI).
      - Use I(state=absent) to cancel an in-process import virtual machine task.
    default: "present"
    choices: ["present", "absent"]
    type: str
  task_name:
    description:
      - The name of the EC2 image import task.
    type: str
  architecture:
    description:
      - The architecture of the virtual machine.
    type: str
    choices: ["i386", "x86_64"]
  client_data:
    description:
      - The client-specific data.
    type: dict
    suboptions:
        comment:
            description:
            - A user-defined comment about the disk upload.
            type: str
        upload_end:
            description:
            - The time that the disk upload ends.
            type: str
        upload_size:
            description:
            - The size of the uploaded disk image, in GiB.
            type: float
        upload_start:
            description:
            - The time that the disk upload starts.
            type: str
  description:
    description:
      - A description string for the import image task.
    type: str
  disk_containers:
    description:
      - Information about the disk containers.
    type: list
    elements: dict
  encrypted:
    description:
      - Specifies whether the destination AMI of the imported image should be encrypted.
      - The default KMS key for EBS is used unless you specify a non-default KMS key using I(kms_key_id).
    type: bool
  hypervisor:
    description:
      - The target hypervisor platform.
    default: str
    choices: ["xen"]
  wait:
    description:
      - Wait for operation to complete before returning.
    default: false
    type: bool
  wait_timeout:
    description:
      - How many seconds to wait for an operation to complete before timing out.
    default: 320
    type: int
  kms_key_id:
    description:
      - An identifier for the symmetric KMS key to use when creating the encrypted AMI.
        This parameter is only required if you want to use a non-default KMS key;
        if this parameter is not specified, the default KMS key for EBS is used.
        If a I(kms_key_id) is specified, the I(encrypted) flag must also be set.
    type: str
  license_type:
    description:
      - The license type to be used for the Amazon Machine Image (AMI) after importing.
    type: str
  platform:
    description:
      - The operating system of the virtual machine.
    type: str
    choices: ["Windows", "Linux"]
  role_name:
    description:
      - The name of the role to use when not using the default role, 'vmimport'.
    type: str
  license_specifications:
    description:
      - The ARNs of the license configurations.
    type: list
    elements: dict
  tags:
    description:
      - The tags to apply to the import image task during creation.
    type: dict
author:
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

"""

RETURN = r"""
  task_name:
    description:
      - The name of the EC2 image import task.
    type: str
  architecture:
    description:
      - The architecture of the virtual machine.
    type: str
  image_id:
    description:
      - The ID of the Amazon Machine Image (AMI) created by the import task.
    type: str
  import_task_id:
    description:
      - The task ID of the import image task.
    type: str
  progress:
    description:
      - The progress of the task.
    type: str
  snapshot_details:
    description:
      - Describes the snapshot created from the imported disk.
    type: dict
    suboptions:
        description:
            description:
            - A description for the snapshot.
            type: str
        device_name:
            description:
            - The block device mapping for the snapshot.
            type: str
        disk_image_size:
            description:
            - The size of the disk in the snapshot, in GiB.
            type: float
        format:
            description:
            - The format of the disk image from which the snapshot is created.
            type: str
        progress:
            description:
            - The percentage of progress for the task.
            type: str
        snapshot_id:
            description:
            - The snapshot ID of the disk being imported.
            type: str
        status:
            description:
            - A brief status of the snapshot creation.
            type: str
        status_message:
            description:
            - A detailed status message for the snapshot creation.
            type: str
        url:
            description:
            - The URL used to access the disk image.
            type: str
        user_bucket:
            description:
            - The Amazon S3 bucket for the disk image.
            type: dict
  status:
    description:
      - A brief status of the task.
    type: str
  status_message:
    description:
      - A detailed status message of the import task.
    type: str
  license_specifications:
    description:
      - The ARNs of the license configurations.
    type: dict
  usage_operation:
    description:
      - The usage operation value.
    type: dict
  description:
    description:
      - A description string for the import image task.
    type: str
  encrypted:
    description:
      - Specifies whether the destination AMI of the imported image should be encrypted.
      - The default KMS key for EBS is used unless you specify a non-default KMS key using I(kms_key_id).
    type: bool
  hypervisor:
    description:
      - The target hypervisor platform.
    default: str
    choices: ["xen"]
  wait:
    description:
      - Wait for operation to complete before returning.
    default: false
    type: bool
  wait_timeout:
    description:
      - How many seconds to wait for an operation to complete before timing out.
    default: 320
    type: int
  kms_key_id:
    description:
      - The identifier for the symmetric KMS key that was used to create the encrypted AMI.
    type: str
  license_type:
    description:
      - The license type to be used for the Amazon Machine Image (AMI) after importing.
    type: str
  platform:
    description:
      - The operating system of the virtual machine.
    type: str
    choices: ["Windows", "Linux"]
  role_name:
    description:
      - The name of the role to use when not using the default role, 'vmimport'.
  tags:
    description:
      - The tags to apply to the import image task during creation.
    type: dict
"""

import datetime

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

@AWSRetry.jittered_backoff(retries=10)
def _describe_import_image_tasks(**params):
    try:
        paginator = client.get_paginator("describe_import_image_tasks")
        return paginator.paginate(**params).build_full_result()["ImportImageTasks"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg"Failed to describe the import image")


def absent():
    """
    Cancel an in-process import virtual machine
    """

    filters = {
        "Filters": [
            {"Name": "name", "Values": [module.params["task_name"]]}
            {"Name": "task-state", "Values": ["active"]}
        ]
    }

    result = {"import_image": {}}
    params = {}

    if module.params.get("cancel_reason")
        params["CancelReason"] = module.params["cancel_reason"]

    import_image_info = _describe_import_image_tasks(**filters)

    if import_image_info:
        params["ImportTaskId"] = import_image_info["ImportTaskId"]

        if module.check_mode:
            module.exit_json(changed=True, msg="Would have cancelled the import task if not in check mode")

        try:
            import_image_info = client.cancel_import_task(aws_retry=True, **params)
            import_image_info["Tags"] = boto3_tag_list_to_ansible_dict(import_image_info["Tags"])
            result["import_image"] = camel_dict_to_snake_dict(import_image_info)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg"Failed to import the image")
    else:
        module.exit_json(changed=False, msg="The specified import task does not exist or it cannot be cancelled")

    module.exit_json(changed=True, **result)


def present():
    params = {}
    tags = module.params.get("tags") or {}
    tags.update({"Name": module.params["task_name"]})

    if module.params.get("architecture"):
        params["Architecture"] = module.params["architecture"]
    if module.params.get("client_data"):
        params["ClientData"] = module.params["client_data"]
    if module.params.get("description"):
        params["Description"] = module.params["description"]
    if module.params.get("disk_containers"):
        params["DiskContainers"] = module.params["disk_containers"]
    if module.params.get("encrypted"):
        params["Encrypted"] = module.params["encrypted"]
    if module.params.get("hypervisor"):
        params["Hypervisor"] = module.params["hypervisor"]
    if module.params.get("kms_key_id"):
        params["KmsKeyId"] = module.params["kms_key_id"]
    if module.params.get("license_type"):
        params["LicenseType"] = module.params["license_type"]
    if module.params.get("platform"):
        params["Platform"] = module.params["platform"]
    if module.params.get("role_name"):
        params["RoleName"] = module.params["role_name"]
    if module.params.get("license_specifications"):
        params["LicenseSpecifications"] = module.params["license_specifications"]
    if module.params.get("usage_operation"):
        params["UsageOperation"] = module.params["usage_operation"]
    if module.params.get("boot_mode"):
        params["BootMode"] = module.params.get("boot_mode")

    params["TagSpecifications"] = boto3_tag_specifications(tags, ["import-image-task"])

    wait = module.params.get("wait")
    result = {"import_image": {}}

    filters = {
        "Filters": [
            {"Name": "name", "Values": [module.params["task_name"]]}
            {"Name": "task-state", "Values": ["completed", "active"]}
        ]
    }
    import_image_info = _describe_import_image_tasks(**filters)

    if import_image_info:
        # Import tasks cannot be modified
        module.exit_json(changed=False, msg="An import task with the specified name already exists", **camel_dict_to_snake_dict(import_image_info))
    else:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have created the import task if not in check mode")

        try:
            client.import_image(aws_retry=True, **params)
            import_image_info = _describe_import_image_tasks(**filters)
            import_image_info["Tags"] = boto3_tag_list_to_ansible_dict(import_image_info["Tags"])
            result["import_image"] = camel_dict_to_snake_dict(import_image_info)
            result["import_image"]["task_name"] = module.params["task_name"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg"Failed to import the image")

    module.exit_json(changed=True, **result)


def main():
    global client
    global module

    argument_spec = dict(
        architecture=dict(type="str"),
        client_data=dict(type="dict"),
        description=dict(type="str"),
        disk_containers=dict(type="list", elements="dict"),
        encrypted=dict(type="bool"),
        state=dict(default="present", choices=["present", "absent"]),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=320, required=False),
        hypervisor=dict(type="str", choices=["xen"]),
        kms_key_id=dict(type="str"),
        license_type=dict(type="str", no_log=False),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        platform=dict(type="str", choices=["Windows", "Linux"]),
        role_name=dict(type="str"),
        license_specifications=dict(type="list", elements="dict"),
        usage_operation=dict(type="str"),
        boot_mode=dict(type="str", choices=["legacy-bios", "uefi"]),
        cancel_reason=dict(type="str"),
        task_name=dict(type="str", aliases=["name"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ["state", "absent", ["task_name"]],
            ["state", "present", ["task_name"]],
        ],
    )

    state = module.params.get("state")

    try:
        client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    if state == "present":
        present()
    else:
        absent()


if __name__ == "__main__":
    main()

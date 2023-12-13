#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: ec2_import_image
version_added: 7.0.0
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
    aliases: ["name"]
    required: true
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
    suboptions:
      description:
        description:
          - The description of the disk image.
        type: str
      device_name:
        description:
          - The block device mapping for the disk.
        type: str
      format:
        description:
          - The format of the disk image being imported.
        type: str
        choices: ["OVA", "ova", "VHD", "vhd", "VHDX", "vhdx", "VMDK", "vmdk", "RAW", "raw"]
      snapshot_id:
        description:
          - The ID of the EBS snapshot to be used for importing the snapshot.
        type: str
      url:
        description:
          - The URL to the Amazon S3-based disk image being imported.
            The URL can either be a https URL (https://..) or an Amazon S3 URL (s3://..).
        type: str
      user_bucket:
          description:
          - The S3 bucket for the disk image.
          type: dict
          suboptions:
            s3_bucket:
              description:
                - The name of the Amazon S3 bucket where the disk image is located.
              type: str
            s3_key:
              description:
                - The file name of the disk image.
              type: str
  encrypted:
    description:
      - Specifies whether the destination AMI of the imported image should be encrypted.
      - The default KMS key for EBS is used unless you specify a non-default KMS key using I(kms_key_id).
    type: bool
  hypervisor:
    description:
      - The target hypervisor platform.
    type: str
    choices: ["xen"]
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
    suboptions:
      license_configuration_arn:
        description:
          - The ARN of a license configuration.
        type: str
  boot_mode:
    description:
      - The boot mode of the virtual machine.
    type: str
    choices: ["legacy-bios", "uefi"]
  cancel_reason:
    description:
      - The reason for canceling the task.
    type: str
  usage_operation:
    description:
      - The usage operation value.
    type: str
  tags:
    description:
      - The tags to apply to the import image task during creation.
    type: dict
    aliases: ["resource_tags"]
author:
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Import image
  amazon.aws.ec2_import_image:
    state: present
    task_name: "clone-vm-import-image"
    disk_containers:
      - format: raw
        user_bucket:
          s3_bucket: "clone-vm-s3-bucket"
          s3_key: "clone-vm-s3-bucket/ubuntu-vm-clone.raw"

- name: Cancel an import image task
  amazon.aws.ec2_import_image:
    state: absent
    task_name: "clone-vm-import-image"
"""

RETURN = r"""
import_image:
  description: A dict containing information about an EC2 import task.
  returned: always
  type: complex
  contains:
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
      contains:
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
      type: bool
    hypervisor:
      description:
        - The target hypervisor platform.
      type: str
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
    role_name:
      description:
        - The name of the role to use when not using the default role, 'vmimport'.
      type: str
    tags:
      description:
        - The tags to apply to the import image task during creation.
      type: dict
"""

import copy

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import helper_describe_import_image_tasks
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def ensure_ec2_import_image_result(import_image_info):
    result = {"import_image": {}}
    if import_image_info:
        image = copy.deepcopy(import_image_info[0])
        image["Tags"] = boto3_tag_list_to_ansible_dict(image["Tags"])
        result["import_image"] = camel_dict_to_snake_dict(image, ignore_list=["Tags"])
    return result


def absent(client, module):
    """
    Cancel an in-process import virtual machine
    """

    filters = {
        "Filters": [
            {"Name": "tag:Name", "Values": [module.params["task_name"]]},
            {"Name": "task-state", "Values": ["active"]},
        ]
    }

    params = {}

    if module.params.get("cancel_reason"):
        params["CancelReason"] = module.params["cancel_reason"]

    import_image_info = helper_describe_import_image_tasks(client, module, **filters)

    if import_image_info:
        params["ImportTaskId"] = import_image_info[0]["ImportTaskId"]
        import_image_info[0]["TaskName"] = module.params["task_name"]

        if module.check_mode:
            module.exit_json(changed=True, msg="Would have cancelled the import task if not in check mode")

        try:
            client.cancel_import_task(aws_retry=True, **params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to import the image")
    else:
        module.exit_json(
            changed=False,
            msg="The specified import task does not exist or it cannot be cancelled",
            **{"import_image": {}},
        )

    module.exit_json(changed=True, **ensure_ec2_import_image_result(import_image_info))


def present(client, module):
    params = {}
    tags = module.params.get("tags") or {}
    tags.update({"Name": module.params["task_name"]})

    if module.params.get("architecture"):
        params["Architecture"] = module.params["architecture"]
    if module.params.get("client_data"):
        params["ClientData"] = snake_dict_to_camel_dict(module.params["client_data"], capitalize_first=True)
    if module.params.get("description"):
        params["Description"] = module.params["description"]
    if module.params.get("disk_containers"):
        params["DiskContainers"] = snake_dict_to_camel_dict(module.params["disk_containers"], capitalize_first=True)
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
        params["LicenseSpecifications"] = snake_dict_to_camel_dict(
            module.params["license_specifications"], capitalize_first=True
        )
    if module.params.get("usage_operation"):
        params["UsageOperation"] = module.params["usage_operation"]
    if module.params.get("boot_mode"):
        params["BootMode"] = module.params.get("boot_mode")
    params["TagSpecifications"] = boto3_tag_specifications(tags, ["import-image-task"])

    filters = {
        "Filters": [
            {"Name": "tag:Name", "Values": [module.params["task_name"]]},
            {"Name": "task-state", "Values": ["completed", "active", "deleting"]},
        ]
    }
    import_image_info = helper_describe_import_image_tasks(client, module, **filters)

    if import_image_info:
        import_image_info[0]["TaskName"] = module.params["task_name"]
        module.exit_json(
            changed=False,
            msg="An import task with the specified name already exists",
            **ensure_ec2_import_image_result(import_image_info),
        )
    else:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have created the import task if not in check mode")

        params = scrub_none_parameters(params)

        try:
            client.import_image(aws_retry=True, **params)
            import_image_info = helper_describe_import_image_tasks(client, module, **filters)
            import_image_info[0]["TaskName"] = module.params["task_name"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to import the image")

    module.exit_json(changed=True, **ensure_ec2_import_image_result(import_image_info))


def main():
    argument_spec = dict(
        architecture=dict(type="str", choices=["i386", "x86_64"]),
        client_data=dict(
            type="dict",
            options=dict(
                comment=dict(type="str"),
                upload_end=dict(type="str"),
                upload_size=dict(type="float"),
                upload_start=dict(type="str"),
            ),
        ),
        description=dict(type="str"),
        license_specifications=dict(
            type="list",
            elements="dict",
            options=dict(
                license_configuration_arn=dict(type="str"),
            ),
        ),
        encrypted=dict(type="bool"),
        state=dict(default="present", choices=["present", "absent"]),
        hypervisor=dict(type="str", choices=["xen"]),
        kms_key_id=dict(type="str"),
        license_type=dict(type="str", no_log=False),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        platform=dict(type="str", choices=["Windows", "Linux"]),
        role_name=dict(type="str"),
        disk_containers=dict(
            type="list",
            elements="dict",
            options=dict(
                description=dict(type="str"),
                device_name=dict(type="str"),
                format=dict(
                    type="str", choices=["OVA", "ova", "VHD", "vhd", "VHDX", "vhdx", "VMDK", "vmdk", "RAW", "raw"]
                ),
                snapshot_id=dict(type="str"),
                url=dict(type="str"),
                user_bucket=dict(
                    type="dict",
                    options=dict(
                        s3_bucket=dict(type="str"),
                        s3_key=dict(type="str", no_log=True),
                    ),
                ),
            ),
        ),
        usage_operation=dict(type="str"),
        boot_mode=dict(type="str", choices=["legacy-bios", "uefi"]),
        cancel_reason=dict(type="str"),
        task_name=dict(type="str", aliases=["name"], required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params.get("state")

    try:
        client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    if state == "present":
        present(client, module)
    else:
        absent(client, module)


if __name__ == "__main__":
    main()

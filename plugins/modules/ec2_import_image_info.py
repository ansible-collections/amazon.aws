#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_import_image_info
version_added: 7.0.0
short_description: Gather information about import virtual machine tasks
description:
  - Displays details about an import virtual machine tasks that are already created.
author:
  - Alina Buzachis (@alinabuzachis)
options:
  import_task_ids:
    description: The IDs of the import image tasks.
    type: list
    elements: str
    aliases: ["ids"]
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImportImageTasks.html) for possible filters.
    type: list
    elements: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Check status of import image
  amazon.aws.ec2_import_image_info:
    filters:
      - Name: "tag:Name"
        Values: ["clone-vm-import-image"]
      - Name: "task-state"
        Values: ["completed", "active"]
"""

RETURN = r"""
import_image:
  description: A list of EC2 import tasks.
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

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import helper_describe_import_image_tasks
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def ensure_ec2_import_image_result(import_image_info):
    result = {"import_image": []}
    if import_image_info:
        for image in import_image_info:
            image = copy.deepcopy(import_image_info[0])
            image["Tags"] = boto3_tag_list_to_ansible_dict(image["Tags"])
            result["import_image"].append(camel_dict_to_snake_dict(image, ignore_list=["Tags"]))
    return result


def main():
    argument_spec = dict(
        import_task_ids=dict(type="list", elements="str", aliases=["ids"]),
        filters=dict(type="list", elements="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())
    params = {}

    if module.params.get("filters"):
        params["Filters"] = module.params["filters"]
    if module.params.get("import_task_ids"):
        params["ImportTaskIds"] = module.params["import_task_ids"]

    import_image_info = helper_describe_import_image_tasks(client, module, **params)

    module.exit_json(**ensure_ec2_import_image_result(import_image_info))


if __name__ == "__main__":
    main()

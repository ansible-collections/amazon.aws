#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_ami_info
version_added: 1.0.0
short_description: Gather information about EC2 AMIs
description:
  - Gather information about EC2 AMIs.
author:
  - Prasad Katti (@prasadkatti)
options:
  image_ids:
    description: One or more image IDs.
    aliases: [image_id]
    type: list
    elements: str
    default: []
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImages.html) for possible filters.
      - Filter names and values are case sensitive.
    type: dict
    default: {}
  owners:
    description:
      - Filter the images by the owner. Valid options are an AWS account ID, self,
        or an AWS owner alias ( amazon | aws-marketplace | microsoft ).
    aliases: [owner]
    type: list
    elements: str
    default: []
  executable_users:
    description:
      - Filter images by users with explicit launch permissions. Valid options are an AWS account ID, self, or all (public AMIs).
    aliases: [executable_user]
    type: list
    elements: str
    default: []
  describe_image_attributes:
    description:
      - Describe attributes (like launchPermission) of the images found.
    default: false
    type: bool

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: gather information about an AMI using ami-id
  amazon.aws.ec2_ami_info:
    image_ids: ami-5b488823

- name: gather information about all AMIs with tag key Name and value webapp
  amazon.aws.ec2_ami_info:
    filters:
      "tag:Name": webapp

- name: gather information about an AMI with 'AMI Name' equal to foobar
  amazon.aws.ec2_ami_info:
    filters:
      name: foobar

- name: gather information about Ubuntu 17.04 AMIs published by Canonical (099720109477)
  amazon.aws.ec2_ami_info:
    owners: 099720109477
    filters:
      name: "ubuntu/images/ubuntu-zesty-17.04-*"
"""

RETURN = r"""
images:
  description: A list of images.
  returned: always
  type: list
  elements: dict
  contains:
    architecture:
      description: The architecture of the image.
      returned: always
      type: str
      sample: x86_64
    block_device_mappings:
      description: Any block device mapping entries.
      returned: always
      type: list
      elements: dict
      contains:
        device_name:
          description: The device name exposed to the instance.
          returned: always
          type: str
          sample: /dev/sda1
        ebs:
          description: EBS volumes
          returned: always
          type: complex
    creation_date:
      description: The date and time the image was created.
      returned: always
      type: str
      sample: '2017-10-16T19:22:13.000Z'
    description:
      description: The description of the AMI.
      type: str
      sample: ''
    ena_support:
      description: Whether enhanced networking with ENA is enabled.
      returned: always
      type: bool
      sample: true
    hypervisor:
      description: The hypervisor type of the image.
      returned: always
      type: str
      sample: xen
    image_id:
      description: The ID of the AMI.
      returned: always
      type: str
      sample: ami-5b466623
    image_location:
      description: The location of the AMI.
      returned: always
      type: str
      sample: 123456789012/Webapp
    image_type:
      description: The type of image.
      returned: always
      type: str
      sample: machine
    launch_permissions:
      description: A List of AWS accounts may launch the AMI.
      returned: When image is owned by calling account and O(describe_image_attributes=true).
      type: list
      elements: dict
      contains:
        group:
            description: A value of 'all' means the AMI is public.
            type: str
        user_id:
            description: An AWS account ID with permissions to launch the AMI.
            type: str
      sample: [{"group": "all"}, {"user_id": "123456789012"}]
    name:
      description: The name of the AMI that was provided during image creation.
      returned: always
      type: str
      sample: Webapp
    owner_id:
      description: The AWS account ID of the image owner.
      returned: always
      type: str
      sample: '123456789012'
    platform_details:
      description: Platform of image.
      returned: always
      type: str
      sample: "Windows"
    public:
      description: Whether the image has public launch permissions.
      returned: always
      type: bool
      sample: true
    root_device_name:
      description: The device name of the root device.
      returned: always
      type: str
      sample: /dev/sda1
    root_device_type:
      description: The type of root device used by the AMI.
      returned: always
      type: str
      sample: ebs
    sriov_net_support:
      description: Whether enhanced networking is enabled.
      type: str
      sample: simple
    state:
      description: The current state of the AMI.
      returned: always
      type: str
      sample: available
    tags:
      description: Any tags assigned to the image.
      returned: always
      type: dict
    usage_operation:
      description: The operation of the Amazon EC2 instance and the billing code that is associated with the AMI.
      returned: always
      type: str
      sample: "RunInstances"
    virtualization_type:
      description: The type of virtualization of the AMI.
      returned: always
      type: str
      sample: hvm
"""

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_image_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_images
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import is_ansible_aws_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


class AmiInfoFailure(Exception):
    def __init__(self, original_e, user_message):
        self.original_e = original_e
        self.user_message = user_message
        super().__init__(self)


def build_request_args(executable_users, filters, image_ids, owners):
    request_args = {
        "ExecutableUsers": [str(user) for user in executable_users],
        "ImageIds": [str(image_id) for image_id in image_ids],
    }

    # describe_images is *very* slow if you pass the `Owners`
    # param (unless it's self), for some reason.
    # Converting the owners to filters and removing from the
    # owners param greatly speeds things up.
    # Implementation based on aioue's suggestion in #24886
    for owner in owners:
        if owner.isdigit():
            if "owner-id" not in filters:
                filters["owner-id"] = list()
            filters["owner-id"].append(owner)
        elif owner == "self":
            # self not a valid owner-alias filter (https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImages.html)
            request_args["Owners"] = [str(owner)]
        else:
            if "owner-alias" not in filters:
                filters["owner-alias"] = list()
            filters["owner-alias"].append(owner)

    request_args["Filters"] = ansible_dict_to_boto3_filter_list(filters)

    request_args = {k: v for k, v in request_args.items() if v}

    return request_args


def get_images(ec2_client, request_args):
    try:
        images = describe_images(ec2_client, **request_args)
    except AnsibleEC2Error as e:
        raise AmiInfoFailure(e, "error describing images")
    return images


def list_ec2_images(ec2_client, module, request_args):
    images = get_images(ec2_client, request_args)
    images = [camel_dict_to_snake_dict(image) for image in images]

    for image in images:
        try:
            image["tags"] = boto3_tag_list_to_ansible_dict(image.get("tags", []))
            if module.params.get("describe_image_attributes"):
                launch_permissions = describe_image_attribute(
                    ec2_client, attribute="launchPermission", image_id=image["image_id"]
                ).get("LaunchPermissions", [])
                image["launch_permissions"] = [camel_dict_to_snake_dict(perm) for perm in launch_permissions]
        except is_ansible_aws_error_code("AuthFailure"):
            # describing launch permissions of images owned by others is not permitted, but shouldn't cause failures
            pass
        except AnsibleAWSError as e:  # pylint: disable=duplicate-except
            raise AmiInfoFailure(e, "Failed to describe AMI")

    images.sort(key=lambda e: e.get("creation_date", ""))  # it may be possible that creation_date does not always exist

    return images


def main():
    argument_spec = dict(
        describe_image_attributes=dict(default=False, type="bool"),
        executable_users=dict(default=[], type="list", elements="str", aliases=["executable_user"]),
        filters=dict(default={}, type="dict"),
        image_ids=dict(default=[], type="list", elements="str", aliases=["image_id"]),
        owners=dict(default=[], type="list", elements="str", aliases=["owner"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    ec2_client = module.client("ec2")

    request_args = build_request_args(
        executable_users=module.params["executable_users"],
        filters=module.params["filters"],
        image_ids=module.params["image_ids"],
        owners=module.params["owners"],
    )

    images = list_ec2_images(ec2_client, module, request_args)

    module.exit_json(images=images)


if __name__ == "__main__":
    main()

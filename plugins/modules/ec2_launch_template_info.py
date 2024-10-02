#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_launch_template_info
version_added: 9.0.0
short_description: Gather information about launch templates and versions
description:
  - Gather information about launch templates.
author:
  - Aubin Bikouo (@abikouo)
options:
  launch_template_ids:
    description: The IDs of the launch templates.
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeLaunchTemplates.html) for possible filters.
      - Filter names and values are case sensitive.
    type: dict
    default: {}

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about a launch template
  amazon.aws.ec2_launch_template_info:
    launch_template_ids:
      - 'lt-01238c059e3466abc'

- name: Gather information launch template using name
  amazon.aws.ec2_launch_template_info:
    filters:
      launch-template-name: my-test-launch-template
"""

RETURN = r"""
launch_templates:
  description: A list of launch templates.
  returned: always
  type: list
  elements: dict
  contains:
    launch_template_id:
      description: The ID of the launch template.
      type: str
      returned: always
    launch_template_name:
      description: The name of the launch template.
      type: str
      returned: always
    create_time:
      description: The time launch template was created.
      type: str
      returned: always
    created_by:
      description: The principal that created the launch template.
      type: str
      returned: always
    default_version_number:
      description: The version number of the default version of the launch template.
      type: int
      returned: always
    latest_version_number:
      description: The version number of the latest version of the launch template.
      type: int
      returned: always
    tags:
      description: A dictionary of tags assigned to image.
      returned: when AMI is created or already exists
      type: dict
      sample: {
          "Env": "devel",
          "Name": "nat-server"
      }
    versions:
      description: All available versions of the launch template.
      type: list
      elements: dict
      returned: always
      contains:
        launch_template_id:
          description: The ID of the launch template.
          type: str
          returned: always
        launch_template_name:
          description: The name of the launch template.
          type: str
          returned: always
        create_time:
          description: The time the version was created.
          type: str
          returned: always
        created_by:
          description: The principal that created the version.
          type: str
          returned: always
        default_version:
          description: Indicates whether the version is the default version.
          type: bool
          returned: always
        version_number:
          description: The version number.
          type: int
          returned: always
        version_description:
          description: The description for the version.
          type: str
          returned: always
        launch_template_data:
          description: Information about the launch template.
          returned: always
          type: dict
          contains:
            kernel_id:
              description:
                - The ID of the kernel.
              returned: if applicable
              type: str
            image_id:
              description: The ID of the AMI or a Systems Manager parameter.
              type: str
              returned: if applicable
            instance_type:
              description: The instance type.
              type: str
              returned: if applicable
            key_name:
              description: The name of the key pair.
              type: str
              returned: if applicable
            monitoring:
              description: The monitoring for the instance.
              type: dict
              returned: if applicable
              contains:
                enabled:
                  description: Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.
                  type: bool
                  returned: always
            placement:
              description: The placement of the instance.
              type: dict
              returned: if applicable
              contains:
                availability_zone:
                  description: The Availability Zone of the instance.
                  type: str
                  returned: if applicable
                affinity:
                  description: The affinity setting for the instance on the Dedicated Host.
                  type: str
                  returned: if applicable
                group_name:
                  description: The name of the placement group for the instance.
                  type: str
                  returned: if applicable
                host_id:
                  description: The ID of the Dedicated Host for the instance.
                  type: str
                  returned: if applicable
                tenancy:
                  description: The tenancy of the instance.
                  type: str
                  returned: if applicable
                host_resource_group_arn:
                  description: The ARN of the host resource group in which to launch the instances.
                  type: str
                  returned: if applicable
                partition_number:
                  description: The number of the partition the instance should launch in.
                  type: int
                  returned: if applicable
                group_id:
                  description: The Group ID of the placement group.
                  type: str
                  returned: if applicable
            ebs_optimized:
              description:
                - Indicates whether the instance is optimized for Amazon EBS I/O.
              type: bool
              returned: always
            iam_instance_profile:
              description:
                - The IAM instance profile.
              type: dict
              returned: if application
              contains:
                arn:
                  description: The Amazon Resource Name (ARN) of the instance profile.
                  type: str
                  returned: always
                name:
                  description: The name of the instance profile.
                  type: str
                  returned: always
            block_device_mappings:
              description: The block device mappings.
              type: list
              elements: dict
              returned: if applicable
              contains:
                device_name:
                  description: The device name.
                  type: str
                  returned: always
                virtual_name:
                  description: The virtual device name.
                  type: str
                  returned: always
                ebs:
                  description: Information about the block device for an EBS volume.
                  type: str
                  returned: if applicable
                  contains:
                    encrypted:
                      description: Indicates whether the EBS volume is encrypted.
                      type: bool
                      returned: always
                    delete_on_termination:
                      description: Indicates whether the EBS volume is deleted on instance termination.
                      type: bool
                      returned: always
                    iops:
                      description: The number of I/O operations per second (IOPS) that the volume supports.
                      type: int
                      returned: always
                    kms_key_id:
                      description: The ARN of the Key Management Service (KMS) CMK used for encryption.
                      type: int
                      returned: always
                    snapshot_id:
                      description: The ID of the snapshot.
                      type: str
                      returned: always
                    volume_size:
                      description: The size of the volume, in GiB.
                      type: int
                      returned: always
                    volume_type:
                      description: The volume type.
                      type: str
                      returned: always
                    throughput:
                      description: The throughput that the volume supports, in MiB/s.
                      type: int
                      returned: always
                no_device:
                  description: To omit the device from the block device mapping, specify an empty string.
                  type: str
            network_interfaces:
              description: The network interfaces.
              type: list
              elements: dict
              returned: if applicable
              contains:
                associate_carrier_ip_address:
                  description: Indicates whether to associate a Carrier IP address with eth0 for a new network interface.
                  type: bool
                  returned: always
                associate_public_ip_address:
                  description: Indicates whether to associate a public IPv4 address with eth0 for a new network interface.
                  type: bool
                  returned: always
                delete_on_termination:
                  description: Indicates whether the network interface is deleted when the instance is terminated.
                  type: bool
                  returned: always
                description:
                  description: A description for the network interface.
                  type: str
                  returned: always
                device_index:
                  description: The device index for the network interface attachment.
                  type: int
                  returned: always
                groups:
                  description: The IDs of one or more security groups.
                  type: list
                  elements: str
                  returned: if applicable
                interface_type:
                  description: The type of network interface.
                  type: str
                  returned: always
                ipv6_address_count:
                  description: The number of IPv6 addresses for the network interface.
                  type: int
                  returned: if applicable
                ipv6_addresses:
                  description: The IPv6 addresses for the network interface.
                  returned: if applicable
                  type: list
                  elements: dict
                  contains:
                    ipv6_address:
                      description: The IPv6 address.
                      type: str
                      returned: always
                    is_primary_ipv6:
                      description: Determines if an IPv6 address associated with a network interface is the primary IPv6 address.
                      type: bool
                      returned: always
                network_interface_id:
                  description: The ID of the network interface.
                  type: str
                  returned: always
                private_ip_address:
                  description: The primary private IPv4 address of the network interface.
                  type: str
                  returned: if applicable
                private_ip_addresses:
                  description: A list of private IPv4 addresses.
                  type: list
                  elements: str
                  returned: if applicable
                  contains:
                    primary:
                      description: Indicates whether the private IPv4 address is the primary private IPv4 address.
                      type: bool
                      returned: always
                    private_ip_address:
                      description: The private IPv4 address.
                      type: bool
                      returned: always
                secondary_private_ip_address_count:
                  description: The number of secondary private IPv4 addresses for the network interface.
                  type: int
                  returned: if applicable
                subnet_id:
                  description: The ID of the subnet for the network interface.
                  type: str
                  returned: always
                network_card_index:
                  description: The index of the network card.
                  type: int
                  returned: if applicable
                ipv4_prefixes:
                  description: A list of IPv4 prefixes assigned to the network interface.
                  type: list
                  elements: dict
                  returned: if applicable
                  contains:
                    ipv4_prefix:
                      description: The IPv4 delegated prefixes assigned to the network interface.
                      type: str
                      returned: always
                ipv4_prefix_count:
                  description: The number of IPv4 prefixes that Amazon Web Services automatically assigned to the network interface.
                  type: int
                  returned: if applicable
                ipv6_prefixes:
                  description: A list of IPv6 prefixes assigned to the network interface.
                  type: list
                  elements: dict
                  returned: if applicable
                  contains:
                    ipv6_prefix:
                      description: The IPv6 delegated prefixes assigned to the network interface.
                      type: str
                      returned: always
                ipv6_prefix_count:
                  description: The number of IPv6 prefixes that Amazon Web Services automatically assigned to the network interface.
                  type: int
                  returned: if applicable
                primary_ipv6:
                  description: The primary IPv6 address of the network interface.
                  type: str
                  returned: if applicable
                ena_srd_specification:
                  description: Contains the ENA Express settings for instances launched from your launch template.
                  type: dict
                  returned: if applicable
                  contains:
                    ena_srd_enabled:
                      description: Indicates whether ENA Express is enabled for the network interface.
                      type: bool
                      returned: always
                    ena_srd_udp_specification:
                      description: Configures ENA Express for UDP network traffic.
                      type: dict
                      returned: always
                      contains:
                        ena_srd_udp_enabled:
                          description: Indicates whether UDP traffic to and from the instance uses ENA Express.
                          type: bool
                          returned: always
                connection_tracking_specification:
                  description:
                    - A security group connection tracking specification that enables you to set the timeout
                      for connection tracking on an Elastic network interface.
                  type: dict
                  returned: if applicable
                  contains:
                    tcp_established_timeout:
                      description: Timeout (in seconds) for idle TCP connections in an established state.
                      type: int
                      returned: always
                    udp_timeout:
                      description:
                        - Timeout (in seconds) for idle UDP flows that have seen traffic only in a single direction
                          or a single request-response transaction.
                      type: int
                      returned: always
                    udp_stream_timeout:
                      description:
                        - Timeout (in seconds) for idle UDP flows classified as streams which have seen more
                          than one request-response transaction.
                      type: int
                      returned: always
            ram_disk_id:
              description: The ID of the RAM disk, if applicable.
              type: str
              returned: if applicable
            disable_api_termination:
              description: If set to true, indicates that the instance cannot be terminated using the Amazon EC2 console, command line tool, or API.
              type: bool
              returned: if applicable
            instance_initiated_shutdown_behavior:
              description: Indicates whether an instance stops or terminates when you initiate shutdown from the instance.
              type: str
              returned: if applicable
            user_data:
              description: The user data for the instance.
              type: str
              returned: if applicable
            tag_specifications:
              description: The tags that are applied to the resources that are created during instance launch.
              type: list
              elements: dict
              returned: if applicable
              contains:
                resource_type:
                  description: The type of resource to tag.
                  type: str
                  returned: always
                tags:
                  description: The tags for the resource.
                  type: list
                  elements: dict
                  contains:
                    key:
                      description: The key of the tag.
                      type: str
                      returned: always
                    value:
                      description: The value of the tag.
                      type: str
                      returned: always
            enclave_options:
              description: Indicates whether the instance is enabled for Amazon Web Services Nitro Enclaves.
              type: dict
              returned: if applicable
              contains:
                enabled:
                  description: If this parameter is set to true, the instance is enabled for Amazon Web Services Nitro Enclaves.
                  type: bool
                  returned: always
            metadata_options:
              description: The metadata options for the instance.
              type: dict
              returned: if applicable
              contains:
                state:
                  description: The state of the metadata option changes.
                  type: str
                  returned: if applicable
                http_tokens:
                  description: Indicates whether IMDSv2 is required.
                  type: str
                  returned: if applicable
                http_put_response_hop_limit:
                  description: The desired HTTP PUT response hop limit for instance metadata requests.
                  type: int
                  returned: if applicable
                http_endpoint:
                  description: Enables or disables the HTTP metadata endpoint on your instances.
                  type: str
                  returned: if applicable
                http_protocol_ipv6:
                  description: Enables or disables the IPv6 endpoint for the instance metadata service.
                  type: str
                  returned: if applicable
                instance_metadata_tags:
                  description: Set to enabled to allow access to instance tags from the instance metadata.
                  type: str
                  returned: if applicable
            cpu_options:
              description: The CPU options for the instance.
              type: dict
              returned: if applicable
              contains:
                core_count:
                  description: The number of CPU cores for the instance.
                  type: int
                  returned: if applicable
                threads_per_core:
                  description: The number of threads per CPU core.
                  type: int
                  returned: if applicable
                amd_sev_snp:
                  description: Indicates whether the instance is enabled for AMD SEV-SNP.
                  type: int
                  returned: if applicable
            security_group_ids:
              description: The security group IDs.
              type: list
              elements: str
              returned: if applicable
            security_groups:
              description: The security group names.
              type: list
              elements: str
              returned: if applicable
"""

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_template_versions
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_templates
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def list_launch_templates(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    try:
        # Describe launch templates
        launch_templates = describe_launch_templates(
            client,
            launch_template_ids=module.params.get("launch_template_ids"),
            filters=ansible_dict_to_boto3_filter_list(module.params.get("filters")),
        )

        # Describe launch templates versions
        for template in launch_templates:
            template["Versions"] = describe_launch_template_versions(
                client, LaunchTemplateId=template["LaunchTemplateId"]
            )

        # format output
        launch_templates = [camel_dict_to_snake_dict(t, ignore_list=["Tags"]) for t in launch_templates]
        for t in launch_templates:
            t["tags"] = boto3_tag_list_to_ansible_dict(t.pop("tags", {}))

        return normalize_boto3_result(launch_templates)

    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


def main():
    argument_spec = dict(
        launch_template_ids=dict(type="list", elements="str"),
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    client = module.client("ec2")

    launch_templates = list_launch_templates(client, module)
    module.exit_json(launch_templates=launch_templates)


if __name__ == "__main__":
    main()

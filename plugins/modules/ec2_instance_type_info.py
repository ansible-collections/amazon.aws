#!/usr/bin/python
# -*- coding: utf-8 -*-
# ruff: noqa: E402

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_instance_type_info
version_added: 11.1.0
short_description: Retrieve information about EC2 instance types
description:
  - Retrieves detailed information about EC2 instance types.
  - By default, all instance types for the current region are described.
  - Can filter results using instance type names or filters.
  - Does not implement DryRun feature.
author:
  - "Jonathan Springer (@jonpspri)"
options:
    instance_types:
        description:
          - List of instance types to describe.
          - Must be exact instance type names (e.g., V(t3.micro), V(m5.large)).
          - For wildcard matching, use the O(filters) option with V(instance-type) filter instead.
          - Maximum of 100 instance types.
          - If not provided, all instance types are returned.
        required: false
        type: list
        elements: str
        default: []
    filters:
        description:
          - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
          - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstanceTypes.html)
            for possible filters.
          - Filter names and values are case sensitive.
          - Filter values support wildcards (e.g., V(t3.*) to match all t3 instance types).
        type: dict
        default: {}
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Get information about all instance types
  amazon.aws.ec2_instance_type_info:
  register: all_instance_types

- name: Get information about specific instance types
  ec2_instance_type_info:
    instance_types:
      - t3.micro
      - t3.small
      - t3.medium
  register: t3_types

- name: Get all c5 instance types using wildcard filter
  amazon.aws.ec2_instance_type_info:
    filters:
      instance-type:
        - "c5.*"
  register: c5_types

- name: Filter for current generation instance types with GPU
  amazon.aws.ec2_instance_type_info:
    filters:
      current-generation:
        - "true"
      instance-type:
        - "p3.*"
  register: gpu_types

- name: Filter for bare metal instance types
  amazon.aws.ec2_instance_type_info:
    filters:
      bare-metal:
        - "true"
  register: bare_metal_types

- name: Filter by processor architecture
  amazon.aws.ec2_instance_type_info:
    filters:
      processor-info.supported-architecture:
        - arm64
  register: arm_types

- name: Filter for free tier eligible instances
  amazon.aws.ec2_instance_type_info:
    filters:
      free-tier-eligible:
        - "true"
  register: free_tier_types

- name: Combine multiple filters (m5 family with 4 vCPUs)
  amazon.aws.ec2_instance_type_info:
    filters:
      instance-type:
        - "m5.*"
      vcpu-info.default-vcpus:
        - "4"
  register: m5_4vcpu_types

- name: Filter with multiple values
  amazon.aws.ec2_instance_type_info:
    filters:
      processor-info.supported-architecture:
        - arm64
        - x86_64
  register: multi_arch_types

- name: Combine specific instance types with filters
  amazon.aws.ec2_instance_type_info:
    instance_types:
      - t3.micro
      - t3.small
      - t3.medium
    filters:
      processor-info.supported-architecture:
        - x86_64
  register: filtered_t3_types
"""

RETURN = r"""
instance_types:
    description: List of instance type information objects.
    returned: always
    type: complex
    contains:
        instance_type:
            description: The instance type identifier.
            returned: always
            type: str
            sample: "t3.micro"
        current_generation:
            description: Whether the instance type is current generation.
            returned: always
            type: bool
        free_tier_eligible:
            description: Whether the instance type is eligible for the free tier.
            returned: always
            type: bool
        supported_usage_classes:
            description: Usage classes supported (on-demand, spot, capacity-block).
            returned: always
            type: list
            elements: str
        supported_root_device_types:
            description: Supported root device types (ebs, instance-store).
            returned: always
            type: list
            elements: str
        supported_virtualization_types:
            description: Supported virtualization types (hvm, paravirtual).
            returned: always
            type: list
            elements: str
        bare_metal:
            description: Whether this is a bare metal instance type.
            returned: always
            type: bool
        hypervisor:
            description: The hypervisor type (nitro, xen).
            returned: when available
            type: str
        processor_info:
            description: Processor information.
            returned: always
            type: dict
            contains:
                supported_architectures:
                    description: Supported CPU architectures.
                    type: list
                    elements: str
                sustained_clock_speed_in_ghz:
                    description: Sustained clock speed in GHz.
                    type: float
        v_cpu_info:
            description: vCPU information.
            returned: always
            type: dict
            contains:
                default_v_cpus:
                    description: Default number of vCPUs.
                    type: int
                default_cores:
                    description: Default number of cores.
                    type: int
                default_threads_per_core:
                    description: Default threads per core.
                    type: int
                valid_cores:
                    description: List of valid core counts.
                    type: list
                    elements: int
                valid_threads_per_core:
                    description: List of valid thread per core counts.
                    type: list
                    elements: int
        memory_info:
            description: Memory information.
            returned: always
            type: dict
            contains:
                size_in_mi_b:
                    description: Memory size in MiB.
                    type: int
        instance_storage_supported:
            description: Whether instance storage is supported.
            returned: always
            type: bool
        instance_storage_info:
            description: Instance storage information.
            returned: when instance_storage_supported is true
            type: dict
            contains:
                total_size_in_g_b:
                    description: Total instance storage size in GB.
                    type: int
                disks:
                    description: List of instance storage disks.
                    type: list
                    elements: dict
                nvme_support:
                    description: NVMe support status.
                    type: str
                encryption_support:
                    description: Encryption support status.
                    type: str
        ebs_info:
            description: EBS information.
            returned: always
            type: dict
            contains:
                ebs_optimized_support:
                    description: EBS optimized support status.
                    type: str
                encryption_support:
                    description: EBS encryption support status.
                    type: str
                ebs_optimized_info:
                    description: EBS optimized performance info.
                    type: dict
                nvme_support:
                    description: NVMe support status.
                    type: str
        network_info:
            description: Network information.
            returned: always
            type: dict
            contains:
                network_performance:
                    description: Network performance description.
                    type: str
                maximum_network_interfaces:
                    description: Maximum number of network interfaces.
                    type: int
                maximum_network_cards:
                    description: Maximum number of network cards.
                    type: int
                ipv4_addresses_per_interface:
                    description: Maximum IPv4 addresses per interface.
                    type: int
                ipv6_addresses_per_interface:
                    description: Maximum IPv6 addresses per interface.
                    type: int
                ipv6_supported:
                    description: Whether IPv6 is supported.
                    type: bool
                ena_support:
                    description: ENA support status.
                    type: str
                efa_supported:
                    description: Whether EFA is supported.
                    type: bool
                encryption_in_transit_supported:
                    description: Whether encryption in transit is supported.
                    type: bool
        gpu_info:
            description: GPU information.
            returned: when GPU is available
            type: dict
            contains:
                gpus:
                    description: List of GPU devices.
                    type: list
                    elements: dict
                total_gpu_memory_in_mi_b:
                    description: Total GPU memory in MiB.
                    type: int
        fpga_info:
            description: FPGA information.
            returned: when FPGA is available
            type: dict
        inference_accelerator_info:
            description: Inference accelerator information.
            returned: when inference accelerators are available
            type: dict
        placement_group_info:
            description: Placement group information.
            returned: always
            type: dict
            contains:
                supported_strategies:
                    description: Supported placement strategies.
                    type: list
                    elements: str
        hibernation_supported:
            description: Whether hibernation is supported.
            returned: always
            type: bool
        burstable_performance_supported:
            description: Whether burstable performance is supported.
            returned: always
            type: bool
        dedicated_hosts_supported:
            description: Whether dedicated hosts are supported.
            returned: always
            type: bool
        auto_recovery_supported:
            description: Whether auto recovery is supported.
            returned: always
            type: bool
        supported_boot_modes:
            description: Supported boot modes (legacy-bios, uefi).
            returned: always
            type: list
            elements: str
        nitro_enclaves_support:
            description: Nitro Enclaves support status.
            returned: when available
            type: str
        nitro_tpm_support:
            description: NitroTPM support status.
            returned: when available
            type: str
        nitro_tpm_info:
            description: NitroTPM information.
            returned: when NitroTPM is supported
            type: dict
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list

class EC2InstanceTypesManager:
    """Handles EC2 instance types information retrieval"""

    def __init__(self, module):
        self.module = module
        self.ec2 = module.client("ec2")

    def describe_instance_types(self, instance_types=None, filters=None):
        """Describe EC2 instance types with optional filtering.

        Args:
            instance_types: Optional list of instance type names
            filters: Optional list of boto3 filters

        Returns:
            List of instance type info dictionaries
        """
        params = {}

        if instance_types:
            params["InstanceTypes"] = instance_types

        if filters:
            params["Filters"] = filters

        try:
            paginator = self.ec2.get_paginator("describe_instance_types")
            return paginator.paginate(**params).build_full_result()["InstanceTypes"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Failed to describe instance types")


def main():
    argument_spec = dict(
        instance_types=dict(required=False, type="list", elements="str", default=[]),
        filters=dict(required=False, type="dict", default={}),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    instance_types = module.params["instance_types"]
    filters_dict = module.params["filters"]

    # Convert filters to boto3 format
    filters = ansible_dict_to_boto3_filter_list(filters_dict)

    manager = EC2InstanceTypesManager(module)

    # Get instance type information
    raw_results = manager.describe_instance_types(
        instance_types=instance_types if instance_types else None,
        filters=filters,
    )

    # Convert keys to snake_case for Ansible convention
    instance_type_list = [camel_dict_to_snake_dict(item) for item in raw_results]

    module.exit_json(
        changed=False,
        instance_types=instance_type_list,
    )


if __name__ == "__main__":
    main()

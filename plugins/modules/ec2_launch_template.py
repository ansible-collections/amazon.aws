#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_launch_template
version_added: 1.0.0
version_added_collection: community.aws
short_description: Manage EC2 launch templates
description:
- Create, modify, and delete EC2 Launch Templates, which can be used to
  create individual instances or with Autoscaling Groups.
- The M(amazon.aws.ec2_instance) and M(community.aws.autoscaling_group) modules can, instead of specifying all
  parameters on those tasks, be passed a Launch Template which contains
  settings like instance size, disk type, subnet, and more.
author:
- Ryan Scott Brown (@ryansb)
options:
  template_id:
    description:
    - The ID for the launch template, can be used for all cases except creating a new Launch Template.
    - At least one of O(template_id) and O(template_name) must be specified.
    aliases: [id]
    type: str
  template_name:
    description:
    - The template name. This must be unique in the region-account combination you are using.
    - If no launch template exists with the specified name, a new launch template is created.
    - If a launch template with the specified name already exists and the configuration has not changed,
      nothing happens.
    - If a launch template with the specified name already exists and the configuration has changed,
      a new version of the launch template is created.
    - At least one of O(template_id) and O(template_name) must be specified.
    aliases: [name]
    type: str
  default_version:
    description:
    - Which version should be the default when users spin up new instances based on this template? By default, the latest version will be made the default.
    type: str
    default: latest
  version_description:
    version_added: 5.5.0
    description:
    - The description of a launch template version.
    default: ""
    type: str
  versions_to_delete:
    description:
    - The version numbers of a launch template versions to delete.
    - Use O(default_version) to specify a new default version when deleting the current default version.
    - By default, the latest version will be made the default.
    - Ignored when O(state=present).
    type: list
    elements: int
    version_added: 9.0.0
  state:
    description:
    - Whether the launch template should exist or not.
    - Deleting specific versions of a launch template is not supported at this time.
    choices: [present, absent]
    default: present
    type: str
  block_device_mappings:
    description:
    - The block device mapping. Supplying both a snapshot ID and an encryption
      value as arguments for block-device mapping results in an error. This is
      because only blank volumes can be encrypted on start, and these are not
      created from a snapshot. If a snapshot is the basis for the volume, it
      contains data by definition and its encryption status cannot be changed
      using this action.
    type: list
    elements: dict
    suboptions:
      device_name:
        description: The device name (for example, V(/dev/sdh) or V(xvdh)).
        type: str
      no_device:
        description: Suppresses the specified device included in the block device mapping of the AMI.
        type: str
      virtual_name:
        description: >
          The virtual device name (ephemeralN). Instance store volumes are
          numbered starting from 0. An instance type with 2 available instance
          store volumes can specify mappings for ephemeral0 and ephemeral1. The
          number of available instance store volumes depends on the instance
          type. After you connect to the instance, you must mount the volume.
        type: str
      ebs:
        description: Parameters used to automatically set up EBS volumes when the instance is launched.
        type: dict
        suboptions:
          delete_on_termination:
            description: Indicates whether the EBS volume is deleted on instance termination.
            type: bool
          encrypted:
            description: >
              Indicates whether the EBS volume is encrypted. Encrypted volumes
              can only be attached to instances that support Amazon EBS
              encryption. If you are creating a volume from a snapshot, you
              can't specify an encryption value.
            type: bool
          iops:
            description:
            - The number of I/O operations per second (IOPS) that the volume
              supports. For io1, this represents the number of IOPS that are
              provisioned for the volume. For gp2, this represents the baseline
              performance of the volume and the rate at which the volume
              accumulates I/O credits for bursting. For more information about
              General Purpose SSD baseline performance, I/O credits, and
              bursting, see Amazon EBS Volume Types in the Amazon Elastic
              Compute Cloud User Guide.
            - >
              Condition: This parameter is required for requests to create io1
              volumes; it is not used in requests to create gp2, st1, sc1, or
              standard volumes.
            type: int
          kms_key_id:
            description: The ARN of the AWS Key Management Service (AWS KMS) CMK used for encryption.
            type: str
          snapshot_id:
            description: The ID of the snapshot to create the volume from.
            type: str
          volume_size:
            description:
            - The size of the volume, in GiB.
            - "Default: If you're creating the volume from a snapshot and don't specify a volume size, the default is the snapshot size."
            type: int
          volume_type:
            description: The volume type
            type: str
          throughput:
            description: >
              The throughput to provision for a gp3 volume, with a maximum of 1,000 MiB/s.
              Valid Range - Minimum value of V(125). Maximum value of V(1000).
            type: int
            version_added: 9.0.0
  cpu_options:
    description:
    - Choose CPU settings for the EC2 instances that will be created with this template.
    - For more information, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-optimize-cpu.html)
    type: dict
    suboptions:
      core_count:
        description: The number of CPU cores for the instance.
        type: int
      threads_per_core:
        description: >
          The number of threads per CPU core. To disable Intel Hyper-Threading
          Technology for the instance, specify a value of V(1). Otherwise, specify
          the default value of V(2).
        type: int
  credit_specification:
    description: The credit option for CPU usage of the instance. Valid for T2 or T3 instances only.
    type: dict
    suboptions:
      cpu_credits:
        description:
          - The credit option for CPU usage of a T2 or T3 instance. Valid values are C(standard) and C(unlimited).
        type: str
  disable_api_termination:
    description:
      - This helps protect instances from accidental termination.
      - If set to V(true), you can't terminate the instance using the Amazon EC2 console, CLI, or API.
    type: bool
  ebs_optimized:
    description: >
      Indicates whether the instance is optimized for Amazon EBS I/O. This
      optimization provides dedicated throughput to Amazon EBS and an optimized
      configuration stack to provide optimal Amazon EBS I/O performance. This
      optimization isn't available with all instance types. Additional usage
      charges apply when using an EBS-optimized instance.
    type: bool
  elastic_gpu_specifications:
    type: list
    elements: dict
    description: Settings for Elastic GPU attachments. See U(https://aws.amazon.com/ec2/elastic-gpus/) for details.
    suboptions:
      type:
        description: The type of Elastic GPU to attach
        type: str
  iam_instance_profile:
    description: >
      The name or ARN of an IAM instance profile. Requires permissions to
      describe existing instance roles to confirm ARN is properly formed.
    type: str
  image_id:
    description: >
      The AMI ID to use for new instances launched with this template. This
      value is region-dependent since AMIs are not global resources.
    type: str
  instance_initiated_shutdown_behavior:
    description: >
      Indicates whether an instance stops or terminates when you initiate
      shutdown from the instance using the operating system shutdown command.
    choices: [stop, terminate]
    type: str
  instance_market_options:
    description: Options for alternative instance markets, currently only the spot market is supported.
    type: dict
    suboptions:
      market_type:
        description: The market type. This should always be V(spot).
        type: str
      spot_options:
        description: Spot-market specific settings.
        type: dict
        suboptions:
          block_duration_minutes:
            description:
              - The required duration for the Spot Instances (also known as Spot blocks), in minutes.
              - This value must be a multiple of V(60) (V(60), V(120), V(180), V(240), V(300), or V(360)).
            type: int
          instance_interruption_behavior:
            description: The behavior when a Spot Instance is interrupted. The default is V(terminate).
            choices: [hibernate, stop, terminate]
            type: str
          max_price:
            description: The highest hourly price you're willing to pay for this Spot Instance.
            type: str
          spot_instance_type:
            description: The request type to send.
            choices: [one-time, persistent]
            type: str
  instance_type:
    description:
      - The instance type, such as V(c5.2xlarge). For a full list of instance types, see
        U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html).
    type: str
  kernel_id:
    description:
      - The ID of the kernel.
      - We recommend that you use PV-GRUB instead of kernels and RAM disks. For more information, see
        U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/UserProvidedkernels.html)
    type: str
  key_name:
    description:
    - The name of the key pair. You can create a key pair using M(amazon.aws.ec2_key).
    - If you do not specify a key pair, you can't connect to the instance
      unless you choose an AMI that is configured to allow users another way to log in.
    type: str
  monitoring:
    description: Settings for instance monitoring.
    type: dict
    suboptions:
      enabled:
        type: bool
        description: Whether to turn on detailed monitoring for new instances. This will incur extra charges.
  network_interfaces:
    description: One or more network interfaces.
    type: list
    elements: dict
    suboptions:
      associate_public_ip_address:
        description: Associates a public IPv4 address with eth0 for a new network interface.
        type: bool
      delete_on_termination:
        description: Indicates whether the network interface is deleted when the instance is terminated.
        type: bool
      description:
        description: A description for the network interface.
        type: str
      device_index:
        description: The device index for the network interface attachment.
        type: int
      groups:
        description: List of security group IDs to include on this instance.
        type: list
        elements: str
      ipv6_address_count:
        description:
          - The number of IPv6 addresses to assign to a network interface.
          - Amazon EC2 automatically selects the IPv6 addresses from the subnet range.
          - You can't use this option if specifying the O(network_interfaces.ipv6_addresses) option.
        type: int
      ipv6_addresses:
        description:
          - A list of one or more specific IPv6 addresses from the IPv6 CIDR block range of your subnet.
          - You can't use this option if you're specifying the O(network_interfaces.ipv6_address_count) option.
        type: list
        elements: str
      network_interface_id:
        description: The eni ID of a network interface to attach.
        type: str
      private_ip_address:
        description: The primary private IPv4 address of the network interface.
        type: str
      subnet_id:
        description: The ID of the subnet for the network interface.
        type: str
  placement:
    description: The placement group settings for the instance.
    type: dict
    suboptions:
      affinity:
        description: The affinity setting for an instance on a Dedicated Host.
        type: str
      availability_zone:
        description: The Availability Zone for the instance.
        type: str
      group_name:
        description: The name of the placement group for the instance.
        type: str
      host_id:
        description: The ID of the Dedicated Host for the instance.
        type: str
      tenancy:
        description: >
          The tenancy of the instance (if the instance is running in a VPC). An
          instance with a tenancy of dedicated runs on single-tenant hardware.
        type: str
  ram_disk_id:
    description: >
      The ID of the RAM disk to launch the instance with. We recommend that you
      use PV-GRUB instead of kernels and RAM disks. For more information, see
      U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/UserProvidedkernels.html)
    type: str
  security_group_ids:
    description: A list of security group IDs (VPC or EC2-Classic) that the new instances will be added to.
    type: list
    elements: str
  security_groups:
    description: >
      A list of security group names (Default VPC or EC2-Classic) that the new instances will be added to.
      For any VPC other than Default, you must use O(security_group_ids).
    type: list
    elements: str
  source_version:
    description:
      - The version number of the launch template version on which to base the new version.
      - The new version inherits the same launch parameters as the source version, except for parameters that you explicity specify.
      - Snapshots applied to the O(block_device_mappings) are ignored when creating a new version unless they are explicitly included.
    type: str
    default: latest
    version_added: 4.1.0
  tag_specifications:
    description:
    - The tags to apply to the resources when this Launch template is used.
    type: list
    elements: dict
    version_added: 9.0.0
    suboptions:
      resource_type:
        description:
          - The type of resource to tag.
          - If the instance does not include the resource type that you specify, the instance launch fails.
        type: str
        default: instance
        choices:
          - instance
          - volume
          - network-interface
          - spot-instances-request
      tags:
        description:
        - A set of key-value pairs to be applied to the resource type.
        - "Tag key constraints: Tag keys are case-sensitive and accept a maximum of 127 Unicode characters. May not begin with I(aws:)"
        - "Tag value constraints: Tag values are case-sensitive and accept a maximum of 255 Unicode characters."
        type: dict
  user_data:
    description: >
      The Base64-encoded user data to make available to the instance. For more information, see the Linux
      U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) and Windows
      U(http://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-instance-metadata.html#instancedata-add-user-data)
      documentation on user-data.
    type: str
  metadata_options:
    description:
    - Configure EC2 Metadata options.
    - For more information see the IMDS documentation
      U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html).
    type: dict
    version_added: 1.5.0
    suboptions:
      http_endpoint:
        type: str
        description: This parameter enables or disables the HTTP metadata endpoint on your instances.
        choices: [enabled, disabled]
        default: 'enabled'
      http_put_response_hop_limit:
        type: int
        description:
          - The desired HTTP PUT response hop limit for instance metadata requests.
          - The larger the number, the further instance metadata requests can travel.
        default: 1
      http_tokens:
        type: str
        description: The state of token usage for your instance metadata requests.
        choices: [optional, required]
        default: 'optional'
      http_protocol_ipv6:
        version_added: 3.1.0
        type: str
        description:
          - Whether the instance metadata endpoint is available via IPv6.
        choices: [enabled, disabled]
        default: 'disabled'
      instance_metadata_tags:
        version_added: 3.1.0
        type: str
        description:
          - Whether the instance tags are availble (V(enabled)) via metadata endpoint or not (V(disabled)).
        choices: [enabled, disabled]
        default: 'disabled'
notes:
  - The O(tags) option used has been in release 9.0.0 to be applied to the launch template resource instead of launch template resource.
  - Use O(tag_specifications) to define tags to be applied to resources when this Launch Template is used.
  - Support for O(purge_tags) was added in release 9.0.0.
extends_documentation_fragment:
- amazon.aws.common.modules
- amazon.aws.region.modules
- amazon.aws.boto3
- amazon.aws.tags
"""

EXAMPLES = r"""
- name: Create an ec2 launch template
  amazon.aws.ec2_launch_template:
    name: "my_template"
    image_id: "ami-04b762b4289fba92b"
    key_name: my_ssh_key
    instance_type: t2.micro
    iam_instance_profile: myTestProfile
    disable_api_termination: true

- name: >
    Create a new version of an existing ec2 launch template with a different instance type,
    while leaving an older version as the default version
  amazon.aws.ec2_launch_template:
    name: "my_template"
    default_version: 1
    instance_type: c5.4xlarge

- name: Delete an ec2 launch template
  amazon.aws.ec2_launch_template:
    name: "my_template"
    state: absent

- name: Delete a specific version of an ec2 launch template
  amazon.aws.ec2_launch_template:
    name: "my_template"
    versions_to_delete:
      - 2
    state: absent

- name: Delete a specific version of an ec2 launch template and change the default version
  amazon.aws.ec2_launch_template:
    name: "my_template"
    versions_to_delete:
      - 1
    default_version: 2
    state: absent

- name: Create an ec2 launch template with specific tags
  amazon.aws.ec2_launch_template:
    name: "my_template"
    image_id: "ami-04b762b4289fba92b"
    instance_type: t2.micro
    disable_api_termination: true
    tags:
      Some: tag
      Another: tag

- name: Create an ec2 launch template with different tag for volume and instance
  amazon.aws.ec2_launch_template:
    name: "my_template"
    image_id: "ami-04b762b4289fba92b"
    instance_type: t2.micro
    block_device_mappings:
      - device_name: /dev/sdb
        ebs:
          volume_size: 20
          delete_on_termination: true
          volume_type: standard
    tag_specifications:
      - resource_type: instance
        tags:
          OsType: Linux
      - resource_type: volume
        tags:
          foo: bar
"""

RETURN = r"""
latest_version:
  description: The latest available version number of the launch template.
  returned: when RV(latest_template) has a version number.
  type: int
default_version:
  description: The version that will be used if only the template name is specified. Often this is the same as the latest version, but not always.
  returned: when RV(default_template) has a version number.
  type: int
template:
  description: Latest available version of the launch template.
  returned: when O(state=present)
  type: complex
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
  returned: when O(state=present)
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
      sample: {
          "block_device_mappings": [
              {
                  "device_name": "/dev/sdb",
                  "ebs": {
                      "delete_on_termination": true,
                      "encrypted": true,
                      "volumeSize": 5
                  }
              }
          ],
          "ebs_optimized": false,
          "image_id": "ami-0231217be14a6f3ba",
          "instance_type": "t2.micro",
          "network_interfaces": [
              {
                  "associate_public_ip_address": false,
                  "device_index": 0,
                  "ipv6_addresses": [
                      {
                          "ipv6_address": "2001:0:130F:0:0:9C0:876A:130B"
                      }
                  ]
              }
          ]
      }
latest_template:
  description: The latest available version of the launch template.
  returned: when O(state=present)
  type: complex
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
default_template:
  description:
    - The launch template version that will be used if only the template name is specified.
    - Often this is the same as the latest version, but not always.
  returned: when O(state=present)
  type: complex
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
deleted_template:
  description: information about a launch template deleted.
  returned: when O(state=absent)
  type: complex
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
deleted_versions:
  description: Information about deleted launch template versions.
  returned: when O(state=absent)
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
    version_number:
      description: The version number of the launch template.
      type: int
      returned: always
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from uuid import uuid4

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_launch_template
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_launch_template_version
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_launch_template
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_launch_template_versions
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_template_versions
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_launch_templates
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import determine_iam_arn_from_name
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_launch_template
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def find_existing(client, module: AnsibleAWSModule) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    launch_template = None
    launch_template_versions = []
    params = {}
    template_id = module.params.get("template_id")
    template_name = module.params.get("template_name")
    if template_id:
        params["launch_template_ids"] = [template_id]
    else:
        params["launch_template_names"] = [template_name]
    launch_templates = describe_launch_templates(client, **params)
    if launch_templates:
        launch_template = launch_templates[0]
        launch_template_versions = describe_launch_template_versions(
            client, LaunchTemplateId=launch_template["LaunchTemplateId"]
        )
    return normalize_boto3_result(launch_template), normalize_boto3_result(launch_template_versions)


def params_to_launch_data(
    template_params: Dict[str, Any], iam_instance_profile_arn: Optional[str] = None
) -> Dict[str, Any]:
    if iam_instance_profile_arn:
        template_params["iam_instance_profile"] = {"arn": iam_instance_profile_arn}
    for interface in template_params.get("network_interfaces") or []:
        if interface.get("ipv6_addresses"):
            interface["ipv6_addresses"] = [{"ipv6_address": x} for x in interface["ipv6_addresses"]]
    params = snake_dict_to_camel_dict(
        dict((k, v) for k, v in template_params.items() if v is not None),
        capitalize_first=True,
    )
    return params


def validate_string_as_int(module: AnsibleAWSModule, version: str, param_name: str) -> int:
    try:
        return int(version)
    except ValueError:
        module.fail_json(msg=f'{param_name} param was not a valid integer, got "{version}"')


def validate_version_deletion(
    module: AnsibleAWSModule, launch_template_id: str, existing_versions: List[Dict[str, Any]]
) -> Tuple[List[str], Optional[int]]:
    versions_to_delete = module.params.get("versions_to_delete")
    launch_template_versions_to_delete = []
    default_version_to_set = None
    if versions_to_delete:
        unique_versions_to_delete = list(set(versions_to_delete))
        launch_template_versions_to_delete = [
            t["VersionNumber"] for t in existing_versions if t["VersionNumber"] in unique_versions_to_delete
        ]
        if len(launch_template_versions_to_delete) != len(unique_versions_to_delete):
            missing = [m for m in unique_versions_to_delete if m not in launch_template_versions_to_delete]
            module.fail_json(
                msg=f"The following versions {missing} do not exist for launch template id '{launch_template_id}'."
            )

        remaining_versions = [
            t["VersionNumber"]
            for t in existing_versions
            if t["VersionNumber"] not in launch_template_versions_to_delete
        ]

        # Find the default version
        default_version = module.params.get("default_version")
        if default_version in (None, ""):
            default_version_int = [t["VersionNumber"] for t in existing_versions if t["DefaultVersion"]][0]
        elif default_version == "latest":
            default_version_int = max(remaining_versions, default=None)
            default_version_to_set = default_version_int
        else:
            default_version_int = validate_string_as_int(module, default_version, "default_version")
            default_version_to_set = default_version_int

        # Ensure we are not deleting the default version
        if default_version_int in launch_template_versions_to_delete or not remaining_versions:
            module.fail_json(msg="Cannot delete the launch template default version.")

        if default_version_to_set and default_version_to_set not in remaining_versions:
            module.fail_json(
                msg=f"Could not set version '{default_version_to_set}' as default, "
                "the launch template version was not found for the specified launch template id '{launch_template_id}'."
            )
    else:
        # By default delete all non default version before the launch template deletion
        launch_template_versions_to_delete = [t["VersionNumber"] for t in existing_versions if not t["DefaultVersion"]]

    return [to_text(v) for v in launch_template_versions_to_delete], default_version_to_set


def ensure_absent(
    client, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]], existing_versions: List[Dict[str, Any]]
) -> None:
    deleted_versions = []
    deleted_template = {}
    changed = False

    if existing:
        launch_template_id = existing["LaunchTemplateId"]
        v_to_delete, v_default = validate_version_deletion(module, launch_template_id, existing_versions)

        # Update default version
        if v_default:
            changed = True
            if not module.check_mode:
                modify_launch_template(
                    client,
                    LaunchTemplateId=launch_template_id,
                    ClientToken=uuid4().hex,
                    DefaultVersion=to_text(v_default),
                )
        # Delete versions
        if v_to_delete:
            changed = True
            if not module.check_mode:
                response = delete_launch_template_versions(
                    client, launch_template_id=launch_template_id, versions=v_to_delete
                )
                if response["UnsuccessfullyDeletedLaunchTemplateVersions"]:
                    module.warn(
                        f"Failed to delete template versions {response['UnsuccessfullyDeletedLaunchTemplateVersions']} on"
                        f" launch template {launch_template_id}"
                    )
                deleted_versions = [
                    camel_dict_to_snake_dict(v) for v in response["SuccessfullyDeletedLaunchTemplateVersions"]
                ]

        # Delete the launch template when a list of versions was not specified
        if not module.params.get("versions_to_delete"):
            changed = True
            if not module.check_mode:
                deleted_template = delete_launch_template(client, launch_template_id=launch_template_id)
                deleted_template = camel_dict_to_snake_dict(deleted_template, ignore_list=["Tags"])
                if "tags" in deleted_template:
                    deleted_template["tags"] = boto3_tag_list_to_ansible_dict(deleted_template.get("tags"))

    module.exit_json(changed=changed, deleted_versions=deleted_versions, deleted_template=deleted_template)


def add_launch_template_version(
    client,
    module: AnsibleAWSModule,
    launch_template_id: str,
    launch_template_data: Dict[str, Any],
    existing_versions: List[Dict[str, Any]],
    most_recent_version_number: str,
) -> int:
    source_version = module.params.get("source_version")
    version_description = module.params.get("version_description")

    params = {
        "LaunchTemplateId": launch_template_id,
        "ClientToken": uuid4().hex,
        "VersionDescription": version_description,
    }

    if source_version == "latest":
        params.update({"SourceVersion": most_recent_version_number})
    elif source_version not in (None, ""):
        # Source version passed as int
        source_version_int = validate_string_as_int(module, source_version, "source_version")
        # get source template version
        next_source_version = next(
            (v for v in existing_versions if v["VersionNumber"] == source_version_int),
            None,
        )
        if next_source_version is None:
            module.fail_json(msg=f'source_version does not exist, got "{source_version}"')
        params.update({"SourceVersion": str(next_source_version["VersionNumber"])})

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have created launch template version if not in check mode.")

    # Create Launch template version
    launch_template_version = create_launch_template_version(
        client, launch_template_data=launch_template_data, **params
    )
    return launch_template_version["VersionNumber"]


def ensure_default_version(
    client,
    module: AnsibleAWSModule,
    launch_template_id: str,
    current_default_version_number: int,
    most_recent_version_number: int,
) -> bool:
    # Modify default version
    default_version = module.params.get("default_version")
    changed = False
    if default_version not in (None, ""):
        if default_version == "latest":
            default_version = to_text(most_recent_version_number)
        else:
            default_version = to_text(validate_string_as_int(module, default_version, "default_version"))
        if to_text(current_default_version_number) != default_version:
            changed = True
            if not module.check_mode:
                modify_launch_template(
                    client,
                    LaunchTemplateId=launch_template_id,
                    ClientToken=uuid4().hex,
                    DefaultVersion=default_version,
                )
    return changed


def format_module_output(client, module: AnsibleAWSModule) -> Dict[str, Any]:
    # Describe launch template
    template, template_versions = find_existing(client, module)
    template = camel_dict_to_snake_dict(template, ignore_list=["Tags"])
    if "tags" in template:
        template["tags"] = boto3_tag_list_to_ansible_dict(template.get("tags"))
    template_versions = [camel_dict_to_snake_dict(v) for v in template_versions]
    result = {
        "template": template,
        "versions": template_versions,
        "default_template": [v for v in template_versions if v.get("default_version")][0],
        "latest_template": [
            v
            for v in template_versions
            if (v.get("version_number") and int(v["version_number"]) == int(template["latest_version_number"]))
        ][0],
    }
    if "version_number" in result["default_template"]:
        result["default_version"] = result["default_template"]["version_number"]
    if "version_number" in result["latest_template"]:
        result["latest_version"] = result["latest_template"]["version_number"]
    return result


def ensure_present(
    client,
    module: AnsibleAWSModule,
    template_options: Dict[str, Any],
    existing: Optional[Dict[str, Any]],
    existing_versions: List[Dict[str, Any]],
) -> None:
    template_name = module.params["template_name"]
    tags = module.params["tags"]
    tag_specifications = module.params.get("tag_specifications")
    version_description = module.params.get("version_description")
    iam_instance_profile = module.params.get("iam_instance_profile")
    # IAM instance profile
    if iam_instance_profile:
        iam_instance_profile = determine_iam_arn_from_name(module.client("iam"), iam_instance_profile)
    # Convert Launch template data
    launch_template_data = params_to_launch_data(
        dict((k, v) for k, v in module.params.items() if k in template_options), iam_instance_profile
    )
    # Tag specifications
    if tag_specifications:
        boto3_tag_specs = []
        for tag_spec in tag_specifications:
            boto3_tag_specs.extend(boto3_tag_specifications(tag_spec["tags"], types=tag_spec["resource_type"]))
        launch_template_data["TagSpecifications"] = boto3_tag_specs
    launch_template_data = scrub_none_parameters(launch_template_data, descend_into_lists=True)
    changed = False

    if not (existing or existing_versions):
        # Create Launch template
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have created launch template if not in check mode.")
        create_launch_template(
            client,
            launch_template_name=template_name,
            launch_template_data=launch_template_data,
            tags=tags,
            ClientToken=uuid4().hex,
            VersionDescription=version_description,
        )
        changed = True
    else:
        launch_template_id = existing["LaunchTemplateId"]
        default_version_number = existing["DefaultVersionNumber"]
        most_recent = sorted(existing_versions, key=lambda x: x["VersionNumber"])[-1]
        most_recent_version_number = most_recent["VersionNumber"]
        if not (
            launch_template_data == most_recent["LaunchTemplateData"]
            and version_description == most_recent.get("VersionDescription", "")
        ):
            changed = True
            most_recent_version_number = add_launch_template_version(
                client,
                module,
                launch_template_id,
                launch_template_data,
                existing_versions,
                str(most_recent["VersionNumber"]),
            )

        # Ensure default version
        changed |= ensure_default_version(
            client, module, launch_template_id, default_version_number, most_recent_version_number
        )
        # Ensure tags
        changed |= ensure_ec2_tags(
            client,
            module,
            launch_template_id,
            resource_type="launch-template",
            tags=tags,
            purge_tags=module.params["purge_tags"],
        )

    module.exit_json(changed=changed, **format_module_output(client, module))


def main():
    template_options = dict(
        block_device_mappings=dict(
            type="list",
            elements="dict",
            options=dict(
                device_name=dict(),
                ebs=dict(
                    type="dict",
                    options=dict(
                        delete_on_termination=dict(type="bool"),
                        encrypted=dict(type="bool"),
                        iops=dict(type="int"),
                        kms_key_id=dict(),
                        snapshot_id=dict(),
                        volume_size=dict(type="int"),
                        volume_type=dict(),
                        throughput=dict(type="int"),
                    ),
                ),
                no_device=dict(),
                virtual_name=dict(),
            ),
        ),
        cpu_options=dict(
            type="dict",
            options=dict(
                core_count=dict(type="int"),
                threads_per_core=dict(type="int"),
            ),
        ),
        credit_specification=dict(
            dict(type="dict"),
            options=dict(
                cpu_credits=dict(),
            ),
        ),
        disable_api_termination=dict(type="bool"),
        ebs_optimized=dict(type="bool"),
        elastic_gpu_specifications=dict(
            options=dict(type=dict()),
            type="list",
            elements="dict",
        ),
        image_id=dict(),
        instance_initiated_shutdown_behavior=dict(choices=["stop", "terminate"]),
        instance_market_options=dict(
            type="dict",
            options=dict(
                market_type=dict(),
                spot_options=dict(
                    type="dict",
                    options=dict(
                        block_duration_minutes=dict(type="int"),
                        instance_interruption_behavior=dict(choices=["hibernate", "stop", "terminate"]),
                        max_price=dict(),
                        spot_instance_type=dict(choices=["one-time", "persistent"]),
                    ),
                ),
            ),
        ),
        instance_type=dict(),
        kernel_id=dict(),
        key_name=dict(),
        monitoring=dict(
            type="dict",
            options=dict(enabled=dict(type="bool")),
        ),
        metadata_options=dict(
            type="dict",
            options=dict(
                http_endpoint=dict(choices=["enabled", "disabled"], default="enabled"),
                http_put_response_hop_limit=dict(type="int", default=1),
                http_tokens=dict(choices=["optional", "required"], default="optional"),
                http_protocol_ipv6=dict(choices=["disabled", "enabled"], default="disabled"),
                instance_metadata_tags=dict(choices=["disabled", "enabled"], default="disabled"),
            ),
        ),
        network_interfaces=dict(
            type="list",
            elements="dict",
            options=dict(
                associate_public_ip_address=dict(type="bool"),
                delete_on_termination=dict(type="bool"),
                description=dict(),
                device_index=dict(type="int"),
                groups=dict(type="list", elements="str"),
                ipv6_address_count=dict(type="int"),
                ipv6_addresses=dict(type="list", elements="str"),
                network_interface_id=dict(),
                private_ip_address=dict(),
                subnet_id=dict(),
            ),
        ),
        placement=dict(
            options=dict(
                affinity=dict(),
                availability_zone=dict(),
                group_name=dict(),
                host_id=dict(),
                tenancy=dict(),
            ),
            type="dict",
        ),
        ram_disk_id=dict(),
        security_group_ids=dict(type="list", elements="str"),
        security_groups=dict(type="list", elements="str"),
        user_data=dict(),
    )

    argument_spec = dict(
        state=dict(choices=["present", "absent"], default="present"),
        template_name=dict(aliases=["name"]),
        template_id=dict(aliases=["id"]),
        default_version=dict(default="latest"),
        source_version=dict(default="latest"),
        version_description=dict(default=""),
        iam_instance_profile=dict(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        versions_to_delete=dict(type="list", elements="int"),
        tag_specifications=dict(
            type="list",
            elements="dict",
            options=dict(
                resource_type=dict(
                    type="str",
                    default="instance",
                    choices=["instance", "volume", "network-interface", "spot-instances-request"],
                ),
                tags=dict(type="dict"),
            ),
        ),
    )

    argument_spec.update(template_options)

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=[
            ("template_name", "template_id"),
        ],
        supports_check_mode=True,
    )

    state = module.params.get("state")
    client = module.client("ec2")
    launch_template, launch_template_versions = find_existing(client, module)

    try:
        if state == "present":
            ensure_present(client, module, template_options, launch_template, launch_template_versions)
        else:
            ensure_absent(client, module, launch_template, launch_template_versions)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

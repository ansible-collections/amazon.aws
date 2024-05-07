#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_instance_info
version_added: 1.0.0
short_description: Gather information about ec2 instances in AWS
description:
    - Gather information about ec2 instances in AWS
author:
  - Michael Schuett (@michaeljs1990)
  - Rob White (@wimnat)
options:
  instance_ids:
    description:
      - If you specify one or more instance IDs, only instances that have the specified IDs are returned.
    required: false
    type: list
    elements: str
    default: []
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    default: {}
    type: dict
  minimum_uptime:
    description:
      - Minimum running uptime in minutes of instances.  For example if I(uptime) is C(60) return all instances that have run more than 60 minutes.
    required: false
    aliases: ['uptime']
    type: int
  include_attributes:
    description:
      - Describes the specified attributes of the returned instances.
    required: false
    type: list
    elements: str
    choices:
    - instanceType
    - kernel
    - ramdisk
    - userData
    - disableApiTermination
    - instanceInitiatedShutdownBehavior
    - rootDeviceName
    - blockDeviceMapping
    - productCodes
    - sourceDestCheck
    - groupSet
    - ebsOptimized
    - sriovNetSupport
    - enclaveOptions
    - disableApiStop
    aliases: ['attributes']
    version_added: 6.3.0

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all instances
  amazon.aws.ec2_instance_info:

- name: Gather information about all instances in AZ ap-southeast-2a
  amazon.aws.ec2_instance_info:
    filters:
      availability-zone: ap-southeast-2a

- name: Gather information about a particular instance using ID
  amazon.aws.ec2_instance_info:
    instance_ids:
      - i-12345678

- name: Gather information about any instance with a tag key Name and value Example
  amazon.aws.ec2_instance_info:
    filters:
      "tag:Name": Example

- name: Gather information about any instance in states "shutting-down", "stopping", "stopped"
  amazon.aws.ec2_instance_info:
    filters:
      instance-state-name: ["shutting-down", "stopping", "stopped"]

- name: Gather information about any instance with Name beginning with RHEL and an uptime of at least 60 minutes
  amazon.aws.ec2_instance_info:
    region: "{{ ec2_region }}"
    uptime: 60
    filters:
      "tag:Name": "RHEL-*"
      instance-state-name: ["running"]
  register: ec2_node_info

- name: Gather information about a particular instance using ID and include kernel attribute
  amazon.aws.ec2_instance_info:
    instance_ids:
      - i-12345678
    include_attributes:
      - kernel
"""

RETURN = r"""
instances:
    description: A list of ec2 instances.
    returned: always
    type: complex
    contains:
        ami_launch_index:
            description: The AMI launch index, which can be used to find this instance in the launch group.
            returned: always
            type: int
            sample: 0
        architecture:
            description: The architecture of the image.
            returned: always
            type: str
            sample: x86_64
        block_device_mappings:
            description: Any block device mapping entries for the instance.
            returned: always
            type: complex
            contains:
                device_name:
                    description: The device name exposed to the instance (for example, /dev/sdh or xvdh).
                    returned: always
                    type: str
                    sample: /dev/sdh
                ebs:
                    description: Parameters used to automatically set up EBS volumes when the instance is launched.
                    returned: always
                    type: complex
                    contains:
                        attach_time:
                            description: The time stamp when the attachment initiated.
                            returned: always
                            type: str
                            sample: "2017-03-23T22:51:24+00:00"
                        delete_on_termination:
                            description: Indicates whether the volume is deleted on instance termination.
                            returned: always
                            type: bool
                            sample: true
                        status:
                            description: The attachment state.
                            returned: always
                            type: str
                            sample: attached
                        volume_id:
                            description: The ID of the EBS volume.
                            returned: always
                            type: str
                            sample: vol-12345678
        capacity_reservation_specification:
            description: Information about the Capacity Reservation targeting option.
            type: complex
            contains:
                capacity_reservation_preference:
                    description: Describes the Capacity Reservation preferences.
                    type: str
                    sample: open
        cpu_options:
            description: The CPU options set for the instance.
            returned: always
            type: complex
            contains:
                core_count:
                     description: The number of CPU cores for the instance.
                     returned: always
                     type: int
                     sample: 1
                threads_per_core:
                     description: The number of threads per CPU core. On supported instance, a value of 1 means Intel Hyper-Threading Technology is disabled.
                     returned: always
                     type: int
                     sample: 1
        client_token:
            description: The idempotency token you provided when you launched the instance, if applicable.
            returned: always
            type: str
            sample: mytoken
        current_instance_boot_mode:
            description: The boot mode that is used to boot the instance at launch or start.
            type: str
            sample: legacy-bios
        ebs_optimized:
            description: Indicates whether the instance is optimized for EBS I/O.
            returned: always
            type: bool
            sample: false
        ena_support:
            description: Specifies whether enhanced networking with ENA is enabled.
            returned: always
            type: bool
            sample: true
        enclave_options:
            description: Indicates whether the instance is enabled for Amazon Web Services Nitro Enclaves.
            type: dict
            contains:
                enabled:
                    description: If this parameter is set to true, the instance is enabled for Amazon Web Services Nitro Enclaves.
                    returned: always
                    type: bool
                    sample: false
        hibernation_options:
            description: Indicates whether the instance is enabled for hibernation.
            type: dict
            contains:
                configured:
                    description: If true, your instance is enabled for hibernation; otherwise, it is not enabled for hibernation.
                    returned: always
                    type: bool
                    sample: false
        hypervisor:
            description: The hypervisor type of the instance.
            returned: always
            type: str
            sample: xen
        iam_instance_profile:
            description: The IAM instance profile associated with the instance, if applicable.
            type: complex
            contains:
                arn:
                    description: The Amazon Resource Name (ARN) of the instance profile.
                    returned: always
                    type: str
                    sample: "arn:aws:iam::123456789012:instance-profile/myprofile"
                id:
                    description: The ID of the instance profile.
                    returned: always
                    type: str
                    sample: JFJ397FDG400FG9FD1N
        image_id:
            description: The ID of the AMI used to launch the instance.
            returned: always
            type: str
            sample: ami-0011223344
        instance_id:
            description: The ID of the instance.
            returned: always
            type: str
            sample: i-012345678
        instance_type:
            description: The instance type size of the running instance.
            returned: always
            type: str
            sample: t2.micro
        key_name:
            description: The name of the key pair, if this instance was launched with an associated key pair.
            returned: always
            type: str
            sample: my-key
        launch_time:
            description: The time the instance was launched.
            returned: always
            type: str
            sample: "2017-03-23T22:51:24+00:00"
        maintenance_options:
            description: Provides information on the recovery and maintenance options of your instance.
            returned: always
            type: dict
            contains:
                auto_recovery:
                    description: Provides information on the current automatic recovery behavior of your instance.
                    type: str
                    sample: default
        metadata_options:
            description: The metadata options for the instance.
            returned: always
            type: complex
            contains:
                http_endpoint:
                    description: Indicates whether the HTTP metadata endpoint on your instances is enabled or disabled.
                    type: str
                    sample: enabled
                http_protocol_ipv6:
                    description: Indicates whether the IPv6 endpoint for the instance metadata service is enabled or disabled.
                    type: str
                    sample: disabled
                http_put_response_hop_limit:
                    description: The maximum number of hops that the metadata token can travel.
                    type: int
                    sample: 1
                http_tokens:
                    description: Indicates whether IMDSv2 is required.
                    type: str
                    sample: optional
                instance_metadata_tags:
                    description: Indicates whether access to instance tags from the instance metadata is enabled or disabled.
                    type: str
                    sample: disabled
                state:
                    description: The state of the metadata option changes.
                    type: str
                    sample: applied
        monitoring:
            description: The monitoring for the instance.
            returned: always
            type: complex
            contains:
                state:
                    description: Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.
                    returned: always
                    type: str
                    sample: disabled
        network_interfaces:
            description: One or more network interfaces for the instance.
            returned: always
            type: complex
            contains:
                association:
                    description: The association information for an Elastic IPv4 associated with the network interface.
                    returned: always
                    type: complex
                    contains:
                        ip_owner_id:
                            description: The ID of the owner of the Elastic IP address.
                            returned: always
                            type: str
                            sample: amazon
                        public_dns_name:
                            description: The public DNS name.
                            returned: always
                            type: str
                            sample: ""
                        public_ip:
                            description: The public IP address or Elastic IP address bound to the network interface.
                            returned: always
                            type: str
                            sample: 1.2.3.4
                attachment:
                    description: The network interface attachment.
                    returned: always
                    type: complex
                    contains:
                        attach_time:
                            description: The time stamp when the attachment initiated.
                            returned: always
                            type: str
                            sample: "2017-03-23T22:51:24+00:00"
                        attachment_id:
                            description: The ID of the network interface attachment.
                            returned: always
                            type: str
                            sample: eni-attach-3aff3f
                        delete_on_termination:
                            description: Indicates whether the network interface is deleted when the instance is terminated.
                            returned: always
                            type: bool
                            sample: true
                        device_index:
                            description: The index of the device on the instance for the network interface attachment.
                            returned: always
                            type: int
                            sample: 0
                        network_card_index:
                            description: The index of the network card.
                            returned: always
                            type: int
                            sample: 0
                        status:
                            description: The attachment state.
                            returned: always
                            type: str
                            sample: attached
                description:
                    description: The description.
                    returned: always
                    type: str
                    sample: My interface
                groups:
                    description: One or more security groups.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        group_id:
                            description: The ID of the security group.
                            returned: always
                            type: str
                            sample: sg-abcdef12
                        group_name:
                            description: The name of the security group.
                            returned: always
                            type: str
                            sample: mygroup
                interface_type:
                    description: The type of network interface.
                    returned: always
                    type: str
                    sample: interface
                ipv6_addresses:
                    description: One or more IPv6 addresses associated with the network interface.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        ipv6_address:
                            description: The IPv6 address.
                            returned: always
                            type: str
                            sample: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
                mac_address:
                    description: The MAC address.
                    returned: always
                    type: str
                    sample: "00:11:22:33:44:55"
                network_interface_id:
                    description: The ID of the network interface.
                    returned: always
                    type: str
                    sample: eni-01234567
                owner_id:
                    description: The AWS account ID of the owner of the network interface.
                    returned: always
                    type: str
                    sample: 01234567890
                private_dns_name:
                    description: The private DNS hostname name assigned to the instance.
                    type: str
                    returned: always
                    sample: ip-10-1-0-156.ec2.internal
                private_ip_address:
                    description: The IPv4 address of the network interface within the subnet.
                    returned: always
                    type: str
                    sample: 10.0.0.1
                private_ip_addresses:
                    description: The private IPv4 addresses associated with the network interface.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        association:
                            description: The association information for an Elastic IP address (IPv4) associated with the network interface.
                            type: complex
                            contains:
                                ip_owner_id:
                                    description: The ID of the owner of the Elastic IP address.
                                    returned: always
                                    type: str
                                    sample: amazon
                                public_dns_name:
                                    description: The public DNS name.
                                    returned: always
                                    type: str
                                    sample: ""
                                public_ip:
                                    description: The public IP address or Elastic IP address bound to the network interface.
                                    returned: always
                                    type: str
                                    sample: 1.2.3.4
                        primary:
                            description: Indicates whether this IPv4 address is the primary private IP address of the network interface.
                            returned: always
                            type: bool
                            sample: true
                        private_dns_name:
                            description: The private DNS hostname name assigned to the instance.
                            type: str
                            returned: always
                            sample: ip-10-1-0-156.ec2.internal
                        private_ip_address:
                            description: The private IPv4 address of the network interface.
                            returned: always
                            type: str
                            sample: 10.0.0.1
                source_dest_check:
                    description: Indicates whether source/destination checking is enabled.
                    returned: always
                    type: bool
                    sample: true
                status:
                    description: The status of the network interface.
                    returned: always
                    type: str
                    sample: in-use
                subnet_id:
                    description: The ID of the subnet for the network interface.
                    returned: always
                    type: str
                    sample: subnet-0123456
                vpc_id:
                    description: The ID of the VPC for the network interface.
                    returned: always
                    type: str
                    sample: vpc-0123456
        placement:
            description: The location where the instance launched, if applicable.
            returned: always
            type: complex
            contains:
                availability_zone:
                    description: The Availability Zone of the instance.
                    returned: always
                    type: str
                    sample: ap-southeast-2a
                group_name:
                    description: The name of the placement group the instance is in (for cluster compute instances).
                    returned: always
                    type: str
                    sample: ""
                tenancy:
                    description: The tenancy of the instance (if the instance is running in a VPC).
                    returned: always
                    type: str
                    sample: default
        platform_details:
            description: The platform details value for the instance.
            returned: always
            type: str
            sample: Linux/UNIX
        private_dns_name:
            description: The private DNS name.
            returned: always
            type: str
            sample: ip-10-0-0-1.ap-southeast-2.compute.internal
        private_dns_name_options:
            description: The options for the instance hostname.
            type: dict
            contains:
                enable_resource_name_dns_a_record:
                    description: Indicates whether to respond to DNS queries for instance hostnames with DNS A records.
                    type: bool
                    sample: false
                enable_resource_name_dns_aaaa_record:
                    description: Indicates whether to respond to DNS queries for instance hostnames with DNS AAAA records.
                    type: bool
                    sample: false
                hostname_type:
                    description: The type of hostname to assign to an instance.
                    type: str
                    sample: ip-name
        private_ip_address:
            description: The IPv4 address of the network interface within the subnet.
            returned: always
            type: str
            sample: 10.0.0.1
        product_codes:
            description: One or more product codes.
            returned: always
            type: list
            elements: dict
            contains:
                product_code_id:
                    description: The product code.
                    returned: always
                    type: str
                    sample: aw0evgkw8ef3n2498gndfgasdfsd5cce
                product_code_type:
                    description: The type of product code.
                    returned: always
                    type: str
                    sample: marketplace
        public_dns_name:
            description: The public DNS name assigned to the instance.
            returned: always
            type: str
            sample:
        public_ip_address:
            description: The public IPv4 address assigned to the instance.
            returned: always
            type: str
            sample: 52.0.0.1
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
        security_groups:
            description: One or more security groups for the instance.
            returned: always
            type: list
            elements: dict
            contains:
                group_id:
                    description: The ID of the security group.
                    returned: always
                    type: str
                    sample: sg-0123456
                group_name:
                    description: The name of the security group.
                    returned: always
                    type: str
                    sample: my-security-group
        source_dest_check:
            description: Indicates whether source/destination checking is enabled.
            returned: always
            type: bool
            sample: true
        state:
            description: The current state of the instance.
            returned: always
            type: complex
            contains:
                code:
                    description: The low byte represents the state.
                    returned: always
                    type: int
                    sample: 16
                name:
                    description: The name of the state.
                    returned: always
                    type: str
                    sample: running
        state_transition_reason:
            description: The reason for the most recent state transition.
            returned: always
            type: str
            sample:
        subnet_id:
            description: The ID of the subnet in which the instance is running.
            returned: always
            type: str
            sample: subnet-00abcdef
        tags:
            description: Any tags assigned to the instance.
            returned: always
            type: dict
            sample:
        virtualization_type:
            description: The type of virtualization of the AMI.
            returned: always
            type: str
            sample: hvm
        vpc_id:
            description: The ID of the VPC the instance is in.
            returned: always
            type: dict
            sample: vpc-0011223344
        attributes:
            description: The details of the instance attribute specified on input.
            returned: when include_attribute is specified
            type: dict
            sample:
                {
                    'disable_api_termination': {
                        'value': True
                    },
                    'ebs_optimized': {
                        'value': True
                    }
                }
            version_added: 6.3.0
"""

import datetime

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


@AWSRetry.jittered_backoff()
def _describe_instances(connection, **params):
    paginator = connection.get_paginator("describe_instances")
    return paginator.paginate(**params).build_full_result()


def list_ec2_instances(connection, module):
    instance_ids = module.params.get("instance_ids")
    uptime = module.params.get("minimum_uptime")
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        reservations = _describe_instances(connection, InstanceIds=instance_ids, Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list ec2 instances")

    instances = []

    if uptime:
        timedelta = int(uptime) if uptime else 0
        oldest_launch_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=timedelta)
        # Get instances from reservations
        for reservation in reservations["Reservations"]:
            instances += [
                instance
                for instance in reservation["Instances"]
                if instance["LaunchTime"].replace(tzinfo=None) < oldest_launch_time
            ]
    else:
        for reservation in reservations["Reservations"]:
            instances = instances + reservation["Instances"]

    # include instances attributes
    attributes = module.params.get("include_attributes")
    if attributes:
        for instance in instances:
            instance["attributes"] = describe_instance_attributes(connection, instance["InstanceId"], attributes)

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_instances = [camel_dict_to_snake_dict(instance) for instance in instances]

    # Turn the boto3 result in to ansible friendly tag dictionary
    for instance in snaked_instances:
        instance["tags"] = boto3_tag_list_to_ansible_dict(instance.get("tags", []), "key", "value")

    module.exit_json(instances=snaked_instances)


def describe_instance_attributes(connection, instance_id, attributes):
    result = {}
    for attr in attributes:
        response = connection.describe_instance_attribute(Attribute=attr, InstanceId=instance_id)
        for key in response:
            if key not in ("InstanceId", "ResponseMetadata"):
                result[key] = response[key]
    return result


def main():
    instance_attributes = [
        "instanceType",
        "kernel",
        "ramdisk",
        "userData",
        "disableApiTermination",
        "instanceInitiatedShutdownBehavior",
        "rootDeviceName",
        "blockDeviceMapping",
        "productCodes",
        "sourceDestCheck",
        "groupSet",
        "ebsOptimized",
        "sriovNetSupport",
        "enclaveOptions",
        "disableApiStop",
    ]
    argument_spec = dict(
        minimum_uptime=dict(required=False, type="int", default=None, aliases=["uptime"]),
        instance_ids=dict(default=[], type="list", elements="str"),
        filters=dict(default={}, type="dict"),
        include_attributes=dict(type="list", elements="str", aliases=["attributes"], choices=instance_attributes),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["instance_ids", "filters"]],
        supports_check_mode=True,
    )

    try:
        connection = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    list_ec2_instances(connection, module)


if __name__ == "__main__":
    main()

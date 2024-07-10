#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_eni
version_added: 1.0.0
short_description: Create and optionally attach an Elastic Network Interface (ENI) to an instance
description:
  - Create and optionally attach an Elastic Network Interface (ENI) to an instance.
  - If O(eni_id) or O(private_ip_address) is provided, the existing ENI (if any) will be modified.
  - The O(attached) parameter controls the attachment status of the network interface.
author:
  - "Rob White (@wimnat)"
  - "Mike Healey (@healem)"
options:
  eni_id:
    description:
      - The ID of the ENI (to modify).
      - If O(eni_id=None) and O(state=present), a new ENI will be created.
    type: str
  instance_id:
    description:
      - Instance ID that you wish to attach ENI to.
    type: str
  private_ip_address:
    description:
      - Private IP address.
    type: str
  subnet_id:
    description:
      - ID of subnet in which to create the ENI.
    type: str
  description:
    description:
      - Optional description of the ENI.
    type: str
  security_groups:
    description:
      - List of security groups associated with the interface.
      - Ignored when O(state=absent).
    type: list
    elements: str
    default: []
  state:
    description:
      - Create or delete ENI.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  device_index:
    description:
      - The index of the device for the network interface attachment on the instance.
    default: 0
    type: int
  attached:
    description:
      - Specifies if network interface should be attached or detached from instance. If omitted, attachment status
        won't change
    type: bool
  force_detach:
    description:
      - Force detachment of the interface. This applies either when explicitly detaching the interface by setting O(instance_id=None)
        or when deleting an interface with O(state=absent).
    default: false
    type: bool
  delete_on_termination:
    description:
      - Delete the interface when the instance it is attached to is terminated. You can only specify this flag when the
        interface is being modified, not on creation.
    required: false
    type: bool
  source_dest_check:
    description:
      - By default, interfaces perform source/destination checks. NAT instances however need this check to be disabled.
        You can only specify this flag when the interface is being modified, not on creation.
    required: false
    type: bool
  secondary_private_ip_addresses:
    description:
      - A list of IP addresses to assign as secondary IP addresses to the network interface.
      - This option is mutually exclusive of O(secondary_private_ip_address_count).
    required: false
    type: list
    elements: str
  purge_secondary_private_ip_addresses:
    description:
      - To be used with O(secondary_private_ip_addresses) to determine whether or not to remove any secondary IP addresses other than those specified.
      - Set O(secondary_private_ip_addresses=[]) to purge all secondary addresses.
    default: false
    type: bool
  secondary_private_ip_address_count:
    description:
      - The number of secondary IP addresses to assign to the network interface.
      - This option is mutually exclusive of O(secondary_private_ip_addresses).
    required: false
    type: int
  allow_reassignment:
    description:
      - Indicates whether to allow an IP address that is already assigned to another network interface or instance
        to be reassigned to the specified network interface.
    required: false
    default: false
    type: bool
  name:
    description:
      - Name for the ENI. This will create a tag with the key V(Name) and the value assigned here.
      - This can be used in conjunction with O(subnet_id) as another means of identifiying a network interface.
      - AWS does not enforce unique V(Name) tags, so duplicate names are possible if you configure it that way.
        If that is the case, you will need to provide other identifying information such as O(private_ip_address) or O(eni_id).
    required: false
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
notes:
  - This module identifies and ENI based on either the O(eni_id), a combination of O(private_ip_address) and O(subnet_id),
    or a combination of O(instance_id) and O(device_index). Any of these options will let you specify a particular ENI.
  - Support for O(tags) and O(purge_tags) was added in release 1.3.0.
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ENI. As no security group is defined, ENI will be created in default security group
- amazon.aws.ec2_eni:
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present

# Create an ENI and attach it to an instance
- amazon.aws.ec2_eni:
    instance_id: i-xxxxxxx
    device_index: 1
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present

# Create an ENI with two secondary addresses
- amazon.aws.ec2_eni:
    subnet_id: subnet-xxxxxxxx
    state: present
    secondary_private_ip_address_count: 2

# Assign a secondary IP address to an existing ENI
# This will purge any existing IPs
- amazon.aws.ec2_eni:
    subnet_id: subnet-xxxxxxxx
    eni_id: eni-yyyyyyyy
    state: present
    secondary_private_ip_addresses:
      - 172.16.1.1

# Remove any secondary IP addresses from an existing ENI
- amazon.aws.ec2_eni:
    subnet_id: subnet-xxxxxxxx
    eni_id: eni-yyyyyyyy
    state: present
    secondary_private_ip_address_count: 0

# Destroy an ENI, detaching it from any instance if necessary
- amazon.aws.ec2_eni:
    eni_id: eni-xxxxxxx
    force_detach: true
    state: absent

# Update an ENI
- amazon.aws.ec2_eni:
    eni_id: eni-xxxxxxx
    description: "My new description"
    state: present

# Update an ENI using name and subnet_id
- amazon.aws.ec2_eni:
    name: eni-20
    subnet_id: subnet-xxxxxxx
    description: "My new description"
    state: present

# Update an ENI identifying it by private_ip_address and subnet_id
- amazon.aws.ec2_eni:
    subnet_id: subnet-xxxxxxx
    private_ip_address: 172.16.1.1
    description: "My new description"

# Detach an ENI from an instance
- amazon.aws.ec2_eni:
    eni_id: eni-xxxxxxx
    instance_id: None
    state: present

### Delete an interface on termination
# First create the interface
- amazon.aws.ec2_eni:
    instance_id: i-xxxxxxx
    device_index: 1
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present
  register: eni

# Modify the interface to enable the delete_on_terminaton flag
- amazon.aws.ec2_eni:
    eni_id: "{{ eni.interface.id }}"
    delete_on_termination: true
"""


RETURN = r"""
interface:
  description: Network interface attributes.
  returned: when state != absent
  type: complex
  contains:
    attachment:
      description: The network interface attachment.
      type: dict
      sample: {
            "attach_time": "2024-04-25T20:57:20+00:00",
            "attachment_id": "eni-attach-0ddce58b341a1846f",
            "delete_on_termination": true,
            "device_index": 0,
            "instance_id": "i-032cb1cceb29250d2",
            "status": "attached"
        }
    description:
      description: Interface description.
      type: str
      sample: Firewall network interface
    groups:
      description: Dict of security groups.
      type: dict
      sample: { "sg-f8a8a9da": "default" }
    id:
      description: Network interface id.
      type: str
      sample: "eni-1d889198"
    mac_address:
      description: Interface's physical address.
      type: str
      sample: "00:00:5E:00:53:23"
    name:
      description: The name of the ENI.
      type: str
      sample: "my-eni-20"
    owner_id:
      description: AWS account id.
      type: str
      sample: 812381371
    private_ip_address:
      description: Primary ip address of this interface.
      type: str
      sample: 10.20.30.40
    private_ip_addresses:
      description: List of all private ip addresses associated to this interface.
      type: list
      elements: dict
      sample: [ { "primary_address": true, "private_ip_address": "10.20.30.40" } ]
    source_dest_check:
      description: Value of source/dest check flag.
      type: bool
      sample: True
    status:
      description: Network interface status.
      type: str
      sample: "pending"
    subnet_id:
      description: Which vpc subnet the interface is bound.
      type: str
      sample: subnet-b0a0393c
    tags:
      description: The dictionary of tags associated with the ENI.
      type: dict
      sample: { "Name": "my-eni", "group": "Finance" }
    vpc_id:
      description: Which vpc this network interface is bound.
      type: str
      sample: vpc-9a9a9da
"""

import time
from ipaddress import ip_address
from ipaddress import ip_network

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import assign_private_ip_addresses
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import attach_network_interface
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_network_interface
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_network_interface
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_network_interfaces
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_subnets
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import detach_network_interface
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_ec2_security_group_ids_from_names
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_network_interface_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import unassign_private_ip_addresses
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def get_eni_info(interface):
    # Private addresses
    private_addresses = []
    if "PrivateIpAddresses" in interface:
        for ip in interface["PrivateIpAddresses"]:
            private_addresses.append({"private_ip_address": ip["PrivateIpAddress"], "primary_address": ip["Primary"]})

    groups = {}
    if "Groups" in interface:
        for group in interface["Groups"]:
            groups[group["GroupId"]] = group["GroupName"]

    interface_info = {
        "id": interface.get("NetworkInterfaceId"),
        "subnet_id": interface.get("SubnetId"),
        "vpc_id": interface.get("VpcId"),
        "description": interface.get("Description"),
        "owner_id": interface.get("OwnerId"),
        "status": interface.get("Status"),
        "mac_address": interface.get("MacAddress"),
        "private_ip_address": interface.get("PrivateIpAddress"),
        "source_dest_check": interface.get("SourceDestCheck"),
        "groups": groups,
        "private_ip_addresses": private_addresses,
    }

    if "TagSet" in interface:
        tags = boto3_tag_list_to_ansible_dict(interface["TagSet"])
        if "Name" in tags:
            interface_info["name"] = tags["Name"]
        interface_info["tags"] = tags

    if "Attachment" in interface:
        interface_info["attachment"] = {
            "attachment_id": interface["Attachment"].get("AttachmentId"),
            "instance_id": interface["Attachment"].get("InstanceId"),
            "device_index": interface["Attachment"].get("DeviceIndex"),
            "status": interface["Attachment"].get("Status"),
            "attach_time": interface["Attachment"].get("AttachTime"),
            "delete_on_termination": interface["Attachment"].get("DeleteOnTermination"),
        }

    return interface_info


def correct_ips(connection, ip_list, module, eni_id):
    eni = describe_eni(connection, module, eni_id)
    private_addresses = set()
    if "PrivateIpAddresses" in eni:
        for ip in eni["PrivateIpAddresses"]:
            private_addresses.add(ip["PrivateIpAddress"])

    ip_set = set(ip_list)

    return ip_set.issubset(private_addresses)


def absent_ips(connection, ip_list, module, eni_id):
    eni = describe_eni(connection, module, eni_id)
    private_addresses = set()
    if "PrivateIpAddresses" in eni:
        for ip in eni["PrivateIpAddresses"]:
            private_addresses.add(ip["PrivateIpAddress"])

    ip_set = set(ip_list)

    return not ip_set.union(private_addresses)


def correct_ip_count(connection, ip_count, module, eni_id):
    eni = describe_eni(connection, module, eni_id)
    private_addresses = set()
    if "PrivateIpAddresses" in eni:
        for ip in eni["PrivateIpAddresses"]:
            private_addresses.add(ip["PrivateIpAddress"])

    return bool(len(private_addresses) == ip_count)


def wait_for(function_pointer, *args):
    max_wait = 30
    interval_time = 3
    current_wait = 0
    while current_wait < max_wait:
        time.sleep(interval_time)
        current_wait += interval_time
        if function_pointer(*args):
            break


def create_eni(connection, vpc_id, module):
    instance_id = module.params.get("instance_id")
    attached = module.params.get("attached")
    if instance_id == "None":
        instance_id = None
    device_index = module.params.get("device_index")
    subnet_id = module.params.get("subnet_id")
    private_ip_address = module.params.get("private_ip_address")
    description = module.params.get("description")
    security_groups = get_ec2_security_group_ids_from_names(
        module.params.get("security_groups"), connection, vpc_id=vpc_id
    )
    secondary_private_ip_addresses = module.params.get("secondary_private_ip_addresses")
    secondary_private_ip_address_count = module.params.get("secondary_private_ip_address_count")
    changed = False

    tags = module.params.get("tags") or dict()
    name = module.params.get("name")
    # Make sure that the 'name' parameter sets the Name tag
    if name:
        tags["Name"] = name

    args = {"SubnetId": subnet_id}
    if private_ip_address:
        args["PrivateIpAddress"] = private_ip_address
    if description:
        args["Description"] = description
    if len(security_groups) > 0:
        args["Groups"] = security_groups
    if tags:
        args["TagSpecifications"] = boto3_tag_specifications(tags, types="network-interface")

    # check if provided private_ip_address is within the subnet's address range
    if private_ip_address:
        try:
            cidr_block = describe_subnets(connection, SubnetIds=[str(subnet_id)])[0]["CidrBlock"]
        except AnsibleEC2Error as e:
            module.fail_json_aws_error(e)
        valid_private_ip = ip_address(private_ip_address) in ip_network(cidr_block)
        if not valid_private_ip:
            module.fail_json(
                changed=False,
                msg="Error: cannot create ENI - Address does not fall within the subnet's address range.",
            )
    if module.check_mode:
        module.exit_json(changed=True, msg="Would have created ENI if not in check mode.")

    try:
        eni = create_network_interface(connection, **args)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)
    # Once we have an ID make sure we're always modifying the same object
    eni_id = eni["NetworkInterfaceId"]
    wait_for_resource_state(connection, module, "network_interface_available", NetworkInterfaceIds=[eni_id])

    if attached and instance_id is not None:
        try:
            attach_network_interface(
                connection,
                InstanceId=instance_id,
                DeviceIndex=device_index,
                NetworkInterfaceId=eni["NetworkInterfaceId"],
            )
        except AnsibleEC2Error as e:
            delete_network_interface(connection, eni_id)
            module.fail_json_aws_error(e)
        wait_for_resource_state(connection, module, "network_interface_attached", NetworkInterfaceIds=[eni_id])

    if secondary_private_ip_address_count is not None:
        try:
            assign_private_ip_addresses(
                connection,
                NetworkInterfaceId=eni["NetworkInterfaceId"],
                SecondaryPrivateIpAddressCount=secondary_private_ip_address_count,
            )
            wait_for(correct_ip_count, connection, secondary_private_ip_address_count, module, eni_id)
        except AnsibleEC2Error as e:
            delete_network_interface(connection, eni_id)
            module.fail_json_aws_error(e)

    if secondary_private_ip_addresses is not None:
        try:
            assign_private_ip_addresses(
                connection,
                NetworkInterfaceId=eni["NetworkInterfaceId"],
                PrivateIpAddresses=secondary_private_ip_addresses,
            )
            wait_for(correct_ips, connection, secondary_private_ip_addresses, module, eni_id)
        except AnsibleEC2Error as e:
            delete_network_interface(connection, eni_id)
            module.fail_json_aws_error(e)

    # Refresh the eni data
    eni = describe_eni(connection, module, eni_id)
    changed = True

    module.exit_json(changed=changed, interface=get_eni_info(eni))


def modify_eni(connection, module, eni):
    instance_id = module.params.get("instance_id")
    attached = module.params.get("attached")
    device_index = module.params.get("device_index")
    description = module.params.get("description")
    security_groups = module.params.get("security_groups")
    source_dest_check = module.params.get("source_dest_check")
    delete_on_termination = module.params.get("delete_on_termination")
    secondary_private_ip_addresses = module.params.get("secondary_private_ip_addresses")
    purge_secondary_private_ip_addresses = module.params.get("purge_secondary_private_ip_addresses")
    secondary_private_ip_address_count = module.params.get("secondary_private_ip_address_count")
    allow_reassignment = module.params.get("allow_reassignment")
    changed = False
    tags = module.params.get("tags")
    name = module.params.get("name")
    purge_tags = module.params.get("purge_tags")

    eni = uniquely_find_eni(connection, module, eni)
    eni_id = eni["NetworkInterfaceId"]

    try:
        if description is not None:
            if "Description" not in eni or eni["Description"] != description:
                if not module.check_mode:
                    modify_network_interface_attribute(
                        connection, NetworkInterfaceId=eni_id, Description={"Value": description}
                    )
                changed = True
        if len(security_groups) > 0:
            groups = get_ec2_security_group_ids_from_names(security_groups, connection, vpc_id=eni["VpcId"])
            if sorted(get_sec_group_list(eni["Groups"])) != sorted(groups):
                if not module.check_mode:
                    modify_network_interface_attribute(connection, NetworkInterfaceId=eni_id, Groups=groups)
                changed = True
        if source_dest_check is not None:
            if "SourceDestCheck" not in eni or eni["SourceDestCheck"] != source_dest_check:
                if not module.check_mode:
                    modify_network_interface_attribute(
                        connection, NetworkInterfaceId=eni_id, SourceDestCheck={"Value": source_dest_check}
                    )
                changed = True
        if delete_on_termination is not None and "Attachment" in eni:
            if eni["Attachment"]["DeleteOnTermination"] is not delete_on_termination:
                if not module.check_mode:
                    modify_network_interface_attribute(
                        connection,
                        NetworkInterfaceId=eni_id,
                        Attachment={
                            "AttachmentId": eni["Attachment"]["AttachmentId"],
                            "DeleteOnTermination": delete_on_termination,
                        },
                    )
                    if delete_on_termination:
                        waiter = "network_interface_delete_on_terminate"
                    else:
                        waiter = "network_interface_no_delete_on_terminate"
                    wait_for_resource_state(connection, module, waiter, NetworkInterfaceIds=[eni_id])
                changed = True

        current_secondary_addresses = []
        if "PrivateIpAddresses" in eni:
            current_secondary_addresses = [i["PrivateIpAddress"] for i in eni["PrivateIpAddresses"] if not i["Primary"]]

        if secondary_private_ip_addresses is not None:
            secondary_addresses_to_remove = list(set(current_secondary_addresses) - set(secondary_private_ip_addresses))
            if secondary_addresses_to_remove and purge_secondary_private_ip_addresses:
                if not module.check_mode:
                    unassign_private_ip_addresses(
                        connection,
                        NetworkInterfaceId=eni_id,
                        PrivateIpAddresses=list(set(current_secondary_addresses) - set(secondary_private_ip_addresses)),
                    )
                    wait_for(absent_ips, connection, secondary_addresses_to_remove, module, eni_id)
                changed = True
            secondary_addresses_to_add = list(set(secondary_private_ip_addresses) - set(current_secondary_addresses))
            if secondary_addresses_to_add:
                if not module.check_mode:
                    assign_private_ip_addresses(
                        connection,
                        NetworkInterfaceId=eni_id,
                        PrivateIpAddresses=secondary_addresses_to_add,
                        AllowReassignment=allow_reassignment,
                    )
                    wait_for(correct_ips, connection, secondary_addresses_to_add, module, eni_id)
                changed = True

        if secondary_private_ip_address_count is not None:
            current_secondary_address_count = len(current_secondary_addresses)
            if secondary_private_ip_address_count > current_secondary_address_count:
                if not module.check_mode:
                    assign_private_ip_addresses(
                        connection,
                        NetworkInterfaceId=eni_id,
                        SecondaryPrivateIpAddressCount=(
                            secondary_private_ip_address_count - current_secondary_address_count
                        ),
                        AllowReassignment=allow_reassignment,
                    )
                    wait_for(correct_ip_count, connection, secondary_private_ip_address_count, module, eni_id)
                changed = True
            elif secondary_private_ip_address_count < current_secondary_address_count:
                # How many of these addresses do we want to remove
                if not module.check_mode:
                    secondary_addresses_to_remove_count = (
                        current_secondary_address_count - secondary_private_ip_address_count
                    )
                    unassign_private_ip_addresses(
                        connection,
                        NetworkInterfaceId=eni_id,
                        PrivateIpAddresses=current_secondary_addresses[:secondary_addresses_to_remove_count],
                    )
                    wait_for(correct_ip_count, connection, secondary_private_ip_address_count, module, eni_id)
                changed = True

        if attached is True:
            if "Attachment" in eni and eni["Attachment"]["InstanceId"] != instance_id:
                if not module.check_mode:
                    detach_eni(connection, eni, module)
                    attach_network_interface(
                        connection,
                        InstanceId=instance_id,
                        DeviceIndex=device_index,
                        NetworkInterfaceId=eni_id,
                    )
                    wait_for_resource_state(
                        connection, module, "network_interface_attached", NetworkInterfaceIds=[eni_id]
                    )
                changed = True
            if "Attachment" not in eni:
                if not module.check_mode:
                    attach_network_interface(
                        connection,
                        InstanceId=instance_id,
                        DeviceIndex=device_index,
                        NetworkInterfaceId=eni_id,
                    )
                    wait_for_resource_state(
                        connection, module, "network_interface_attached", NetworkInterfaceIds=[eni_id]
                    )
                changed = True

        elif attached is False:
            changed |= detach_eni(connection, eni, module)
            wait_for_resource_state(connection, module, "network_interface_available", NetworkInterfaceIds=[eni_id])

        changed |= manage_tags(connection, module, eni, name, tags, purge_tags)

    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    eni = describe_eni(connection, module, eni_id)
    if module.check_mode and changed:
        module.exit_json(
            changed=changed, msg=f"Would have modified ENI: {eni['NetworkInterfaceId']} if not in check mode"
        )
    module.exit_json(changed=changed, interface=get_eni_info(eni))


def delete_eni(connection, module):
    eni = uniquely_find_eni(connection, module)
    if not eni:
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have deleted ENI if not in check mode.")

    eni_id = eni["NetworkInterfaceId"]
    force_detach = module.params.get("force_detach")

    try:
        if force_detach is True:
            if "Attachment" in eni:
                detach_network_interface(
                    connection,
                    attachment_id=eni["Attachment"]["AttachmentId"],
                    force=True,
                )
                wait_for_resource_state(
                    connection,
                    module,
                    "network_interface_available",
                    delay=5,
                    max_attempts=80,
                    NetworkInterfaceIds=[eni_id],
                )
            changed = delete_network_interface(connection, eni_id)
        else:
            changed = delete_network_interface(connection, eni_id)

        module.exit_json(changed=changed)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


def detach_eni(connection, eni, module):
    if module.check_mode:
        module.exit_json(changed=True, msg="Would have detached ENI if not in check mode.")

    eni_id = eni["NetworkInterfaceId"]

    force_detach = module.params.get("force_detach")
    if "Attachment" in eni:
        detach_network_interface(
            connection,
            attachment_id=eni["Attachment"]["AttachmentId"],
            force=force_detach,
        )
        wait_for_resource_state(
            connection, module, "network_interface_available", delay=5, max_attempts=80, NetworkInterfaceIds=[eni_id]
        )
        return True

    return False


def describe_eni(connection, module, eni_id):
    try:
        result = None
        enis = describe_network_interfaces(connection, NetworkInterfaceIds=[eni_id])
        if enis:
            result = enis[0]
        return result
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


def uniquely_find_eni(connection, module, eni=None):
    if eni:
        # In the case of create, eni_id will not be a param but we can still get the eni_id after creation
        if "NetworkInterfaceId" in eni:
            eni_id = eni["NetworkInterfaceId"]
        else:
            eni_id = None
    else:
        eni_id = module.params.get("eni_id")

    private_ip_address = module.params.get("private_ip_address")
    subnet_id = module.params.get("subnet_id")
    instance_id = module.params.get("instance_id")
    device_index = module.params.get("device_index")
    attached = module.params.get("attached")
    name = module.params.get("name")

    filters = []

    # proceed only if we're unequivocally specifying an ENI
    if eni_id is None and private_ip_address is None and (instance_id is None and device_index is None):
        return None

    if eni_id:
        filters.append({"Name": "network-interface-id", "Values": [eni_id]})

    if private_ip_address and subnet_id and not filters:
        filters.append({"Name": "private-ip-address", "Values": [private_ip_address]})
        filters.append({"Name": "subnet-id", "Values": [subnet_id]})

    if not attached and instance_id and device_index and not filters:
        filters.append({"Name": "attachment.instance-id", "Values": [instance_id]})
        filters.append({"Name": "attachment.device-index", "Values": [str(device_index)]})

    if name and subnet_id and not filters:
        filters.append({"Name": "tag:Name", "Values": [name]})
        filters.append({"Name": "subnet-id", "Values": [subnet_id]})

    if not filters:
        return None

    try:
        result = None
        enis = describe_network_interfaces(connection, Filters=filters)
        if len(enis) == 1:
            result = enis[0]
        return result
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


def get_sec_group_list(groups):
    # Build list of remote security groups
    remote_security_groups = []
    for group in groups:
        remote_security_groups.append(group["GroupId"])

    return remote_security_groups


def _get_vpc_id(connection, module, subnet_id):
    try:
        return describe_subnets(connection, SubnetIds=[subnet_id])[0]["VpcId"]
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


def manage_tags(connection, module, eni, name, tags, purge_tags):
    # Do not purge tags unless tags is not None
    if tags is None:
        purge_tags = False
        tags = {}

    if name:
        tags["Name"] = name

    eni_id = eni["NetworkInterfaceId"]

    changed = ensure_ec2_tags(connection, module, eni_id, tags=tags, purge_tags=purge_tags)
    return changed


def main():
    argument_spec = dict(
        eni_id=dict(default=None, type="str"),
        instance_id=dict(default=None, type="str"),
        private_ip_address=dict(type="str"),
        subnet_id=dict(type="str"),
        description=dict(type="str"),
        security_groups=dict(default=[], type="list", elements="str"),
        device_index=dict(default=0, type="int"),
        state=dict(default="present", choices=["present", "absent"]),
        force_detach=dict(default="no", type="bool"),
        source_dest_check=dict(default=None, type="bool"),
        delete_on_termination=dict(default=None, type="bool"),
        secondary_private_ip_addresses=dict(default=None, type="list", elements="str"),
        purge_secondary_private_ip_addresses=dict(default=False, type="bool"),
        secondary_private_ip_address_count=dict(default=None, type="int"),
        allow_reassignment=dict(default=False, type="bool"),
        attached=dict(default=None, type="bool"),
        name=dict(default=None, type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["secondary_private_ip_addresses", "secondary_private_ip_address_count"]],
        required_if=(
            [
                ("attached", True, ["instance_id"]),
                ("purge_secondary_private_ip_addresses", True, ["secondary_private_ip_addresses"]),
            ]
        ),
        supports_check_mode=True,
    )

    connection = module.client("ec2")
    state = module.params.get("state")

    if state == "present":
        eni = uniquely_find_eni(connection, module)
        if eni is None:
            subnet_id = module.params.get("subnet_id")
            if subnet_id is None:
                module.fail_json(msg="subnet_id is required when creating a new ENI")

            vpc_id = _get_vpc_id(connection, module, subnet_id)
            create_eni(connection, vpc_id, module)
        else:
            modify_eni(connection, module, eni)

    elif state == "absent":
        delete_eni(connection, module)


if __name__ == "__main__":
    main()

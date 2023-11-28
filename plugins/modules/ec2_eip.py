#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_eip
version_added: 5.0.0
short_description: manages EC2 elastic IP (EIP) addresses.
description:
  - This module can allocate or release an EIP.
  - This module can associate/disassociate an EIP with instances or network interfaces.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  device_id:
    description:
      - The id of the device for the EIP.
      - Can be an EC2 Instance id or Elastic Network Interface (ENI) id.
      - When specifying an ENI id, I(in_vpc) must be C(true)
      - The C(instance_id) alias was removed in release 6.0.0.
    required: false
    type: str
  public_ip:
    description:
      - The IP address of a previously allocated EIP.
      - When I(state=present) and device is specified, the EIP is associated with the device.
      - When I(state=absent) and device is specified, the EIP is disassociated from the device.
    aliases: [ ip ]
    type: str
  state:
    description:
      - When C(state=present), allocate an EIP or associate an existing EIP with a device.
      - When C(state=absent), disassociate the EIP from the device and optionally release it.
    choices: ['present', 'absent']
    default: present
    type: str
  in_vpc:
    description:
      - Allocate an EIP inside a VPC or not.
      - Required if specifying an ENI with I(device_id).
    default: false
    type: bool
  reuse_existing_ip_allowed:
    description:
      - Reuse an EIP that is not associated to a device (when available), instead of allocating a new one.
    default: false
    type: bool
  release_on_disassociation:
    description:
      - Whether or not to automatically release the EIP when it is disassociated.
    default: false
    type: bool
  private_ip_address:
    description:
      - The primary or secondary private IP address to associate with the Elastic IP address.
    type: str
  allow_reassociation:
    description:
      -  Specify this option to allow an Elastic IP address that is already associated with another
         network interface or instance to be re-associated with the specified instance or interface.
    default: false
    type: bool
  tag_name:
    description:
      - When I(reuse_existing_ip_allowed=true), supplement with this option to only reuse
        an Elastic IP if it is tagged with I(tag_name).
    type: str
  tag_value:
    description:
      - Supplements I(tag_name) but also checks that the value of the tag provided in I(tag_name) matches I(tag_value).
    type: str
  public_ipv4_pool:
    description:
      - Allocates the new Elastic IP from the provided public IPv4 pool (BYOIP)
        only applies to newly allocated Elastic IPs, isn't validated when I(reuse_existing_ip_allowed=true).
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3

author:
  - "Rick Mendes (@rickmendes) <rmendes@illumina.com>"
notes:
  - There may be a delay between the time the EIP is assigned and when
    the cloud instance is reachable via the new address. Use wait_for and
    pause to delay further playbook execution until the instance is reachable,
    if necessary.
  - This module returns multiple changed statuses on disassociation or release.
    It returns an overall status based on any changes occurring. It also returns
    individual changed statuses for disassociation and release.
  - Support for I(tags) and I(purge_tags) was added in release 2.1.0.
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: associate an elastic IP with an instance
  amazon.aws.ec2_eip:
    device_id: i-1212f003
    ip: 93.184.216.119

- name: associate an elastic IP with a device
  amazon.aws.ec2_eip:
    device_id: eni-c8ad70f3
    ip: 93.184.216.119

- name: associate an elastic IP with a device and allow reassociation
  amazon.aws.ec2_eip:
    device_id: eni-c8ad70f3
    public_ip: 93.184.216.119
    allow_reassociation: true

- name: disassociate an elastic IP from an instance
  amazon.aws.ec2_eip:
    device_id: i-1212f003
    ip: 93.184.216.119
    state: absent

- name: disassociate an elastic IP with a device
  amazon.aws.ec2_eip:
    device_id: eni-c8ad70f3
    ip: 93.184.216.119
    state: absent

- name: allocate a new elastic IP and associate it with an instance
  amazon.aws.ec2_eip:
    device_id: i-1212f003

- name: allocate a new elastic IP without associating it to anything
  amazon.aws.ec2_eip:
    state: present
  register: eip

- name: output the IP
  ansible.builtin.debug:
    msg: "Allocated IP is {{ eip.public_ip }}"

- name: provision new instances with ec2
  amazon.aws.ec2:
    keypair: mykey
    instance_type: c1.medium
    image: ami-40603AD1
    wait: true
    group: webserver
    count: 3
  register: ec2

- name: associate new elastic IPs with each of the instances
  amazon.aws.ec2_eip:
    device_id: "{{ item }}"
  loop: "{{ ec2.instance_ids }}"

- name: allocate a new elastic IP inside a VPC in us-west-2
  amazon.aws.ec2_eip:
    region: us-west-2
    in_vpc: true
  register: eip

- name: output the IP
  ansible.builtin.debug:
    msg: "Allocated IP inside a VPC is {{ eip.public_ip }}"

- name: allocate eip - reuse unallocated ips (if found) with FREE tag
  amazon.aws.ec2_eip:
    region: us-east-1
    in_vpc: true
    reuse_existing_ip_allowed: true
    tag_name: FREE

- name: allocate eip - reuse unallocated ips if tag reserved is nope
  amazon.aws.ec2_eip:
    region: us-east-1
    in_vpc: true
    reuse_existing_ip_allowed: true
    tag_name: reserved
    tag_value: nope

- name: allocate new eip - from servers given ipv4 pool
  amazon.aws.ec2_eip:
    region: us-east-1
    in_vpc: true
    public_ipv4_pool: ipv4pool-ec2-0588c9b75a25d1a02

- name: allocate eip - from a given pool (if no free addresses where dev-servers tag is dynamic)
  amazon.aws.ec2_eip:
    region: us-east-1
    in_vpc: true
    reuse_existing_ip_allowed: true
    tag_name: dev-servers
    public_ipv4_pool: ipv4pool-ec2-0588c9b75a25d1a02

- name: allocate eip from pool - check if tag reserved_for exists and value is our hostname
  amazon.aws.ec2_eip:
    region: us-east-1
    in_vpc: true
    reuse_existing_ip_allowed: true
    tag_name: reserved_for
    tag_value: "{{ inventory_hostname }}"
    public_ipv4_pool: ipv4pool-ec2-0588c9b75a25d1a02
"""

RETURN = r"""
allocation_id:
  description: allocation_id of the elastic ip
  returned: on success
  type: str
  sample: eipalloc-51aa3a6c
public_ip:
  description: an elastic ip address
  returned: on success
  type: str
  sample: 52.88.159.209
"""

try:
    import botocore.exceptions
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


class EipError(Exception):
    pass


def associate_ip_and_device(
    ec2, module, address, private_ip_address, device_id, allow_reassociation, check_mode, is_instance=True
):
    if address_is_associated_with_device(ec2, module, address, device_id, is_instance):
        return {"changed": False}

    # If we're in check mode, nothing else to do
    if not check_mode:
        if is_instance:
            try:
                params = dict(
                    InstanceId=device_id,
                    AllowReassociation=allow_reassociation,
                )
                if private_ip_address:
                    params["PrivateIpAddress"] = private_ip_address
                if address["Domain"] == "vpc":
                    params["AllocationId"] = address["AllocationId"]
                else:
                    params["PublicIp"] = address["PublicIp"]
                res = ec2.associate_address(aws_retry=True, **params)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                msg = f"Couldn't associate Elastic IP address with instance '{device_id}'"
                module.fail_json_aws(e, msg=msg)
        else:
            params = dict(
                NetworkInterfaceId=device_id,
                AllocationId=address["AllocationId"],
                AllowReassociation=allow_reassociation,
            )

            if private_ip_address:
                params["PrivateIpAddress"] = private_ip_address

            try:
                res = ec2.associate_address(aws_retry=True, **params)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                msg = f"Couldn't associate Elastic IP address with network interface '{device_id}'"
                module.fail_json_aws(e, msg=msg)
        if not res:
            module.fail_json(msg="Association failed.")

    return {"changed": True}


def disassociate_ip_and_device(ec2, module, address, device_id, check_mode, is_instance=True):
    if not address_is_associated_with_device(ec2, module, address, device_id, is_instance):
        return {"changed": False}

    # If we're in check mode, nothing else to do
    if not check_mode:
        try:
            if address["Domain"] == "vpc":
                ec2.disassociate_address(AssociationId=address["AssociationId"], aws_retry=True)
            else:
                ec2.disassociate_address(PublicIp=address["PublicIp"], aws_retry=True)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Dissassociation of Elastic IP failed")

    return {"changed": True}


@AWSRetry.jittered_backoff()
def find_address(ec2, module, public_ip, device_id, is_instance=True):
    """Find an existing Elastic IP address"""
    filters = []
    kwargs = {}

    if public_ip:
        kwargs["PublicIps"] = [public_ip]
    elif device_id:
        if is_instance:
            filters.append({"Name": "instance-id", "Values": [device_id]})
        else:
            filters.append({"Name": "network-interface-id", "Values": [device_id]})

    if len(filters) > 0:
        kwargs["Filters"] = filters
    elif len(filters) == 0 and public_ip is None:
        return None

    try:
        addresses = ec2.describe_addresses(**kwargs)
    except is_boto3_error_code("InvalidAddress.NotFound") as e:
        # If we're releasing and we can't find it, it's already gone...
        if module.params.get("state") == "absent":
            module.exit_json(changed=False, disassociated=False, released=False)
        module.fail_json_aws(e, msg="Couldn't obtain list of existing Elastic IP addresses")

    addresses = addresses["Addresses"]
    if len(addresses) == 1:
        return addresses[0]
    elif len(addresses) > 1:
        msg = f"Found more than one address using args {kwargs} Addresses found: {addresses}"
        module.fail_json_aws(botocore.exceptions.ClientError, msg=msg)


def address_is_associated_with_device(ec2, module, address, device_id, is_instance=True):
    """Check if the elastic IP is currently associated with the device"""
    address = find_address(ec2, module, address["PublicIp"], device_id, is_instance)
    if address:
        if is_instance:
            if "InstanceId" in address and address["InstanceId"] == device_id:
                return address
        else:
            if "NetworkInterfaceId" in address and address["NetworkInterfaceId"] == device_id:
                return address
    return False


def allocate_address(
    ec2,
    module,
    domain,
    reuse_existing_ip_allowed,
    check_mode,
    tags,
    search_tags=None,
    public_ipv4_pool=None,
):
    """Allocate a new elastic IP address (when needed) and return it"""
    if not domain:
        domain = "standard"

    if reuse_existing_ip_allowed:
        filters = []
        filters.append({"Name": "domain", "Values": [domain]})

        if search_tags is not None:
            filters += ansible_dict_to_boto3_filter_list(search_tags)

        try:
            all_addresses = ec2.describe_addresses(Filters=filters, aws_retry=True)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't obtain list of existing Elastic IP addresses")

        all_addresses = all_addresses["Addresses"]

        if domain == "vpc":
            unassociated_addresses = [a for a in all_addresses if not a.get("AssociationId", None)]
        else:
            unassociated_addresses = [a for a in all_addresses if not a["InstanceId"]]
        if unassociated_addresses:
            return unassociated_addresses[0], False

    if public_ipv4_pool:
        return (
            allocate_address_from_pool(
                ec2,
                module,
                domain,
                check_mode,
                public_ipv4_pool,
                tags,
            ),
            True,
        )

    params = {"Domain": domain}
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="elastic-ip")

    try:
        if check_mode:
            return None, True
        result = ec2.allocate_address(aws_retry=True, **params), True
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't allocate Elastic IP address")
    return result


def release_address(ec2, module, address, check_mode):
    """Release a previously allocated elastic IP address"""

    # If we're in check mode, nothing else to do
    if not check_mode:
        try:
            ec2.release_address(AllocationId=address["AllocationId"], aws_retry=True)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't release Elastic IP address")

    return {"changed": True}


@AWSRetry.jittered_backoff()
def describe_eni_with_backoff(ec2, module, device_id):
    try:
        return ec2.describe_network_interfaces(NetworkInterfaceIds=[device_id])
    except is_boto3_error_code("InvalidNetworkInterfaceID.NotFound") as e:
        module.fail_json_aws(e, msg="Couldn't get list of network interfaces.")


def find_device(ec2, module, device_id, is_instance=True):
    """Attempt to find the EC2 instance and return it"""

    if is_instance:
        try:
            paginator = ec2.get_paginator("describe_instances")
            reservations = list(paginator.paginate(InstanceIds=[device_id]).search("Reservations[]"))
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't get list of instances")

        if len(reservations) == 1:
            instances = reservations[0]["Instances"]
            if len(instances) == 1:
                return instances[0]
    else:
        try:
            interfaces = describe_eni_with_backoff(ec2, module, device_id)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't get list of network interfaces.")
        if len(interfaces) == 1:
            return interfaces[0]


def ensure_present(
    ec2,
    module,
    domain,
    address,
    private_ip_address,
    device_id,
    reuse_existing_ip_allowed,
    allow_reassociation,
    check_mode,
    tags,
    is_instance=True,
):
    changed = False

    # Return the EIP object since we've been given a public IP
    if not address:
        if check_mode:
            return {"changed": True}

        address, changed = allocate_address(
            ec2,
            module,
            domain,
            reuse_existing_ip_allowed,
            check_mode,
            tags,
        )

    if device_id:
        # Allocate an IP for instance since no public_ip was provided
        if is_instance:
            instance = find_device(ec2, module, device_id)
            if reuse_existing_ip_allowed:
                if instance["VpcId"] and len(instance["VpcId"]) > 0 and domain is None:
                    msg = "You must set 'in_vpc' to true to associate an instance with an existing ip in a vpc"
                    module.fail_json_aws(botocore.exceptions.ClientError, msg=msg)

            # Associate address object (provided or allocated) with instance
            assoc_result = associate_ip_and_device(
                ec2, module, address, private_ip_address, device_id, allow_reassociation, check_mode
            )
        else:
            instance = find_device(ec2, module, device_id, is_instance=False)
            # Associate address object (provided or allocated) with instance
            assoc_result = associate_ip_and_device(
                ec2, module, address, private_ip_address, device_id, allow_reassociation, check_mode, is_instance=False
            )

        changed = changed or assoc_result["changed"]

    return {"changed": changed, "public_ip": address["PublicIp"], "allocation_id": address["AllocationId"]}


def ensure_absent(ec2, module, address, device_id, check_mode, is_instance=True):
    if not address:
        return {"changed": False}

    # disassociating address from instance
    if device_id:
        if is_instance:
            return disassociate_ip_and_device(ec2, module, address, device_id, check_mode)
        else:
            return disassociate_ip_and_device(ec2, module, address, device_id, check_mode, is_instance=False)
    # releasing address
    else:
        return release_address(ec2, module, address, check_mode)


def allocate_address_from_pool(
    ec2,
    module,
    domain,
    check_mode,
    public_ipv4_pool,
    tags,
):
    # type: (EC2Connection, AnsibleAWSModule, str, bool, str) -> Address
    """Overrides botocore's allocate_address function to support BYOIP"""
    if check_mode:
        return None

    params = {}

    if domain is not None:
        params["Domain"] = domain

    if public_ipv4_pool is not None:
        params["PublicIpv4Pool"] = public_ipv4_pool

    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="elastic-ip")

    try:
        result = ec2.allocate_address(aws_retry=True, **params)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't allocate Elastic IP address")
    return result


def generate_tag_dict(module, tag_name, tag_value):
    # type: (AnsibleAWSModule, str, str) -> Optional[Dict]
    """Generates a dictionary to be passed as a filter to Amazon"""
    if tag_name and not tag_value:
        if tag_name.startswith("tag:"):
            tag_name = tag_name.strip("tag:")
        return {"tag-key": tag_name}

    elif tag_name and tag_value:
        if not tag_name.startswith("tag:"):
            tag_name = "tag:" + tag_name
        return {tag_name: tag_value}

    elif tag_value and not tag_name:
        module.fail_json(msg="parameters are required together: ('tag_name', 'tag_value')")


def check_is_instance(device_id, in_vpc):
    if not device_id:
        return False
    if device_id.startswith("i-"):
        return True

    if device_id.startswith("eni-") and not in_vpc:
        raise EipError("If you are specifying an ENI, in_vpc must be true")

    return False


def main():
    argument_spec = dict(
        device_id=dict(required=False),
        public_ip=dict(required=False, aliases=["ip"]),
        state=dict(required=False, default="present", choices=["present", "absent"]),
        in_vpc=dict(required=False, type="bool", default=False),
        reuse_existing_ip_allowed=dict(required=False, type="bool", default=False),
        release_on_disassociation=dict(required=False, type="bool", default=False),
        allow_reassociation=dict(type="bool", default=False),
        private_ip_address=dict(),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(required=False, type="bool", default=True),
        tag_name=dict(),
        tag_value=dict(),
        public_ipv4_pool=dict(),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_by={
            "private_ip_address": ["device_id"],
        },
    )

    ec2 = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    device_id = module.params.get("device_id")
    public_ip = module.params.get("public_ip")
    private_ip_address = module.params.get("private_ip_address")
    state = module.params.get("state")
    in_vpc = module.params.get("in_vpc")
    domain = "vpc" if in_vpc else None
    reuse_existing_ip_allowed = module.params.get("reuse_existing_ip_allowed")
    release_on_disassociation = module.params.get("release_on_disassociation")
    allow_reassociation = module.params.get("allow_reassociation")
    tag_name = module.params.get("tag_name")
    tag_value = module.params.get("tag_value")
    public_ipv4_pool = module.params.get("public_ipv4_pool")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")

    try:
        is_instance = check_is_instance(device_id, in_vpc)
    except EipError as e:
        module.fail_json(msg=str(e))

    # Tags for *searching* for an EIP.
    search_tags = generate_tag_dict(module, tag_name, tag_value)

    try:
        if device_id:
            address = find_address(ec2, module, public_ip, device_id, is_instance=is_instance)
        else:
            address = find_address(ec2, module, public_ip, None)

        if state == "present":
            if device_id:
                result = ensure_present(
                    ec2,
                    module,
                    domain,
                    address,
                    private_ip_address,
                    device_id,
                    reuse_existing_ip_allowed,
                    allow_reassociation,
                    module.check_mode,
                    tags,
                    is_instance=is_instance,
                )
                if "allocation_id" not in result:
                    # Don't check tags on check_mode here - no EIP to pass through
                    module.exit_json(**result)
            else:
                if address:
                    result = {
                        "changed": False,
                        "public_ip": address["PublicIp"],
                        "allocation_id": address["AllocationId"],
                    }
                else:
                    address, changed = allocate_address(
                        ec2,
                        module,
                        domain,
                        reuse_existing_ip_allowed,
                        module.check_mode,
                        tags,
                        search_tags,
                        public_ipv4_pool,
                    )
                    if address:
                        result = {
                            "changed": changed,
                            "public_ip": address["PublicIp"],
                            "allocation_id": address["AllocationId"],
                        }
                    else:
                        # Don't check tags on check_mode here - no EIP to pass through
                        result = {"changed": changed}
                        module.exit_json(**result)

            result["changed"] |= ensure_ec2_tags(
                ec2, module, result["allocation_id"], resource_type="elastic-ip", tags=tags, purge_tags=purge_tags
            )
        else:
            if device_id:
                disassociated = ensure_absent(
                    ec2, module, address, device_id, module.check_mode, is_instance=is_instance
                )

                if release_on_disassociation and disassociated["changed"]:
                    released = release_address(ec2, module, address, module.check_mode)
                    result = {
                        "changed": True,
                        "disassociated": disassociated["changed"],
                        "released": released["changed"],
                    }
                else:
                    result = {
                        "changed": disassociated["changed"],
                        "disassociated": disassociated["changed"],
                        "released": False,
                    }
            else:
                released = release_address(ec2, module, address, module.check_mode)
                result = {"changed": released["changed"], "disassociated": False, "released": released["changed"]}

    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(str(e))

    module.exit_json(**result)


if __name__ == "__main__":
    main()

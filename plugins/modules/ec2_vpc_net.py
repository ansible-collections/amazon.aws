#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_net
version_added: 1.0.0
short_description: Configure AWS Virtual Private Clouds
description:
  - Create, modify, and terminate AWS Virtual Private Clouds (VPCs).
author:
  - Jonathan Davila (@defionscode)
  - Sloane Hertel (@s-hertel)
options:
  name:
    description:
      - The name to give your VPC. This is used in combination with O(cidr_block)
        to determine if a VPC already exists.
      - The value of O(name) overrides any value set for V(Name) in the O(tags)
        parameter.
      - At least one of O(name) and O(vpc_id) must be specified.
      - O(name) must be specified when creating a new VPC.
    type: str
  vpc_id:
    version_added: 4.0.0
    description:
      - The ID of the VPC.
      - At least one of O(name) and O(vpc_id) must be specified.
      - At least one of O(name) and O(cidr_block) must be specified.
    type: str
  cidr_block:
    description:
      - The primary CIDR of the VPC.
      - The first in the list will be used as the primary CIDR
        and is used in conjunction with O(name) to ensure idempotence.
      - Required when O(vpc_id) is not set.
    type: list
    elements: str
  ipv6_cidr:
    description:
      - Request an Amazon-provided IPv6 CIDR block with /56 prefix length. You cannot specify the range of IPv6 addresses,
        or the size of the CIDR block.
      - Default value is V(false) when creating a new VPC.
    type: bool
  purge_cidrs:
    description:
      - Remove CIDRs that are associated with the VPC and are not specified in O(cidr_block).
    default: false
    type: bool
  tenancy:
    description:
      - Whether to be V(default) or V(dedicated) tenancy.
      - This cannot be changed after the VPC has been created.
    default: default
    choices: [ 'default', 'dedicated' ]
    type: str
  dns_support:
    description:
      - Whether to enable AWS DNS support.
      - Default value is V(true) when creating a new VPC.
    type: bool
  dns_hostnames:
    description:
      - Whether to enable AWS hostname support.
      - Default value is V(true) when creating a new VPC.
    type: bool
  dhcp_opts_id:
    description:
      - The id of the DHCP options to use for this VPC.
    type: str
  state:
    description:
      - The state of the VPC. Either absent or present.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  multi_ok:
    description:
      - By default the module will not create another VPC if there is another VPC with the same name and CIDR block.
        Specify O(multi_ok=true) if you want duplicate VPCs created.
    type: bool
    default: false
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a VPC with dedicated tenancy and a couple of tags
  amazon.aws.ec2_vpc_net:
    name: Module_dev2
    cidr_block: 10.10.0.0/16
    region: us-east-1
    tags:
      module: ec2_vpc_net
      this: works
    tenancy: dedicated

- name: create a VPC with dedicated tenancy and request an IPv6 CIDR
  amazon.aws.ec2_vpc_net:
    name: Module_dev2
    cidr_block: 10.10.0.0/16
    ipv6_cidr: true
    region: us-east-1
    tenancy: dedicated

- name: Delete an existing VPC
  amazon.aws.ec2_vpc_net:
    vpc_id: vpc-0123456789abcdef0
    state: absent
"""

RETURN = r"""
vpc:
  description: Info about the VPC that was created or deleted.
  returned: always
  type: complex
  contains:
    cidr_block:
      description: The CIDR of the VPC.
      returned: always
      type: str
      sample: 10.0.0.0/16
    cidr_block_association_set:
      description: IPv4 CIDR blocks associated with the VPC.
      returned: success
      type: list
      sample:
        "cidr_block_association_set": [
            {
                "association_id": "vpc-cidr-assoc-97aeeefd",
                "cidr_block": "10.0.0.0/24",
                "cidr_block_state": {
                    "state": "associated"
                }
            }
        ]
    dhcp_options_id:
      description: The id of the DHCP options associated with this VPC.
      returned: always
      type: str
      sample: dopt-12345678
    id:
      description: VPC resource id.
      returned: always
      type: str
      sample: vpc-12345678
    name:
      description: The Name tag of the VPC.
      returned: When the Name tag has been set on the VPC
      type: str
      sample: MyVPC
      version_added: 4.0.0
    instance_tenancy:
      description: Indicates whether VPC uses default or dedicated tenancy.
      returned: always
      type: str
      sample: default
    ipv6_cidr_block_association_set:
      description: IPv6 CIDR blocks associated with the VPC.
      returned: success
      type: list
      sample:
        "ipv6_cidr_block_association_set": [
            {
                "association_id": "vpc-cidr-assoc-97aeeefd",
                "ipv6_cidr_block": "2001:db8::/56",
                "ipv6_cidr_block_state": {
                    "state": "associated"
                }
            }
        ]
    is_default:
      description: Indicates whether this is the default VPC.
      returned: always
      type: bool
      sample: false
    state:
      description: State of the VPC.
      returned: always
      type: str
      sample: available
    tags:
      description: Tags attached to the VPC, includes name.
      returned: always
      type: complex
      contains:
        Name:
          description: Name tag for the VPC.
          returned: always
          type: str
          sample: pk_vpc4
    owner_id:
      description: The AWS account which owns the VPC.
      returned: always
      type: str
      sample: 123456789012
"""

from time import sleep
from time import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.network import to_subnet

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import associate_dhcp_options
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import associate_vpc_cidr_block
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_vpc
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_vpc
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpcs
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import disassociate_vpc_cidr_block
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_vpc_attribute
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def get_vpc_id(connection, module: AnsibleAWSModule) -> Optional[str]:
    """Returns None or a vpc object depending on the existence of a VPC. When supplied
    with a CIDR, it will check for matching tags to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return None.
    """
    name = module.params.get("name")
    cidr_block = module.params.get("cidr_block")
    multi_ok = module.params.get("multi_ok")
    vpc_filters = ansible_dict_to_boto3_filter_list({"tag:Name": name, "cidr-block": cidr_block})
    matching_vpcs = describe_vpcs(connection, Filters=vpc_filters)
    # If an exact matching using a list of CIDRs isn't found, check for a match with the first CIDR as is documented for C(cidr_block)
    if not matching_vpcs:
        vpc_filters = ansible_dict_to_boto3_filter_list({"tag:Name": name, "cidr-block": [cidr_block[0]]})
        matching_vpcs = describe_vpcs(connection, Filters=vpc_filters)

    vpc_id = None
    if not multi_ok and matching_vpcs:
        if len(matching_vpcs) > 1:
            module.fail_json(
                msg=(
                    f"Currently there are {len(matching_vpcs)} VPCs that have the same name and CIDR block you specified."
                    " If you would like to create the VPC anyway please pass True to the multi_ok param."
                )
            )
        vpc_id = matching_vpcs[0]["VpcId"]
    return vpc_id


def get_vpc(module: AnsibleAWSModule, connection, vpc_id: str) -> Dict[str, Any]:
    wait_for_resource_state(connection, module, "vpc_available", VpcIds=[vpc_id])
    return describe_vpcs(connection, VpcIds=[vpc_id])[0]


def update_vpc_tags(connection, module, vpc_id, tags, name, purge_tags):
    # Name is a tag rather than a direct parameter, we need to inject 'Name'
    # into tags, but since tags isn't explicitly passed we'll treat it not being
    # set as purge_tags == False
    if name:
        if purge_tags and tags is None:
            purge_tags = False
        tags = tags or {}
        tags.update({"Name": name})

    if tags is None:
        return False

    changed = ensure_ec2_tags(connection, module, vpc_id, tags=tags, purge_tags=purge_tags)
    if not changed or module.check_mode:
        return changed

    return True


def update_dhcp_opts(connection, module: AnsibleAWSModule, vpc_obj: Dict[str, Any], dhcp_id: Optional[str]) -> bool:
    if dhcp_id is None:
        return False
    if vpc_obj["DhcpOptionsId"] == dhcp_id:
        return False
    if module.check_mode:
        return True

    return associate_dhcp_options(connection, vpc_id=vpc_obj["VpcId"], dhcp_options_id=dhcp_id)


def create_vpc_net(
    connection,
    module: AnsibleAWSModule,
    cidr_block: List[str],
    tenancy,
    tags: Dict[str, str],
    ipv6_cidr: bool,
    name: Optional[str],
) -> Dict[str, Any]:
    if module.check_mode:
        module.exit_json(changed=True, msg="VPC would be created if not in check mode")

    create_args = dict(
        CidrBlock=cidr_block,
        InstanceTenancy=tenancy,
    )

    if name:
        tags = tags or {}
        tags["Name"] = name
    if tags:
        create_args["TagSpecifications"] = boto3_tag_specifications(tags, "vpc")

    # Defaults to False (including None)
    if ipv6_cidr:
        create_args["AmazonProvidedIpv6CidrBlock"] = True

    vpc_obj = create_vpc(connection, **create_args)

    # Wait up to 30 seconds for vpc to exist and for state 'available'
    for waiter_name in ("vpc_exists", "vpc_available"):
        wait_for_resource_state(connection, module, waiter_name, max_attempts=30, VpcIds=[vpc_obj["VpcId"]])

    return vpc_obj


def wait_for_vpc_attribute(connection, module, vpc_id, attribute, expected_value):
    if expected_value is None:
        return
    if module.check_mode:
        return

    start_time = time()
    updated = False
    while time() < start_time + 300:
        current_value = describe_vpc_attribute(connection, attribute=attribute, vpc_id=vpc_id)[
            f"{attribute[0].upper()}{attribute[1:]}"
        ]["Value"]
        if current_value != expected_value:
            sleep(3)
        else:
            updated = True
            break
    if not updated:
        module.fail_json(msg=f"Failed to wait for {attribute} to be updated")


def wait_for_vpc_ipv6_state(module, connection, vpc_id, ipv6_assoc_state):
    """
    If ipv6_assoc_state is True, wait for VPC to be associated with at least one Amazon-provided IPv6 CIDR block.
    If ipv6_assoc_state is False, wait for VPC to be dissociated from all Amazon-provided IPv6 CIDR blocks.
    """

    if ipv6_assoc_state is None:
        return
    if module.check_mode:
        return

    start_time = time()
    criteria_match = False
    while time() < start_time + 300:
        current_value = get_vpc(module, connection, vpc_id)
        if current_value:
            ipv6_set = current_value.get("Ipv6CidrBlockAssociationSet")
            # "ipv6_cidr": false and no Ipv6CidrBlockAssociationSet
            if not ipv6_set and not ipv6_assoc_state:
                return
            if ipv6_set:
                if ipv6_assoc_state:
                    # At least one 'Amazon' IPv6 CIDR block must be associated.
                    for val in ipv6_set:
                        if (
                            val.get("Ipv6Pool") == "Amazon"
                            and val.get("Ipv6CidrBlockState").get("State") == "associated"
                        ):
                            criteria_match = True
                            break
                    if criteria_match:
                        break
                else:
                    # All 'Amazon' IPv6 CIDR blocks must be disassociated.
                    expected_count = sum([(val.get("Ipv6Pool") == "Amazon") for val in ipv6_set])
                    actual_count = sum(
                        [
                            (
                                val.get("Ipv6Pool") == "Amazon"
                                and val.get("Ipv6CidrBlockState").get("State") == "disassociated"
                            )
                            for val in ipv6_set
                        ]
                    )
                    if actual_count == expected_count:
                        criteria_match = True
                        break
        sleep(3)
    if not criteria_match:
        module.fail_json(msg="Failed to wait for IPv6 CIDR association")


def get_cidr_network_bits(module, cidr_block):
    if cidr_block is None:
        return None

    fixed_cidrs = []
    for cidr in cidr_block:
        split_addr = cidr.split("/")
        if len(split_addr) == 2:
            # this_ip is a IPv4 CIDR that may or may not have host bits set
            # Get the network bits.
            valid_cidr = to_subnet(split_addr[0], split_addr[1])
            if cidr != valid_cidr:
                module.warn(
                    f"One of your CIDR addresses ({cidr}) has host bits set. To get rid of this warning, check the"
                    f" network mask and make sure that only network bits are set: {valid_cidr}."
                )
            fixed_cidrs.append(valid_cidr)
        else:
            # let AWS handle invalid CIDRs
            fixed_cidrs.append(cidr)
    return fixed_cidrs


def update_ipv6_cidrs(connection, module, vpc_obj, vpc_id, ipv6_cidr):
    if ipv6_cidr is None:
        return False

    # Fetch current state from vpc_object
    current_ipv6_cidr = False
    if "Ipv6CidrBlockAssociationSet" in vpc_obj.keys():
        for ipv6_assoc in vpc_obj["Ipv6CidrBlockAssociationSet"]:
            if ipv6_assoc["Ipv6Pool"] == "Amazon" and ipv6_assoc["Ipv6CidrBlockState"]["State"] in [
                "associated",
                "associating",
            ]:
                current_ipv6_cidr = True
                break

    if ipv6_cidr == current_ipv6_cidr:
        return False

    if module.check_mode:
        return True

    # There's no block associated, and we want one to be associated
    if ipv6_cidr:
        associate_vpc_cidr_block(connection, vpc_id=vpc_id, AmazonProvidedIpv6CidrBlock=ipv6_cidr)
    else:
        for ipv6_assoc in vpc_obj["Ipv6CidrBlockAssociationSet"]:
            if ipv6_assoc["Ipv6Pool"] == "Amazon" and ipv6_assoc["Ipv6CidrBlockState"]["State"] in [
                "associated",
                "associating",
            ]:
                disassociate_vpc_cidr_block(connection, association_id=ipv6_assoc["AssociationId"])
    return True


def update_cidrs(connection, module, vpc_obj, cidr_block, purge_cidrs):
    if not cidr_block:
        return False, None

    associated_cidrs = dict(
        (cidr["CidrBlock"], cidr["AssociationId"])
        for cidr in vpc_obj.get("CidrBlockAssociationSet", [])
        if cidr["CidrBlockState"]["State"] not in ["disassociating", "disassociated"]
    )

    current_cidrs = set(associated_cidrs.keys())
    desired_cidrs = set(cidr_block)
    if not purge_cidrs:
        desired_cidrs = desired_cidrs.union(current_cidrs)

    cidrs_to_add = list(desired_cidrs.difference(current_cidrs))
    cidrs_to_remove = list(current_cidrs.difference(desired_cidrs))

    if not cidrs_to_add and not cidrs_to_remove:
        return False, None

    if not module.check_mode:
        for cidr in cidrs_to_add:
            try:
                associate_vpc_cidr_block(connection, vpc_id=vpc_obj["VpcId"], CidrBlock=cidr)
            except AnsibleEC2Error as e:
                module.fail_json_aws(e, f"Unable to associate CIDR {cidr}.")

        for cidr in cidrs_to_remove:
            try:
                disassociate_vpc_cidr_block(connection, associated_cidrs[cidr])
            except AnsibleEC2Error as e:
                module.fail_json_aws(
                    e,
                    (
                        f"Unable to disassociate {associated_cidrs[cidr]}. You must detach or delete all gateways and resources"
                        " that are associated with the CIDR block before you can disassociate it."
                    ),
                )
    return True, list(desired_cidrs)


def update_dns_enabled(connection, module, vpc_id, dns_support):
    if dns_support is None:
        return False

    current_dns_enabled = describe_vpc_attribute(connection, attribute="enableDnsSupport", vpc_id=vpc_id)[
        "EnableDnsSupport"
    ]["Value"]
    if current_dns_enabled == dns_support:
        return False

    if module.check_mode:
        return True

    modify_vpc_attribute(connection, vpc_id=vpc_id, EnableDnsSupport={"Value": dns_support})
    return True


def update_dns_hostnames(connection, module, vpc_id, dns_hostnames):
    if dns_hostnames is None:
        return False

    current_dns_hostnames = describe_vpc_attribute(connection, attribute="enableDnsHostnames", vpc_id=vpc_id)[
        "EnableDnsHostnames"
    ]["Value"]
    if current_dns_hostnames == dns_hostnames:
        return False

    if module.check_mode:
        return True

    modify_vpc_attribute(connection, vpc_id=vpc_id, EnableDnsHostnames={"Value": dns_hostnames})
    return True


def wait_for_updates(connection, module, vpc_id, ipv6_cidr, expected_cidrs, dns_support, dns_hostnames, tags, dhcp_id):
    if module.check_mode:
        return

    if expected_cidrs:
        wait_for_resource_state(
            connection,
            module,
            "vpc_available",
            VpcIds=[vpc_id],
            Filters=[{"Name": "cidr-block-association.cidr-block", "Values": expected_cidrs}],
        )
    wait_for_vpc_ipv6_state(module, connection, vpc_id, ipv6_cidr)

    if tags is not None:
        tag_list = ansible_dict_to_boto3_tag_list(tags)
        filters = [{"Name": f"tag:{t['Key']}", "Values": [t["Value"]]} for t in tag_list]
        wait_for_resource_state(connection, module, "vpc_available", VpcIds=[vpc_id], Filters=filters)

    wait_for_vpc_attribute(connection, module, vpc_id, "enableDnsSupport", dns_support)
    wait_for_vpc_attribute(connection, module, vpc_id, "enableDnsHostnames", dns_hostnames)

    if dhcp_id is not None:
        # Wait for DhcpOptionsId to be updated
        filters = [{"Name": "dhcp-options-id", "Values": [dhcp_id]}]
        wait_for_resource_state(connection, module, "vpc_available", VpcIds=[vpc_id], Filters=filters)

    return


def ensure_present(connection, module: AnsibleAWSModule, vpc_id: Optional[str]) -> None:
    name = module.params.get("name")
    cidr_block = module.params.get("cidr_block")
    ipv6_cidr = module.params.get("ipv6_cidr")
    purge_cidrs = module.params.get("purge_cidrs")
    tenancy = module.params.get("tenancy")
    dns_support = module.params.get("dns_support")
    dns_hostnames = module.params.get("dns_hostnames")
    dhcp_id = module.params.get("dhcp_opts_id")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")

    if not vpc_id:
        if not name:
            module.fail_json("The name parameter must be specified when creating a new VPC.")
        vpc_obj = create_vpc_net(connection, module, cidr_block[0], tenancy, tags, ipv6_cidr, name)
        vpc_id = vpc_obj["VpcId"]
        changed = True
        # Set on-creation defaults
        if dns_hostnames is None:
            dns_hostnames = True
        if dns_support is None:
            dns_support = True
    else:
        changed = False
        vpc_obj = get_vpc(module, connection, vpc_id)
        changed |= update_ipv6_cidrs(connection, module, vpc_obj, vpc_id, ipv6_cidr)
        changed |= update_vpc_tags(connection, module, vpc_id, tags, name, purge_tags)

    cidrs_changed, desired_cidrs = update_cidrs(connection, module, vpc_obj, cidr_block, purge_cidrs)
    changed |= cidrs_changed
    changed |= update_dhcp_opts(connection, module, vpc_obj, dhcp_id)
    changed |= update_dns_enabled(connection, module, vpc_id, dns_support)
    changed |= update_dns_hostnames(connection, module, vpc_id, dns_hostnames)

    wait_for_updates(connection, module, vpc_id, ipv6_cidr, desired_cidrs, dns_support, dns_hostnames, tags, dhcp_id)

    updated_obj = get_vpc(module, connection, vpc_id)
    final_state = camel_dict_to_snake_dict(updated_obj)
    final_state["tags"] = boto3_tag_list_to_ansible_dict(updated_obj.get("Tags", []))
    final_state["name"] = final_state["tags"].get("Name", None)
    final_state["id"] = final_state.pop("vpc_id")

    module.exit_json(changed=changed, vpc=final_state)


def ensure_absent(connection, module: AnsibleAWSModule, vpc_id: str) -> None:
    changed = False
    if vpc_id:
        if module.check_mode:
            changed = True
        else:
            changed = delete_vpc(connection, vpc_id=vpc_id)
    module.exit_json(changed=changed, vpc={})


def main():
    argument_spec = dict(
        name=dict(required=False),
        vpc_id=dict(type="str", required=False, default=None),
        cidr_block=dict(type="list", elements="str"),
        ipv6_cidr=dict(type="bool", default=None),
        tenancy=dict(choices=["default", "dedicated"], default="default"),
        dns_support=dict(type="bool"),
        dns_hostnames=dict(type="bool"),
        dhcp_opts_id=dict(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        state=dict(choices=["present", "absent"], default="present"),
        multi_ok=dict(type="bool", default=False),
        purge_cidrs=dict(type="bool", default=False),
    )
    required_one_of = [
        ["vpc_id", "name"],
        ["vpc_id", "cidr_block"],
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_one_of=required_one_of, supports_check_mode=True)

    dns_support = module.params.get("dns_support")
    dns_hostnames = module.params.get("dns_hostnames")
    state = module.params.get("state")

    if dns_hostnames and not dns_support:
        module.fail_json(msg="In order to enable DNS Hostnames you must also enable DNS support")

    connection = module.client("ec2")
    try:
        vpc_id = module.params.get("vpc_id") or get_vpc_id(connection, module)
        if state == "present":
            ensure_present(connection, module, vpc_id)
        else:
            ensure_absent(connection, module, vpc_id)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

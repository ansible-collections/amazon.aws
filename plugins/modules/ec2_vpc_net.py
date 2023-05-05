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
      - The name to give your VPC. This is used in combination with I(cidr_block)
        to determine if a VPC already exists.
      - The value of I(name) overrides any value set for C(Name) in the I(tags)
        parameter.
      - At least one of I(name) and I(vpc_id) must be specified.
      - I(name) must be specified when creating a new VPC.
    type: str
  vpc_id:
    version_added: 4.0.0
    description:
      - The ID of the VPC.
      - At least one of I(name) and I(vpc_id) must be specified.
      - At least one of I(name) and I(cidr_block) must be specified.
    type: str
  cidr_block:
    description:
      - The primary CIDR of the VPC.
      - The first in the list will be used as the primary CIDR
        and is used in conjunction with I(name) to ensure idempotence.
      - Required when I(vpc_id) is not set.
    type: list
    elements: str
  ipv6_cidr:
    description:
      - Request an Amazon-provided IPv6 CIDR block with /56 prefix length. You cannot specify the range of IPv6 addresses,
        or the size of the CIDR block.
      - Default value is C(false) when creating a new VPC.
    type: bool
  purge_cidrs:
    description:
      - Remove CIDRs that are associated with the VPC and are not specified in I(cidr_block).
    default: false
    type: bool
  tenancy:
    description:
      - Whether to be default or dedicated tenancy.
      - This cannot be changed after the VPC has been created.
    default: default
    choices: [ 'default', 'dedicated' ]
    type: str
  dns_support:
    description:
      - Whether to enable AWS DNS support.
      - Default value is C(true) when creating a new VPC.
    type: bool
  dns_hostnames:
    description:
      - Whether to enable AWS hostname support.
      - Default value is C(true) when creating a new VPC.
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
        Specify I(multi_ok=true) if you want duplicate VPCs created.
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
    ipv6_cidr: True
    region: us-east-1
    tenancy: dedicated
"""

RETURN = r"""
vpc:
  description: info about the VPC that was created or deleted
  returned: always
  type: complex
  contains:
    cidr_block:
      description: The CIDR of the VPC
      returned: always
      type: str
      sample: 10.0.0.0/16
    cidr_block_association_set:
      description: IPv4 CIDR blocks associated with the VPC
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
      description: the id of the DHCP options associated with this VPC
      returned: always
      type: str
      sample: dopt-12345678
    id:
      description: VPC resource id
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
      description: indicates whether VPC uses default or dedicated tenancy
      returned: always
      type: str
      sample: default
    ipv6_cidr_block_association_set:
      description: IPv6 CIDR blocks associated with the VPC
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
      description: indicates whether this is the default VPC
      returned: always
      type: bool
      sample: false
    state:
      description: state of the VPC
      returned: always
      type: str
      sample: available
    tags:
      description: tags attached to the VPC, includes name
      returned: always
      type: complex
      contains:
        Name:
          description: name tag for the VPC
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

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.network import to_subnet
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


def vpc_exists(module, vpc, name, cidr_block, multi):
    """Returns None or a vpc object depending on the existence of a VPC. When supplied
    with a CIDR, it will check for matching tags to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return None.
    """
    try:
        vpc_filters = ansible_dict_to_boto3_filter_list({"tag:Name": name, "cidr-block": cidr_block})
        matching_vpcs = vpc.describe_vpcs(aws_retry=True, Filters=vpc_filters)["Vpcs"]
        # If an exact matching using a list of CIDRs isn't found, check for a match with the first CIDR as is documented for C(cidr_block)
        if not matching_vpcs:
            vpc_filters = ansible_dict_to_boto3_filter_list({"tag:Name": name, "cidr-block": [cidr_block[0]]})
            matching_vpcs = vpc.describe_vpcs(aws_retry=True, Filters=vpc_filters)["Vpcs"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")

    if multi:
        return None
    elif len(matching_vpcs) == 1:
        return matching_vpcs[0]["VpcId"]
    elif len(matching_vpcs) > 1:
        module.fail_json(
            msg=(
                f"Currently there are {len(matching_vpcs)} VPCs that have the same name and CIDR block you specified."
                " If you would like to create the VPC anyway please pass True to the multi_ok param."
            )
        )
    return None


def wait_for_vpc_to_exist(module, connection, **params):
    # wait for vpc to be available
    try:
        get_waiter(connection, "vpc_exists").wait(**params)
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="VPC failed to reach expected state (exists)")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to wait for VPC creation.")


def wait_for_vpc(module, connection, **params):
    # wait for vpc to be available
    try:
        get_waiter(connection, "vpc_available").wait(**params)
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="VPC failed to reach expected state (available)")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to wait for VPC state to update.")


def get_vpc(module, connection, vpc_id, wait=True):
    wait_for_vpc(module, connection, VpcIds=[vpc_id])
    try:
        vpc_obj = connection.describe_vpcs(VpcIds=[vpc_id], aws_retry=True)["Vpcs"][0]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")

    return vpc_obj


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


def update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
    if dhcp_id is None:
        return False
    if vpc_obj["DhcpOptionsId"] == dhcp_id:
        return False
    if module.check_mode:
        return True

    try:
        connection.associate_dhcp_options(DhcpOptionsId=dhcp_id, VpcId=vpc_obj["VpcId"], aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to associate DhcpOptionsId {dhcp_id}")

    return True


def create_vpc(connection, module, cidr_block, tenancy, tags, ipv6_cidr, name):
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

    try:
        vpc_obj = connection.create_vpc(aws_retry=True, **create_args)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to create the VPC")

    # wait up to 30 seconds for vpc to exist
    wait_for_vpc_to_exist(
        module,
        connection,
        VpcIds=[vpc_obj["Vpc"]["VpcId"]],
        WaiterConfig=dict(MaxAttempts=30),
    )
    # Wait for the VPC to enter an 'Available' State
    wait_for_vpc(
        module,
        connection,
        VpcIds=[vpc_obj["Vpc"]["VpcId"]],
        WaiterConfig=dict(MaxAttempts=30),
    )

    return vpc_obj["Vpc"]["VpcId"]


def wait_for_vpc_attribute(connection, module, vpc_id, attribute, expected_value):
    if expected_value is None:
        return
    if module.check_mode:
        return

    start_time = time()
    updated = False
    while time() < start_time + 300:
        current_value = connection.describe_vpc_attribute(Attribute=attribute, VpcId=vpc_id, aws_retry=True)[
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
        try:
            connection.associate_vpc_cidr_block(AmazonProvidedIpv6CidrBlock=ipv6_cidr, VpcId=vpc_id, aws_retry=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, "Unable to associate IPv6 CIDR")
    else:
        for ipv6_assoc in vpc_obj["Ipv6CidrBlockAssociationSet"]:
            if ipv6_assoc["Ipv6Pool"] == "Amazon" and ipv6_assoc["Ipv6CidrBlockState"]["State"] in [
                "associated",
                "associating",
            ]:
                try:
                    connection.disassociate_vpc_cidr_block(AssociationId=ipv6_assoc["AssociationId"], aws_retry=True)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, f"Unable to disassociate IPv6 CIDR {ipv6_assoc['AssociationId']}.")
    return True


def update_cidrs(connection, module, vpc_obj, vpc_id, cidr_block, purge_cidrs):
    if cidr_block is None:
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

    if module.check_mode:
        return True, list(desired_cidrs)

    for cidr in cidrs_to_add:
        try:
            connection.associate_vpc_cidr_block(CidrBlock=cidr, VpcId=vpc_id, aws_retry=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, f"Unable to associate CIDR {cidr}.")

    for cidr in cidrs_to_remove:
        association_id = associated_cidrs[cidr]
        try:
            connection.disassociate_vpc_cidr_block(AssociationId=association_id, aws_retry=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(
                e,
                (
                    f"Unable to disassociate {association_id}. You must detach or delete all gateways and resources"
                    " that are associated with the CIDR block before you can disassociate it."
                ),
            )
    return True, list(desired_cidrs)


def update_dns_enabled(connection, module, vpc_id, dns_support):
    if dns_support is None:
        return False

    current_dns_enabled = connection.describe_vpc_attribute(Attribute="enableDnsSupport", VpcId=vpc_id, aws_retry=True)[
        "EnableDnsSupport"
    ]["Value"]
    if current_dns_enabled == dns_support:
        return False

    if module.check_mode:
        return True

    try:
        connection.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": dns_support}, aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to update enabled dns support attribute")
    return True


def update_dns_hostnames(connection, module, vpc_id, dns_hostnames):
    if dns_hostnames is None:
        return False

    current_dns_hostnames = connection.describe_vpc_attribute(
        Attribute="enableDnsHostnames", VpcId=vpc_id, aws_retry=True
    )["EnableDnsHostnames"]["Value"]
    if current_dns_hostnames == dns_hostnames:
        return False

    if module.check_mode:
        return True

    try:
        connection.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": dns_hostnames}, aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to update enabled dns hostnames attribute")
    return True


def delete_vpc(connection, module, vpc_id):
    if vpc_id is None:
        return False
    if module.check_mode:
        return True

    try:
        connection.delete_vpc(VpcId=vpc_id, aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e,
            msg=(
                f"Failed to delete VPC {vpc_id} You may want to use the ec2_vpc_subnet, ec2_vpc_igw, and/or"
                " ec2_vpc_route_table modules to ensure that all depenednt components are absent."
            ),
        )

    return True


def wait_for_updates(connection, module, vpc_id, ipv6_cidr, expected_cidrs, dns_support, dns_hostnames, tags, dhcp_id):
    if module.check_mode:
        return

    if expected_cidrs:
        wait_for_vpc(
            module,
            connection,
            VpcIds=[vpc_id],
            Filters=[{"Name": "cidr-block-association.cidr-block", "Values": expected_cidrs}],
        )
    wait_for_vpc_ipv6_state(module, connection, vpc_id, ipv6_cidr)

    if tags is not None:
        tag_list = ansible_dict_to_boto3_tag_list(tags)
        filters = [{"Name": f"tag:{t['Key']}", "Values": [t["Value"]]} for t in tag_list]
        wait_for_vpc(module, connection, VpcIds=[vpc_id], Filters=filters)

    wait_for_vpc_attribute(connection, module, vpc_id, "enableDnsSupport", dns_support)
    wait_for_vpc_attribute(connection, module, vpc_id, "enableDnsHostnames", dns_hostnames)

    if dhcp_id is not None:
        # Wait for DhcpOptionsId to be updated
        filters = [{"Name": "dhcp-options-id", "Values": [dhcp_id]}]
        wait_for_vpc(module, connection, VpcIds=[vpc_id], Filters=filters)

    return


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

    name = module.params.get("name")
    vpc_id = module.params.get("vpc_id")
    cidr_block = module.params.get("cidr_block")
    ipv6_cidr = module.params.get("ipv6_cidr")
    purge_cidrs = module.params.get("purge_cidrs")
    tenancy = module.params.get("tenancy")
    dns_support = module.params.get("dns_support")
    dns_hostnames = module.params.get("dns_hostnames")
    dhcp_id = module.params.get("dhcp_opts_id")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    state = module.params.get("state")
    multi = module.params.get("multi_ok")

    changed = False

    connection = module.client(
        "ec2",
        retry_decorator=AWSRetry.jittered_backoff(
            retries=8, delay=3, catch_extra_error_codes=["InvalidVpcID.NotFound"]
        ),
    )

    if dns_hostnames and not dns_support:
        module.fail_json(msg="In order to enable DNS Hostnames you must also enable DNS support")

    cidr_block = get_cidr_network_bits(module, module.params.get("cidr_block"))

    if vpc_id is None:
        vpc_id = vpc_exists(module, connection, name, cidr_block, multi)

    if state == "present":
        # Check if VPC exists
        if vpc_id is None:
            if module.params.get("name") is None:
                module.fail_json("The name parameter must be specified when creating a new VPC.")
            vpc_id = create_vpc(connection, module, cidr_block[0], tenancy, tags, ipv6_cidr, name)
            changed = True
            vpc_obj = get_vpc(module, connection, vpc_id)
            if len(cidr_block) > 1:
                cidrs_changed, desired_cidrs = update_cidrs(
                    connection, module, vpc_obj, vpc_id, cidr_block, purge_cidrs
                )
                changed |= cidrs_changed
            else:
                desired_cidrs = None
            # Set on-creation defaults
            if dns_hostnames is None:
                dns_hostnames = True
            if dns_support is None:
                dns_support = True
        else:
            vpc_obj = get_vpc(module, connection, vpc_id)
            cidrs_changed, desired_cidrs = update_cidrs(connection, module, vpc_obj, vpc_id, cidr_block, purge_cidrs)
            changed |= cidrs_changed
            ipv6_changed = update_ipv6_cidrs(connection, module, vpc_obj, vpc_id, ipv6_cidr)
            changed |= ipv6_changed
            tags_changed = update_vpc_tags(connection, module, vpc_id, tags, name, purge_tags)
            changed |= tags_changed

        dhcp_changed = update_dhcp_opts(connection, module, vpc_obj, dhcp_id)
        changed |= dhcp_changed
        dns_changed = update_dns_enabled(connection, module, vpc_id, dns_support)
        changed |= dns_changed
        hostnames_changed = update_dns_hostnames(connection, module, vpc_id, dns_hostnames)
        changed |= hostnames_changed

        wait_for_updates(
            connection, module, vpc_id, ipv6_cidr, desired_cidrs, dns_support, dns_hostnames, tags, dhcp_id
        )

        updated_obj = get_vpc(module, connection, vpc_id)
        final_state = camel_dict_to_snake_dict(updated_obj)
        final_state["tags"] = boto3_tag_list_to_ansible_dict(updated_obj.get("Tags", []))
        final_state["name"] = final_state["tags"].get("Name", None)
        final_state["id"] = final_state.pop("vpc_id")

        module.exit_json(changed=changed, vpc=final_state)

    elif state == "absent":
        changed = delete_vpc(connection, module, vpc_id)
        module.exit_json(changed=changed, vpc={})


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_subnet
version_added: 1.0.0
short_description: Manage subnets in AWS virtual private clouds
description:
  - Manage subnets in AWS virtual private clouds.
author:
  - Robert Estelle (@erydo)
  - Brad Davidson (@brandond)
options:
  az:
    description:
      - The availability zone for the subnet.
      - Required if O(outpost_arn) is set.
    type: str
  cidr:
    description:
      - The CIDR block for the subnet. E.g. V(192.0.2.0/24).
    type: str
    required: true
  ipv6_cidr:
    description:
      - The IPv6 CIDR block for the subnet.
      - The VPC must have a /56 block assigned and this value must be a valid IPv6 /64 that falls in the VPC range.
      - Required if O(assign_instances_ipv6=true)
    type: str
    default: ''
  outpost_arn:
    description:
      - The Amazon Resource Name (ARN) of the Outpost.
      - If set, allows to create subnet in an Outpost.
      - If O(outpost_arn) is set, O(az) must also be specified.
    type: str
    default: ''
  state:
    description:
      - Create or remove the subnet.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  vpc_id:
    description:
      -"VPC ID of the VPC in which to create or delete the subnet.
    required: true
    type: str
  map_public:
    description:
      - Whether instances launched into the subnet should default to being assigned public IP address.
    type: bool
    default: false
  assign_instances_ipv6:
    description:
      - Whether instances launched into the subnet should default to being automatically assigned an IPv6 address.
      - If O(assign_instances_ipv6=true), O(ipv6_cidr) must also be specified.
    type: bool
    default: false
  wait:
    description:
      - Whether to wait for changes to complete.
    type: bool
    default: true
  wait_timeout:
    description:
      - Number of seconds to wait for changes to complete
      - Ignored unless O(wait=true).
    default: 300
    type: int
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create subnet for database servers
  amazon.aws.ec2_vpc_subnet:
    state: present
    vpc_id: vpc-123456
    cidr: 10.0.1.16/28
    tags:
      Name: Database Subnet
  register: database_subnet

- name: Remove subnet for database servers
  amazon.aws.ec2_vpc_subnet:
    state: absent
    vpc_id: vpc-123456
    cidr: 10.0.1.16/28

- name: Create subnet with IPv6 block assigned
  amazon.aws.ec2_vpc_subnet:
    state: present
    vpc_id: vpc-123456
    cidr: 10.1.100.0/24
    ipv6_cidr: 2001:db8:0:102::/64

- name: Remove IPv6 block assigned to subnet
  amazon.aws.ec2_vpc_subnet:
    state: present
    vpc_id: vpc-123456
    cidr: 10.1.100.0/24
    ipv6_cidr: ''
"""

RETURN = r"""
subnet:
    description: Dictionary of subnet values.
    returned: O(state=present)
    type: complex
    contains:
        id:
            description: Subnet resource id.
            returned: O(state=present)
            type: str
            sample: subnet-b883b2c4
        cidr_block:
            description: The IPv4 CIDR of the Subnet.
            returned: O(state=present)
            type: str
            sample: "10.0.0.0/16"
        ipv6_cidr_block:
            description: The IPv6 CIDR block actively associated with the Subnet.
            returned: O(state=present)
            type: str
            sample: "2001:db8:0:102::/64"
        availability_zone:
            description: Availability zone of the Subnet.
            returned: O(state=present)
            type: str
            sample: us-east-1a
        availability_zone_id:
            description: The AZ ID of the subnet.
            returned: O(state=present)
            type: str
            sample: use1-az6
        state:
            description: State of the Subnet.
            returned: O(state=present)
            type: str
            sample: available
        tags:
            description: Tags attached to the Subnet, includes name.
            returned: O(state=present)
            type: dict
            sample: {"Name": "My Subnet", "env": "staging"}
        map_public_ip_on_launch:
            description: Whether public IP is auto-assigned to new instances.
            returned: O(state=present)
            type: bool
            sample: false
        assign_ipv6_address_on_creation:
            description: Whether IPv6 address is auto-assigned to new instances.
            returned: O(state=present)
            type: bool
            sample: false
        vpc_id:
            description: The id of the VPC where this Subnet exists.
            returned: O(state=present)
            type: str
            sample: vpc-67236184
        available_ip_address_count:
            description: Number of available IPv4 addresses.
            returned: O(state=present)
            type: str
            sample: 251
        default_for_az:
            description: Indicates whether this is the default Subnet for this Availability Zone.
            returned: O(state=present)
            type: bool
            sample: false
        enable_dns64:
            description:
            - Indicates whether DNS queries made should return synthetic IPv6 addresses for IPv4-only destinations.
            type: bool
            sample: false
        ipv6_association_id:
            description: The IPv6 association ID for the currently associated CIDR.
            returned: O(state=present)
            type: str
            sample: subnet-cidr-assoc-b85c74d2
        ipv6_native:
            description: Indicates whether this is an IPv6 only subnet.
            type: bool
            sample: false
        ipv6_cidr_block_association_set:
            description: An array of IPv6 cidr block association set information.
            returned: O(state=present)
            type: complex
            contains:
                association_id:
                    description: The association ID.
                    returned: always
                    type: str
                ipv6_cidr_block:
                    description: The IPv6 CIDR block that is associated with the subnet.
                    returned: always
                    type: str
                ipv6_cidr_block_state:
                    description: A hash/dict that contains a single item. The state of the cidr block association.
                    returned: always
                    type: dict
                    contains:
                        state:
                            description: The CIDR block association state.
                            returned: always
                            type: str
        map_customer_owned_ip_on_launch:
            description:
            - Indicates whether a network interface receives a customer-owned IPv4 address.
            type: bool
            sample: flase
        owner_id:
            description: The ID of the Amazon Web Services account that owns the subnet.
            type: str
            sample: 12344567
        private_dns_name_options_on_launch:
            description:
            - The type of hostnames to assign to instances in the subnet at launch.
            - An instance hostname is based on the IPv4 address or ID of the instance.
            type: dict
            sample: {
                "enable_resource_name_dns_a_record": false,
                "enable_resource_name_dns_aaaa_record": false,
                "hostname_type": "ip-name"
            }
        subnet_arn:
            description: The Amazon Resource Name (ARN) of the subnet.
            type: str
            sample: arn:aws:ec2:us-east-1:xxx:subnet/subnet-xxx

"""


import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.arn import is_outpost_arn
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import associate_subnet_cidr_block
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_subnet
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_subnet
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_subnets
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import disassociate_subnet_cidr_block
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_subnet_attribute
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_tag_filter_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def get_subnet_info(subnet: Dict[str, Any]) -> Dict[str, Any]:
    subnet = camel_dict_to_snake_dict(subnet)
    if "tags" in subnet:
        subnet["tags"] = boto3_tag_list_to_ansible_dict(subnet["tags"])
    else:
        subnet["tags"] = dict()

    if "subnet_id" in subnet:
        subnet["id"] = subnet["subnet_id"]
        del subnet["subnet_id"]

    subnet["ipv6_cidr_block"] = ""
    subnet["ipv6_association_id"] = ""
    ipv6set = subnet.get("ipv6_cidr_block_association_set")
    if ipv6set:
        for item in ipv6set:
            if item.get("ipv6_cidr_block_state", {}).get("state") in ("associated", "associating"):
                subnet["ipv6_cidr_block"] = item["ipv6_cidr_block"]
                subnet["ipv6_association_id"] = item["association_id"]

    return subnet


def wait_vpc_subnet_state(conn, module: AnsibleAWSModule, waiter_name: str, start_time: float, **params) -> None:
    max_attempts = int(module.params["wait_timeout"] + start_time - time.time())
    wait_for_resource_state(conn, module, waiter_name, delay=5, max_attempts=max_attempts, **params)


def create_vpc_subnet(
    connection,
    module: AnsibleAWSModule,
    start_time: float,
) -> Dict[str, Any]:
    vpc_id = module.params["vpc_id"]
    cidr = module.params["cidr"]
    tags = module.params["tags"]
    ipv6_cidr = module.params["ipv6_cidr"]
    outpost_arn = module.params["outpost_arn"]
    az = module.params["az"]
    wait = module.params["wait"]

    params = {"VpcId": vpc_id, "CidrBlock": cidr}

    if ipv6_cidr:
        params["Ipv6CidrBlock"] = ipv6_cidr
    if az:
        params["AvailabilityZone"] = az
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="subnet")
    if outpost_arn:
        if is_outpost_arn(outpost_arn):
            params["OutpostArn"] = outpost_arn
        else:
            module.fail_json("OutpostArn does not match the pattern specified in API specifications.")

    try:
        subnet = get_subnet_info(create_subnet(connection, **params))
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    # Sometimes AWS takes its time to create a subnet and so using
    # new subnets's id to do things like create tags results in
    # exception.
    if wait and subnet.get("state") != "available":
        wait_vpc_subnet_state(connection, module, "subnet_exists", start_time=start_time, SubnetIds=[subnet["id"]])
        wait_vpc_subnet_state(connection, module, "subnet_available", start_time=start_time, SubnetIds=[subnet["id"]])
        subnet["state"] = "available"

    return subnet


def disassociate_ipv6_cidr(conn, module: AnsibleAWSModule, subnet: Dict[str, Any], start_time: float):
    if subnet.get("assign_ipv6_address_on_creation"):
        try:
            modify_subnet_attribute(conn, subnet["id"], AssignIpv6AddressOnCreation={"Value": False})
        except AnsibleEC2Error as e:
            module.fail_json_aws_error(e)

    try:
        disassociate_subnet_cidr_block(conn, subnet["ipv6_association_id"])
    except AnsibleEC2Error as e:
        module.fail_json_aws(
            e,
            msg=f"Couldn't disassociate ipv6 cidr block id {subnet['ipv6_association_id']} from subnet {subnet['id']}",
        )

    # Wait for cidr block to be disassociated
    if module.params["wait"]:
        filters = ansible_dict_to_boto3_filter_list(
            {"ipv6-cidr-block-association.state": ["disassociated"], "vpc-id": subnet["vpc_id"]}
        )
        wait_vpc_subnet_state(
            conn, module, "subnet_exists", start_time=start_time, SubnetIds=[subnet["id"]], Filters=filters
        )


def ensure_ipv6_cidr_block(conn, module: AnsibleAWSModule, subnet: Dict[str, Any], start_time: float) -> bool:
    ipv6_cidr = module.params["ipv6_cidr"]
    wait = module.params["wait"]
    changed = False

    if subnet["ipv6_association_id"] and not ipv6_cidr:
        if not module.check_mode:
            disassociate_ipv6_cidr(conn, module, subnet, start_time)
        changed = True

    if ipv6_cidr:
        filters = ansible_dict_to_boto3_filter_list(
            {"ipv6-cidr-block-association.ipv6-cidr-block": ipv6_cidr, "vpc-id": subnet["vpc_id"]}
        )

        try:
            check_subnets = [get_subnet_info(x) for x in describe_subnets(client=conn, Filters=filters)]
        except AnsibleEC2Error as e:
            module.fail_json_aws_error(e)

        if check_subnets and check_subnets[0]["ipv6_cidr_block"]:
            module.fail_json(msg=f"The IPv6 CIDR '{ipv6_cidr}' conflicts with another subnet")

        if subnet["ipv6_association_id"]:
            if not module.check_mode:
                disassociate_ipv6_cidr(conn, module, subnet, start_time)
            changed = True

        try:
            if not module.check_mode:
                associate_resp = associate_subnet_cidr_block(conn, subnet_id=subnet["id"], Ipv6CidrBlock=ipv6_cidr)
            changed = True
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg=f"Couldn't associate ipv6 cidr {ipv6_cidr} to {subnet['id']}")
        else:
            if not module.check_mode and wait:
                filters = ansible_dict_to_boto3_filter_list(
                    {"ipv6-cidr-block-association.state": ["associated"], "vpc-id": subnet["vpc_id"]}
                )
                wait_vpc_subnet_state(
                    conn, module, "subnet_exists", start_time=start_time, SubnetIds=[subnet["id"]], Filters=filters
                )
        if not module.check_mode:
            if associate_resp.get("AssociationId"):
                subnet["ipv6_association_id"] = associate_resp["AssociationId"]
                subnet["ipv6_cidr_block"] = associate_resp["Ipv6CidrBlock"]
                if subnet["ipv6_cidr_block_association_set"]:
                    subnet["ipv6_cidr_block_association_set"][0] = camel_dict_to_snake_dict(associate_resp)
                else:
                    subnet["ipv6_cidr_block_association_set"].append(camel_dict_to_snake_dict(associate_resp))

    return changed


def _matching_subnet_filters(vpc_id: str, cidr: List[str]) -> Dict[str, Union[str, List[str]]]:
    return ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id, "cidr-block": cidr})


def get_matching_subnet(conn, module: AnsibleAWSModule, vpc_id: str, cidr: List[str]) -> Optional[Dict[str, Any]]:
    filters = _matching_subnet_filters(vpc_id, cidr)
    try:
        for subnet in describe_subnets(client=conn, Filters=filters):
            # The list contains only one subnet
            return get_subnet_info(subnet)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)
    return None


def update_subnet_attributes(
    conn, module: AnsibleAWSModule, subnet: Dict[str, Any], start_time: float
) -> Tuple[bool, Dict[str, Any]]:
    changed = False
    # Ensure IPv6 CIDR Block
    if module.params["ipv6_cidr"] != subnet.get("ipv6_cidr_block"):
        changed |= ensure_ipv6_cidr_block(conn, module, subnet, start_time)

    # Modify subnet attribute 'MapPublicIpOnLaunch'
    map_public = module.params["map_public"]
    if map_public != subnet.get("map_public_ip_on_launch"):
        changed = True
        if not module.check_mode:
            params = {"MapPublicIpOnLaunch": {"Value": map_public}}
            modify_subnet_attribute(conn, subnet["id"], **params)

    # Modify subnet attribute 'AssignIpv6AddressOnCreation'
    assign_instances_ipv6 = module.params["assign_instances_ipv6"]
    if assign_instances_ipv6 != subnet.get("assign_ipv6_address_on_creation"):
        changed = True
        if not module.check_mode:
            params = {"AssignIpv6AddressOnCreation": {"Value": assign_instances_ipv6}}
            modify_subnet_attribute(conn, subnet["id"], **params)

    # Ensure subnet tags
    tags_updated = ensure_ec2_tags(
        conn,
        module,
        subnet["id"],
        resource_type="subnet",
        purge_tags=module.params["purge_tags"],
        tags=module.params["tags"],
        retry_codes=["InvalidSubnetID.NotFound"],
    )
    if tags_updated:
        changed = True
        if module.params["wait"] and not module.check_mode:
            # Wait for tags to be updated
            filters = ansible_dict_to_boto3_filter_list(ansible_dict_to_tag_filter_dict(module.params["tags"]))
            wait_vpc_subnet_state(
                conn, module, "subnet_exists", start_time=start_time, SubnetIds=[subnet["id"]], Filters=filters
            )

    subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
    if not module.check_mode and module.params["wait"]:
        subnet_filter = _matching_subnet_filters(module.params["vpc_id"], module.params["cidr"])
        wait_vpc_subnet_state(
            conn, module, "subnet_exists", start_time=start_time, SubnetIds=[subnet["id"]], Filters=subnet_filter
        )
        subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
        if not subnet:
            module.fail_json("Failed to describe newly created subnet")
        # GET calls are not monotonic for map_public_ip_on_launch and assign_ipv6_address_on_creation
        # so we only wait for those if necessary just before returning the subnet
        subnet = ensure_final_subnet(conn, module, subnet, start_time)
    return changed, subnet


def ensure_subnet_present(conn, module: AnsibleAWSModule) -> Dict[str, Any]:
    subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
    changed = False

    # Initialize start so max time does not exceed the specified wait_timeout for multiple operations
    start_time = time.time()

    if subnet is None:
        if not module.check_mode:
            subnet = create_vpc_subnet(conn, module, start_time)
        changed = True
        # Subnet will be None when check_mode is true
        if subnet is None:
            return {"changed": changed, "subnet": {}}

    attribute_change, subnet = update_subnet_attributes(conn, module, subnet, start_time)
    return {"changed": changed or attribute_change, "subnet": subnet}


def ensure_final_subnet(conn, module: AnsibleAWSModule, subnet: Dict[str, Any], start_time: float) -> Dict[str, Any]:
    for _rewait in range(0, 30):
        map_public_correct = True
        assign_ipv6_correct = True

        if module.params["map_public"] != subnet["map_public_ip_on_launch"]:
            map_public_correct = False
            waiter_name = "subnet_has_map_public" if module.params["map_public"] else "subnet_no_map_public"
            wait_vpc_subnet_state(conn, module, waiter_name, start_time=start_time, SubnetIds=[subnet["id"]])

        if module.params["assign_instances_ipv6"] != subnet.get("assign_ipv6_address_on_creation"):
            assign_ipv6_correct = False
            waiter_name = (
                "subnet_has_assign_ipv6" if module.params["assign_instances_ipv6"] else "subnet_no_assign_ipv6"
            )
            wait_vpc_subnet_state(conn, module, waiter_name, start_time=start_time, SubnetIds=[subnet["id"]])

        if map_public_correct and assign_ipv6_correct:
            break

        time.sleep(5)
        subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"]) or {}

    return subnet


def ensure_subnet_absent(conn, module: AnsibleAWSModule) -> Dict[str, Any]:
    subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
    if subnet is None:
        return {"changed": False}

    try:
        changed = False
        if module.check_mode:
            changed = True
        else:
            changed = delete_subnet(conn, subnet["id"])
            if module.params["wait"]:
                wait_vpc_subnet_state(conn, module, "subnet_deleted", start_time=time.time(), SubnetIds=[subnet["id"]])
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)
    return {"changed": changed}


def main() -> None:
    argument_spec = dict(
        az=dict(default=None, required=False),
        cidr=dict(required=True),
        ipv6_cidr=dict(default="", required=False),
        outpost_arn=dict(default="", type="str", required=False),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        vpc_id=dict(required=True),
        map_public=dict(default=False, required=False, type="bool"),
        assign_instances_ipv6=dict(default=False, required=False, type="bool"),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=300, required=False),
        purge_tags=dict(default=True, type="bool"),
    )

    required_if = [("assign_instances_ipv6", True, ["ipv6_cidr"])]

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)

    if module.params.get("outpost_arn") and not module.params.get("az"):
        module.fail_json(msg="To specify OutpostArn, you must specify the Availability Zone of the Outpost subnet.")

    if module.params.get("assign_instances_ipv6") and not module.params.get("ipv6_cidr"):
        module.fail_json(msg="assign_instances_ipv6 is True but ipv6_cidr is None or an empty string")

    connection = module.client("ec2")

    state = module.params.get("state")

    try:
        if state == "present":
            result = ensure_subnet_present(connection, module)
        elif state == "absent":
            result = ensure_subnet_absent(connection, module)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    module.exit_json(**result)


if __name__ == "__main__":
    main()

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
      - Required if I(outpost_arn) is set.
    type: str
  cidr:
    description:
      - The CIDR block for the subnet. E.g. C(192.0.2.0/24).
    type: str
    required: true
  ipv6_cidr:
    description:
      - The IPv6 CIDR block for the subnet.
      - The VPC must have a /56 block assigned and this value must be a valid IPv6 /64 that falls in the VPC range.
      - Required if I(assign_instances_ipv6=true)
    type: str
    default: ''
  outpost_arn:
    description:
      - The Amazon Resource Name (ARN) of the Outpost.
      - If set, allows to create subnet in an Outpost.
      - If I(outpost_arn) is set, I(az) must also be specified.
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
      - If I(assign_instances_ipv6=true), I(ipv6_cidr) must also be specified.
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
      - Ignored unless I(wait=True).
    default: 300
    type: int
  tags:
    default: {}
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
    description: Dictionary of subnet values
    returned: I(state=present)
    type: complex
    contains:
        id:
            description: Subnet resource id
            returned: I(state=present)
            type: str
            sample: subnet-b883b2c4
        cidr_block:
            description: The IPv4 CIDR of the Subnet
            returned: I(state=present)
            type: str
            sample: "10.0.0.0/16"
        ipv6_cidr_block:
            description: The IPv6 CIDR block actively associated with the Subnet
            returned: I(state=present)
            type: str
            sample: "2001:db8:0:102::/64"
        availability_zone:
            description: Availability zone of the Subnet
            returned: I(state=present)
            type: str
            sample: us-east-1a
        state:
            description: state of the Subnet
            returned: I(state=present)
            type: str
            sample: available
        tags:
            description: tags attached to the Subnet, includes name
            returned: I(state=present)
            type: dict
            sample: {"Name": "My Subnet", "env": "staging"}
        map_public_ip_on_launch:
            description: whether public IP is auto-assigned to new instances
            returned: I(state=present)
            type: bool
            sample: false
        assign_ipv6_address_on_creation:
            description: whether IPv6 address is auto-assigned to new instances
            returned: I(state=present)
            type: bool
            sample: false
        vpc_id:
            description: the id of the VPC where this Subnet exists
            returned: I(state=present)
            type: str
            sample: vpc-67236184
        available_ip_address_count:
            description: number of available IPv4 addresses
            returned: I(state=present)
            type: str
            sample: 251
        default_for_az:
            description: indicates whether this is the default Subnet for this Availability Zone
            returned: I(state=present)
            type: bool
            sample: false
        ipv6_association_id:
            description: The IPv6 association ID for the currently associated CIDR
            returned: I(state=present)
            type: str
            sample: subnet-cidr-assoc-b85c74d2
        ipv6_cidr_block_association_set:
            description: An array of IPv6 cidr block association set information.
            returned: I(state=present)
            type: complex
            contains:
                association_id:
                    description: The association ID
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
"""


import time

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.arn import is_outpost_arn
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


def get_subnet_info(subnet):
    if "Subnets" in subnet:
        return [get_subnet_info(s) for s in subnet["Subnets"]]
    elif "Subnet" in subnet:
        subnet = camel_dict_to_snake_dict(subnet["Subnet"])
    else:
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


def waiter_params(module, params, start_time):
    remaining_wait_timeout = int(module.params["wait_timeout"] + start_time - time.time())
    params["WaiterConfig"] = {"Delay": 5, "MaxAttempts": remaining_wait_timeout // 5}
    return params


def handle_waiter(conn, module, waiter_name, params, start_time):
    try:
        get_waiter(conn, waiter_name).wait(**waiter_params(module, params, start_time))
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, "Failed to wait for updates to complete")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "An exception happened while trying to wait for updates")


def create_subnet(conn, module, vpc_id, cidr, ipv6_cidr=None, outpost_arn=None, az=None, start_time=None):
    wait = module.params["wait"]

    params = dict(VpcId=vpc_id, CidrBlock=cidr)

    if ipv6_cidr:
        params["Ipv6CidrBlock"] = ipv6_cidr

    if az:
        params["AvailabilityZone"] = az

    if outpost_arn:
        if is_outpost_arn(outpost_arn):
            params["OutpostArn"] = outpost_arn
        else:
            module.fail_json("OutpostArn does not match the pattern specified in API specifications.")

    try:
        subnet = get_subnet_info(conn.create_subnet(aws_retry=True, **params))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create subnet")

    # Sometimes AWS takes its time to create a subnet and so using
    # new subnets's id to do things like create tags results in
    # exception.
    if wait and subnet.get("state") != "available":
        handle_waiter(conn, module, "subnet_exists", {"SubnetIds": [subnet["id"]]}, start_time)
        handle_waiter(conn, module, "subnet_available", {"SubnetIds": [subnet["id"]]}, start_time)
        subnet["state"] = "available"

    return subnet


def ensure_tags(conn, module, subnet, tags, purge_tags, start_time):
    changed = ensure_ec2_tags(
        conn,
        module,
        subnet["id"],
        resource_type="subnet",
        purge_tags=purge_tags,
        tags=tags,
        retry_codes=["InvalidSubnetID.NotFound"],
    )

    if module.params["wait"] and not module.check_mode:
        # Wait for tags to be updated
        filters = [{"Name": f"tag:{k}", "Values": [v]} for k, v in tags.items()]
        handle_waiter(conn, module, "subnet_exists", {"SubnetIds": [subnet["id"]], "Filters": filters}, start_time)

    return changed


def ensure_map_public(conn, module, subnet, map_public, check_mode, start_time):
    if check_mode:
        return
    try:
        conn.modify_subnet_attribute(aws_retry=True, SubnetId=subnet["id"], MapPublicIpOnLaunch={"Value": map_public})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't modify subnet attribute")


def ensure_assign_ipv6_on_create(conn, module, subnet, assign_instances_ipv6, check_mode, start_time):
    if check_mode:
        return
    try:
        conn.modify_subnet_attribute(
            aws_retry=True, SubnetId=subnet["id"], AssignIpv6AddressOnCreation={"Value": assign_instances_ipv6}
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't modify subnet attribute")


def disassociate_ipv6_cidr(conn, module, subnet, start_time):
    if subnet.get("assign_ipv6_address_on_creation"):
        ensure_assign_ipv6_on_create(conn, module, subnet, False, False, start_time)

    try:
        conn.disassociate_subnet_cidr_block(aws_retry=True, AssociationId=subnet["ipv6_association_id"])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e,
            msg=f"Couldn't disassociate ipv6 cidr block id {subnet['ipv6_association_id']} from subnet {subnet['id']}",
        )

    # Wait for cidr block to be disassociated
    if module.params["wait"]:
        filters = ansible_dict_to_boto3_filter_list(
            {"ipv6-cidr-block-association.state": ["disassociated"], "vpc-id": subnet["vpc_id"]}
        )
        handle_waiter(conn, module, "subnet_exists", {"SubnetIds": [subnet["id"]], "Filters": filters}, start_time)


def ensure_ipv6_cidr_block(conn, module, subnet, ipv6_cidr, check_mode, start_time):
    wait = module.params["wait"]
    changed = False

    if subnet["ipv6_association_id"] and not ipv6_cidr:
        if not check_mode:
            disassociate_ipv6_cidr(conn, module, subnet, start_time)
        changed = True

    if ipv6_cidr:
        filters = ansible_dict_to_boto3_filter_list(
            {"ipv6-cidr-block-association.ipv6-cidr-block": ipv6_cidr, "vpc-id": subnet["vpc_id"]}
        )

        try:
            _subnets = conn.describe_subnets(aws_retry=True, Filters=filters)
            check_subnets = get_subnet_info(_subnets)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get subnet info")

        if check_subnets and check_subnets[0]["ipv6_cidr_block"]:
            module.fail_json(msg=f"The IPv6 CIDR '{ipv6_cidr}' conflicts with another subnet")

        if subnet["ipv6_association_id"]:
            if not check_mode:
                disassociate_ipv6_cidr(conn, module, subnet, start_time)
            changed = True

        try:
            if not check_mode:
                associate_resp = conn.associate_subnet_cidr_block(
                    aws_retry=True, SubnetId=subnet["id"], Ipv6CidrBlock=ipv6_cidr
                )
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't associate ipv6 cidr {ipv6_cidr} to {subnet['id']}")
        else:
            if not check_mode and wait:
                filters = ansible_dict_to_boto3_filter_list(
                    {"ipv6-cidr-block-association.state": ["associated"], "vpc-id": subnet["vpc_id"]}
                )
                handle_waiter(
                    conn, module, "subnet_exists", {"SubnetIds": [subnet["id"]], "Filters": filters}, start_time
                )

        if associate_resp.get("Ipv6CidrBlockAssociation", {}).get("AssociationId"):
            subnet["ipv6_association_id"] = associate_resp["Ipv6CidrBlockAssociation"]["AssociationId"]
            subnet["ipv6_cidr_block"] = associate_resp["Ipv6CidrBlockAssociation"]["Ipv6CidrBlock"]
            if subnet["ipv6_cidr_block_association_set"]:
                subnet["ipv6_cidr_block_association_set"][0] = camel_dict_to_snake_dict(
                    associate_resp["Ipv6CidrBlockAssociation"]
                )
            else:
                subnet["ipv6_cidr_block_association_set"].append(
                    camel_dict_to_snake_dict(associate_resp["Ipv6CidrBlockAssociation"])
                )

    return changed


def get_matching_subnet(conn, module, vpc_id, cidr):
    filters = ansible_dict_to_boto3_filter_list({"vpc-id": vpc_id, "cidr-block": cidr})
    try:
        _subnets = conn.describe_subnets(aws_retry=True, Filters=filters)
        subnets = get_subnet_info(_subnets)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get matching subnet")

    if subnets:
        return subnets[0]

    return None


def ensure_subnet_present(conn, module):
    subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
    changed = False

    # Initialize start so max time does not exceed the specified wait_timeout for multiple operations
    start_time = time.time()

    if subnet is None:
        if not module.check_mode:
            subnet = create_subnet(
                conn,
                module,
                module.params["vpc_id"],
                module.params["cidr"],
                ipv6_cidr=module.params["ipv6_cidr"],
                outpost_arn=module.params["outpost_arn"],
                az=module.params["az"],
                start_time=start_time,
            )
        changed = True
        # Subnet will be None when check_mode is true
        if subnet is None:
            return {"changed": changed, "subnet": {}}
    if module.params["wait"]:
        handle_waiter(conn, module, "subnet_exists", {"SubnetIds": [subnet["id"]]}, start_time)

    if module.params["ipv6_cidr"] != subnet.get("ipv6_cidr_block"):
        if ensure_ipv6_cidr_block(conn, module, subnet, module.params["ipv6_cidr"], module.check_mode, start_time):
            changed = True

    if module.params["map_public"] != subnet["map_public_ip_on_launch"]:
        ensure_map_public(conn, module, subnet, module.params["map_public"], module.check_mode, start_time)
        changed = True

    if module.params["assign_instances_ipv6"] != subnet.get("assign_ipv6_address_on_creation"):
        ensure_assign_ipv6_on_create(
            conn, module, subnet, module.params["assign_instances_ipv6"], module.check_mode, start_time
        )
        changed = True

    if module.params["tags"] != subnet["tags"]:
        stringified_tags_dict = dict((to_text(k), to_text(v)) for k, v in module.params["tags"].items())
        if ensure_tags(conn, module, subnet, stringified_tags_dict, module.params["purge_tags"], start_time):
            changed = True

    subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
    if not module.check_mode and module.params["wait"]:
        for _rewait in range(0, 5):
            if subnet:
                break
            time.sleep(2)
            subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
        # GET calls are not monotonic for map_public_ip_on_launch and assign_ipv6_address_on_creation
        # so we only wait for those if necessary just before returning the subnet
        subnet = ensure_final_subnet(conn, module, subnet, start_time)

    return {"changed": changed, "subnet": subnet}


def ensure_final_subnet(conn, module, subnet, start_time):
    for _rewait in range(0, 30):
        map_public_correct = False
        assign_ipv6_correct = False

        if module.params["map_public"] == subnet["map_public_ip_on_launch"]:
            map_public_correct = True
        else:
            if module.params["map_public"]:
                handle_waiter(conn, module, "subnet_has_map_public", {"SubnetIds": [subnet["id"]]}, start_time)
            else:
                handle_waiter(conn, module, "subnet_no_map_public", {"SubnetIds": [subnet["id"]]}, start_time)

        if module.params["assign_instances_ipv6"] == subnet.get("assign_ipv6_address_on_creation"):
            assign_ipv6_correct = True
        else:
            if module.params["assign_instances_ipv6"]:
                handle_waiter(conn, module, "subnet_has_assign_ipv6", {"SubnetIds": [subnet["id"]]}, start_time)
            else:
                handle_waiter(conn, module, "subnet_no_assign_ipv6", {"SubnetIds": [subnet["id"]]}, start_time)

        if map_public_correct and assign_ipv6_correct:
            break

        time.sleep(5)
        subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])

    return subnet


def ensure_subnet_absent(conn, module):
    subnet = get_matching_subnet(conn, module, module.params["vpc_id"], module.params["cidr"])
    if subnet is None:
        return {"changed": False}

    try:
        if not module.check_mode:
            conn.delete_subnet(aws_retry=True, SubnetId=subnet["id"])
            if module.params["wait"]:
                handle_waiter(conn, module, "subnet_deleted", {"SubnetIds": [subnet["id"]]}, time.time())
        return {"changed": True}
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete subnet")


def main():
    argument_spec = dict(
        az=dict(default=None, required=False),
        cidr=dict(required=True),
        ipv6_cidr=dict(default="", required=False),
        outpost_arn=dict(default="", type="str", required=False),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(default={}, required=False, type="dict", aliases=["resource_tags"]),
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

    retry_decorator = AWSRetry.jittered_backoff(retries=10)
    connection = module.client("ec2", retry_decorator=retry_decorator)

    state = module.params.get("state")

    try:
        if state == "present":
            result = ensure_subnet_present(connection, module)
        elif state == "absent":
            result = ensure_subnet_absent(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(**result)


if __name__ == "__main__":
    main()

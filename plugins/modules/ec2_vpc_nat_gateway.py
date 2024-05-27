#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_nat_gateway
version_added: 1.0.0
short_description: Manage AWS VPC NAT Gateways
description:
  - Ensure the state of AWS VPC NAT Gateways based on their id, allocation and subnet ids.
options:
  state:
    description:
      - Ensure NAT Gateway is present or absent.
    default: "present"
    choices: ["present", "absent"]
    type: str
  nat_gateway_id:
    description:
      - The id AWS dynamically allocates to the NAT Gateway on creation.
        This is required when the absent option is present.
    type: str
  subnet_id:
    description:
      - The id of the subnet to create the NAT Gateway in. This is required
        with the present option.
    type: str
  allocation_id:
    description:
      - The id of the elastic IP allocation. If this is not passed and the
        eip_address is not passed. An EIP is generated for this NAT Gateway.
    type: str
  connectivity_type:
    description:
      - Indicates whether the NAT gateway supports public or private connectivity.
    choices: ["public", "private"]
    default: "public"
    type: str
    version_added: 5.5.0
  eip_address:
    description:
      - The elastic IP address of the EIP you want attached to this NAT Gateway.
        If this is not passed and the O(allocation_id) is not passed,
        an EIP is generated for this NAT Gateway.
    type: str
  if_exist_do_not_create:
    description:
      - If a NAT Gateway exists already in the O(subnet_id), then do not create a new one.
    required: false
    default: false
    type: bool
  release_eip:
    description:
      - Deallocate the EIP from the VPC.
      - Option is only valid with the absent state.
      - You should use this with the wait option. Since you can not release an address while a delete operation is happening.
    default: false
    type: bool
  wait:
    description:
      - Wait for operation to complete before returning.
    default: false
    type: bool
  wait_timeout:
    description:
      - How many seconds to wait for an operation to complete before timing out.
    default: 320
    type: int
  client_token:
    description:
      - Optional unique token to be used during create to ensure idempotency.
        When specifying this option, ensure you specify the eip_address parameter
        as well otherwise any subsequent runs will fail.
    type: str
  default_create:
    description:
      - When O(default_create=true) and O(eip_address) has been set, but not yet
        allocated, the NAT gateway is created and a new EIP is automatically allocated.
      - When O(default_create=false) and O(eip_address) has been set, but not yet
        allocated, the module will fail.
      - If O(eip_address) has not been set, this parameter has no effect.
    default: false
    type: bool
    version_added: 6.2.0
author:
  - Allen Sanabria (@linuxdynasty)
  - Jon Hadfield (@jonhadfield)
  - Karen Cheng (@Etherdaemon)
  - Alina Buzachis (@alinabuzachis)
notes:
  - Support for O(tags) and O(purge_tags) was added in release 1.4.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create new nat gateway with client token.
  amazon.aws.ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    eip_address: 52.1.1.1
    region: ap-southeast-2
    client_token: abcd-12345678
  register: new_nat_gateway

- name: Create new nat gateway using an allocation-id and connectivity type.
  amazon.aws.ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    allocation_id: eipalloc-12345678
    connectivity_type: "private"
    region: ap-southeast-2
  register: new_nat_gateway

- name: Create new nat gateway, using an EIP address  and wait for available status.
  amazon.aws.ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    eip_address: 52.1.1.1
    wait: true
    region: ap-southeast-2
  register: new_nat_gateway

- name: Create new nat gateway and allocate new EIP.
  amazon.aws.ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    wait: true
    region: ap-southeast-2
  register: new_nat_gateway

- name: Create new nat gateway and allocate new EIP if a nat gateway does not yet exist in the subnet.
  amazon.aws.ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    wait: true
    region: ap-southeast-2
    if_exist_do_not_create: true
  register: new_nat_gateway

- name: Delete nat gateway using discovered nat gateways from facts module.
  amazon.aws.ec2_vpc_nat_gateway:
    state: absent
    region: ap-southeast-2
    wait: true
    nat_gateway_id: "{{ item.NatGatewayId }}"
    release_eip: true
  register: delete_nat_gateway_result
  loop: "{{ gateways_to_remove.result }}"

- name: Delete nat gateway and wait for deleted status.
  amazon.aws.ec2_vpc_nat_gateway:
    state: absent
    nat_gateway_id: nat-12345678
    wait: true
    wait_timeout: 500
    region: ap-southeast-2

- name: Delete nat gateway and release EIP.
  amazon.aws.ec2_vpc_nat_gateway:
    state: absent
    nat_gateway_id: nat-12345678
    release_eip: true
    wait: true
    wait_timeout: 300
    region: ap-southeast-2

- name: Create new nat gateway using allocation-id and tags.
  amazon.aws.ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    allocation_id: eipalloc-12345678
    region: ap-southeast-2
    tags:
      Tag1: tag1
      Tag2: tag2
  register: new_nat_gateway

- name: Update tags without purge
  amazon.aws.ec2_vpc_nat_gateway:
    subnet_id: subnet-12345678
    allocation_id: eipalloc-12345678
    region: ap-southeast-2
    purge_tags: false
    tags:
      Tag3: tag3
    wait: true
  register: update_tags_nat_gateway
"""

RETURN = r"""
connectivity_type:
    description:
      - Indicates whether the NAT gateway supports public or private connectivity.
    returned: always
    type: str
    sample: public
create_time:
  description: The ISO 8601 date time format in UTC.
  returned: always
  type: str
  sample: "2016-03-05T05:19:20.282000+00:00'"
nat_gateway_id:
  description: Id of the VPC NAT Gateway.
  returned: always
  type: str
  sample: "nat-0d1e3a878585988f8"
subnet_id:
  description: Id of the Subnet.
  returned: always
  type: str
  sample: "subnet-12345"
state:
  description: The current state of the NAT Gateway.
  returned: always
  type: str
  sample: "available"
tags:
  description: The tags associated the VPC NAT Gateway.
  type: dict
  returned: When tags are present.
  sample:
    tags:
        "Ansible": "Test"
vpc_id:
  description: Id of the VPC.
  returned: always
  type: str
  sample: "vpc-12345"
nat_gateway_addresses:
  description: List of dictionaries containing the public_ip, network_interface_id, private_ip, and allocation_id.
  returned: always
  type: complex
  contains:
    allocation_id:
        description: The allocation ID of the Elastic IP address that's associated with the NAT gateway.
        returned: always
        type: str
        sample: eipalloc-0853e66a40803da76
    association_id:
        description: The association ID of the Elastic IP address that is associated with the NAT gateway.
        returned: always
        type: str
        sample: eipassoc-0d6365c7eeb7d4932
    is_primary:
        description: Defines if the IP address is the primary address.
        returned: always
        type: bool
        sample: true
    network_interface_id:
        description: The ID of the network interface associated with the NAT gateway.
        returned: always
        type: str
        sample: eni-0a37acdbe306c661c
    private_ip:
        description: The private IP address associated with the Elastic IP address.
        returned: always
        type: str
        sample: 10.0.238.227
    public_ip:
        description: The Elastic IP address associated with the NAT gateway.
        returned: always
        type: str
        sample: 34.204.123.52
    status:
        description: The address status.
        returned: always
        type: str
        sample: succeeded
  sample: [
       {
            "allocation_id": "eipalloc-08ec128d03629671d",
            "association_id": "eipassoc-0d6365c7eeb7d4932",
            "is_primary": true,
            "network_interface_id": "eni-095104e630881bad6",
            "private_ip": "10.1.0.250",
            "public_ip": "34.202.90.172",
            "status": "succeeded"
        }
  ]
"""

import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import allocate_address
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_nat_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_nat_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_addresses
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_nat_gateways
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import release_address
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import is_ansible_aws_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def wait_for_status(client, module: AnsibleAWSModule, waiter_name: str, nat_gateway_id: str) -> None:
    wait_timeout = module.params.get("wait_timeout")
    wait_delay = 5
    attempts = 1 + int(wait_timeout / wait_delay)
    wait_for_resource_state(
        client, module, waiter_name, delay=wait_delay, max_attempts=attempts, NatGatewayIds=[nat_gateway_id]
    )


def get_nat_gateways(
    client, subnet_id: Optional[str] = None, nat_gateway_id: Optional[str] = None, states: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Retrieve a list of NAT Gateways
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance

    Kwargs:
        subnet_id (str): The subnet_id the nat resides in.
        nat_gateway_id (str): The Amazon NAT id.
        states (list): States available (pending, failed, available, deleting, and deleted)
            default=None

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> subnet_id = 'subnet-12345678'
        >>> get_nat_gateways(client, module, subnet_id)
        [
            {
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "55.55.55.55",
                        "network_interface_id": "eni-1234567",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-1234567"
                    }
                ],
                "nat_gateway_id": "nat-123456789",
                "state": "deleted",
                "subnet_id": "subnet-123456789",
                "tags": {},
                "vpc_id": "vpc-12345678"
            }
        ]

    Returns:
        list
    """

    params: dict[str, Any] = {}
    if not states:
        states = ["available", "pending"]
    if nat_gateway_id:
        params["NatGatewayIds"] = [nat_gateway_id]
    else:
        params["Filter"] = [
            {"Name": "subnet-id", "Values": [subnet_id]},
            {"Name": "state", "Values": states},
        ]

    return [camel_dict_to_snake_dict(gw) for gw in describe_nat_gateways(client, **params) or []]


def gateway_in_subnet_exists(
    client, subnet_id: str, allocation_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """Retrieve all NAT Gateways for a subnet.
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance
        subnet_id (str): The subnet_id the nat resides in.

    Kwargs:
        allocation_id (str): The EIP Amazon identifier.
            default = None

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> subnet_id = 'subnet-1234567'
        >>> allocation_id = 'eipalloc-1234567'
        >>> gateway_in_subnet_exists(client, module, subnet_id, allocation_id)
        (
            [
                {
                    "create_time": "2016-03-05T00:33:21.209000+00:00",
                    "delete_time": "2016-03-05T00:36:37.329000+00:00",
                    "nat_gateway_addresses": [
                        {
                            "public_ip": "55.55.55.55",
                            "network_interface_id": "eni-1234567",
                            "private_ip": "10.0.0.102",
                            "allocation_id": "eipalloc-1234567"
                        }
                    ],
                    "nat_gateway_id": "nat-123456789",
                    "state": "deleted",
                    "subnet_id": "subnet-123456789",
                    "tags": {},
                    "vpc_id": "vpc-1234567"
                }
            ],
            False
        )

    Returns:
        Tuple (list, bool)
    """

    states = ["available", "pending"]
    nat_gateways = get_nat_gateways(client, subnet_id=subnet_id, states=states)
    if not allocation_id:
        return nat_gateways, False

    allocation_id_exists = False
    gateways = []
    for gw in nat_gateways:
        for address in gw["nat_gateway_addresses"]:
            if address.get("allocation_id") == allocation_id:
                allocation_id_exists = True
                gateways.append(gw)

    return gateways, allocation_id_exists


def get_eip_allocation_id_by_address(client, eip_address: str) -> Tuple[Optional[str], str]:
    """Release an EIP from your EIP Pool
    Args:
        client (botocore.client.EC2): Boto3 client
        eip_address (str): The Elastic IP Address of the EIP.

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> eip_address = '52.87.29.36'
        >>> get_eip_allocation_id_by_address(client, eip_address)
        (
            'eipalloc-36014da3', ''
        )

    Returns:
        Tuple (str, str)
    """

    params = {
        "PublicIps": [eip_address],
    }
    allocation_id = None
    msg = ""

    try:
        allocations = describe_addresses(client, **params)
        if not allocations:
            msg = f"EIP {eip_address} does not exist"
            allocation_id = None
            return allocation_id, msg

        if len(allocations) == 1:
            allocation = allocations[0]
        else:
            allocation = None

        if allocation:
            if allocation.get("Domain") != "vpc":
                msg = f"EIP {eip_address} is a non-VPC EIP, please allocate a VPC scoped EIP"
            else:
                allocation_id = allocation.get("AllocationId")

    except is_ansible_aws_error_code("InvalidAddress.Malformed"):
        raise AnsibleAWSError(message=f"EIP address {eip_address} is invalid.")

    return allocation_id, msg


def allocate_eip_address(client, check_mode: bool) -> Tuple[bool, str, Optional[str]]:
    """Release an EIP from your EIP Pool
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> allocate_eip_address(client, module)
        (
            True, '', ''
        )

    Returns:
        Tuple (bool, str, str)
    """

    new_eip = None
    msg = ""
    params = {
        "Domain": "vpc",
    }

    if check_mode:
        ip_allocated = True
        new_eip = None
        return ip_allocated, msg, new_eip

    new_eip = allocate_address(client, **params)["AllocationId"]
    ip_allocated = True
    msg = f"eipalloc id {new_eip} created"

    return ip_allocated, msg, new_eip


def release_eip_address(client, allocation_id: str, check_mode: bool) -> bool:
    """Release an EIP from your EIP Pool
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance
        allocation_id (str): The eip Amazon identifier.

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> allocation_id = "eipalloc-123456"
        >>> release_address(client, module, allocation_id)
        True

    Returns:
        bool
    """

    changed = False
    if check_mode:
        return True

    addresses = describe_addresses(client, AllocationIds=[allocation_id])
    if addresses:
        # Release IP address
        changed = release_address(client, allocation_id=allocation_id)

    return changed


def create(client, module: AnsibleAWSModule, allocation_id: Optional[str]) -> Tuple[bool, str, Dict[str, Any]]:
    """Create an Amazon NAT Gateway.
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance
        allocation_id (str): The eip Amazon identifier

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> create(client, module, allocation_id)
        [
            true,
            {
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "55.55.55.55",
                        "network_interface_id": "eni-1234567",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-1234567"
                    }
                ],
                "nat_gateway_id": "nat-123456789",
                "state": "deleted",
                "subnet_id": "subnet-1234567",
                "tags": {},
                "vpc_id": "vpc-1234567"
            },
            ""
        ]

    Returns:
        Tuple (bool, str, list)
    """

    connectivity_type = module.params.get("connectivity_type")
    wait = module.params.get("wait")
    client_token = module.params.get("client_token")
    subnet_id = module.params.get("subnet_id")
    tags = module.params.get("tags")

    params = {"SubnetId": subnet_id, "ConnectivityType": connectivity_type}

    if connectivity_type == "public":
        params.update({"AllocationId": allocation_id})

    request_time = datetime.datetime.utcnow()
    changed = False
    token_provided = False
    result: dict[str, Any] = {}
    msg = ""

    if client_token:
        token_provided = True
        params["ClientToken"] = client_token

    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, ["natgateway"])

    if module.check_mode:
        changed = True
        return changed, msg, result

    try:
        result = create_nat_gateway(client, **params)
        result = camel_dict_to_snake_dict(result)
        changed = True

        create_time = result["create_time"].replace(tzinfo=None)

        if token_provided and (request_time > create_time):
            changed = False

        elif wait and result.get("state") != "available":
            wait_for_status(client, module, "nat_gateway_available", result["nat_gateway_id"])

            # Get new result
            result = camel_dict_to_snake_dict(
                describe_nat_gateways(client, NatGatewayIds=[result["nat_gateway_id"]])[0]
            )

    except is_ansible_aws_error_code("IdempotentParameterMismatch") as e:
        msg = "NAT Gateway does not support update and token has already been provided:" + e
        changed = False
        result = {}

    if result:
        result["tags"] = describe_ec2_tags(client, module, result["nat_gateway_id"], resource_type="natgateway")

    return changed, msg, result


def pre_create(
    client, module: AnsibleAWSModule, allocation_id: Optional[str], eip_address: Optional[str]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Create an Amazon NAT Gateway.
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> pre_create(client, module)
        [
            true,
            "",
            {
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "52.87.29.36",
                        "network_interface_id": "eni-5579742d",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-36014da3"
                    }
                ],
                "nat_gateway_id": "nat-03835afb6e31df79b",
                "state": "deleted",
                "subnet_id": "subnet-w4t12897",
                "tags": {},
                "vpc_id": "vpc-w68571b5"
            }
        ]

    Returns:
        Tuple (bool, str, list)
    """

    changed = False
    msg = ""
    results = {}

    connectivity_type = module.params.get("connectivity_type")
    if_exist_do_not_create = module.params.get("if_exist_do_not_create")
    purge_tags = module.params.get("purge_tags")
    default_create = module.params.get("default_create")
    subnet_id = module.params.get("subnet_id")
    tags = module.params.get("tags")

    if not allocation_id and not eip_address:
        existing_gateways, allocation_id_exists = gateway_in_subnet_exists(client, subnet_id=subnet_id)
        if len(existing_gateways) > 0 and if_exist_do_not_create:
            results = existing_gateways[0]
            changed |= ensure_ec2_tags(
                client, module, results["nat_gateway_id"], resource_type="natgateway", tags=tags, purge_tags=purge_tags
            )

            results["tags"] = describe_ec2_tags(client, module, results["nat_gateway_id"], resource_type="natgateway")

            if changed:
                return changed, msg, results

            changed = False
            msg = f"NAT Gateway {existing_gateways[0]['nat_gateway_id']} already exists in subnet_id {subnet_id}"
            return changed, msg, results
        else:
            if connectivity_type == "public":
                changed, msg, allocation_id = allocate_eip_address(client, module.check_mode)

                if not changed:
                    return changed, msg, {}

    elif eip_address or allocation_id:
        if eip_address and not allocation_id:
            allocation_id, msg = get_eip_allocation_id_by_address(client, eip_address)
            if not allocation_id and not default_create:
                changed = False
                module.fail_json(msg=msg)
            elif not allocation_id and default_create:
                eip_address = None
                return pre_create(client, module, allocation_id, eip_address)

        existing_gateways, allocation_id_exists = gateway_in_subnet_exists(
            client, subnet_id=subnet_id, allocation_id=allocation_id
        )

        if len(existing_gateways) > 0 and (allocation_id_exists or if_exist_do_not_create):
            results = existing_gateways[0]
            changed |= ensure_ec2_tags(
                client, module, results["nat_gateway_id"], resource_type="natgateway", tags=tags, purge_tags=purge_tags
            )

            results["tags"] = describe_ec2_tags(client, module, results["nat_gateway_id"], resource_type="natgateway")

            if changed:
                return changed, msg, results

            changed = False
            msg = f"NAT Gateway {existing_gateways[0]['nat_gateway_id']} already exists in subnet_id {subnet_id}"
            return changed, msg, results

    return create(client, module, allocation_id)


def remove(client, module: AnsibleAWSModule) -> Tuple[bool, str, Dict[str, Any]]:
    """Delete an Amazon NAT Gateway.
    Args:
        client (botocore.client.EC2): Boto3 client
        module: AnsibleAWSModule class instance
    Kwargs:
        wait (bool): Wait for the nat to be in the deleted state before returning.
        release_eip (bool): Once the nat has been deleted, you can deallocate the eip from the vpc.
        connectivity_type (str): private/public connection type

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> module = AnsibleAWSModule(...)
        >>> nat_gw_id = 'nat-03835afb6e31df79b'
        >>> remove(client, module, nat_gw_id, wait=True, release_eip=True, connectivity_type='public')
        [
            true,
            "",
            {
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "52.87.29.36",
                        "network_interface_id": "eni-5579742d",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-36014da3"
                    }
                ],
                "nat_gateway_id": "nat-03835afb6e31df79b",
                "state": "deleted",
                "subnet_id": "subnet-w4t12897",
                "tags": {},
                "vpc_id": "vpc-w68571b5"
            }
        ]

    Returns:
        Tuple (bool, str, list)
    """

    allocation_id = None
    changed = False
    results: dict[str, Any] = {}
    states = ["pending", "available"]
    msg = ""
    nat_gateway_id = module.params.get("nat_gateway_id")
    wait = module.params.get("wait")
    release_eip = module.params.get("release_eip")
    connectivity_type = module.params.get("connectivity_type")

    if module.check_mode:
        changed = True
        return changed, msg, results

    gw_list = get_nat_gateways(client, nat_gateway_id=nat_gateway_id, states=states)

    if len(gw_list) == 1:
        results = gw_list[0]
        try:
            changed = delete_nat_gateway(client, nat_gateway_id)
        except AnsibleEC2Error as e:
            module.fail_json_aws_error(e)
        if connectivity_type == "public":
            allocation_id = results["nat_gateway_addresses"][0]["allocation_id"]
        msg = f"NAT gateway {nat_gateway_id} is in a deleting state. Delete was successful"

        if wait and results.get("state") != "deleted":
            wait_for_status(client, module, "nat_gateway_deleted", nat_gateway_id)

            # Get new results
            results = camel_dict_to_snake_dict(describe_nat_gateways(client, NatGatewayIds=[nat_gateway_id])[0])
            results["tags"] = describe_ec2_tags(client, module, nat_gateway_id, resource_type="natgateway")

    if release_eip and allocation_id:
        changed |= release_eip_address(client, allocation_id, module.check_mode)

    return changed, msg, results


def main() -> None:
    argument_spec = dict(
        subnet_id=dict(type="str"),
        eip_address=dict(type="str"),
        allocation_id=dict(type="str"),
        connectivity_type=dict(type="str", default="public", choices=["private", "public"]),
        if_exist_do_not_create=dict(type="bool", default=False),
        state=dict(default="present", choices=["present", "absent"]),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=320, required=False),
        release_eip=dict(type="bool", default=False),
        nat_gateway_id=dict(type="str"),
        client_token=dict(type="str", no_log=False),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        default_create=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["allocation_id", "eip_address"]],
        required_if=[["state", "absent", ["nat_gateway_id"]], ["state", "present", ["subnet_id"]]],
    )

    try:
        client = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed = False
    msg = ""
    state = module.params.get("state")

    try:
        if state == "present":
            allocation_id = module.params.get("allocation_id")
            eip_address = module.params.get("eip_address")
            changed, msg, results = pre_create(client, module, allocation_id, eip_address)
        else:
            changed, msg, results = remove(client, module)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(msg=msg, changed=changed, **results)


if __name__ == "__main__":
    main()

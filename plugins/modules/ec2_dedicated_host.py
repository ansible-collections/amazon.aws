#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_dedicated_host
version_added: 9.3.0
short_description: Create, update or delete (release) EC2 dedicated host
description:
  - Create, update or delete (release) EC2 dedicated host.
author:
  - "Aubin Bikouo (@abikouo)"
options:
  state:
    description:
      - Create or delete dedicated host.
    required: false
    choices: [ present, absent ]
    default: 'present'
    type: str
  host_id:
    description:
      - The IDs of the Dedicated Hosts to release or modify
    type: str
    required: false
  lookup:
    description:
      - Look up EC2 dedicated host by either O(tags) or by O(host_id).
      - If O(lookup=tag) and O(tags) is not specified then no lookup for an
        existing dedicated host is performed and a new dedicated host will be created.
      - When using O(lookup=tag), multiple matches being found will result in
        a failure and no changes will be made.
      - To change the tags of a dedicated host, use O(lookup=host_id).
    default: tag
    choices: [ 'tag', 'host_id' ]
    type: str
  instance_family:
    description:
      - Specifies the instance family to be supported by the Dedicated Hosts.
      - If you specify an instance family, the Dedicated Hosts support multiple instance types within that instance family.
      - At least one of O(instance_family) or O(instance_type) must be specified when allocating dedicated host.
      - Mutually exclusive with paramter O(instance_type).
    type: str
  instance_type:
    description:
      - Specifies the instance type to be supported by the Dedicated Hosts.
      - If you specify an instance type, the Dedicated Hosts support instances of the specified instance type only.
      - At least one of O(instance_family) or O(instance_type) must be specified when allocating dedicated host.
      - Mutually exclusive with paramter O(instance_family).
    type: str
  host_recovery:
    description:
      - Indicates whether to enable or disable host recovery for the Dedicated Host.
      - Host recovery is disabled by default.
    type: str
    default: 'off'
    choices: ['on', 'off']
  outpost_arn:
    description:
      - The Amazon Resource Name (ARN) of the Amazon Web Services Outpost on which to allocate the Dedicated Host.
    type: str
  host_maintenance:
    description:
      - Indicates whether to enable or disable host maintenance for the Dedicated Host.
    type: str
    default: 'off'
    choices: ['on', 'off']
  asset_ids:
    description:
      - The IDs of the Outpost hardware assets on which to allocate the Dedicated Hosts.
      - Targeting specific hardware assets on an Outpost can help to minimize latency between your workloads.
      - This parameter is supported only if you specify O(outpost_arn).
      - If you specify this parameter, you can omit O(quantity).
      - If you specify both O(asset_ids) and O(quantity), then the value for O(quantity) must be equal to the number of O(asset_ids) specified.
    type: list
    elements: str
  auto_placement:
    description:
      - Indicates whether the host accepts any untargeted instance launches that match its instance type configuration,
        or if it only accepts Host tenancy instance launches that specify its unique host ID.
    type: str
    default: 'off'
    choices: ['on', 'off']
  client_token:
    description:
      - case-sensitive identifier that you provide to ensure the idempotency of the request.
    type: str
  quantity:
    description:
      - The number of Dedicated Hosts to allocate to your account with these parameters.
      - Required when O(state=present).
      - If you are allocating the Dedicated Hosts on an Outpost, and you specify O(asset_ids), you can omit this parameter.
      - If you specify both O(asset_ids) and O(quantity), then the value that you specify for O(quantity) must be equal to the number of O(asset_ids) specified.
    type: int
  availability_zone:
    description:
      - The Availability Zone in which to allocate the Dedicated Host.
      - Required if O(state=present).
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Release dedicated hosts
- name: Release dedicated host
  amazon.aws.ec2_dedicated_host:
    host_id: "h-0123456789abcdef0"

# Allocate dedicated host using instance type
- name: Allocate dedicated host using instance_type
  amazon.aws.ec2_dedicated_host:
    availability_zone: us-east-1a
    quantity: 1
    instance_type: mac2.metal
    tags:
      Scope: Mac
"""

RETURN = r"""
host:
  description: Information about the dedicated host created/updated.
  returned: When O(state=present)
  type: complex
  contains:
    allocation_time:
      description: The time that the Dedicated Host was allocated.
      returned: always
      type: str
      sample: "2025-02-12T12:09:22+00:00"
    allows_multiple_instance_types:
      description: Indicates whether the Dedicated Host supports multiple instance types of the same instance family.
      returned: always
      type: str
      sample: "off"
    auto_placement:
      description: Whether auto-placement is on or off.
      returned: always
      type: str
      sample: "off"
    availability_zone:
      description: The Availability Zone of the Dedicated Host.
      returned: always
      type: str
      sample: "us-east-1b"
    availability_zone_id:
      description: The ID of the Availability Zone in which the Dedicated Host is allocated.
      returned: always
      type: str
      sample: "use1-az6"
    available_capacity:
      description: Information about the instances running on the Dedicated Host.
      returned: always
      type: dict
      contains:
        available_v_cpus:
          description: The number of vCPUs available for launching instances onto the Dedicated Host.
          returned: always
          type: int
          sample: 8
        available_instance_capacity:
          description: The number of instances that can be launched onto the Dedicated Host.
          returned: always
          type: complex
          contains:
            available_capacity:
              description: The number of instances that can be launched onto the Dedicated Host.
              returned: always
              type: int
              sample: 1
            instance_type:
              description: The instance type supported by the Dedicated Host.
              returned: always
              type: str
              sample: "mac2.metal"
            total_capacity:
              description: The total number of instances that can be launched onto the Dedicated Host if there are no instances running on it.
              returned: always
              type: dict
              sample: 1
    host_id:
      description: The ID of the Dedicated Host.
      returned: always
      type: str
      sample: "h-03f51341e6e39f848"
    client_token:
      description: Unique, case-sensitive identifier that you provide to ensure the idempotency of the request.
      returned: always
      type: str
      sample: "token-0123456789a"
    host_properties:
      description: The hardware specifications of the Dedicated Host.
      returned: always
      type: dict
      contains:
        cores:
          description: The number of cores on the Dedicated Host.
          returned: always
          type: int
          sample: 8
        instance_type:
          description: The instance type supported by the Dedicated Host.
          returned: always
          type: str
          sample: "mac2.metal"
        instance_family:
          description: The instance family supported by the Dedicated Host.
          returned: if defined
          type: str
          sample: "mac2"
        sockets:
          description: The number of sockets on the Dedicated Host.
          returned: always
          type: int
          sample: 1
        total_v_cpus:
          description: The total number of vCPUs on the Dedicated Host.
          returned: always
          type: int
          sample: 8
    host_reservation_id:
      description: The reservation ID of the Dedicated Host.
      returned: always
      type: str
    instances:
      description: The IDs and instance type that are currently running on the Dedicated Host.
      returned: always
      type: complex
      contains:
        instance_id:
          description: The ID of instance that is running on the Dedicated Host.
          returned: always
          type: str
          sample: "i-0123456789abcd"
        instance_type:
          description: The instance type of the running instance.
          returned: always
          type: str
          sample: "ec2.micro"
        owner_id:
          description: The ID of the Amazon Web Services account that owns the instance.
          returned: always
          type: str
          sample: "0123456789"
    state:
      description: The state of the Dedicated Host.
      returned: always
      type: str
      sample: "available"
    release_time:
      description: The time that the Dedicated Host was released.
      returned: always
      type: str
      sample: "2025-02-12T12:09:22+00:00"
    host_recovery:
      description: Indicates whether host recovery is enabled or disabled for the Dedicated Host.
      returned: always
      type: str
      sample: "off"
    owner_id:
      description: The ID of the Amazon Web Services account that owns the Dedicated Host.
      returned: always
      type: str
      sample: "0123456789"
    member_of_service_linked_resource_group:
      description: Indicates whether the Dedicated Host is in a host resource group.
      returned: always
      type: bool
      sample: false
    outpost_arn:
      description: The Amazon Resource Name (ARN) of the Amazon Web Services Outpost on which the Dedicated Host is allocated.
      returned: always
      type: str
      sample: "arn:aws:outposts:us-east-1:0123012301230123:outpost/op-0123456789abcdef0"
    host_maintenance:
      description: Indicates whether host maintenance is enabled or disabled for the Dedicated Host.
      returned: always
      type: str
      sample: "off"
    asset_id:
      description: The ID of the Outpost hardware asset on which the Dedicated Host is allocated.
      returned: always
      type: str
      sample: "abcdefgh"
    tags:
      description: Dictionary of tags added to the dedicated host.
      returned: always
      type: dict
      sample: {}
"""

from typing import Any
from typing import Dict
from typing import List
from typing import NoReturn
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import allocate_ec2_dedicated_hosts
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_dedicated_hosts
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_ec2_dedicated_hosts
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import release_ec2_dedicated_host
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def describe_host(client, host_id: str) -> Optional[Dict[str, Any]]:
    host_info = None
    hosts = describe_ec2_dedicated_hosts(client, HostIds=[host_id])
    if hosts:
        host_info = hosts[0]
    return host_info


def tags_match(match_tags: Dict[str, str], candidate_tags: Dict[str, str]) -> bool:
    return all((k in candidate_tags and candidate_tags[k] == v for k, v in match_tags.items()))


def get_ec2_dedicated_host(client, module: AnsibleAWSModule) -> Optional[Dict[str, Any]]:
    host_info = None
    # Select all states except 'released' and 'released-permanent-failure'
    params = {"Filters": [{"Name": "state", "Values": ["available", "under-assessment", "permanent-failure"]}]}

    lookup = module.params.get("lookup")
    host_id = module.params.get("host_id")
    ansible_tags = module.params.get("tags")

    if lookup == "host_id":
        params["HostIds"] = [host_id]
    elif lookup == "tag" and not ansible_tags:
        # lookup == 'tag' but tags was not provided
        return host_info
    hosts = describe_ec2_dedicated_hosts(client, **params)
    if hosts:
        if lookup == "tag":
            count = 0
            for h in hosts:
                aws_tags = boto3_tag_list_to_ansible_dict(h.get("Tags", {}))
                if aws_tags == ansible_tags:
                    host_info = h
                    count += 1
            if count > 1:
                module.fail_json(msg=f"Tags provided do not identify a unique dedicated host ({count} found).")
        else:
            host_info = hosts[0]

    return host_info


def format_output(host: Dict[str, Any]) -> List[Dict[str, Any]]:
    host["tags"] = boto3_tag_list_to_ansible_dict(host.pop("Tags", {}))
    return camel_dict_to_snake_dict(host, ignore_list=["tags"])


def release_host(client, module: AnsibleAWSModule, existing: Dict[str, Any]) -> NoReturn:
    if not existing:
        module.exit_json(changed=False)
    host_id = module.params.get("host_id")
    if module.check_mode:
        module.exit_json(changed=True, msg=f"Would have released dedicated host '{host_id}' if not in check mode.")
    changed = release_ec2_dedicated_host(client, host_id)
    module.exit_json(changed=changed, host=format_output(existing))


def create_or_update_host(client, module: AnsibleAWSModule, existing: Dict[str, Any]) -> NoReturn:
    host_id = module.params.get("host_id")
    changed = False
    if existing:
        # Update dedicated host
        # Check if one of the following has changed ('HostRecovery', 'InstanceType', 'InstanceFamily', 'HostMaintenance', 'AutoPlacement')
        host_maintenance = module.params.get("host_maintenance")
        instance_type = module.params.get("instance_type")
        instance_family = module.params.get("instance_family")
        auto_placement = module.params.get("auto_placement")
        host_recovery = module.params.get("host_recovery")
        params_to_update = {}
        if host_recovery != existing.get("HostRecovery"):
            params_to_update["HostRecovery"] = host_recovery
        if instance_type != existing.get("HostProperties", {}).get("InstanceType"):
            params_to_update["InstanceType"] = instance_type
        if instance_family != existing.get("HostProperties", {}).get("InstanceFamily"):
            params_to_update["InstanceFamily"] = instance_family
        if host_maintenance != existing.get("HostMaintenance"):
            params_to_update["HostMaintenance"] = host_maintenance
        if auto_placement != existing.get("AutoPlacement"):
            params_to_update["AutoPlacement"] = auto_placement

        if params_to_update:
            if module.check_mode:
                module.exit_json(changed=True, msg="Would have update dedicated host if not in check mode.")

            result = modify_ec2_dedicated_hosts(client, host_id=host_id, **params_to_update)
            if result.get("Unsuccessful"):
                code = result["Unsuccessful"][0]["Error"]["Code"]
                message = result["Unsuccessful"][0]["Error"]["Message"]
                module.fail_json(
                    msg=f"The Dedicated Hosts '{host_id}' could not be modified. Code='{code}' Message = '{message}'"
                )
            changed = True
    else:
        # Allocate dedicated host
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have allocate dedicated host if not in check mode.")

        availability_zone = module.params.get("availability_zone")
        instance_family = module.params.get("instance_family")
        host_recovery = module.params.get("host_recovery")
        outpost_arn = module.params.get("outpost_arn")
        host_maintenance = module.params.get("host_maintenance")
        auto_placement = module.params.get("auto_placement")
        asset_ids = module.params.get("asset_ids")
        client_token = module.params.get("client_token")
        instance_type = module.params.get("instance_type")
        quantity = module.params.get("quantity")

        params = {}
        if instance_family:
            params["InstanceFamily"] = instance_family
        if host_recovery:
            params["HostRecovery"] = host_recovery
        if outpost_arn:
            params["OutpostArn"] = outpost_arn
        if host_maintenance:
            params["HostMaintenance"] = host_maintenance
        if asset_ids:
            params["AssetIds"] = asset_ids
        if client_token:
            params["ClientToken"] = client_token
        if instance_type:
            params["InstanceType"] = instance_type
        if quantity:
            params["Quantity"] = quantity

        host_id = allocate_ec2_dedicated_hosts(client, availability_zone=availability_zone, **params)[0]
        changed = True

    # Ensure tags
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    changed |= ensure_ec2_tags(client, module, host_id, tags=tags, purge_tags=purge_tags)

    host_info = describe_host(client, host_id)
    module.exit_json(changed=changed, host=format_output(host_info))


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),
            availability_zone=dict(type="str", required=False),
            host_id=dict(),
            lookup=dict(type="str", choices=["tag", "host_id"], default="tag"),
            instance_family=dict(type="str"),
            host_recovery=dict(type="str", choices=["on", "off"], default="off"),
            outpost_arn=dict(),
            host_maintenance=dict(type="str", choices=["on", "off"], default="off"),
            auto_placement=dict(type="str", choices=["on", "off"], default="off"),
            asset_ids=dict(type="list", elements="str"),
            client_token=dict(no_log=False),
            instance_type=dict(),
            quantity=dict(type="int"),
            tags=dict(type="dict", aliases=["resource_tags"]),
            purge_tags=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
        mutually_exclusive=[["instance_family", "instance_type"]],
        required_if=[
            ["state", "present", ["availability_zone", "quantity"]],
            ["state", "absent", ["host_id"]],
            ["lookup", "host_id", ["host_id"]],
        ],
    )

    client = module.client("ec2")
    state = module.params.get("state")

    existing = get_ec2_dedicated_host(client, module)

    try:
        if state == "absent":
            # Release EC2 dedicated host
            release_host(client, module, existing)
        else:
            create_or_update_host(client, module, existing)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

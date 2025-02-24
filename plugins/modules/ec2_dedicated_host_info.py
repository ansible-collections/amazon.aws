#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_dedicated_host_info
version_added: 9.3.0
short_description: Gather information about EC2 Dedicated Hosts in AWS
description:
  - Gather information about EC2 Dedicated Hosts in AWS.
  - The module can also gather information about dedicated Mac hosts.
author:
  - "Aubin Bikouo (@abikouo)"
options:
  host_ids:
    description:
      - The IDs of the Dedicated Hosts.
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeHosts.html) for possible filters.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeMacHosts.html) for possible filters for
        EC2 Mac dedicated hosts.
    type: dict
  mac_only:
    description:
      - When set to V(true) retrieve EC2 Mac Dedicated Hosts only.
    type: bool
    default: False
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all dedicated hosts
- name: Gather information about all dedicated hosts
  amazon.aws.ec2_dedicated_host_info:

# Gather information about all EC2 Mac dedicated hosts only
- name: Gather information about all EC2 Mac dedicated hosts
  amazon.aws.ec2_dedicated_host_info:
    mac_only: true

# Gather information about dedicated hosts with state=released
- name: Gather information about released dedicated hosts
  amazon.aws.ec2_dedicated_host_info:
    filters:
      state: released
"""

RETURN = r"""
hosts:
  description: List of dedicated hosts.
  returned: When O(mac_only=false)
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
mac_hosts:
  description: List of EC2 Mac dedicated hosts.
  returned: When O(mac_only=true)
  type: complex
  contains:
    host_id:
      description: The EC2 Mac Dedicated Host ID.
      returned: always
      type: str
      sample: "h-04b38258aba8c1875"
    mac_os_latest_supported_versions:
      description: The latest macOS versions that the EC2 Mac Dedicated Host can launch without being upgraded.
      returned: always
      type: list
      elements: str
      sample: ["15.3", "14.7.3", "13.7.3"]
"""

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_dedicated_hosts
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_mac_dedicated_hosts
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def format_results(hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for h in hosts:
        h["tags"] = boto3_tag_list_to_ansible_dict(h.pop("Tags", {}))
        results.append(camel_dict_to_snake_dict(h, ignore_list=["tags"]))
    return results


def build_args(module: AnsibleAWSModule) -> Dict[str, Any]:
    filters = module.params.get("filters")
    host_ids = module.params.get("host_ids")
    params = {}
    if host_ids:
        params["HostIds"] = host_ids
    if filters:
        params["Filters"] = ansible_dict_to_boto3_filter_list(filters)
    return params


def list_dedicated_hosts(client: Any, module: AnsibleAWSModule) -> Dict[str, Any]:
    params = build_args(module)
    results = describe_ec2_dedicated_hosts(client, **params)
    return dict(hosts=format_results(results))


def list_mac_dedicated_hosts(client: Any, module: AnsibleAWSModule) -> Dict[str, Any]:
    params = build_args(module)
    results = describe_ec2_mac_dedicated_hosts(client, **params)
    return dict(mac_hosts=format_results(results))


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            host_ids=dict(type="list", elements="str"),
            filters=dict(type="dict"),
            mac_only=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    client = module.client("ec2")
    mac_only = module.params.get("mac_only")

    if mac_only:
        result = list_mac_dedicated_hosts(client, module)
    else:
        result = list_dedicated_hosts(client, module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

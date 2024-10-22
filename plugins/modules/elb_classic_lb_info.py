#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: elb_classic_lb_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: Gather information about EC2 Classic Elastic Load Balancers in AWS
description:
  - Gather information about EC2 Classic Elastic Load Balancers in AWS.
author:
  - "Michael Schultz (@mjschultz)"
  - "Fernando Jose Pando (@nand0p)"
options:
  names:
    description:
      - List of ELB names to gather information about. Pass this option to gather information about a set of ELBs, otherwise, all ELBs are returned.
    type: list
    elements: str
    default: []
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Output format tries to match amazon.aws.elb_classic_lb module input parameters

- name: Gather information about all ELBs
  amazon.aws.elb_classic_lb_info:
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

- name: Gather information about a particular ELB
  amazon.aws.elb_classic_lb_info:
    names: frontend-prod-elb
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ elb_info.elbs.0.dns_name }}"

- name: Gather information about a set of ELBs
  amazon.aws.elb_classic_lb_info:
    names:
      - frontend-prod-elb
      - backend-prod-elb
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"
"""

RETURN = r"""
elbs:
  description: A list of load balancers.
  returned: always
  type: list
  elements: dict
  contains:
    attributes:
      description: Information about the load balancer attributes.
      returned: always
      type: dict
      contains:
        access_log:
          description: Information on whether access logs are enabled or not.
          type: dict
          sample: {
                    "enabled": false
                  }
        additional_attributes:
          description: Information about additional load balancer attributes.
          type: list
          elements: dict
          sample: [
                    {
                        "key": "elb.http.desyncmitigationmode",
                        "value": "defensive"
                    }
                  ]
        connection_draining:
          description:
            - Information on connection draining configuration of elastic load balancer.
          type: dict
          sample: {
                    "enabled": true,
                    "timeout": 300
                  }
          contains:
            enabled:
              description: Whether connection draining is enabled.
              type: bool
              returned: always
            timeout:
              description: The maximum time, in seconds, to keep the existing connections open before deregistering the instances.
              type: int
              returned: always
        connection_settings:
          description: Information on connection settings.
          type: dict
          sample: {
                    "idle_timeout": 60
                  }
        cross_zone_load_balancing:
          description: Information on whether cross zone load balancing is enabled or not.
          type: dict
          sample: {
                    "enabled": true
                  }
    availability_zones:
      description: The Availability Zones for the load balancer.
      type: list
      elements: str
      returned: always
      sample: [
                "us-west-2a"
              ]
    backend_server_descriptions:
      description: Information about your EC2 instances.
      type: list
      elements: dict
      returned: always
      sample: [
                {
                    instance_port: 8085,
                    policy_names: [
                        'MyPolicy1',
                    ]
                },
              ]
    canonical_hosted_zone_name:
      description: The DNS name of the load balancer.
      type: str
      returned: always
      sample: "test-123456789.us-west-2.elb.amazonaws.com"
    canonical_hosted_zone_name_id:
      description: The ID of the Amazon Route 53 hosted zone for the load balancer.
      type: str
      returned: always
      sample: "Z1Z1ZZ5HABSF5"
    created_time:
      description: The date and time the load balancer was created.
      type: str
      returned: always
      sample: "2024-09-04T17:52:22.270000+00:00"
    dns_name:
      description: The DNS name of the load balancer.
      type: str
      returned: "always"
      sample: "test-123456789.us-west-2.elb.amazonaws.com"
    health_check:
      description: Information about the health checks conducted on the load balancer.
      type: dict
      returned: always
      sample: {
                "healthy_threshold": 10,
                "interval": 5,
                "target": "HTTP:80/index.html",
                "timeout": 2,
                "unhealthy_threshold": 2
              }
      contains:
        healthy_threshold:
          description: The number of consecutive health checks successes required before moving the instance to the Healthy state.
          type: int
          returned: always
        interval:
          description: The approximate interval, in seconds, between health checks of an individual instance.
          type: int
          returned: always
        target:
          description: The instance being checked. The protocol is either TCP, HTTP, HTTPS, or SSL. The range of valid ports is one (1) through 65535.
          type: str
          returned: always
        timeout:
          description: The amount of time, in seconds, during which no response means a failed health check.
          type: int
          returned: always
        unhealthy_threshold:
          description: The number of consecutive health checks successes required before moving the instance to the Unhealthy state.
          type: int
          returned: always
    instances:
      description: The IDs of the instances for the load balancer.
      type: list
      elements: dict
      returned: always
      sample: [
                {
                    "instance_id": "i-11d1f111ea111111b"
                }
              ]
    instances_inservice:
      description: Information about instances for load balancer in state "InService".
      type: list
      returned: always
      sample: [
                "i-11d1f111ea111111b"
              ]
    instances_inservice_count:
      description: Total number of instances for load balancer with state "InService".
      type: int
      returned: always
      sample: 1
    instances_outofservice:
      description: Information about instances for load balancer in state "OutOfService".
      type: list
      returned: always
      sample: [
                "i-11d1f111ea111111b"
              ]
    instances_outofservice_count:
      description: Total number of instances for load balancer with state "OutOfService".
      type: int
      returned: always
      sample: 0
    instances_unknownservice:
      description: Information about instances for load balancer in state "Unknown".
      type: list
      returned: always
      sample: [
                "i-11d1f111ea111111b"
              ]
    instances_unknownservice_count:
      description: Total number of instances for load balancer with state "Unknown".
      type: int
      returned: always
      sample: 1
    listener_descriptions:
      description: Information about the listeners for the load balancer.
      type: list
      elements: dict
      returned: always
      sample: [
                {
                  "listener": {
                      "instance_port": 80,
                      "instance_protocol": "HTTP",
                      "load_balancer_port": 80,
                      "protocol": "HTTP"
                  },
                  "policy_names": []
                }
              ]
    load_balancer_name:
      description: The name of the elastic load balancer.
      type: str
      returned: always
      sample: "MyLoadBalancer"
    policies:
      description: Information about the policies defined for the load balancer.
      type: dict
      returned: always
      sample: {
                "app_cookie_stickiness_policies": [],
                "lb_cookie_stickiness_policies": [],
                "other_policies": []
              }
      contains:
        app_cookie_stickiness_policies:
          description: The stickiness policies created using CreateAppCookieStickinessPolicy.
          type: list
          returned: always
        lb_cookie_stickiness_policies:
          description: The stickiness policies created using CreateLBCookieStickinessPolicy.
          type: list
          returned: always
        other_policies:
          description: The policies other than the stickiness policies.
          type: list
          returned: always
    scheme:
      description: The type of load balancer.
      type: str
      returned: always
      sample: "internet-facing"
    security_groups:
      description: The security groups for the load balancer.
      type: list
      returned: always
      sample: [
                "sg-111111af1111cb111"
              ]
    source_security_group:
      description:
        - The security group for the load balancer,
          which are used as part of inbound rules for registered instances.
      type: dict
      returned: always
      sample: {
                  "group_name": "default",
                  "owner_alias": "721111111111"
              }
      contains:
        group_name:
          description: The name of the security group.
          type: str
          returned: always
        owner_alias:
          description: The owner of the security group.
          type: str
          returned: always
    subnets:
      description: The IDs of the subnets for the load balancer.
      type: list
      returned: always
      sample: [
                "subnet-111111af1111cb111"
              ]
    tags:
      description: The tags associated with a load balancer.
      type: dict
      returned: always
      sample: {
                "Env": "Dev",
                "Owner": "Dev001"
              }
    vpc_id:
      description: The ID of the VPC for the load balancer.
      type: str
      returned: always
      sample: "vpc-0cc28c9e20d111111"
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def list_elbs(connection: Any, load_balancer_names: List[str]) -> List[Dict]:
    """
    List Elastic Load Balancers (ELBs) and their detailed information.

    Parameters:
      connection (boto3.client): The Boto3 ELB client object.
      load_balancer_names (List[str]): List of ELB names to gather information about.

    Returns:
      A list of dictionaries where each dictionary contains informtion about one ELB.
    """
    results = []

    if not load_balancer_names:
        for lb in get_all_lb(connection):
            results.append(describe_elb(connection, lb))

    for load_balancer_name in load_balancer_names:
        lb = get_lb(connection, load_balancer_name)
        if not lb:
            continue
        results.append(describe_elb(connection, lb))
    return results


def describe_elb(connection: Any, lb: Dict[str, Any]) -> Dict[str, Any]:
    """
    Describes an Elastic Load Balancer (ELB).

    Parameters:
      connection (boto3.client): The Boto3 ELB client object.
      lb (Dict): Dictionary containing ELB .

    Returns:
      A dictionary with detailed information of the ELB.
    """
    description = camel_dict_to_snake_dict(lb)
    name = lb["LoadBalancerName"]
    instances = lb.get("Instances", [])
    description["tags"] = get_tags(connection, name)
    description["instances_inservice"], description["instances_inservice_count"] = lb_instance_health(
        connection, name, instances, "InService"
    )
    description["instances_outofservice"], description["instances_outofservice_count"] = lb_instance_health(
        connection, name, instances, "OutOfService"
    )
    description["instances_unknownservice"], description["instances_unknownservice_count"] = lb_instance_health(
        connection, name, instances, "Unknown"
    )
    description["attributes"] = get_lb_attributes(connection, name)
    return description


@AWSRetry.jittered_backoff()
def get_all_lb(connection: Any) -> List:
    """
    Get paginated result for information of all Elastic Load Balancers.

    Parameters:
        connection (boto3.client): The Boto3 ELB client object.

    Returns:
        A list of dictionaries containing descriptions of all ELBs.
    """
    paginator = connection.get_paginator("describe_load_balancers")
    return paginator.paginate().build_full_result()["LoadBalancerDescriptions"]


def get_lb(connection: Any, load_balancer_name: str) -> Union[Dict[str, Any], List]:
    """
    Describes a specific Elastic Load Balancer (ELB) by name.

    Parameters:
      connection (boto3.client): The Boto3 ELB client object.
      load_balancer_name (str): Name of the ELB to gather information about.

    Returns:
      A dictionary with detailed information of the specified ELB.
    """
    try:
        return connection.describe_load_balancers(aws_retry=True, LoadBalancerNames=[load_balancer_name])[
            "LoadBalancerDescriptions"
        ][0]
    except is_boto3_error_code("LoadBalancerNotFound"):
        return []


def get_lb_attributes(connection: Any, load_balancer_name: str) -> Dict[str, Any]:
    """
    Retrieves attributes of specific Elastic Load Balancer (ELB) by name.

    Parameters:
      connection (boto3.client): The Boto3 ELB client object.
      load_balancer_name (str): Name of the ELB to gather information about.

    Returns:
      A dictionary with detailed information of the attributes of specified ELB.
    """
    attributes = connection.describe_load_balancer_attributes(aws_retry=True, LoadBalancerName=load_balancer_name).get(
        "LoadBalancerAttributes", {}
    )
    return camel_dict_to_snake_dict(attributes)


def get_tags(connection: Any, load_balancer_name: str) -> Dict[str, Any]:
    """
    Retrieves tags of specific Elastic Load Balancer (ELB) by name.

    Parameters:
      connection (boto3.client): The Boto3 ELB client object.
      load_balancer_name (str): Name of the ELB to gather information about.

    Returns:
      A dictionary of tags associated with the specified ELB.
    """
    tags = connection.describe_tags(aws_retry=True, LoadBalancerNames=[load_balancer_name])["TagDescriptions"]
    if not tags:
        return {}
    return boto3_tag_list_to_ansible_dict(tags[0]["Tags"])


def lb_instance_health(
    connection: Any, load_balancer_name: str, instances: List[Dict[str, Any]], state: str
) -> Tuple[List[str], int]:
    """
    Describes the health status of instances associated with a specific Elastic Load Balancer (ELB).

    Parameters:
        connection (Any): The Boto3 client object for ELB.
        load_balancer_name (str): The name of the ELB.
        instances (List[Dict]): List of dictionaries containing instances associated with the ELB.
        state (str): The health state to filter by (e.g., "InService", "OutOfService", "Unknown").

    Returns:
        Tuple[List, int]: A tuple containing a list of instance IDs matching state and the count of matching instances.
    """
    instance_states = connection.describe_instance_health(LoadBalancerName=load_balancer_name, Instances=instances).get(
        "InstanceStates", []
    )
    instate = [instance["InstanceId"] for instance in instance_states if instance["State"] == state]
    return instate, len(instate)


def main():
    argument_spec = dict(
        names=dict(default=[], type="list", elements="str"),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    connection = module.client("elb", retry_decorator=AWSRetry.jittered_backoff(retries=5, delay=5))

    try:
        elbs = list_elbs(connection, module.params.get("names"))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get load balancer information.")

    module.exit_json(elbs=elbs)


if __name__ == "__main__":
    main()

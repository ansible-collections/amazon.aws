#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: elb_classic_lb_info
version_added: 1.0.0
version_added_collection: community.aws
short_description: Gather information about EC2 Elastic Load Balancers in AWS
description:
  - Gather information about EC2 Elastic Load Balancers in AWS
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
# Output format tries to match amazon.aws.ec2_elb_lb module input parameters

- name: Gather information about all ELBs
  amazon.aws.elb_classic_lb_info:
  register: elb_info

- name: Print dns names from above task result
  ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

- name: Gather information about a particular ELB
  amazon.aws.elb_classic_lb_info:
    names: frontend-prod-elb
  register: elb_info

- name: Prnt dns name from above task result
  ansible.builtin.debug:
    msg: "{{ elb_info.elbs.0.dns_name }}"

- name: Gather information about a set of ELBs
  amazon.aws.elb_classic_lb_info:
    names:
      - frontend-prod-elb
      - backend-prod-elb
  register: elb_info

- name: Print dns names from above task result
  ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"
"""

RETURN = r"""
elbs:
  description: a list of load balancers
  returned: always
  type: list
  sample:
    elbs:
      - attributes:
          access_log:
            enabled: false
          connection_draining:
            enabled: true
            timeout: 300
          connection_settings:
            idle_timeout: 60
          cross_zone_load_balancing:
            enabled: true
        availability_zones:
          - "us-east-1a"
          - "us-east-1b"
          - "us-east-1c"
          - "us-east-1d"
          - "us-east-1e"
        backend_server_description: []
        canonical_hosted_zone_name: test-lb-XXXXXXXXXXXX.us-east-1.elb.amazonaws.com
        canonical_hosted_zone_name_id: XXXXXXXXXXXXXX
        created_time: '2017-08-23T18:25:03.280000+00:00'
        dns_name: test-lb-XXXXXXXXXXXX.us-east-1.elb.amazonaws.com
        health_check:
          healthy_threshold: 10
          interval: 30
          target: HTTP:80/index.html
          timeout: 5
          unhealthy_threshold: 2
        instances: []
        instances_inservice: []
        instances_inservice_count: 0
        instances_outofservice: []
        instances_outofservice_count: 0
        instances_unknownservice: []
        instances_unknownservice_count: 0
        listener_descriptions:
          - listener:
              instance_port: 80
              instance_protocol: HTTP
              load_balancer_port: 80
              protocol: HTTP
            policy_names: []
        load_balancer_name: test-lb
        policies:
          app_cookie_stickiness_policies: []
          lb_cookie_stickiness_policies: []
          other_policies: []
        scheme: internet-facing
        security_groups:
          - sg-29d13055
        source_security_group:
          group_name: default
          owner_alias: XXXXXXXXXXXX
        subnets:
          - subnet-XXXXXXXX
          - subnet-XXXXXXXX
        tags: {}
        vpc_id: vpc-c248fda4
"""

from typing import Any
from typing import List
from typing import Dict
from typing import Tuple
from typing import Union

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


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


def describe_elb(connection: Any, lb: Dict) -> Dict:
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
def get_all_lb(connection):
    """
    Get paginated result for information of all Elastic Load Balancers.

    Parameters:
        connection (boto3.client): The Boto3 ELB client object.

    Returns:
        A list of dictionaries containing descriptions of all ELBs.
    """
    paginator = connection.get_paginator("describe_load_balancers")
    return paginator.paginate().build_full_result()["LoadBalancerDescriptions"]


def get_lb(connection: Any, load_balancer_name: str) -> Union[Dict, List]:
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


def get_lb_attributes(connection: Any, load_balancer_name: str) -> Dict:
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


def get_tags(connection: Any, load_balancer_name: str) -> Dict:
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


def lb_instance_health(connection: Any, load_balancer_name: str, instances: List[Dict], state: str) -> Tuple[List, int]:
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

    connection = module.client(
        "elb", retry_decorator=AWSRetry.jittered_backoff(retries=5, delay=5)
    )

    try:
        elbs = list_elbs(connection, module.params.get("names"))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get load balancer information.")

    module.exit_json(elbs=elbs)


if __name__ == "__main__":
    main()

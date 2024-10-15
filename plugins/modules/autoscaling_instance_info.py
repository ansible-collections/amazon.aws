#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: autoscaling_instance_info
version_added: 9.0.0
short_description: describe instances associated with AWS AutoScaling Groups (ASGs)
description:
  - Describe instances associated with AWS AutoScaling Groups (ASGs).
author:
  - "Mark Chappell (@tremble)"
options:
  group_name:
    description:
      - Name of the AutoScaling Group to manage.
      - O(group_name) and O(instance_ids) are mutually exclusive.
    type: str
  instance_ids:
    description:
      - The IDs of the EC2 instances.
      - O(group_name) and O(instance_ids) are mutually exclusive.
    type: list
    elements: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Describe all instances in a region
  amazon.aws.autoscaling_instance_info:
  register: instances

- name: Describe a specific instance
  amazon.aws.autoscaling_instance_info:
    instance_ids:
      - "i-123456789abcdef01"
  register: instances

- name: Describe the instances attached to a specific Auto Scaling Group
  amazon.aws.autoscaling_instance_info:
    group_name: example-asg
  register: instances
"""

RETURN = r"""
auto_scaling_instances:
  description: A description of the EC2 instances attached to an Auto Scaling group.
  returned: always
  type: list
  contains:
    availability_zone:
      description: The availability zone that the instance is in.
      returned: always
      type: str
      sample: "us-east-1a"
    health_status:
      description: The last reported health status of the instance.
      returned: always
      type: str
      sample: "Healthy"
    instance_id:
      description: The ID of the instance.
      returned: always
      type: str
      sample: "i-123456789abcdef01"
    instance_type:
      description: The instance type of the instance.
      returned: always
      type: str
      sample: "t3.micro"
    launch_configuration_name:
      description: The name of the launch configuration used when launching the instance.
      returned: When the instance was launched using an Auto Scaling launch configuration.
      type: str
      sample: "ansible-test-49630214-mchappel-thinkpadt14gen3-asg-instance-1"
    launch_template:
      description: A description of the launch template used when launching the instance.
      returned: When the instance was launched using an Auto Scaling launch template.
      type: dict
      contains:
        launch_template_id:
          description: The ID of the launch template used when launching the instance.
          returned: always
          type: str
          sample: "12345678-abcd-ef12-2345-6789abcdef01"
        launch_template_name:
          description: The name of the launch template used when launching the instance.
          returned: always
          type: str
          sample: "example-launch-configuration"
        version:
          description: The version of the launch template used when launching the instance.
          returned: always
          type: str
          sample: "$Default"
    lifecycle_state:
      description: The lifecycle state of the instance.
      returned: always
      type: str
      sample: "InService"
    protected_from_scale_in:
      description: Whether the instance is protected from termination when the Auto Scaling group is scaled in.
      returned: always
      type: bool
      sample: false
"""

from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import get_autoscaling_instances
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        group_name=dict(type="str"),
        instance_ids=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["instance_ids", "group_name"]],
    )

    client = module.client("autoscaling", retry_decorator=AWSRetry.jittered_backoff())

    instances = get_autoscaling_instances(
        client,
        instance_ids=module.params["instance_ids"],
        group_name=module.params["group_name"],
    )

    module.exit_json(changed=False, auto_scaling_instances=instances)


if __name__ == "__main__":
    main()

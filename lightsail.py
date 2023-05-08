#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lightsail
version_added: 1.0.0
short_description: Manage instances in AWS Lightsail
description:
  - Manage instances in AWS Lightsail.
  - Instance tagging is not yet supported in this module.
author:
  - "Nick Ball (@nickball)"
  - "Prasad Katti (@prasadkatti)"
options:
  state:
    description:
      - Indicate desired state of the target.
      - I(rebooted) and I(restarted) are aliases.
    default: present
    choices: ['present', 'absent', 'running', 'restarted', 'rebooted', 'stopped']
    type: str
  name:
    description: Name of the instance.
    required: true
    type: str
  zone:
    description:
      - AWS availability zone in which to launch the instance.
      - Required when I(state=present)
    type: str
  blueprint_id:
    description:
      - ID of the instance blueprint image.
      - Required when I(state=present)
    type: str
  bundle_id:
    description:
      - Bundle of specification info for the instance.
      - Required when I(state=present).
    type: str
  user_data:
    description:
      - Launch script that can configure the instance with additional data.
    type: str
    default: ''
  public_ports:
    description:
      - A list of dictionaries to describe the ports to open for the specified instance.
    type: list
    elements: dict
    suboptions:
      from_port:
        description: The first port in a range of open ports on the instance.
        type: int
        required: true
      to_port:
        description: The last port in a range of open ports on the instance.
        type: int
        required: true
      protocol:
        description: The IP protocol name accepted for the defined range of open ports.
        type: str
        choices: ['tcp', 'all', 'udp', 'icmp']
        required: true
      cidrs:
        description:
          - The IPv4 address, or range of IPv4 addresses (in CIDR notation) that are allowed to connect to the instance through the ports, and the protocol.
          - One of I(cidrs) or I(ipv6_cidrs) must be specified.
        type: list
        elements: str
      ipv6_cidrs:
        description:
          - The IPv6 address, or range of IPv6 addresses (in CIDR notation) that are allowed to connect to the instance through the ports, and the protocol.
          - One of I(cidrs) or I(ipv6_cidrs) must be specified.
        type: list
        elements: str
    version_added: 6.0.0
  key_pair_name:
    description:
      - Name of the key pair to use with the instance.
      - If I(state=present) and a key_pair_name is not provided, the default keypair from the region will be used.
    type: str
  wait:
    description:
      - Wait for the instance to be in state 'running' before returning.
      - If I(wait=false) an ip_address may not be returned.
      - Has no effect when I(state=rebooted) or I(state=absent).
    type: bool
    default: true
  wait_timeout:
    description:
      - How long before I(wait) gives up, in seconds.
    default: 300
    type: int

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Create a new Lightsail instance
  community.aws.lightsail:
    state: present
    name: my_instance
    region: us-east-1
    zone: us-east-1a
    blueprint_id: ubuntu_16_04
    bundle_id: nano_1_0
    key_pair_name: id_rsa
    user_data: " echo 'hello world' > /home/ubuntu/test.txt"
    public_ports:
      - from_port: 22
        to_port: 22
        protocol: "tcp"
        cidrs: ["0.0.0.0/0"]
        ipv6_cidrs: ["::/0"]
  register: my_instance

- name: Delete an instance
  community.aws.lightsail:
    state: absent
    region: us-east-1
    name: my_instance
"""

RETURN = r"""
changed:
  description: if a snapshot has been modified/created
  returned: always
  type: bool
  sample:
    changed: true
instance:
  description: instance data
  returned: always
  type: dict
  sample:
    arn: "arn:aws:lightsail:us-east-1:123456789012:Instance/1fef0175-d6c8-480e-84fa-214f969cda87"
    blueprint_id: "ubuntu_16_04"
    blueprint_name: "Ubuntu"
    bundle_id: "nano_1_0"
    created_at: "2017-03-27T08:38:59.714000-04:00"
    hardware:
      cpu_count: 1
      ram_size_in_gb: 0.5
    is_static_ip: false
    location:
      availability_zone: "us-east-1a"
      region_name: "us-east-1"
    name: "my_instance"
    networking:
      monthly_transfer:
        gb_per_month_allocated: 1024
      ports:
        - access_direction: "inbound"
          access_from: "Anywhere (0.0.0.0/0)"
          access_type: "public"
          common_name: ""
          from_port: 80
          protocol: tcp
          to_port: 80
        - access_direction: "inbound"
          access_from: "Anywhere (0.0.0.0/0)"
          access_type: "public"
          common_name: ""
          from_port: 22
          protocol: tcp
          to_port: 22
    private_ip_address: "172.26.8.14"
    public_ip_address: "34.207.152.202"
    resource_type: "Instance"
    ssh_key_name: "keypair"
    state:
      code: 16
      name: running
    support_code: "123456789012/i-0997c97831ee21e33"
    username: "ubuntu"
"""

import time

try:
    import botocore
except ImportError:
    # will be caught by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def find_instance_info(module, client, instance_name, fail_if_not_found=False):
    try:
        res = client.get_instance(instanceName=instance_name)
    except is_boto3_error_code("NotFoundException") as e:
        if fail_if_not_found:
            module.fail_json_aws(e)
        return None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)
    return res["instance"]


def wait_for_instance_state(module, client, instance_name, states):
    """
    `states` is a list of instance states that we are waiting for.
    """

    wait_timeout = module.params.get("wait_timeout")
    wait_max = time.time() + wait_timeout
    while wait_max > time.time():
        try:
            instance = find_instance_info(module, client, instance_name)
            if instance["state"]["name"] in states:
                break
            time.sleep(5)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
    else:
        module.fail_json(
            msg=f'Timed out waiting for instance "{instance_name}" to get to one of the following states - {states}'
        )


def update_public_ports(module, client, instance_name):
    try:
        client.put_instance_public_ports(
            portInfos=snake_dict_to_camel_dict(module.params.get("public_ports")),
            instanceName=instance_name,
        )
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)


def create_or_update_instance(module, client, instance_name):
    inst = find_instance_info(module, client, instance_name)

    if not inst:
        create_params = {
            "instanceNames": [instance_name],
            "availabilityZone": module.params.get("zone"),
            "blueprintId": module.params.get("blueprint_id"),
            "bundleId": module.params.get("bundle_id"),
            "userData": module.params.get("user_data"),
        }

        key_pair_name = module.params.get("key_pair_name")
        if key_pair_name:
            create_params["keyPairName"] = key_pair_name

        try:
            client.create_instances(**create_params)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)

        wait = module.params.get("wait")
        if wait:
            desired_states = ["running"]
            wait_for_instance_state(module, client, instance_name, desired_states)

    if module.params.get("public_ports") is not None:
        update_public_ports(module, client, instance_name)
    after_update_inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    module.exit_json(
        changed=after_update_inst != inst,
        instance=camel_dict_to_snake_dict(after_update_inst),
    )


def delete_instance(module, client, instance_name):
    changed = False

    inst = find_instance_info(module, client, instance_name)
    if inst is None:
        module.exit_json(changed=changed, instance={})

    # Wait for instance to exit transition state before deleting
    desired_states = ["running", "stopped"]
    wait_for_instance_state(module, client, instance_name, desired_states)

    try:
        client.delete_instance(instanceName=instance_name)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(inst))


def restart_instance(module, client, instance_name):
    """
    Reboot an existing instance
    Wait will not apply here as this is an OS-level operation
    """

    changed = False

    inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    try:
        client.reboot_instance(instanceName=instance_name)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(inst))


def start_or_stop_instance(module, client, instance_name, state):
    """
    Start or stop an existing instance
    """

    changed = False

    inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    # Wait for instance to exit transition state before state change
    desired_states = ["running", "stopped"]
    wait_for_instance_state(module, client, instance_name, desired_states)

    # Try state change
    if inst and inst["state"]["name"] != state:
        try:
            if state == "running":
                client.start_instance(instanceName=instance_name)
            else:
                client.stop_instance(instanceName=instance_name)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        changed = True
        # Grab current instance info
        inst = find_instance_info(module, client, instance_name)

    wait = module.params.get("wait")
    if wait:
        desired_states = [state]
        wait_for_instance_state(module, client, instance_name, desired_states)
        inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(inst))


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(
            type="str", default="present", choices=["present", "absent", "stopped", "running", "restarted", "rebooted"]
        ),
        zone=dict(type="str"),
        blueprint_id=dict(type="str"),
        bundle_id=dict(type="str"),
        key_pair_name=dict(type="str"),
        user_data=dict(type="str", default=""),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(default=300, type="int"),
        public_ports=dict(
            type="list",
            elements="dict",
            options=dict(
                from_port=dict(type="int", required=True),
                to_port=dict(type="int", required=True),
                protocol=dict(type="str", choices=["tcp", "all", "udp", "icmp"], required=True),
                cidrs=dict(type="list", elements="str"),
                ipv6_cidrs=dict(type="list", elements="str"),
            ),
            required_one_of=[("cidrs", "ipv6_cidrs")],
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, required_if=[["state", "present", ("zone", "blueprint_id", "bundle_id")]]
    )

    client = module.client("lightsail")

    name = module.params.get("name")
    state = module.params.get("state")

    if state == "present":
        create_or_update_instance(module, client, name)
    elif state == "absent":
        delete_instance(module, client, name)
    elif state in ("running", "stopped"):
        start_or_stop_instance(module, client, name, state)
    elif state in ("restarted", "rebooted"):
        restart_instance(module, client, name)


if __name__ == "__main__":
    main()

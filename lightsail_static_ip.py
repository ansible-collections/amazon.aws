#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lightsail_static_ip
version_added: 4.1.0
short_description: Manage static IP addresses in AWS Lightsail
description:
  - Manage static IP addresses in AWS Lightsail.
author:
  - "Daniel Cotton (@danielcotton)"
options:
  state:
    description:
      - Describes the desired state.
    default: present
    choices: ['present', 'absent']
    type: str
  name:
    description: Name of the static IP.
    required: true
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Provision a Lightsail static IP
  community.aws.lightsail_static_ip:
    state: present
    name: my_static_ip
  register: my_ip

- name: Remove a static IP
  community.aws.lightsail_static_ip:
    state: absent
    name: my_static_ip
"""

RETURN = r"""
static_ip:
  description: static_ipinstance data
  returned: always
  type: dict
  sample:
    arn: "arn:aws:lightsail:ap-southeast-2:123456789012:StaticIp/d8f47672-c261-4443-a484-4a2ec983db9a"
    created_at: "2021-02-28T00:04:05.202000+10:30"
    ip_address: "192.0.2.5"
    is_attached: false
    location:
        availability_zone: all
        region_name: ap-southeast-2
    name: "static_ip"
    resource_type: StaticIp
    support_code: "123456789012/192.0.2.5"
"""

try:
    import botocore
except ImportError:
    # will be caught by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def find_static_ip_info(module, client, static_ip_name, fail_if_not_found=False):
    try:
        res = client.get_static_ip(staticIpName=static_ip_name)
    except is_boto3_error_code("NotFoundException") as e:
        if fail_if_not_found:
            module.fail_json_aws(e)
        return None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)
    return res["staticIp"]


def create_static_ip(module, client, static_ip_name):
    inst = find_static_ip_info(module, client, static_ip_name)
    if inst:
        module.exit_json(changed=False, static_ip=camel_dict_to_snake_dict(inst))
    else:
        create_params = {"staticIpName": static_ip_name}

        try:
            client.allocate_static_ip(**create_params)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)

        inst = find_static_ip_info(module, client, static_ip_name, fail_if_not_found=True)

        module.exit_json(changed=True, static_ip=camel_dict_to_snake_dict(inst))


def delete_static_ip(module, client, static_ip_name):
    inst = find_static_ip_info(module, client, static_ip_name)
    if inst is None:
        module.exit_json(changed=False, static_ip={})

    changed = False
    try:
        client.release_static_ip(staticIpName=static_ip_name)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed, static_ip=camel_dict_to_snake_dict(inst))


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    client = module.client("lightsail")

    name = module.params.get("name")
    state = module.params.get("state")

    if state == "present":
        create_static_ip(module, client, name)
    elif state == "absent":
        delete_static_ip(module, client, name)


if __name__ == "__main__":
    main()

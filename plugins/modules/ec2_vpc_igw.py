#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_igw
version_added: 1.0.0
short_description: Manage an AWS VPC Internet gateway
description:
    - Manage an AWS VPC Internet gateway.
author: Robert Estelle (@erydo)
options:
  internet_gateway_id:
    version_added: 7.0.0
    description:
      - The ID of Internet Gateway to manage.
    required: false
    type: str
  vpc_id:
    description:
      - The VPC ID for the VPC to attach (when O(state=present)).
      - VPC ID can also be provided to find the internet gateway to manage that the VPC is attached to.
    required: false
    type: str
  state:
    description:
      - Create or terminate the IGW.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  force_attach:
    version_added: 7.0.0
    description:
      - Force attaching VPC to O(vpc_id).
      - Setting this option to true will detach an existing VPC attachment and attach to the supplied O(vpc_id).
      - Ignored when O(state=absent).
      - O(vpc_id) must be specified when O(force_attach=true).
    default: false
    type: bool
  detach_vpc:
    version_added: 7.0.0
    description:
      - Remove attached VPC from gateway.
    default: false
    type: bool
notes:
- Support for O(purge_tags) was added in release 1.3.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{igw.gateway_id}} for use in setting up NATs etc.
- name: Create Internet gateway
  amazon.aws.ec2_vpc_igw:
    vpc_id: vpc-abcdefgh
    state: present
  register: igw

- name: Create Internet gateway with tags
  amazon.aws.ec2_vpc_igw:
    vpc_id: vpc-abcdefgh
    state: present
    tags:
      Tag1: tag1
      Tag2: tag2
  register: igw

- name: Create a detached gateway
  amazon.aws.ec2_vpc_igw:
    state: present
  register: igw

- name: Change the VPC the gateway is attached to
  amazon.aws.ec2_vpc_igw:
    internet_gateway_id: igw-abcdefgh
    vpc_id: vpc-stuvwxyz
    force_attach: true
    state: present
  register: igw

- name: Delete Internet gateway using the attached vpc id
  amazon.aws.ec2_vpc_igw:
    state: absent
    vpc_id: vpc-abcdefgh
  register: vpc_igw_delete

- name: Delete Internet gateway with gateway id
  amazon.aws.ec2_vpc_igw:
    state: absent
    internet_gateway_id: igw-abcdefgh
  register: vpc_igw_delete

- name: Delete Internet gateway ensuring attached VPC is correct
  amazon.aws.ec2_vpc_igw:
    state: absent
    internet_gateway_id: igw-abcdefgh
    vpc_id: vpc-abcdefgh
  register: vpc_igw_delete
"""

RETURN = r"""
changed:
  description: If any changes have been made to the Internet Gateway.
  type: bool
  returned: always
  sample:
    changed: false
gateway_id:
  description: The unique identifier for the Internet Gateway.
  type: str
  returned: O(state=present)
  sample:
    gateway_id: "igw-XXXXXXXX"
tags:
  description: The tags associated the Internet Gateway.
  type: dict
  returned: O(state=present)
  sample:
    tags:
      "Ansible": "Test"
vpc_id:
  description: The VPC ID associated with the Internet Gateway.
  type: str
  returned: O(state=present)
  sample:
    vpc_id: "vpc-XXXXXXXX"
"""

from typing import Any
from typing import Dict
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import attach_internet_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_internet_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_internet_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_internet_gateways
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpcs
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import detach_internet_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


class AnsibleEc2Igw:
    def __init__(self, module: AnsibleAWSModule) -> None:
        self._module = module
        self._results = {"changed": False}
        self._connection = self._module.client("ec2")
        self._check_mode = self._module.check_mode

    def process(self) -> None:
        internet_gateway_id = self._module.params.get("internet_gateway_id")
        vpc_id = self._module.params.get("vpc_id")
        state = self._module.params.get("state", "present")
        tags = self._module.params.get("tags")
        purge_tags = self._module.params.get("purge_tags")
        force_attach = self._module.params.get("force_attach")
        detach_vpc = self._module.params.get("detach_vpc")

        if state == "present":
            self.ensure_igw_present(internet_gateway_id, vpc_id, tags, purge_tags, force_attach, detach_vpc)
        elif state == "absent":
            self.ensure_igw_absent(internet_gateway_id, vpc_id)
        self._module.exit_json(**self._results)

    def get_matching_igw(self, vpc_id: str, gateway_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Returns the internet gateway found.
            Parameters:
                vpc_id (str): VPC ID
                gateway_id (str): Internet Gateway ID, if specified
            Returns:
                igw (dict): dict of igw found, None if none found
        """

        # If we know the gateway_id, use it to avoid bugs with using filters
        # See https://github.com/ansible-collections/amazon.aws/pull/766
        params = (
            {"InternetGatewayIds": [gateway_id]}
            if gateway_id
            else {"Filters": ansible_dict_to_boto3_filter_list({"attachment.vpc-id": vpc_id})}
        )

        igw = None
        igws = describe_internet_gateways(self._connection, **params)
        if igws:
            if len(igws) > 1:
                self._module.fail_json(msg=f"EC2 returned more than one Internet Gateway for VPC {vpc_id}, aborting")
            igw = camel_dict_to_snake_dict(igws[0])
        return igw

    def get_matching_vpc(self, vpc_id: str) -> Dict[str, Any]:
        """
        Returns the virtual private cloud found.
            Parameters:
                vpc_id (str): VPC ID
            Returns:
                vpc (dict): dict of vpc found, None if none found
        """
        vpcs = describe_vpcs(self._connection, VpcIds=[vpc_id])
        if not vpcs:
            self._module.fail_json(msg=f"VPC with Id {vpc_id} not found, aborting")

        if len(vpcs) > 1:
            self._module.fail_json(msg=f"EC2 returned more than one VPC for {vpc_id}, aborting")
        return camel_dict_to_snake_dict(vpcs[0])

    @staticmethod
    def get_igw_info(igw, vpc_id):
        return {
            "gateway_id": igw["internet_gateway_id"],
            "tags": boto3_tag_list_to_ansible_dict(igw["tags"]),
            "vpc_id": vpc_id,
        }

    def attach_vpc(self, igw_id, vpc_id):
        self._results["changed"] |= attach_internet_gateway(self._connection, internet_gateway_id=igw_id, vpc_id=vpc_id)
        wait_for_resource_state(
            self._connection, self._module, "internet_gateway_attached", InternetGatewayIds=[igw_id]
        )

    def ensure_igw_absent(self, igw_id, vpc_id):
        igw = self.get_matching_igw(vpc_id, gateway_id=igw_id)
        if igw is None:
            return self._results

        igw_vpc_id = ""

        if len(igw["attachments"]) > 0:
            igw_vpc_id = igw["attachments"][0]["vpc_id"]

        if vpc_id and (igw_vpc_id != vpc_id):
            self._module.fail_json(msg=f"Supplied VPC ({vpc_id}) does not match found VPC ({igw_vpc_id}), aborting")

        if self._check_mode:
            self._results["changed"] = True
            return self._results

        if igw_vpc_id:
            self._results["changed"] |= detach_internet_gateway(
                self._connection, internet_gateway_id=igw["internet_gateway_id"], vpc_id=igw_vpc_id
            )

        self._results["changed"] |= delete_internet_gateway(self._connection, igw["internet_gateway_id"])

        return self._results

    def ensure_igw_present(self, igw_id, vpc_id, tags, purge_tags, force_attach, detach_vpc):
        igw = None

        if igw_id:
            igw = self.get_matching_igw(None, gateway_id=igw_id)
        elif vpc_id:
            igw = self.get_matching_igw(vpc_id)

        if igw is None:
            if self._check_mode:
                self._results["changed"] = True
                self._results["gateway_id"] = None
                return self._results

            if vpc_id:
                self.get_matching_vpc(vpc_id)

            response = create_internet_gateway(self._connection, tags=tags)
            self._results["changed"] = True
            # Ensure the gateway exists before trying to attach it or add tags
            wait_for_resource_state(
                self._connection,
                self._module,
                "internet_gateway_exists",
                InternetGatewayIds=[response["InternetGatewayId"]],
            )

            igw = camel_dict_to_snake_dict(response)

            if vpc_id:
                self.attach_vpc(igw["internet_gateway_id"], vpc_id)
        else:
            igw_vpc_id = None

            if len(igw["attachments"]) > 0:
                igw_vpc_id = igw["attachments"][0]["vpc_id"]

                if detach_vpc:
                    if self._check_mode:
                        self._results["changed"] = True
                        self._results["gateway_id"] = igw["internet_gateway_id"]
                        return self._results

                    self._results["changed"] |= detach_internet_gateway(
                        self._connection, internet_gateway_id=igw["internet_gateway_id"], vpc_id=igw_vpc_id
                    )

                elif igw_vpc_id != vpc_id:
                    if self._check_mode:
                        self._results["changed"] = True
                        self._results["gateway_id"] = igw["internet_gateway_id"]
                        return self._results

                    if force_attach:
                        self.get_matching_vpc(vpc_id)

                        self._results["changed"] |= detach_internet_gateway(
                            self._connection, internet_gateway_id=igw["internet_gateway_id"], vpc_id=igw_vpc_id
                        )
                        self.attach_vpc(igw["internet_gateway_id"], vpc_id)
                    else:
                        self._module.fail_json(msg="VPC already attached, but does not match requested VPC.")

            elif vpc_id:
                if self._check_mode:
                    self._results["changed"] = True
                    self._results["gateway_id"] = igw["internet_gateway_id"]
                    return self._results

                self.get_matching_vpc(vpc_id)
                self.attach_vpc(igw["internet_gateway_id"], vpc_id)

        # Modify tags
        self._results["changed"] |= ensure_ec2_tags(
            self._connection,
            self._module,
            igw["internet_gateway_id"],
            resource_type="internet-gateway",
            tags=tags,
            purge_tags=purge_tags,
            retry_codes="InvalidInternetGatewayID.NotFound",
        )

        # Update igw
        igw = self.get_matching_igw(vpc_id, gateway_id=igw["internet_gateway_id"])
        igw_info = self.get_igw_info(igw, vpc_id)
        self._results.update(igw_info)

        return self._results


def main() -> None:
    argument_spec = dict(
        internet_gateway_id=dict(),
        vpc_id=dict(),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        force_attach=dict(default=False, type="bool"),
        detach_vpc=dict(default=False, type="bool"),
    )

    required_if = [
        ("force_attach", True, ("vpc_id",), False),
        ("state", "absent", ("internet_gateway_id", "vpc_id"), True),
        ("detach_vpc", True, ("internet_gateway_id", "vpc_id"), True),
    ]

    mutually_exclusive = [("force_attach", "detach_vpc")]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
    )

    igw_manager = AnsibleEc2Igw(module=module)
    try:
        igw_manager.process()
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

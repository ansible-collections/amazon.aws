#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_vgw
short_description: Create and delete AWS VPN Virtual Gateways
version_added: 1.0.0
version_added_collection: community.aws
description:
  - Creates AWS VPN Virtual Gateways.
  - Deletes AWS VPN Virtual Gateways.
  - Attaches Virtual Gateways to VPCs.
  - Detaches Virtual Gateways from VPCs.
options:
  state:
    description:
      - V(present) to ensure resource is created.
      - V(absent) to remove resource.
    default: present
    choices: [ "present", "absent"]
    type: str
  name:
    description:
      - Name of the VGW to be created or deleted.
    type: str
  type:
    description:
      - Type of the virtual gateway to be created.
    choices: [ "ipsec.1" ]
    default: "ipsec.1"
    type: str
  vpn_gateway_id:
    description:
      - VPN gateway ID of an existing virtual gateway.
    type: str
  vpc_id:
    description:
      - The ID of a VPC to attach or detach to the VGW.
    type: str
  asn:
    description:
      - The BGP ASN on the Amazon side.
    type: int
  wait_timeout:
    description:
      - Number of seconds to wait for status during VPC attach and detach.
    default: 320
    type: int
notes:
  - Support for O(purge_tags) was added in release 4.0.0.
author:
  - Nick Aslanidis (@naslanidis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create a new VGW attached to a specific VPC
  amazon.aws.ec2_vpc_vgw:
    state: present
    region: ap-southeast-2
    profile: personal
    vpc_id: vpc-12345678
    name: personal-testing
    type: ipsec.1

- name: Create a new unattached VGW
  amazon.aws.ec2_vpc_vgw:
    state: present
    region: ap-southeast-2
    profile: personal
    name: personal-testing
    type: ipsec.1
    tags:
      environment: production
      owner: ABC

- name: Remove a new VGW using the name
  amazon.aws.ec2_vpc_vgw:
    state: absent
    region: ap-southeast-2
    profile: personal
    name: personal-testing
    type: ipsec.1

- name: Remove a new VGW using the vpn_gateway_id
  amazon.aws.ec2_vpc_vgw:
    state: absent
    region: ap-southeast-2
    profile: personal
    vpn_gateway_id: vgw-3a9aa123

- name: Detach vpn gateway from VPC
  amazon.aws.ec2_vpc_vgw:
    state: present
    name: "{{ vgw_name }}"
    register: vgw

- name: Delete vpn gateway
  amazon.aws.ec2_vpc_vgw:
    state: absent
    vpn_gateway_id: '{{ vgw.vgw.id | default(vgw_id) }}'
    ignore_errors: true
"""

RETURN = r"""
vgw:
  description: Information about the virtual private gateway.
  returned: success
  type: dict
  contains:
    id:
      description: The ID of the virtual private gateway.
      type: str
      returned: success
      sample: "vgw-0123456789abcdef0"
    state:
      description: The current state of the virtual private gateway.
      type: str
      returned: success
      sample: "available"
    tags:
      description: A dictionary representing the tags attached to the virtual private gateway.
      type: dict
      returned: success
      sample: {
                    "Name": "ansible-test-ec2-vpc-vgw",
                    "Env": "Dev_Test_001"
                }
    type:
      description: The type of VPN connection the virtual private gateway supports.
      type: str
      returned: success
      sample: "ipsec.1"
    vpc_id:
      description: The ID of the VPC.
      type: str
      returned: success
      sample: "vpc-123456789abcdef01"
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import attach_vpn_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_vpn_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_vpn_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpcs
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpn_gateways
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import detach_vpn_gateway
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


# AWS uses VpnGatewayLimitExceeded for both 'Too many VGWs' and 'Too many concurrent changes'
# we need to look at the mesage to tell the difference.
class VGWRetry(AWSRetry):
    @staticmethod
    def status_code_from_exception(error: Any) -> Tuple[str, str]:
        return (
            error.response["Error"]["Code"],
            error.response["Error"]["Message"],
        )

    @staticmethod
    def found(response_code: Union[str, Tuple[str, ...]], catch_extra_error_codes: Optional[List[str]] = None) -> bool:
        retry_on = ["The maximum number of mutating objects has been reached."]

        if catch_extra_error_codes:
            retry_on.extend(catch_extra_error_codes)
        if not isinstance(response_code, tuple):
            response_code = (response_code,)

        for code in response_code:
            if super(VGWRetry, VGWRetry).found(response_code, catch_extra_error_codes):
                return True

        return False


def format_vgw_info(vgw: Dict) -> Optional[Dict[str, Any]]:
    # to handle check mode case where vgw passed to this function is {}
    if not vgw:
        return

    vgw_info = {
        "id": vgw["VpnGatewayId"],
        "type": vgw["Type"],
        "state": vgw["State"],
        "vpc_id": None,
        "tags": dict(),
    }

    if vgw["Tags"]:
        vgw_info["tags"] = boto3_tag_list_to_ansible_dict(vgw["Tags"])

    if len(vgw["VpcAttachments"]) != 0 and vgw["VpcAttachments"][0]["State"] == "attached":
        vgw_info["vpc_id"] = vgw["VpcAttachments"][0]["VpcId"]

    return vgw_info


def wait_for_status(client, module: AnsibleAWSModule, vpn_gateway_id: str, desired_status: str) -> Tuple[bool, Any]:
    polling_increment_secs = 15
    max_retries = module.params.get("wait_timeout") // polling_increment_secs
    try:
        wait_for_resource_state(client, module, "vpn_gateway_exists", VpnGatewayIds=[vpn_gateway_id])
        if desired_status not in ("attached", "detached"):
            module.fail_json(msg=f"Unsupported status: {desired_status}")
        wait_for_resource_state(
            client,
            module,
            f"vpn_gateway_{desired_status}",
            VpnGatewayIds=[vpn_gateway_id],
            delay=polling_increment_secs,
            max_attempts=max_retries,
        )

        response = find_vgw(client, module, vpn_gateway_id)
        status_achieved = response[0]["VpcAttachments"][0]["State"] == desired_status

    except AnsibleEC2Error as e:
        module.fail_json_aws(e)

    return status_achieved, response


def attach_vgw_to_vpc(client, module: AnsibleAWSModule, vpn_gateway_id: str) -> bool:
    if module.check_mode:
        return True
    response = None
    vpc_id = module.params.get("vpc_id")
    response = attach_vpn_gateway(client, vpc_id, vpn_gateway_id)
    status_achieved, vgw = wait_for_status(client, module, vpn_gateway_id, "attached")

    if not status_achieved:
        module.fail_json(msg="Error waiting for VPC to attach to VGW - please check the AWS console")

    return response


def detach_vgw(client, module: AnsibleAWSModule, vpn_gateway_id: str, vpc_id: Optional[str] = None) -> bool:
    if module.check_mode:
        return True
    response = None
    vpc_id = vpc_id or module.params.get("vpc_id")

    response = detach_vpn_gateway(client, vpc_id, vpn_gateway_id)

    status_achieved, vgw = wait_for_status(client, module, vpn_gateway_id, "detached")
    if not status_achieved:
        module.fail_json(msg="Error waiting for  vpc to detach from vgw - please check the AWS console")

    return response


def create_vgw(client, module: AnsibleAWSModule) -> Dict:
    if module.check_mode:
        return {}

    params = {
        "Type": module.params.get("type"),
        "TagSpecifications": boto3_tag_specifications(
            {**(module.params.get("tags") or {}), "Name": module.params.get("name")}, ["vpn-gateway"]
        ),
    }

    if module.params.get("asn"):
        params["AmazonSideAsn"] = module.params.get("asn")

    try:
        create_vgw_result = create_vpn_gateway(client, **params)
        get_waiter(client, "vpn_gateway_exists").wait(VpnGatewayIds=[create_vgw_result["VpnGatewayId"]])
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(
            e, msg=f"Failed to wait for Vpn Gateway {create_vgw_result['VpnGatewayId']} to be available"
        )

    return create_vgw_result


def delete_vgw(client, module: AnsibleAWSModule, vpn_gateway_id: str) -> Optional[str]:
    delete_vpn_gateway(client, vpn_gateway_id)

    # return the deleted VpnGatewayId as this is not included in the above response
    result = vpn_gateway_id
    return result


def find_vpc(client, module: AnsibleAWSModule) -> Optional[Any]:
    response = None
    params = dict()
    vpc_id = module.params.get("vpc_id")

    if vpc_id:
        params["VpcIds"] = [vpc_id]
        response = describe_vpcs(client, **params)

    return response


def find_vgw(client, module: AnsibleAWSModule, vpn_gateway_id: Optional[str] = None) -> List[Dict[str, Any]]:
    params = dict()
    if vpn_gateway_id:
        params["VpnGatewayIds"] = [vpn_gateway_id]
    else:
        params["Filters"] = [
            {"Name": "type", "Values": [module.params.get("type")]},
            {"Name": "tag:Name", "Values": [module.params.get("name")]},
        ]
        if module.params.get("state") == "present":
            params["Filters"].append({"Name": "state", "Values": ["pending", "available"]})

    response = describe_vpn_gateways(client, **params)

    return sorted(response, key=lambda k: k["VpnGatewayId"])


def ensure_vgw_present(client, module: AnsibleAWSModule) -> Tuple[bool, Dict[str, Any]]:
    changed = False
    vgw = {}

    # Check if provided vgw already exists
    existing_vgw = find_vgw(client, module, module.params.get("vpn_gateway_id"))

    # if existing vgw, handle changes as required
    if existing_vgw:
        changed |= handle_existing_vgw(client, module, existing_vgw[0])
        vgw = find_vgw(client, module, existing_vgw[0]["VpnGatewayId"])[
            0
        ]  # [0] as find_vgw returns list[dict] i.e. [{vgw_info}] as it is possible to have multiple vgw with same names
    # if not existing vgw, create new and return
    else:
        changed = True
        if not module.check_mode:
            vgw = create_vgw(client, module)
            # if vpc_id provided, attach vgw to vpc
            if module.params.get("vpc_id"):
                attach_vgw_to_vpc(client, module, vgw["VpnGatewayId"])
            vgw = find_vgw(client, module, vgw["VpnGatewayId"])[0]

    return changed, format_vgw_info(vgw)


def handle_existing_vgw(client, module: AnsibleAWSModule, existing_vgw: dict) -> bool:
    changed = False
    vpn_gateway_id = existing_vgw["VpnGatewayId"]
    provided_vpc_id = module.params.get("vpc_id")

    # Update tags
    desired_tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    if desired_tags is None:
        desired_tags = dict()
        purge_tags = False
    tags = dict(Name=module.params.get("name"))
    tags.update(desired_tags)
    # check_mode is handled by esure_ec2_tags()
    changed |= ensure_ec2_tags(
        client, module, vpn_gateway_id, resource_type="vpn-gateway", tags=tags, purge_tags=purge_tags
    )

    # Manage VPC attachments
    current_vpc_attachments = existing_vgw["VpcAttachments"]
    if provided_vpc_id:
        # if vgw is attached to a vpc
        if current_vpc_attachments and current_vpc_attachments[0]["State"] == "attached":
            # if provided vpc is differenct than current vpc, then detach current vpc, attach new vpc
            if provided_vpc_id != current_vpc_attachments[0]["VpcId"]:
                if module.check_mode:
                    return True
                detach_vgw(client, module, vpn_gateway_id, current_vpc_attachments[0]["VpcId"])
                get_waiter(client, "vpn_gateway_detached").wait(VpnGatewayIds=[vpn_gateway_id])
                attach_vgw_to_vpc(client, module, vpn_gateway_id)
                changed = True
        # if vgw is not currently attached to a vpc, attach it to provided vpc
        else:
            if module.check_mode:
                return True
            attach_vgw_to_vpc(client, module, vpn_gateway_id)
            changed = True
    # if vpc_id not provided, then detach vgw from vpc
    else:
        if current_vpc_attachments and current_vpc_attachments[0]["State"] == "attached":
            if module.check_mode:
                return True
            detach_vgw(client, module, vpn_gateway_id, current_vpc_attachments[0]["VpcId"])
            changed = True

    return changed


def ensure_vgw_absent(client, module: AnsibleAWSModule) -> Tuple[bool, Optional[str]]:
    # If an existing vgw name and type matches our args, then a match is considered to have been
    # found and we will take steps to delete it.

    changed = False
    params = dict()
    result = dict()
    deleted_vgw = None
    params["Name"] = module.params.get("name")
    params["VpcId"] = module.params.get("vpc_id")
    params["Type"] = module.params.get("type")
    params["Tags"] = module.params.get("tags")
    params["VpnGatewayIds"] = module.params.get("vpn_gateway_id")
    vpn_gateway_id = module.params.get("vpn_gateway_id")

    # check if a gateway matching our module args already exists
    if params["VpnGatewayIds"]:
        existing_vgw_with_id = find_vgw(client, module, module.params.get("vpn_gateway_id"))
        if existing_vgw_with_id != [] and existing_vgw_with_id[0]["State"] != "deleted":
            if module.check_mode:
                return True, existing_vgw_with_id[0]["VpnGatewayId"]
            existing_vgw = existing_vgw_with_id
            if existing_vgw[0]["VpcAttachments"] != [] and existing_vgw[0]["VpcAttachments"][0]["State"] == "attached":
                if params["VpcId"]:
                    if params["VpcId"] != existing_vgw[0]["VpcAttachments"][0]["VpcId"]:
                        module.fail_json(
                            msg="The vpc-id provided does not match the vpc-id currently attached - please check the AWS console"
                        )

                    else:
                        # detach the vpc from the vgw
                        detach_vgw(client, module, params["VpnGatewayIds"], params["VpcId"])
                        deleted_vgw = delete_vgw(client, module, params["VpnGatewayIds"])
                        changed = True

                else:
                    # attempt to detach any attached vpcs
                    for vpc in existing_vgw[0]["VpcAttachments"]:
                        detach_vgw(client, module, vpn_gateway_id, vpc["VpcId"])
                    deleted_vgw = delete_vgw(client, module, params["VpnGatewayIds"])
                    changed = True

            else:
                # no vpc's are attached so attempt to delete the vgw
                deleted_vgw = delete_vgw(client, module, params["VpnGatewayIds"])
                changed = True

        else:
            changed = False
            deleted_vgw = "Nothing to do"

    else:
        # Check that a name and type argument has been supplied if no vgw-id
        if not module.params.get("name") or not module.params.get("type"):
            module.fail_json(msg="A name and type is required when no vgw-id and a status of 'absent' is supplied")

        existing_vgw = find_vgw(client, module)
        if existing_vgw != [] and existing_vgw[0]["State"] != "deleted":
            vpn_gateway_id = existing_vgw[0]["VpnGatewayId"]
            if existing_vgw[0]["VpcAttachments"] != [] and existing_vgw[0]["VpcAttachments"][0]["State"] == "attached":
                if params["VpcId"]:
                    if params["VpcId"] != existing_vgw[0]["VpcAttachments"][0]["VpcId"]:
                        module.fail_json(
                            msg="The vpc-id provided does not match the vpc-id currently attached - please check the AWS console"
                        )

                    else:
                        if module.check_mode:
                            return True, None
                        # detach the vpc from the vgw
                        detach_vgw(client, module, vpn_gateway_id, params["VpcId"])

                        # now that the vpc has been detached, delete the vgw
                        deleted_vgw = delete_vgw(client, module, vpn_gateway_id)
                        changed = True

                else:
                    if module.check_mode:
                        return True, vpn_gateway_id
                    # attempt to detach any attached vpcs
                    vpc_to_detach = existing_vgw[0]["VpcAttachments"][0]["VpcId"]
                    detach_vgw(client, module, vpn_gateway_id, vpc_to_detach)
                    changed = True

                    # now that the vpc has been detached, delete the vgw
                    deleted_vgw = delete_vgw(client, module, vpn_gateway_id)

            else:
                if module.check_mode:
                    return True, vpn_gateway_id
                # no vpc's are attached so attempt to delete the vgw
                deleted_vgw = delete_vgw(client, module, vpn_gateway_id)
                changed = True

        else:
            changed = False
            deleted_vgw = None

    result = deleted_vgw
    return changed, result


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent"]),
        name=dict(),
        vpn_gateway_id=dict(),
        vpc_id=dict(),
        asn=dict(type="int"),
        wait_timeout=dict(type="int", default=320),
        type=dict(default="ipsec.1", choices=["ipsec.1"]),
        tags=dict(default=None, required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["name"]]],
        supports_check_mode=True,
    )
    state = module.params.get("state").lower()

    client = module.client("ec2")

    if state == "present":
        (changed, results) = ensure_vgw_present(client, module)
    else:
        (changed, results) = ensure_vgw_absent(client, module)
    module.exit_json(changed=changed, vgw=results)


if __name__ == "__main__":
    main()

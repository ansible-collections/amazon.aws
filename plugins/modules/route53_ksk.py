#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: route53_ksk
short_description: Manages a key-signing key (KSK)
version_added: 5.0.0
description:
    - Creates a new key-signing key (KSK) associated with a hosted zone.
      You can only have two KSKs per hosted zone.
    - Deletes a key-signing key (KSK). Before you can delete a KSK, you must deactivate it.
      The KSK must be deactivated before you can delete it regardless of whether the hosted
      zone is enabled for DNSSEC signing.
    - Activates a key-signing key (KSK) so that it can be used for signing by DNSSEC.
    - Deactivates a key-signing key (KSK) so that it will not be used for signing by DNSSEC.
options:
    state:
        description:
            - Whether or not the zone should exist or not.
        default: present
        choices: [ "present", "absent" ]
        type: str
    caller_reference:
        description:
            - A unique string that identifies the request.
        required: true
        type: str
    hosted_zone_id:
        description:
            - The unique string (ID) used to identify a hosted zone.
        type: str
        aliases: ["zone_id"]
    key_management_service_arn:
        description:
            - The Amazon resource name (ARN) for a customer managed key in Key Management Service (KMS).
        type: str
        aliases: ["kms_arn"]
    name:
        description:
            - A string used to identify a key-signing key (KSK).
        type: str
        required: true
    status:
        description:
            - A string specifying the initial status of the key-signing key (KSK).
              You can set the value to V(ACTIVE) or V(INACTIVE).
        type: str
        default: "ACTIVE"
    wait:
        description:
            - Wait until the changes have been replicated.
        type: bool
        default: false
    wait_timeout:
        description:
        - How long to wait for the changes to be replicated, in seconds.
        default: 300
        type: int
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
author:
    - Alina Buzachis (@alinabuzachis)
"""

EXAMPLES = r"""
- name: Create a Key Signing Key Request
  amazon.aws.route53_ksk:
    name: "{{ resource_prefix }}-ksk"
    hosted_zone_id: "{{ _hosted_zone.zone_id }}"
    key_management_service_arn: "{{ kms_key.key_arn }}"
    caller_reference: "{{ aws_caller_info.arn }}"
    status: "INACTIVE"
    state: present

- name: Activate KSK
  amazon.aws.route53_ksk:
    name: "{{ resource_prefix }}-ksk"
    hosted_zone_id: "{{ _hosted_zone.zone_id }}"
    key_management_service_arn: "{{ kms_key.key_arn }}"
    caller_reference: "{{ aws_caller_info.arn }}"
    status: "ACTIVE"
    state: present

- name: Delete KSK and deactivate it
  amazon.aws.route53_ksk:
    name: "{{ resource_prefix }}-ksk"
    hosted_zone_id: "{{ _hosted_zone.zone_id }}"
    status: "INACTIVE"
    state: absent
"""

RETURN = r"""
comment:
    description: Optional hosted zone comment.
    returned: when hosted zone exists
    type: str
    sample: "Private zone"
name:
    description: Hosted zone name.
    returned: when hosted zone exists
    type: str
    sample: "private.local."
private_zone:
    description: Whether hosted zone is private or public.
    returned: when hosted zone exists
    type: bool
    sample: true
vpc_id:
    description: Id of the first vpc attached to private hosted zone (use vpcs for associating multiple).
    returned: for private hosted zone
    type: str
    sample: "vpc-1d36c84f"
vpc_region:
    description: Region of the first vpc attached to private hosted zone (use vpcs for assocaiting multiple).
    returned: for private hosted zone
    type: str
    sample: "eu-west-1"
vpcs:
    version_added: 5.3.0
    description: The list of VPCs attached to the private hosted zone.
    returned: for private hosted zone
    type: list
    elements: dict
    sample: "[{'id': 'vpc-123456', 'region': 'us-west-2'}]"
    contains:
        id:
            description: ID of the VPC.
            returned: for private hosted zone
            type: str
            sample: "vpc-123456"
        region:
            description: Region of the VPC.
            returned: for private hosted zone
            type: str
            sample: "eu-west-2"
zone_id:
    description: Hosted zone id.
    returned: when hosted zone exists
    type: str
    sample: "Z6JQG9820BEFMW"
delegation_set_id:
    description: Id of the associated reusable delegation set.
    returned: for public hosted zones, if they have been associated with a reusable delegation set
    type: str
    sample: "A1BCDEF2GHIJKL"
tags:
    description: Tags associated with the zone.
    returned: when tags are defined
    type: dict
"""

import datetime

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


def deactivate(client, hosted_zone_id, name):
    return client.deactivate_key_signing_key(
        HostedZoneId=hosted_zone_id,
        Name=name
    )


def activate(client, hosted_zone_id, name):
    return client.activate_key_signing_key(
        HostedZoneId=hosted_zone_id,
        Name=name
    )


def wait(client, module, change_id):
    try:
        waiter = get_waiter(client, "resource_record_sets_changed")
        waiter.wait(
            Id=change_id,
            WaiterConfig=dict(
                Delay=5,
                MaxAttempts=module.params.get("wait_timeout") // 5,
            ),
        )
    except botocore.exceptions.WaiterError as e:
            module.fail_json_aws(e, msg="Timeout waiting for changes to be applied")


def create(client, module: AnsibleAWSModule):
    # The API does not raise KeySigningKeyAlreadyExists when a request with the same name and
    # KMS arn already exist. It will always try to create a new KSK request.
    changed: bool = True
    zone_id = module.params.get("hosted_zone_id")
    name = module.params.get("name")
    status = module.params.get("status")
    request_time = datetime.datetime.utcnow()

    response = client.create_key_signing_key(
        CallerReference=module.params.get("caller_reference"),
        KeyManagementServiceArn=module.params.get("key_management_service_arn"),
        HostedZoneId=zone_id,
        Name=name,
        Status=status
    )

    if response and response.get("ChangeInfo", {}):
        submitted_at = response["ChangeInfo"].get("SubmittedAt").replace(tzinfo=None)
        if submitted_at < request_time:
            # A KSK request already exists.
            if response["KeySigningKey"]["Status"] != status:
                # Wait before activating or deactivating to reach INSYNC state
                change_id = response["ChangeInfo"]["Id"]
                wait(client, module, change_id)

                if module.params.get("status") == "ACTIVE":
                    response = activate(client, zone_id, name)
                elif module.params.get('status') == "INACTIVE":
                    response = deactivate(client, zone_id, name)
                else:
                    changed = False

                if module.params.get("wait"):
                    change_id = response["ChangeInfo"]["Id"]
                    wait(client, module, change_id)
            else:
                changed = False

    return changed, response


def delete(client, module: AnsibleAWSModule):
    changed: bool = False
    zone_id = module.params.get("hosted_zone_id")
    name = module.params.get("name")

    if module.params.get('status') == "INACTIVE":
        # Deactivate the Key Signing Request before deleting
        result = deactivate(client, zone_id, name)
        change_id = result["ChangeInfo"]["Id"]
        wait(client, module, change_id)
    try:
        response = client.delete_key_signing_key(
            HostedZoneId=zone_id,
            Name=name
        )
        changed = True

        if module.params.get("wait"):
            change_id = response["ChangeInfo"]["Id"]
            wait(client, module, change_id)
    except is_boto3_error_code("NoSuchKeySigningKey"):
        pass

    return changed, response


def main() -> None:
    argument_spec = dict(
        caller_reference=dict(type="str"),
        hosted_zone_id=dict(type="str", aliases=["zone_id"], required=True),
        key_management_service_arn=dict(type="str", aliases=["kms_arn"]),
        name=dict(type="str", required=True),
        status=dict(type="str", default=["ACTIVE"], choices=["ACTIVE", "INACTIVE"]),
        state=dict(default="present", choices=["present", "absent"]),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=300),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["caller_reference", "key_management_service_arn"]]],
    )

    try:
        client = module.client("route53")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed = False
    state = module.params.get("state")

    try:
        if state == "present":
            changed, result = create(client, module)
        else:
            changed, result = delete(client, module)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    del result["ResponseMetadata"]
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


if __name__ == "__main__":
    main()

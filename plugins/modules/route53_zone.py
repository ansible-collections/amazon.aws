#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: route53_zone
short_description: add or delete Route 53 zones
version_added: 5.0.0
description:
    - Creates and deletes Route 53 private and public zones.
    - This module was originally added to C(community.aws) in release 1.0.0.
options:
    zone:
        description:
            - "The DNS zone record (eg: foo.com.)"
        required: true
        type: str
    state:
        description:
            - Whether or not the zone should exist or not.
        default: present
        choices: [ "present", "absent" ]
        type: str
    vpc_id:
        description:
            - The VPC ID the zone should be a part of (if this is going to be a private zone).
        type: str
    vpc_region:
        description:
            - The VPC Region the zone should be a part of (if this is going to be a private zone).
        type: str
    vpcs:
        version_added: 5.3.0
        description:
            - The VPCs the zone should be a part of (if this is going to be a private zone).
        type: list
        elements: dict
        suboptions:
            id:
                description:
                    - The ID of the VPC.
                type: str
                required: true
            region:
                description:
                    - The region of the VPC.
                type: str
                required: true
    comment:
        description:
            - Comment associated with the zone.
        default: ''
        type: str
    hosted_zone_id:
        description:
            - The unique zone identifier you want to delete or "all" if there are many zones with the same domain name.
            - Required if there are multiple zones identified with the above options.
        type: str
    delegation_set_id:
        description:
            - The reusable delegation set ID to be associated with the zone.
            - Note that you can't associate a reusable delegation set with a private hosted zone.
        type: str
    dnssec:
        description:
            - Enables DNSSEC signing in a specific hosted zone.
        type: bool
        default: false
        version_added: 9.2.0
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.tags
    - amazon.aws.boto3
notes:
    - Support for O(tags) and O(purge_tags) was added in release 2.1.0.
author:
    - "Christopher Troup (@minichate)"
"""

EXAMPLES = r"""
- name: create a public zone
  amazon.aws.route53_zone:
    zone: example.com
    comment: this is an example

- name: delete a public zone
  amazon.aws.route53_zone:
    zone: example.com
    state: absent

- name: create a private zone
  amazon.aws.route53_zone:
    zone: devel.example.com
    vpc_id: '{{ myvpc_id }}'
    vpc_region: us-west-2
    comment: developer domain

- name: create a private zone with multiple associated VPCs
  amazon.aws.route53_zone:
    zone: crossdevel.example.com
    vpcs:
      - id: vpc-123456
        region: us-west-2
      - id: vpc-000001
        region: us-west-2
    comment: developer cross-vpc domain

- name: create a public zone associated with a specific reusable delegation set
  amazon.aws.route53_zone:
    zone: example.com
    comment: reusable delegation set example
    delegation_set_id: A1BCDEF2GHIJKL

- name: create a public zone with tags
  amazon.aws.route53_zone:
    zone: example.com
    comment: this is an example
    tags:
      Owner: Ansible Team

- name: modify a public zone, removing all previous tags and adding a new one
  amazon.aws.route53_zone:
    zone: example.com
    comment: this is an example
    tags:
      Support: Ansible Community
    purge_tags: true
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
dnssec:
    description: Information about DNSSEC for a specific hosted zone.
    returned: when O(state=present) and the hosted zone is public
    version_added: 9.2.0
    type: dict
    contains:
        key_signing_key:
            description: The key-signing key (KSK) that the request creates.
            returned: when O(state=present)
            type: list
            elements: dict
            contains:
                name:
                    description: A string used to identify a key-signing key (KSK).
                    type: str
                kms_arn:
                    description: The Amazon resource name (ARN) used to identify the customer managed key in Key Management Service (KMS).
                    type: str
                flag:
                    description: An integer that specifies how the key is used.
                    type: int
                signing_algorithm_mnemonic:
                    description: A string used to represent the signing algorithm.
                    type: str
                signing_algorithm_type:
                    description: An integer used to represent the signing algorithm.
                    type: int
                digest_algorithm_mnemonic:
                    description: A string used to represent the delegation signer digest algorithm.
                    type: str
                digest_algorithm_type:
                    description: An integer used to represent the delegation signer digest algorithm.
                    type: int
                key_tag:
                    description: An integer used to identify the DNSSEC record for the domain name.
                    type: int
                digest_value:
                    description: A cryptographic digest of a DNSKEY resource record (RR).
                    type: str
                public_key:
                    description: The public key, represented as a Base64 encoding.
                    type: str
                ds_record:
                    description: A string that represents a delegation signer (DS) record.
                    type: str
                dnskey_record:
                    description: A string that represents a DNSKEY record.
                    type: str
                status:
                    description: A string that represents the current key-signing key (KSK) status.
                    type: str
                status_message:
                    description: The status message provided for ACTION_NEEDED or INTERNAL_FAILURE statuses.
                    type: str
                created_date:
                    description: The date when the key-signing key (KSK) was created.
                    type: str
                last_modified_date:
                    description: The last time that the key-signing key (KSK) was changed.
                    type: str
            sample: [{
                "created_date": "2024-12-04T15:15:36.715000+00:00",
                "digest_algorithm_mnemonic": "SHA-256",
                "digest_algorithm_type": 2,
                "digest_value": "xxx",
                "dnskey_record": "xxx",
                "ds_record": "xxx",
                "flag": 257,
                "key_tag": 18948,
                "kms_arn": "arn:aws:kms:us-east-1:xxx:key/xxx",
                "last_modified_date": "2024-12-04T15:15:36.715000+00:00",
                "name": "ansible-test-44230979--ksk",
                "public_key": "xxxx",
                "signing_algorithm_mnemonic": "ECDSAP256SHA256",
                "signing_algorithm_type": 13,
                "status": "INACTIVE"
            }]
        status:
            description: A dictionary representing the status of DNSSEC.
            type: dict
            contains:
                serve_signature:
                    description: A string that represents the current hosted zone signing status.
                    type: str
            sample: {
                "serve_signature": "SIGNING"
            }
tags:
    description: Tags associated with the zone.
    returned: when tags are defined
    type: dict
"""

import time
from typing import Any
from typing import Dict

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.route53 import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.route53 import manage_tags

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule


@AWSRetry.jittered_backoff()
def _list_zones():
    paginator = client.get_paginator("list_hosted_zones")
    return paginator.paginate().build_full_result()


def find_zones(zone_in, private_zone):
    try:
        results = _list_zones()
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Could not list current hosted zones")
    zones = []
    for r53zone in results["HostedZones"]:
        if r53zone["Name"] != zone_in:
            continue
        # only save zone names that match the public/private setting
        if (r53zone["Config"]["PrivateZone"] and private_zone) or (
            not r53zone["Config"]["PrivateZone"] and not private_zone
        ):
            zones.append(r53zone)

    return zones


def get_dnssec(hosted_zone_id: str) -> Dict[str, Any]:
    try:
        return client.get_dnssec(HostedZoneId=hosted_zone_id)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Could not get dnssec details about hosted zone {hosted_zone_id}")


def enable_hosted_zone_dnssec(zone_id: str) -> None:
    try:
        client.enable_hosted_zone_dnssec(HostedZoneId=zone_id)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Could not enable DNSSEC for {zone_id}")


def disable_hosted_zone_dnssec(zone_id: str) -> None:
    try:
        client.disable_hosted_zone_dnssec(HostedZoneId=zone_id)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Could not enable DNSSEC for {zone_id}")


def get_hosted_zone(hosted_zone_id: str) -> Dict[str, Any]:
    try:
        return client.get_hosted_zone(Id=hosted_zone_id)  # could be in different regions or have different VPCids
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Could not get details about hosted zone {hosted_zone_id}")


def ensure_dnssec(zone_id: str) -> bool:
    changed = False
    dnssec = module.params.get("dnssec")

    response = get_dnssec(zone_id)
    dnssec_status = response["Status"]["ServeSignature"]

    # If get_dnssec command output returns "NOT_SIGNING",
    # the Domain Name System Security Extensions (DNSSEC) signing is not enabled for the
    # Amazon Route 53 hosted zone.
    if dnssec:
        if dnssec_status == "NOT_SIGNING":
            # Enable DNSSEC
            if not module.check_mode:
                enable_hosted_zone_dnssec(zone_id)
            changed = True
        elif dnssec_status == "DELETING":
            # DNSSEC signing is in the process of being removed for the hosted zone.
            module.warn(
                f"DNSSEC signing is in the process of being removed for the hosted zone: {zone_id}."
                "Could not enable it."
            )
    else:
        if dnssec_status == "SIGNING":
            # Disable DNSSEC
            if not module.check_mode:
                disable_hosted_zone_dnssec(zone_id)
            changed = True
        # if dnssec_status == "DELETING":
        # DNSSEC signing is in the process of being removed for the hosted zone.

    return changed


def create(matching_zones):
    zone_in = module.params.get("zone").lower()
    vpc_id = module.params.get("vpc_id")
    vpc_region = module.params.get("vpc_region")
    vpcs = module.params.get("vpcs") or ([{"id": vpc_id, "region": vpc_region}] if vpc_id and vpc_region else None)
    comment = module.params.get("comment")
    delegation_set_id = module.params.get("delegation_set_id")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")

    if not zone_in.endswith("."):
        zone_in += "."

    private_zone = bool(vpcs)

    record = {
        "private_zone": private_zone,
        "vpc_id": vpcs and vpcs[0]["id"],  # The first one for backwards compatibility
        "vpc_region": vpcs and vpcs[0]["region"],  # The first one for backwards compatibility
        "vpcs": vpcs,
        "comment": comment,
        "name": zone_in,
        "delegation_set_id": delegation_set_id,
        "zone_id": None,
    }

    if private_zone:
        changed, result = create_or_update_private(matching_zones, record)
    else:
        changed, result = create_or_update_public(matching_zones, record)

    zone_id = result.get("zone_id")
    if zone_id:
        if not private_zone:
            # Enable/Disable DNSSEC
            changed |= ensure_dnssec(zone_id)

            # Update result with information about DNSSEC
            result["dnssec"] = camel_dict_to_snake_dict(get_dnssec(zone_id))
            del result["dnssec"]["response_metadata"]

        # Handle Tags
        if tags is not None:
            changed |= manage_tags(module, client, "hostedzone", zone_id, tags, purge_tags)
        result["tags"] = get_tags(module, client, "hostedzone", zone_id)
    else:
        result["tags"] = tags

    return changed, result


def create_or_update_private(matching_zones, record):
    for z in matching_zones:
        result = get_hosted_zone(z["Id"])  # could be in different regions or have different VPCids
        zone_details = result["HostedZone"]
        vpc_details = result["VPCs"]
        matching = False
        if isinstance(vpc_details, dict) and len(record["vpcs"]) == 1:
            if vpc_details["VPC"]["VPCId"] == record["vpcs"][0]["id"]:
                matching = True
        else:
            # Sort the lists and compare them to make sure they contain the same items
            if sorted([vpc["id"] for vpc in record["vpcs"]]) == sorted([v["VPCId"] for v in vpc_details]) and sorted(
                [vpc["region"] for vpc in record["vpcs"]]
            ) == sorted([v["VPCRegion"] for v in vpc_details]):
                matching = True

        if matching:
            record["zone_id"] = zone_details["Id"].replace("/hostedzone/", "")
            if "Comment" in zone_details["Config"] and zone_details["Config"]["Comment"] != record["comment"]:
                if not module.check_mode:
                    try:
                        client.update_hosted_zone_comment(Id=zone_details["Id"], Comment=record["comment"])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg=f"Could not update comment for hosted zone {zone_details['Id']}")
                return True, record
            else:
                record["msg"] = (
                    "There is already a private hosted zone in the same region with the same VPC(s)"
                    " you chose. Unable to create a new private hosted zone in the same name space."
                )
                return False, record

    if not module.check_mode:
        try:
            result = client.create_hosted_zone(
                Name=record["name"],
                HostedZoneConfig={
                    "Comment": record["comment"] if record["comment"] is not None else "",
                    "PrivateZone": True,
                },
                VPC={
                    "VPCRegion": record["vpcs"][0]["region"],
                    "VPCId": record["vpcs"][0]["id"],
                },
                CallerReference=f"{record['name']}-{time.time()}",
            )
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not create hosted zone")

        hosted_zone = result["HostedZone"]
        zone_id = hosted_zone["Id"].replace("/hostedzone/", "")
        record["zone_id"] = zone_id

        if len(record["vpcs"]) > 1:
            for vpc in record["vpcs"][1:]:
                try:
                    result = client.associate_vpc_with_hosted_zone(
                        HostedZoneId=zone_id,
                        VPC={
                            "VPCRegion": vpc["region"],
                            "VPCId": vpc["id"],
                        },
                    )
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Could not associate additional VPCs with hosted zone")

    changed = True
    return changed, record


def create_or_update_public(matching_zones, record):
    zone_details, zone_delegation_set_details = None, {}
    for matching_zone in matching_zones:
        zone = get_hosted_zone(matching_zone["Id"])
        zone_details = zone["HostedZone"]
        zone_delegation_set_details = zone.get("DelegationSet", {})
        if "Comment" in zone_details["Config"] and zone_details["Config"]["Comment"] != record["comment"]:
            if not module.check_mode:
                try:
                    client.update_hosted_zone_comment(Id=zone_details["Id"], Comment=record["comment"])
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg=f"Could not update comment for hosted zone {zone_details['Id']}")
            changed = True
        else:
            changed = False
        break

    if zone_details is None:
        if not module.check_mode:
            try:
                params = dict(
                    Name=record["name"],
                    HostedZoneConfig={
                        "Comment": record["comment"] if record["comment"] is not None else "",
                        "PrivateZone": False,
                    },
                    CallerReference=f"{record['name']}-{time.time()}",
                )

                if record.get("delegation_set_id") is not None:
                    params["DelegationSetId"] = record["delegation_set_id"]

                result = client.create_hosted_zone(**params)
                zone_details = result["HostedZone"]
                zone_delegation_set_details = result.get("DelegationSet", {})

            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not create hosted zone")
        changed = True

    if module.check_mode:
        if zone_details:
            record["zone_id"] = zone_details["Id"].replace("/hostedzone/", "")
    else:
        record["zone_id"] = zone_details["Id"].replace("/hostedzone/", "")
        record["name"] = zone_details["Name"]
        record["delegation_set_id"] = zone_delegation_set_details.get("Id", "").replace("/delegationset/", "")

    return changed, record


def delete_private(matching_zones, vpcs):
    for z in matching_zones:
        result = get_hosted_zone(z["Id"])
        zone_details = result["HostedZone"]
        vpc_details = result["VPCs"]
        if isinstance(vpc_details, dict):
            if vpc_details["VPC"]["VPCId"] == vpcs[0]["id"] and vpcs[0]["region"] == vpc_details["VPC"]["VPCRegion"]:
                if not module.check_mode:
                    delete_hosted_zone(z["Id"])
                return True, f"Successfully deleted {zone_details['Name']}"
        else:
            # Sort the lists and compare them to make sure they contain the same items
            if sorted([vpc["id"] for vpc in vpcs]) == sorted([v["VPCId"] for v in vpc_details]) and sorted(
                [vpc["region"] for vpc in vpcs]
            ) == sorted([v["VPCRegion"] for v in vpc_details]):
                if not module.check_mode:
                    delete_hosted_zone(z["Id"])
                return True, f"Successfully deleted {zone_details['Name']}"

    return False, "The VPCs do not match a private hosted zone."


def delete_public(matching_zones):
    if len(matching_zones) > 1:
        changed = False
        msg = "There are multiple zones that match. Use hosted_zone_id to specify the correct zone."
    else:
        if not module.check_mode:
            delete_hosted_zone(matching_zones[0]["Id"])
        changed = True
        msg = f"Successfully deleted {matching_zones[0]['Id']}"
    return changed, msg


def delete_hosted_id(hosted_zone_id, matching_zones):
    if hosted_zone_id == "all":
        deleted = []
        for z in matching_zones:
            deleted.append(z["Id"])
            if not module.check_mode:
                delete_hosted_zone(z["Id"])
        changed = True
        msg = f"Successfully deleted zones: {deleted}"
    elif hosted_zone_id in [zo["Id"].replace("/hostedzone/", "") for zo in matching_zones]:
        if not module.check_mode:
            delete_hosted_zone(hosted_zone_id)
        changed = True
        msg = f"Successfully deleted zone: {hosted_zone_id}"
    else:
        changed = False
        msg = f"There is no zone to delete that matches hosted_zone_id {hosted_zone_id}."
    return changed, msg


def delete_hosted_zone(hosted_zone_id):
    try:
        client.delete_hosted_zone(Id=hosted_zone_id)
    except is_boto3_error_code("HostedZoneNotEmpty") as e:
        module.fail_json_aws(e, msg=f"Could not get delete hosted zone {hosted_zone_id}")
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Could not delete hosted zone {hosted_zone_id}")


def delete(matching_zones):
    zone_in = module.params.get("zone").lower()
    vpc_id = module.params.get("vpc_id")
    vpc_region = module.params.get("vpc_region")
    vpcs = module.params.get("vpcs") or ([{"id": vpc_id, "region": vpc_region}] if vpc_id and vpc_region else None)
    hosted_zone_id = module.params.get("hosted_zone_id")

    if not zone_in.endswith("."):
        zone_in += "."

    private_zone = bool(vpcs)

    if zone_in in [z["Name"] for z in matching_zones]:
        if hosted_zone_id:
            changed, result = delete_hosted_id(hosted_zone_id, matching_zones)
        else:
            if private_zone:
                changed, result = delete_private(matching_zones, vpcs)
            else:
                changed, result = delete_public(matching_zones)
    else:
        changed = False
        result = "No zone to delete."

    return changed, result


def main():
    global module
    global client

    argument_spec = dict(
        zone=dict(required=True),
        state=dict(default="present", choices=["present", "absent"]),
        vpc_id=dict(default=None),
        vpc_region=dict(default=None),
        vpcs=dict(
            type="list", default=None, elements="dict", options=dict(id=dict(required=True), region=dict(required=True))
        ),
        comment=dict(default=""),
        hosted_zone_id=dict(),
        delegation_set_id=dict(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        dnssec=dict(type="bool", default=False),
    )

    mutually_exclusive = [
        ["delegation_set_id", "vpc_id"],
        ["delegation_set_id", "vpc_region"],
        ["delegation_set_id", "vpcs"],
        ["vpcs", "vpc_id"],
        ["vpcs", "vpc_region"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
    )

    zone_in = module.params.get("zone").lower()
    state = module.params.get("state").lower()
    vpc_id = module.params.get("vpc_id")
    vpc_region = module.params.get("vpc_region")
    vpcs = module.params.get("vpcs")

    if not zone_in.endswith("."):
        zone_in += "."

    private_zone = bool(vpcs or (vpc_id and vpc_region))

    client = module.client("route53", retry_decorator=AWSRetry.jittered_backoff())

    zones = find_zones(zone_in, private_zone)
    if state == "present":
        changed, result = create(matching_zones=zones)
    elif state == "absent":
        changed, result = delete(matching_zones=zones)

    if isinstance(result, dict):
        module.exit_json(changed=changed, result=result, **result)
    else:
        module.exit_json(changed=changed, result=result)


if __name__ == "__main__":
    main()

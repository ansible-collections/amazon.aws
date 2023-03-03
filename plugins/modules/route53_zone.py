#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: route53_zone
short_description: add or delete Route53 zones
version_added: 5.0.0
description:
    - Creates and deletes Route53 private and public zones.
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
extends_documentation_fragment:
    - amazon.aws.aws
    - amazon.aws.ec2
    - amazon.aws.tags
    - amazon.aws.boto3
notes:
    - Support for I(tags) and I(purge_tags) was added in release 2.1.0.
author:
    - "Christopher Troup (@minichate)"
'''

EXAMPLES = r'''
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
'''

RETURN = r'''
comment:
    description: optional hosted zone comment
    returned: when hosted zone exists
    type: str
    sample: "Private zone"
name:
    description: hosted zone name
    returned: when hosted zone exists
    type: str
    sample: "private.local."
private_zone:
    description: whether hosted zone is private or public
    returned: when hosted zone exists
    type: bool
    sample: true
vpc_id:
    description: id of the first vpc attached to private hosted zone (use vpcs for associating multiple).
    returned: for private hosted zone
    type: str
    sample: "vpc-1d36c84f"
vpc_region:
    description: region of the first vpc attached to private hosted zone (use vpcs for assocaiting multiple).
    returned: for private hosted zone
    type: str
    sample: "eu-west-1"
vpcs:
    version_added: 5.3.0
    description: The list of VPCs attached to the private hosted zone
    returned: for private hosted zone
    type: list
    elements: dict
    sample: "[{'id': 'vpc-123456', 'region': 'us-west-2'}]"
    contains:
        id:
            description: ID of the VPC
            returned: for private hosted zone
            type: str
            sample: "vpc-123456"
        region:
            description: Region of the VPC
            returned: for private hosted zone
            type: str
            sample: "eu-west-2"
zone_id:
    description: hosted zone id
    returned: when hosted zone exists
    type: str
    sample: "Z6JQG9820BEFMW"
delegation_set_id:
    description: id of the associated reusable delegation set
    returned: for public hosted zones, if they have been associated with a reusable delegation set
    type: str
    sample: "A1BCDEF2GHIJKL"
tags:
    description: tags associated with the zone
    returned: when tags are defined
    type: dict
'''

import time
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.route53 import manage_tags
from ansible_collections.amazon.aws.plugins.module_utils.route53 import get_tags

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule


@AWSRetry.jittered_backoff()
def _list_zones():
    paginator = client.get_paginator('list_hosted_zones')
    return paginator.paginate().build_full_result()


def find_zones(zone_in, private_zone):
    try:
        results = _list_zones()
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Could not list current hosted zones")
    zones = []
    for r53zone in results['HostedZones']:
        if r53zone['Name'] != zone_in:
            continue
        # only save zone names that match the public/private setting
        if (r53zone['Config']['PrivateZone'] and private_zone) or \
           (not r53zone['Config']['PrivateZone'] and not private_zone):
            zones.append(r53zone)

    return zones


def create(matching_zones):
    zone_in = module.params.get('zone').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    vpcs = module.params.get('vpcs') or ([{'id': vpc_id, 'region': vpc_region}] if vpc_id and vpc_region else None)
    comment = module.params.get('comment')
    delegation_set_id = module.params.get('delegation_set_id')
    tags = module.params.get('tags')
    purge_tags = module.params.get('purge_tags')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpcs)

    record = {
        'private_zone': private_zone,
        'vpc_id': vpcs and vpcs[0]['id'],  # The first one for backwards compatibility
        'vpc_region': vpcs and vpcs[0]['region'],  # The first one for backwards compatibility
        'vpcs': vpcs,
        'comment': comment,
        'name': zone_in,
        'delegation_set_id': delegation_set_id,
        'zone_id': None,
    }

    if private_zone:
        changed, result = create_or_update_private(matching_zones, record)
    else:
        changed, result = create_or_update_public(matching_zones, record)

    zone_id = result.get('zone_id')
    if zone_id:
        if tags is not None:
            changed |= manage_tags(module, client, 'hostedzone', zone_id, tags, purge_tags)
        result['tags'] = get_tags(module, client, 'hostedzone', zone_id)
    else:
        result['tags'] = tags

    return changed, result


def create_or_update_private(matching_zones, record):
    for z in matching_zones:
        try:
            result = client.get_hosted_zone(Id=z['Id'])  # could be in different regions or have different VPCids
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not get details about hosted zone %s" % z['Id'])
        zone_details = result['HostedZone']
        vpc_details = result['VPCs']
        current_vpc_ids = None
        current_vpc_regions = None
        matching = False
        if isinstance(vpc_details, dict) and len(record['vpcs']) == 1:
            if vpc_details['VPC']['VPCId'] == record['vpcs'][0]['id']:
                current_vpc_ids = [vpc_details['VPC']['VPCId']]
                current_vpc_regions = [vpc_details['VPC']['VPCRegion']]
                matching = True
        else:
            # Sort the lists and compare them to make sure they contain the same items
            if (sorted([vpc['id'] for vpc in record['vpcs']]) == sorted([v['VPCId'] for v in vpc_details])
                    and sorted([vpc['region'] for vpc in record['vpcs']]) == sorted([v['VPCRegion'] for v in vpc_details])):
                current_vpc_ids = [vpc['id'] for vpc in record['vpcs']]
                current_vpc_regions = [vpc['region'] for vpc in record['vpcs']]
                matching = True

        if matching:
            record['zone_id'] = zone_details['Id'].replace('/hostedzone/', '')
            if 'Comment' in zone_details['Config'] and zone_details['Config']['Comment'] != record['comment']:
                if not module.check_mode:
                    try:
                        client.update_hosted_zone_comment(Id=zone_details['Id'], Comment=record['comment'])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Could not update comment for hosted zone %s" % zone_details['Id'])
                return True, record
            else:
                record['msg'] = "There is already a private hosted zone in the same region with the same VPC(s) \
                    you chose. Unable to create a new private hosted zone in the same name space."
                return False, record

    if not module.check_mode:
        try:
            result = client.create_hosted_zone(
                Name=record['name'],
                HostedZoneConfig={
                    'Comment': record['comment'] if record['comment'] is not None else "",
                    'PrivateZone': True,
                },
                VPC={
                    'VPCRegion': record['vpcs'][0]['region'],
                    'VPCId': record['vpcs'][0]['id'],
                },
                CallerReference="%s-%s" % (record['name'], time.time()),
            )
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not create hosted zone")

        hosted_zone = result['HostedZone']
        zone_id = hosted_zone['Id'].replace('/hostedzone/', '')
        record['zone_id'] = zone_id

        if len(record['vpcs']) > 1:
            for vpc in record['vpcs'][1:]:
                try:
                    result = client.associate_vpc_with_hosted_zone(
                        HostedZoneId=zone_id,
                        VPC={
                            'VPCRegion': vpc['region'],
                            'VPCId': vpc['id'],
                        },
                    )
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Could not associate additional VPCs with hosted zone")

    changed = True
    return changed, record


def create_or_update_public(matching_zones, record):
    zone_details, zone_delegation_set_details = None, {}
    for matching_zone in matching_zones:
        try:
            zone = client.get_hosted_zone(Id=matching_zone['Id'])
            zone_details = zone['HostedZone']
            zone_delegation_set_details = zone.get('DelegationSet', {})
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not get details about hosted zone %s" % matching_zone['Id'])
        if 'Comment' in zone_details['Config'] and zone_details['Config']['Comment'] != record['comment']:
            if not module.check_mode:
                try:
                    client.update_hosted_zone_comment(
                        Id=zone_details['Id'],
                        Comment=record['comment']
                    )
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Could not update comment for hosted zone %s" % zone_details['Id'])
            changed = True
        else:
            changed = False
        break

    if zone_details is None:
        if not module.check_mode:
            try:
                params = dict(
                    Name=record['name'],
                    HostedZoneConfig={
                        'Comment': record['comment'] if record['comment'] is not None else "",
                        'PrivateZone': False,
                    },
                    CallerReference="%s-%s" % (record['name'], time.time()),
                )

                if record.get('delegation_set_id') is not None:
                    params['DelegationSetId'] = record['delegation_set_id']

                result = client.create_hosted_zone(**params)
                zone_details = result['HostedZone']
                zone_delegation_set_details = result.get('DelegationSet', {})

            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not create hosted zone")
        changed = True

    if module.check_mode:
        if zone_details:
            record['zone_id'] = zone_details['Id'].replace('/hostedzone/', '')
    else:
        record['zone_id'] = zone_details['Id'].replace('/hostedzone/', '')
        record['name'] = zone_details['Name']
        record['delegation_set_id'] = zone_delegation_set_details.get('Id', '').replace('/delegationset/', '')

    return changed, record


def delete_private(matching_zones, vpcs):
    for z in matching_zones:
        try:
            result = client.get_hosted_zone(Id=z['Id'])
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not get details about hosted zone %s" % z['Id'])
        zone_details = result['HostedZone']
        vpc_details = result['VPCs']
        if isinstance(vpc_details, dict):
            if vpc_details['VPC']['VPCId'] == vpcs[0]['id'] and vpcs[0]['region'] == vpc_details['VPC']['VPCRegion']:
                if not module.check_mode:
                    try:
                        client.delete_hosted_zone(Id=z['Id'])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Could not delete hosted zone %s" % z['Id'])
                return True, "Successfully deleted %s" % zone_details['Name']
        else:
            # Sort the lists and compare them to make sure they contain the same items
            if (sorted([vpc['id'] for vpc in vpcs]) == sorted([v['VPCId'] for v in vpc_details])
                    and sorted([vpc['region'] for vpc in vpcs]) == sorted([v['VPCRegion'] for v in vpc_details])):
                if not module.check_mode:
                    try:
                        client.delete_hosted_zone(Id=z['Id'])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Could not delete hosted zone %s" % z['Id'])
                return True, "Successfully deleted %s" % zone_details['Name']

    return False, "The VPCs do not match a private hosted zone."


def delete_public(matching_zones):
    if len(matching_zones) > 1:
        changed = False
        msg = "There are multiple zones that match. Use hosted_zone_id to specify the correct zone."
    else:
        if not module.check_mode:
            try:
                client.delete_hosted_zone(Id=matching_zones[0]['Id'])
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not get delete hosted zone %s" % matching_zones[0]['Id'])
        changed = True
        msg = "Successfully deleted %s" % matching_zones[0]['Id']
    return changed, msg


def delete_hosted_id(hosted_zone_id, matching_zones):
    if hosted_zone_id == "all":
        deleted = []
        for z in matching_zones:
            deleted.append(z['Id'])
            if not module.check_mode:
                try:
                    client.delete_hosted_zone(Id=z['Id'])
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Could not delete hosted zone %s" % z['Id'])
        changed = True
        msg = "Successfully deleted zones: %s" % deleted
    elif hosted_zone_id in [zo['Id'].replace('/hostedzone/', '') for zo in matching_zones]:
        if not module.check_mode:
            try:
                client.delete_hosted_zone(Id=hosted_zone_id)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not delete hosted zone %s" % hosted_zone_id)
        changed = True
        msg = "Successfully deleted zone: %s" % hosted_zone_id
    else:
        changed = False
        msg = "There is no zone to delete that matches hosted_zone_id %s." % hosted_zone_id
    return changed, msg


def delete(matching_zones):
    zone_in = module.params.get('zone').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    vpcs = module.params.get('vpcs') or ([{'id': vpc_id, 'region': vpc_region}] if vpc_id and vpc_region else None)
    hosted_zone_id = module.params.get('hosted_zone_id')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpcs)

    if zone_in in [z['Name'] for z in matching_zones]:
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
        state=dict(default='present', choices=['present', 'absent']),
        vpc_id=dict(default=None),
        vpc_region=dict(default=None),
        vpcs=dict(type='list', default=None, elements='dict', options=dict(
            id=dict(required=True),
            region=dict(required=True)
        )),
        comment=dict(default=''),
        hosted_zone_id=dict(),
        delegation_set_id=dict(),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
    )

    mutually_exclusive = [
        ['delegation_set_id', 'vpc_id'],
        ['delegation_set_id', 'vpc_region'],
        ['delegation_set_id', 'vpcs'],
        ['vpcs', 'vpc_id'],
        ['vpcs', 'vpc_region'],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
    )

    zone_in = module.params.get('zone').lower()
    state = module.params.get('state').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    vpcs = module.params.get('vpcs')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpcs or (vpc_id and vpc_region))

    client = module.client('route53', retry_decorator=AWSRetry.jittered_backoff())

    zones = find_zones(zone_in, private_zone)
    if state == 'present':
        changed, result = create(matching_zones=zones)
    elif state == 'absent':
        changed, result = delete(matching_zones=zones)

    if isinstance(result, dict):
        module.exit_json(changed=changed, result=result, **result)
    else:
        module.exit_json(changed=changed, result=result)


if __name__ == '__main__':
    main()

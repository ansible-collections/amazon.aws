#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: ec2_transit_gateway_vpc_attachment
short_description: Create and delete AWS Transit Gateway VPC attachments
version_added: 4.0.0
description:
  - Creates, Deletes and Updates AWS Transit Gateway VPC Attachments.
options:
  transit_gateway:
    description:
      - The ID of the Transit Gateway that the attachment belongs to.
      - When creating a new attachment, I(transit_gateway) must be provided.
      - At least one of I(name), I(transit_gateway) and I(id) must be provided.
      - I(transit_gateway) is an immutable setting and can not be updated on an
        existing attachment.
    type: str
    required: false
    aliases: ['transit_gateway_id']
  id:
    description:
      - The ID of the Transit Gateway Attachment.
      - When I(id) is not set, a search using I(transit_gateway) and I(name) will be
        performed.  If multiple results are returned, the module will fail.
      - At least one of I(name), I(transit_gateway) and I(id) must be provided.
    type: str
    required: false
    aliases: ['attachment_id']
  name:
    description:
      - The C(Name) tag of the Transit Gateway attachment.
      - Providing both I(id) and I(name) will set the C(Name) tag on an existing
        attachment the matching I(id).
      - Setting the C(Name) tag in I(tags) will also result in the C(Name) tag being
        updated.
      - At least one of I(name), I(transit_gateway) and I(id) must be provided.
    type: str
    required: false
  state:
    description:
      - Create or remove the Transit Gateway attachment.
    type: str
    required: false
    choices: ['present', 'absent']
    default: 'present'
  subnets:
    description:
      - The ID of the subnets in which to create the transit gateway VPC attachment.
      - Required when creating a new attachment.
    type: list
    elements: str
    required: false
  purge_subnets:
    description:
      - If I(purge_subnets=true), existing subnets will be removed from the
        attachment as necessary to match exactly what is defined by I(subnets).
    type: bool
    required: false
    default: true
  dns_support:
    description:
      - Whether DNS support is enabled.
    type: bool
    required: false
  ipv6_support:
    description:
      - Whether IPv6 support is enabled.
    type: bool
    required: false
  appliance_mode_support:
    description:
      - Whether the attachment is configured for appliance mode.
      - When appliance mode is enabled, Transit Gateway, using 4-tuples of an
        IP packet, selects a single Transit Gateway ENI in the Appliance VPC
        for the life of a flow to send traffic to.
    type: bool
    required: false
  wait:
    description:
      - Whether to wait for the Transit Gateway attachment to reach the
        C(Available) or C(Deleted) state before the module returns.
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - Maximum time, in seconds, to wait for the Transit Gateway attachment
        to reach the expected state.
      - Defaults to 600 seconds.
    type: int
    required: false
author:
  - "Mark Chappell (@tremble)"
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
  - amazon.aws.tags
'''

EXAMPLES = '''
# Create a Transit Gateway attachment
- community.aws.ec2_transit_gateway_vpc_attachment:
    state: present
    transit_gateway: 'tgw-123456789abcdef01'
    name: AnsibleTest-1
    subnets:
    - subnet-00000000000000000
    - subnet-11111111111111111
    - subnet-22222222222222222
    ipv6_support: True
    purge_subnets: True
    dns_support: True
    appliance_mode_support: True
    tags:
      TestTag: changed data in Test Tag

# Set sub options on a Transit Gateway attachment
- community.aws.ec2_transit_gateway_vpc_attachment:
    state: present
    id: 'tgw-attach-0c0c5fd0b0f01d1c9'
    name: AnsibleTest-1
    ipv6_support: True
    purge_subnets: False
    dns_support: False
    appliance_mode_support: True

# Delete the transit gateway
- community.aws.ec2_transit_gateway_vpc_attachment:
    state: absent
    id: 'tgw-attach-0c0c5fd0b0f01d1c9'
'''

RETURN = '''
transit_gateway_attachments:
  description: The attributes of the Transit Gateway attachments.
  type: list
  elements: dict
  returned: success
  contains:
    creation_time:
      description:
        - An ISO 8601 date time stamp of when the attachment was created.
      type: str
      returned: success
      example: '2022-03-10T16:40:26+00:00'
    options:
      description:
        - Additional VPC attachment options.
      type: dict
      returned: success
      contains:
        appliance_mode_support:
          description:
            - Indicates whether appliance mode support is enabled.
          type: str
          returned: success
          example: 'enable'
        dns_support:
          description:
            - Indicates whether DNS support is enabled.
          type: str
          returned: success
          example: 'disable'
        ipv6_support:
          description:
            - Indicates whether IPv6 support is disabled.
          type: str
          returned: success
          example: 'disable'
    state:
      description:
        - The state of the attachment.
      type: str
      returned: success
      example: 'deleting'
    subnet_ids:
      description:
        - The IDs of the subnets in use by the attachment.
      type: list
      elements: str
      returned: success
      example: ['subnet-0123456789abcdef0', 'subnet-11111111111111111']
    tags:
      description:
        - A dictionary representing the resource tags.
      type: dict
      returned: success
    transit_gateway_attachment_id:
      description:
        - The ID of the attachment.
      type: str
      returned: success
      example: 'tgw-attach-0c0c5fd0b0f01d1c9'
    transit_gateway_id:
      description:
        - The ID of the transit gateway that the attachment is connected to.
      type: str
      returned: success
      example: 'tgw-0123456789abcdef0'
    vpc_id:
      description:
        - The ID of the VPC that the attachment is connected to.
      type: str
      returned: success
      example: 'vpc-0123456789abcdef0'
    vpc_owner_id:
      description:
        - The ID of the account that the VPC belongs to.
      type: str
      returned: success
      example: '123456789012'
'''


from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule

from ansible_collections.community.aws.plugins.module_utils.transitgateway import TransitGatewayVpcAttachmentManager


def main():

    argument_spec = dict(
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        transit_gateway=dict(type='str', required=False, aliases=['transit_gateway_id']),
        id=dict(type='str', required=False, aliases=['attachment_id']),
        name=dict(type='str', required=False),
        subnets=dict(type='list', elements='str', required=False),
        purge_subnets=dict(type='bool', required=False, default=True),
        tags=dict(type='dict', required=False, aliases=['resource_tags']),
        purge_tags=dict(type='bool', required=False, default=True),
        appliance_mode_support=dict(type='bool', required=False),
        dns_support=dict(type='bool', required=False),
        ipv6_support=dict(type='bool', required=False),
        wait=dict(type='bool', required=False, default=True),
        wait_timeout=dict(type='int', required=False),
    )

    one_of = [
        ['id', 'transit_gateway', 'name'],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=one_of,
    )

    attach_id = module.params.get('id', None)
    tgw = module.params.get('transit_gateway', None)
    name = module.params.get('name', None)
    tags = module.params.get('tags', None)
    purge_tags = module.params.get('purge_tags')
    state = module.params.get('state')
    subnets = module.params.get('subnets', None)
    purge_subnets = module.params.get('purge_subnets')

    # When not provided with an ID see if one exists.
    if not attach_id:
        search_manager = TransitGatewayVpcAttachmentManager(module=module)
        filters = dict()
        if tgw:
            filters['transit-gateway-id'] = tgw
        if name:
            filters['tag:Name'] = name
        if subnets:
            vpc_id = search_manager.subnets_to_vpc(subnets)
            filters['vpc-id'] = vpc_id

        # Attachments lurk in a 'deleted' state, for a while, ignore them so we
        # can reuse the names
        filters['state'] = [
            'available', 'deleting', 'failed', 'failing', 'initiatingRequest', 'modifying',
            'pendingAcceptance', 'pending', 'rollingBack', 'rejected', 'rejecting'
        ]
        attachments = search_manager.list(filters=filters)
        if len(attachments) > 1:
            module.fail_json('Multiple matching attachments found, provide an ID', attachments=attachments)
        # If we find a match then we'll modify it by ID, otherwise we'll be
        # creating a new RTB.
        if attachments:
            attach_id = attachments[0]['transit_gateway_attachment_id']

    manager = TransitGatewayVpcAttachmentManager(module=module, id=attach_id)
    manager.set_wait(module.params.get('wait', None))
    manager.set_wait_timeout(module.params.get('wait_timeout', None))

    if state == 'absent':
        manager.delete()
    else:
        if not attach_id:
            if not tgw:
                module.fail_json('No existing attachment found.  To create a new attachment'
                                 ' the `transit_gateway` parameter must be provided.')
            if not subnets:
                module.fail_json('No existing attachment found.  To create a new attachment'
                                 ' the `subnets` parameter must be provided.')

        # name is just a special case of tags.
        if name:
            new_tags = dict(Name=name)
            if tags is None:
                purge_tags = False
            else:
                new_tags.update(tags)
            tags = new_tags

        manager.set_transit_gateway(tgw)
        manager.set_subnets(subnets, purge_subnets)
        manager.set_tags(tags, purge_tags)
        manager.set_dns_support(module.params.get('dns_support', None))
        manager.set_ipv6_support(module.params.get('ipv6_support', None))
        manager.set_appliance_mode_support(module.params.get('appliance_mode_support', None))
        manager.flush_changes()

    results = dict(
        changed=manager.changed,
        attachments=[manager.updated_resource],
    )
    if manager.changed:
        results['diff'] = dict(
            before=manager.original_resource,
            after=manager.updated_resource,
        )

    module.exit_json(**results)


if __name__ == '__main__':
    main()

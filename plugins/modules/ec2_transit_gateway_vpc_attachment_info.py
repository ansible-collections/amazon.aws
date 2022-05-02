#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: ec2_transit_gateway_vpc_attachment_info
short_description: describes AWS Transit Gateway VPC attachments
version_added: 4.0.0
description:
  - Describes AWS Transit Gateway VPC Attachments.
options:
  id:
    description:
      - The ID of the Transit Gateway Attachment.
      - Mutually exclusive with I(name) and I(filters)
    type: str
    required: false
    aliases: ['attachment_id']
  name:
    description:
      - The C(Name) tag of the Transit Gateway attachment.
    type: str
    required: false
  filters:
    description:
      - A dictionary of filters to apply. Each dict item consists of a filter key and a filter value.
      - Setting a C(tag:Name) filter will override the I(name) parameter.
    type: dict
    required: false
  include_deleted:
    description:
      - If I(include_deleted=True), then attachments in a deleted state will
        also be returned.
      - Setting a C(state) filter will override the I(include_deleted) parameter.
    type: bool
    required: false
    default: false
author: "Mark Chappell (@tremble)"
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
'''

EXAMPLES = '''
# Describe a specific Transit Gateway attachment.
- community.aws.ec2_transit_gateway_vpc_attachment_info:
    state: present
    id: 'tgw-attach-0123456789abcdef0'

# Describe all attachments attached to a transit gateway.
- community.aws.ec2_transit_gateway_vpc_attachment_info:
    state: present
    filters:
      transit-gateway-id: tgw-0fedcba9876543210'

# Describe all attachments in an account.
- community.aws.ec2_transit_gateway_vpc_attachment_info:
    state: present
    filters:
      transit-gateway-id: tgw-0fedcba9876543210'
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
      example: '012345678901'
'''


from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule

from ansible_collections.community.aws.plugins.module_utils.transitgateway import TransitGatewayVpcAttachmentManager


def main():

    argument_spec = dict(
        id=dict(type='str', required=False, aliases=['attachment_id']),
        name=dict(type='str', required=False),
        filters=dict(type='dict', required=False),
        include_deleted=dict(type='bool', required=False, default=False)
    )

    mutually_exclusive = [
        ['id', 'name'],
        ['id', 'filters'],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params.get('name', None)
    id = module.params.get('id', None)
    opt_filters = module.params.get('filters', None)

    search_manager = TransitGatewayVpcAttachmentManager(module=module)
    filters = dict()

    if name:
        filters['tag:Name'] = name

    if not module.params.get('include_deleted'):
        # Attachments lurk in a 'deleted' state, for a while, ignore them so we
        # can reuse the names
        filters['state'] = [
            'available', 'deleting', 'failed', 'failing', 'initiatingRequest', 'modifying',
            'pendingAcceptance', 'pending', 'rollingBack', 'rejected', 'rejecting'
        ]

    if opt_filters:
        filters.update(opt_filters)

    attachments = search_manager.list(filters=filters, id=id)

    module.exit_json(changed=False, attachments=attachments, filters=filters)


if __name__ == '__main__':
    main()

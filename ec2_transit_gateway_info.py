#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_transit_gateway_info
short_description: Gather information about ec2 transit gateways in AWS
version_added: 1.0.0
description:
    - Gather information about ec2 transit gateways in AWS
author: "Bob Boldin (@BobBoldin)"
options:
  transit_gateway_ids:
    description:
      - A list of transit gateway IDs to gather information for.
    aliases: [transit_gateway_id]
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeTransitGateways.html) for filters.
    type: dict
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather info about all transit gateways
  community.aws.ec2_transit_gateway_info:

- name: Gather info about a particular transit gateway using filter transit gateway ID
  community.aws.ec2_transit_gateway_info:
    filters:
      transit-gateway-id: tgw-02c42332e6b7da829

- name: Gather info about a particular transit gateway using multiple option filters
  community.aws.ec2_transit_gateway_info:
    filters:
      options.dns-support: enable
      options.vpn-ecmp-support: enable

- name: Gather info about multiple transit gateways using module param
  community.aws.ec2_transit_gateway_info:
    transit_gateway_ids:
      - tgw-02c42332e6b7da829
      - tgw-03c53443d5a8cb716
'''

RETURN = r'''
transit_gateways:
    description: >
        Transit gateways that match the provided filters. Each element consists of a dict with all the information
        related to that transit gateway.
    returned: on success
    type: complex
    contains:
        creation_time:
            description: The creation time.
            returned: always
            type: str
            sample: "2019-02-05T16:19:58+00:00"
        description:
            description: The description of the transit gateway.
            returned: always
            type: str
            sample: "A transit gateway"
        options:
            description: A dictionary of the transit gateway options.
            returned: always
            type: complex
            contains:
                 amazon_side_asn:
                    description:
                      - A private Autonomous System Number (ASN) for  the  Amazon
                        side  of  a  BGP session. The range is 64512 to 65534 for
                        16-bit ASNs and 4200000000 to 4294967294 for 32-bit ASNs.
                    returned: always
                    type: int
                    sample: 64512
                 auto_accept_shared_attachments:
                    description:
                       - Indicates whether attachment requests  are  automatically accepted.
                    returned: always
                    type: str
                    sample: "enable"
                 default_route_table_association:
                    description:
                      - Indicates  whether resource attachments are automatically
                        associated with the default association route table.
                    returned: always
                    type: str
                    sample: "disable"
                 association_default_route_table_id:
                    description:
                      - The ID of the default association route table.
                    returned: when present
                    type: str
                    sample: "rtb-11223344"
                 default_route_table_propagation:
                    description:
                      - Indicates  whether  resource  attachments   automatically
                        propagate routes to the default propagation route table.
                    returned: always
                    type: str
                    sample: "disable"
                 dns_support:
                    description:
                      - Indicates whether DNS support is enabled.
                    returned: always
                    type: str
                    sample: "enable"
                 propagation_default_route_table_id:
                    description:
                      - The ID of the default propagation route table.
                    returned: when present
                    type: str
                    sample: "rtb-11223344"
                 vpn_ecmp_support:
                    description:
                      - Indicates  whether  Equal Cost Multipath Protocol support
                        is enabled.
                    returned: always
                    type: str
                    sample: "enable"
        owner_id:
            description: The AWS account number ID which owns the transit gateway.
            returned: always
            type: str
            sample: "123456789012"
        state:
            description: The state of the transit gateway.
            returned: always
            type: str
            sample: "available"
        tags:
            description: A dict of tags associated with the transit gateway.
            returned: always
            type: dict
            sample: '{
              "Name": "A sample TGW"
              }'
        transit_gateway_arn:
            description: The Amazon Resource Name (ARN) of the transit gateway.
            returned: always
            type: str
            sample: "arn:aws:ec2:us-west-2:123456789012:transit-gateway/tgw-02c42332e6b7da829"
        transit_gateway_id:
            description: The ID of the transit gateway.
            returned: always
            type: str
            sample: "tgw-02c42332e6b7da829"
'''

try:
    import botocore
except ImportError:
    pass  # handled by imported AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


class AnsibleEc2TgwInfo(object):

    def __init__(self, module, results):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode

    @AWSRetry.exponential_backoff()
    def describe_transit_gateways(self):
        """
        Describe transit gateways.

        module  : AnsibleAWSModule object
        connection  : boto3 client connection object
        """
        # collect parameters
        filters = ansible_dict_to_boto3_filter_list(self._module.params['filters'])
        transit_gateway_ids = self._module.params['transit_gateway_ids']

        # init empty list for return vars
        transit_gateway_info = list()

        # Get the basic transit gateway info
        try:
            response = self._connection.describe_transit_gateways(
                TransitGatewayIds=transit_gateway_ids, Filters=filters)
        except is_boto3_error_code('InvalidTransitGatewayID.NotFound'):
            self._results['transit_gateways'] = []
            return

        for transit_gateway in response['TransitGateways']:
            transit_gateway_info.append(camel_dict_to_snake_dict(transit_gateway, ignore_list=['Tags']))
            # convert tag list to ansible dict
            transit_gateway_info[-1]['tags'] = boto3_tag_list_to_ansible_dict(transit_gateway.get('Tags', []))

        self._results['transit_gateways'] = transit_gateway_info
        return


def setup_module_object():
    """
    merge argument spec and create Ansible module object
    :return: Ansible module object
    """

    argument_spec = dict(
        transit_gateway_ids=dict(type='list', default=[], elements='str', aliases=['transit_gateway_id']),
        filters=dict(type='dict', default={})
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    return module


def main():

    module = setup_module_object()

    results = dict(
        changed=False
    )

    tgwf_manager = AnsibleEc2TgwInfo(module=module, results=results)
    try:
        tgwf_manager.describe_transit_gateways()
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e)

    module.exit_json(**results)


if __name__ == '__main__':
    main()

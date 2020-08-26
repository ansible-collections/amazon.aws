#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_customer_gateway
version_added: 1.0.0
short_description: Manage an AWS customer gateway
description:
    - Manage an AWS customer gateway.
author: Michael Baydoun (@MichaelBaydoun)
requirements: [ botocore, boto3 ]
notes:
    - You cannot create more than one customer gateway with the same IP address. If you run an identical request more than one time, the
      first request creates the customer gateway, and subsequent requests return information about the existing customer gateway. The subsequent
      requests do not create new customer gateway resources.
    - Return values contain customer_gateway and customer_gateways keys which are identical dicts. You should use
      customer_gateway. See U(https://github.com/ansible/ansible-modules-extras/issues/2773) for details.
options:
  bgp_asn:
    description:
      - Border Gateway Protocol (BGP) Autonomous System Number (ASN), required when I(state=present).
    type: int
  ip_address:
    description:
      - Internet-routable IP address for customers gateway, must be a static address.
    required: true
    type: str
  name:
    description:
      - Name of the customer gateway.
    required: true
    type: str
  routing:
    description:
      - The type of routing.
    choices: ['static', 'dynamic']
    default: dynamic
    type: str
  state:
    description:
      - Create or terminate the Customer Gateway.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: Create Customer Gateway
  community.aws.ec2_customer_gateway:
    bgp_asn: 12345
    ip_address: 1.2.3.4
    name: IndianapolisOffice
    region: us-east-1
  register: cgw

- name: Delete Customer Gateway
  community.aws.ec2_customer_gateway:
    ip_address: 1.2.3.4
    name: IndianapolisOffice
    state: absent
    region: us-east-1
  register: cgw
'''

RETURN = '''
gateway.customer_gateways:
    description: details about the gateway that was created.
    returned: success
    type: complex
    contains:
        bgp_asn:
            description: The Border Gateway Autonomous System Number.
            returned: when exists and gateway is available.
            sample: 65123
            type: str
        customer_gateway_id:
            description: gateway id assigned by amazon.
            returned: when exists and gateway is available.
            sample: cgw-cb6386a2
            type: str
        ip_address:
            description: ip address of your gateway device.
            returned: when exists and gateway is available.
            sample: 1.2.3.4
            type: str
        state:
            description: state of gateway.
            returned: when gateway exists and is available.
            sample: available
            type: str
        tags:
            description: Any tags on the gateway.
            returned: when gateway exists and is available, and when tags exist.
            type: list
        type:
            description: encryption type.
            returned: when gateway exists and is available.
            sample: ipsec.1
            type: str
'''

try:
    from botocore.exceptions import ClientError
    import boto3
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


class Ec2CustomerGatewayManager:

    def __init__(self, module):
        self.module = module

        try:
            self.ec2 = module.client('ec2')
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to connect to AWS')

    @AWSRetry.jittered_backoff(delay=2, max_delay=30, retries=6, catch_extra_error_codes=['IncorrectState'])
    def ensure_cgw_absent(self, gw_id):
        response = self.ec2.delete_customer_gateway(
            DryRun=False,
            CustomerGatewayId=gw_id
        )
        return response

    def ensure_cgw_present(self, bgp_asn, ip_address):
        if not bgp_asn:
            bgp_asn = 65000
        response = self.ec2.create_customer_gateway(
            DryRun=False,
            Type='ipsec.1',
            PublicIp=ip_address,
            BgpAsn=bgp_asn,
        )
        return response

    def tag_cgw_name(self, gw_id, name):
        response = self.ec2.create_tags(
            DryRun=False,
            Resources=[
                gw_id,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name
                },
            ]
        )
        return response

    def describe_gateways(self, ip_address):
        response = self.ec2.describe_customer_gateways(
            DryRun=False,
            Filters=[
                {
                    'Name': 'state',
                    'Values': [
                        'available',
                    ]
                },
                {
                    'Name': 'ip-address',
                    'Values': [
                        ip_address,
                    ]
                }
            ]
        )
        return response


def main():
    argument_spec = dict(
        bgp_asn=dict(required=False, type='int'),
        ip_address=dict(required=True),
        name=dict(required=True),
        routing=dict(default='dynamic', choices=['dynamic', 'static']),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('routing', 'dynamic', ['bgp_asn'])
        ]
    )

    gw_mgr = Ec2CustomerGatewayManager(module)

    name = module.params.get('name')

    existing = gw_mgr.describe_gateways(module.params['ip_address'])

    results = dict(changed=False)
    if module.params['state'] == 'present':
        if existing['CustomerGateways']:
            existing['CustomerGateway'] = existing['CustomerGateways'][0]
            results['gateway'] = existing
            if existing['CustomerGateway']['Tags']:
                tag_array = existing['CustomerGateway']['Tags']
                for key, value in enumerate(tag_array):
                    if value['Key'] == 'Name':
                        current_name = value['Value']
                        if current_name != name:
                            results['name'] = gw_mgr.tag_cgw_name(
                                results['gateway']['CustomerGateway']['CustomerGatewayId'],
                                module.params['name'],
                            )
                            results['changed'] = True
        else:
            if not module.check_mode:
                results['gateway'] = gw_mgr.ensure_cgw_present(
                    module.params['bgp_asn'],
                    module.params['ip_address'],
                )
                results['name'] = gw_mgr.tag_cgw_name(
                    results['gateway']['CustomerGateway']['CustomerGatewayId'],
                    module.params['name'],
                )
            results['changed'] = True

    elif module.params['state'] == 'absent':
        if existing['CustomerGateways']:
            existing['CustomerGateway'] = existing['CustomerGateways'][0]
            results['gateway'] = existing
            if not module.check_mode:
                results['gateway'] = gw_mgr.ensure_cgw_absent(
                    existing['CustomerGateway']['CustomerGatewayId']
                )
            results['changed'] = True

    pretty_results = camel_dict_to_snake_dict(results)
    module.exit_json(**pretty_results)


if __name__ == '__main__':
    main()

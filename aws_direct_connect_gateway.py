#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: aws_direct_connect_gateway
author: Gobin Sougrakpam (@gobins)
version_added: 1.0.0
short_description: Manage AWS Direct Connect gateway
description:
  - Creates AWS Direct Connect Gateway.
  - Deletes AWS Direct Connect Gateway.
  - Attaches Virtual Gateways to Direct Connect Gateway.
  - Detaches Virtual Gateways to Direct Connect Gateway.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

requirements: [ boto3 ]
options:
  state:
    description:
        - Set I(state=present) to ensure a resource is created.
        - Set I(state=absent) to remove a resource.
    default: present
    choices: [ "present", "absent"]
    type: str
  name:
    description:
        - Name of the Direct Connect Gateway to be created or deleted.
    type: str
  amazon_asn:
    description:
        - The Amazon side ASN.
        - Required when I(state=present).
    type: str
  direct_connect_gateway_id:
    description:
        - The ID of an existing Direct Connect Gateway.
        - Required when I(state=absent).
    type: str
  virtual_gateway_id:
    description:
        - The VPN gateway ID of an existing virtual gateway.
    type: str
  wait_timeout:
    description:
        - How long to wait for the association to be deleted.
    type: int
    default: 320
'''

EXAMPLES = '''
- name: Create a new direct connect gateway attached to virtual private gateway
  community.aws.aws_direct_connect_gateway:
    state: present
    name: my-dx-gateway
    amazon_asn: 7224
    virtual_gateway_id: vpg-12345
  register: created_dxgw

- name: Create a new unattached dxgw
  community.aws.aws_direct_connect_gateway:
    state: present
    name: my-dx-gateway
    amazon_asn: 7224
  register: created_dxgw

'''

RETURN = '''
result:
  description:
    - The attributes of the Direct Connect Gateway
  type: complex
  returned: I(state=present)
  contains:
    amazon_side_asn:
      description: ASN on the amazon side.
      type: str
    direct_connect_gateway_id:
      description: The ID of the direct connect gateway.
      type: str
    direct_connect_gateway_name:
      description: The name of the direct connect gateway.
      type: str
    direct_connect_gateway_state:
      description: The state of the direct connect gateway.
      type: str
    owner_account:
      description: The AWS account ID of the owner of the direct connect gateway.
      type: str
'''

import time
import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def dx_gateway_info(client, gateway_id, module):
    try:
        resp = client.describe_direct_connect_gateways(
            directConnectGatewayId=gateway_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    if resp['directConnectGateways']:
        return resp['directConnectGateways'][0]


def wait_for_status(client, module, gateway_id, virtual_gateway_id, status):
    polling_increment_secs = 15
    max_retries = 3
    status_achieved = False

    for x in range(0, max_retries):
        try:
            response = check_dxgw_association(
                client,
                module,
                gateway_id=gateway_id,
                virtual_gateway_id=virtual_gateway_id)
            if response['directConnectGatewayAssociations']:
                if response['directConnectGatewayAssociations'][0]['associationState'] == status:
                    status_achieved = True
                    break
                else:
                    time.sleep(polling_increment_secs)
            else:
                status_achieved = True
                break
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    result = response
    return status_achieved, result


def associate_direct_connect_gateway(client, module, gateway_id):
    params = dict()
    params['virtual_gateway_id'] = module.params.get('virtual_gateway_id')
    try:
        response = client.create_direct_connect_gateway_association(
            directConnectGatewayId=gateway_id,
            virtualGatewayId=params['virtual_gateway_id'])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    status_achieved, dxgw = wait_for_status(client, module, gateway_id, params['virtual_gateway_id'], 'associating')
    if not status_achieved:
        module.fail_json(msg='Error waiting for dxgw to attach to vpg - please check the AWS console')

    result = response
    return result


def delete_association(client, module, gateway_id, virtual_gateway_id):
    try:
        response = client.delete_direct_connect_gateway_association(
            directConnectGatewayId=gateway_id,
            virtualGatewayId=virtual_gateway_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    status_achieved, dxgw = wait_for_status(client, module, gateway_id, virtual_gateway_id, 'disassociating')
    if not status_achieved:
        module.fail_json(msg='Error waiting for  dxgw to detach from vpg - please check the AWS console')

    result = response
    return result


def create_dx_gateway(client, module):
    params = dict()
    params['name'] = module.params.get('name')
    params['amazon_asn'] = module.params.get('amazon_asn')
    try:
        response = client.create_direct_connect_gateway(
            directConnectGatewayName=params['name'],
            amazonSideAsn=int(params['amazon_asn']))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    result = response
    return result


def find_dx_gateway(client, module, gateway_id=None):
    params = dict()
    gateways = list()
    if gateway_id is not None:
        params['directConnectGatewayId'] = gateway_id
    while True:
        try:
            resp = client.describe_direct_connect_gateways(**params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        gateways.extend(resp['directConnectGateways'])
        if 'nextToken' in resp:
            params['nextToken'] = resp['nextToken']
        else:
            break
    if gateways != []:
        count = 0
        for gateway in gateways:
            if module.params.get('name') == gateway['directConnectGatewayName']:
                count += 1
                return gateway
    return None


def check_dxgw_association(client, module, gateway_id, virtual_gateway_id=None):
    try:
        if virtual_gateway_id is None:
            resp = client.describe_direct_connect_gateway_associations(
                directConnectGatewayId=gateway_id
            )
        else:
            resp = client.describe_direct_connect_gateway_associations(
                directConnectGatewayId=gateway_id,
                virtualGatewayId=virtual_gateway_id,
            )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    return resp


def ensure_present(client, module):
    # If an existing direct connect gateway matches our args
    # then a match is considered to have been found and we will not create another dxgw.

    changed = False
    params = dict()
    result = dict()
    params['name'] = module.params.get('name')
    params['amazon_asn'] = module.params.get('amazon_asn')
    params['virtual_gateway_id'] = module.params.get('virtual_gateway_id')

    # check if a gateway matching our module args already exists
    existing_dxgw = find_dx_gateway(client, module)

    if existing_dxgw is not None and existing_dxgw['directConnectGatewayState'] != 'deleted':
        gateway_id = existing_dxgw['directConnectGatewayId']
        # if a gateway_id was provided, check if it is attach to the DXGW
        if params['virtual_gateway_id']:
            resp = check_dxgw_association(
                client,
                module,
                gateway_id=gateway_id,
                virtual_gateway_id=params['virtual_gateway_id'])
            if not resp["directConnectGatewayAssociations"]:
                # attach the dxgw to the supplied virtual_gateway_id
                associate_direct_connect_gateway(client, module, gateway_id)
                changed = True
        # if params['virtual_gateway_id'] is not provided, check the dxgw is attached to a VPG. If so, detach it.
        else:
            existing_dxgw = find_dx_gateway(client, module)

            resp = check_dxgw_association(client, module, gateway_id=gateway_id)
            if resp["directConnectGatewayAssociations"]:
                for association in resp['directConnectGatewayAssociations']:
                    if association['associationState'] not in ['disassociating', 'disassociated']:
                        delete_association(
                            client,
                            module,
                            gateway_id=gateway_id,
                            virtual_gateway_id=association['virtualGatewayId'])
    else:
        # create a new dxgw
        new_dxgw = create_dx_gateway(client, module)
        changed = True
        gateway_id = new_dxgw['directConnectGateway']['directConnectGatewayId']

        # if a vpc-id was supplied, attempt to attach it to the dxgw
        if params['virtual_gateway_id']:
            associate_direct_connect_gateway(client, module, gateway_id)
            resp = check_dxgw_association(client,
                                          module,
                                          gateway_id=gateway_id
                                          )
            if resp["directConnectGatewayAssociations"]:
                changed = True

    result = dx_gateway_info(client, gateway_id, module)
    return changed, result


def ensure_absent(client, module):
    # If an existing direct connect gateway matches our args
    # then a match is considered to have been found and we will not create another dxgw.

    changed = False
    result = dict()
    dx_gateway_id = module.params.get('direct_connect_gateway_id')
    existing_dxgw = find_dx_gateway(client, module, dx_gateway_id)
    if existing_dxgw is not None:
        resp = check_dxgw_association(client, module,
                                      gateway_id=dx_gateway_id)
        if resp["directConnectGatewayAssociations"]:
            for association in resp['directConnectGatewayAssociations']:
                if association['associationState'] not in ['disassociating', 'disassociated']:
                    delete_association(client, module,
                                       gateway_id=dx_gateway_id,
                                       virtual_gateway_id=association['virtualGatewayId'])
        # wait for deleting association
        timeout = time.time() + module.params.get('wait_timeout')
        while time.time() < timeout:
            resp = check_dxgw_association(client,
                                          module,
                                          gateway_id=dx_gateway_id)
            if resp["directConnectGatewayAssociations"] != []:
                time.sleep(15)
            else:
                break

        try:
            resp = client.delete_direct_connect_gateway(
                directConnectGatewayId=dx_gateway_id
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        result = resp['directConnectGateway']
    return changed


def main():
    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(),
        amazon_asn=dict(),
        virtual_gateway_id=dict(),
        direct_connect_gateway_id=dict(),
        wait_timeout=dict(type='int', default=320),
    )
    required_if = [('state', 'present', ['name', 'amazon_asn']),
                   ('state', 'absent', ['direct_connect_gateway_id'])]
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=required_if)

    state = module.params.get('state')

    try:
        client = module.client('directconnect')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    if state == 'present':
        (changed, results) = ensure_present(client, module)
    elif state == 'absent':
        changed = ensure_absent(client, module)
        results = {}

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()

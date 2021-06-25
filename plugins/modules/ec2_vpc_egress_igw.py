#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_egress_igw
version_added: 1.0.0
short_description: Manage an AWS VPC Egress Only Internet gateway
description:
    - Manage an AWS VPC Egress Only Internet gateway
author: Daniel Shepherd (@shepdelacreme)
options:
  vpc_id:
    description:
      - The VPC ID for the VPC that this Egress Only Internet Gateway should be attached.
    required: true
    type: str
  state:
    description:
      - Create or delete the EIGW.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{eigw.gateway_id}} for use in setting up NATs etc.
- community.aws.ec2_vpc_egress_igw:
    vpc_id: vpc-abcdefgh
    state: present
  register: eigw

'''

RETURN = '''
gateway_id:
    description: The ID of the Egress Only Internet Gateway or Null.
    returned: always
    type: str
    sample: eigw-0e00cf111ba5bc11e
vpc_id:
    description: The ID of the VPC to attach or detach gateway from.
    returned: always
    type: str
    sample: vpc-012345678
'''


from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


def delete_eigw(module, conn, eigw_id):
    """
    Delete EIGW.

    module     : AnsibleAWSModule object
    conn       : boto3 client connection object
    eigw_id    : ID of the EIGW to delete
    """
    changed = False

    try:
        response = conn.delete_egress_only_internet_gateway(DryRun=module.check_mode, EgressOnlyInternetGatewayId=eigw_id)
    except botocore.exceptions.ClientError as e:
        # When boto3 method is run with DryRun=True it returns an error on success
        # We need to catch the error and return something valid
        if e.response.get('Error', {}).get('Code') == "DryRunOperation":
            changed = True
        else:
            module.fail_json_aws(e, msg="Could not delete Egress-Only Internet Gateway {0} from VPC {1}".format(eigw_id, module.vpc_id))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Could not delete Egress-Only Internet Gateway {0} from VPC {1}".format(eigw_id, module.vpc_id))

    if not module.check_mode:
        changed = response.get('ReturnCode', False)

    return changed


def create_eigw(module, conn, vpc_id):
    """
    Create EIGW.

    module       : AnsibleAWSModule object
    conn         : boto3 client connection object
    vpc_id       : ID of the VPC we are operating on
    """
    gateway_id = None
    changed = False

    try:
        response = conn.create_egress_only_internet_gateway(DryRun=module.check_mode, VpcId=vpc_id)
    except botocore.exceptions.ClientError as e:
        # When boto3 method is run with DryRun=True it returns an error on success
        # We need to catch the error and return something valid
        if e.response.get('Error', {}).get('Code') == "DryRunOperation":
            changed = True
        elif e.response.get('Error', {}).get('Code') == "InvalidVpcID.NotFound":
            module.fail_json_aws(e, msg="invalid vpc ID '{0}' provided".format(vpc_id))
        else:
            module.fail_json_aws(e, msg="Could not create Egress-Only Internet Gateway for vpc ID {0}".format(vpc_id))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Could not create Egress-Only Internet Gateway for vpc ID {0}".format(vpc_id))

    if not module.check_mode:
        gateway = response.get('EgressOnlyInternetGateway', {})
        state = gateway.get('Attachments', [{}])[0].get('State')
        gateway_id = gateway.get('EgressOnlyInternetGatewayId')

        if gateway_id and state in ('attached', 'attaching'):
            changed = True
        else:
            # EIGW gave back a bad attachment state or an invalid response so we error out
            module.fail_json(msg='Unable to create and attach Egress Only Internet Gateway to VPCId: {0}. Bad or no state in response'.format(vpc_id),
                             **camel_dict_to_snake_dict(response))

    return changed, gateway_id


def describe_eigws(module, conn, vpc_id):
    """
    Describe EIGWs.

    module     : AnsibleAWSModule object
    conn       : boto3 client connection object
    vpc_id     : ID of the VPC we are operating on
    """
    gateway_id = None

    try:
        response = conn.describe_egress_only_internet_gateways()
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Could not get list of existing Egress-Only Internet Gateways")

    for eigw in response.get('EgressOnlyInternetGateways', []):
        for attachment in eigw.get('Attachments', []):
            if attachment.get('VpcId') == vpc_id and attachment.get('State') in ('attached', 'attaching'):
                gateway_id = eigw.get('EgressOnlyInternetGatewayId')

    return gateway_id


def main():
    argument_spec = dict(
        vpc_id=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('ec2')

    vpc_id = module.params.get('vpc_id')
    state = module.params.get('state')

    eigw_id = describe_eigws(module, connection, vpc_id)

    result = dict(gateway_id=eigw_id, vpc_id=vpc_id)
    changed = False

    if state == 'present' and not eigw_id:
        changed, result['gateway_id'] = create_eigw(module, connection, vpc_id)
    elif state == 'absent' and eigw_id:
        changed = delete_eigw(module, connection, eigw_id)

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()

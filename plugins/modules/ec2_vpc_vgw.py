#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: ec2_vpc_vgw
short_description: Create and delete AWS VPN Virtual Gateways
version_added: 1.0.0
description:
  - Creates AWS VPN Virtual Gateways
  - Deletes AWS VPN Virtual Gateways
  - Attaches Virtual Gateways to VPCs
  - Detaches Virtual Gateways from VPCs
options:
  state:
    description:
      - C(present) to ensure resource is created.
      - C(absent) to remove resource.
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
  - Support for I(purge_tags) was added in release 4.0.0.
author:
  - Nick Aslanidis (@naslanidis)
extends_documentation_fragment:
  - amazon.aws.ec2
  - amazon.aws.aws
  - amazon.aws.tags
'''

EXAMPLES = '''
- name: Create a new VGW attached to a specific VPC
  community.aws.ec2_vpc_vgw:
    state: present
    region: ap-southeast-2
    profile: personal
    vpc_id: vpc-12345678
    name: personal-testing
    type: ipsec.1
  register: created_vgw

- name: Create a new unattached VGW
  community.aws.ec2_vpc_vgw:
    state: present
    region: ap-southeast-2
    profile: personal
    name: personal-testing
    type: ipsec.1
    tags:
      environment: production
      owner: ABC
  register: created_vgw

- name: Remove a new VGW using the name
  community.aws.ec2_vpc_vgw:
    state: absent
    region: ap-southeast-2
    profile: personal
    name: personal-testing
    type: ipsec.1
  register: deleted_vgw

- name: Remove a new VGW using the vpn_gateway_id
  community.aws.ec2_vpc_vgw:
    state: absent
    region: ap-southeast-2
    profile: personal
    vpn_gateway_id: vgw-3a9aa123
  register: deleted_vgw
'''

RETURN = '''
vgw:
  description: A description of the VGW
  returned: success
  type: dict
  contains:
    id:
      description: The ID of the VGW.
      type: str
      returned: success
      example: "vgw-0123456789abcdef0"
    state:
      description: The state of the VGW.
      type: str
      returned: success
      example: "available"
    tags:
      description: A dictionary representing the tags attached to the VGW
      type: dict
      returned: success
      example: { "Name": "ansible-test-ec2-vpc-vgw" }
    type:
      description: The type of VPN connection the virtual private gateway supports.
      type: str
      returned: success
      example: "ipsec.1"
    vpc_id:
      description: The ID of the VPC to which the VGW is attached.
      type: str
      returned: success
      example: vpc-123456789abcdef01
'''

import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


# AWS uses VpnGatewayLimitExceeded for both 'Too many VGWs' and 'Too many concurrent changes'
# we need to look at the mesage to tell the difference.
class VGWRetry(AWSRetry):
    @staticmethod
    def status_code_from_exception(error):
        return (error.response['Error']['Code'], error.response['Error']['Message'],)

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        retry_on = ['The maximum number of mutating objects has been reached.']

        if catch_extra_error_codes:
            retry_on.extend(catch_extra_error_codes)
        if not isinstance(response_code, tuple):
            response_code = (response_code,)

        for code in response_code:
            if super().found(response_code, catch_extra_error_codes):
                return True

        return False


def get_vgw_info(vgws):
    if not isinstance(vgws, list):
        return

    for vgw in vgws:
        vgw_info = {
            'id': vgw['VpnGatewayId'],
            'type': vgw['Type'],
            'state': vgw['State'],
            'vpc_id': None,
            'tags': dict()
        }

        if vgw['Tags']:
            vgw_info['tags'] = boto3_tag_list_to_ansible_dict(vgw['Tags'])

        if len(vgw['VpcAttachments']) != 0 and vgw['VpcAttachments'][0]['State'] == 'attached':
            vgw_info['vpc_id'] = vgw['VpcAttachments'][0]['VpcId']

        return vgw_info


def wait_for_status(client, module, vpn_gateway_id, status):
    polling_increment_secs = 15
    max_retries = (module.params.get('wait_timeout') // polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        try:
            response = find_vgw(client, module, vpn_gateway_id)
            if response[0]['VpcAttachments'][0]['State'] == status:
                status_achieved = True
                break
            else:
                time.sleep(polling_increment_secs)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failure while waiting for status update')

    result = response
    return status_achieved, result


def attach_vgw(client, module, vpn_gateway_id):
    params = dict()
    params['VpcId'] = module.params.get('vpc_id')

    try:
        # Immediately after a detachment, the EC2 API sometimes will report the VpnGateways[0].State
        # as available several seconds before actually permitting a new attachment.
        # So we catch and retry that error.  See https://github.com/ansible/ansible/issues/53185
        response = VGWRetry.jittered_backoff(retries=5,
                                             catch_extra_error_codes=['InvalidParameterValue']
                                             )(client.attach_vpn_gateway)(VpnGatewayId=vpn_gateway_id,
                                                                          VpcId=params['VpcId'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to attach VPC')

    status_achieved, vgw = wait_for_status(client, module, [vpn_gateway_id], 'attached')
    if not status_achieved:
        module.fail_json(msg='Error waiting for vpc to attach to vgw - please check the AWS console')

    result = response
    return result


def detach_vgw(client, module, vpn_gateway_id, vpc_id=None):
    params = dict()
    params['VpcId'] = module.params.get('vpc_id')

    try:
        if vpc_id:
            response = client.detach_vpn_gateway(VpnGatewayId=vpn_gateway_id, VpcId=vpc_id, aws_retry=True)
        else:
            response = client.detach_vpn_gateway(VpnGatewayId=vpn_gateway_id, VpcId=params['VpcId'], aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, 'Failed to detach gateway')

    status_achieved, vgw = wait_for_status(client, module, [vpn_gateway_id], 'detached')
    if not status_achieved:
        module.fail_json(msg='Error waiting for  vpc to detach from vgw - please check the AWS console')

    result = response
    return result


def create_vgw(client, module):
    params = dict()
    params['Type'] = module.params.get('type')
    tags = module.params.get('tags') or {}
    tags['Name'] = module.params.get('name')
    params['TagSpecifications'] = boto3_tag_specifications(tags, ['vpn-gateway'])
    if module.params.get('asn'):
        params['AmazonSideAsn'] = module.params.get('asn')

    try:
        response = client.create_vpn_gateway(aws_retry=True, **params)
        get_waiter(
            client, 'vpn_gateway_exists'
        ).wait(
            VpnGatewayIds=[response['VpnGateway']['VpnGatewayId']]
        )
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="Failed to wait for Vpn Gateway {0} to be available".format(response['VpnGateway']['VpnGatewayId']))
    except is_boto3_error_code('VpnGatewayLimitExceeded') as e:
        module.fail_json_aws(e, msg="Too many VPN gateways exist in this account.")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to create gateway')

    result = response
    return result


def delete_vgw(client, module, vpn_gateway_id):

    try:
        response = client.delete_vpn_gateway(VpnGatewayId=vpn_gateway_id, aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to delete gateway')

    # return the deleted VpnGatewayId as this is not included in the above response
    result = vpn_gateway_id
    return result


def find_vpc(client, module):
    params = dict()
    params['vpc_id'] = module.params.get('vpc_id')

    if params['vpc_id']:
        try:
            response = client.describe_vpcs(VpcIds=[params['vpc_id']], aws_retry=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to describe VPC')

    result = response
    return result


def find_vgw(client, module, vpn_gateway_id=None):
    params = dict()
    if vpn_gateway_id:
        params['VpnGatewayIds'] = vpn_gateway_id
    else:
        params['Filters'] = [
            {'Name': 'type', 'Values': [module.params.get('type')]},
            {'Name': 'tag:Name', 'Values': [module.params.get('name')]},
        ]
        if module.params.get('state') == 'present':
            params['Filters'].append({'Name': 'state', 'Values': ['pending', 'available']})
    try:
        response = client.describe_vpn_gateways(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe gateway using filters')

    return sorted(response['VpnGateways'], key=lambda k: k['VpnGatewayId'])


def ensure_vgw_present(client, module):

    # If an existing vgw name and type matches our args, then a match is considered to have been
    # found and we will not create another vgw.

    changed = False
    params = dict()
    result = dict()
    params['Name'] = module.params.get('name')
    params['VpcId'] = module.params.get('vpc_id')
    params['Type'] = module.params.get('type')
    params['Tags'] = module.params.get('tags')
    params['VpnGatewayIds'] = module.params.get('vpn_gateway_id')

    # check that the vpc_id exists. If not, an exception is thrown
    if params['VpcId']:
        vpc = find_vpc(client, module)

    # check if a gateway matching our module args already exists
    existing_vgw = find_vgw(client, module)

    if existing_vgw != []:
        vpn_gateway_id = existing_vgw[0]['VpnGatewayId']
        desired_tags = module.params.get('tags')
        purge_tags = module.params.get('purge_tags')
        if desired_tags is None:
            desired_tags = dict()
            purge_tags = False
        tags = dict(Name=module.params.get('name'))
        tags.update(desired_tags)
        changed = ensure_ec2_tags(client, module, vpn_gateway_id, resource_type='vpn-gateway',
                                  tags=tags, purge_tags=purge_tags)

        # if a vpc_id was provided, check if it exists and if it's attached
        if params['VpcId']:

            current_vpc_attachments = existing_vgw[0]['VpcAttachments']

            if current_vpc_attachments != [] and current_vpc_attachments[0]['State'] == 'attached':
                if current_vpc_attachments[0]['VpcId'] != params['VpcId'] or current_vpc_attachments[0]['State'] != 'attached':
                    # detach the existing vpc from the virtual gateway
                    vpc_to_detach = current_vpc_attachments[0]['VpcId']
                    detach_vgw(client, module, vpn_gateway_id, vpc_to_detach)
                    get_waiter(client, 'vpn_gateway_detached').wait(VpnGatewayIds=[vpn_gateway_id])
                    attached_vgw = attach_vgw(client, module, vpn_gateway_id)
                    changed = True
            else:
                # attach the vgw to the supplied vpc
                attached_vgw = attach_vgw(client, module, vpn_gateway_id)
                changed = True

        # if params['VpcId'] is not provided, check the vgw is attached to a vpc. if so, detach it.
        else:
            existing_vgw = find_vgw(client, module, [vpn_gateway_id])

            if existing_vgw[0]['VpcAttachments'] != []:
                if existing_vgw[0]['VpcAttachments'][0]['State'] == 'attached':
                    # detach the vpc from the vgw
                    vpc_to_detach = existing_vgw[0]['VpcAttachments'][0]['VpcId']
                    detach_vgw(client, module, vpn_gateway_id, vpc_to_detach)
                    changed = True

    else:
        # create a new vgw
        new_vgw = create_vgw(client, module)
        changed = True
        vpn_gateway_id = new_vgw['VpnGateway']['VpnGatewayId']

        # if a vpc-id was supplied, attempt to attach it to the vgw
        if params['VpcId']:
            attached_vgw = attach_vgw(client, module, vpn_gateway_id)
            changed = True

    # return current state of the vgw
    vgw = find_vgw(client, module, [vpn_gateway_id])
    result = get_vgw_info(vgw)
    return changed, result


def ensure_vgw_absent(client, module):

    # If an existing vgw name and type matches our args, then a match is considered to have been
    # found and we will take steps to delete it.

    changed = False
    params = dict()
    result = dict()
    params['Name'] = module.params.get('name')
    params['VpcId'] = module.params.get('vpc_id')
    params['Type'] = module.params.get('type')
    params['Tags'] = module.params.get('tags')
    params['VpnGatewayIds'] = module.params.get('vpn_gateway_id')

    # check if a gateway matching our module args already exists
    if params['VpnGatewayIds']:
        existing_vgw_with_id = find_vgw(client, module, [params['VpnGatewayIds']])
        if existing_vgw_with_id != [] and existing_vgw_with_id[0]['State'] != 'deleted':
            existing_vgw = existing_vgw_with_id
            if existing_vgw[0]['VpcAttachments'] != [] and existing_vgw[0]['VpcAttachments'][0]['State'] == 'attached':
                if params['VpcId']:
                    if params['VpcId'] != existing_vgw[0]['VpcAttachments'][0]['VpcId']:
                        module.fail_json(msg='The vpc-id provided does not match the vpc-id currently attached - please check the AWS console')

                    else:
                        # detach the vpc from the vgw
                        detach_vgw(client, module, params['VpnGatewayIds'], params['VpcId'])
                        deleted_vgw = delete_vgw(client, module, params['VpnGatewayIds'])
                        changed = True

                else:
                    # attempt to detach any attached vpcs
                    vpc_to_detach = existing_vgw[0]['VpcAttachments'][0]['VpcId']
                    detach_vgw(client, module, params['VpnGatewayIds'], vpc_to_detach)
                    deleted_vgw = delete_vgw(client, module, params['VpnGatewayIds'])
                    changed = True

            else:
                # no vpc's are attached so attempt to delete the vgw
                deleted_vgw = delete_vgw(client, module, params['VpnGatewayIds'])
                changed = True

        else:
            changed = False
            deleted_vgw = "Nothing to do"

    else:
        # Check that a name and type argument has been supplied if no vgw-id
        if not module.params.get('name') or not module.params.get('type'):
            module.fail_json(msg='A name and type is required when no vgw-id and a status of \'absent\' is supplied')

        existing_vgw = find_vgw(client, module)
        if existing_vgw != [] and existing_vgw[0]['State'] != 'deleted':
            vpn_gateway_id = existing_vgw[0]['VpnGatewayId']
            if existing_vgw[0]['VpcAttachments'] != [] and existing_vgw[0]['VpcAttachments'][0]['State'] == 'attached':
                if params['VpcId']:
                    if params['VpcId'] != existing_vgw[0]['VpcAttachments'][0]['VpcId']:
                        module.fail_json(msg='The vpc-id provided does not match the vpc-id currently attached - please check the AWS console')

                    else:
                        # detach the vpc from the vgw
                        detach_vgw(client, module, vpn_gateway_id, params['VpcId'])

                        # now that the vpc has been detached, delete the vgw
                        deleted_vgw = delete_vgw(client, module, vpn_gateway_id)
                        changed = True

                else:
                    # attempt to detach any attached vpcs
                    vpc_to_detach = existing_vgw[0]['VpcAttachments'][0]['VpcId']
                    detach_vgw(client, module, vpn_gateway_id, vpc_to_detach)
                    changed = True

                    # now that the vpc has been detached, delete the vgw
                    deleted_vgw = delete_vgw(client, module, vpn_gateway_id)

            else:
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
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(),
        vpn_gateway_id=dict(),
        vpc_id=dict(),
        asn=dict(type='int'),
        wait_timeout=dict(type='int', default=320),
        type=dict(default='ipsec.1', choices=['ipsec.1']),
        tags=dict(default=None, required=False, type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['state', 'present', ['name']]])

    state = module.params.get('state').lower()

    client = module.client('ec2', retry_decorator=VGWRetry.jittered_backoff(retries=10))

    if state == 'present':
        (changed, results) = ensure_vgw_present(client, module)
    else:
        (changed, results) = ensure_vgw_absent(client, module)
    module.exit_json(changed=changed, vgw=results)


if __name__ == '__main__':
    main()

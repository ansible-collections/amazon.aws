#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_net
version_added: 1.0.0
short_description: Configure AWS virtual private clouds
description:
    - Create, modify, and terminate AWS virtual private clouds.
author:
  - Jonathan Davila (@defionscode)
  - Sloane Hertel (@s-hertel)
options:
  name:
    description:
      - The name to give your VPC. This is used in combination with C(cidr_block) to determine if a VPC already exists.
    required: yes
    type: str
  cidr_block:
    description:
      - The primary CIDR of the VPC. After 2.5 a list of CIDRs can be provided. The first in the list will be used as the primary CIDR
        and is used in conjunction with the C(name) to ensure idempotence.
    required: yes
    type: list
    elements: str
  ipv6_cidr:
    description:
      - Request an Amazon-provided IPv6 CIDR block with /56 prefix length. You cannot specify the range of IPv6 addresses,
        or the size of the CIDR block.
      - Default value is C(false) when creating a new VPC.
    type: bool
  purge_cidrs:
    description:
      - Remove CIDRs that are associated with the VPC and are not specified in C(cidr_block).
    default: no
    type: bool
  tenancy:
    description:
      - Whether to be default or dedicated tenancy. This cannot be changed after the VPC has been created.
    default: default
    choices: [ 'default', 'dedicated' ]
    type: str
  dns_support:
    description:
      - Whether to enable AWS DNS support.
    default: yes
    type: bool
  dns_hostnames:
    description:
      - Whether to enable AWS hostname support.
    default: yes
    type: bool
  dhcp_opts_id:
    description:
      - The id of the DHCP options to use for this VPC.
    type: str
  tags:
    description:
      - The tags you want attached to the VPC. This is independent of the name value, note if you pass a 'Name' key it would override the Name of
        the VPC if it's different.
    aliases: [ 'resource_tags' ]
    type: dict
  state:
    description:
      - The state of the VPC. Either absent or present.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  multi_ok:
    description:
      - By default the module will not create another VPC if there is another VPC with the same name and CIDR block. Specify this as true if you want
        duplicate VPCs created.
    type: bool
    default: false
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a VPC with dedicated tenancy and a couple of tags
  amazon.aws.ec2_vpc_net:
    name: Module_dev2
    cidr_block: 10.10.0.0/16
    region: us-east-1
    tags:
      module: ec2_vpc_net
      this: works
    tenancy: dedicated

- name: create a VPC with dedicated tenancy and request an IPv6 CIDR
  amazon.aws.ec2_vpc_net:
    name: Module_dev2
    cidr_block: 10.10.0.0/16
    ipv6_cidr: True
    region: us-east-1
    tenancy: dedicated
'''

RETURN = '''
vpc:
  description: info about the VPC that was created or deleted
  returned: always
  type: complex
  contains:
    cidr_block:
      description: The CIDR of the VPC
      returned: always
      type: str
      sample: 10.0.0.0/16
    cidr_block_association_set:
      description: IPv4 CIDR blocks associated with the VPC
      returned: success
      type: list
      sample:
        "cidr_block_association_set": [
            {
                "association_id": "vpc-cidr-assoc-97aeeefd",
                "cidr_block": "10.0.0.0/24",
                "cidr_block_state": {
                    "state": "associated"
                }
            }
        ]
    classic_link_enabled:
      description: indicates whether ClassicLink is enabled
      returned: always
      type: bool
      sample: false
    dhcp_options_id:
      description: the id of the DHCP options associated with this VPC
      returned: always
      type: str
      sample: dopt-12345678
    id:
      description: VPC resource id
      returned: always
      type: str
      sample: vpc-12345678
    instance_tenancy:
      description: indicates whether VPC uses default or dedicated tenancy
      returned: always
      type: str
      sample: default
    ipv6_cidr_block_association_set:
      description: IPv6 CIDR blocks associated with the VPC
      returned: success
      type: list
      sample:
        "ipv6_cidr_block_association_set": [
            {
                "association_id": "vpc-cidr-assoc-97aeeefd",
                "ipv6_cidr_block": "2001:db8::/56",
                "ipv6_cidr_block_state": {
                    "state": "associated"
                }
            }
        ]
    is_default:
      description: indicates whether this is the default VPC
      returned: always
      type: bool
      sample: false
    state:
      description: state of the VPC
      returned: always
      type: str
      sample: available
    tags:
      description: tags attached to the VPC, includes name
      returned: always
      type: complex
      contains:
        Name:
          description: name tag for the VPC
          returned: always
          type: str
          sample: pk_vpc4
    owner_id:
      description: The AWS account which owns the VPC.
      returned: always
      type: str
      sample: 123456789012
'''

from time import sleep
from time import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.network import to_subnet
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.core import is_boto3_error_message
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ..module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ..module_utils.ec2 import compare_aws_tags
from ..module_utils.waiters import get_waiter


def vpc_exists(module, vpc, name, cidr_block, multi):
    """Returns None or a vpc object depending on the existence of a VPC. When supplied
    with a CIDR, it will check for matching tags to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return None.
    """
    try:
        vpc_filters = ansible_dict_to_boto3_filter_list({'tag:Name': name, 'cidr-block': cidr_block})
        matching_vpcs = vpc.describe_vpcs(aws_retry=True, Filters=vpc_filters)['Vpcs']
        # If an exact matching using a list of CIDRs isn't found, check for a match with the first CIDR as is documented for C(cidr_block)
        if not matching_vpcs:
            vpc_filters = ansible_dict_to_boto3_filter_list({'tag:Name': name, 'cidr-block': [cidr_block[0]]})
            matching_vpcs = vpc.describe_vpcs(aws_retry=True, Filters=vpc_filters)['Vpcs']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")

    if multi:
        return None
    elif len(matching_vpcs) == 1:
        return matching_vpcs[0]['VpcId']
    elif len(matching_vpcs) > 1:
        module.fail_json(msg='Currently there are %d VPCs that have the same name and '
                             'CIDR block you specified. If you would like to create '
                             'the VPC anyway please pass True to the multi_ok param.' % len(matching_vpcs))
    return None


def get_classic_link_status(module, connection, vpc_id):
    try:
        results = connection.describe_vpc_classic_link(aws_retry=True, VpcIds=[vpc_id])
        return results['Vpcs'][0].get('ClassicLinkEnabled')
    except is_boto3_error_message('The functionality you requested is not available in this region.'):
        return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe VPCs")


def wait_for_vpc_to_exist(module, connection, **params):
    # wait for vpc to be available
    try:
        get_waiter(connection, 'vpc_exists').wait(**params)
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="VPC failed to reach expected state (exists)")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to wait for VPC creation.")


def wait_for_vpc(module, connection, **params):
    # wait for vpc to be available
    try:
        get_waiter(connection, 'vpc_available').wait(**params)
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="VPC failed to reach expected state (available)")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to wait for VPC state to update.")


def get_vpc(module, connection, vpc_id):
    wait_for_vpc(module, connection, VpcIds=[vpc_id])
    try:
        vpc_obj = connection.describe_vpcs(VpcIds=[vpc_id], aws_retry=True)['Vpcs'][0]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")

    vpc_obj['ClassicLinkEnabled'] = get_classic_link_status(module, connection, vpc_id)

    return vpc_obj


def update_vpc_tags(connection, module, vpc_id, tags, name):
    if tags is None:
        tags = dict()

    tags.update({'Name': name})
    tags = dict((k, to_native(v)) for k, v in tags.items())
    try:
        filters = ansible_dict_to_boto3_filter_list({'resource-id': vpc_id})
        current_tags = dict((t['Key'], t['Value']) for t in connection.describe_tags(Filters=filters, aws_retry=True)['Tags'])
        tags_to_update, dummy = compare_aws_tags(current_tags, tags, False)
        if tags_to_update:
            if not module.check_mode:
                tags = ansible_dict_to_boto3_tag_list(tags_to_update)
                vpc_obj = connection.create_tags(Resources=[vpc_id], Tags=tags, aws_retry=True)

                # Wait for tags to be updated
                expected_tags = boto3_tag_list_to_ansible_dict(tags)
                filters = [{'Name': 'tag:{0}'.format(key), 'Values': [value]} for key, value in expected_tags.items()]
                wait_for_vpc(module, connection, VpcIds=[vpc_id], Filters=filters)

            return True
        else:
            return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update tags")


def update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
    if vpc_obj['DhcpOptionsId'] != dhcp_id:
        if not module.check_mode:
            try:
                connection.associate_dhcp_options(DhcpOptionsId=dhcp_id, VpcId=vpc_obj['VpcId'], aws_retry=True)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to associate DhcpOptionsId {0}".format(dhcp_id))

            # Wait for DhcpOptionsId to be updated
            filters = [{'Name': 'dhcp-options-id', 'Values': [dhcp_id]}]
            wait_for_vpc(module, connection, VpcIds=[vpc_obj['VpcId']], Filters=filters)

        return True
    else:
        return False


def create_vpc(connection, module, cidr_block, tenancy):
    try:
        if not module.check_mode:
            vpc_obj = connection.create_vpc(CidrBlock=cidr_block, InstanceTenancy=tenancy, aws_retry=True)
        else:
            module.exit_json(changed=True, msg="VPC would be created if not in check mode")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to create the VPC")

    # wait up to 30 seconds for vpc to exist
    wait_for_vpc_to_exist(
        module, connection,
        VpcIds=[vpc_obj['Vpc']['VpcId']],
        WaiterConfig=dict(MaxAttempts=30)
    )
    # Wait for the VPC to enter an 'Available' State
    wait_for_vpc_to_exist(
        module, connection,
        VpcIds=[vpc_obj['Vpc']['VpcId']],
        WaiterConfig=dict(MaxAttempts=30)
    )

    return vpc_obj['Vpc']['VpcId']


def wait_for_vpc_attribute(connection, module, vpc_id, attribute, expected_value):
    start_time = time()
    updated = False
    while time() < start_time + 300:
        current_value = connection.describe_vpc_attribute(
            Attribute=attribute,
            VpcId=vpc_id,
            aws_retry=True
        )['{0}{1}'.format(attribute[0].upper(), attribute[1:])]['Value']
        if current_value != expected_value:
            sleep(3)
        else:
            updated = True
            break
    if not updated:
        module.fail_json(msg="Failed to wait for {0} to be updated".format(attribute))


def wait_for_vpc_ipv6_state(module, connection, vpc_id, ipv6_assoc_state):
    """
    If ipv6_assoc_state is True, wait for VPC to be associated with at least one Amazon-provided IPv6 CIDR block.
    If ipv6_assoc_state is False, wait for VPC to be dissociated from all Amazon-provided IPv6 CIDR blocks.
    """
    start_time = time()
    criteria_match = False
    while time() < start_time + 300:
        current_value = get_vpc(module, connection, vpc_id)
        if current_value:
            ipv6_set = current_value.get('Ipv6CidrBlockAssociationSet')
            if ipv6_set:
                if ipv6_assoc_state:
                    # At least one 'Amazon' IPv6 CIDR block must be associated.
                    for val in ipv6_set:
                        if val.get('Ipv6Pool') == 'Amazon' and val.get("Ipv6CidrBlockState").get("State") == "associated":
                            criteria_match = True
                            break
                    if criteria_match:
                        break
                else:
                    # All 'Amazon' IPv6 CIDR blocks must be disassociated.
                    expected_count = sum(
                        [(val.get("Ipv6Pool") == "Amazon") for val in ipv6_set])
                    actual_count = sum([(val.get('Ipv6Pool') == 'Amazon' and
                                         val.get("Ipv6CidrBlockState").get("State") == "disassociated") for val in ipv6_set])
                    if actual_count == expected_count:
                        criteria_match = True
                        break
        sleep(3)
    if not criteria_match:
        module.fail_json(msg="Failed to wait for IPv6 CIDR association")


def get_cidr_network_bits(module, cidr_block):
    fixed_cidrs = []
    for cidr in cidr_block:
        split_addr = cidr.split('/')
        if len(split_addr) == 2:
            # this_ip is a IPv4 CIDR that may or may not have host bits set
            # Get the network bits.
            valid_cidr = to_subnet(split_addr[0], split_addr[1])
            if cidr != valid_cidr:
                module.warn("One of your CIDR addresses ({0}) has host bits set. To get rid of this warning, "
                            "check the network mask and make sure that only network bits are set: {1}.".format(cidr, valid_cidr))
            fixed_cidrs.append(valid_cidr)
        else:
            # let AWS handle invalid CIDRs
            fixed_cidrs.append(cidr)
    return fixed_cidrs


def main():
    argument_spec = dict(
        name=dict(required=True),
        cidr_block=dict(type='list', required=True, elements='str'),
        ipv6_cidr=dict(type='bool', default=None),
        tenancy=dict(choices=['default', 'dedicated'], default='default'),
        dns_support=dict(type='bool', default=True),
        dns_hostnames=dict(type='bool', default=True),
        dhcp_opts_id=dict(),
        tags=dict(type='dict', aliases=['resource_tags']),
        state=dict(choices=['present', 'absent'], default='present'),
        multi_ok=dict(type='bool', default=False),
        purge_cidrs=dict(type='bool', default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    name = module.params.get('name')
    cidr_block = get_cidr_network_bits(module, module.params.get('cidr_block'))
    ipv6_cidr = module.params.get('ipv6_cidr')
    purge_cidrs = module.params.get('purge_cidrs')
    tenancy = module.params.get('tenancy')
    dns_support = module.params.get('dns_support')
    dns_hostnames = module.params.get('dns_hostnames')
    dhcp_id = module.params.get('dhcp_opts_id')
    tags = module.params.get('tags')
    state = module.params.get('state')
    multi = module.params.get('multi_ok')

    changed = False

    connection = module.client(
        'ec2',
        retry_decorator=AWSRetry.jittered_backoff(
            retries=8, delay=3, catch_extra_error_codes=['InvalidVpcID.NotFound']
        )
    )

    if dns_hostnames and not dns_support:
        module.fail_json(msg='In order to enable DNS Hostnames you must also enable DNS support')

    if state == 'present':

        # Check if VPC exists
        vpc_id = vpc_exists(module, connection, name, cidr_block, multi)
        is_new_vpc = False
        if vpc_id is None:
            is_new_vpc = True
            vpc_id = create_vpc(connection, module, cidr_block[0], tenancy)
            changed = True
            if ipv6_cidr is None:
                # default value when creating new VPC.
                ipv6_cidr = False

        vpc_obj = get_vpc(module, connection, vpc_id)
        if not is_new_vpc and ipv6_cidr is None:
            # 'ipv6_cidr' wasn't specified in the task.
            # Retain the value from the existing VPC.
            ipv6_cidr = False
            if 'Ipv6CidrBlockAssociationSet' in vpc_obj.keys():
                for ipv6_assoc in vpc_obj['Ipv6CidrBlockAssociationSet']:
                    if ipv6_assoc['Ipv6Pool'] == 'Amazon' and ipv6_assoc['Ipv6CidrBlockState']['State'] in ['associated', 'associating']:
                        ipv6_cidr = True
                        break

        associated_cidrs = dict((cidr['CidrBlock'], cidr['AssociationId']) for cidr in vpc_obj.get('CidrBlockAssociationSet', [])
                                if cidr['CidrBlockState']['State'] != 'disassociated')
        to_add = [cidr for cidr in cidr_block if cidr not in associated_cidrs]
        to_remove = [associated_cidrs[cidr] for cidr in associated_cidrs if cidr not in cidr_block]
        expected_cidrs = [cidr for cidr in associated_cidrs if associated_cidrs[cidr] not in to_remove] + to_add

        if len(cidr_block) > 1:
            for cidr in to_add:
                changed = True
                if not module.check_mode:
                    try:
                        connection.associate_vpc_cidr_block(CidrBlock=cidr, VpcId=vpc_id, aws_retry=True)
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, "Unable to associate CIDR {0}.".format(ipv6_cidr))
        if ipv6_cidr:
            if 'Ipv6CidrBlockAssociationSet' not in vpc_obj.keys():
                changed = True
                if not module.check_mode:
                    try:
                        connection.associate_vpc_cidr_block(AmazonProvidedIpv6CidrBlock=ipv6_cidr, VpcId=vpc_id, aws_retry=True)
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, "Unable to associate CIDR {0}.".format(ipv6_cidr))
            else:
                # If the VPC has been created with IPv6 CIDR, and the ipv6 blocks were subsequently
                # disassociated, a Amazon-provide block must be associate a new block.
                assoc_needed = True
                for ipv6_assoc in vpc_obj['Ipv6CidrBlockAssociationSet']:
                    if ipv6_assoc['Ipv6Pool'] == 'Amazon' and ipv6_assoc['Ipv6CidrBlockState']['State'] in ['associated', 'associating']:
                        assoc_needed = False
                        break
                if assoc_needed:
                    changed = True
                    if not module.check_mode:
                        try:
                            connection.associate_vpc_cidr_block(AmazonProvidedIpv6CidrBlock=ipv6_cidr, VpcId=vpc_id, aws_retry=True)
                        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                            module.fail_json_aws(e, "Unable to associate CIDR {0}.".format(ipv6_cidr))
                        wait_for_vpc_ipv6_state(module, connection, vpc_id, True)
        else:
            # ipv6_cidr is False
            if 'Ipv6CidrBlockAssociationSet' in vpc_obj.keys() and len(vpc_obj['Ipv6CidrBlockAssociationSet']) > 0:
                assoc_disable = False
                for ipv6_assoc in vpc_obj['Ipv6CidrBlockAssociationSet']:
                    if ipv6_assoc['Ipv6Pool'] == 'Amazon' and ipv6_assoc['Ipv6CidrBlockState']['State'] in ['associated', 'associating']:
                        assoc_disable = True
                        changed = True
                        if not module.check_mode:
                            try:
                                connection.disassociate_vpc_cidr_block(AssociationId=ipv6_assoc['AssociationId'], aws_retry=True)
                            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                                module.fail_json_aws(e, "Unable to disassociate IPv6 CIDR {0}.".format(ipv6_assoc['AssociationId']))
                if assoc_disable and not module.check_mode:
                    wait_for_vpc_ipv6_state(module, connection, vpc_id, False)
        if purge_cidrs:
            for association_id in to_remove:
                changed = True
                if not module.check_mode:
                    try:
                        connection.disassociate_vpc_cidr_block(AssociationId=association_id, aws_retry=True)
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, "Unable to disassociate {0}. You must detach or delete all gateways and resources that "
                                             "are associated with the CIDR block before you can disassociate it.".format(association_id))

        if dhcp_id is not None:
            try:
                if update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
                    changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, "Failed to update DHCP options")

        if tags is not None or name is not None:
            try:
                if update_vpc_tags(connection, module, vpc_id, tags, name):
                    changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to update tags")

        current_dns_enabled = connection.describe_vpc_attribute(Attribute='enableDnsSupport', VpcId=vpc_id, aws_retry=True)['EnableDnsSupport']['Value']
        current_dns_hostnames = connection.describe_vpc_attribute(Attribute='enableDnsHostnames', VpcId=vpc_id, aws_retry=True)['EnableDnsHostnames']['Value']
        if current_dns_enabled != dns_support:
            changed = True
            if not module.check_mode:
                try:
                    connection.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': dns_support}, aws_retry=True)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, "Failed to update enabled dns support attribute")

        if current_dns_hostnames != dns_hostnames:
            changed = True
            if not module.check_mode:
                try:
                    connection.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': dns_hostnames}, aws_retry=True)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, "Failed to update enabled dns hostnames attribute")

        # wait for associated cidrs to match
        if to_add or to_remove:
            wait_for_vpc(
                module, connection,
                VpcIds=[vpc_id],
                Filters=[{'Name': 'cidr-block-association.cidr-block', 'Values': expected_cidrs}]
            )

        # try to wait for enableDnsSupport and enableDnsHostnames to match
        wait_for_vpc_attribute(connection, module, vpc_id, 'enableDnsSupport', dns_support)
        wait_for_vpc_attribute(connection, module, vpc_id, 'enableDnsHostnames', dns_hostnames)

        final_state = camel_dict_to_snake_dict(get_vpc(module, connection, vpc_id))
        final_state['tags'] = boto3_tag_list_to_ansible_dict(final_state.get('tags', []))
        final_state['id'] = final_state.pop('vpc_id')
        debugging = dict(to_add=to_add, to_remove=to_remove, expected_cidrs=expected_cidrs)

        module.exit_json(changed=changed, vpc=final_state, debugging=debugging)

    elif state == 'absent':

        # Check if VPC exists
        vpc_id = vpc_exists(module, connection, name, cidr_block, multi)

        if vpc_id is not None:
            try:
                if not module.check_mode:
                    connection.delete_vpc(VpcId=vpc_id, aws_retry=True)
                changed = True

            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to delete VPC {0} You may want to use the ec2_vpc_subnet, ec2_vpc_igw, "
                                     "and/or ec2_vpc_route_table modules to ensure the other components are absent.".format(vpc_id))

        module.exit_json(changed=changed, vpc={})


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_igw
version_added: 1.0.0
short_description: Manage an AWS VPC Internet gateway
description:
    - Manage an AWS VPC Internet gateway
author: Robert Estelle (@erydo)
options:
  vpc_id:
    description:
      - The VPC ID for the VPC in which to manage the Internet Gateway.
    required: true
    type: str
  state:
    description:
      - Create or terminate the IGW
    default: present
    choices: [ 'present', 'absent' ]
    type: str
notes:
- Support for I(purge_tags) was added in release 1.3.0.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.tags
- amazon.aws.boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Ensure that the VPC has an Internet Gateway.
# The Internet Gateway ID is can be accessed via {{igw.gateway_id}} for use in setting up NATs etc.
- name: Create Internet gateway
  amazon.aws.ec2_vpc_igw:
    vpc_id: vpc-abcdefgh
    state: present
  register: igw

- name: Create Internet gateway with tags
  amazon.aws.ec2_vpc_igw:
    vpc_id: vpc-abcdefgh
    state: present
    tags:
        Tag1: tag1
        Tag2: tag2
  register: igw

- name: Delete Internet gateway
  amazon.aws.ec2_vpc_igw:
    state: absent
    vpc_id: vpc-abcdefgh
  register: vpc_igw_delete
'''

RETURN = '''
changed:
  description: If any changes have been made to the Internet Gateway.
  type: bool
  returned: always
  sample:
    changed: false
gateway_id:
  description: The unique identifier for the Internet Gateway.
  type: str
  returned: I(state=present)
  sample:
    gateway_id: "igw-XXXXXXXX"
tags:
  description: The tags associated the Internet Gateway.
  type: dict
  returned: I(state=present)
  sample:
    tags:
      "Ansible": "Test"
vpc_id:
  description: The VPC ID associated with the Internet Gateway.
  type: str
  returned: I(state=present)
  sample:
    vpc_id: "vpc-XXXXXXXX"
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


@AWSRetry.jittered_backoff(retries=10, delay=10)
def describe_igws_with_backoff(connection, **params):
    paginator = connection.get_paginator('describe_internet_gateways')
    return paginator.paginate(**params).build_full_result()['InternetGateways']


class AnsibleEc2Igw():

    def __init__(self, module, results):
        self._module = module
        self._results = results
        self._connection = self._module.client(
            'ec2', retry_decorator=AWSRetry.jittered_backoff()
        )
        self._check_mode = self._module.check_mode

    def process(self):
        vpc_id = self._module.params.get('vpc_id')
        state = self._module.params.get('state', 'present')
        tags = self._module.params.get('tags')
        purge_tags = self._module.params.get('purge_tags')

        if state == 'present':
            self.ensure_igw_present(vpc_id, tags, purge_tags)
        elif state == 'absent':
            self.ensure_igw_absent(vpc_id)

    def get_matching_igw(self, vpc_id, gateway_id=None):
        '''
        Returns the internet gateway found.
            Parameters:
                vpc_id (str): VPC ID
                gateway_id (str): Internet Gateway ID, if specified
            Returns:
                igw (dict): dict of igw found, None if none found
        '''
        filters = ansible_dict_to_boto3_filter_list({'attachment.vpc-id': vpc_id})
        try:
            # If we know the gateway_id, use it to avoid bugs with using filters
            # See https://github.com/ansible-collections/amazon.aws/pull/766
            if not gateway_id:
                igws = describe_igws_with_backoff(self._connection, Filters=filters)
            else:
                igws = describe_igws_with_backoff(self._connection, InternetGatewayIds=[gateway_id])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e)

        igw = None
        if len(igws) > 1:
            self._module.fail_json(
                msg='EC2 returned more than one Internet Gateway for VPC {0}, aborting'
                    .format(vpc_id))
        elif igws:
            igw = camel_dict_to_snake_dict(igws[0])

        return igw

    @staticmethod
    def get_igw_info(igw, vpc_id):
        return {
            'gateway_id': igw['internet_gateway_id'],
            'tags': boto3_tag_list_to_ansible_dict(igw['tags']),
            'vpc_id': vpc_id
        }

    def ensure_igw_absent(self, vpc_id):
        igw = self.get_matching_igw(vpc_id)
        if igw is None:
            return self._results

        if self._check_mode:
            self._results['changed'] = True
            return self._results

        try:
            self._results['changed'] = True
            self._connection.detach_internet_gateway(
                aws_retry=True,
                InternetGatewayId=igw['internet_gateway_id'],
                VpcId=vpc_id
            )
            self._connection.delete_internet_gateway(
                aws_retry=True,
                InternetGatewayId=igw['internet_gateway_id']
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="Unable to delete Internet Gateway")

        return self._results

    def ensure_igw_present(self, vpc_id, tags, purge_tags):
        igw = self.get_matching_igw(vpc_id)

        if igw is None:
            if self._check_mode:
                self._results['changed'] = True
                self._results['gateway_id'] = None
                return self._results

            try:
                response = self._connection.create_internet_gateway(aws_retry=True)

                # Ensure the gateway exists before trying to attach it or add tags
                waiter = get_waiter(self._connection, 'internet_gateway_exists')
                waiter.wait(InternetGatewayIds=[response['InternetGateway']['InternetGatewayId']])

                igw = camel_dict_to_snake_dict(response['InternetGateway'])
                self._connection.attach_internet_gateway(
                    aws_retry=True,
                    InternetGatewayId=igw['internet_gateway_id'],
                    VpcId=vpc_id
                )

                # Ensure the gateway is attached before proceeding
                waiter = get_waiter(self._connection, 'internet_gateway_attached')
                waiter.wait(InternetGatewayIds=[igw['internet_gateway_id']])
                self._results['changed'] = True
            except botocore.exceptions.WaiterError as e:
                self._module.fail_json_aws(e, msg="No Internet Gateway exists.")
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg='Unable to create Internet Gateway')

        # Modify tags
        self._results['changed'] |= ensure_ec2_tags(
            self._connection, self._module, igw['internet_gateway_id'],
            resource_type='internet-gateway', tags=tags, purge_tags=purge_tags,
            retry_codes='InvalidInternetGatewayID.NotFound'
        )

        # Update igw
        igw = self.get_matching_igw(vpc_id, gateway_id=igw['internet_gateway_id'])
        igw_info = self.get_igw_info(igw, vpc_id)
        self._results.update(igw_info)

        return self._results


def main():
    argument_spec = dict(
        vpc_id=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(required=False, type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    results = dict(
        changed=False
    )
    igw_manager = AnsibleEc2Igw(module=module, results=results)
    igw_manager.process()

    module.exit_json(**results)


if __name__ == '__main__':
    main()

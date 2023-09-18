#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_s3_bucket_info
short_description: Lists S3 buckets in AWS
requirements:
  - boto3 >= 1.4.4
  - python >= 2.6
description:
    - Lists S3 buckets in AWS
    - This module was called C(aws_s3_bucket_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(aws_s3_bucket_info) module no longer returns C(ansible_facts)!
author: "Gerben Geijteman (@hyperized)"
extends_documentation_fragment:
- ansible.amazon.aws
- ansible.amazon.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Note: Only AWS S3 is currently supported

# Lists all s3 buckets
- aws_s3_bucket_info:
  register: result

- name: List buckets
  debug:
    msg: "{{ result['buckets'] }}"
'''

RETURN = '''
buckets:
  description: "List of buckets"
  returned: always
  sample:
    - creation_date: 2017-07-06 15:05:12 +00:00
      name: my_bucket
  type: list
'''

import traceback

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.ansible.amazon.plugins.module_utils.ec2 import (boto3_conn, ec2_argument_spec, HAS_BOTO3, camel_dict_to_snake_dict,
                                      get_aws_connection_info)


def get_bucket_list(module, connection):
    """
    Return result of list_buckets json encoded
    :param module:
    :param connection:
    :return:
    """
    try:
        buckets = camel_dict_to_snake_dict(connection.list_buckets())['buckets']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    return buckets


def main():
    """
    Get list of S3 buckets
    :return:
    """

    # Ensure we have an empty dict
    result = {}

    # Including ec2 argument spec
    module = AnsibleModule(argument_spec=ec2_argument_spec(), supports_check_mode=True)
    is_old_facts = module._name == 'aws_s3_bucket_facts'
    if is_old_facts:
        module.deprecate("The 'aws_s3_bucket_facts' module has been renamed to 'aws_s3_bucket_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    # Verify Boto3 is used
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    # Set up connection
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=HAS_BOTO3)
    connection = boto3_conn(module, conn_type='client', resource='s3', region=region, endpoint=ec2_url,
                            **aws_connect_params)

    # Gather results
    result['buckets'] = get_bucket_list(module, connection)

    # Send exit
    if is_old_facts:
        module.exit_json(msg="Retrieved s3 facts.", ansible_facts=result)
    else:
        module.exit_json(msg="Retrieved s3 info.", **result)


if __name__ == '__main__':
    main()

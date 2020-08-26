#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: aws_s3_bucket_info
version_added: 1.0.0
short_description: Lists S3 buckets in AWS
requirements:
  - boto3 >= 1.4.4
  - python >= 2.6
description:
    - Lists S3 buckets in AWS
    - This module was called C(aws_s3_bucket_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(community.aws.aws_s3_bucket_info) module no longer returns C(ansible_facts)!
author: "Gerben Geijteman (@hyperized)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Note: Only AWS S3 is currently supported

# Lists all s3 buckets
- community.aws.aws_s3_bucket_info:
  register: result

- name: List buckets
  ansible.builtin.debug:
    msg: "{{ result['buckets'] }}"
'''

RETURN = '''
buckets:
  description: "List of buckets"
  returned: always
  sample:
    - creation_date: '2017-07-06 15:05:12 +00:00'
      name: my_bucket
  type: list
'''

import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


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
    module = AnsibleAWSModule(argument_spec={}, supports_check_mode=True)
    is_old_facts = module._name == 'aws_s3_bucket_facts'
    if is_old_facts:
        module.deprecate("The 'aws_s3_bucket_facts' module has been renamed to 'aws_s3_bucket_info', "
                         "and the renamed one no longer returns ansible_facts", date='2021-12-01', collection_name='community.aws')

    # Set up connection
    try:
        connection = module.client('s3')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    # Gather results
    result['buckets'] = get_bucket_list(module, connection)

    # Send exit
    if is_old_facts:
        module.exit_json(msg="Retrieved s3 facts.", ansible_facts=result)
    else:
        module.exit_json(msg="Retrieved s3 info.", **result)


if __name__ == '__main__':
    main()

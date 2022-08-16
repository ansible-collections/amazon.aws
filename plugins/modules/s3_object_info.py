#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: s3_object_info
version_added: 5.0.0
short_description: Gather information about objects in s3
description:
  - Describes the objects in s3.
author:
  - Mandar Vijay Kulkarni (@mandar242)
options:
  name:
    description:
      - Name of the S3 bucket containing the object.extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.s3_object
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
pass'''

RETURN = '''
pass
'''
try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list

def _describe_s3_object_acl(connection, **params):
    describe_s3_object_acl_response = connection.get_object(**params)
    return describe_s3_object_acl_response

def describe_s3_object_acl(connection, module):
    params = {}
    if module.params.get('bucket_name'):
        params['Bucket'] = module.params.get('bucket_name')
    if module.params.get('object_key'):
        params['Key'] = module.params.get('object_key')

    try:
        object_info = _describe_s3_object_acl(connection, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe s3 object')

    if len(object_info) == 0:
        module.exit_json(msg='Failed to find S3 object found for specified options')
    module.exit_json(object_info=object_info)

def main():

    argument_spec = dict(
        bucket_name=dict(required=True),
        object_key=dict(required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        connection = module.client('s3', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    describe_s3_object_acl(connection, module)

if __name__ == '__main__':
    main()
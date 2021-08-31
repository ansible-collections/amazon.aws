#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

DOCUMENTATION = '''
---
'''

EXAMPLES = '''
'''

RETURN = '''
'''
import time
import datetime

try:
    import botocore
except ImportError:
    pass # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code

def describe_spot_instance_requests(connection, module):

    params = {}

    if module.params.get('filters'):
        params['Filters'] = module.params.get('filters')
    if module.params.get('dry_run'):
        params['DryRun'] = module.params.get('dry_run')
    if module.params.get('spot_instance_request_ids'):
        params['SpotInstanceRequestIds'] = module.params.get('spot_instance_request_ids')
    if module.params.get('next_token'):
        params['NextToken'] = module.params.get('next_token')
    if module.params.get('max_results'):
        params['MaxResults'] = module.params.get('max_results')

    pass

def main():

    argument_spec=dict(
        filters=dict(default=[], type='list', elements='dict'),
        dry_run = dict(default=False, type='bool', choices=[True, False]),
        spot_instance_request_ids=dict(default=[], type='list', elements='str'),
        next_token = dict(default=None, type='str'),
        max_results = dict(type='int')
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    try:
        connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    describe_spot_instance_requests(connection, module)

if __name__ == '__main__':
    main()

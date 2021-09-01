#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

DOCUMENTATION = '''
---
module: ec2_spot_instance_info
version_added: 2.0.0
short_description: Gather information about ec2 spot instance requests
description:
	- Describes the specified Spot Instance requests.
options:
	filters:
		description:
			- A list of filters to apply.
			- Each list item is a dict consisting of a filter key and a filter value.
			- See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSpotInstanceRequests.html) for possible filters.
		type: list
	dry_run:
		description:
			- A boolean to check if you have the required permissions for the action.
			- Does not make the request.
			- If required permissions are not present then returns an error response UnauthorizedOperation else DryRunOperation.
		type: bool
	spot_instance_request_ids:
		description:
			- One or more Spot Instance request IDs.
		type: str
	next_token:
		description:
			- A token to request the next set of results.
			- Value is null when no more results to return
		type: str
	max_results:
		description:
			- Maximum number of results to be returned in a single call.
			- Value can be between 5 and 1000.
		type: int

'''

EXAMPLES = '''
'''

RETURN = '''
'''

import q
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

    changed = True

    if module.check_mode:
        module.exit_json(changed=changed)

    params = {}

    if module.params.get('filters'):
        filters_dit = module.params.get('filters')
        camel_filters = snake_dict_to_camel_dict(filters_dit, capitalize_first=True)
        params['Filters'] = camel_filters
    if module.params.get('dry_run'):
        params['DryRun'] = module.params.get('dry_run')
    if module.params.get('spot_instance_request_ids'):
        params['SpotInstanceRequestIds'] = module.params.get('spot_instance_request_ids')
    if module.params.get('next_token'):
        params['NextToken'] = module.params.get('next_token')
    if module.params.get('max_results'):
        params['MaxResults'] = module.params.get('max_results')

    try:
        describe_spot_instance_requests_response = (connection.describe_spot_instance_requests(**params))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe sport instance requests')

    describe_spot_instance_requests_response['Tags'] = boto3_tag_list_to_ansible_dict(describe_spot_instance_requests_response.get('Tags', []))
    describe_spot_requests = camel_dict_to_snake_dict(describe_spot_instance_requests_response, ignore_list=['Tags'])
    module.exit_json(describe_spot_requests=describe_spot_requests, changed=changed)

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

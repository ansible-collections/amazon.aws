#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type


DOCUMENTATION = '''
---
module: autoscaling_instance_refresh_info
version_added: 3.2.0
short_description: Gather information about EC2 Auto Scaling Group (ASG) Instance Refreshes in AWS
description:
  - Describes one or more instance refreshes.
  - You can determine the status of a request by looking at the I(status) parameter.
  - Prior to release 5.0.0 this module was called C(community.aws.ec2_asg_instance_refresh_info).
    The usage did not change.
author: "Dan Khersonsky (@danquixote)"
options:
  name:
    description:
      - The name of the Auto Scaling group.
    type: str
    required: true
  ids:
    description:
      - One or more instance refresh IDs.
    type: list
    elements: str
    default: []
  next_token:
    description:
      - The token for the next set of items to return. (You received this token from a previous call.)
    type: str
  max_records:
    description:
      - The maximum number of items to return with this call. The default value is 50 and the maximum value is 100.
    type: int
    required: false
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Find an refresh by ASG name
  community.aws.autoscaling_instance_refresh_info:
    name: somename-asg

- name: Find an refresh by ASG name and one or more refresh-IDs
  community.aws.autoscaling_instance_refresh_info:
    name: somename-asg
    ids: ['some-id-123']
  register: asgs

- name: Find an refresh by ASG name and set max_records
  community.aws.autoscaling_instance_refresh_info:
    name: somename-asg
    max_records: 4
  register: asgs

- name: Find an refresh by ASG name and NextToken, if received from a previous call
  community.aws.autoscaling_instance_refresh_info:
    name: somename-asg
    next_token: 'some-token-123'
  register: asgs
'''

RETURN = '''
---
instance_refresh_id:
    description: instance refresh id
    returned: success
    type: str
    sample: "08b91cf7-8fa6-48af-b6a6-d227f40f1b9b"
auto_scaling_group_name:
    description: Name of autoscaling group
    returned: success
    type: str
    sample: "public-webapp-production-1"
status:
    description:
      - The current state of the group when DeleteAutoScalingGroup is in progress.
      - The following are the possible statuses
      - C(Pending) - The request was created, but the operation has not started.
      - C(InProgress) - The operation is in progress.
      - C(Successful) - The operation completed successfully.
      - C(Failed) - The operation failed to complete.
        You can troubleshoot using the status reason and the scaling activities.
      - C(Cancelling) - An ongoing operation is being cancelled.
        Cancellation does not roll back any replacements that have already been
        completed, but it prevents new replacements from being started.
      - C(Cancelled) - The operation is cancelled.'
    returned: success
    type: str
    sample: "Pending"
start_time:
    description: The date and time this ASG was created, in ISO 8601 format.
    returned: success
    type: str
    sample: "2015-11-25T00:05:36.309Z"
end_time:
    description: The date and time this ASG was created, in ISO 8601 format.
    returned: success
    type: str
    sample: "2015-11-25T00:05:36.309Z"
percentage_complete:
    description: the % of completeness
    returned: success
    type: int
    sample: 100
instances_to_update:
    description: num. of instance to update
    returned: success
    type: int
    sample: 5
'''

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def find_asg_instance_refreshes(conn, module):
    """
    Args:
        conn (boto3.AutoScaling.Client): Valid Boto3 ASG client.
        module: AnsibleAWSModule object

    Returns:
        {
            "instance_refreshes": [
                    {
                        'auto_scaling_group_name': 'ansible-test-hermes-63642726-asg',
                        'instance_refresh_id': '6507a3e5-4950-4503-8978-e9f2636efc09',
                        'instances_to_update': 1,
                        'percentage_complete': 0,
                        "preferences": {
                            "instance_warmup": 60,
                            "min_healthy_percentage": 90,
                            "skip_matching": false
                        },
                        'start_time': '2021-02-04T03:39:40+00:00',
                        'status': 'Cancelled',
                        'status_reason': 'Cancelled due to user request.',
                    }
            ],
            'next_token': 'string'
        }
        """

    asg_name = module.params.get('name')
    asg_ids = module.params.get('ids')
    asg_next_token = module.params.get('next_token')
    asg_max_records = module.params.get('max_records')

    args = {}
    args['AutoScalingGroupName'] = asg_name
    if asg_ids:
        args['InstanceRefreshIds'] = asg_ids
    if asg_next_token:
        args['NextToken'] = asg_next_token
    if asg_max_records:
        args['MaxRecords'] = asg_max_records

    try:
        instance_refreshes_result = {}
        response = conn.describe_instance_refreshes(**args)
        if 'InstanceRefreshes' in response:
            instance_refreshes_dict = dict(
                instance_refreshes=response['InstanceRefreshes'], next_token=response.get('next_token', ''))
            instance_refreshes_result = camel_dict_to_snake_dict(
                instance_refreshes_dict)

        while 'NextToken' in response:
            args['NextToken'] = response['NextToken']
            response = conn.describe_instance_refreshes(**args)
            if 'InstanceRefreshes' in response:
                instance_refreshes_dict = camel_dict_to_snake_dict(dict(
                    instance_refreshes=response['InstanceRefreshes'], next_token=response.get('next_token', '')))
                instance_refreshes_result.update(instance_refreshes_dict)

        return module.exit_json(**instance_refreshes_result)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to describe InstanceRefreshes')


def main():

    argument_spec = dict(
        name=dict(required=True, type='str'),
        ids=dict(required=False, default=[], elements='str', type='list'),
        next_token=dict(required=False, default=None, type='str', no_log=True),
        max_records=dict(required=False, type='int'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    autoscaling = module.client(
        'autoscaling',
        retry_decorator=AWSRetry.jittered_backoff(retries=10)
    )
    find_asg_instance_refreshes(autoscaling, module)


if __name__ == '__main__':
    main()

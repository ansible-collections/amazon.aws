#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_placement_group
version_added: 1.0.0
short_description: Create or delete an EC2 Placement Group
description:
    - Create an EC2 Placement Group; if the placement group already exists,
      nothing is done. Or, delete an existing placement group. If the placement
      group is absent, do nothing. See also
      U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/placement-groups.html)
author: "Brad Macpherson (@iiibrad)"
options:
  name:
    description:
      - The name for the placement group.
    required: true
    type: str
  partition_count:
    description:
      - The number of partitions.
      - Valid only when I(Strategy) is set to C(partition).
      - Must be a value between C(1) and C(7).
    type: int
    version_added: 3.1.0
  state:
    description:
      - Create or delete placement group.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  strategy:
    description:
      - Placement group strategy. Cluster will cluster instances into a
        low-latency group in a single Availability Zone, while Spread spreads
        instances across underlying hardware.
    default: cluster
    choices: [ 'cluster', 'spread', 'partition' ]
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide
# for details.

- name: Create a placement group.
  community.aws.ec2_placement_group:
    name: my-cluster
    state: present

- name: Create a Spread placement group.
  community.aws.ec2_placement_group:
    name: my-cluster
    state: present
    strategy: spread

- name: Create a Partition strategy placement group.
  community.aws.ec2_placement_group:
    name: my-cluster
    state: present
    strategy: partition
    partition_count: 3

- name: Delete a placement group.
  community.aws.ec2_placement_group:
    name: my-cluster
    state: absent

'''


RETURN = '''
placement_group:
  description: Placement group attributes
  returned: when state != absent
  type: complex
  contains:
    name:
      description: PG name
      type: str
      sample: my-cluster
    state:
      description: PG state
      type: str
      sample: "available"
    strategy:
      description: PG strategy
      type: str
      sample: "cluster"

'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


@AWSRetry.exponential_backoff()
def search_placement_group(connection, module):
    """
    Check if a placement group exists.
    """
    name = module.params.get("name")
    try:
        response = connection.describe_placement_groups(
            Filters=[{
                "Name": "group-name",
                "Values": [name]
            }])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't find placement group named [%s]" % name)

    if len(response['PlacementGroups']) != 1:
        return None
    else:
        placement_group = response['PlacementGroups'][0]
        return {
            "name": placement_group['GroupName'],
            "state": placement_group['State'],
            "strategy": placement_group['Strategy'],
        }


@AWSRetry.exponential_backoff(catch_extra_error_codes=['InvalidPlacementGroup.Unknown'])
def get_placement_group_information(connection, name):
    """
    Retrieve information about a placement group.
    """
    response = connection.describe_placement_groups(
        GroupNames=[name]
    )
    placement_group = response['PlacementGroups'][0]
    return {
        "name": placement_group['GroupName'],
        "state": placement_group['State'],
        "strategy": placement_group['Strategy'],
    }


@AWSRetry.exponential_backoff()
def create_placement_group(connection, module):
    name = module.params.get("name")
    strategy = module.params.get("strategy")
    partition_count = module.params.get("partition_count")

    if strategy != 'partition' and partition_count:
        module.fail_json(
            msg="'partition_count' can only be set when strategy is set to 'partition'.")

    params = {}
    params['GroupName'] = name
    params['Strategy'] = strategy
    if partition_count:
        params['PartitionCount'] = partition_count
    params['DryRun'] = module.check_mode

    try:
        connection.create_placement_group(**params)
    except is_boto3_error_code('DryRunOperation'):
        module.exit_json(changed=True, placement_group={
            "name": name,
            "state": 'DryRun',
            "strategy": strategy,
        })
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(
            e,
            msg="Couldn't create placement group [%s]" % name)

    module.exit_json(changed=True,
                     placement_group=get_placement_group_information(connection, name))


@AWSRetry.exponential_backoff()
def delete_placement_group(connection, module):
    name = module.params.get("name")

    try:
        connection.delete_placement_group(
            GroupName=name, DryRun=module.check_mode)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't delete placement group [%s]" % name)

    module.exit_json(changed=True)


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        partition_count=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent']),
        strategy=dict(default='cluster', choices=['cluster', 'spread', 'partition'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    connection = module.client('ec2')

    state = module.params.get("state")

    if state == 'present':
        placement_group = search_placement_group(connection, module)
        if placement_group is None:
            create_placement_group(connection, module)
        else:
            strategy = module.params.get("strategy")
            if placement_group['strategy'] == strategy:
                module.exit_json(
                    changed=False, placement_group=placement_group)
            else:
                name = module.params.get("name")
                module.fail_json(
                    msg=("Placement group '{}' exists, can't change strategy" +
                         " from '{}' to '{}'").format(
                             name,
                             placement_group['strategy'],
                             strategy))

    elif state == 'absent':
        placement_group = search_placement_group(connection, module)
        if placement_group is None:
            module.exit_json(changed=False)
        else:
            delete_placement_group(connection, module)


if __name__ == '__main__':
    main()

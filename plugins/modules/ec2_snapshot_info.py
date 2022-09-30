#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_snapshot_info
version_added: 1.0.0
short_description: Gathers information about EC2 volume snapshots in AWS
description:
  - Gathers information about EC2 volume snapshots in AWS.
author:
  - Rob White (@wimnat)
  - Aubin Bikouo (@abikouo)
options:
  snapshot_ids:
    description:
      - If you specify one or more snapshot IDs, only snapshots that have the specified IDs are returned.
    required: false
    default: []
    type: list
    elements: str
  owner_ids:
    description:
      - If you specify one or more snapshot owners, only snapshots from the specified owners and for which you have
        access are returned.
    required: false
    default: []
    type: list
    elements: str
  restorable_by_user_ids:
    description:
      - If you specify a list of restorable users, only snapshots with create snapshot permissions for those users are
        returned.
    required: false
    default: []
    type: list
    elements: str
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    type: dict
    default: {}
  max_results:
    description:
    - The maximum number of snapshot results returned in paginated output.
    - When used only a single page along with a C(next_token_id) response element will be returned.
    - The remaining results of the initial request can be seen by sending another request with the returned C(next_token_id) value.
    - This value can be between 5 and 1000; if I(next_token_id) is given a value larger than 1000, only 1000 results are returned.
    - If this parameter is not used, then DescribeSnapshots returns all results.
    - This parameter is mutually exclusive with I(snapshot_ids).
    required: False
    type: int
  next_token_id:
    description:
    - Contains the value returned from a previous paginated request where I(max_results) was used and the results exceeded the value of that parameter.
    - Pagination continues from the end of the previous results that returned the I(next_token_id) value.
    - This parameter is mutually exclusive with I(snapshot_ids)
    required: false
    type: str
notes:
  - By default, the module will return all snapshots, including public ones. To limit results to snapshots owned by
    the account use the filter 'owner-id'.

extends_documentation_fragment:
  - amazon.aws.ec2
  - amazon.aws.aws
  - amazon.aws.boto3
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all snapshots, including public ones
- amazon.aws.ec2_snapshot_info:

# Gather information about all snapshots owned by the account 123456789012
- amazon.aws.ec2_snapshot_info:
    filters:
      owner-id: 123456789012

# Or alternatively...
- amazon.aws.ec2_snapshot_info:
    owner_ids:
      - 123456789012

# Gather information about a particular snapshot using ID
- amazon.aws.ec2_snapshot_info:
    filters:
      snapshot-id: snap-00112233

# Or alternatively...
- amazon.aws.ec2_snapshot_info:
    snapshot_ids:
      - snap-00112233

# Gather information about any snapshot with a tag key Name and value Example
- amazon.aws.ec2_snapshot_info:
    filters:
      "tag:Name": Example

# Gather information about any snapshot with an error status
- amazon.aws.ec2_snapshot_info:
    filters:
      status: error

'''

RETURN = r'''
snapshots:
    description: List of snapshots retrieved with their respective info.
    type: list
    returned: success
    elements: dict
    contains:
        snapshot_id:
            description: The ID of the snapshot. Each snapshot receives a unique identifier when it is created.
            type: str
            returned: always
            sample: snap-01234567
        volume_id:
            description: The ID of the volume that was used to create the snapshot.
            type: str
            returned: always
            sample: vol-01234567
        state:
            description: The snapshot state (completed, pending or error).
            type: str
            returned: always
            sample: completed
        state_message:
            description:
              - Encrypted Amazon EBS snapshots are copied asynchronously. If a snapshot copy operation fails (for example, if the proper
                AWS Key Management Service (AWS KMS) permissions are not obtained) this field displays error state details to help you diagnose why the
                error occurred.
            type: str
            returned: always
            sample:
        start_time:
            description: The time stamp when the snapshot was initiated.
            type: str
            returned: always
            sample: "2015-02-12T02:14:02+00:00"
        progress:
            description: The progress of the snapshot, as a percentage.
            type: str
            returned: always
            sample: "100%"
        owner_id:
            description: The AWS account ID of the EBS snapshot owner.
            type: str
            returned: always
            sample: "123456789012"
        description:
            description: The description for the snapshot.
            type: str
            returned: always
            sample: "My important backup"
        volume_size:
            description: The size of the volume, in GiB.
            type: int
            returned: always
            sample: 8
        owner_alias:
            description: The AWS account alias (for example, amazon, self) or AWS account ID that owns the snapshot.
            type: str
            returned: always
            sample: "123456789012"
        tags:
            description: Any tags assigned to the snapshot.
            type: dict
            returned: always
            sample: "{ 'my_tag_key': 'my_tag_value' }"
        encrypted:
            description: Indicates whether the snapshot is encrypted.
            type: bool
            returned: always
            sample: "True"
        kms_key_id:
            description:
              - The full ARN of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to
                protect the volume encryption key for the parent volume.
            type: str
            returned: always
            sample: "74c9742a-a1b2-45cb-b3fe-abcdef123456"
        data_encryption_key_id:
            description:
              - The data encryption key identifier for the snapshot. This value is a unique identifier that
                corresponds to the data encryption key that was used to encrypt the original volume or snapshot copy.
            type: str
            returned: always
            sample: "arn:aws:kms:ap-southeast-2:123456789012:key/74c9742a-a1b2-45cb-b3fe-abcdef123456"
next_token_id:
    description:
    - Contains the value returned from a previous paginated request where C(max_results) was used and the results exceeded the value of that parameter.
    - This value is null when there are no more results to return.
    type: str
    returned: when option C(max_results) is set in input
'''

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def list_ec2_snapshots(connection, module):

    snapshot_ids = module.params.get("snapshot_ids")
    owner_ids = [str(owner_id) for owner_id in module.params.get("owner_ids")]
    restorable_by_user_ids = [str(user_id) for user_id in module.params.get("restorable_by_user_ids")]
    filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    max_results = module.params.get('max_results')
    next_token = module.params.get('next_token_id')
    optional_param = {}
    if max_results:
        optional_param['MaxResults'] = max_results
    if next_token:
        optional_param['NextToken'] = next_token

    try:
        snapshots = connection.describe_snapshots(
            aws_retry=True,
            SnapshotIds=snapshot_ids, OwnerIds=owner_ids,
            RestorableByUserIds=restorable_by_user_ids, Filters=filters,
            **optional_param)
    except is_boto3_error_code('InvalidSnapshot.NotFound') as e:
        if len(snapshot_ids) > 1:
            module.warn("Some of your snapshots may exist, but %s" % str(e))
        snapshots = {'Snapshots': []}
    except ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to describe snapshots')

    result = {}
    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_snapshots = []
    for snapshot in snapshots['Snapshots']:
        snaked_snapshots.append(camel_dict_to_snake_dict(snapshot))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for snapshot in snaked_snapshots:
        if 'tags' in snapshot:
            snapshot['tags'] = boto3_tag_list_to_ansible_dict(snapshot['tags'], 'key', 'value')

    result['snapshots'] = snaked_snapshots

    if snapshots.get('NextToken'):
        result.update(camel_dict_to_snake_dict({'NextTokenId': snapshots.get('NextToken')}))

    module.exit_json(**result)


def main():

    argument_spec = dict(
        snapshot_ids=dict(default=[], type='list', elements='str'),
        owner_ids=dict(default=[], type='list', elements='str'),
        restorable_by_user_ids=dict(default=[], type='list', elements='str'),
        filters=dict(default={}, type='dict'),
        max_results=dict(type='int'),
        next_token_id=dict(type='str')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['snapshot_ids', 'owner_ids', 'restorable_by_user_ids', 'filters'],
            ['snapshot_ids', 'max_results'],
            ['snapshot_ids', 'next_token_id']
        ],
        supports_check_mode=True
    )

    connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    list_ec2_snapshots(connection, module)


if __name__ == '__main__':
    main()

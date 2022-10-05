#!/usr/bin/python

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_snapshot_copy
version_added: 1.0.0
short_description: Copies an EC2 snapshot and returns the new Snapshot ID
description:
  - Copies an EC2 Snapshot from a source region to a destination region.
options:
  source_region:
    description:
      - The source region the Snapshot should be copied from.
    required: true
    type: str
  source_snapshot_id:
    description:
      - The ID of the Snapshot in source region that should be copied.
    required: true
    type: str
  description:
    description:
      - An optional human-readable string describing purpose of the new Snapshot.
    type: str
  encrypted:
    description:
      - Whether or not the destination Snapshot should be encrypted.
    type: bool
    default: false
  kms_key_id:
    description:
      - KMS key id used to encrypt snapshot. If not specified, AWS defaults to C(alias/aws/ebs).
    type: str
  wait:
    description:
      - Wait for the copied Snapshot to be in the C(Available) state before returning.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 600
    type: int
  tags:
    description:
      - A dictionary representing the tags to be applied to the newly created resource.
    type: dict
    aliases: ['resource_tags']
author:
  - Deepak Kothandan (@Deepakkothandan) <deepak.kdy@gmail.com>
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = '''
- name: Basic Snapshot Copy
  community.aws.ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx

- name: Copy Snapshot and wait until available
  community.aws.ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    wait: true
    wait_timeout: 1200   # Default timeout is 600
  register: snapshot_id

- name: Tagged Snapshot copy
  community.aws.ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    tags:
        Name: Snapshot-Name

- name: Encrypted Snapshot copy
  community.aws.ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    encrypted: true

- name: Encrypted Snapshot copy with specified key
  community.aws.ec2_snapshot_copy:
    source_region: eu-central-1
    region: eu-west-1
    source_snapshot_id: snap-xxxxxxx
    encrypted: true
    kms_key_id: arn:aws:kms:eu-central-1:XXXXXXXXXXXX:key/746de6ea-50a4-4bcb-8fbc-e3b29f2d367b
'''

RETURN = '''
snapshot_id:
    description: snapshot id of the newly created snapshot
    returned: when snapshot copy is successful
    type: str
    sample: "snap-e9095e8c"
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications


def copy_snapshot(module, ec2):
    """
    Copies an EC2 Snapshot to another region

    module : AnsibleAWSModule object
    ec2: ec2 connection object
    """

    params = {
        'SourceRegion': module.params.get('source_region'),
        'SourceSnapshotId': module.params.get('source_snapshot_id'),
        'Description': module.params.get('description')
    }

    if module.params.get('encrypted'):
        params['Encrypted'] = True

    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')

    if module.params.get('tags'):
        params['TagSpecifications'] = boto3_tag_specifications(module.params.get('tags'))

    try:
        snapshot_id = ec2.copy_snapshot(**params)['SnapshotId']
        if module.params.get('wait'):
            delay = 15
            # Add one to max_attempts as wait() increment
            # its counter before assessing it for time.sleep()
            max_attempts = (module.params.get('wait_timeout') // delay) + 1
            ec2.get_waiter('snapshot_completed').wait(
                SnapshotIds=[snapshot_id],
                WaiterConfig=dict(Delay=delay, MaxAttempts=max_attempts)
            )

    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='An error occurred waiting for the snapshot to become available.')

    module.exit_json(changed=True, snapshot_id=snapshot_id)


def main():
    argument_spec = dict(
        source_region=dict(required=True),
        source_snapshot_id=dict(required=True),
        description=dict(default=''),
        encrypted=dict(type='bool', default=False, required=False),
        kms_key_id=dict(type='str', required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        tags=dict(type='dict', aliases=['resource_tags']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    try:
        client = module.client('ec2')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    copy_snapshot(module, client)


if __name__ == '__main__':
    main()

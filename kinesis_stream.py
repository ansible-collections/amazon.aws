#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: kinesis_stream
version_added: 1.0.0
short_description: Manage a Kinesis Stream.
description:
    - Create or Delete a Kinesis Stream.
    - Update the retention period of a Kinesis Stream.
    - Update Tags on a Kinesis Stream.
    - Enable/disable server side encryption on a Kinesis Stream.
requirements: [ boto3 ]
author: Allen Sanabria (@linuxdynasty)
options:
  name:
    description:
      - The name of the Kinesis Stream you are managing.
    required: true
    type: str
  shards:
    description:
      - The number of shards you want to have with this stream.
      - This is required when I(state=present)
    type: int
  retention_period:
    description:
      - The length of time (in hours) data records are accessible after they are added to
        the stream.
      - The default retention period is 24 hours and can not be less than 24 hours.
      - The maximum retention period is 168 hours.
      - The retention period can be modified during any point in time.
    type: int
  state:
    description:
      - Create or Delete the Kinesis Stream.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  wait:
    description:
      - Wait for operation to complete before returning.
    default: true
    type: bool
  wait_timeout:
    description:
      - How many seconds to wait for an operation to complete before timing out.
    default: 300
    type: int
  tags:
    description:
      - "A dictionary of resource tags of the form: C({ tag1: value1, tag2: value2 })."
    aliases: [ "resource_tags" ]
    type: dict
  encryption_state:
    description:
      - Enable or Disable encryption on the Kinesis Stream.
    choices: [ 'enabled', 'disabled' ]
    type: str
  encryption_type:
    description:
      - The type of encryption.
      - Defaults to C(KMS)
    choices: ['KMS', 'NONE']
    type: str
  key_id:
    description:
      - The GUID or alias for the KMS key.
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic creation example:
- name: Set up Kinesis Stream with 10 shards and wait for the stream to become ACTIVE
  community.aws.kinesis_stream:
    name: test-stream
    shards: 10
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic creation example with tags:
- name: Set up Kinesis Stream with 10 shards, tag the environment, and wait for the stream to become ACTIVE
  community.aws.kinesis_stream:
    name: test-stream
    shards: 10
    tags:
      Env: development
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic creation example with tags and increase the retention period from the default 24 hours to 48 hours:
- name: Set up Kinesis Stream with 10 shards, tag the environment, increase the retention period and wait for the stream to become ACTIVE
  community.aws.kinesis_stream:
    name: test-stream
    retention_period: 48
    shards: 10
    tags:
      Env: development
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic delete example:
- name: Delete Kinesis Stream test-stream and wait for it to finish deleting.
  community.aws.kinesis_stream:
    name: test-stream
    state: absent
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic enable encryption example:
- name: Encrypt Kinesis Stream test-stream.
  community.aws.kinesis_stream:
    name: test-stream
    state: present
    shards: 1
    encryption_state: enabled
    encryption_type: KMS
    key_id: alias/aws/kinesis
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic disable encryption example:
- name: Encrypt Kinesis Stream test-stream.
  community.aws.kinesis_stream:
    name: test-stream
    state: present
    shards: 1
    encryption_state: disabled
    encryption_type: KMS
    key_id: alias/aws/kinesis
    wait: yes
    wait_timeout: 600
  register: test_stream
'''

RETURN = '''
stream_name:
  description: The name of the Kinesis Stream.
  returned: when state == present.
  type: str
  sample: "test-stream"
stream_arn:
  description: The amazon resource identifier
  returned: when state == present.
  type: str
  sample: "arn:aws:kinesis:east-side:123456789:stream/test-stream"
stream_status:
  description: The current state of the Kinesis Stream.
  returned: when state == present.
  type: str
  sample: "ACTIVE"
retention_period_hours:
  description: Number of hours messages will be kept for a Kinesis Stream.
  returned: when state == present.
  type: int
  sample: 24
tags:
  description: Dictionary containing all the tags associated with the Kinesis stream.
  returned: when state == present.
  type: dict
  sample: {
      "Name": "Splunk",
      "Env": "development"
  }
'''

import re
import datetime
import time
from functools import reduce

try:
    import botocore.exceptions
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags


def get_tags(client, stream_name):
    """Retrieve the tags for a Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): Name of the Kinesis stream.

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >> get_tags(client, stream_name)

    Returns:
        Tuple (bool, str, dict)
    """
    err_msg = ''
    success = False
    params = {
        'StreamName': stream_name,
    }
    results = dict()
    try:
        results = (
            client.list_tags_for_stream(**params)['Tags']
        )
        success = True
    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg, boto3_tag_list_to_ansible_dict(results)


def find_stream(client, stream_name):
    """Retrieve a Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): Name of the Kinesis stream.

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'

    Returns:
        Tuple (bool, str, dict)
    """
    err_msg = ''
    success = False
    params = {
        'StreamName': stream_name,
    }
    results = dict()
    has_more_shards = True
    shards = list()
    try:
        while has_more_shards:
            results = (
                client.describe_stream(**params)['StreamDescription']
            )
            shards.extend(results.pop('Shards'))
            has_more_shards = results['HasMoreShards']
            if has_more_shards:
                params['ExclusiveStartShardId'] = shards[-1]['ShardId']
        results['Shards'] = shards
        num_closed_shards = len([s for s in shards if 'EndingSequenceNumber' in s['SequenceNumberRange']])
        results['OpenShardsCount'] = len(shards) - num_closed_shards
        results['ClosedShardsCount'] = num_closed_shards
        results['ShardsCount'] = len(shards)
        success = True
    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg, results


def wait_for_status(client, stream_name, status, wait_timeout=300,
                    check_mode=False):
    """Wait for the status to change for a Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client
        stream_name (str): The name of the kinesis stream.
        status (str): The status to wait for.
            examples. status=available, status=deleted

    Kwargs:
        wait_timeout (int): Number of seconds to wait, until this timeout is reached.
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> wait_for_status(client, stream_name, 'ACTIVE', 300)

    Returns:
        Tuple (bool, str, dict)
    """
    polling_increment_secs = 5
    wait_timeout = time.time() + wait_timeout
    status_achieved = False
    stream = dict()
    err_msg = ""

    while wait_timeout > time.time():
        try:
            find_success, find_msg, stream = (
                find_stream(client, stream_name)
            )
            if check_mode:
                status_achieved = True
                break

            elif status != 'DELETING':
                if find_success and stream:
                    if stream.get('StreamStatus') == status:
                        status_achieved = True
                        break

            else:
                if not find_success:
                    status_achieved = True
                    break

        except botocore.exceptions.ClientError as e:
            err_msg = to_native(e)

        time.sleep(polling_increment_secs)

    if not status_achieved:
        err_msg = "Wait time out reached, while waiting for results"
    else:
        err_msg = "Status {0} achieved successfully".format(status)

    return status_achieved, err_msg, stream


def tags_action(client, stream_name, tags, action='create', check_mode=False):
    """Create or delete multiple tags from a Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        resource_id (str): The Amazon resource id.
        tags (list): List of dictionaries.
            examples.. [{Name: "", Values: [""]}]

    Kwargs:
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> resource_id = 'pcx-123345678'
        >>> tags = {'env': 'development'}
        >>> update_tags(client, resource_id, tags)
        [True, '']

    Returns:
        List (bool, str)
    """
    success = False
    err_msg = ""
    params = {'StreamName': stream_name}
    try:
        if not check_mode:
            if action == 'create':
                params['Tags'] = tags
                client.add_tags_to_stream(**params)
                success = True
            elif action == 'delete':
                params['TagKeys'] = tags
                client.remove_tags_from_stream(**params)
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)
        else:
            if action == 'create':
                success = True
            elif action == 'delete':
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)

    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg


def update_tags(client, stream_name, tags, check_mode=False):
    """Update tags for an amazon resource.
    Args:
        resource_id (str): The Amazon resource id.
        tags (dict): Dictionary of tags you want applied to the Kinesis stream.

    Kwargs:
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> stream_name = 'test-stream'
        >>> tags = {'env': 'development'}
        >>> update_tags(client, stream_name, tags)
        [True, '']

    Return:
        Tuple (bool, str)
    """
    success = False
    changed = False
    err_msg = ''
    tag_success, tag_msg, current_tags = (
        get_tags(client, stream_name)
    )

    tags_to_set, tags_to_delete = compare_aws_tags(
        current_tags, tags,
        purge_tags=True,
    )
    if tags_to_delete:
        delete_success, delete_msg = (
            tags_action(
                client, stream_name, tags_to_delete, action='delete',
                check_mode=check_mode
            )
        )
        if not delete_success:
            return delete_success, changed, delete_msg
        tag_msg = 'Tags removed'

    if tags_to_set:
        create_success, create_msg = (
            tags_action(
                client, stream_name, tags_to_set, action='create',
                check_mode=check_mode
            )
        )
        if create_success:
            changed = True
        return create_success, changed, create_msg

    return success, changed, err_msg


def stream_action(client, stream_name, shard_count=1, action='create',
                  timeout=300, check_mode=False):
    """Create or Delete an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        shard_count (int): Number of shards this stream will use.
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> shard_count = 20
        >>> stream_action(client, stream_name, shard_count, action='create')

    Returns:
        List (bool, str)
    """
    success = False
    err_msg = ''
    params = {
        'StreamName': stream_name
    }
    try:
        if not check_mode:
            if action == 'create':
                params['ShardCount'] = shard_count
                client.create_stream(**params)
                success = True
            elif action == 'delete':
                client.delete_stream(**params)
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)
        else:
            if action == 'create':
                success = True
            elif action == 'delete':
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)

    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg


def stream_encryption_action(client, stream_name, action='start_encryption', encryption_type='', key_id='',
                             timeout=300, check_mode=False):
    """Create, Encrypt or Delete an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        shard_count (int): Number of shards this stream will use.
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        encryption_type (str): NONE or KMS
        key_id (str): The GUID or alias for the KMS key
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> shard_count = 20
        >>> stream_action(client, stream_name, shard_count, action='create', encryption_type='KMS',key_id='alias/aws')

    Returns:
        List (bool, str)
    """
    success = False
    err_msg = ''
    params = {
        'StreamName': stream_name
    }
    try:
        if not check_mode:
            if action == 'start_encryption':
                params['EncryptionType'] = encryption_type
                params['KeyId'] = key_id
                client.start_stream_encryption(**params)
                success = True
            elif action == 'stop_encryption':
                params['EncryptionType'] = encryption_type
                params['KeyId'] = key_id
                client.stop_stream_encryption(**params)
                success = True
            else:
                err_msg = 'Invalid encryption action {0}'.format(action)
        else:
            if action == 'start_encryption':
                success = True
            elif action == 'stop_encryption':
                success = True
            else:
                err_msg = 'Invalid encryption action {0}'.format(action)

    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg


def retention_action(client, stream_name, retention_period=24,
                     action='increase', check_mode=False):
    """Increase or Decrease the retention of messages in the Kinesis stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        retention_period (int): This is how long messages will be kept before
            they are discarded. This can not be less than 24 hours.
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> retention_period = 48
        >>> retention_action(client, stream_name, retention_period, action='increase')

    Returns:
        Tuple (bool, str)
    """
    success = False
    err_msg = ''
    params = {
        'StreamName': stream_name
    }
    try:
        if not check_mode:
            if action == 'increase':
                params['RetentionPeriodHours'] = retention_period
                client.increase_stream_retention_period(**params)
                success = True
                err_msg = (
                    'Retention Period increased successfully to {0}'.format(retention_period)
                )
            elif action == 'decrease':
                params['RetentionPeriodHours'] = retention_period
                client.decrease_stream_retention_period(**params)
                success = True
                err_msg = (
                    'Retention Period decreased successfully to {0}'.format(retention_period)
                )
            else:
                err_msg = 'Invalid action {0}'.format(action)
        else:
            if action == 'increase':
                success = True
            elif action == 'decrease':
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)

    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg


def update_shard_count(client, stream_name, number_of_shards=1, check_mode=False):
    """Increase or Decrease the number of shards in the Kinesis stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        number_of_shards (int): Number of shards this stream will use.
            default=1
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> number_of_shards = 3
        >>> update_shard_count(client, stream_name, number_of_shards)

    Returns:
        Tuple (bool, str)
    """
    success = True
    err_msg = ''
    params = {
        'StreamName': stream_name,
        'ScalingType': 'UNIFORM_SCALING'
    }
    if not check_mode:
        params['TargetShardCount'] = number_of_shards
        try:
            client.update_shard_count(**params)
        except botocore.exceptions.ClientError as e:
            return False, str(e)

    return success, err_msg


def update(client, current_stream, stream_name, number_of_shards=1, retention_period=None,
           tags=None, wait=False, wait_timeout=300, check_mode=False):
    """Update an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        number_of_shards (int): Number of shards this stream will use.
            default=1
        retention_period (int): This is how long messages will be kept before
            they are discarded. This can not be less than 24 hours.
        tags (dict): The tags you want applied.
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> current_stream = {
            'ShardCount': 3,
            'HasMoreShards': True,
            'RetentionPeriodHours': 24,
            'StreamName': 'test-stream',
            'StreamARN': 'arn:aws:kinesis:us-west-2:123456789:stream/test-stream',
            'StreamStatus': "ACTIVE'
        }
        >>> stream_name = 'test-stream'
        >>> retention_period = 48
        >>> number_of_shards = 10
        >>> update(client, current_stream, stream_name,
                   number_of_shards, retention_period )

    Returns:
        Tuple (bool, bool, str)
    """
    success = True
    changed = False
    err_msg = ''
    if retention_period:
        if wait:
            wait_success, wait_msg, current_stream = (
                wait_for_status(
                    client, stream_name, 'ACTIVE', wait_timeout,
                    check_mode=check_mode
                )
            )
            if not wait_success:
                return wait_success, False, wait_msg

        if current_stream.get('StreamStatus') == 'ACTIVE':
            retention_changed = False
            if retention_period > current_stream['RetentionPeriodHours']:
                retention_changed, retention_msg = (
                    retention_action(
                        client, stream_name, retention_period, action='increase',
                        check_mode=check_mode
                    )
                )

            elif retention_period < current_stream['RetentionPeriodHours']:
                retention_changed, retention_msg = (
                    retention_action(
                        client, stream_name, retention_period, action='decrease',
                        check_mode=check_mode
                    )
                )

            elif retention_period == current_stream['RetentionPeriodHours']:
                retention_msg = (
                    'Retention {0} is the same as {1}'
                    .format(
                        retention_period,
                        current_stream['RetentionPeriodHours']
                    )
                )
                success = True

            if retention_changed:
                success = True
                changed = True

            err_msg = retention_msg
            if changed and wait:
                wait_success, wait_msg, current_stream = (
                    wait_for_status(
                        client, stream_name, 'ACTIVE', wait_timeout,
                        check_mode=check_mode
                    )
                )
                if not wait_success:
                    return wait_success, False, wait_msg
            elif changed and not wait:
                stream_found, stream_msg, current_stream = (
                    find_stream(client, stream_name)
                )
                if stream_found:
                    if current_stream['StreamStatus'] != 'ACTIVE':
                        err_msg = (
                            'Retention Period for {0} is in the process of updating'
                            .format(stream_name)
                        )
                        return success, changed, err_msg
        else:
            err_msg = (
                'StreamStatus has to be ACTIVE in order to modify the retention period. Current status is {0}'
                .format(current_stream.get('StreamStatus', 'UNKNOWN'))
            )
            return success, changed, err_msg

    if current_stream['OpenShardsCount'] != number_of_shards:
        success, err_msg = (
            update_shard_count(client, stream_name, number_of_shards, check_mode=check_mode)
        )

        if not success:
            return success, changed, err_msg

        changed = True

        if wait:
            wait_success, wait_msg, current_stream = (
                wait_for_status(
                    client, stream_name, 'ACTIVE', wait_timeout,
                    check_mode=check_mode
                )
            )
            if not wait_success:
                return wait_success, changed, wait_msg
        else:
            stream_found, stream_msg, current_stream = (
                find_stream(client, stream_name)
            )
            if stream_found and current_stream['StreamStatus'] != 'ACTIVE':
                err_msg = (
                    'Number of shards for {0} is in the process of updating'
                    .format(stream_name)
                )
                return success, changed, err_msg

    if tags:
        tag_success, tag_changed, err_msg = (
            update_tags(client, stream_name, tags, check_mode=check_mode)
        )
        changed |= tag_changed
    if wait:
        success, err_msg, status_stream = (
            wait_for_status(
                client, stream_name, 'ACTIVE', wait_timeout,
                check_mode=check_mode
            )
        )
    if success and changed:
        err_msg = 'Kinesis Stream {0} updated successfully.'.format(stream_name)
    elif success and not changed:
        err_msg = 'Kinesis Stream {0} did not change.'.format(stream_name)

    return success, changed, err_msg


def create_stream(client, stream_name, number_of_shards=1, retention_period=None,
                  tags=None, wait=False, wait_timeout=300, check_mode=False):
    """Create an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        number_of_shards (int): Number of shards this stream will use.
            default=1
        retention_period (int): Can not be less than 24 hours
            default=None
        tags (dict): The tags you want applied.
            default=None
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> number_of_shards = 10
        >>> tags = {'env': 'test'}
        >>> create_stream(client, stream_name, number_of_shards, tags=tags)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    results = dict()

    stream_found, stream_msg, current_stream = (
        find_stream(client, stream_name)
    )

    if stream_found and current_stream.get('StreamStatus') == 'DELETING' and wait:
        wait_success, wait_msg, current_stream = (
            wait_for_status(
                client, stream_name, 'ACTIVE', wait_timeout,
                check_mode=check_mode
            )
        )

    if stream_found and current_stream.get('StreamStatus') != 'DELETING':
        success, changed, err_msg = update(
            client, current_stream, stream_name, number_of_shards,
            retention_period, tags, wait, wait_timeout, check_mode=check_mode
        )
    else:
        create_success, create_msg = (
            stream_action(
                client, stream_name, number_of_shards, action='create',
                check_mode=check_mode
            )
        )
        if not create_success:
            changed = True
            err_msg = 'Failed to create Kinesis stream: {0}'.format(create_msg)
            return False, True, err_msg, {}
        else:
            changed = True
            if wait:
                wait_success, wait_msg, results = (
                    wait_for_status(
                        client, stream_name, 'ACTIVE', wait_timeout,
                        check_mode=check_mode
                    )
                )
                err_msg = (
                    'Kinesis Stream {0} is in the process of being created'
                    .format(stream_name)
                )
                if not wait_success:
                    return wait_success, True, wait_msg, results
            else:
                err_msg = (
                    'Kinesis Stream {0} created successfully'
                    .format(stream_name)
                )

            if tags:
                changed, err_msg = (
                    tags_action(
                        client, stream_name, tags, action='create',
                        check_mode=check_mode
                    )
                )
                if changed:
                    success = True
                if not success:
                    return success, changed, err_msg, results

            stream_found, stream_msg, current_stream = (
                find_stream(client, stream_name)
            )
            if retention_period and current_stream.get('StreamStatus') == 'ACTIVE':
                changed, err_msg = (
                    retention_action(
                        client, stream_name, retention_period, action='increase',
                        check_mode=check_mode
                    )
                )
                if changed:
                    success = True
                if not success:
                    return success, changed, err_msg, results
            else:
                err_msg = (
                    'StreamStatus has to be ACTIVE in order to modify the retention period. Current status is {0}'
                    .format(current_stream.get('StreamStatus', 'UNKNOWN'))
                )
                success = create_success
                changed = True

    if success:
        stream_found, stream_msg, results = (
            find_stream(client, stream_name)
        )
        tag_success, tag_msg, current_tags = (
            get_tags(client, stream_name)
        )
        if check_mode:
            current_tags = tags

        if not current_tags:
            current_tags = dict()

        results = camel_dict_to_snake_dict(results)
        results['tags'] = current_tags

    return success, changed, err_msg, results


def delete_stream(client, stream_name, wait=False, wait_timeout=300,
                  check_mode=False):
    """Delete an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> delete_stream(client, stream_name)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    results = dict()
    stream_found, stream_msg, current_stream = (
        find_stream(client, stream_name)
    )
    if stream_found:
        success, err_msg = (
            stream_action(
                client, stream_name, action='delete', check_mode=check_mode
            )
        )
        if success:
            changed = True
            if wait:
                success, err_msg, results = (
                    wait_for_status(
                        client, stream_name, 'DELETING', wait_timeout,
                        check_mode=check_mode
                    )
                )
                err_msg = 'Stream {0} deleted successfully'.format(stream_name)
                if not success:
                    return success, True, err_msg, results
            else:
                err_msg = (
                    'Stream {0} is in the process of being deleted'
                    .format(stream_name)
                )
    else:
        success = True
        changed = False
        err_msg = 'Stream {0} does not exist'.format(stream_name)

    return success, changed, err_msg, results


def start_stream_encryption(client, stream_name, encryption_type='', key_id='',
                            wait=False, wait_timeout=300, check_mode=False):
    """Start encryption on an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        encryption_type (str): KMS or NONE
        key_id (str): KMS key GUID or alias
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> key_id = 'alias/aws'
        >>> encryption_type = 'KMS'
        >>> start_stream_encryption(client, stream_name,encryption_type,key_id)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    params = {
        'StreamName': stream_name
    }

    results = dict()
    stream_found, stream_msg, current_stream = (
        find_stream(client, stream_name)
    )
    if stream_found:
        if (current_stream.get("EncryptionType") == encryption_type and current_stream.get("KeyId") == key_id):
            changed = False
            success = True
            err_msg = 'Kinesis Stream {0} encryption already configured.'.format(stream_name)
        else:
            success, err_msg = (
                stream_encryption_action(
                    client, stream_name, action='start_encryption', encryption_type=encryption_type, key_id=key_id, check_mode=check_mode
                )
            )
            if success:
                changed = True
                if wait:
                    success, err_msg, results = (
                        wait_for_status(
                            client, stream_name, 'ACTIVE', wait_timeout,
                            check_mode=check_mode
                        )
                    )
                    err_msg = 'Kinesis Stream {0} encryption started successfully.'.format(stream_name)
                    if not success:
                        return success, True, err_msg, results
                else:
                    err_msg = (
                        'Kinesis Stream {0} is in the process of starting encryption.'.format(stream_name)
                    )
    else:
        success = True
        changed = False
        err_msg = 'Kinesis Stream {0} does not exist'.format(stream_name)

    if success:
        stream_found, stream_msg, results = (
            find_stream(client, stream_name)
        )
        tag_success, tag_msg, current_tags = (
            get_tags(client, stream_name)
        )
        if not current_tags:
            current_tags = dict()

        results = camel_dict_to_snake_dict(results)
        results['tags'] = current_tags

    return success, changed, err_msg, results


def stop_stream_encryption(client, stream_name, encryption_type='', key_id='',
                           wait=True, wait_timeout=300, check_mode=False):
    """Stop encryption on an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        encryption_type (str): KMS or NONE
        key_id (str): KMS key GUID or alias
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> stop_stream_encryption(client, stream_name,encryption_type, key_id)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    params = {
        'StreamName': stream_name
    }

    results = dict()
    stream_found, stream_msg, current_stream = (
        find_stream(client, stream_name)
    )
    if stream_found:
        if current_stream.get('EncryptionType') == 'KMS':
            success, err_msg = (
                stream_encryption_action(
                    client, stream_name, action='stop_encryption', key_id=key_id, encryption_type=encryption_type, check_mode=check_mode
                )
            )
            changed = success
            if wait:
                success, err_msg, results = (
                    wait_for_status(
                        client, stream_name, 'ACTIVE', wait_timeout,
                        check_mode=check_mode
                    )
                )
                if not success:
                    return success, True, err_msg, results
                err_msg = 'Kinesis Stream {0} encryption stopped successfully.'.format(stream_name)
            else:
                err_msg = (
                    'Stream {0} is in the process of stopping encryption.'.format(stream_name)
                )
        elif current_stream.get('EncryptionType') == 'NONE':
            success = True
            err_msg = 'Kinesis Stream {0} encryption already stopped.'.format(stream_name)
    else:
        success = True
        changed = False
        err_msg = 'Stream {0} does not exist.'.format(stream_name)

    if success:
        stream_found, stream_msg, results = (
            find_stream(client, stream_name)
        )
        tag_success, tag_msg, current_tags = (
            get_tags(client, stream_name)
        )
        if not current_tags:
            current_tags = dict()

        results = camel_dict_to_snake_dict(results)
        results['tags'] = current_tags

    return success, changed, err_msg, results


def main():
    argument_spec = dict(
        name=dict(required=True),
        shards=dict(default=None, required=False, type='int'),
        retention_period=dict(default=None, required=False, type='int'),
        tags=dict(default=None, required=False, type='dict', aliases=['resource_tags']),
        wait=dict(default=True, required=False, type='bool'),
        wait_timeout=dict(default=300, required=False, type='int'),
        state=dict(default='present', choices=['present', 'absent']),
        encryption_type=dict(required=False, choices=['NONE', 'KMS']),
        key_id=dict(required=False, type='str'),
        encryption_state=dict(required=False, choices=['enabled', 'disabled']),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    retention_period = module.params.get('retention_period')
    stream_name = module.params.get('name')
    shards = module.params.get('shards')
    state = module.params.get('state')
    tags = module.params.get('tags')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    encryption_type = module.params.get('encryption_type')
    key_id = module.params.get('key_id')
    encryption_state = module.params.get('encryption_state')

    if state == 'present' and not shards:
        module.fail_json(msg='Shards is required when state == present.')

    if retention_period:
        if retention_period < 24:
            module.fail_json(msg='Retention period can not be less than 24 hours.')

    check_mode = module.check_mode
    try:
        client = module.client('kinesis')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    if state == 'present':
        success, changed, err_msg, results = (
            create_stream(
                client, stream_name, shards, retention_period, tags,
                wait, wait_timeout, check_mode
            )
        )
        if encryption_state == 'enabled':
            success, changed, err_msg, results = (
                start_stream_encryption(
                    client, stream_name, encryption_type, key_id, wait, wait_timeout, check_mode
                )
            )
        elif encryption_state == 'disabled':
            success, changed, err_msg, results = (
                stop_stream_encryption(
                    client, stream_name, encryption_type, key_id, wait, wait_timeout, check_mode
                )
            )
    elif state == 'absent':
        success, changed, err_msg, results = (
            delete_stream(client, stream_name, wait, wait_timeout, check_mode)
        )

    if success:
        module.exit_json(
            success=success, changed=changed, msg=err_msg, **results
        )
    else:
        module.fail_json(
            success=success, changed=changed, msg=err_msg, result=results
        )


if __name__ == '__main__':
    main()

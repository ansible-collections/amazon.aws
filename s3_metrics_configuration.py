#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: s3_metrics_configuration
version_added: 1.3.0
short_description: Manage s3 bucket metrics configuration in AWS
description:
    - Manage s3 bucket metrics configuration in AWS which allows to get the CloudWatch request metrics for the objects in a bucket
author: Dmytro Vorotyntsev (@vorotech)
notes:
    - This modules manages single metrics configuration, the s3 bucket might have up to 1,000 metrics configurations
    - To request metrics for the entire bucket, create a metrics configuration without a filter
    - Metrics configurations are necessary only to enable request metric, bucket-level daily storage metrics are always turned on
options:
  bucket_name:
    description:
      - "Name of the s3 bucket"
    required: true
    type: str
  id:
    description:
      - "The ID used to identify the metrics configuration"
    required: true
    type: str
  filter_prefix:
    description:
      - "A prefix used when evaluating a metrics filter"
    required: false
    type: str
  filter_tags:
    description:
      - "A dictionary of one or more tags used when evaluating a metrics filter"
    required: false
    aliases: ['filter_tag']
    type: dict
    default: {}
  state:
    description:
      - "Create or delete metrics configuration"
    default: present
    choices: ['present', 'absent']
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a metrics configuration that enables metrics for an entire bucket
  community.aws.s3_metrics_configuration:
    bucket_name: my-bucket
    id: EntireBucket
    state: present

- name: Put a metrics configuration that enables metrics for objects starting with a prefix
  community.aws.s3_metrics_configuration:
    bucket_name: my-bucket
    id: Assets
    filter_prefix: assets
    state: present

- name: Put a metrics configuration that enables metrics for objects with specific tag
  community.aws.s3_metrics_configuration:
    bucket_name: my-bucket
    id: Assets
    filter_tag:
      kind: asset
    state: present

- name: Put a metrics configuration that enables metrics for objects that start with a particular prefix and have specific tags applied
  community.aws.s3_metrics_configuration:
    bucket_name: my-bucket
    id: ImportantBlueDocuments
    filter_prefix: documents
    filter_tags:
      priority: high
      class: blue
    state: present

- name: Delete metrics configuration
  community.aws.s3_metrics_configuration:
    bucket_name: my-bucket
    id: EntireBucket
    state: absent

'''

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list


def _create_metrics_configuration(mc_id, filter_prefix, filter_tags):
    payload = {
        'Id': mc_id
    }
    # Just a filter_prefix or just a single tag filter is a special case
    if filter_prefix and not filter_tags:
        payload['Filter'] = {
            'Prefix': filter_prefix
        }
    elif not filter_prefix and len(filter_tags) == 1:
        payload['Filter'] = {
            'Tag': ansible_dict_to_boto3_tag_list(filter_tags)[0]
        }
    # Otherwise we need to use 'And'
    elif filter_tags:
        payload['Filter'] = {
            'And': {
                'Tags': ansible_dict_to_boto3_tag_list(filter_tags)
            }
        }
        if filter_prefix:
            payload['Filter']['And']['Prefix'] = filter_prefix

    return payload


def create_or_update_metrics_configuration(client, module):
    bucket_name = module.params.get('bucket_name')
    mc_id = module.params.get('id')
    filter_prefix = module.params.get('filter_prefix')
    filter_tags = module.params.get('filter_tags')

    try:
        response = client.get_bucket_metrics_configuration(aws_retry=True, Bucket=bucket_name, Id=mc_id)
        metrics_configuration = response['MetricsConfiguration']
    except is_boto3_error_code('NoSuchConfiguration'):
        metrics_configuration = None
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket metrics configuration")

    new_configuration = _create_metrics_configuration(mc_id, filter_prefix, filter_tags)

    if metrics_configuration:
        if metrics_configuration == new_configuration:
            module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        client.put_bucket_metrics_configuration(
            aws_retry=True,
            Bucket=bucket_name,
            Id=mc_id,
            MetricsConfiguration=new_configuration
        )
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to put bucket metrics configuration '%s'" % mc_id)

    module.exit_json(changed=True)


def delete_metrics_configuration(client, module):
    bucket_name = module.params.get('bucket_name')
    mc_id = module.params.get('id')

    try:
        client.get_bucket_metrics_configuration(aws_retry=True, Bucket=bucket_name, Id=mc_id)
    except is_boto3_error_code('NoSuchConfiguration'):
        module.exit_json(changed=False)
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket metrics configuration")

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        client.delete_bucket_metrics_configuration(aws_retry=True, Bucket=bucket_name, Id=mc_id)
    except is_boto3_error_code('NoSuchConfiguration'):
        module.exit_json(changed=False)
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to delete bucket metrics configuration '%s'" % mc_id)

    module.exit_json(changed=True)


def main():
    argument_spec = dict(
        bucket_name=dict(type='str', required=True),
        id=dict(type='str', required=True),
        filter_prefix=dict(type='str', required=False),
        filter_tags=dict(default={}, type='dict', required=False, aliases=['filter_tag']),
        state=dict(default='present', type='str', choices=['present', 'absent']),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params.get('state')

    try:
        client = module.client('s3', retry_decorator=AWSRetry.exponential_backoff(retries=10, delay=3))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    if state == 'present':
        create_or_update_metrics_configuration(client, module)
    elif state == 'absent':
        delete_metrics_configuration(client, module)


if __name__ == '__main__':
    main()

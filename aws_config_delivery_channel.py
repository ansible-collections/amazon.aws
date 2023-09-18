#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: aws_config_delivery_channel
version_added: 1.0.0
short_description: Manage AWS Config delivery channels
description:
    - This module manages AWS Config delivery locations for rule checks and configuration info.
author:
    - "Aaron Smith (@slapula)"
options:
  name:
    description:
    - The name of the AWS Config resource.
    required: true
    type: str
  state:
    description:
    - Whether the Config rule should be present or absent.
    default: present
    choices: ['present', 'absent']
    type: str
  s3_bucket:
    description:
    - The name of the Amazon S3 bucket to which AWS Config delivers configuration snapshots and configuration history files.
    type: str
    required: true
  s3_prefix:
    description:
    - The prefix for the specified Amazon S3 bucket.
    type: str
  sns_topic_arn:
    description:
    - The Amazon Resource Name (ARN) of the Amazon SNS topic to which AWS Config sends notifications about configuration changes.
    type: str
  delivery_frequency:
    description:
    - The frequency with which AWS Config delivers configuration snapshots.
    choices: ['One_Hour', 'Three_Hours', 'Six_Hours', 'Twelve_Hours', 'TwentyFour_Hours']
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: Create Delivery Channel for AWS Config
  community.aws.aws_config_delivery_channel:
    name: test_delivery_channel
    state: present
    s3_bucket: 'test_aws_config_bucket'
    sns_topic_arn: 'arn:aws:sns:us-east-1:123456789012:aws_config_topic:1234ab56-cdef-7g89-01hi-2jk34l5m67no'
    delivery_frequency: 'Twelve_Hours'
'''

RETURN = '''#'''


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


# this waits for an IAM role to become fully available, at the cost of
# taking a long time to fail when the IAM role/policy really is invalid
retry_unavailable_iam_on_put_delivery = AWSRetry.jittered_backoff(
    catch_extra_error_codes=['InsufficientDeliveryPolicyException'],
)


def resource_exists(client, module, params):
    try:
        channel = client.describe_delivery_channels(
            DeliveryChannelNames=[params['name']],
            aws_retry=True,
        )
        return channel['DeliveryChannels'][0]
    except is_boto3_error_code('NoSuchDeliveryChannelException'):
        return
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


def create_resource(client, module, params, result):
    try:
        retry_unavailable_iam_on_put_delivery(
            client.put_delivery_channel,
        )(
            DeliveryChannel=params,
        )
        result['changed'] = True
        result['channel'] = camel_dict_to_snake_dict(resource_exists(client, module, params))
        return result
    except is_boto3_error_code('InvalidS3KeyPrefixException') as e:
        module.fail_json_aws(e, msg="The `s3_prefix` parameter was invalid. Try '/' for no prefix")
    except is_boto3_error_code('InsufficientDeliveryPolicyException') as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="The `s3_prefix` or `s3_bucket` parameter is invalid. "
                             "Make sure the bucket exists and is available")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't create AWS Config delivery channel")


def update_resource(client, module, params, result):
    current_params = client.describe_delivery_channels(
        DeliveryChannelNames=[params['name']],
        aws_retry=True,
    )

    if params != current_params['DeliveryChannels'][0]:
        try:
            retry_unavailable_iam_on_put_delivery(
                client.put_delivery_channel,
            )(
                DeliveryChannel=params,
            )
            result['changed'] = True
            result['channel'] = camel_dict_to_snake_dict(resource_exists(client, module, params))
            return result
        except is_boto3_error_code('InvalidS3KeyPrefixException') as e:
            module.fail_json_aws(e, msg="The `s3_prefix` parameter was invalid. Try '/' for no prefix")
        except is_boto3_error_code('InsufficientDeliveryPolicyException') as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="The `s3_prefix` or `s3_bucket` parameter is invalid. "
                                 "Make sure the bucket exists and is available")
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Couldn't create AWS Config delivery channel")


def delete_resource(client, module, params, result):
    try:
        response = client.delete_delivery_channel(
            DeliveryChannelName=params['name']
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete AWS Config delivery channel")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            's3_bucket': dict(type='str', required=True),
            's3_prefix': dict(type='str'),
            'sns_topic_arn': dict(type='str'),
            'delivery_frequency': dict(
                type='str',
                choices=[
                    'One_Hour',
                    'Three_Hours',
                    'Six_Hours',
                    'Twelve_Hours',
                    'TwentyFour_Hours'
                ]
            ),
        },
        supports_check_mode=False,
    )

    result = {
        'changed': False
    }

    name = module.params.get('name')
    state = module.params.get('state')

    params = {}
    if name:
        params['name'] = name
    if module.params.get('s3_bucket'):
        params['s3BucketName'] = module.params.get('s3_bucket')
    if module.params.get('s3_prefix'):
        params['s3KeyPrefix'] = module.params.get('s3_prefix')
    if module.params.get('sns_topic_arn'):
        params['snsTopicARN'] = module.params.get('sns_topic_arn')
    if module.params.get('delivery_frequency'):
        params['configSnapshotDeliveryProperties'] = {
            'deliveryFrequency': module.params.get('delivery_frequency')
        }

    client = module.client('config', retry_decorator=AWSRetry.jittered_backoff())

    resource_status = resource_exists(client, module, params)

    if state == 'present':
        if not resource_status:
            create_resource(client, module, params, result)
        if resource_status:
            update_resource(client, module, params, result)

    if state == 'absent':
        if resource_status:
            delete_resource(client, module, params, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: sns_topic_info
short_description: sns_topic_info module
version_added: 3.2.0
description:
- The M(community.aws.sns_topic_info) module allows to get all AWS SNS topics or properties of a specific AWS SNS topic.
author:
- "Alina Buzachis (@alinabuzachis)"
options:
    topic_arn:
        description: The ARN of the AWS SNS topic for which you wish to find subscriptions or list attributes.
        required: false
        type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = r'''
- name: list all the topics
  community.aws.sns_topic_info:
  register: sns_topic_list

- name: get info on specific topic
  community.aws.sns_topic_info:
    topic_arn: "{{ sns_arn }}"
  register: sns_topic_info
'''

RETURN = r'''
result:
  description:
    - The result contaning the details of one or all AWS SNS topics.
  returned: success
  type: list
  contains:
    sns_arn:
        description: The ARN of the topic.
        type: str
        returned: always
        sample: "arn:aws:sns:us-east-2:123456789012:my_topic_name"
    sns_topic:
        description: Dict of sns topic details.
        type: complex
        returned: always
        contains:
            delivery_policy:
                description: Delivery policy for the SNS topic.
                returned: when topic is owned by this AWS account
                type: str
                sample: >
                    {"http":{"defaultHealthyRetryPolicy":{"minDelayTarget":20,"maxDelayTarget":20,"numRetries":3,"numMaxDelayRetries":0,
                    "numNoDelayRetries":0,"numMinDelayRetries":0,"backoffFunction":"linear"},"disableSubscriptionOverrides":false}}
            display_name:
                description: Display name for SNS topic.
                returned: when topic is owned by this AWS account
                type: str
                sample: My topic name
            owner:
                description: AWS account that owns the topic.
                returned: when topic is owned by this AWS account
                type: str
                sample: '123456789012'
            policy:
                description: Policy for the SNS topic.
                returned: when topic is owned by this AWS account
                type: str
                sample: >
                    {"Version":"2012-10-17","Id":"SomePolicyId","Statement":[{"Sid":"ANewSid","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::123456789012:root"},
                    "Action":"sns:Subscribe","Resource":"arn:aws:sns:us-east-2:123456789012:ansible-test-dummy-topic","Condition":{"StringEquals":{"sns:Protocol":"email"}}}]}
            subscriptions:
                description: List of subscribers to the topic in this AWS account.
                returned: always
                type: list
                sample: []
            subscriptions_added:
                description: List of subscribers added in this run.
                returned: always
                type: list
                sample: []
            subscriptions_confirmed:
                description: Count of confirmed subscriptions.
                returned: when topic is owned by this AWS account
                type: str
                sample: '0'
            subscriptions_deleted:
                description: Count of deleted subscriptions.
                returned: when topic is owned by this AWS account
                type: str
                sample: '0'
            subscriptions_existing:
                description: List of existing subscriptions.
                returned: always
                type: list
                sample: []
            subscriptions_new:
                description: List of new subscriptions.
                returned: always
                type: list
                sample: []
            subscriptions_pending:
                description: Count of pending subscriptions.
                returned: when topic is owned by this AWS account
                type: str
                sample: '0'
            subscriptions_purge:
                description: Whether or not purge_subscriptions was set.
                returned: always
                type: bool
                sample: true
            topic_arn:
                description: ARN of the SNS topic (equivalent to sns_arn).
                returned: when topic is owned by this AWS account
                type: str
                sample: arn:aws:sns:us-east-2:123456789012:ansible-test-dummy-topic
            topic_type:
                description: The type of topic.
                type: str
                sample: "standard"
'''


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.community.aws.plugins.module_utils.sns import list_topics
from ansible_collections.community.aws.plugins.module_utils.sns import get_info


def main():
    argument_spec = dict(
        topic_arn=dict(type='str', required=False),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    topic_arn = module.params.get('topic_arn')

    try:
        connection = module.client('sns', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS.')

    if topic_arn:
        results = dict(sns_arn=topic_arn, sns_topic=get_info(connection, module, topic_arn))
    else:
        results = list_topics(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()

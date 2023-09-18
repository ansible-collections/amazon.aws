#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Michael J. Schultz <mjschultz@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: sns
short_description: Send Amazon Simple Notification Service messages
version_added: 1.0.0
description:
  - Sends a notification to a topic on your Amazon SNS account.
author:
  - Michael J. Schultz (@mjschultz)
  - Paul Arthur (@flowerysong)
options:
  msg:
    description:
      - Default message for subscriptions without a more specific message.
    required: true
    aliases: [ "default" ]
    type: str
  subject:
    description:
      - Message subject
    type: str
  topic:
    description:
      - The name or ARN of the topic to publish to.
    required: true
    type: str
  email:
    description:
      - Message to send to email subscriptions.
    type: str
  email_json:
    description:
      - Message to send to email-json subscriptions.
    type: str
  sqs:
    description:
      - Message to send to SQS subscriptions.
    type: str
  sms:
    description:
      - Message to send to SMS subscriptions.
    type: str
  http:
    description:
      - Message to send to HTTP subscriptions.
    type: str
  https:
    description:
      - Message to send to HTTPS subscriptions.
    type: str
  application:
    description:
      - Message to send to application subscriptions.
    type: str
  lambda:
    description:
      - Message to send to Lambda subscriptions.
    type: str
  message_attributes:
    description:
      - Dictionary of message attributes. These are optional structured data entries to be sent along to the endpoint.
      - This is in AWS's distinct Name/Type/Value format; see example below.
    type: dict
  message_structure:
    description:
      - The payload format to use for the message.
      - This must be C(json) to support protocol-specific messages (C(http), C(https), C(email), C(sms), C(sqs)).
      - It must be C(string) to support I(message_attributes).
    default: json
    choices: ['json', 'string']
    type: str
  message_group_id:
    description:
      - A tag which is used to process messages that belong to the same group in a FIFO manner.
      - Has to be included when publishing a message to a fifo topic.
      - Can contain up to 128 alphanumeric characters and punctuation.
    type: str
    version_added: 5.4.0
  message_deduplication_id:
    description:
      - Only in connection with the message_group_id.
      - Overwrites the auto generated MessageDeduplicationId.
      - Can contain up to 128 alphanumeric characters and punctuation.
      - Messages with the same deduplication id getting recognized as the same message.
      - Gets overwritten by an auto generated token, if the topic has ContentBasedDeduplication set.
    type: str
    version_added: 5.4.0

extends_documentation_fragment:
  - amazon.aws.region.modules
  - amazon.aws.common.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Send default notification message via SNS
  community.aws.sns:
    msg: '{{ inventory_hostname }} has completed the play.'
    subject: Deploy complete!
    topic: deploy
  delegate_to: localhost

- name: Send notification messages via SNS with short message for SMS
  community.aws.sns:
    msg: '{{ inventory_hostname }} has completed the play.'
    sms: deployed!
    subject: Deploy complete!
    topic: deploy
  delegate_to: localhost

- name: Send message with message_attributes
  community.aws.sns:
    topic: "deploy"
    msg: "message with extra details!"
    message_attributes:
      channel:
        data_type: String
        string_value: "mychannel"
      color:
        data_type: String
        string_value: "green"
  delegate_to: localhost

- name: Send message to a fifo topic
  community.aws.sns:
    topic: "deploy"
    msg: "Message with message group id"
    subject: Deploy complete!
    message_group_id: "deploy-1"
  delegate_to: localhost
"""

RETURN = r"""
msg:
  description: Human-readable diagnostic information
  returned: always
  type: str
  sample: OK
message_id:
  description: The message ID of the submitted message
  returned: when success
  type: str
  sample: 2f681ef0-6d76-5c94-99b2-4ae3996ce57b
sequence_number:
  description: A 128 bits long sequence number which gets assigned to the message in fifo topics
  returned: when success
  type: str
"""

import json

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.community.aws.plugins.module_utils.sns import topic_arn_lookup

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def main():
    protocols = [
        "http",
        "https",
        "email",
        "email_json",
        "sms",
        "sqs",
        "application",
        "lambda",
    ]

    argument_spec = dict(
        msg=dict(required=True, aliases=["default"]),
        subject=dict(),
        topic=dict(required=True),
        message_attributes=dict(type="dict"),
        message_structure=dict(choices=["json", "string"], default="json"),
        message_group_id=dict(),
        message_deduplication_id=dict(),
    )

    for p in protocols:
        argument_spec[p] = dict()

    module = AnsibleAWSModule(argument_spec=argument_spec)

    sns_kwargs = dict(
        Message=module.params["msg"],
        Subject=module.params["subject"],
        MessageStructure=module.params["message_structure"],
    )

    if module.params["message_attributes"]:
        if module.params["message_structure"] != "string":
            module.fail_json(msg='message_attributes is only supported when the message_structure is "string".')
        sns_kwargs["MessageAttributes"] = module.params["message_attributes"]

    if module.params["message_group_id"]:
        sns_kwargs["MessageGroupId"] = module.params["message_group_id"]
        if module.params["message_deduplication_id"]:
            sns_kwargs["MessageDeduplicationId"] = module.params["message_deduplication_id"]

    dict_msg = {"default": sns_kwargs["Message"]}

    for p in protocols:
        if module.params[p]:
            if sns_kwargs["MessageStructure"] != "json":
                module.fail_json(msg='Protocol-specific messages are only supported when message_structure is "json".')
            dict_msg[p.replace("_", "-")] = module.params[p]

    client = module.client("sns")

    topic = module.params["topic"]
    if ":" in topic:
        # Short names can't contain ':' so we'll assume this is the full ARN
        sns_kwargs["TopicArn"] = topic
    else:
        sns_kwargs["TopicArn"] = topic_arn_lookup(client, module, topic)

    if not sns_kwargs["TopicArn"]:
        module.fail_json(msg=f"Could not find topic: {topic}")

    if sns_kwargs["MessageStructure"] == "json":
        sns_kwargs["Message"] = json.dumps(dict_msg)

    try:
        result = client.publish(**sns_kwargs)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to publish message")

    sns_result = dict(msg="OK", message_id=result["MessageId"])

    if module.params["message_group_id"]:
        sns_result["sequence_number"] = result["SequenceNumber"]

    module.exit_json(**sns_result)


if __name__ == "__main__":
    main()

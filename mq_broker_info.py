#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: mq_broker_info
version_added: 6.0.0
short_description: Retrieve MQ Broker details
description:
  - Get details about a broker.
author:
  - FCO (@fotto)
options:
  broker_id:
    description: Get details for broker with specified ID.
    type: str
  broker_name:
    description:
      - Get details for broker with specified Name.
      - Is ignored if I(broker_id) is specified.
    type: str
extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.modules
  - amazon.aws.region.modules
"""


EXAMPLES = r"""
- name: get current broker settings by id
  amazon.aws.mq_broker_info:
    broker_id: "aws-mq-broker-id"
  register: broker_info
- name: get current broker settings by name setting all credential parameters explicitly
  amazon.aws.mq_broker_info:
    broker_name: "aws-mq-broker-name"
  register: broker_info
"""

RETURN = r"""
broker:
    description: API response of describe_broker() converted to snake yaml.
    type: dict
    returned: success
"""

try:
    import botocore
except ImportError:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def get_broker_id(conn, module):
    try:
        broker_name = module.params["broker_name"]
        broker_id = None
        response = conn.list_brokers(MaxResults=100)
        for broker in response["BrokerSummaries"]:
            if broker["BrokerName"] == broker_name:
                broker_id = broker["BrokerId"]
                break
        return broker_id
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list broker brokers.")


def get_broker_info(conn, module, broker_id):
    try:
        return conn.describe_broker(BrokerId=broker_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if module.check_mode:
            module.exit_json(broker={"broker_id": broker_id, "broker_name": "fakeName"})
        else:
            module.fail_json_aws(e, msg="Couldn't get broker details.")


def main():
    argument_spec = dict(broker_id=dict(type="str"), broker_name=dict(type="str"))
    required_one_of = (
        (
            "broker_name",
            "broker_id",
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=required_one_of,
        supports_check_mode=True,
    )
    broker_id = module.params["broker_id"]
    broker_name = module.params["broker_name"]

    connection = module.client("mq")

    try:
        if not broker_id:
            broker_id = get_broker_id(connection, module)
        if not broker_id:
            if module.check_mode:
                module.exit_json(
                    broker={"broker_id": "fakeId", "broker_name": broker_name if broker_name else "fakeName"}
                )
        result = get_broker_info(connection, module, broker_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)
    #
    module.exit_json(broker=camel_dict_to_snake_dict(result, ignore_list=["Tags"]))


if __name__ == "__main__":
    main()

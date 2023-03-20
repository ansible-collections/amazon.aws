#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: mq_user_info
version_added: 6.0.0
short_description: List users of an Amazon MQ broker
description:
  - List users for the specified broker ID.
  - Pending creations and deletions can be skipped by options.
author:
  - FCO (@fotto)
options:
  broker_id:
    description:
      - The ID of the MQ broker to work on.
    type: str
    required: true
  max_results:
    description:
      - The maximum number of results to return.
    type: int
    default: 100
  skip_pending_create:
    description:
      - Will skip pending creates from the result set.
    type: bool
    default: false
  skip_pending_delete:
    description:
      - Will skip pending deletes from the result set.
    type: bool
    default: false
  as_dict:
    description:
      - Convert result into lookup table by username.
    type: bool
    default: false

extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.modules
  - amazon.aws.region.modules
"""


EXAMPLES = r"""
- name: get all users as list - relying on environment for API credentials
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    max_results: 50
  register: result
- name: get users as dict - explicitly specifying all credentials
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
  register: result
- name: get list of users to decide which may need to be deleted
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    skip_pending_delete: true
- name: get list of users to decide which may need to be created
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    skip_pending_create: true
"""

RETURN = r"""
users:
    type: dict
    returned: success
    description:
    - dict key is username
    - each entry is the record for a user as returned by API but converted to snake yaml
"""

try:
    import botocore
except ImportError as ex:
    # handled by AnsibleAWSModule
    pass

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


DEFAULTS = {"max_results": 100, "skip_pending_create": False, "skip_pending_delete": False, "as_dict": True}


def get_user_info(conn, module):
    try:
        response = conn.list_users(BrokerId=module.params["broker_id"], MaxResults=module.params["max_results"])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if module.check_mode:
            # return empty set for unknown broker in check mode
            if DEFAULTS["as_dict"]:
                return {}
            return []
        module.fail_json_aws(e, msg="Failed to describe users")
    #
    if not module.params["skip_pending_create"] and not module.params["skip_pending_delete"]:
        # we can simply return the sub-object from the response
        records = response["Users"]
    else:
        records = []
        for record in response["Users"]:
            if "PendingChange" in record:
                if record["PendingChange"] == "CREATE" and module.params["skip_pending_create"]:
                    continue
                if record["PendingChange"] == "DELETE" and module.params["skip_pending_delete"]:
                    continue
            #
            records.append(record)
    #
    if DEFAULTS["as_dict"]:
        user_records = {}
        for record in records:
            user_records[record["Username"]] = record
        #
        return camel_dict_to_snake_dict(user_records, ignore_list=["Tags"])

    return camel_dict_to_snake_dict(records, ignore_list=["Tags"])


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type="str"),
        max_results=dict(required=False, type="int", default=DEFAULTS["max_results"]),
        skip_pending_create=dict(required=False, type="bool", default=DEFAULTS["skip_pending_create"]),
        skip_pending_delete=dict(required=False, type="bool", default=DEFAULTS["skip_pending_delete"]),
        as_dict=dict(required=False, type="bool", default=False),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("mq")

    try:
        user_records = get_user_info(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(users=user_records)


if __name__ == "__main__":
    main()

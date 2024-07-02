#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_key_info
version_added: 6.4.0
short_description: Gather information about EC2 key pairs in AWS
description:
    - Gather information about EC2 key pairs in AWS.
author:
  - Aubin Bikouo (@abikouo)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeKeyPairs.html) for possible filters. Filter
        names and values are case sensitive.
    required: false
    default: {}
    type: dict
  names:
    description:
      - The key pair names.
    required: false
    type: list
    elements: str
    default: []
  ids:
    description:
      - The IDs of the key pairs.
    required: false
    type: list
    elements: str
    default: []
  include_public_key:
    description:
      - Whether or not to include the public key material in the response.
    type: bool
    default: false
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all key pairs
  amazon.aws.ec2_key_info:

- name: Gather information about a specific key pair
  amazon.aws.ec2_key_info:
    names:
      - my-sample-key

- name: Retrieve EC2 key pair by fingerprint
  amazon.aws.ec2_key_info:
    filters:
      fingerprint: "1bSd8jVye3In5oF4zZI4o8BcXfdbYN+daCt9O1fh3Qk="
"""

RETURN = r"""
keypairs:
    description: A list of ec2 key pairs.
    returned: always
    type: complex
    contains:
        key_pair_id:
            description: The ID of the key pair.
            returned: always
            type: str
            sample: key-01238eb03f07d7268
        key_fingerprint:
            description: Fingerprint of the key.
            returned: always
            type: str
            sample: '05:97:1a:2a:df:f6:06:a9:98:4b:ca:05:71:a1:81:e8:ff:6d:d2:a3'
        key_name:
            description: The name of the key pair.
            returned: always
            type: str
            sample: my-sample-keypair
        key_type:
            description: The type of key pair.
            returned: always
            type: str
            sample: rsa
        public_key:
            description: The public key material.
            returned: always
            type: str
        create_time:
            description: The time the key pair was created.
            returned: always
            type: str
            sample: "2023-08-16T10:13:33.025000+00:00"
        tags:
            description: A dictionary representing the tags attached to the key pair.
            returned: always
            type: dict
            sample: '{"my_key": "my value"}'
"""


try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_key_pairs
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def list_ec2_key_pairs(connection, module):
    ids = module.params.get("ids")
    names = module.params.get("names")
    include_public_key = module.params.get("include_public_key")
    filters = module.params.get("filters")
    if filters:
        filters = ansible_dict_to_boto3_filter_list(filters)

    params = {}
    if filters:
        params["Filters"] = filters
    if ids:
        params["KeyPairIds"] = ids
    if names:
        params["KeyNames"] = names
    if include_public_key:
        params["IncludePublicKey"] = True

    try:
        result = describe_key_pairs(connection, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to list EC2 key pairs")

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_keys = [camel_dict_to_snake_dict(key) for key in result]

    # Turn the boto3 result in to ansible friendly tag dictionary
    for key in snaked_keys:
        key["tags"] = boto3_tag_list_to_ansible_dict(key.get("tags", []), "key", "value")

    module.exit_json(keypairs=snaked_keys)


def main():
    argument_spec = dict(
        filters=dict(type="dict", default={}),
        names=dict(type="list", elements="str", default=[]),
        ids=dict(type="list", elements="str", default=[]),
        include_public_key=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        connection = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    list_ec2_key_pairs(connection, module)


if __name__ == "__main__":
    main()

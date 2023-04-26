#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ssm_parameter
version_added: 1.0.0
short_description: Manage key-value pairs in AWS Systems Manager Parameter Store
description:
  - Manage key-value pairs in AWS Systems Manager (SSM) Parameter Store.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_ssm_parameter_store).
    The usage did not change.
options:
  name:
    description:
      - Parameter key name.
    required: true
    type: str
  description:
    description:
      - Parameter key description.
    required: false
    type: str
  value:
    description:
      - Parameter value.
    required: false
    type: str
  state:
    description:
      - Creates or modifies an existing parameter.
      - Deletes a parameter.
    required: false
    choices: ['present', 'absent']
    default: present
    type: str
  string_type:
    description:
      - Parameter String type.
    required: false
    choices: ['String', 'StringList', 'SecureString']
    default: String
    type: str
    aliases: ['type']
  decryption:
    description:
      - Work with SecureString type to get plain text secrets
    type: bool
    required: false
    default: true
  key_id:
    description:
      - AWS KMS key to decrypt the secrets.
      - The default key (C(alias/aws/ssm)) is automatically generated the first
        time it's requested.
    required: false
    default: alias/aws/ssm
    type: str
  overwrite_value:
    description:
      - Option to overwrite an existing value if it already exists.
    required: false
    choices: ['never', 'changed', 'always']
    default: changed
    type: str
  tier:
    description:
      - Parameter store tier type.
    required: false
    choices: ['Standard', 'Advanced', 'Intelligent-Tiering']
    default: Standard
    type: str
    version_added: 1.5.0
seealso:
  - ref: amazon.aws.aws_ssm lookup <ansible_collections.amazon.aws.aws_ssm_lookup>
    description: The documentation for the C(amazon.aws.aws_ssm) lookup plugin.

author:
  - "Davinder Pal (@116davinder) <dpsangwal@gmail.com>"
  - "Nathan Webster (@nathanwebsterdotme)"
  - "Bill Wang (@ozbillwang) <ozbillwang@gmail.com>"
  - "Michael De La Rue (@mikedlr)"

notes:
  - Support for I(tags) and I(purge_tags) was added in release 5.3.0.

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create or update key/value pair in AWS SSM parameter store
  community.aws.ssm_parameter:
    name: "Hello"
    description: "This is your first key"
    value: "World"

- name: Delete the key
  community.aws.ssm_parameter:
    name: "Hello"
    state: absent

- name: Create or update secure key/value pair with default KMS key (aws/ssm)
  community.aws.ssm_parameter:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    value: "World"

- name: Create or update secure key/value pair with nominated KMS key
  community.aws.ssm_parameter:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    key_id: "alias/demo"
    value: "World"

- name: Always update a parameter store value and create a new version
  community.aws.ssm_parameter:
    name: "overwrite_example"
    description: "This example will always overwrite the value"
    string_type: "String"
    value: "Test1234"
    overwrite_value: "always"

- name: Create or update key/value pair in AWS SSM parameter store with tier
  community.aws.ssm_parameter:
    name: "Hello"
    description: "This is your first key"
    value: "World"
    tier: "Advanced"

- name: recommend to use with aws_ssm lookup plugin
  ansible.builtin.debug:
    msg: "{{ lookup('amazon.aws.aws_ssm', 'Hello') }}"

- name: Create or update key/value pair in AWS SSM parameter store w/ tags
  community.aws.ssm_parameter:
    name: "Hello"
    description: "This is your first key"
    value: "World"
    tags:
      Environment: "dev"
      Version: "1.0"
      Confidentiality: "low"
      Tag With Space: "foo bar"

- name: Add or update a tag on an existing parameter w/o removing existing tags
  community.aws.ssm_parameter:
    name: "Hello"
    purge_tags: false
    tags:
      Contact: "person1"

- name: Delete all tags on an existing parameter
  community.aws.ssm_parameter:
    name: "Hello"
    tags: {}
"""

RETURN = r"""
parameter_metadata:
  type: dict
  description:
    - Information about a parameter.
    - Does not include the value of the parameter as this can be sensitive
      information.
  returned: success
  contains:
    data_type:
      type: str
      description: Parameter Data type.
      example: text
      returned: success
    description:
      type: str
      description: Parameter key description.
      example: This is your first key
      returned: success
    last_modified_date:
      type: str
      description: Time and date that the parameter was last modified.
      example: '2022-06-20T09:56:58.573000+00:00'
      returned: success
    last_modified_user:
      type: str
      description: ARN of the last user to modify the parameter.
      example: 'arn:aws:sts::123456789012:assumed-role/example-role/session=example'
      returned: success
    name:
      type: str
      description: Parameter key name.
      example: Hello
      returned: success
    policies:
      type: list
      description: A list of policies associated with a parameter.
      elements: dict
      returned: success
      contains:
        policy_text:
          type: str
          description: The JSON text of the policy.
          returned: success
        policy_type:
          type: str
          description: The type of policy.
          example: Expiration
          returned: success
        policy_status:
          type: str
          description: The status of the policy.
          example: Pending
          returned: success
    tier:
      type: str
      description: Parameter tier.
      example: Standard
      returned: success
    type:
      type: str
      description: Parameter type
      example: String
      returned: success
    version:
      type: int
      description: Parameter version number
      example: 3
      returned: success
    tags:
      description: A dictionary representing the tags associated with the parameter.
      type: dict
      returned: when the parameter has tags
      example: {'MyTagName': 'Some Value'}
      version_added: 5.3.0
"""

import time

try:
    import botocore
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

from ansible_collections.community.aws.plugins.module_utils.base import BaseWaiterFactory
from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class ParameterWaiterFactory(BaseWaiterFactory):
    def __init__(self, module):
        client = module.client("ssm")
        super(ParameterWaiterFactory, self).__init__(module, client)

    @property
    def _waiter_model_data(self):
        data = super(ParameterWaiterFactory, self)._waiter_model_data
        ssm_data = dict(
            parameter_exists=dict(
                operation="DescribeParameters",
                delay=1,
                maxAttempts=20,
                acceptors=[
                    dict(state="retry", matcher="error", expected="ParameterNotFound"),
                    dict(state="retry", matcher="path", expected=True, argument="length(Parameters[].Name) == `0`"),
                    dict(state="success", matcher="path", expected=True, argument="length(Parameters[].Name) > `0`"),
                ],
            ),
            parameter_deleted=dict(
                operation="DescribeParameters",
                delay=1,
                maxAttempts=20,
                acceptors=[
                    dict(state="retry", matcher="path", expected=True, argument="length(Parameters[].Name) > `0`"),
                    dict(state="success", matcher="path", expected=True, argument="length(Parameters[]) == `0`"),
                    dict(state="success", matcher="error", expected="ParameterNotFound"),
                ],
            ),
        )
        data.update(ssm_data)
        return data


def _wait_exists(client, module, name):
    if module.check_mode:
        return
    wf = ParameterWaiterFactory(module)
    waiter = wf.get_waiter("parameter_exists")
    try:
        waiter.wait(
            ParameterFilters=[{"Key": "Name", "Values": [name]}],
        )
    except botocore.exceptions.WaiterError:
        module.warn("Timeout waiting for parameter to exist")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe parameter while waiting for creation")


def _wait_updated(client, module, name, version):
    # Unfortunately we can't filter on the Version, as such we need something custom.
    if module.check_mode:
        return
    for x in range(1, 10):
        try:
            parameter = describe_parameter(client, module, ParameterFilters=[{"Key": "Name", "Values": [name]}])
            if parameter.get("Version", 0) > version:
                return
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to describe parameter while waiting for update")
        time.sleep(1)


def _wait_deleted(client, module, name):
    if module.check_mode:
        return
    wf = ParameterWaiterFactory(module)
    waiter = wf.get_waiter("parameter_deleted")
    try:
        waiter.wait(
            ParameterFilters=[{"Key": "Name", "Values": [name]}],
        )
    except botocore.exceptions.WaiterError:
        module.warn("Timeout waiting for parameter to exist")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe parameter while waiting for deletion")


def tag_parameter(client, module, parameter_name, tags):
    try:
        return client.add_tags_to_resource(
            aws_retry=True, ResourceType="Parameter", ResourceId=parameter_name, Tags=tags
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to add tag(s) to parameter")


def untag_parameter(client, module, parameter_name, tag_keys):
    try:
        return client.remove_tags_from_resource(
            aws_retry=True, ResourceType="Parameter", ResourceId=parameter_name, TagKeys=tag_keys
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to remove tag(s) from parameter")


def get_parameter_tags(client, module, parameter_name):
    try:
        tags = client.list_tags_for_resource(aws_retry=True, ResourceType="Parameter", ResourceId=parameter_name)[
            "TagList"
        ]
        tags_dict = boto3_tag_list_to_ansible_dict(tags)
        return tags_dict
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to retrieve parameter tags")


def update_parameter_tags(client, module, parameter_name, supplied_tags):
    changed = False
    response = {}

    if supplied_tags is None:
        return False, response

    current_tags = get_parameter_tags(client, module, parameter_name)
    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, supplied_tags, module.params.get("purge_tags"))

    if tags_to_add:
        if module.check_mode:
            return True, response
        response = tag_parameter(client, module, parameter_name, ansible_dict_to_boto3_tag_list(tags_to_add))
        changed = True
    if tags_to_remove:
        if module.check_mode:
            return True, response
        response = untag_parameter(client, module, parameter_name, tags_to_remove)
        changed = True

    return changed, response


def update_parameter(client, module, **args):
    changed = False
    response = {}
    if module.check_mode:
        return True, response

    try:
        response = client.put_parameter(aws_retry=True, **args)
        changed = True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as exc:
        module.fail_json_aws(exc, msg="setting parameter")

    return changed, response


@AWSRetry.jittered_backoff()
def describe_parameter(client, module, **args):
    paginator = client.get_paginator("describe_parameters")
    existing_parameter = paginator.paginate(**args).build_full_result()

    if not existing_parameter["Parameters"]:
        return None

    tags_dict = get_parameter_tags(client, module, module.params.get("name"))
    existing_parameter["Parameters"][0]["tags"] = tags_dict

    return existing_parameter["Parameters"][0]


def create_update_parameter(client, module):
    changed = False
    existing_parameter = None
    response = {}

    args = dict(Name=module.params.get("name"), Type=module.params.get("string_type"), Tier=module.params.get("tier"))

    if module.params.get("overwrite_value") in ("always", "changed"):
        args.update(Overwrite=True)
    else:
        args.update(Overwrite=False)

    if module.params.get("value") is not None:
        args.update(Value=module.params.get("value"))

    if module.params.get("description"):
        args.update(Description=module.params.get("description"))

    if module.params.get("string_type") == "SecureString":
        args.update(KeyId=module.params.get("key_id"))

    try:
        existing_parameter = client.get_parameter(aws_retry=True, Name=args["Name"], WithDecryption=True)
    except botocore.exceptions.ClientError:
        pass
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="fetching parameter")

    if existing_parameter:
        original_version = existing_parameter["Parameter"]["Version"]
        if "Value" not in args:
            args["Value"] = existing_parameter["Parameter"]["Value"]

        if module.params.get("overwrite_value") == "always":
            (changed, response) = update_parameter(client, module, **args)

        elif module.params.get("overwrite_value") == "changed":
            if existing_parameter["Parameter"]["Type"] != args["Type"]:
                (changed, response) = update_parameter(client, module, **args)

            elif existing_parameter["Parameter"]["Value"] != args["Value"]:
                (changed, response) = update_parameter(client, module, **args)

            elif args.get("Description"):
                # Description field not available from get_parameter function so get it from describe_parameters
                try:
                    describe_existing_parameter = describe_parameter(
                        client, module, ParameterFilters=[{"Key": "Name", "Values": [args["Name"]]}]
                    )
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="getting description value")

                if describe_existing_parameter.get("Description") != args["Description"]:
                    (changed, response) = update_parameter(client, module, **args)
        if changed:
            _wait_updated(client, module, module.params.get("name"), original_version)

        # Handle tag updates for existing parameters
        if module.params.get("overwrite_value") != "never":
            tags_changed, tags_response = update_parameter_tags(
                client, module, existing_parameter["Parameter"]["Name"], module.params.get("tags")
            )

            changed = changed or tags_changed

            if tags_response:
                response["tag_updates"] = tags_response

    else:
        # Add tags in initial creation request
        if module.params.get("tags"):
            args.update(Tags=ansible_dict_to_boto3_tag_list(module.params.get("tags")))
            # Overwrite=True conflicts with tags and is not needed for new param
            args.update(Overwrite=False)

        (changed, response) = update_parameter(client, module, **args)
        _wait_exists(client, module, module.params.get("name"))

    return changed, response


def delete_parameter(client, module):
    response = {}

    try:
        existing_parameter = client.get_parameter(aws_retry=True, Name=module.params.get("name"), WithDecryption=True)
    except is_boto3_error_code("ParameterNotFound"):
        return False, {}
    except botocore.exceptions.ClientError:
        # If we can't describe the parameter we may still be able to delete it
        existing_parameter = True
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="setting parameter")

    if not existing_parameter:
        return False, {}
    if module.check_mode:
        return True, {}

    try:
        response = client.delete_parameter(aws_retry=True, Name=module.params.get("name"))
    except is_boto3_error_code("ParameterNotFound"):
        return False, {}
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="deleting parameter")

    _wait_deleted(client, module, module.params.get("name"))

    return True, response


def setup_client(module):
    retry_decorator = AWSRetry.jittered_backoff()
    connection = module.client("ssm", retry_decorator=retry_decorator)
    return connection


def setup_module_object():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        value=dict(required=False, no_log=True),
        state=dict(default="present", choices=["present", "absent"]),
        string_type=dict(default="String", choices=["String", "StringList", "SecureString"], aliases=["type"]),
        decryption=dict(default=True, type="bool"),
        key_id=dict(default="alias/aws/ssm"),
        overwrite_value=dict(default="changed", choices=["never", "changed", "always"]),
        tier=dict(default="Standard", choices=["Standard", "Advanced", "Intelligent-Tiering"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )

    return AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )


def main():
    module = setup_module_object()
    state = module.params.get("state")
    client = setup_client(module)

    invocations = {
        "present": create_update_parameter,
        "absent": delete_parameter,
    }
    (changed, response) = invocations[state](client, module)

    result = {"response": response}

    try:
        parameter_metadata = describe_parameter(
            client, module, ParameterFilters=[{"Key": "Name", "Values": [module.params.get("name")]}]
        )
    except is_boto3_error_code("ParameterNotFound"):
        return False, {}
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="to describe parameter")
    if parameter_metadata:
        result["parameter_metadata"] = camel_dict_to_snake_dict(parameter_metadata, ignore_list=["tags"])

    module.exit_json(changed=changed, **result)


if __name__ == "__main__":
    main()

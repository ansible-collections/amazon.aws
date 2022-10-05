#!/usr/bin/python
# Copyright: (c) 2021, Daniil Kupchenko (@oukooveu)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: msk_config
short_description: Manage Amazon MSK cluster configurations
version_added: "2.0.0"
description:
    - Create, delete and modify Amazon MSK (Managed Streaming for Apache Kafka) cluster configurations.
    - Prior to release 5.0.0 this module was called C(community.aws.aws_msk_config).
      The usage did not change.
author:
    - Daniil Kupchenko (@oukooveu)
options:
    state:
        description: Create (C(present)) or delete (C(absent)) cluster configuration.
        choices: ['present', 'absent']
        default: 'present'
        type: str
    name:
        description: The name of the configuration.
        required: true
        type: str
    description:
        description: The description of the configuration.
        type: str
    config:
        description: Contents of the server.properties file.
        type: dict
        aliases: ['configuration']
    kafka_versions:
        description:
            - The versions of Apache Kafka with which you can use this MSK configuration.
            - Required when I(state=present).
        type: list
        elements: str
extends_documentation_fragment:
    - amazon.aws.aws
    - amazon.aws.ec2
    - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- community.aws.msk_config:
    name: kafka-cluster-configuration
    state: present
    kafka_versions:
      - 2.6.0
      - 2.6.1
    config:
      auto.create.topics.enable: false
      num.partitions: 1
      default.replication.factor: 3
      zookeeper.session.timeout.ms: 18000

- community.aws.msk_config:
    name: kafka-cluster-configuration
    state: absent
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.

arn:
    description: The Amazon Resource Name (ARN) of the configuration.
    type: str
    returned: I(state=present)
    sample: "arn:aws:kafka:<region>:<account>:configuration/<name>/<resource-id>"
revision:
    description: The revision number.
    type: int
    returned: I(state=present)
    sample: 1
server_properties:
    description: Contents of the server.properties file.
    type: str
    returned: I(state=present)
    sample: "default.replication.factor=3\nnum.io.threads=8\nzookeeper.session.timeout.ms=18000"
response:
    description: The response from actual API call.
    type: dict
    returned: always
    sample: {}
"""

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (
    camel_dict_to_snake_dict,
    AWSRetry,
)


def dict_to_prop(d):
    """convert dictionary to multi-line properties"""
    if len(d) == 0:
        return ""
    return "\n".join("{0}={1}".format(k, v) for k, v in d.items())


def prop_to_dict(p):
    """convert properties to dictionary"""
    if len(p) == 0:
        return {}
    r_dict = {}
    for s in p.decode().split("\n"):
        kv = s.split("=")
        r_dict[kv[0].strip()] = kv[1].strip()
    return r_dict
    # python >= 2.7 is required:
    # return {
    #     k.strip(): v.strip() for k, v in (i.split("=") for i in p.decode().split("\n"))
    # }


@AWSRetry.jittered_backoff(retries=5, delay=5)
def get_configurations_with_backoff(client):
    paginator = client.get_paginator("list_configurations")
    return paginator.paginate().build_full_result()


def find_active_config(client, module):
    """
    looking for configuration by name
    """

    name = module.params["name"]

    try:
        all_configs = get_configurations_with_backoff(client)["Configurations"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="failed to obtain kafka configurations")

    active_configs = list(
        item
        for item in all_configs
        if item["Name"] == name and item["State"] == "ACTIVE"
    )

    if active_configs:
        if len(active_configs) == 1:
            return active_configs[0]
        else:
            module.fail_json_aws(
                msg="found more than one active config with name '{0}'".format(name)
            )

    return None


def get_configuration_revision(client, module, arn, revision):
    try:
        return client.describe_configuration_revision(Arn=arn, Revision=revision, aws_retry=True)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:
        module.fail_json_aws(e, "failed to describe kafka configuration revision")


def is_configuration_changed(module, current):
    """
    compare configuration's description and properties
    python 2.7+ version:
    prop_module = {str(k): str(v) for k, v in module.params.get("config").items()}
    """
    prop_module = {}
    for k, v in module.params.get("config").items():
        prop_module[str(k)] = str(v)
    if prop_to_dict(current.get("ServerProperties", "")) == prop_module:
        if current.get("Description", "") == module.params.get("description"):
            return False
    return True


def create_config(client, module):
    """create new or update existing configuration"""

    config = find_active_config(client, module)

    # create new configuration
    if not config:

        if module.check_mode:
            return True, {}

        try:
            response = client.create_configuration(
                Name=module.params.get("name"),
                Description=module.params.get("description"),
                KafkaVersions=module.params.get("kafka_versions"),
                ServerProperties=dict_to_prop(module.params.get("config")).encode(),
                aws_retry=True
            )
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(e, "failed to create kafka configuration")

    # update existing configuration (creates new revision)
    else:
        # it's required because 'config' doesn't contain 'ServerProperties'
        response = get_configuration_revision(client, module, arn=config["Arn"], revision=config["LatestRevision"]["Revision"])

        if not is_configuration_changed(module, response):
            return False, response

        if module.check_mode:
            return True, {}

        try:
            response = client.update_configuration(
                Arn=config["Arn"],
                Description=module.params.get("description"),
                ServerProperties=dict_to_prop(module.params.get("config")).encode(),
                aws_retry=True
            )
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(e, "failed to update kafka configuration")

    arn = response["Arn"]
    revision = response["LatestRevision"]["Revision"]

    result = get_configuration_revision(client, module, arn=arn, revision=revision)

    return True, result


def delete_config(client, module):
    """delete configuration"""

    config = find_active_config(client, module)

    if module.check_mode:
        if config:
            return True, config
        else:
            return False, {}

    if config:
        try:
            response = client.delete_configuration(Arn=config["Arn"], aws_retry=True)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(e, "failed to delete the kafka configuration")
        return True, response

    return False, {}


def main():

    module_args = dict(
        name=dict(type="str", required=True),
        description=dict(type="str", default=""),
        state=dict(choices=["present", "absent"], default="present"),
        config=dict(type="dict", aliases=["configuration"], default={}),
        kafka_versions=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=module_args, supports_check_mode=True)

    client = module.client("kafka", retry_decorator=AWSRetry.jittered_backoff())

    if module.params["state"] == "present":
        changed, response = create_config(client, module)

    elif module.params["state"] == "absent":
        changed, response = delete_config(client, module)

    # return some useless staff in check mode if configuration doesn't exists
    # can be useful when these options are referenced by other modules during check mode run
    if module.check_mode and not response.get("Arn"):
        arn = "arn:aws:kafka:region:account:configuration/name/id"
        revision = 1
        server_properties = ""
    else:
        arn = response.get("Arn")
        revision = response.get("Revision")
        server_properties = response.get("ServerProperties", "")

    module.exit_json(
        changed=changed,
        arn=arn,
        revision=revision,
        server_properties=server_properties,
        response=camel_dict_to_snake_dict(response),
    )


if __name__ == "__main__":
    main()

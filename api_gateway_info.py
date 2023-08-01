#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: api_gateway_info
version_added: 6.1.0
short_description: Gather information about ec2 instances in AWS
description:
  - Gather information about ec2 instances in AWS
options:
  ids:
    description:
      - The list of the string identifiers of the associated RestApis.
    type: list
    elements: str
author:
  - Aubin Bikouo (@abikouo)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
---
# List all API gateway
- name: List all for a specific function
  community.aws.api_gateway_info:

# Get information for a specific API gateway
- name: List all for a specific function
  community.aws.api_gateway_info:
    ids:
    - 012345678a
    - abcdefghij
"""

RETURN = r"""
---
rest_apis:
    description: A list of API gateway.
    returned: always
    type: complex
    contains:
        name:
            description: The name of the API.
            returned: success
            type: str
            sample: 'ansible-tmp-api'
        id:
            description: The identifier of the API.
            returned: success
            type: str
            sample: 'abcdefgh'
        api_key_source:
            description: The source of the API key for metering requests according to a usage plan.
            returned: success
            type: str
            sample: 'HEADER'
        created_date:
            description: The timestamp when the API was created.
            returned: success
            type: str
            sample: "2020-01-01T11:37:59+00:00"
        description:
            description: The description of the API.
            returned: success
            type: str
            sample: "Automatic deployment by Ansible."
        disable_execute_api_endpoint:
            description: Specifies whether clients can invoke your API by using the default execute-api endpoint.
            returned: success
            type: bool
            sample: False
        endpoint_configuration:
            description: The endpoint configuration of this RestApi showing the endpoint types of the API.
            returned: success
            type: dict
            sample: {"types": ["REGIONAL"]}
        tags:
            description: The collection of tags.
            returned: success
            type: dict
            sample: {"key": "value"}
"""


try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.jittered_backoff()
def _list_rest_apis(connection, **params):
    paginator = connection.get_paginator("get_rest_apis")
    return paginator.paginate(**params).build_full_result().get("items", [])


@AWSRetry.jittered_backoff()
def _describe_rest_api(connection, module, rest_api_id):
    try:
        response = connection.get_rest_api(restApiId=rest_api_id)
        response.pop("ResponseMetadata")
    except is_boto3_error_code("ResourceNotFoundException"):
        response = {}
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get Rest API '{0}'.".format(rest_api_id))
    return response


def main():
    argument_spec = dict(
        ids=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        connection = module.client("apigateway")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    ids = module.params.get("ids")
    if ids:
        rest_apis = []
        for rest_api_id in ids:
            result = _describe_rest_api(connection, module, rest_api_id)
            if result:
                rest_apis.append(result)
    else:
        rest_apis = _list_rest_apis(connection)

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_rest_apis = [camel_dict_to_snake_dict(item) for item in rest_apis]
    module.exit_json(changed=False, rest_apis=snaked_rest_apis)


if __name__ == "__main__":
    main()

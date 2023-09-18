#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: config_aggregation_authorization
version_added: 1.0.0
short_description: Manage cross-account AWS Config authorizations
description:
  - Module manages AWS Config aggregation authorizations.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_config_aggregation_authorization).
    The usage did not change.
author:
  - "Aaron Smith (@slapula)"
options:
  state:
    description:
      - Whether the Config rule should be present or absent.
    default: present
    choices: ['present', 'absent']
    type: str
  authorized_account_id:
    description:
      - The 12-digit account ID of the account authorized to aggregate data.
    type: str
    required: true
  authorized_aws_region:
    description:
      - The region authorized to collect aggregated data.
    type: str
    required: true
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Get current account ID
  community.aws.aws_caller_info:
  register: whoami
- community.aws.config_aggregation_authorization:
    state: present
    authorized_account_id: '{{ whoami.account }}'
    authorized_aws_region: us-east-1
"""

RETURN = r"""#"""

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def resource_exists(client, module, params):
    try:
        current_authorizations = client.describe_aggregation_authorizations()["AggregationAuthorizations"]
        authorization_exists = next(
            (item for item in current_authorizations if item["AuthorizedAccountId"] == params["AuthorizedAccountId"]),
            None,
        )
        if authorization_exists:
            return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        return False


def create_resource(client, module, params, result):
    try:
        response = client.put_aggregation_authorization(
            AuthorizedAccountId=params["AuthorizedAccountId"],
            AuthorizedAwsRegion=params["AuthorizedAwsRegion"],
        )
        result["changed"] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create AWS Aggregation authorization")


def update_resource(client, module, params, result):
    current_authorizations = client.describe_aggregation_authorizations()["AggregationAuthorizations"]
    current_params = next(
        (item for item in current_authorizations if item["AuthorizedAccountId"] == params["AuthorizedAccountId"]),
        None,
    )

    del current_params["AggregationAuthorizationArn"]
    del current_params["CreationTime"]

    if params != current_params:
        try:
            response = client.put_aggregation_authorization(
                AuthorizedAccountId=params["AuthorizedAccountId"],
                AuthorizedAwsRegion=params["AuthorizedAwsRegion"],
            )
            result["changed"] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Aggregation authorization")


def delete_resource(client, module, params, result):
    try:
        response = client.delete_aggregation_authorization(
            AuthorizedAccountId=params["AuthorizedAccountId"],
            AuthorizedAwsRegion=params["AuthorizedAwsRegion"],
        )
        result["changed"] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete AWS Aggregation authorization")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            "state": dict(type="str", choices=["present", "absent"], default="present"),
            "authorized_account_id": dict(type="str", required=True),
            "authorized_aws_region": dict(type="str", required=True),
        },
        supports_check_mode=False,
    )

    result = {"changed": False}

    params = {
        "AuthorizedAccountId": module.params.get("authorized_account_id"),
        "AuthorizedAwsRegion": module.params.get("authorized_aws_region"),
    }

    client = module.client("config", retry_decorator=AWSRetry.jittered_backoff())
    resource_status = resource_exists(client, module, params)

    if module.params.get("state") == "present":
        if not resource_status:
            create_resource(client, module, params, result)
        else:
            update_resource(client, module, params, result)

    if module.params.get("state") == "absent":
        if resource_status:
            delete_resource(client, module, params, result)

    module.exit_json(changed=result["changed"])


if __name__ == "__main__":
    main()

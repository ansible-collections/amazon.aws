#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: glue_crawler
version_added: 4.1.0
short_description: Manage an AWS Glue crawler
description:
  - Manage an AWS Glue crawler. See U(https://aws.amazon.com/glue/) for details.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_glue_crawler).
    The usage did not change.
author:
  - 'Ivan Chekaldin (@ichekaldin)'
options:
  database_name:
    description:
      - The name of the database where results are written.
    type: str
  description:
    description:
      - Description of the crawler being defined.
    type: str
  name:
    description:
      - The name you assign to this crawler definition. It must be unique in your account.
    required: true
    type: str
  recrawl_policy:
    description:
      - A policy that specifies whether to crawl the entire dataset again, or to crawl only folders that were added since the last crawler run.
    suboptions:
      recrawl_behavior:
        description:
          - Specifies whether to crawl the entire dataset again or to crawl only folders that were added since the last crawler run.
          - Supported options are C(CRAWL_EVERYTHING) and C(CRAWL_NEW_FOLDERS_ONLY).
        type: str
    type: dict
  role:
    description:
      - The name or ARN of the IAM role associated with this crawler.
      - Required when I(state=present).
    type: str
  schema_change_policy:
    description:
      - The policy for the crawler's update and deletion behavior.
    suboptions:
      delete_behavior:
        description:
          - Defines the deletion behavior when the crawler finds a deleted object.
          - Supported options are C(LOG), C(DELETE_FROM_DATABASE), and C(DEPRECATE_IN_DATABASE).
        type: str
      update_behavior:
        description:
          - Defines the update behavior when the crawler finds a changed schema..
          - Supported options are C(LOG) and C(UPDATE_IN_DATABASE).
        type: str
    type: dict
  state:
    description:
      - Create or delete the AWS Glue crawler.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  table_prefix:
    description:
      - The table prefix used for catalog tables that are created.
    type: str
  targets:
    description:
      - A list of targets to crawl. See example below.
      - Required when I(state=present).
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an AWS Glue crawler
- community.aws.glue_crawler:
    name: my-glue-crawler
    database_name: my_database
    role: my-iam-role
    schema_change_policy:
      delete_behavior: DELETE_FROM_DATABASE
      update_behavior: UPDATE_IN_DATABASE
    recrawl_policy:
      recrawl_ehavior: CRAWL_EVERYTHING
    targets:
      S3Targets:
        - Path: "s3://my-bucket/prefix/folder/"
          ConnectionName: my-connection
          Exclusions:
            - "**.json"
            - "**.yml"
    state: present

# Delete an AWS Glue crawler
- community.aws.glue_crawler:
    name: my-glue-crawler
    state: absent
"""

RETURN = r"""
creation_time:
    description: The time and date that this crawler definition was created.
    returned: when state is present
    type: str
    sample: '2021-04-01T05:19:58.326000+00:00'
database_name:
    description: The name of the database where results are written.
    returned: when state is present
    type: str
    sample: my_table
description:
    description: Description of the crawler.
    returned: when state is present
    type: str
    sample: My crawler
last_updated:
    description: The time and date that this crawler definition was last updated.
    returned: when state is present
    type: str
    sample: '2021-04-01T05:19:58.326000+00:00'
name:
    description: The name of the AWS Glue crawler.
    returned: always
    type: str
    sample: my-glue-crawler
recrawl_policy:
    description: A policy that specifies whether to crawl the entire dataset again, or to crawl only folders that were added since the last crawler run.
    returned: when state is present
    type: complex
    contains:
        RecrawlBehavior:
            description: Whether to crawl the entire dataset again or to crawl only folders that were added since the last crawler run.
            returned: when state is present
            type: str
            sample: CRAWL_EVERYTHING
role:
    description: The name or ARN of the IAM role associated with this crawler.
    returned: when state is present
    type: str
    sample: my-iam-role
schema_change_policy:
    description: The policy for the crawler's update and deletion behavior.
    returned: when state is present
    type: complex
    contains:
        DeleteBehavior:
            description: The deletion behavior when the crawler finds a deleted object.
            returned: when state is present
            type: str
            sample: DELETE_FROM_DATABASE
        UpdateBehavior:
            description: The update behavior when the crawler finds a changed schema.
            returned: when state is present
            type: str
            sample: UPDATE_IN_DATABASE

table_prefix:
    description: The table prefix used for catalog tables that are created.
    returned: when state is present
    type: str
    sample: my_prefix
targets:
    description: A list of targets to crawl.
    returned: when state is present
    type: complex
    contains:
        S3Targets:
            description: List of S3 targets.
            returned: when state is present
            type: list
        JdbcTargets:
            description: List of JDBC targets.
            returned: when state is present
            type: list
        MongoDBTargets:
            description: List of Mongo DB targets.
            returned: when state is present
            type: list
        DynamoDBTargets:
            description: List of DynamoDB targets.
            returned: when state is present
            type: list
        CatalogTargets:
            description: List of catalog targets.
            returned: when state is present
            type: list
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_aws_account_info
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def _get_glue_crawler(connection, module, glue_crawler_name):
    """
    Get an AWS Glue crawler based on name. If not found, return None.
    """
    try:
        return connection.get_crawler(aws_retry=True, Name=glue_crawler_name)["Crawler"]
    except is_boto3_error_code("EntityNotFoundException"):
        return None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


def _trim_targets(targets):
    return [_trim_target(t) for t in targets]


def _trim_target(target):
    """
    Some target types have optional parameters which AWS will fill in and return
    To compare the desired targets and the current targets we need to ignore the defaults
    """
    if not target:
        return None
    retval = target.copy()
    if not retval.get("Exclusions", None):
        retval.pop("Exclusions", None)
    return retval


def _compare_glue_crawler_params(user_params, current_params):
    """
    Compare Glue crawler params. If there is a difference, return True immediately else return False
    """
    if "DatabaseName" in user_params and user_params["DatabaseName"] != current_params["DatabaseName"]:
        return True
    if "Description" in user_params and user_params["Description"] != current_params["Description"]:
        return True
    if "RecrawlPolicy" in user_params and user_params["RecrawlPolicy"] != current_params["RecrawlPolicy"]:
        return True
    if "Role" in user_params and user_params["Role"] != current_params["Role"]:
        return True
    if (
        "SchemaChangePolicy" in user_params
        and user_params["SchemaChangePolicy"] != current_params["SchemaChangePolicy"]
    ):
        return True
    if "TablePrefix" in user_params and user_params["TablePrefix"] != current_params["TablePrefix"]:
        return True
    if "Targets" in user_params:
        if "S3Targets" in user_params["Targets"]:
            if _trim_targets(user_params["Targets"]["S3Targets"]) != _trim_targets(
                current_params["Targets"]["S3Targets"]
            ):
                return True
        if (
            "JdbcTargets" in user_params["Targets"]
            and user_params["Targets"]["JdbcTargets"] != current_params["Targets"]["JdbcTargets"]
        ):
            if _trim_targets(user_params["Targets"]["JdbcTargets"]) != _trim_targets(
                current_params["Targets"]["JdbcTargets"]
            ):
                return True
        if (
            "MongoDBTargets" in user_params["Targets"]
            and user_params["Targets"]["MongoDBTargets"] != current_params["Targets"]["MongoDBTargets"]
        ):
            return True
        if (
            "DynamoDBTargets" in user_params["Targets"]
            and user_params["Targets"]["DynamoDBTargets"] != current_params["Targets"]["DynamoDBTargets"]
        ):
            return True
        if (
            "CatalogTargets" in user_params["Targets"]
            and user_params["Targets"]["CatalogTargets"] != current_params["Targets"]["CatalogTargets"]
        ):
            return True

    return False


def ensure_tags(connection, module, glue_crawler):
    changed = False

    if module.params.get("tags") is None:
        return False

    account_id, partition = get_aws_account_info(module)
    arn = f"arn:{partition}:glue:{module.region}:{account_id}:crawler/{module.params.get('name')}"

    try:
        existing_tags = connection.get_tags(aws_retry=True, ResourceArn=arn).get("Tags", {})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if module.check_mode:
            existing_tags = {}
        else:
            module.fail_json_aws(e, msg=f"Unable to get tags for Glue crawler {module.params.get('name')}")

    tags_to_add, tags_to_remove = compare_aws_tags(
        existing_tags, module.params.get("tags"), module.params.get("purge_tags")
    )

    if tags_to_remove:
        changed = True
        if not module.check_mode:
            try:
                connection.untag_resource(aws_retry=True, ResourceArn=arn, TagsToRemove=tags_to_remove)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Glue crawler {module.params.get('name')}")

    if tags_to_add:
        changed = True
        if not module.check_mode:
            try:
                connection.tag_resource(aws_retry=True, ResourceArn=arn, TagsToAdd=tags_to_add)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Glue crawler {module.params.get('name')}")

    return changed


def create_or_update_glue_crawler(connection, module, glue_crawler):
    """
    Create or update an AWS Glue crawler
    """

    changed = False
    params = dict()
    params["Name"] = module.params.get("name")
    params["Role"] = module.params.get("role")
    params["Targets"] = module.params.get("targets")
    if module.params.get("database_name") is not None:
        params["DatabaseName"] = module.params.get("database_name")
    if module.params.get("description") is not None:
        params["Description"] = module.params.get("description")
    if module.params.get("recrawl_policy") is not None:
        params["RecrawlPolicy"] = snake_dict_to_camel_dict(module.params.get("recrawl_policy"), capitalize_first=True)
    if module.params.get("role") is not None:
        params["Role"] = module.params.get("role")
    if module.params.get("schema_change_policy") is not None:
        params["SchemaChangePolicy"] = snake_dict_to_camel_dict(
            module.params.get("schema_change_policy"), capitalize_first=True
        )
    if module.params.get("table_prefix") is not None:
        params["TablePrefix"] = module.params.get("table_prefix")
    if module.params.get("targets") is not None:
        params["Targets"] = module.params.get("targets")

    if glue_crawler:
        if _compare_glue_crawler_params(params, glue_crawler):
            try:
                if not module.check_mode:
                    connection.update_crawler(aws_retry=True, **params)
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e)
    else:
        try:
            if not module.check_mode:
                connection.create_crawler(aws_retry=True, **params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e)

    glue_crawler = _get_glue_crawler(connection, module, params["Name"])

    changed |= ensure_tags(connection, module, glue_crawler)

    module.exit_json(
        changed=changed,
        **camel_dict_to_snake_dict(glue_crawler or {}, ignore_list=["SchemaChangePolicy", "RecrawlPolicy", "Targets"]),
    )


def delete_glue_crawler(connection, module, glue_crawler):
    """
    Delete an AWS Glue crawler
    """
    changed = False

    if glue_crawler:
        try:
            if not module.check_mode:
                connection.delete_crawler(aws_retry=True, Name=glue_crawler["Name"])
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed)


def main():
    argument_spec = dict(
        database_name=dict(type="str"),
        description=dict(type="str"),
        name=dict(required=True, type="str"),
        purge_tags=dict(type="bool", default=True),
        recrawl_policy=dict(type="dict", options=dict(recrawl_behavior=dict(type="str"))),
        role=dict(type="str"),
        schema_change_policy=dict(
            type="dict", options=dict(delete_behavior=dict(type="str"), update_behavior=dict(type="str"))
        ),
        state=dict(required=True, choices=["present", "absent"], type="str"),
        table_prefix=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        targets=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[("state", "present", ["role", "targets"])],
        supports_check_mode=True,
    )

    connection = module.client("glue", retry_decorator=AWSRetry.jittered_backoff(retries=10))

    state = module.params.get("state")

    glue_crawler = _get_glue_crawler(connection, module, module.params.get("name"))

    if state == "present":
        create_or_update_glue_crawler(connection, module, glue_crawler)
    else:
        delete_glue_crawler(connection, module, glue_crawler)


if __name__ == "__main__":
    main()

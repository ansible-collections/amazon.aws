# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO3

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def get_backup_resource_tags(module, backup_client):
    resource = module.params.get("resource")
    try:
        response = backup_client.list_tags(ResourceArn=resource)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed to list tags on the resource {resource}")

    return response["Tags"]


def _list_backup_plans(client, backup_plan_name):
    first_iteration = False
    next_token = None

    # We can not use the paginator at the moment because if was introduced after boto3 version 1.22
    # paginator = client.get_paginator("list_backup_plans")
    # result = paginator.paginate(**params).build_full_result()["BackupPlansList"]

    response = client.list_backup_plans()
    next_token = response.get("NextToken", None)

    if next_token is None:
        entries = response["BackupPlansList"]
        for backup_plan in entries:
            if backup_plan_name == backup_plan["BackupPlanName"]:
                return backup_plan["BackupPlanId"]

    while next_token is not None:
        if first_iteration != False:
            response = client.list_backup_plans(NextToken=next_token)
        first_iteration = True
        entries = response["BackupPlansList"]
        for backup_plan in entries:
            if backup_plan_name == backup_plan["BackupPlanName"]:
                return backup_plan["BackupPlanId"]
        try:
            next_token = response.get('NextToken')
        except:
            next_token = None


def get_plan_details(module, client, backup_plan_name: str):
    backup_plan_id = _list_backup_plans(client, backup_plan_name)

    if not backup_plan_id:
        return []

    try:
        result = client.get_backup_plan(BackupPlanId=backup_plan_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed to describe plan {backup_plan_id}")

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_backup_plan = []

    try:
       module.params["resource"] = result.get("BackupPlanArn", None)
       tag_dict = get_backup_resource_tags(module, client)
       result.update({"tags": tag_dict})
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
     module.fail_json_aws(e, msg=f"Failed to get the backup plan tags")

    snaked_backup_plan.append(camel_dict_to_snake_dict(result))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for v in snaked_backup_plan:
        if "tags_list" in v:
            v["tags"] = boto3_tag_list_to_ansible_dict(v["tags_list"], "key", "value")
            del v["tags_list"]
        if "response_metadata" in v:
            del v["response_metadata"]
        v["backup_plan_name"] = v["backup_plan"]["backup_plan_name"]

    return snaked_backup_plan


def _list_backup_selections(client, backup_plan_id, backup_selection_name):
    first_iteration = False
    next_token = None

    # We can not use the paginator at the moment because if was introduced after boto3 version 1.22
    # paginator = client.get_paginator("list_backup_selections")
    # result = paginator.paginate(**params).build_full_result()["BackupSelectionsList"]

    response = client.list_backup_selections(BackupPlanId=backup_plan_id)
    next_token = response.get("NextToken", None)

    if next_token is None:
        entries = response["BackupSelectionsList"]
        for backup_selection in entries:
            if backup_selection_name == backup_selection["SelectionName"]:
                return backup_selection["SelectionId"]

    while next_token is not None:
        if first_iteration != False:
            response = client.list_backup_selections(BackupPlanId=backup_plan_id, NextToken=next_token)
        first_iteration = True
        entries = response["BackupSelectionsList"]
        for backup_selection in entries:
            if backup_selection_name == backup_selection["BackupPlanName"]:
                return backup_selection["SelectionId"]
        try:
            next_token = response.get('NextToken')
        except:
            next_token = None


def get_selection_details(module, client, backup_plan_name, backup_selection_name: str):
    backup_plan = get_plan_details(module, client, backup_plan_name)

    if not backup_plan:
        module.fail_json(e, msg=f"The backup plan {backup_plan_name} does not exist. Please create one first.")

    backup_plan_id = backup_plan[0]["backup_plan_id"]
    backup_selection_id = _list_backup_selections(client, backup_plan_id, backup_selection_name)

    if not backup_selection_id:
        return []

    try:
        result = client.get_backup_selection(BackupPlanId=backup_plan_id, SelectionId=backup_selection_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed to describe plan {backup_selection_id}")

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_backup_selection = []

    # try:
    #    module.params["resource"] = result.get("BackupPlanArn", None)
    #    tag_dict = get_backup_resource_tags(module, client)
    #    result.update({"tags": tag_dict})
    # except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    #  module.fail_json_aws(e, msg=f"Failed to get the backup plan tags")

    snaked_backup_selection.append(camel_dict_to_snake_dict(result))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for v in snaked_backup_selection:
        if "tags_list" in v:
            v["tags"] = boto3_tag_list_to_ansible_dict(v["tags_list"], "key", "value")
            del v["tags_list"]
        if "response_metadata" in v:
            del v["response_metadata"]
        if "backup_selection" in v:
            for backup_selection_key in v['backup_selection']:
                v[backup_selection_key] = v['backup_selection'][backup_selection_key]
        del v["backup_selection"]

    return snaked_backup_selection

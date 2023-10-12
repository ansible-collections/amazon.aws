# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO3

from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


def get_backup_resource_tags(module, backup_client, resource):
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
        if first_iteration:
            response = client.list_backup_plans(NextToken=next_token)
        first_iteration = True
        entries = response["BackupPlansList"]
        for backup_plan in entries:
            if backup_plan_name == backup_plan["BackupPlanName"]:
                return backup_plan["BackupPlanId"]
        next_token = response.get("NextToken")


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
        resource = result.get("BackupPlanArn", None)
        tag_dict = get_backup_resource_tags(module, client, resource)
        result.update({"tags": tag_dict})
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to get the backup plan tags")

    snaked_backup_plan.append(camel_dict_to_snake_dict(result, ignore_list="tags"))

    # Remove AWS API response and add top-level plan name
    for v in snaked_backup_plan:
        if "response_metadata" in v:
            del v["response_metadata"]
        v["backup_plan_name"] = v["backup_plan"]["backup_plan_name"]

    return snaked_backup_plan


def _list_backup_selections(client, module, plan_id):
    first_iteration = False
    next_token = None
    selections = []

    # We can not use the paginator at the moment because if was introduced after boto3 version 1.22
    # paginator = client.get_paginator("list_backup_selections")
    # result = paginator.paginate(**params).build_full_result()["BackupSelectionsList"]

    try:
        response = client.list_backup_selections(BackupPlanId=plan_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list AWS backup selections")

    next_token = response.get("NextToken", None)

    if next_token is None:
        return response["BackupSelectionsList"]

    while next_token:
        if first_iteration:
            try:
                response = client.list_backup_selections(BackupPlanId=plan_id, NextToken=next_token)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to list AWS backup selections")
        first_iteration = True
        selections.append(response["BackupSelectionsList"])
        next_token = response.get("NextToken")


def _get_backup_selection(client, module, plan_id, selection_id):
    try:
        result = client.get_backup_selection(BackupPlanId=plan_id, SelectionId=selection_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed to describe selection {selection_id}")
    return result or []


def get_selection_details(module, client, plan_name: str, selection_name: Union[str, list]):
    result = []

    plan = get_plan_details(module, client, plan_name)

    if not plan:
        module.fail_json(msg=f"The backup plan {plan_name} does not exist. Please create one first.")

    plan_id = plan[0]["backup_plan_id"]

    selection_list = _list_backup_selections(client, module, plan_id)

    if selection_name:
        for selection in selection_list:
            if isinstance(selection_name, list):
                for name in selection_name:
                    if selection["SelectionName"] == name:
                        selection_id = selection["SelectionId"]
                        selection_info = _get_backup_selection(client, module, plan_id, selection_id)
                        result.append(selection_info)
            if isinstance(selection_name, str):
                if selection["SelectionName"] == selection_name:
                    selection_id = selection["SelectionId"]
                    result.append(_get_backup_selection(client, module, plan_id, selection_id))
                    break
    else:
        for selection in selection_list:
            selection_id = selection["SelectionId"]
            result.append(_get_backup_selection(client, module, plan_id, selection_id))

    for v in result:
        if "ResponseMetadata" in v:
            del v["ResponseMetadata"]
        if "BackupSelection" in v:
            for backup_selection_key in v["BackupSelection"]:
                v[backup_selection_key] = v["BackupSelection"][backup_selection_key]
        del v["BackupSelection"]

    return result

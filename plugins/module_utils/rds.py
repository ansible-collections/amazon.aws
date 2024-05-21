# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections import namedtuple
from time import sleep
from typing import Any
from typing import Dict
from typing import List

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
    from botocore.exceptions import WaiterError
except ImportError:
    pass

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from .botocore import is_boto3_error_code
from .core import AnsibleAWSModule
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict
from .tagging import compare_aws_tags
from .waiters import get_waiter

Boto3ClientMethod = namedtuple(
    "Boto3ClientMethod", ["name", "waiter", "operation_description", "resource", "retry_codes"]
)
# Whitelist boto3 client methods for cluster and instance resources
cluster_method_names = [
    "create_db_cluster",
    "restore_db_cluster_from_snapshot",
    "restore_db_cluster_from_s3",
    "restore_db_cluster_to_point_in_time",
    "modify_db_cluster",
    "delete_db_cluster",
    "add_tags_to_resource",
    "remove_tags_from_resource",
    "list_tags_for_resource",
    "promote_read_replica_db_cluster",
    "stop_db_cluster",
    "start_db_cluster",
]
instance_method_names = [
    "create_db_instance",
    "restore_db_instance_to_point_in_time",
    "restore_db_instance_from_s3",
    "restore_db_instance_from_db_snapshot",
    "create_db_instance_read_replica",
    "modify_db_instance",
    "delete_db_instance",
    "add_tags_to_resource",
    "remove_tags_from_resource",
    "list_tags_for_resource",
    "promote_read_replica",
    "stop_db_instance",
    "start_db_instance",
    "reboot_db_instance",
    "add_role_to_db_instance",
    "remove_role_from_db_instance",
]

cluster_snapshot_method_names = [
    "create_db_cluster_snapshot",
    "delete_db_cluster_snapshot",
    "add_tags_to_resource",
    "remove_tags_from_resource",
    "list_tags_for_resource",
    "copy_db_cluster_snapshot",
]

instance_snapshot_method_names = [
    "create_db_snapshot",
    "delete_db_snapshot",
    "add_tags_to_resource",
    "remove_tags_from_resource",
    "copy_db_snapshot",
    "list_tags_for_resource",
]


def get_rds_method_attribute(method_name, module):
    """
    Returns rds attributes of the specified method.

        Parameters:
            method_name (str): RDS method to call
            module: AnsibleAWSModule

        Returns:
            Boto3ClientMethod (dict):
                name (str): Name of method
                waiter (str): Name of waiter associated with given method
                operation_description (str): Description of method
                resource (str): Type of resource this method applies to
                                One of ['instance', 'cluster', 'instance_snapshot', 'cluster_snapshot']
                retry_codes (list): List of extra error codes to retry on

        Raises:
            NotImplementedError if wait is True but no waiter can be found for specified method
    """
    waiter = ""
    readable_op = method_name.replace("_", " ").replace("db", "DB")
    resource = ""
    retry_codes = []
    if method_name in cluster_method_names and "new_db_cluster_identifier" in module.params:
        resource = "cluster"
        if method_name == "delete_db_cluster":
            waiter = "cluster_deleted"
        else:
            waiter = "cluster_available"
        # Handle retry codes
        if method_name == "restore_db_cluster_from_snapshot":
            retry_codes = ["InvalidDBClusterSnapshotState"]
        else:
            retry_codes = ["InvalidDBClusterState"]
    elif method_name in instance_method_names and "new_db_instance_identifier" in module.params:
        resource = "instance"
        if method_name == "delete_db_instance":
            waiter = "db_instance_deleted"
        elif method_name == "stop_db_instance":
            waiter = "db_instance_stopped"
        elif method_name == "add_role_to_db_instance":
            waiter = "role_associated"
        elif method_name == "remove_role_from_db_instance":
            waiter = "role_disassociated"
        elif method_name == "promote_read_replica":
            waiter = "read_replica_promoted"
        elif method_name == "db_cluster_promoting":
            waiter = "db_cluster_promoting"
        else:
            waiter = "db_instance_available"
        # Handle retry codes
        if method_name == "restore_db_instance_from_db_snapshot":
            retry_codes = ["InvalidDBSnapshotState"]
        else:
            retry_codes = ["InvalidDBInstanceState", "InvalidDBSecurityGroupState"]
    elif method_name in cluster_snapshot_method_names and "db_cluster_snapshot_identifier" in module.params:
        resource = "cluster_snapshot"
        if method_name == "delete_db_cluster_snapshot":
            waiter = "db_cluster_snapshot_deleted"
            retry_codes = ["InvalidDBClusterSnapshotState"]
        elif method_name == "create_db_cluster_snapshot":
            waiter = "db_cluster_snapshot_available"
            retry_codes = ["InvalidDBClusterState"]
        else:
            # Tagging
            waiter = "db_cluster_snapshot_available"
            retry_codes = ["InvalidDBClusterSnapshotState"]
    elif method_name in instance_snapshot_method_names and "db_snapshot_identifier" in module.params:
        resource = "instance_snapshot"
        if method_name == "delete_db_snapshot":
            waiter = "db_snapshot_deleted"
            retry_codes = ["InvalidDBSnapshotState"]
        elif method_name == "create_db_snapshot":
            waiter = "db_snapshot_available"
            retry_codes = ["InvalidDBInstanceState"]
        else:
            # Tagging
            waiter = "db_snapshot_available"
            retry_codes = ["InvalidDBSnapshotState"]
    else:
        if module.params.get("wait"):
            raise NotImplementedError(
                f"method {method_name} hasn't been added to the list of accepted methods to use a waiter in module_utils/rds.py",
            )

    return Boto3ClientMethod(
        name=method_name, waiter=waiter, operation_description=readable_op, resource=resource, retry_codes=retry_codes
    )


def get_final_identifier(method_name, module):
    updated_identifier = None
    apply_immediately = module.params.get("apply_immediately")
    resource = get_rds_method_attribute(method_name, module).resource
    if resource == "cluster":
        identifier = module.params["db_cluster_identifier"]
        updated_identifier = module.params["new_db_cluster_identifier"]
    elif resource == "instance":
        identifier = module.params["db_instance_identifier"]
        updated_identifier = module.params["new_db_instance_identifier"]
    elif resource == "instance_snapshot":
        identifier = module.params["db_snapshot_identifier"]
    elif resource == "cluster_snapshot":
        identifier = module.params["db_cluster_snapshot_identifier"]
    else:
        raise NotImplementedError(
            f"method {method_name} hasn't been added to the list of accepted methods in module_utils/rds.py",
        )
    if not module.check_mode and updated_identifier and apply_immediately:
        identifier = updated_identifier
    return identifier


def handle_errors(module, exception, method_name, parameters):
    if not isinstance(exception, ClientError):
        module.fail_json_aws(exception, msg=f"Unexpected failure for method {method_name} with parameters {parameters}")

    changed = True
    error_code = exception.response["Error"]["Code"]
    if method_name in ("modify_db_instance", "modify_db_cluster") and error_code == "InvalidParameterCombination":
        if "No modifications were requested" in to_text(exception):
            changed = False
        elif "ModifyDbCluster API" in to_text(exception):
            module.fail_json_aws(
                exception,
                msg="It appears you are trying to modify attributes that are managed at the cluster level. Please see rds_cluster",
            )
        else:
            module.fail_json_aws(
                exception,
                msg=f"Unable to {get_rds_method_attribute(method_name, module).operation_description}",
            )
    elif method_name == "promote_read_replica" and error_code == "InvalidDBInstanceState":
        if "DB Instance is not a read replica" in to_text(exception):
            changed = False
        else:
            module.fail_json_aws(
                exception,
                msg=f"Unable to {get_rds_method_attribute(method_name, module).operation_description}",
            )
    elif method_name == "promote_read_replica_db_cluster" and error_code == "InvalidDBClusterStateFault":
        if "DB Cluster that is not a read replica" in to_text(exception):
            changed = False
        else:
            module.fail_json_aws(
                exception,
                msg=f"Unable to {get_rds_method_attribute(method_name, module).operation_description}",
            )
    elif method_name == "create_db_cluster" and error_code == "InvalidParameterValue":
        accepted_engines = ["aurora", "aurora-mysql", "aurora-postgresql", "mysql", "postgres"]
        if parameters.get("Engine") not in accepted_engines:
            module.fail_json_aws(
                exception, msg=f"DB engine {parameters.get('Engine')} should be one of {accepted_engines}"
            )
        else:
            module.fail_json_aws(
                exception,
                msg=f"Unable to {get_rds_method_attribute(method_name, module).operation_description}",
            )
    else:
        module.fail_json_aws(
            exception,
            msg=f"Unable to {get_rds_method_attribute(method_name, module).operation_description}",
        )

    return changed


def call_method(client, module, method_name, parameters):
    result = {}
    changed = True
    if not module.check_mode:
        wait = module.params.get("wait")
        retry_codes = get_rds_method_attribute(method_name, module).retry_codes
        method = getattr(client, method_name)
        try:
            result = AWSRetry.jittered_backoff(catch_extra_error_codes=retry_codes)(method)(**parameters)
        except (BotoCoreError, ClientError) as e:
            changed = handle_errors(module, e, method_name, parameters)

        if wait and changed:
            identifier = get_final_identifier(method_name, module)
            wait_for_status(client, module, identifier, method_name)
    return result, changed


def wait_for_instance_status(client, module, db_instance_id, waiter_name):
    def wait(client, db_instance_id, waiter_name):
        try:
            waiter = client.get_waiter(waiter_name)
        except ValueError:
            # using a waiter in module_utils/waiters.py
            waiter = get_waiter(client, waiter_name)
        waiter.wait(WaiterConfig={"Delay": 60, "MaxAttempts": 60}, DBInstanceIdentifier=db_instance_id)

    waiter_expected_status = {
        "db_instance_deleted": "deleted",
        "db_instance_stopped": "stopped",
    }
    expected_status = waiter_expected_status.get(waiter_name, "available")
    for _wait_attempts in range(0, 10):
        try:
            wait(client, db_instance_id, waiter_name)
            break
        except WaiterError as e:
            # Instance may be renamed and AWSRetry doesn't handle WaiterError
            if e.last_response.get("Error", {}).get("Code") == "DBInstanceNotFound":
                sleep(10)
                continue
            module.fail_json_aws(e, msg=f"Error while waiting for DB instance {db_instance_id} to be {expected_status}")
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(
                e, msg=f"Unexpected error while waiting for DB instance {db_instance_id} to be {expected_status}"
            )


def wait_for_cluster_status(client, module, db_cluster_id, waiter_name):
    try:
        get_waiter(client, waiter_name).wait(DBClusterIdentifier=db_cluster_id)
    except WaiterError as e:
        if waiter_name == "cluster_deleted":
            msg = f"Failed to wait for DB cluster {db_cluster_id} to be deleted"
        else:
            msg = f"Failed to wait for DB cluster {db_cluster_id} to be available"
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed with an unexpected error while waiting for the DB cluster {db_cluster_id}")


def wait_for_instance_snapshot_status(client, module, db_snapshot_id, waiter_name):
    try:
        client.get_waiter(waiter_name).wait(DBSnapshotIdentifier=db_snapshot_id)
    except WaiterError as e:
        if waiter_name == "db_snapshot_deleted":
            msg = f"Failed to wait for DB snapshot {db_snapshot_id} to be deleted"
        else:
            msg = f"Failed to wait for DB snapshot {db_snapshot_id} to be available"
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e, msg=f"Failed with an unexpected error while waiting for the DB snapshot {db_snapshot_id}"
        )


def wait_for_cluster_snapshot_status(client, module, db_snapshot_id, waiter_name):
    try:
        client.get_waiter(waiter_name).wait(DBClusterSnapshotIdentifier=db_snapshot_id)
    except WaiterError as e:
        if waiter_name == "db_cluster_snapshot_deleted":
            msg = f"Failed to wait for DB cluster snapshot {db_snapshot_id} to be deleted"
        else:
            msg = f"Failed to wait for DB cluster snapshot {db_snapshot_id} to be available"
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg=f"Failed with an unexpected error while waiting for the DB cluster snapshot {db_snapshot_id}",
        )


def wait_for_status(client, module, identifier, method_name):
    rds_method_attributes = get_rds_method_attribute(method_name, module)
    waiter_name = rds_method_attributes.waiter
    resource = rds_method_attributes.resource

    if resource == "cluster":
        wait_for_cluster_status(client, module, identifier, waiter_name)
    elif resource == "instance":
        wait_for_instance_status(client, module, identifier, waiter_name)
    elif resource == "instance_snapshot":
        wait_for_instance_snapshot_status(client, module, identifier, waiter_name)
    elif resource == "cluster_snapshot":
        wait_for_cluster_snapshot_status(client, module, identifier, waiter_name)


def get_tags(client, module, resource_arn):
    try:
        return boto3_tag_list_to_ansible_dict(client.list_tags_for_resource(ResourceName=resource_arn)["TagList"])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe tags")


def arg_spec_to_rds_params(options_dict):
    tags = options_dict.pop("tags")
    has_processor_features = False
    if "processor_features" in options_dict:
        has_processor_features = True
        processor_features = options_dict.pop("processor_features")
    camel_options = snake_dict_to_camel_dict(options_dict, capitalize_first=True)
    for key in list(camel_options.keys()):
        for old, new in (("Db", "DB"), ("Iam", "IAM"), ("Az", "AZ"), ("Ca", "CA")):
            if old in key:
                camel_options[key.replace(old, new)] = camel_options.pop(key)
    camel_options["Tags"] = tags
    if has_processor_features:
        camel_options["ProcessorFeatures"] = processor_features
    return camel_options


def ensure_tags(client, module, resource_arn, existing_tags, tags, purge_tags):
    if tags is None:
        return False
    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, tags, purge_tags)
    changed = bool(tags_to_add or tags_to_remove)
    if tags_to_add:
        call_method(
            client,
            module,
            method_name="add_tags_to_resource",
            parameters={"ResourceName": resource_arn, "Tags": ansible_dict_to_boto3_tag_list(tags_to_add)},
        )
    if tags_to_remove:
        call_method(
            client,
            module,
            method_name="remove_tags_from_resource",
            parameters={"ResourceName": resource_arn, "TagKeys": tags_to_remove},
        )
    return changed


def compare_iam_roles(existing_roles, target_roles, purge_roles):
    """
    Returns differences between target and existing IAM roles

        Parameters:
            existing_roles (list): Existing IAM roles
            target_roles (list): Target IAM roles
            purge_roles (bool): Remove roles not in target_roles if True

        Returns:
            roles_to_add (list): List of IAM roles to add
            roles_to_delete (list): List of IAM roles to delete
    """
    existing_roles = [dict((k, v) for k, v in role.items() if k != "status") for role in existing_roles]
    roles_to_add = [role for role in target_roles if role not in existing_roles]
    roles_to_remove = [role for role in existing_roles if role not in target_roles] if purge_roles else []
    return roles_to_add, roles_to_remove


def update_iam_roles(client, module, instance_id, roles_to_add, roles_to_remove):
    """
    Update a DB instance's associated IAM roles

        Parameters:
            client: RDS client
            module: AnsibleAWSModule
            instance_id (str): DB's instance ID
            roles_to_add (list): List of IAM roles to add
            roles_to_delete (list): List of IAM roles to delete

        Returns:
            changed (bool): True if changes were successfully made to DB instance's IAM roles; False if not
    """
    for role in roles_to_remove:
        params = {"DBInstanceIdentifier": instance_id, "RoleArn": role["role_arn"], "FeatureName": role["feature_name"]}
        _result, changed = call_method(client, module, method_name="remove_role_from_db_instance", parameters=params)
    for role in roles_to_add:
        params = {"DBInstanceIdentifier": instance_id, "RoleArn": role["role_arn"], "FeatureName": role["feature_name"]}
        _result, changed = call_method(client, module, method_name="add_role_to_db_instance", parameters=params)
    return changed


@AWSRetry.jittered_backoff()
def describe_db_cluster_parameter_groups(
    module: AnsibleAWSModule, connection: Any, group_name: str
) -> List[Dict[str, Any]]:
    result = []
    try:
        params = {}
        if group_name is not None:
            params["DBClusterParameterGroupName"] = group_name
        paginator = connection.get_paginator("describe_db_cluster_parameter_groups")
        result = paginator.paginate(**params).build_full_result()["DBClusterParameterGroups"]
    except is_boto3_error_code("DBParameterGroupNotFound"):
        pass
    except ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't access parameter groups information")
    return result


@AWSRetry.jittered_backoff()
def describe_db_cluster_parameters(
    module: AnsibleAWSModule, connection: Any, group_name: str, source: str = "all"
) -> List[Dict[str, Any]]:
    result = []
    try:
        paginator = connection.get_paginator("describe_db_cluster_parameters")
        params = {"DBClusterParameterGroupName": group_name}
        if source != "all":
            params["Source"] = source
        result = paginator.paginate(**params).build_full_result()["Parameters"]
    except is_boto3_error_code("DBParameterGroupNotFound"):
        pass
    except ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't access RDS cluster parameters information")
    return result

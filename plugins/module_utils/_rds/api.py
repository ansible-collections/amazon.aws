# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.text.converters import to_text

from ..botocore import is_boto3_error_code
from ..retries import AWSRetry
from ..tagging import boto3_tag_list_to_ansible_dict
from .common import RDSErrorHandler
from .common import get_rds_method_attribute
from .waiters import wait_for_status


@RDSErrorHandler.list_error_handler("describe db cluster snapshots", [])
@AWSRetry.jittered_backoff()
def describe_db_cluster_snapshots(client, **params: Dict) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_db_cluster_snapshots")
    return paginator.paginate(**params).build_full_result()["DBClusterSnapshots"]


@RDSErrorHandler.list_error_handler("describe db instances", [])
@AWSRetry.jittered_backoff()
def describe_db_instances(client, **params: Dict) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_db_instances")
    return paginator.paginate(**params).build_full_result()["DBInstances"]


@RDSErrorHandler.list_error_handler("describe db snapshots", [])
@AWSRetry.jittered_backoff()
def describe_db_snapshots(client, **params: Dict) -> List[Dict]:
    paginator = client.get_paginator("describe_db_snapshots")
    return paginator.paginate(**params).build_full_result()["DBSnapshots"]


@RDSErrorHandler.list_error_handler("list tags for resource", [])
@AWSRetry.jittered_backoff()
def list_tags_for_resource(client, resource_arn: str) -> List[Dict[str, str]]:
    return client.list_tags_for_resource(ResourceName=resource_arn)["TagList"]


def get_final_identifier(method_name: str, module) -> str:
    """
    Returns the final identifier for the resource to which the specified method applies.

        Parameters:
            method_name (str): RDS method whose target resource final identifier is returned
            module: AnsibleAWSModule

        Returns:
            updated_identifier (str): The new resource identifier from module params if not in check mode, there is a new identifier in module params, and
                apply_immediately is True; otherwise returns the original resource identifier from module params

        Raises:
            NotImplementedError if the provided method is not supported
    """
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


_NOOP_ERRORS = [
    (("modify_db_instance", "modify_db_cluster"), "InvalidParameterCombination", "No modifications were requested"),
    (("promote_read_replica",), "InvalidDBInstanceState", "DB Instance is not a read replica"),
    (("promote_read_replica_db_cluster",), "InvalidDBClusterStateFault", "DB Cluster that is not a read replica"),
]

_SPECIAL_ERRORS = [
    (
        ("modify_db_instance", "modify_db_cluster"),
        "InvalidParameterCombination",
        "ModifyDbCluster API",
        "It appears you are trying to modify attributes that are managed at the cluster level. Please see rds_cluster",
    ),
]


def handle_errors(module, exception: Any, method_name: str, parameters: Dict[str, Any]) -> bool:
    """
    Fails the module with an appropriate error message given the provided exception.

        Parameters:
            module: AnsibleAWSModule
            exception: Botocore exception to be handled
            method_name (str): Name of boto3 rds client method
            parameters (dict): Parameters provided to boto3 client method

        Returns:
            changed (bool): False if provided exception indicates that no modifications were requested or a read replica promotion was attempted on an
                instance/cluseter that is not a read replica; should never return True (the module should always fail instead)
    """
    if not isinstance(exception, ClientError):
        module.fail_json_aws(exception, msg=f"Unexpected failure for method {method_name} with parameters {parameters}")
        return True

    error_code = exception.response["Error"]["Code"]
    error_text = to_text(exception)

    for methods, code, message in _NOOP_ERRORS:
        if method_name in methods and error_code == code and message in error_text:
            return False

    for methods, code, message, custom_msg in _SPECIAL_ERRORS:
        if method_name in methods and error_code == code and message in error_text:
            module.fail_json_aws(exception, msg=custom_msg)
            return True

    if method_name == "create_db_cluster" and error_code == "InvalidParameterValue":
        accepted_engines = ["aurora", "aurora-mysql", "aurora-postgresql", "mysql", "postgres"]
        if parameters.get("Engine") not in accepted_engines:
            module.fail_json_aws(
                exception, msg=f"DB engine {parameters.get('Engine')} should be one of {accepted_engines}"
            )
            return True

    module.fail_json_aws(
        exception,
        msg=f"Unable to {get_rds_method_attribute(method_name, module).operation_description}",
    )
    return True


def call_method(client, module, method_name: str, parameters: Dict[str, Any]) -> Tuple[Any, bool]:
    """Calls the provided boto3 rds client method with the provided parameters.

    Handles check mode determination, whether or not to wait for resource status, and method-specific retry codes.

        Parameters:
            client: boto3 rds client
            module: Ansible AWS module
            method_name (str): Name of the boto3 rds client method to call
            parameters (dict): Parameters to pass to the boto3 client method; these must already match expected parameters for the method and
                be formatted correctly (CamelCase, Tags and other attributes converted to lists of dicts as needed)

        Returns:
            tuple (any, bool):
                result (any): Result value from method call
                changed (bool): True if changes were made to the resource, False otherwise
    """
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


def get_snapshot(client, snapshot_identifier: str, snapshot_type: str, convert_tags: bool = True) -> Dict[str, Any]:
    """
    Returns instance or cluster snapshot attributes given the snapshot identifier.

        Parameters:
            client: boto3 rds client
            snapshot_identifier (str): Unique snapshot identifier
            snapshot_type (str): Which type of snapshot to get, one of: cluster, instance
            convert_tags (bool): Whether to convert the snapshot tags from boto3 list of dicts to Ansible dict; defaults to True

        Returns:
            snapshot (dict): Snapshot attributes. If snapshot with provided id is not found, returns an empty dict

        Raises:
            ValueError if an invalid snapshot_type is passed
    """
    valid_types = ("cluster", "instance")
    if snapshot_type not in valid_types:
        raise ValueError(f"Invalid snapshot_type. Expected one of: {valid_types}")

    snapshot = {}
    if snapshot_type == "cluster":
        snapshots = describe_db_cluster_snapshots(client, DBClusterSnapshotIdentifier=snapshot_identifier)
    elif snapshot_type == "instance":
        snapshots = describe_db_snapshots(client, DBSnapshotIdentifier=snapshot_identifier)
    if snapshots:
        snapshot = snapshots[0]

    if snapshot and convert_tags:
        snapshot["Tags"] = boto3_tag_list_to_ansible_dict(snapshot.pop("TagList", None))

    return snapshot


def update_iam_roles(
    client,
    module,
    instance_id: str,
    roles_to_add: List[Dict[str, str]],
    roles_to_remove: List[Dict[str, str]],
) -> bool:
    """
    Update a DB instance's associated IAM roles

        Parameters:
            client: RDS client
            module: AnsibleAWSModule
            instance_id (str): DB's instance ID
            roles_to_add (list): List of IAM roles to add in snake-cased dict format
            roles_to_delete (list): List of IAM roles to delete in snake-cased dict format

        Returns:
            changed (bool): True if changes were successfully made to DB instance's IAM roles; False if not
    """
    changed = False
    for role in roles_to_remove:
        params = {"DBInstanceIdentifier": instance_id, "RoleArn": role["role_arn"], "FeatureName": role["feature_name"]}
        _result, local_changed = call_method(
            client, module, method_name="remove_role_from_db_instance", parameters=params
        )
        changed |= local_changed
    for role in roles_to_add:
        params = {"DBInstanceIdentifier": instance_id, "RoleArn": role["role_arn"], "FeatureName": role["feature_name"]}
        _result, local_changed = call_method(client, module, method_name="add_role_to_db_instance", parameters=params)
        changed |= local_changed
    return changed


@AWSRetry.jittered_backoff()
def describe_db_cluster_parameter_groups(module, connection: Any, group_name: Optional[str]) -> List[Dict[str, Any]]:
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
def describe_db_instance_parameter_groups(connection: Any, module, db_parameter_group_name: str = None) -> List[dict]:
    try:
        if db_parameter_group_name:
            result = connection.describe_db_parameter_groups(DBParameterGroupName=db_parameter_group_name)[
                "DBParameterGroups"
            ]
        else:
            result = connection.describe_db_parameter_groups()["DBParameterGroups"]

        # Get tags
        for parameter_group in result:
            existing_tags = connection.list_tags_for_resource(ResourceName=parameter_group["DBParameterGroupArn"])[
                "TagList"
            ]
            parameter_group["tags"] = boto3_tag_list_to_ansible_dict(existing_tags)

        return [camel_dict_to_snake_dict(group, ignore_list=["tags"]) for group in result] if result else []
    except is_boto3_error_code("DBParameterGroupNotFound"):
        return []
    except ClientError as e:
        module.fail_json_aws(e, msg="Couldn't access parameter group information")
    return result


@AWSRetry.jittered_backoff()
def describe_db_cluster_parameters(
    module, connection: Any, group_name: str, source: str = "all"
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

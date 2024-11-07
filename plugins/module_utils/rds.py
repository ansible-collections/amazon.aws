# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections import namedtuple
from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
    from botocore.exceptions import WaiterError
except ImportError:
    pass

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter

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


class AnsibleRDSError(AnsibleAWSError):
    pass


class RDSErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleRDSError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(
            ["DBInstanceNotFound", "DBSnapshotNotFound", "DBClusterNotFound", "DBClusterSnapshotNotFoundFault"]
        )


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


def get_rds_method_attribute(method_name: str, module: AnsibleAWSModule) -> Boto3ClientMethod:
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


def get_final_identifier(method_name: str, module: AnsibleAWSModule) -> str:
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


def handle_errors(module: AnsibleAWSModule, exception: Any, method_name: str, parameters: Dict[str, Any]) -> bool:
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


def call_method(client, module: AnsibleAWSModule, method_name: str, parameters: Dict[str, Any]) -> Tuple[Any, bool]:
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


def wait_for_instance_status(client, module: AnsibleAWSModule, db_instance_id: str, waiter_name: str) -> None:
    """
    Waits until provided instance has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_instance_id (str): DB instance identifier
            waiter_name (str): Name of either a boto3 rds client waiter or an RDS waiter defined in module_utils/waiters.py
    """

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


def wait_for_cluster_status(client, module: AnsibleAWSModule, db_cluster_id: str, waiter_name: str) -> None:
    """
    Waits until provided cluster has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_cluster_id (str): DB cluster identifier
            waiter_name (str): Name of either a boto3 rds client waiter or an RDS waiter defined in module_utils/waiters.py
    """
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


def wait_for_instance_snapshot_status(client, module: AnsibleAWSModule, db_snapshot_id: str, waiter_name: str) -> None:
    """
    Waits until provided instance snapshot has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_snapshot_id (str): DB instance snapshot identifier
            waiter_name (str): Name of a boto3 rds client waiter
    """
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


def wait_for_cluster_snapshot_status(client, module: AnsibleAWSModule, db_snapshot_id: str, waiter_name: str) -> None:
    """
    Waits until provided cluster snapshot has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_snapshot_id (str): DB cluster snapshot identifier
            waiter_name (str): Name of a boto3 rds client waiter
    """
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


def wait_for_status(client, module: AnsibleAWSModule, identifier: str, method_name: str) -> None:
    """
    Waits until provided resource has reached the expected final status for provided method.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            identifier (str): resource identifier
            method_name (str): Name of boto3 rds client method on whose final status to wait
    """
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


def get_tags(client, module: AnsibleAWSModule, resource_arn: str) -> Dict[str, str]:
    """
    Returns tags for provided RDS resource, formatted as an Ansible dict.

    Fails the module if an error is raised while retrieving resource tags.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            resource_arn (str): AWS resource ARN

        Returns:
            tags (dict): Tags for resource, formatted as an Ansible dict. An empty list is returned if the resource has no tags.
    """
    try:
        tags = list_tags_for_resource(client, resource_arn)
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Unable to list tags for resource {resource_arn}")
    return boto3_tag_list_to_ansible_dict(tags)


def arg_spec_to_rds_params(options_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts snake_cased rds module options to CamelCased parameter formats expected by boto3 rds client.

    Does not alter case for keys or values in the following attributes: tags, processor_features.
    Includes special handling of certain boto3 params that do not follow standard CamelCase.

        Parameters:
            options_dict (dict): Snake-cased options for a boto3 rds client method

        Returns:
            camel_options (dct): Options formatted for boto3 rds client
    """
    tags = options_dict.pop("tags")
    has_processor_features = False
    if "processor_features" in options_dict:
        has_processor_features = True
        processor_features = options_dict.pop("processor_features")
    camel_options = snake_dict_to_camel_dict(options_dict, capitalize_first=True)
    aws_replace_keys = (
        ("Db", "DB"),
        ("Iam", "IAM"),
        ("Az", "AZ"),
        ("Ca", "CA"),
        ("PerformanceInsightsKmsKeyId", "PerformanceInsightsKMSKeyId"),
    )
    for key in list(camel_options.keys()):
        for old, new in aws_replace_keys:
            if old in key:
                camel_options[key.replace(old, new)] = camel_options.pop(key)
    camel_options["Tags"] = tags
    if has_processor_features:
        camel_options["ProcessorFeatures"] = processor_features
    return camel_options


def format_rds_client_method_parameters(
    client, module: AnsibleAWSModule, parameters: Dict[str, Any], method_name: str, format_tags: bool
) -> Dict[str, Any]:
    """
    Returns a dict of parameters validated and formatted for the provided boto3 client method.

    Performs the following parameters checks and updates:
        - Converts parameters supplied as snake_cased module options to CamelCase
        - Ensures that all required parameters for the provided method are present
        - Ensures that only parameters allowed for the provided method are present, removing any that are not relevant
        - Removes parameters with None values
        - If format_tags is True, converts "Tags" param from an Ansible dict to boto3 list of dicts

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            parameters (dict): Parameter options as provided to module
            method_name (str): boto3 client method for which to validate parameters
            format_tags (bool): Whether to convert tags from an Ansible dict to boto3 list of dicts

        Returns:
            Dict of client parameters formatted for the provided method

        Raises:
            Fails the module if any parameters required by the provided method are not provided in module options
    """
    required_options = get_boto3_client_method_parameters(client, method_name, required=True)
    if any(parameters.get(k) is None for k in required_options):
        method_description = get_rds_method_attribute(method_name, module).operation_description
        module.fail_json(msg=f"To {method_description} requires the parameters: {required_options}")
    options = get_boto3_client_method_parameters(client, method_name)
    parameters = dict((k, v) for k, v in parameters.items() if k in options and v is not None)
    if format_tags and parameters.get("Tags"):
        parameters["Tags"] = ansible_dict_to_boto3_tag_list(parameters["Tags"])

    return parameters


def ensure_tags(
    client,
    module: AnsibleAWSModule,
    resource_arn: str,
    existing_tags: Dict[str, str],
    tags: Optional[Dict[str, str]],
    purge_tags: bool,
) -> bool:
    """
    Compares current resource tages to desired tags and adds/removes tags to ensure desired tags are present.

    A value of None for desired tags results in resource tags being left as is.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            resource_arn (str): AWS resource ARN
            existing_tags (dict): Current resource tags formatted as an Ansible dict
            tags (dict): Desired resource tags formatted as an Ansible dict
            purge_tags (bool): Whether to remove any existing resource tags not present in desired tags

        Returns:
            True if resource tags are updated, False if not.
    """
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


def compare_iam_roles(
    existing_roles: List[Dict[str, str]], target_roles: List[Dict[str, str]], purge_roles: bool
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Returns differences between target and existing IAM roles.

        Parameters:
            existing_roles (list): Existing IAM roles as a list of snake-cased dicts
            target_roles (list): Target IAM roles as a list of snake-cased dicts
            purge_roles (bool): Remove roles not in target_roles if True

        Returns:
            roles_to_add (list): List of IAM roles to add
            roles_to_delete (list): List of IAM roles to delete
    """
    existing_roles = [dict((k, v) for k, v in role.items() if k != "status") for role in existing_roles]
    roles_to_add = [role for role in target_roles if role not in existing_roles]
    roles_to_remove = [role for role in existing_roles if role not in target_roles] if purge_roles else []
    return roles_to_add, roles_to_remove


def update_iam_roles(
    client,
    module: AnsibleAWSModule,
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
    for role in roles_to_remove:
        params = {"DBInstanceIdentifier": instance_id, "RoleArn": role["role_arn"], "FeatureName": role["feature_name"]}
        _result, changed = call_method(client, module, method_name="remove_role_from_db_instance", parameters=params)
    for role in roles_to_add:
        params = {"DBInstanceIdentifier": instance_id, "RoleArn": role["role_arn"], "FeatureName": role["feature_name"]}
        _result, changed = call_method(client, module, method_name="add_role_to_db_instance", parameters=params)
    return changed


@AWSRetry.jittered_backoff()
def describe_db_cluster_parameter_groups(
    module: AnsibleAWSModule, connection: Any, group_name: Optional[str]
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
def describe_db_instance_parameter_groups(
    connection: Any, module: AnsibleAWSModule, db_parameter_group_name: str = None
) -> List[dict]:
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

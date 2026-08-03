# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections import namedtuple

from ..botocore import is_boto3_error_code
from ..errors import AWSErrorHandler
from ..exceptions import AnsibleAWSError


class AnsibleRDSError(AnsibleAWSError):
    pass


class RDSErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleRDSError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(
            ["DBInstanceNotFound", "DBSnapshotNotFound", "DBClusterNotFound", "DBClusterSnapshotNotFoundFault"]
        )


Boto3ClientMethod = namedtuple(
    "Boto3ClientMethod", ["name", "waiter", "operation_description", "resource", "retry_codes"]
)

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


_RESOURCE_CONFIGS = {
    "cluster": {
        "methods": cluster_method_names,
        "param_key": "new_db_cluster_identifier",
        "default_waiter": "cluster_available",
        "default_retry_codes": ["InvalidDBClusterState"],
        "overrides": {
            "delete_db_cluster": {"waiter": "cluster_deleted"},
            "restore_db_cluster_from_snapshot": {"retry_codes": ["InvalidDBClusterSnapshotState"]},
        },
    },
    "instance": {
        "methods": instance_method_names,
        "param_key": "new_db_instance_identifier",
        "default_waiter": "db_instance_available",
        "default_retry_codes": ["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
        "overrides": {
            "delete_db_instance": {"waiter": "db_instance_deleted"},
            "stop_db_instance": {"waiter": "db_instance_stopped"},
            "add_role_to_db_instance": {"waiter": "role_associated"},
            "remove_role_from_db_instance": {"waiter": "role_disassociated"},
            "promote_read_replica": {"waiter": "read_replica_promoted"},
            "restore_db_instance_from_db_snapshot": {"retry_codes": ["InvalidDBSnapshotState"]},
        },
    },
    "cluster_snapshot": {
        "methods": cluster_snapshot_method_names,
        "param_key": "db_cluster_snapshot_identifier",
        "default_waiter": "db_cluster_snapshot_available",
        "default_retry_codes": ["InvalidDBClusterSnapshotState"],
        "overrides": {
            "delete_db_cluster_snapshot": {"waiter": "db_cluster_snapshot_deleted"},
            "create_db_cluster_snapshot": {"retry_codes": ["InvalidDBClusterState"]},
        },
    },
    "instance_snapshot": {
        "methods": instance_snapshot_method_names,
        "param_key": "db_snapshot_identifier",
        "default_waiter": "db_snapshot_available",
        "default_retry_codes": ["InvalidDBSnapshotState"],
        "overrides": {
            "delete_db_snapshot": {"waiter": "db_snapshot_deleted"},
            "create_db_snapshot": {"retry_codes": ["InvalidDBInstanceState"]},
        },
    },
}


def get_rds_method_attribute(method_name: str, module) -> Boto3ClientMethod:
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
    readable_op = method_name.replace("_", " ").replace("db", "DB")

    for resource, config in _RESOURCE_CONFIGS.items():
        if method_name in config["methods"] and config["param_key"] in module.params:
            overrides = config["overrides"].get(method_name, {})
            waiter = overrides.get("waiter", config["default_waiter"])
            retry_codes = overrides.get("retry_codes", config["default_retry_codes"])
            return Boto3ClientMethod(
                name=method_name,
                waiter=waiter,
                operation_description=readable_op,
                resource=resource,
                retry_codes=retry_codes,
            )

    if module.params.get("wait"):
        raise NotImplementedError(
            f"method {method_name} hasn't been added to the list of accepted methods to use a waiter in module_utils/rds.py",
        )

    return Boto3ClientMethod(
        name=method_name, waiter="", operation_description=readable_op, resource="", retry_codes=[]
    )

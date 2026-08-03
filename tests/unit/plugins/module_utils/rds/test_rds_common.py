# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.rds import Boto3ClientMethod
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_rds_method_attribute

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_rds_common.py requires the python modules 'boto3' and 'botocore'")


def helper_expected(x):
    return x, nullcontext()


def helper_error(*args, **kwargs):
    return MagicMock(), pytest.raises(*args, **kwargs)


@pytest.mark.parametrize(
    "method_name, params, expected, error",
    [
        (
            "delete_db_cluster",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="delete_db_cluster",
                    waiter="cluster_deleted",
                    operation_description="delete DB cluster",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "create_db_cluster",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="create_db_cluster",
                    waiter="cluster_available",
                    operation_description="create DB cluster",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "start_db_cluster",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="start_db_cluster",
                    waiter="cluster_available",
                    operation_description="start DB cluster",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "stop_db_cluster",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="stop_db_cluster",
                    waiter="cluster_available",
                    operation_description="stop DB cluster",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "restore_db_cluster_from_snapshot",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="restore_db_cluster_from_snapshot",
                    waiter="cluster_available",
                    operation_description="restore DB cluster from snapshot",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterSnapshotState"],
                )
            ),
        ),
        (
            "modify_db_cluster",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="modify_db_cluster",
                    waiter="cluster_available",
                    operation_description="modify DB cluster",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "list_tags_for_resource",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="list_tags_for_resource",
                    waiter="cluster_available",
                    operation_description="list tags for resource",
                    resource="cluster",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "fake_method",
            {"wait": False},
            *helper_expected(
                Boto3ClientMethod(
                    name="fake_method", waiter="", operation_description="fake method", resource="", retry_codes=[]
                )
            ),
        ),
        (
            "fake_method",
            {"wait": True},
            *helper_error(
                NotImplementedError,
                match=(
                    "method fake_method hasn't been added to the list of accepted methods to use a waiter in"
                    " module_utils/rds.py"
                ),
            ),
        ),
    ],
)
def test__get_rds_method_attribute_cluster(method_name, params, expected, error):
    module = MagicMock()
    module.params = params
    with error:
        assert get_rds_method_attribute(method_name, module) == expected


@pytest.mark.parametrize(
    "method_name, params, expected, error",
    [
        (
            "delete_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="delete_db_instance",
                    waiter="db_instance_deleted",
                    operation_description="delete DB instance",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "create_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="create_db_instance",
                    waiter="db_instance_available",
                    operation_description="create DB instance",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "stop_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="stop_db_instance",
                    waiter="db_instance_stopped",
                    operation_description="stop DB instance",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "promote_read_replica",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="promote_read_replica",
                    waiter="read_replica_promoted",
                    operation_description="promote read replica",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "restore_db_instance_from_db_snapshot",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="restore_db_instance_from_db_snapshot",
                    waiter="db_instance_available",
                    operation_description="restore DB instance from DB snapshot",
                    resource="instance",
                    retry_codes=["InvalidDBSnapshotState"],
                )
            ),
        ),
        (
            "modify_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="modify_db_instance",
                    waiter="db_instance_available",
                    operation_description="modify DB instance",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "add_role_to_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="add_role_to_db_instance",
                    waiter="role_associated",
                    operation_description="add role to DB instance",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "remove_role_from_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="remove_role_from_db_instance",
                    waiter="role_disassociated",
                    operation_description="remove role from DB instance",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "list_tags_for_resource",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="list_tags_for_resource",
                    waiter="db_instance_available",
                    operation_description="list tags for resource",
                    resource="instance",
                    retry_codes=["InvalidDBInstanceState", "InvalidDBSecurityGroupState"],
                )
            ),
        ),
        (
            "fake_method",
            {"wait": False},
            *helper_expected(
                Boto3ClientMethod(
                    name="fake_method", waiter="", operation_description="fake method", resource="", retry_codes=[]
                )
            ),
        ),
        (
            "fake_method",
            {"wait": True},
            *helper_error(
                NotImplementedError,
                match=(
                    "method fake_method hasn't been added to the list of accepted methods to use a waiter in"
                    " module_utils/rds.py"
                ),
            ),
        ),
    ],
)
def test__get_rds_method_attribute_instance(method_name, params, expected, error):
    module = MagicMock()
    module.params = params
    with error:
        assert get_rds_method_attribute(method_name, module) == expected


@pytest.mark.parametrize(
    "method_name, params, expected, error",
    [
        (
            "delete_db_snapshot",
            {
                "db_snapshot_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="delete_db_snapshot",
                    waiter="db_snapshot_deleted",
                    operation_description="delete DB snapshot",
                    resource="instance_snapshot",
                    retry_codes=["InvalidDBSnapshotState"],
                )
            ),
        ),
        (
            "create_db_snapshot",
            {
                "db_snapshot_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="create_db_snapshot",
                    waiter="db_snapshot_available",
                    operation_description="create DB snapshot",
                    resource="instance_snapshot",
                    retry_codes=["InvalidDBInstanceState"],
                )
            ),
        ),
        (
            "copy_db_snapshot",
            {"source_db_snapshot_identifier": "test", "db_snapshot_identifier": "test-copy"},
            *helper_expected(
                Boto3ClientMethod(
                    name="copy_db_snapshot",
                    waiter="db_snapshot_available",
                    operation_description="copy DB snapshot",
                    resource="instance_snapshot",
                    retry_codes=["InvalidDBSnapshotState"],
                )
            ),
        ),
        (
            "list_tags_for_resource",
            {
                "db_snapshot_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="list_tags_for_resource",
                    waiter="db_snapshot_available",
                    operation_description="list tags for resource",
                    resource="instance_snapshot",
                    retry_codes=["InvalidDBSnapshotState"],
                )
            ),
        ),
        (
            "delete_db_cluster_snapshot",
            {
                "db_cluster_snapshot_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="delete_db_cluster_snapshot",
                    waiter="db_cluster_snapshot_deleted",
                    operation_description="delete DB cluster snapshot",
                    resource="cluster_snapshot",
                    retry_codes=["InvalidDBClusterSnapshotState"],
                )
            ),
        ),
        (
            "create_db_cluster_snapshot",
            {
                "db_cluster_snapshot_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="create_db_cluster_snapshot",
                    waiter="db_cluster_snapshot_available",
                    operation_description="create DB cluster snapshot",
                    resource="cluster_snapshot",
                    retry_codes=["InvalidDBClusterState"],
                )
            ),
        ),
        (
            "copy_db_cluster_snapshot",
            {"source_db_cluster_snapshot_identifier": "test", "db_cluster_snapshot_identifier": "test-copy"},
            *helper_expected(
                Boto3ClientMethod(
                    name="copy_db_cluster_snapshot",
                    waiter="db_cluster_snapshot_available",
                    operation_description="copy DB cluster snapshot",
                    resource="cluster_snapshot",
                    retry_codes=["InvalidDBClusterSnapshotState"],
                )
            ),
        ),
        (
            "list_tags_for_resource",
            {
                "db_cluster_snapshot_identifier": "test",
            },
            *helper_expected(
                Boto3ClientMethod(
                    name="list_tags_for_resource",
                    waiter="db_cluster_snapshot_available",
                    operation_description="list tags for resource",
                    resource="cluster_snapshot",
                    retry_codes=["InvalidDBClusterSnapshotState"],
                )
            ),
        ),
        (
            "fake_method",
            {"wait": False},
            *helper_expected(
                Boto3ClientMethod(
                    name="fake_method", waiter="", operation_description="fake method", resource="", retry_codes=[]
                )
            ),
        ),
        (
            "fake_method",
            {"wait": True},
            *helper_error(
                NotImplementedError,
                match=(
                    "method fake_method hasn't been added to the list of accepted methods to use a waiter in"
                    " module_utils/rds.py"
                ),
            ),
        ),
    ],
)
def test__get_rds_method_attribute_snapshot(method_name, params, expected, error):
    module = MagicMock()
    module.params = params
    with error:
        assert get_rds_method_attribute(method_name, module) == expected

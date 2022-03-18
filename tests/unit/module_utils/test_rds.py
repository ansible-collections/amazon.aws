# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.plugins.module_utils import rds


from contextlib import nullcontext
import pytest

try:
    from botocore.exceptions import ClientError, WaiterError
except ImportError:
    pass


def expected(x):
    return x, nullcontext()


def error(*args, **kwargs):
    return MagicMock(), pytest.raises(*args, **kwargs)


def build_exception(
    operation_name, code=None, message=None, http_status_code=None, error=True
):
    response = {}
    if error or code or message:
        response["Error"] = {}
    if code:
        response["Error"]["Code"] = code
    if message:
        response["Error"]["Message"] = message
    if http_status_code:
        response["ResponseMetadata"] = {"HTTPStatusCode": http_status_code}
    return ClientError(response, operation_name)


@pytest.mark.parametrize("waiter_name", ["", "db_snapshot_available"])
def test__wait_for_snapshot_status(waiter_name):
    rds.wait_for_snapshot_status(MagicMock(), MagicMock(), "test", waiter_name)


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            "db_snapshot_available",
            "Failed to wait for DB snapshot test to be available",
        ),
        (
            "db_cluster_snapshot_available",
            "Failed to wait for DB snapshot test to be available",
        ),
        ("db_snapshot_deleted", "Failed to wait for DB snapshot test to be deleted"),
        (
            "db_cluster_snapshot_deleted",
            "Failed to wait for DB snapshot test to be deleted",
        ),
    ],
)
def test__wait_for_snapshot_status_failed(input, expected):
    spec = {"get_waiter.side_effect": [WaiterError(None, None, None)]}
    client = MagicMock(**spec)
    module = MagicMock()

    rds.wait_for_snapshot_status(client, module, "test", input)
    module.fail_json_aws.assert_called_once
    module.fail_json_aws.call_args[1]["msg"] == expected


@pytest.mark.parametrize(
    "input, expected, error",
    [
        (
            "delete_db_snapshot",
            *expected(
                rds.Boto3ClientMethod(
                    name="delete_db_snapshot",
                    waiter="db_snapshot_deleted",
                    operation_description="delete DB snapshot",
                    cluster=False,
                    instance=False,
                    snapshot=True,
                )
            ),
        ),
        (
            "create_db_snapshot",
            *expected(
                rds.Boto3ClientMethod(
                    name="create_db_snapshot",
                    waiter="db_snapshot_available",
                    operation_description="create DB snapshot",
                    cluster=False,
                    instance=False,
                    snapshot=True,
                )
            ),
        ),
        (
            "delete_db_cluster_snapshot",
            *expected(
                rds.Boto3ClientMethod(
                    name="delete_db_cluster_snapshot",
                    waiter="db_cluster_snapshot_deleted",
                    operation_description="delete DB cluster snapshot",
                    cluster=False,
                    instance=False,
                    snapshot=True,
                )
            ),
        ),
        (
            "create_db_cluster_snapshot",
            *expected(
                rds.Boto3ClientMethod(
                    name="create_db_cluster_snapshot",
                    waiter="db_cluster_snapshot_available",
                    operation_description="create DB cluster snapshot",
                    cluster=False,
                    instance=False,
                    snapshot=True,
                )
            ),
        ),
        (
            "fake_method",
            *error(
                NotImplementedError,
                match="method fake_method hasn't been added to the list of accepted methods to use a waiter in module_utils/rds.py",
            ),
        ),
    ],
)
def test__get_rds_method_attribute(input, expected, error):
    with error:
        assert rds.get_rds_method_attribute(input, MagicMock()) == expected


@pytest.mark.parametrize(
    "method_name, params, expected",
    [
        ("create_db_snapshot", {"db_snapshot_identifier": "test"}, "test"),
        (
            "create_db_snapshot",
            {"db_snapshot_identifier": "test", "apply_immediately": True},
            "test",
        ),
        (
            "create_db_instance",
            {
                "db_instance_identifier": "test",
                "new_db_instance_identifier": "test_updated",
            },
            "test",
        ),
        (
            "create_db_snapshot",
            {"db_snapshot_identifier": "test", "apply_immediately": True},
            "test",
        ),
        (
            "create_db_instance",
            {
                "db_instance_identifier": "test",
                "new_db_instance_identifier": "test_updated",
                "apply_immediately": True,
            },
            "test_updated",
        ),
        (
            "create_db_cluster",
            {
                "db_cluster_identifier": "test",
                "new_db_cluster_identifier": "test_updated",
            },
            "test",
        ),
        (
            "create_db_snapshot",
            {"db_snapshot_identifier": "test", "apply_immediately": True},
            "test",
        ),
        (
            "create_db_cluster",
            {
                "db_cluster_identifier": "test",
                "new_db_cluster_identifier": "test_updated",
                "apply_immediately": True,
            },
            "test_updated",
        ),
    ],
)
def test__get_final_identifier(method_name, params, expected):
    module = MagicMock()
    module.params = params
    module.check_mode = False

    assert rds.get_final_identifier(method_name, module) == expected


@pytest.mark.parametrize(
    "method_name, exception, expected",
    [
        (
            "modify_db_instance",
            build_exception(
                "modify_db_instance",
                code="InvalidParameterCombination",
                message="No modifications were requested",
            ),
            False,
        ),
        (
            "promote_read_replica",
            build_exception(
                "promote_read_replica",
                code="InvalidDBInstanceState",
                message="DB Instance is not a read replica",
            ),
            False,
        ),
        (
            "promote_read_replica_db_cluster",
            build_exception(
                "promote_read_replica_db_cluster",
                code="InvalidDBClusterStateFault",
                message="DB Cluster that is not a read replica",
            ),
            False,
        ),
    ],
)
def test__handle_errors(method_name, exception, expected):
    assert rds.handle_errors(MagicMock(), exception, method_name, {}) == expected


@pytest.mark.parametrize(
    "method_name, exception, expected, error",
    [
        (
            "modify_db_instance",
            build_exception(
                "modify_db_instance",
                code="InvalidParameterCombination",
                message="ModifyDbCluster API",
            ),
            *expected(
                "It appears you are trying to modify attributes that are managed at the cluster level. Please see rds_cluster"
            ),
        ),
        (
            "modify_db_instance",
            build_exception("modify_db_instance", code="InvalidParameterCombination"),
            *error(
                NotImplementedError,
                match="method modify_db_instance hasn't been added to the list of accepted methods to use a waiter in module_utils/rds.py",
            ),
        ),
        (
            "promote_read_replica",
            build_exception("promote_read_replica", code="InvalidDBInstanceState"),
            *error(
                NotImplementedError,
                match="method promote_read_replica hasn't been added to the list of accepted methods to use a waiter in module_utils/rds.py",
            ),
        ),
        (
            "promote_read_replica_db_cluster",
            build_exception(
                "promote_read_replica_db_cluster", code="InvalidDBClusterStateFault"
            ),
            *error(
                NotImplementedError,
                match="method promote_read_replica_db_cluster hasn't been added to the list of accepted methods to use a waiter in module_utils/rds.py",
            ),
        ),
        (
            "create_db_instance",
            build_exception("create_db_instance", code="InvalidParameterValue"),
            *expected(
                "DB engine fake_engine should be one of aurora, aurora-mysql, aurora-postgresql, mariadb, mysql, oracle-ee, oracle-se, oracle-se1, "
                + "oracle-se2, postgres, sqlserver-ee, sqlserver-ex, sqlserver-se, sqlserver-web"
            ),
        ),
        (
            "create_db_cluster",
            build_exception("create_db_cluster", code="InvalidParameterValue"),
            *expected(
                "DB engine fake_engine should be one of aurora, aurora-mysql, aurora-postgresql"
            ),
        ),
    ],
)
def test__handle_errors_failed(method_name, exception, expected, error):
    module = MagicMock()

    with error:
        rds.handle_errors(module, exception, method_name, {"Engine": "fake_engine"})
        module.fail_json_aws.assert_called_once
        module.fail_json_aws.call_args[1]["msg"] == expected

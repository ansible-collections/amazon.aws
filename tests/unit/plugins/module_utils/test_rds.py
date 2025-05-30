# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from contextlib import nullcontext
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible_collections.amazon.aws.plugins.module_utils import rds
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_rds.py requires the python modules 'boto3' and 'botocore'")

mod_name = "ansible_collections.amazon.aws.plugins.module_utils.rds"


def helper_expected(x):
    return x, nullcontext()


def helper_error(*args, **kwargs):
    return MagicMock(), pytest.raises(*args, **kwargs)


def build_exception(operation_name, code=None, message=None, http_status_code=None, error=True):
    # Support skipping the test is botocore isn't installed
    # (called by parametrize before skip is evaluated)
    if not HAS_BOTO3:
        return Exception("MissingBotoCore")
    response = {}
    if error or code or message:
        response["Error"] = {}
    if code:
        response["Error"]["Code"] = code
    if message:
        response["Error"]["Message"] = message
    if http_status_code:
        response["ResponseMetadata"] = {"HTTPStatusCode": http_status_code}

    return botocore.exceptions.ClientError(response, operation_name)


@pytest.mark.parametrize("waiter_name", ["", "db_snapshot_available"])
def test__wait_for_instance_snapshot_status(waiter_name):
    rds.wait_for_instance_snapshot_status(MagicMock(), MagicMock(), "test", waiter_name)


@pytest.mark.parametrize("waiter_name", ["", "db_cluster_snapshot_available"])
def test__wait_for_cluster_snapshot_status(waiter_name):
    rds.wait_for_cluster_snapshot_status(MagicMock(), MagicMock(), "test", waiter_name)


@pytest.mark.parametrize(
    "waiter_name, expected",
    [
        (
            "db_snapshot_available",
            "Failed to wait for DB snapshot test to be available",
        ),
        ("db_snapshot_deleted", "Failed to wait for DB snapshot test to be deleted"),
    ],
)
def test__wait_for_instance_snapshot_status_failed(waiter_name, expected):
    spec = {"get_waiter.side_effect": [botocore.exceptions.WaiterError(None, None, None)]}
    client = MagicMock(**spec)
    module = MagicMock()

    rds.wait_for_instance_snapshot_status(client, module, "test", waiter_name)
    module.fail_json_aws.assert_called_once()
    assert module.fail_json_aws.call_args[1]["msg"] == expected


@pytest.mark.parametrize(
    "waiter_name, expected",
    [
        (
            "db_cluster_snapshot_available",
            "Failed to wait for DB cluster snapshot test to be available",
        ),
        (
            "db_cluster_snapshot_deleted",
            "Failed to wait for DB cluster snapshot test to be deleted",
        ),
    ],
)
def test__wait_for_cluster_snapshot_status_failed(waiter_name, expected):
    spec = {"get_waiter.side_effect": [botocore.exceptions.WaiterError(None, None, None)]}
    client = MagicMock(**spec)
    module = MagicMock()

    rds.wait_for_cluster_snapshot_status(client, module, "test", waiter_name)
    module.fail_json_aws.assert_called_once()
    assert module.fail_json_aws.call_args[1]["msg"] == expected


@pytest.mark.parametrize(
    "method_name, params, expected, error",
    [
        (
            "delete_db_cluster",
            {
                "new_db_cluster_identifier": "test",
            },
            *helper_expected(
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
        assert rds.get_rds_method_attribute(method_name, module) == expected


@pytest.mark.parametrize(
    "method_name, params, expected, error",
    [
        (
            "delete_db_instance",
            {
                "new_db_instance_identifier": "test",
            },
            *helper_expected(
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
        assert rds.get_rds_method_attribute(method_name, module) == expected


@pytest.mark.parametrize(
    "method_name, params, expected, error",
    [
        (
            "delete_db_snapshot",
            {
                "db_snapshot_identifier": "test",
            },
            *helper_expected(
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
                rds.Boto3ClientMethod(
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
        assert rds.get_rds_method_attribute(method_name, module) == expected


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
            *helper_expected(
                "It appears you are trying to modify attributes that are managed at the cluster level. Please see"
                " rds_cluster"
            ),
        ),
        (
            "modify_db_instance",
            build_exception("modify_db_instance", code="InvalidParameterCombination"),
            *helper_error(
                NotImplementedError,
                match=(
                    "method modify_db_instance hasn't been added to the list of accepted methods to use a waiter in"
                    " module_utils/rds.py"
                ),
            ),
        ),
        (
            "promote_read_replica",
            build_exception("promote_read_replica", code="InvalidDBInstanceState"),
            *helper_error(
                NotImplementedError,
                match=(
                    "method promote_read_replica hasn't been added to the list of accepted methods to use a waiter in"
                    " module_utils/rds.py"
                ),
            ),
        ),
        (
            "promote_read_replica_db_cluster",
            build_exception("promote_read_replica_db_cluster", code="InvalidDBClusterStateFault"),
            *helper_error(
                NotImplementedError,
                match=(
                    "method promote_read_replica_db_cluster hasn't been added to the list of accepted methods to use a"
                    " waiter in module_utils/rds.py"
                ),
            ),
        ),
        (
            "create_db_cluster",
            build_exception("create_db_cluster", code="InvalidParameterValue"),
            *helper_expected(
                "DB engine fake_engine should be one of ['aurora', 'aurora-mysql', 'aurora-postgresql', 'mysql', 'postgres']"
            ),
        ),
    ],
)
def test__handle_errors_failed(method_name, exception, expected, error):
    module = MagicMock()

    with error:
        rds.handle_errors(module, exception, method_name, {"Engine": "fake_engine"})
        module.fail_json_aws.assert_called_once()
        assert module.fail_json_aws.call_args[1]["msg"] == expected


@pytest.mark.parametrize(
    "snapshots, snapshot_type, convert_tags, expected",
    [
        ([], "cluster", False, {}),
        ([], "instance", True, {}),
        (
            [{"DBSnapshotIdentifier": "my-snapshot", "DBInstanceIdentifier": "my-instance", "TagList": []}],
            "instance",
            False,
            {"DBSnapshotIdentifier": "my-snapshot", "DBInstanceIdentifier": "my-instance", "TagList": []},
        ),
        (
            [
                {
                    "DBClusterSnapshotIdentifier": "my-cluster-snapshot",
                    "DBClusterIdentifier": "my-cluster",
                    "TagList": [],
                }
            ],
            "cluster",
            True,
            {"DBClusterSnapshotIdentifier": "my-cluster-snapshot", "DBClusterIdentifier": "my-cluster", "Tags": {}},
        ),
        (
            [
                {
                    "DBClusterSnapshotIdentifier": "my-cluster-snapshot",
                    "DBClusterIdentifier": "my-cluster",
                    "TagList": [{"Key": "TagOne", "Value": "Value one"}, {"Key": "tag_two", "Value": "Value two"}],
                }
            ],
            "cluster",
            False,
            {
                "DBClusterSnapshotIdentifier": "my-cluster-snapshot",
                "DBClusterIdentifier": "my-cluster",
                "TagList": [{"Key": "TagOne", "Value": "Value one"}, {"Key": "tag_two", "Value": "Value two"}],
            },
        ),
        (
            [
                {
                    "DBSnapshotIdentifier": "my-snapshot",
                    "DBInstanceIdentifier": "my-instance",
                    "TagList": [{"Key": "TagOne", "Value": "Value one"}, {"Key": "tag_two", "Value": "Value two"}],
                }
            ],
            "instance",
            True,
            {
                "DBSnapshotIdentifier": "my-snapshot",
                "DBInstanceIdentifier": "my-instance",
                "Tags": {"TagOne": "Value one", "tag_two": "Value two"},
            },
        ),
    ],
)
@patch(mod_name + ".describe_db_snapshots")
@patch(mod_name + ".describe_db_cluster_snapshots")
def test_get_snapshot_success(
    m_describe_db_cluster_snapshots, m_describe_db_snapshots, snapshots, snapshot_type, convert_tags, expected
):
    client = MagicMock()
    m_describe_db_cluster_snapshots.return_value = snapshots
    m_describe_db_snapshots.return_value = snapshots
    assert rds.get_snapshot(client, "my-snapshot", snapshot_type, convert_tags) == expected


def test_get_snapshot_error():
    client = MagicMock()
    with pytest.raises(ValueError) as e:
        rds.get_snapshot(client, "my-snapshot", "bad parameter")
    assert "Invalid snapshot_type. Expected one of: ('cluster', 'instance')" in str(e)


@pytest.mark.parametrize(
    "provided_params, format_tags, expected",
    [
        (
            {"RequiredParameter": "Present"},
            False,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "OptionalParameter": None},
            False,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "IrrelevantParameter": "Not used by this method"},
            False,
            {"RequiredParameter": "Present"},
        ),
        (
            {
                "RequiredParameter": "Present",
                "OptionalParameter": "Present",
                "Tags": {"still_in": "ansible_dict_format"},
            },
            False,
            {
                "RequiredParameter": "Present",
                "OptionalParameter": "Present",
                "Tags": {"still_in": "ansible_dict_format"},
            },
        ),
        (
            {"RequiredParameter": "Present"},
            True,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "Tags": None},
            True,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "Tags": {}},
            True,
            {"RequiredParameter": "Present", "Tags": {}},
        ),
        (
            {"RequiredParameter": "Present", "Tags": {"Now in": "boto3_list_format"}},
            True,
            {"RequiredParameter": "Present", "Tags": [{"Key": "Now in", "Value": "boto3_list_format"}]},
        ),
    ],
)
@patch(mod_name + ".get_boto3_client_method_parameters")
def test_format_rds_client_method_parameters_success(
    m_get_boto3_client_method_parameters, provided_params, format_tags, expected
):
    module = MagicMock()
    module.fail_json_aws = MagicMock()
    client = MagicMock()
    m_get_boto3_client_method_parameters.side_effect = [
        ["RequiredParameter"],
        ["RequiredParameter", "OptionalParameter", "Tags"],
    ]

    assert (
        rds.format_rds_client_method_parameters(client, module, provided_params, "mock_method", format_tags) == expected
    )


@pytest.mark.parametrize(
    "provided_params",
    [
        ({"RequiredParameter": None}),
        ({"OptionalParameter": "present"}),
        ({}),
    ],
)
@patch(mod_name + ".get_boto3_client_method_parameters")
@patch(mod_name + ".get_rds_method_attribute")
def test_format_rds_client_method_parameters_failure(
    m_get_rds_method_attribute, m_get_boto3_client_method_parameters, provided_params
):
    module = MagicMock()
    client = MagicMock()
    m_get_boto3_client_method_parameters.return_value = ["RequiredParameter"]
    m_get_rds_method_attribute.return_value = rds.Boto3ClientMethod("mock_method", None, "mock method", None, None)

    rds.format_rds_client_method_parameters(client, module, provided_params, "mock_method", False)
    module.fail_json.assert_called_with(msg="To mock method requires the parameters: ['RequiredParameter']")


class TestRdsUtils:
    # ========================================================
    # Setup some initial data that we can use within our tests
    # ========================================================
    def setup_method(self):
        self.target_role_list = [
            {"role_arn": "role_won", "feature_name": "s3Export"},
            {"role_arn": "role_too", "feature_name": "Lambda"},
            {"role_arn": "role_thrie", "feature_name": "s3Import"},
        ]

    # ========================================================
    #   rds.compare_iam_roles
    # ========================================================

    def test_compare_iam_roles_equal(self):
        existing_list = self.target_role_list
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, self.target_role_list, purge_roles=False)
        assert [] == roles_to_add
        assert [] == roles_to_delete
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, self.target_role_list, purge_roles=True)
        assert [] == roles_to_add
        assert [] == roles_to_delete

    def test_compare_iam_roles_empty_arr_existing(self):
        roles_to_add, roles_to_delete = rds.compare_iam_roles([], self.target_role_list, purge_roles=False)
        assert self.target_role_list == roles_to_add
        assert [] == roles_to_delete
        roles_to_add, roles_to_delete = rds.compare_iam_roles([], self.target_role_list, purge_roles=True)
        assert self.target_role_list, roles_to_add
        assert [] == roles_to_delete

    def test_compare_iam_roles_empty_arr_target(self):
        existing_list = self.target_role_list
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, [], purge_roles=False)
        assert [] == roles_to_add
        assert [] == roles_to_delete
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, [], purge_roles=True)
        assert [] == roles_to_add
        assert self.target_role_list == roles_to_delete

    def test_compare_iam_roles_different(self):
        existing_list = [{"role_arn": "role_wonn", "feature_name": "s3Export"}]
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, self.target_role_list, purge_roles=False)
        assert self.target_role_list == roles_to_add
        assert [] == roles_to_delete
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, self.target_role_list, purge_roles=True)
        assert self.target_role_list == roles_to_add
        assert existing_list == roles_to_delete

        existing_list = self.target_role_list.copy()
        self.target_role_list = [{"role_arn": "role_wonn", "feature_name": "s3Export"}]
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, self.target_role_list, purge_roles=False)
        assert self.target_role_list == roles_to_add
        assert [] == roles_to_delete
        roles_to_add, roles_to_delete = rds.compare_iam_roles(existing_list, self.target_role_list, purge_roles=True)
        assert self.target_role_list == roles_to_add
        assert existing_list == roles_to_delete

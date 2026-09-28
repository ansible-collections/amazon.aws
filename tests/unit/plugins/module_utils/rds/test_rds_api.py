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
    pass

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.rds import Boto3ClientMethod
from ansible_collections.amazon.aws.plugins.module_utils.rds import call_method
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_final_identifier
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_snapshot
from ansible_collections.amazon.aws.plugins.module_utils.rds import handle_errors
from ansible_collections.amazon.aws.plugins.module_utils.rds import update_iam_roles

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_rds_api.py requires the python modules 'boto3' and 'botocore'")

mod_api = "ansible_collections.amazon.aws.plugins.module_utils._rds.api"


def helper_expected(x):
    return x, nullcontext()


def helper_error(*args, **kwargs):
    return MagicMock(), pytest.raises(*args, **kwargs)


def build_exception(operation_name, code=None, message=None, http_status_code=None, error=True):
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

    assert get_final_identifier(method_name, module) == expected


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
    assert handle_errors(MagicMock(), exception, method_name, {}) == expected


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
        handle_errors(module, exception, method_name, {"Engine": "fake_engine"})
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
@patch(mod_api + ".describe_db_snapshots")
@patch(mod_api + ".describe_db_cluster_snapshots")
def test_get_snapshot_success(
    m_describe_db_cluster_snapshots, m_describe_db_snapshots, snapshots, snapshot_type, convert_tags, expected
):
    client = MagicMock()
    sentinel = [{"WRONG_MOCK": True}]
    if snapshot_type == "cluster":
        m_describe_db_cluster_snapshots.return_value = snapshots
        m_describe_db_snapshots.return_value = sentinel
    else:
        m_describe_db_snapshots.return_value = snapshots
        m_describe_db_cluster_snapshots.return_value = sentinel
    assert get_snapshot(client, "my-snapshot", snapshot_type, convert_tags) == expected
    if snapshot_type == "cluster":
        m_describe_db_snapshots.assert_not_called()
    else:
        m_describe_db_cluster_snapshots.assert_not_called()


def test_get_snapshot_error():
    client = MagicMock()
    with pytest.raises(ValueError) as e:
        get_snapshot(client, "my-snapshot", "bad parameter")
    assert "Invalid snapshot_type. Expected one of: ('cluster', 'instance')" in str(e)


# =============================================================================
# get_final_identifier — cluster_snapshot path
# =============================================================================


def test__get_final_identifier_cluster_snapshot():
    module = MagicMock()
    module.params = {"db_cluster_snapshot_identifier": "my-cluster-snap", "new_db_cluster_identifier": "x"}
    module.check_mode = False

    assert get_final_identifier("create_db_cluster_snapshot", module) == "my-cluster-snap"


def test__get_final_identifier_check_mode_ignores_updated():
    module = MagicMock()
    module.params = {
        "db_instance_identifier": "original",
        "new_db_instance_identifier": "updated",
        "apply_immediately": True,
    }
    module.check_mode = True

    assert get_final_identifier("create_db_instance", module) == "original"


def test__get_final_identifier_unsupported_method():
    module = MagicMock()
    module.params = {"wait": False}

    with pytest.raises(NotImplementedError):
        get_final_identifier("unsupported_method", module)


# =============================================================================
# handle_errors — additional paths
# =============================================================================


def test__handle_errors_botocore_error():
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    exception = botocore.exceptions.BotoCoreError()

    with pytest.raises(SystemExit):
        handle_errors(module, exception, "some_method", {"Param": "value"})

    module.fail_json_aws.assert_called_once()
    assert "Unexpected failure" in module.fail_json_aws.call_args[1]["msg"]


def test__handle_errors_modify_db_cluster():
    exception = build_exception(
        "modify_db_cluster",
        code="InvalidParameterCombination",
        message="No modifications were requested",
    )
    assert handle_errors(MagicMock(), exception, "modify_db_cluster", {}) is False


def test__handle_errors_generic_error_code():
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    module.params = {"new_db_instance_identifier": "test"}
    exception = build_exception("delete_db_instance", code="SomeRandomError")

    with pytest.raises(SystemExit):
        handle_errors(module, exception, "delete_db_instance", {})

    module.fail_json_aws.assert_called_once()
    assert "Unable to" in module.fail_json_aws.call_args[1]["msg"]


def test__handle_errors_create_cluster_valid_engine():
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    module.params = {"new_db_cluster_identifier": "test"}
    exception = build_exception("create_db_cluster", code="InvalidParameterValue")

    with pytest.raises(SystemExit):
        handle_errors(module, exception, "create_db_cluster", {"Engine": "aurora-mysql"})

    module.fail_json_aws.assert_called_once()
    assert "Unable to" in module.fail_json_aws.call_args[1]["msg"]


# =============================================================================
# call_method
# =============================================================================


@patch(mod_api + ".get_rds_method_attribute")
def test__call_method_check_mode(m_get_attr):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = True

    result, changed = call_method(client, module, "create_db_instance", {"DBInstanceIdentifier": "test"})

    assert result == {}
    assert changed is True
    m_get_attr.assert_not_called()


@patch(mod_api + ".wait_for_status")
@patch(mod_api + ".get_rds_method_attribute")
def test__call_method_success_no_wait(m_get_attr, m_wait):
    m_get_attr.return_value = Boto3ClientMethod("create_db_instance", "", "create DB instance", "instance", [])
    client = MagicMock()
    client.create_db_instance.return_value = {"DBInstance": {"DBInstanceIdentifier": "test"}}
    module = MagicMock()
    module.check_mode = False
    module.params = {"wait": False}

    result, changed = call_method(client, module, "create_db_instance", {"DBInstanceIdentifier": "test"})

    assert changed is True
    m_wait.assert_not_called()


@patch(mod_api + ".get_final_identifier")
@patch(mod_api + ".wait_for_status")
@patch(mod_api + ".get_rds_method_attribute")
def test__call_method_success_with_wait(m_get_attr, m_wait, m_get_final):
    m_get_attr.return_value = Boto3ClientMethod("create_db_instance", "", "create DB instance", "instance", [])
    m_get_final.return_value = "test"
    client = MagicMock()
    client.create_db_instance.return_value = {"DBInstance": {"DBInstanceIdentifier": "test"}}
    module = MagicMock()
    module.check_mode = False
    module.params = {"wait": True}

    result, changed = call_method(client, module, "create_db_instance", {"DBInstanceIdentifier": "test"})

    assert changed is True
    m_wait.assert_called_once_with(client, module, "test", "create_db_instance")


@patch(mod_api + ".handle_errors")
@patch(mod_api + ".get_rds_method_attribute")
def test__call_method_error_delegates_to_handle_errors(m_get_attr, m_handle):
    m_get_attr.return_value = Boto3ClientMethod("modify_db_instance", "", "modify DB instance", "instance", [])
    m_handle.return_value = False
    client = MagicMock()
    client.modify_db_instance.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "InvalidParameterCombination", "Message": "No modifications were requested"}},
        "ModifyDBInstance",
    )
    module = MagicMock()
    module.check_mode = False
    module.params = {"wait": False}

    result, changed = call_method(client, module, "modify_db_instance", {"DBInstanceIdentifier": "test"})

    assert changed is False
    m_handle.assert_called_once()


# =============================================================================
# update_iam_roles
# =============================================================================


@patch(mod_api + ".call_method")
def test__update_iam_roles_add_and_remove(m_call_method):
    m_call_method.return_value = ({}, True)
    client = MagicMock()
    module = MagicMock()
    roles_to_add = [{"role_arn": "arn:aws:iam::123:role/new", "feature_name": "s3Import"}]
    roles_to_remove = [{"role_arn": "arn:aws:iam::123:role/old", "feature_name": "s3Export"}]

    result = update_iam_roles(client, module, "my-instance", roles_to_add, roles_to_remove)

    assert result is True
    assert m_call_method.call_count == 2
    remove_call = m_call_method.call_args_list[0]
    assert remove_call[1]["method_name"] == "remove_role_from_db_instance"
    add_call = m_call_method.call_args_list[1]
    assert add_call[1]["method_name"] == "add_role_to_db_instance"


@patch(mod_api + ".call_method")
def test__update_iam_roles_changed_accumulates(m_call_method):
    m_call_method.side_effect = [({}, True), ({}, False)]
    client = MagicMock()
    module = MagicMock()
    roles_to_add = [{"role_arn": "arn:aws:iam::123:role/new", "feature_name": "s3Import"}]
    roles_to_remove = [{"role_arn": "arn:aws:iam::123:role/old", "feature_name": "s3Export"}]

    result = update_iam_roles(client, module, "my-instance", roles_to_add, roles_to_remove)

    assert result is True


@patch(mod_api + ".call_method")
def test__update_iam_roles_no_changes(m_call_method):
    m_call_method.return_value = ({}, False)
    client = MagicMock()
    module = MagicMock()

    result = update_iam_roles(client, module, "my-instance", [], [])

    assert result is False
    m_call_method.assert_not_called()


@patch(mod_api + ".call_method")
def test__update_iam_roles_add_only(m_call_method):
    m_call_method.return_value = ({}, True)
    client = MagicMock()
    module = MagicMock()
    roles_to_add = [{"role_arn": "arn:aws:iam::123:role/new", "feature_name": "s3Import"}]

    result = update_iam_roles(client, module, "my-instance", roles_to_add, [])

    assert result is True
    m_call_method.assert_called_once()
    assert m_call_method.call_args[1]["method_name"] == "add_role_to_db_instance"

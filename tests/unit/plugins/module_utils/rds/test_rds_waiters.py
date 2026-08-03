# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.rds import Boto3ClientMethod
from ansible_collections.amazon.aws.plugins.module_utils.rds import wait_for_cluster_snapshot_status
from ansible_collections.amazon.aws.plugins.module_utils.rds import wait_for_cluster_status
from ansible_collections.amazon.aws.plugins.module_utils.rds import wait_for_instance_snapshot_status
from ansible_collections.amazon.aws.plugins.module_utils.rds import wait_for_instance_status
from ansible_collections.amazon.aws.plugins.module_utils.rds import wait_for_status

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_rds_waiters.py requires the python modules 'boto3' and 'botocore'")

mod_waiters = "ansible_collections.amazon.aws.plugins.module_utils._rds.waiters"


# =============================================================================
# wait_for_instance_snapshot_status
# =============================================================================


@pytest.mark.parametrize("waiter_name", ["", "db_snapshot_available"])
def test__wait_for_instance_snapshot_status(waiter_name):
    wait_for_instance_snapshot_status(MagicMock(), MagicMock(), "test", waiter_name)


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

    wait_for_instance_snapshot_status(client, module, "test", waiter_name)
    module.fail_json_aws.assert_called_once()
    assert module.fail_json_aws.call_args[1]["msg"] == expected


def test__wait_for_instance_snapshot_status_botocore_error():
    client = MagicMock()
    client.get_waiter.return_value.wait.side_effect = botocore.exceptions.BotoCoreError()
    module = MagicMock()

    wait_for_instance_snapshot_status(client, module, "test-snap", "db_snapshot_available")
    module.fail_json_aws.assert_called_once()
    assert "unexpected error" in module.fail_json_aws.call_args[1]["msg"].lower()


# =============================================================================
# wait_for_cluster_snapshot_status
# =============================================================================


@pytest.mark.parametrize("waiter_name", ["", "db_cluster_snapshot_available"])
def test__wait_for_cluster_snapshot_status(waiter_name):
    wait_for_cluster_snapshot_status(MagicMock(), MagicMock(), "test", waiter_name)


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

    wait_for_cluster_snapshot_status(client, module, "test", waiter_name)
    module.fail_json_aws.assert_called_once()
    assert module.fail_json_aws.call_args[1]["msg"] == expected


def test__wait_for_cluster_snapshot_status_botocore_error():
    client = MagicMock()
    client.get_waiter.return_value.wait.side_effect = botocore.exceptions.BotoCoreError()
    module = MagicMock()

    wait_for_cluster_snapshot_status(client, module, "test-snap", "db_cluster_snapshot_available")
    module.fail_json_aws.assert_called_once()
    assert "unexpected error" in module.fail_json_aws.call_args[1]["msg"].lower()


# =============================================================================
# wait_for_cluster_status
# =============================================================================


@patch(mod_waiters + ".get_waiter")
def test__wait_for_cluster_status_success(m_get_waiter):
    client = MagicMock()
    module = MagicMock()

    wait_for_cluster_status(client, module, "my-cluster", "cluster_available")

    m_get_waiter.assert_called_once_with(client, "cluster_available")
    m_get_waiter.return_value.wait.assert_called_once_with(DBClusterIdentifier="my-cluster")
    module.fail_json_aws.assert_not_called()


@patch(mod_waiters + ".get_waiter")
def test__wait_for_cluster_status_deleted_waiter_error(m_get_waiter):
    m_get_waiter.return_value.wait.side_effect = botocore.exceptions.WaiterError(None, None, None)
    module = MagicMock()

    wait_for_cluster_status(MagicMock(), module, "my-cluster", "cluster_deleted")

    module.fail_json_aws.assert_called_once()
    assert "deleted" in module.fail_json_aws.call_args[1]["msg"]


@patch(mod_waiters + ".get_waiter")
def test__wait_for_cluster_status_available_waiter_error(m_get_waiter):
    m_get_waiter.return_value.wait.side_effect = botocore.exceptions.WaiterError(None, None, None)
    module = MagicMock()

    wait_for_cluster_status(MagicMock(), module, "my-cluster", "cluster_available")

    module.fail_json_aws.assert_called_once()
    assert "available" in module.fail_json_aws.call_args[1]["msg"]


@patch(mod_waiters + ".get_waiter")
def test__wait_for_cluster_status_botocore_error(m_get_waiter):
    m_get_waiter.return_value.wait.side_effect = botocore.exceptions.BotoCoreError()
    module = MagicMock()

    wait_for_cluster_status(MagicMock(), module, "my-cluster", "cluster_available")

    module.fail_json_aws.assert_called_once()
    assert "unexpected error" in module.fail_json_aws.call_args[1]["msg"].lower()


# =============================================================================
# wait_for_instance_status
# =============================================================================


@patch(mod_waiters + ".get_waiter")
def test__wait_for_instance_status_success(m_get_waiter):
    client = MagicMock()
    # client.get_waiter raises ValueError so it falls back to module_utils waiter
    client.get_waiter.side_effect = ValueError("unknown waiter")
    module = MagicMock()

    wait_for_instance_status(client, module, "my-instance", "db_instance_available")

    m_get_waiter.assert_called_with(client, "db_instance_available")
    module.fail_json_aws.assert_not_called()


def test__wait_for_instance_status_success_boto3_waiter():
    client = MagicMock()
    module = MagicMock()

    wait_for_instance_status(client, module, "my-instance", "db_instance_available")

    client.get_waiter.assert_called_with("db_instance_available")
    module.fail_json_aws.assert_not_called()


def test__wait_for_instance_status_waiter_error_not_found_retries():
    client = MagicMock()
    not_found_error = botocore.exceptions.WaiterError(None, None, None)
    not_found_error.last_response = {"Error": {"Code": "DBInstanceNotFound"}}

    success_on_second = [not_found_error, None]
    client.get_waiter.return_value.wait.side_effect = success_on_second
    module = MagicMock()

    wait_for_instance_status(client, module, "my-instance", "db_instance_available")

    assert client.get_waiter.return_value.wait.call_count == 2
    module.fail_json_aws.assert_not_called()


def test__wait_for_instance_status_waiter_error_other_fails():
    client = MagicMock()
    other_error = botocore.exceptions.WaiterError(None, None, None)
    other_error.last_response = {"Error": {"Code": "SomeOtherError"}}

    client.get_waiter.return_value.wait.side_effect = other_error
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        wait_for_instance_status(client, module, "my-instance", "db_instance_available")

    module.fail_json_aws.assert_called_once()
    assert "available" in module.fail_json_aws.call_args[1]["msg"]


def test__wait_for_instance_status_deleted_status_message():
    client = MagicMock()
    other_error = botocore.exceptions.WaiterError(None, None, None)
    other_error.last_response = {"Error": {"Code": "SomeOtherError"}}

    client.get_waiter.return_value.wait.side_effect = other_error
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        wait_for_instance_status(client, module, "my-instance", "db_instance_deleted")

    module.fail_json_aws.assert_called_once()
    assert "deleted" in module.fail_json_aws.call_args[1]["msg"]


def test__wait_for_instance_status_botocore_error():
    client = MagicMock()
    client.get_waiter.return_value.wait.side_effect = botocore.exceptions.BotoCoreError()
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        wait_for_instance_status(client, module, "my-instance", "db_instance_available")

    module.fail_json_aws.assert_called_once()
    assert "unexpected error" in module.fail_json_aws.call_args[1]["msg"].lower()


# =============================================================================
# wait_for_status (dispatcher)
# =============================================================================


@pytest.mark.parametrize(
    "resource, expected_func",
    [
        ("cluster", "wait_for_cluster_status"),
        ("instance", "wait_for_instance_status"),
        ("instance_snapshot", "wait_for_instance_snapshot_status"),
        ("cluster_snapshot", "wait_for_cluster_snapshot_status"),
    ],
)
@patch(mod_waiters + ".get_rds_method_attribute")
def test__wait_for_status_dispatches(m_get_attr, resource, expected_func):
    m_get_attr.return_value = Boto3ClientMethod(
        name="test_method",
        waiter="test_waiter",
        operation_description="test",
        resource=resource,
        retry_codes=[],
    )
    client = MagicMock()
    module = MagicMock()

    with patch(mod_waiters + "." + expected_func) as m_wait_func:
        wait_for_status(client, module, "test-id", "test_method")
        m_wait_func.assert_called_once_with(client, module, "test-id", "test_waiter")

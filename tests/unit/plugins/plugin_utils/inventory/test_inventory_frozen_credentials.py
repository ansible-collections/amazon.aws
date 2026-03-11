# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call

import botocore.exceptions
import pytest

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import AnsibleBotocoreError


def test_freeze_iam_role_success(monkeypatch):
    """Test _freeze_iam_role successfully assumes role and sets credentials."""
    inventory_plugin = utils_inventory.AWSInventoryBase()
    inventory_plugin.ansible_name = "test_plugin"

    mock_client = MagicMock(name="sts_client")
    mock_client.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIA12345EXAMPLE12345",
            "SecretAccessKey": "ExampleSecretKey123456789ABCDEFGHEXAMPLE",
            "SessionToken": "ExampleSessionToken123456789EXAMPLE",
        }
    }

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    test_role_arn = "arn:aws:iam::123456789012:role/test-role"
    inventory_plugin._freeze_iam_role(test_role_arn)

    # Verify client was called for sts
    assert mock_get_client.call_args == call("sts")

    # Verify assume_role was called with correct parameters
    assert mock_client.assume_role.call_args == call(
        RoleArn=test_role_arn, RoleSessionName="ansible_aws_test_plugin_dynamic_inventory"
    )

    # Verify frozen credentials were set correctly
    assert inventory_plugin._frozen_credentials == {
        "profile_name": None,
        "aws_access_key_id": "AKIA12345EXAMPLE12345",
        "aws_secret_access_key": "ExampleSecretKey123456789ABCDEFGHEXAMPLE",
        "aws_session_token": "ExampleSessionToken123456789EXAMPLE",
    }


def test_freeze_iam_role_client_error(monkeypatch):
    """Test _freeze_iam_role when assume_role raises ClientError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    test_error = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "User is not authorised"}},
        operation_name="AssumeRole",
    )

    mock_client = MagicMock(name="sts_client")
    mock_client.assume_role.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_fail_aws = MagicMock(name="fail_aws")
    mock_fail_aws.side_effect = Exception("fail_aws called")
    monkeypatch.setattr(inventory_plugin, "fail_aws", mock_fail_aws)

    test_role_arn = "arn:aws:iam::123456789012:role/test-role"

    with pytest.raises(Exception, match="fail_aws called"):
        inventory_plugin._freeze_iam_role(test_role_arn)

    # Verify fail_aws was called with the error
    assert mock_fail_aws.call_count == 1
    call_args = mock_fail_aws.call_args
    assert "Unable to assume role" in call_args[0][0]
    assert test_role_arn in call_args[0][0]
    assert "exception" in call_args[1]
    assert call_args[1]["exception"] is test_error


def test_freeze_iam_role_botocore_error(monkeypatch):
    """Test _freeze_iam_role when assume_role raises BotoCoreError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    test_error = botocore.exceptions.BotoCoreError()

    mock_client = MagicMock(name="sts_client")
    mock_client.assume_role.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_fail_aws = MagicMock(name="fail_aws")
    mock_fail_aws.side_effect = Exception("fail_aws called")
    monkeypatch.setattr(inventory_plugin, "fail_aws", mock_fail_aws)

    test_role_arn = "arn:aws:iam::123456789012:role/test-role"

    with pytest.raises(Exception, match="fail_aws called"):
        inventory_plugin._freeze_iam_role(test_role_arn)

    # Verify fail_aws was called with the error
    assert mock_fail_aws.call_count == 1
    call_args = mock_fail_aws.call_args
    assert "Unable to assume role" in call_args[0][0]
    assert test_role_arn in call_args[0][0]
    assert "exception" in call_args[1]
    assert call_args[1]["exception"] is test_error


def test_freeze_iam_role_ansible_botocore_error(monkeypatch):
    """Test _freeze_iam_role when assume_role raises AnsibleBotocoreError."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    test_error = AnsibleBotocoreError("Configuration error")

    mock_client = MagicMock(name="sts_client")
    mock_client.assume_role.side_effect = test_error

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_fail_aws = MagicMock(name="fail_aws")
    mock_fail_aws.side_effect = Exception("fail_aws called")
    monkeypatch.setattr(inventory_plugin, "fail_aws", mock_fail_aws)

    test_role_arn = "arn:aws:iam::123456789012:role/test-role"

    with pytest.raises(Exception, match="fail_aws called"):
        inventory_plugin._freeze_iam_role(test_role_arn)

    # Verify fail_aws was called with the error
    assert mock_fail_aws.call_count == 1
    call_args = mock_fail_aws.call_args
    assert "Unable to assume role" in call_args[0][0]
    assert test_role_arn in call_args[0][0]
    assert "exception" in call_args[1]
    assert call_args[1]["exception"] is test_error


def test_freeze_iam_role_missing_credentials(monkeypatch):
    """Test _freeze_iam_role when assume_role returns no credentials."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_client = MagicMock(name="sts_client")
    # Return response without Credentials key
    mock_client.assume_role.return_value = {}

    mock_get_client = MagicMock(name="client")
    mock_get_client.return_value = mock_client
    monkeypatch.setattr(inventory_plugin, "client", mock_get_client)

    mock_fail_aws = MagicMock(name="fail_aws")
    mock_fail_aws.side_effect = Exception("fail_aws called")
    monkeypatch.setattr(inventory_plugin, "fail_aws", mock_fail_aws)

    test_role_arn = "arn:aws:iam::123456789012:role/test-role"

    with pytest.raises(Exception, match="fail_aws called"):
        inventory_plugin._freeze_iam_role(test_role_arn)

    # Verify fail_aws was called
    assert mock_fail_aws.call_count == 1
    call_args = mock_fail_aws.call_args
    assert "Unable to assume role" in call_args[0][0]
    assert test_role_arn in call_args[0][0]


def test_set_frozen_credentials_with_role(monkeypatch):
    """Test _set_frozen_credentials when assume_role_arn is provided."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    test_role_arn = "arn:aws:iam::123456789012:role/test-role"
    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = test_role_arn
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    mock_freeze_iam_role = MagicMock(name="_freeze_iam_role")
    monkeypatch.setattr(inventory_plugin, "_freeze_iam_role", mock_freeze_iam_role)

    inventory_plugin._set_frozen_credentials()

    # Verify get_option was called
    assert mock_get_option.call_args == call("assume_role_arn")

    # Verify _freeze_iam_role was called with the role ARN
    assert mock_freeze_iam_role.call_args == call(test_role_arn)


def test_set_frozen_credentials_without_role(monkeypatch):
    """Test _set_frozen_credentials when assume_role_arn is not provided."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    mock_get_option = MagicMock(name="get_option")
    mock_get_option.return_value = None
    monkeypatch.setattr(inventory_plugin, "get_option", mock_get_option)

    mock_freeze_iam_role = MagicMock(name="_freeze_iam_role")
    monkeypatch.setattr(inventory_plugin, "_freeze_iam_role", mock_freeze_iam_role)

    inventory_plugin._set_frozen_credentials()

    # Verify get_option was called
    assert mock_get_option.call_args == call("assume_role_arn")

    # Verify _freeze_iam_role was NOT called
    assert mock_freeze_iam_role.call_count == 0

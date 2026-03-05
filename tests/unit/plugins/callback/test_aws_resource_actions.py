# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.callback.aws_resource_actions import CallbackModule


@pytest.fixture(name="callback")
def fixture_callback():
    """Create a CallbackModule instance for testing."""
    callback = CallbackModule()
    callback._display = MagicMock()
    return callback


class TestCallbackModuleInit:
    """Test CallbackModule initialization."""

    def test_init(self):
        """Test that the callback module initializes with an empty list."""
        callback = CallbackModule()
        assert callback.aws_resource_actions == []
        assert callback.CALLBACK_VERSION == 2.8
        assert callback.CALLBACK_TYPE == "aggregate"
        assert callback.CALLBACK_NAME == "amazon.aws.aws_resource_actions"
        assert callback.CALLBACK_NEEDS_WHITELIST is True


class TestExtendAwsResourceActions:
    """Test extend_aws_resource_actions method."""

    def test_extend_with_resource_actions(self, callback):
        """Test extending the list when resource_actions are present."""
        result = {"resource_actions": ["s3:PutObject", "s3:GetObject"]}
        callback.extend_aws_resource_actions(result)
        assert callback.aws_resource_actions == ["s3:PutObject", "s3:GetObject"]

    def test_extend_with_additional_actions(self, callback):
        """Test extending an existing list with additional actions."""
        callback.aws_resource_actions = ["s3:PutObject"]
        result = {"resource_actions": ["s3:GetObject", "s3:DeleteObject"]}
        callback.extend_aws_resource_actions(result)
        assert callback.aws_resource_actions == ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]

    def test_extend_without_resource_actions(self, callback):
        """Test that the list is not modified when resource_actions are absent."""
        result = {"other_key": "other_value"}
        callback.extend_aws_resource_actions(result)
        assert callback.aws_resource_actions == []

    def test_extend_with_empty_resource_actions(self, callback):
        """Test extending with an empty resource_actions list."""
        result = {"resource_actions": []}
        callback.extend_aws_resource_actions(result)
        assert callback.aws_resource_actions == []


class TestRunnerCallbacks:
    """Test runner callback methods."""

    def test_runner_on_ok(self, callback):
        """Test runner_on_ok calls extend_aws_resource_actions."""
        host = MagicMock()
        res = {"resource_actions": ["s3:PutObject"]}
        callback.runner_on_ok(host, res)
        assert callback.aws_resource_actions == ["s3:PutObject"]

    def test_runner_on_failed(self, callback):
        """Test runner_on_failed calls extend_aws_resource_actions."""
        host = MagicMock()
        res = {"resource_actions": ["s3:DeleteObject"]}
        callback.runner_on_failed(host, res)
        assert callback.aws_resource_actions == ["s3:DeleteObject"]

    def test_runner_on_failed_with_ignore_errors(self, callback):
        """Test runner_on_failed with ignore_errors parameter."""
        host = MagicMock()
        res = {"resource_actions": ["s3:GetObject"]}
        callback.runner_on_failed(host, res, ignore_errors=True)
        assert callback.aws_resource_actions == ["s3:GetObject"]

    def test_v2_runner_item_on_ok(self, callback):
        """Test v2_runner_item_on_ok calls extend_aws_resource_actions."""
        result = MagicMock()
        result._result = {"resource_actions": ["ec2:DescribeInstances"]}
        callback.v2_runner_item_on_ok(result)
        assert callback.aws_resource_actions == ["ec2:DescribeInstances"]

    def test_v2_runner_item_on_failed(self, callback):
        """Test v2_runner_item_on_failed calls extend_aws_resource_actions."""
        result = MagicMock()
        result._result = {"resource_actions": ["ec2:RunInstances"]}
        callback.v2_runner_item_on_failed(result)
        assert callback.aws_resource_actions == ["ec2:RunInstances"]


class TestPlaybookOnStats:
    """Test playbook_on_stats method."""

    def test_playbook_on_stats_with_actions(self, callback):
        """Test that stats display sorted, deduplicated actions."""
        callback.aws_resource_actions = ["s3:PutObject", "s3:GetObject", "s3:PutObject"]
        stats = MagicMock()
        callback.playbook_on_stats(stats)

        # Verify the list is sorted and deduplicated
        assert callback.aws_resource_actions == ["s3:GetObject", "s3:PutObject"]

        # Verify display was called with the correct message
        callback._display.display.assert_called_once_with("AWS ACTIONS: ['s3:GetObject', 's3:PutObject']")

    def test_playbook_on_stats_without_actions(self, callback):
        """Test that nothing is displayed when there are no actions."""
        callback.aws_resource_actions = []
        stats = MagicMock()
        callback.playbook_on_stats(stats)

        # Verify display was not called
        callback._display.display.assert_not_called()

    def test_playbook_on_stats_with_duplicates(self, callback):
        """Test that duplicate actions are removed."""
        callback.aws_resource_actions = [
            "s3:PutObject",
            "s3:GetObject",
            "s3:PutObject",
            "s3:DeleteObject",
            "s3:GetObject",
        ]
        stats = MagicMock()
        callback.playbook_on_stats(stats)

        # Verify duplicates are removed and sorted
        assert callback.aws_resource_actions == ["s3:DeleteObject", "s3:GetObject", "s3:PutObject"]
        callback._display.display.assert_called_once()

    def test_playbook_on_stats_sorting(self, callback):
        """Test that actions are sorted alphabetically."""
        callback.aws_resource_actions = ["s3:PutObject", "ec2:RunInstances", "iam:GetUser", "s3:GetObject"]
        stats = MagicMock()
        callback.playbook_on_stats(stats)

        expected = ["ec2:RunInstances", "iam:GetUser", "s3:GetObject", "s3:PutObject"]
        assert callback.aws_resource_actions == expected
        callback._display.display.assert_called_once_with(f"AWS ACTIONS: {expected}")


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_full_playbook_workflow(self, callback):
        """Test a complete workflow simulating a playbook run."""
        # Simulate multiple task executions
        callback.runner_on_ok(MagicMock(), {"resource_actions": ["s3:PutObject", "s3:GetObject"]})
        callback.runner_on_ok(MagicMock(), {"resource_actions": ["s3:DeleteObject"]})
        callback.runner_on_failed(MagicMock(), {"resource_actions": ["ec2:DescribeInstances"]})

        result = MagicMock()
        result._result = {"resource_actions": ["iam:GetUser", "s3:PutObject"]}
        callback.v2_runner_item_on_ok(result)

        # Simulate playbook completion
        callback.playbook_on_stats(MagicMock())

        # Verify final result is sorted and deduplicated
        expected = ["ec2:DescribeInstances", "iam:GetUser", "s3:DeleteObject", "s3:GetObject", "s3:PutObject"]
        assert callback.aws_resource_actions == expected

    def test_mixed_success_and_failure(self, callback):
        """Test collecting actions from both successful and failed tasks."""
        callback.runner_on_ok(MagicMock(), {"resource_actions": ["s3:CreateBucket"]})
        callback.runner_on_failed(MagicMock(), {"resource_actions": ["s3:DeleteBucket"]})

        result_ok = MagicMock()
        result_ok._result = {"resource_actions": ["s3:ListBuckets"]}
        callback.v2_runner_item_on_ok(result_ok)

        result_failed = MagicMock()
        result_failed._result = {"resource_actions": ["s3:HeadBucket"]}
        callback.v2_runner_item_on_failed(result_failed)

        callback.playbook_on_stats(MagicMock())

        expected = ["s3:CreateBucket", "s3:DeleteBucket", "s3:HeadBucket", "s3:ListBuckets"]
        assert callback.aws_resource_actions == expected

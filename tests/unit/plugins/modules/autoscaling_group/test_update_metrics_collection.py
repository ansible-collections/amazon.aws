# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestUpdateMetricsCollection:
    def test_no_change_needed_metrics_disabled(self):
        """Test when metrics are disabled and should stay disabled"""
        connection = MagicMock()
        changed = asg_module.update_metrics_collection(
            connection=connection,
            group_name="test-asg",
            current_metrics=[],
            metrics_collection=False,
            metrics_granularity="1Minute",
            metrics_list=["GroupMinSize", "GroupMaxSize"],
        )

        assert changed is False
        connection.enable_metrics_collection.assert_not_called()
        connection.disable_metrics_collection.assert_not_called()

    def test_no_change_needed_metrics_enabled(self):
        """Test when metrics are enabled and should stay enabled with same metrics"""
        connection = MagicMock()
        current_metrics = [
            {"Metric": "GroupMinSize", "Granularity": "1Minute"},
            {"Metric": "GroupMaxSize", "Granularity": "1Minute"},
        ]
        changed = asg_module.update_metrics_collection(
            connection=connection,
            group_name="test-asg",
            current_metrics=current_metrics,
            metrics_collection=True,
            metrics_granularity="1Minute",
            metrics_list=["GroupMinSize", "GroupMaxSize"],
        )

        assert changed is False
        connection.enable_metrics_collection.assert_not_called()
        connection.disable_metrics_collection.assert_not_called()

    def test_enable_metrics(self):
        """Test enabling metrics when currently disabled"""
        connection = MagicMock()
        changed = asg_module.update_metrics_collection(
            connection=connection,
            group_name="test-asg",
            current_metrics=[],
            metrics_collection=True,
            metrics_granularity="1Minute",
            metrics_list=["GroupMinSize", "GroupMaxSize"],
        )

        assert changed is True
        connection.enable_metrics_collection.assert_called_once()
        connection.disable_metrics_collection.assert_not_called()

    def test_disable_metrics(self):
        """Test disabling metrics when currently enabled"""
        connection = MagicMock()
        current_metrics = [
            {"Metric": "GroupMinSize", "Granularity": "1Minute"},
            {"Metric": "GroupMaxSize", "Granularity": "1Minute"},
        ]
        changed = asg_module.update_metrics_collection(
            connection=connection,
            group_name="test-asg",
            current_metrics=current_metrics,
            metrics_collection=False,
            metrics_granularity="1Minute",
            metrics_list=["GroupMinSize", "GroupMaxSize"],
        )

        assert changed is True
        connection.disable_metrics_collection.assert_called_once()
        connection.enable_metrics_collection.assert_not_called()

    def test_change_metrics_list(self):
        """Test changing which metrics are collected"""
        connection = MagicMock()
        current_metrics = [
            {"Metric": "GroupMinSize", "Granularity": "1Minute"},
            {"Metric": "GroupMaxSize", "Granularity": "1Minute"},
        ]
        changed = asg_module.update_metrics_collection(
            connection=connection,
            group_name="test-asg",
            current_metrics=current_metrics,
            metrics_collection=True,
            metrics_granularity="1Minute",
            metrics_list=["GroupDesiredCapacity", "GroupInServiceInstances"],
        )

        assert changed is True
        connection.enable_metrics_collection.assert_called_once()
        connection.disable_metrics_collection.assert_not_called()

    def test_no_change_order_difference(self):
        """Test that metric list order doesn't affect idempotency"""
        connection = MagicMock()
        current_metrics = [
            {"Metric": "GroupMaxSize", "Granularity": "1Minute"},
            {"Metric": "GroupMinSize", "Granularity": "1Minute"},
        ]
        changed = asg_module.update_metrics_collection(
            connection=connection,
            group_name="test-asg",
            current_metrics=current_metrics,
            metrics_collection=True,
            metrics_granularity="1Minute",
            metrics_list=["GroupMinSize", "GroupMaxSize"],
        )

        assert changed is False
        connection.enable_metrics_collection.assert_not_called()
        connection.disable_metrics_collection.assert_not_called()

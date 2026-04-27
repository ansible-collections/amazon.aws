# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._autoscaling import transformations


class TestSortMetrics:
    """Test suite for _sort_metrics helper function."""

    def test_none_metrics(self):
        """Test with None metrics"""
        result = transformations._sort_metrics(None)
        assert result is None

    def test_empty_metrics_list(self):
        """Test with empty metrics list"""
        result = transformations._sort_metrics([])
        assert result == []

    def test_single_metric(self):
        """Test with single metric"""
        # Metrics after boto3_resource_to_ansible_dict have lowercase keys
        metrics = [{"metric": "GroupInServiceInstances", "granularity": "1Minute"}]
        result = transformations._sort_metrics(metrics)
        # Should have both snake_case and CamelCase keys for backwards compatibility
        assert result == [
            {
                "metric": "GroupInServiceInstances",
                "granularity": "1Minute",
                "Metric": "GroupInServiceInstances",
                "Granularity": "1Minute",
            }
        ]

    def test_already_sorted_metrics(self):
        """Test with already sorted metrics"""
        # Metrics after boto3_resource_to_ansible_dict have lowercase keys
        metrics = [
            {"metric": "GroupDesiredCapacity", "granularity": "1Minute"},
            {"metric": "GroupInServiceInstances", "granularity": "1Minute"},
            {"metric": "GroupMaxSize", "granularity": "1Minute"},
        ]
        result = transformations._sort_metrics(metrics)
        # Should have both snake_case and CamelCase keys for backwards compatibility
        assert result == [
            {
                "metric": "GroupDesiredCapacity",
                "granularity": "1Minute",
                "Metric": "GroupDesiredCapacity",
                "Granularity": "1Minute",
            },
            {
                "metric": "GroupInServiceInstances",
                "granularity": "1Minute",
                "Metric": "GroupInServiceInstances",
                "Granularity": "1Minute",
            },
            {
                "metric": "GroupMaxSize",
                "granularity": "1Minute",
                "Metric": "GroupMaxSize",
                "Granularity": "1Minute",
            },
        ]

    def test_unsorted_metrics(self):
        """Test sorting unsorted metrics"""
        # Metrics after boto3_resource_to_ansible_dict have lowercase keys
        metrics = [
            {"metric": "GroupMaxSize", "granularity": "1Minute"},
            {"metric": "GroupDesiredCapacity", "granularity": "1Minute"},
            {"metric": "GroupInServiceInstances", "granularity": "1Minute"},
        ]
        result = transformations._sort_metrics(metrics)
        # Should have both snake_case and CamelCase keys for backwards compatibility
        assert result == [
            {
                "metric": "GroupDesiredCapacity",
                "granularity": "1Minute",
                "Metric": "GroupDesiredCapacity",
                "Granularity": "1Minute",
            },
            {
                "metric": "GroupInServiceInstances",
                "granularity": "1Minute",
                "Metric": "GroupInServiceInstances",
                "Granularity": "1Minute",
            },
            {
                "metric": "GroupMaxSize",
                "granularity": "1Minute",
                "Metric": "GroupMaxSize",
                "Granularity": "1Minute",
            },
        ]

    def test_sorts_by_metric_name_alphabetically(self):
        """Test that sorting is alphabetical by metric key"""
        metrics = [
            {"metric": "Z-Metric"},
            {"metric": "A-Metric"},
            {"metric": "M-Metric"},
        ]
        result = transformations._sort_metrics(metrics)
        # Should have both snake_case and CamelCase keys for backwards compatibility
        assert result == [
            {"metric": "A-Metric", "Metric": "A-Metric"},
            {"metric": "M-Metric", "Metric": "M-Metric"},
            {"metric": "Z-Metric", "Metric": "Z-Metric"},
        ]

    def test_handles_missing_metric_key(self):
        """Test handling metrics without metric key"""
        metrics = [
            {"metric": "B-Metric"},
            {"no_metric_key": "value"},
            {"metric": "A-Metric"},
        ]
        result = transformations._sort_metrics(metrics)
        # Item without 'metric' key should sort to beginning (empty string)
        assert result[0] == {"no_metric_key": "value"}
        assert result[1]["metric"] == "A-Metric"
        assert result[2]["metric"] == "B-Metric"

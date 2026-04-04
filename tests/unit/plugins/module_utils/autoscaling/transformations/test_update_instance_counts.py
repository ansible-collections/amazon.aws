# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._autoscaling import transformations


class TestUpdateInstanceCounts:
    """Test suite for _update_instance_counts helper function."""

    def test_viable_instance_counts(self):
        """Test counting viable instances (Healthy + InService)."""
        counts = {
            "viable_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "in_service_instances": 0,
            "terminating_instances": 0,
            "pending_instances": 0,
        }

        instance = {
            "HealthStatus": "Healthy",
            "LifecycleState": "InService",
        }

        transformations._update_instance_counts(instance, counts)

        assert counts["viable_instances"] == 1
        assert counts["healthy_instances"] == 1
        assert counts["unhealthy_instances"] == 0
        assert counts["in_service_instances"] == 1

    def test_healthy_but_not_in_service(self):
        """Test that healthy but not InService doesn't count as viable."""
        counts = {
            "viable_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "in_service_instances": 0,
            "terminating_instances": 0,
            "pending_instances": 0,
        }

        instance = {
            "HealthStatus": "Healthy",
            "LifecycleState": "Pending",
        }

        transformations._update_instance_counts(instance, counts)

        assert counts["viable_instances"] == 0  # Not viable (not InService)
        assert counts["healthy_instances"] == 1
        assert counts["in_service_instances"] == 0
        assert counts["pending_instances"] == 1

    def test_in_service_but_unhealthy(self):
        """Test that InService but unhealthy doesn't count as viable."""
        counts = {
            "viable_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "in_service_instances": 0,
            "terminating_instances": 0,
            "pending_instances": 0,
        }

        instance = {
            "HealthStatus": "Unhealthy",
            "LifecycleState": "InService",
        }

        transformations._update_instance_counts(instance, counts)

        assert counts["viable_instances"] == 0  # Not viable (not Healthy)
        assert counts["healthy_instances"] == 0
        assert counts["unhealthy_instances"] == 1
        assert counts["in_service_instances"] == 1

    def test_terminating_instance(self):
        """Test counting terminating instances."""
        counts = {
            "viable_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "in_service_instances": 0,
            "terminating_instances": 0,
            "pending_instances": 0,
        }

        instance = {
            "HealthStatus": "Unhealthy",
            "LifecycleState": "Terminating",
        }

        transformations._update_instance_counts(instance, counts)

        assert counts["viable_instances"] == 0
        assert counts["unhealthy_instances"] == 1
        assert counts["terminating_instances"] == 1
        assert counts["in_service_instances"] == 0
        assert counts["pending_instances"] == 0

    def test_multiple_instances(self):
        """Test accumulation across multiple instances."""
        counts = {
            "viable_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "in_service_instances": 0,
            "terminating_instances": 0,
            "pending_instances": 0,
        }

        # Add 3 viable instances
        for _dummy in range(3):
            transformations._update_instance_counts(
                {"HealthStatus": "Healthy", "LifecycleState": "InService"},
                counts,
            )

        # Add 1 pending instance
        transformations._update_instance_counts(
            {"HealthStatus": "Healthy", "LifecycleState": "Pending"},
            counts,
        )

        # Add 1 terminating instance
        transformations._update_instance_counts(
            {"HealthStatus": "Unhealthy", "LifecycleState": "Terminating"},
            counts,
        )

        assert counts["viable_instances"] == 3
        assert counts["healthy_instances"] == 4
        assert counts["unhealthy_instances"] == 1
        assert counts["in_service_instances"] == 3
        assert counts["pending_instances"] == 1
        assert counts["terminating_instances"] == 1

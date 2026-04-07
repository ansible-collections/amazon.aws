# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.module_utils._autoscaling.transformations as transformations


class TestProcessAsgInstances:
    """Test suite for _process_asg_instances helper function."""

    def test_empty_instances_list(self):
        """Test processing empty instances list"""
        instance_ids, instance_facts, count_stats = transformations._process_asg_instances([])

        assert instance_ids == []
        assert instance_facts == {}
        assert count_stats == {
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "in_service_instances": 0,
            "terminating_instances": 0,
            "pending_instances": 0,
            "viable_instances": 0,
        }

    def test_single_healthy_instance(self):
        """Test processing single healthy in-service instance"""
        instances = [
            {
                "InstanceId": "i-123",
                "HealthStatus": "Healthy",
                "LifecycleState": "InService",
                "LaunchConfigurationName": "my-lc",
            }
        ]

        instance_ids, instance_facts, count_stats = transformations._process_asg_instances(instances)

        assert instance_ids == ["i-123"]
        assert instance_facts == {
            "i-123": {
                "health_status": "Healthy",
                "lifecycle_state": "InService",
                "launch_config_name": "my-lc",
            }
        }
        assert count_stats["viable_instances"] == 1
        assert count_stats["healthy_instances"] == 1
        assert count_stats["in_service_instances"] == 1

    def test_multiple_instances_mixed_states(self):
        """Test processing multiple instances with different states"""
        instances = [
            {
                "InstanceId": "i-123",
                "HealthStatus": "Healthy",
                "LifecycleState": "InService",
                "LaunchConfigurationName": "my-lc",
            },
            {
                "InstanceId": "i-456",
                "HealthStatus": "Unhealthy",
                "LifecycleState": "Pending",
                "LaunchTemplate": {"LaunchTemplateId": "lt-789", "Version": "1"},
            },
            {
                "InstanceId": "i-789",
                "HealthStatus": "Healthy",
                "LifecycleState": "Terminating",
                "LaunchConfigurationName": "my-lc",
            },
        ]

        instance_ids, instance_facts, count_stats = transformations._process_asg_instances(instances)

        assert instance_ids == ["i-123", "i-456", "i-789"]
        assert len(instance_facts) == 3
        assert "i-123" in instance_facts
        assert "i-456" in instance_facts
        assert "i-789" in instance_facts
        assert count_stats == {
            "healthy_instances": 2,
            "unhealthy_instances": 1,
            "in_service_instances": 1,
            "terminating_instances": 1,
            "pending_instances": 1,
            "viable_instances": 1,  # Only i-123 is viable (healthy + in-service)
        }

    def test_instance_facts_structure(self):
        """Test that instance facts have correct structure"""
        instances = [
            {
                "InstanceId": "i-123",
                "HealthStatus": "Healthy",
                "LifecycleState": "InService",
                "LaunchTemplate": {"LaunchTemplateId": "lt-123", "Version": "$Latest"},
            }
        ]

        _, instance_facts, _ = transformations._process_asg_instances(instances)

        assert instance_facts["i-123"]["health_status"] == "Healthy"
        assert instance_facts["i-123"]["lifecycle_state"] == "InService"
        assert instance_facts["i-123"]["launch_template"]["LaunchTemplateId"] == "lt-123"

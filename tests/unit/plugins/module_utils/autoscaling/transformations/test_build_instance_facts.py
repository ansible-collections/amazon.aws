# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.module_utils._autoscaling.transformations as transformations


class TestBuildInstanceFacts:
    """Test suite for _build_instance_facts helper function."""

    def test_basic_instance_with_launch_config(self):
        """Test building facts for instance with launch configuration."""
        instance = {
            "HealthStatus": "Healthy",
            "LifecycleState": "InService",
            "LaunchConfigurationName": "my-lc-v1",
        }

        facts = transformations._build_instance_facts(instance)

        assert facts == {
            "health_status": "Healthy",
            "lifecycle_state": "InService",
            "launch_config_name": "my-lc-v1",
        }

    def test_instance_with_launch_template(self):
        """Test building facts for instance with launch template."""
        instance = {
            "HealthStatus": "Unhealthy",
            "LifecycleState": "Pending",
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-123456",
                "LaunchTemplateName": "my-lt",
                "Version": "2",
            },
        }

        facts = transformations._build_instance_facts(instance)

        assert facts == {
            "health_status": "Unhealthy",
            "lifecycle_state": "Pending",
            "launch_template": {
                "LaunchTemplateId": "lt-123456",
                "LaunchTemplateName": "my-lt",
                "Version": "2",
            },
        }

    def test_instance_without_launch_spec(self):
        """Test building facts for instance without launch config or template."""
        instance = {
            "HealthStatus": "Healthy",
            "LifecycleState": "Terminating",
        }

        facts = transformations._build_instance_facts(instance)

        assert facts == {
            "health_status": "Healthy",
            "lifecycle_state": "Terminating",
        }

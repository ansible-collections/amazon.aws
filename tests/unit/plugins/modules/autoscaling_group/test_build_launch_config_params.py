# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError


class TestBuildLaunchConfigParams:
    def test_launch_configuration_name(self):
        """Test with LaunchConfigurationName in launch_object"""
        launch_object = {"LaunchConfigurationName": "my-launch-config"}
        result = asg_module.build_launch_config_params(launch_object, None)

        assert result == {"LaunchConfigurationName": "my-launch-config"}

    def test_launch_template_without_mixed_policy(self):
        """Test with LaunchTemplate but no MixedInstancesPolicy"""
        launch_object = {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-123456",
                "Version": "1",
            }
        }
        result = asg_module.build_launch_config_params(launch_object, None)

        assert result == {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-123456",
                "Version": "1",
            }
        }

    def test_launch_template_with_mixed_policy(self):
        """Test with LaunchTemplate and MixedInstancesPolicy"""
        launch_object = {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-123456",
                "Version": "1",
            },
            "MixedInstancesPolicy": {
                "LaunchTemplate": {
                    "LaunchTemplateSpecification": {
                        "LaunchTemplateId": "lt-123456",
                        "Version": "1",
                    },
                    "Overrides": [
                        {"InstanceType": "t3.micro"},
                        {"InstanceType": "t3a.micro"},
                    ],
                }
            },
        }
        result = asg_module.build_launch_config_params(launch_object, None)

        assert result == {
            "MixedInstancesPolicy": {
                "LaunchTemplate": {
                    "LaunchTemplateSpecification": {
                        "LaunchTemplateId": "lt-123456",
                        "Version": "1",
                    },
                    "Overrides": [
                        {"InstanceType": "t3.micro"},
                        {"InstanceType": "t3a.micro"},
                    ],
                }
            }
        }

    def test_use_existing_launch_configuration_name(self):
        """Test using existing ASG's LaunchConfigurationName when launch_object is empty"""
        launch_object = {}
        as_group = {
            "LaunchConfigurationName": "existing-launch-config",
            "AutoScalingGroupName": "test-asg",
        }
        result = asg_module.build_launch_config_params(launch_object, as_group)

        assert result == {"LaunchConfigurationName": "existing-launch-config"}

    def test_use_existing_launch_template(self):
        """Test using existing ASG's LaunchTemplate when launch_object is empty"""
        launch_object = {}
        as_group = {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-existing",
                "LaunchTemplateName": "existing-template",
                "Version": "2",
            },
            "AutoScalingGroupName": "test-asg",
        }
        result = asg_module.build_launch_config_params(launch_object, as_group)

        assert result == {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-existing",
                "Version": "2",
            }
        }

    def test_missing_launch_config_raises_error(self):
        """Test that missing launch config raises AnsibleAWSError"""
        launch_object = {}
        as_group = None

        with pytest.raises(AnsibleAWSError, match="Missing LaunchConfigurationName or LaunchTemplate"):
            asg_module.build_launch_config_params(launch_object, as_group)

    def test_missing_launch_config_empty_as_group_raises_error(self):
        """Test that missing launch config with empty as_group raises AnsibleAWSError"""
        launch_object = {}
        as_group = {"AutoScalingGroupName": "test-asg"}

        with pytest.raises(AnsibleAWSError, match="Missing LaunchConfigurationName or LaunchTemplate"):
            asg_module.build_launch_config_params(launch_object, as_group)

    def test_prefers_launch_template_id_over_name(self):
        """Test that LaunchTemplateId is used and LaunchTemplateName is excluded"""
        launch_object = {}
        as_group = {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-abc123",
                "LaunchTemplateName": "template-name",
                "Version": "3",
            }
        }
        result = asg_module.build_launch_config_params(launch_object, as_group)

        # Should only include LaunchTemplateId and Version, not LaunchTemplateName
        assert result == {
            "LaunchTemplate": {
                "LaunchTemplateId": "lt-abc123",
                "Version": "3",
            }
        }
        assert "LaunchTemplateName" not in result["LaunchTemplate"]

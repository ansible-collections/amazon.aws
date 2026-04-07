# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.module_utils._autoscaling.transformations as transformations


class TestTransformAutoscalingGroup:
    """Test suite for transform_autoscaling_group function."""

    def test_minimal_asg(self):
        """Test transformation of minimal ASG with required fields only"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 3,
            "Instances": [],
            "TargetGroupNames": [],
        }

        result = transformations.transform_autoscaling_group(asg)

        assert result["auto_scaling_group_name"] == "test-asg"
        assert result["min_size"] == 1
        assert result["max_size"] == 5
        assert result["desired_capacity"] == 3
        assert result["instances"] == []
        assert result["instance_facts"] == {}
        assert result["target_group_names"] == []
        assert result["viable_instances"] == 0
        assert result["healthy_instances"] == 0

    def test_asg_with_instances(self):
        """Test transformation with instances"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 2,
            "MaxSize": 10,
            "DesiredCapacity": 5,
            "Instances": [
                {
                    "InstanceId": "i-123",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchConfigurationName": "lc-1",
                },
                {
                    "InstanceId": "i-456",
                    "HealthStatus": "Unhealthy",
                    "LifecycleState": "Pending",
                    "LaunchTemplate": {"LaunchTemplateId": "lt-789", "Version": "2"},
                },
            ],
            "TargetGroupNames": ["tg-1", "tg-2"],
        }

        result = transformations.transform_autoscaling_group(asg)

        assert result["instances"] == ["i-123", "i-456"]
        assert len(result["instance_facts"]) == 2
        assert result["instance_facts"]["i-123"]["health_status"] == "Healthy"
        assert result["instance_facts"]["i-123"]["lifecycle_state"] == "InService"
        assert result["instance_facts"]["i-456"]["health_status"] == "Unhealthy"
        assert result["instance_facts"]["i-456"]["lifecycle_state"] == "Pending"
        assert result["viable_instances"] == 1  # Only i-123 is viable
        assert result["healthy_instances"] == 1
        assert result["unhealthy_instances"] == 1
        assert result["target_group_names"] == ["tg-1", "tg-2"]

    def test_asg_with_mixed_instances_policy(self):
        """Test transformation with mixed instances policy"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 3,
            "Instances": [],
            "MixedInstancesPolicy": {
                "LaunchTemplate": {
                    "Overrides": [
                        {"InstanceType": "t3.micro"},
                        {"InstanceType": "t3.small"},
                        {"InstanceType": "t3.medium"},
                    ]
                }
            },
            "TargetGroupNames": [],
        }

        result = transformations.transform_autoscaling_group(asg)

        assert result["mixed_instances_policy"] == ["t3.micro", "t3.small", "t3.medium"]

    def test_asg_with_metrics(self):
        """Test transformation with unsorted metrics"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 3,
            "Instances": [],
            # boto3 returns EnabledMetrics
            "EnabledMetrics": [
                {"Metric": "GroupMaxSize", "Granularity": "1Minute"},
                {"Metric": "GroupDesiredCapacity", "Granularity": "1Minute"},
                {"Metric": "GroupInServiceInstances", "Granularity": "1Minute"},
            ],
            "TargetGroupNames": [],
        }

        result = transformations.transform_autoscaling_group(asg)

        # boto3_resource_to_ansible_dict transforms EnabledMetrics to enabled_metrics,
        # then _sort_metrics sorts it and stores as metrics_collection
        # Metrics should be sorted alphabetically (after snake_case conversion)
        assert result["metrics_collection"] is not None
        assert len(result["metrics_collection"]) == 3
        assert result["metrics_collection"][0]["metric"] == "GroupDesiredCapacity"
        assert result["metrics_collection"][1]["metric"] == "GroupInServiceInstances"
        assert result["metrics_collection"][2]["metric"] == "GroupMaxSize"

    def test_asg_with_tags(self):
        """Test transformation converts tag keys to snake_case"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 3,
            "Instances": [],
            "Tags": [
                {"Key": "Environment", "Value": "production", "PropagateAtLaunch": True},
                {"Key": "Application", "Value": "web", "PropagateAtLaunch": False},
            ],
            "TargetGroupNames": [],
        }

        result = transformations.transform_autoscaling_group(asg)

        # boto3_resource_to_ansible_dict transforms keys to snake_case even with transform_tags=False
        # transform_tags=False means it won't transform the tags list structure, but dict keys still get converted
        assert len(result["tags"]) == 2
        assert result["tags"][0]["key"] == "Environment"
        assert result["tags"][0]["value"] == "production"
        assert result["tags"][0]["propagate_at_launch"] is True
        assert result["tags"][1]["key"] == "Application"
        assert result["tags"][1]["value"] == "web"
        assert result["tags"][1]["propagate_at_launch"] is False

    def test_asg_complete_transformation(self):
        """Test complete transformation with all fields"""
        asg = {
            "AutoScalingGroupName": "production-asg",
            "AutoScalingGroupARN": "arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:xxx",
            "MinSize": 2,
            "MaxSize": 10,
            "DesiredCapacity": 5,
            "DefaultCooldown": 300,
            "AvailabilityZones": ["us-east-1a", "us-east-1b"],
            "LoadBalancerNames": ["elb-1"],
            "TargetGroupARNs": ["arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-1/abc"],
            "TargetGroupNames": ["tg-1"],
            "HealthCheckType": "ELB",
            "HealthCheckGracePeriod": 300,
            "Instances": [
                {
                    "InstanceId": "i-123",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchConfigurationName": "lc-1",
                }
            ],
            "CreatedTime": "2024-01-01T00:00:00Z",
            "SuspendedProcesses": [],
            "PlacementGroup": "my-placement-group",
            "VPCZoneIdentifier": "subnet-123,subnet-456",
            "EnabledMetrics": [{"Metric": "GroupInServiceInstances", "Granularity": "1Minute"}],
            "Tags": [{"Key": "Name", "Value": "production-asg"}],
            "TerminationPolicies": ["Default"],
            "NewInstancesProtectedFromScaleIn": False,
        }

        result = transformations.transform_autoscaling_group(asg)

        # Check CamelCase to snake_case conversion
        assert result["auto_scaling_group_name"] == "production-asg"
        assert result["auto_scaling_group_arn"] == "arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:xxx"
        assert result["default_cooldown"] == 300
        assert result["health_check_type"] == "ELB"
        assert result["health_check_grace_period"] == 300
        assert result["vpc_zone_identifier"] == "subnet-123,subnet-456"
        assert result["new_instances_protected_from_scale_in"] is False

        # Check computed fields
        assert result["instances"] == ["i-123"]
        assert result["viable_instances"] == 1
        assert result["healthy_instances"] == 1

        # Check target group names
        assert result["target_group_names"] == ["tg-1"]

    def test_transformation_does_not_modify_original(self):
        """Test that transformation doesn't modify the original ASG dict"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 3,
            "Instances": [],
            "TargetGroupNames": [],
        }

        original_asg = asg.copy()
        transformations.transform_autoscaling_group(asg)

        # Original should be unchanged
        assert asg == original_asg

    def test_instances_as_ids_true(self):
        """Test that instances_as_ids=True returns instance IDs in instances field"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 2,
            "Instances": [
                {
                    "InstanceId": "i-123",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchConfigurationName": "lc-1",
                },
                {
                    "InstanceId": "i-456",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchTemplate": {"LaunchTemplateId": "lt-789", "Version": "1"},
                },
            ],
            "TargetGroupNames": [],
        }

        result = transformations.transform_autoscaling_group(asg, instances_as_ids=True)

        # instances should be list of IDs
        assert result["instances"] == ["i-123", "i-456"]
        assert isinstance(result["instances"][0], str)

        # instance_ids should also be list of IDs
        assert result["instance_ids"] == ["i-123", "i-456"]

        # instance_details should be list of dicts
        assert len(result["instance_details"]) == 2
        assert isinstance(result["instance_details"][0], dict)
        assert result["instance_details"][0]["instance_id"] == "i-123"
        assert result["instance_details"][1]["instance_id"] == "i-456"

    def test_instances_as_ids_false(self):
        """Test that instances_as_ids=False returns full instance dicts in instances field"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 2,
            "Instances": [
                {
                    "InstanceId": "i-123",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchConfigurationName": "lc-1",
                },
                {
                    "InstanceId": "i-456",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "Pending",
                    "LaunchTemplate": {"LaunchTemplateId": "lt-789", "Version": "1"},
                },
            ],
            "TargetGroupNames": [],
        }

        result = transformations.transform_autoscaling_group(asg, instances_as_ids=False)

        # instances should be list of dicts
        assert len(result["instances"]) == 2
        assert isinstance(result["instances"][0], dict)
        assert result["instances"][0]["instance_id"] == "i-123"
        assert result["instances"][1]["instance_id"] == "i-456"

        # instance_ids should still be list of IDs
        assert result["instance_ids"] == ["i-123", "i-456"]
        assert isinstance(result["instance_ids"][0], str)

        # instance_details should match instances
        assert result["instance_details"] == result["instances"]

    def test_instances_as_ids_default(self):
        """Test that instances_as_ids defaults to True"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 1,
            "Instances": [
                {
                    "InstanceId": "i-789",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchConfigurationName": "lc-1",
                },
            ],
            "TargetGroupNames": [],
        }

        # Call without specifying instances_as_ids (should default to True)
        result = transformations.transform_autoscaling_group(asg)

        # instances should be list of IDs (default behavior)
        assert result["instances"] == ["i-789"]
        assert isinstance(result["instances"][0], str)

    def test_instances_fields_always_present(self):
        """Test that instance_ids and instance_details are always present regardless of instances_as_ids"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 5,
            "DesiredCapacity": 1,
            "Instances": [
                {
                    "InstanceId": "i-999",
                    "HealthStatus": "Healthy",
                    "LifecycleState": "InService",
                    "LaunchConfigurationName": "lc-1",
                },
            ],
            "TargetGroupNames": [],
        }

        # Test with instances_as_ids=True
        result_true = transformations.transform_autoscaling_group(asg, instances_as_ids=True)
        assert "instances" in result_true
        assert "instance_ids" in result_true
        assert "instance_details" in result_true
        assert "instance_facts" in result_true

        # Test with instances_as_ids=False
        result_false = transformations.transform_autoscaling_group(asg, instances_as_ids=False)
        assert "instances" in result_false
        assert "instance_ids" in result_false
        assert "instance_details" in result_false
        assert "instance_facts" in result_false

    def test_instances_empty_list_both_modes(self):
        """Test that empty instances list works correctly with both instances_as_ids values"""
        asg = {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 0,
            "MaxSize": 5,
            "DesiredCapacity": 0,
            "Instances": [],
            "TargetGroupNames": [],
        }

        # Test with instances_as_ids=True
        result_true = transformations.transform_autoscaling_group(asg, instances_as_ids=True)
        assert result_true["instances"] == []
        assert result_true["instance_ids"] == []
        assert result_true["instance_details"] == []

        # Test with instances_as_ids=False
        result_false = transformations.transform_autoscaling_group(asg, instances_as_ids=False)
        assert result_false["instances"] == []
        assert result_false["instance_ids"] == []
        assert result_false["instance_details"] == []

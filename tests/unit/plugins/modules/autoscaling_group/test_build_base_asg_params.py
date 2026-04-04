# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestBuildBaseAsgParams:
    def test_required_params_only(self):
        """Test with only required parameters"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=10,
            desired_capacity=5,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=["Default"],
            protected_from_scale_in=False,
        )

        assert result == {
            "AutoScalingGroupName": "test-asg",
            "MinSize": 1,
            "MaxSize": 10,
            "DesiredCapacity": 5,
            "HealthCheckGracePeriod": 300,
            "HealthCheckType": "EC2",
            "DefaultCooldown": 300,
            "TerminationPolicies": ["Default"],
            "NewInstancesProtectedFromScaleIn": False,
        }

    def test_with_vpc_zone_identifier(self):
        """Test with VPC zone identifier"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=2,
            max_size=8,
            desired_capacity=4,
            health_check_period=300,
            health_check_type="ELB",
            default_cooldown=300,
            termination_policies=["OldestInstance"],
            protected_from_scale_in=True,
            vpc_zone_identifier="subnet-abc123,subnet-def456",
        )

        assert result["VPCZoneIdentifier"] == "subnet-abc123,subnet-def456"
        assert "AvailabilityZones" not in result

    def test_with_availability_zones(self):
        """Test with availability zones"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=5,
            desired_capacity=3,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=["Default"],
            protected_from_scale_in=False,
            availability_zones=["us-east-1a", "us-east-1b"],
        )

        assert result["AvailabilityZones"] == ["us-east-1a", "us-east-1b"]
        assert "VPCZoneIdentifier" not in result

    def test_with_max_instance_lifetime(self):
        """Test with max instance lifetime"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=10,
            desired_capacity=5,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=["Default"],
            protected_from_scale_in=False,
            max_instance_lifetime=604800,
        )

        assert result["MaxInstanceLifetime"] == 604800

    def test_with_max_instance_lifetime_zero(self):
        """Test with max instance lifetime set to 0 (removes restriction)"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=10,
            desired_capacity=5,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=["Default"],
            protected_from_scale_in=False,
            max_instance_lifetime=0,
        )

        assert result["MaxInstanceLifetime"] == 0

    def test_without_max_instance_lifetime(self):
        """Test that MaxInstanceLifetime is not included when None"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=10,
            desired_capacity=5,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=["Default"],
            protected_from_scale_in=False,
            max_instance_lifetime=None,
        )

        assert "MaxInstanceLifetime" not in result

    def test_all_optional_params(self):
        """Test with all optional parameters provided"""
        result = asg_module.build_base_asg_params(
            group_name="full-asg",
            min_size=3,
            max_size=15,
            desired_capacity=7,
            health_check_period=600,
            health_check_type="ELB",
            default_cooldown=600,
            termination_policies=["OldestLaunchConfiguration", "ClosestToNextInstanceHour"],
            protected_from_scale_in=True,
            vpc_zone_identifier="subnet-123,subnet-456,subnet-789",
            availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
            max_instance_lifetime=2592000,
        )

        assert result["AutoScalingGroupName"] == "full-asg"
        assert result["MinSize"] == 3
        assert result["MaxSize"] == 15
        assert result["DesiredCapacity"] == 7
        assert result["HealthCheckGracePeriod"] == 600
        assert result["HealthCheckType"] == "ELB"
        assert result["DefaultCooldown"] == 600
        assert result["TerminationPolicies"] == ["OldestLaunchConfiguration", "ClosestToNextInstanceHour"]
        assert result["NewInstancesProtectedFromScaleIn"] is True
        assert result["VPCZoneIdentifier"] == "subnet-123,subnet-456,subnet-789"
        assert result["AvailabilityZones"] == ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
        assert result["MaxInstanceLifetime"] == 2592000

    def test_protected_from_scale_in_true(self):
        """Test with protected_from_scale_in set to True"""
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=10,
            desired_capacity=5,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=["Default"],
            protected_from_scale_in=True,
        )

        assert result["NewInstancesProtectedFromScaleIn"] is True

    def test_multiple_termination_policies(self):
        """Test with multiple termination policies"""
        policies = ["OldestInstance", "NewestInstance", "OldestLaunchConfiguration"]
        result = asg_module.build_base_asg_params(
            group_name="test-asg",
            min_size=1,
            max_size=10,
            desired_capacity=5,
            health_check_period=300,
            health_check_type="EC2",
            default_cooldown=300,
            termination_policies=policies,
            protected_from_scale_in=False,
        )

        assert result["TerminationPolicies"] == policies

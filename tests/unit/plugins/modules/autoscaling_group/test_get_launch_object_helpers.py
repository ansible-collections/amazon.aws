# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestBuildLaunchTemplateSpec:
    def test_with_requested_version(self):
        """Test with explicitly requested version"""
        lt_data = {
            "LaunchTemplateId": "lt-123456",
            "LaunchTemplateName": "my-template",
            "LatestVersionNumber": 5,
        }
        result = asg_module._build_launch_template_spec(lt_data, "2")

        assert result == {
            "LaunchTemplateId": "lt-123456",
            "Version": "2",
        }

    def test_with_latest_version(self):
        """Test with None version (use latest)"""
        lt_data = {
            "LaunchTemplateId": "lt-789012",
            "LaunchTemplateName": "another-template",
            "LatestVersionNumber": 10,
        }
        result = asg_module._build_launch_template_spec(lt_data, None)

        assert result == {
            "LaunchTemplateId": "lt-789012",
            "Version": "10",
        }

    def test_latest_version_number_conversion(self):
        """Test that latest version number is converted to string"""
        lt_data = {
            "LaunchTemplateId": "lt-abc",
            "LatestVersionNumber": 3,
        }
        result = asg_module._build_launch_template_spec(lt_data, None)

        assert result["Version"] == "3"
        assert isinstance(result["Version"], str)


class TestBuildMixedInstancesPolicy:
    def test_minimal_policy(self):
        """Test policy with only launch template spec"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        policy_params = {}

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        assert result == {
            "LaunchTemplate": {"LaunchTemplateSpecification": {"LaunchTemplateId": "lt-123", "Version": "1"}}
        }

    def test_with_instance_types(self):
        """Test policy with instance types"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        policy_params = {"instance_types": ["t3.micro", "t3.small", "t3a.micro"]}

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        assert result["LaunchTemplate"]["LaunchTemplateSpecification"] == lt_spec
        assert result["LaunchTemplate"]["Overrides"] == [
            {"InstanceType": "t3.micro"},
            {"InstanceType": "t3.small"},
            {"InstanceType": "t3a.micro"},
        ]

    def test_with_empty_instance_types(self):
        """Test that empty instance_types list doesn't create Overrides"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        policy_params = {"instance_types": []}

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        assert "Overrides" not in result["LaunchTemplate"]

    def test_with_instances_distribution(self):
        """Test policy with instances distribution"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        policy_params = {
            "instances_distribution": {
                "on_demand_allocation_strategy": "prioritized",
                "on_demand_base_capacity": 1,
                "on_demand_percentage_above_base_capacity": 50,
                "spot_allocation_strategy": "lowest-price",
                "spot_instance_pools": 2,
                "spot_max_price": "0.10",
            }
        }

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        assert "InstancesDistribution" in result
        dist = result["InstancesDistribution"]
        assert dist["OnDemandAllocationStrategy"] == "prioritized"
        assert dist["OnDemandBaseCapacity"] == 1
        assert dist["OnDemandPercentageAboveBaseCapacity"] == 50
        assert dist["SpotAllocationStrategy"] == "lowest-price"
        assert dist["SpotInstancePools"] == 2
        assert dist["SpotMaxPrice"] == "0.10"

    def test_with_empty_instances_distribution(self):
        """Test that empty instances_distribution doesn't create InstancesDistribution"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        policy_params = {"instances_distribution": {}}

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        assert "InstancesDistribution" not in result

    def test_with_both_instance_types_and_distribution(self):
        """Test policy with both instance types and distribution"""
        lt_spec = {"LaunchTemplateId": "lt-456", "Version": "2"}
        policy_params = {
            "instance_types": ["m5.large", "m5a.large"],
            "instances_distribution": {
                "on_demand_base_capacity": 2,
                "spot_allocation_strategy": "capacity-optimized",
            },
        }

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        assert len(result["LaunchTemplate"]["Overrides"]) == 2
        assert result["LaunchTemplate"]["Overrides"][0]["InstanceType"] == "m5.large"
        assert result["LaunchTemplate"]["Overrides"][1]["InstanceType"] == "m5a.large"
        assert result["InstancesDistribution"]["OnDemandBaseCapacity"] == 2
        assert result["InstancesDistribution"]["SpotAllocationStrategy"] == "capacity-optimized"

    def test_instances_distribution_none_parameters_scrubbed(self):
        """Test that None values are scrubbed from instances distribution"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        policy_params = {
            "instances_distribution": {
                "on_demand_base_capacity": 1,
                "spot_max_price": None,  # This should be scrubbed
            }
        }

        result = asg_module._build_mixed_instances_policy(lt_spec, policy_params)

        dist = result["InstancesDistribution"]
        assert "OnDemandBaseCapacity" in dist
        assert "SpotMaxPrice" not in dist  # None value should be scrubbed

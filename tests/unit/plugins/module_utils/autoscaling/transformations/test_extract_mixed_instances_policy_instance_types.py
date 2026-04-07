# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.module_utils._autoscaling.transformations as transformations


class TestExtractMixedInstancesPolicyInstanceTypes:
    """Test suite for _extract_mixed_instances_policy_instance_types helper function."""

    def test_none_policy(self):
        """Test with None policy"""
        result = transformations._extract_mixed_instances_policy_instance_types(None)
        assert result == []

    def test_empty_policy(self):
        """Test with empty policy dict"""
        result = transformations._extract_mixed_instances_policy_instance_types({})
        assert result == []

    def test_policy_without_overrides(self):
        """Test with policy but no overrides"""
        policy = {"LaunchTemplate": {}}
        result = transformations._extract_mixed_instances_policy_instance_types(policy)
        assert result == []

    def test_policy_with_empty_overrides(self):
        """Test with policy with empty overrides list"""
        policy = {"LaunchTemplate": {"Overrides": []}}
        result = transformations._extract_mixed_instances_policy_instance_types(policy)
        assert result == []

    def test_policy_with_single_instance_type(self):
        """Test with policy containing single instance type"""
        policy = {"LaunchTemplate": {"Overrides": [{"InstanceType": "t3.micro"}]}}
        result = transformations._extract_mixed_instances_policy_instance_types(policy)
        assert result == ["t3.micro"]

    def test_policy_with_multiple_instance_types(self):
        """Test with policy containing multiple instance types"""
        policy = {
            "LaunchTemplate": {
                "Overrides": [
                    {"InstanceType": "t3.micro"},
                    {"InstanceType": "t3.small"},
                    {"InstanceType": "t3.medium"},
                ]
            }
        }
        result = transformations._extract_mixed_instances_policy_instance_types(policy)
        assert result == ["t3.micro", "t3.small", "t3.medium"]

    def test_policy_preserves_order(self):
        """Test that instance type order is preserved"""
        policy = {
            "LaunchTemplate": {
                "Overrides": [
                    {"InstanceType": "c5.large"},
                    {"InstanceType": "m5.large"},
                    {"InstanceType": "r5.large"},
                ]
            }
        }
        result = transformations._extract_mixed_instances_policy_instance_types(policy)
        assert result == ["c5.large", "m5.large", "r5.large"]

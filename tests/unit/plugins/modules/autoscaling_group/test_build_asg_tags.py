# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestBuildAsgTags:
    def test_empty_tags(self):
        """Test with empty tag list"""
        result = asg_module.build_asg_tags([], "test-asg")
        assert result == []

    def test_single_tag_with_propagate_true(self):
        """Test single tag with propagate_at_launch=True"""
        tags = [{"Name": "test-instance", "propagate_at_launch": True}]
        result = asg_module.build_asg_tags(tags, "test-asg")

        assert len(result) == 1
        assert result[0]["Key"] == "Name"
        assert result[0]["Value"] == "test-instance"
        assert result[0]["PropagateAtLaunch"] is True
        assert result[0]["ResourceType"] == "auto-scaling-group"
        assert result[0]["ResourceId"] == "test-asg"

    def test_single_tag_with_propagate_false(self):
        """Test single tag with propagate_at_launch=False"""
        tags = [{"Environment": "production", "propagate_at_launch": False}]
        result = asg_module.build_asg_tags(tags, "prod-asg")

        assert len(result) == 1
        assert result[0]["Key"] == "Environment"
        assert result[0]["Value"] == "production"
        assert result[0]["PropagateAtLaunch"] is False
        assert result[0]["ResourceType"] == "auto-scaling-group"
        assert result[0]["ResourceId"] == "prod-asg"

    def test_tag_without_propagate_defaults_to_true(self):
        """Test tag without propagate_at_launch defaults to True"""
        tags = [{"Owner": "team-a"}]
        result = asg_module.build_asg_tags(tags, "test-asg")

        assert len(result) == 1
        assert result[0]["Key"] == "Owner"
        assert result[0]["Value"] == "team-a"
        assert result[0]["PropagateAtLaunch"] is True

    def test_multiple_tags_in_single_dict(self):
        """Test multiple tags in a single dictionary"""
        tags = [{"Name": "instance", "Environment": "dev", "propagate_at_launch": True}]
        result = asg_module.build_asg_tags(tags, "test-asg")

        # Should have 2 tags (propagate_at_launch is not included)
        assert len(result) == 2
        tag_keys = {tag["Key"] for tag in result}
        assert tag_keys == {"Name", "Environment"}

        # All tags should have the same propagate value from the dict
        for tag in result:
            assert tag["PropagateAtLaunch"] is True
            assert tag["ResourceId"] == "test-asg"

    def test_multiple_tag_dicts(self):
        """Test multiple tag dictionaries with different propagate settings"""
        tags = [
            {"Name": "instance", "propagate_at_launch": True},
            {"Environment": "staging", "propagate_at_launch": False},
        ]
        result = asg_module.build_asg_tags(tags, "test-asg")

        assert len(result) == 2

        # Using next() with None default - will fail test if tag not found
        name_tag = next((t for t in result if t["Key"] == "Name"), None)
        assert name_tag is not None
        assert name_tag["Value"] == "instance"
        assert name_tag["PropagateAtLaunch"] is True

        env_tag = next((t for t in result if t["Key"] == "Environment"), None)
        assert env_tag is not None
        assert env_tag["Value"] == "staging"
        assert env_tag["PropagateAtLaunch"] is False

    def test_tag_value_conversion(self):
        """Test that tag values are converted to native strings"""
        tags = [{"Count": 123, "Enabled": True}]
        result = asg_module.build_asg_tags(tags, "test-asg")

        assert len(result) == 2
        # Values should be converted to strings
        count_tag = next((t for t in result if t["Key"] == "Count"), None)
        assert count_tag is not None
        assert count_tag["Value"] == "123"

        enabled_tag = next((t for t in result if t["Key"] == "Enabled"), None)
        assert enabled_tag is not None
        assert enabled_tag["Value"] == "True"

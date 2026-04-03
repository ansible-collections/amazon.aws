# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestCompareAsgTags:
    def test_no_changes_empty_tags(self):
        """Test when both current and desired tags are empty"""
        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags([], [], purge_tags=True)

        assert tags_to_delete == []
        assert tags_to_set is None
        assert changed is False

    def test_no_changes_identical_tags(self):
        """Test when current and desired tags are identical"""
        current_tags = [
            {
                "Key": "Name",
                "Value": "test",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        want_tags = [
            {
                "Key": "Name",
                "Value": "test",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert tags_to_delete == []
        assert tags_to_set is None
        assert changed is False

    def test_add_new_tags(self):
        """Test adding new tags to an ASG"""
        current_tags = []
        want_tags = [
            {
                "Key": "Environment",
                "Value": "production",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert tags_to_delete == []
        assert tags_to_set == want_tags
        assert changed is True

    def test_remove_tags_with_purge(self):
        """Test removing tags when purge_tags=True"""
        current_tags = [
            {
                "Key": "OldTag",
                "Value": "old-value",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        want_tags = []

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert len(tags_to_delete) == 1
        assert tags_to_delete[0]["Key"] == "OldTag"
        # tags_to_set is None because after deletion, have_remaining == want_sorted (both empty)
        assert tags_to_set is None
        assert changed is True

    def test_remove_tags_without_purge(self):
        """Test that tags are NOT removed when purge_tags=False"""
        current_tags = [
            {
                "Key": "OldTag",
                "Value": "old-value",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        want_tags = []

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=False)

        assert tags_to_delete == []
        # tags_to_set is None because have_remaining (empty after filtering keys_to_delete) == want_sorted (empty)
        # Even though we detect changed=True from keys_to_delete, we don't actually update tags
        assert tags_to_set is None
        assert changed is True

    def test_update_tag_value(self):
        """Test updating a tag's value"""
        current_tags = [
            {
                "Key": "Environment",
                "Value": "staging",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        want_tags = [
            {
                "Key": "Environment",
                "Value": "production",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert tags_to_delete == []
        assert tags_to_set == want_tags
        assert changed is True

    def test_update_propagate_at_launch(self):
        """Test updating PropagateAtLaunch without changing key/value"""
        current_tags = [
            {
                "Key": "Name",
                "Value": "test",
                "PropagateAtLaunch": False,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        want_tags = [
            {
                "Key": "Name",
                "Value": "test",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert tags_to_delete == []
        assert tags_to_set == want_tags
        assert changed is True

    def test_mixed_changes(self):
        """Test a mix of adding, removing, and updating tags"""
        current_tags = [
            {
                "Key": "Environment",
                "Value": "staging",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            },
            {
                "Key": "OldTag",
                "Value": "remove-me",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            },
        ]
        want_tags = [
            {
                "Key": "Environment",
                "Value": "production",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            },
            {
                "Key": "NewTag",
                "Value": "new-value",
                "PropagateAtLaunch": False,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            },
        ]

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert len(tags_to_delete) == 1
        assert tags_to_delete[0]["Key"] == "OldTag"
        assert len(tags_to_set) == 2
        assert changed is True

    def test_sorting_handled(self):
        """Test that tags in different order are recognized as identical"""
        current_tags = [
            {"Key": "B", "Value": "b", "PropagateAtLaunch": True},
            {"Key": "A", "Value": "a", "PropagateAtLaunch": True},
        ]
        want_tags = [
            {"Key": "A", "Value": "a", "PropagateAtLaunch": True},
            {"Key": "B", "Value": "b", "PropagateAtLaunch": True},
        ]

        tags_to_delete, tags_to_set, changed = asg_module.compare_asg_tags(current_tags, want_tags, purge_tags=True)

        assert tags_to_delete == []
        assert tags_to_set is None
        assert changed is False

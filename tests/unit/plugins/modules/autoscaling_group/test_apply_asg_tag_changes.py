# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestApplyAsgTagChanges:
    @patch.object(asg_module, "delete_asg_tags")
    @patch.object(asg_module, "create_or_update_asg_tags")
    def test_no_changes_needed(self, mock_create_update, mock_delete):
        """Test when no changes are needed (empty delete list and None for set)"""
        connection = MagicMock()
        changed = asg_module.apply_asg_tag_changes(connection, "test-asg", [], None)

        assert changed is False
        mock_delete.assert_not_called()
        mock_create_update.assert_not_called()

    @patch.object(asg_module, "delete_asg_tags")
    @patch.object(asg_module, "create_or_update_asg_tags")
    def test_only_delete_tags(self, mock_create_update, mock_delete):
        """Test deleting tags without setting new ones"""
        connection = MagicMock()
        tags_to_delete = [
            {
                "Key": "OldTag",
                "Value": "old-value",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        changed = asg_module.apply_asg_tag_changes(connection, "test-asg", tags_to_delete, None)

        assert changed is True
        # Check that delete was called with properly formatted tags
        mock_delete.assert_called_once()
        delete_call_args = mock_delete.call_args[0]
        assert delete_call_args[0] == connection
        delete_tags = delete_call_args[1]
        assert len(delete_tags) == 1
        assert delete_tags[0]["ResourceId"] == "test-asg"
        assert delete_tags[0]["ResourceType"] == "auto-scaling-group"
        assert delete_tags[0]["Key"] == "OldTag"
        assert "Value" not in delete_tags[0]  # Delete format doesn't include Value
        mock_create_update.assert_not_called()

    @patch.object(asg_module, "delete_asg_tags")
    @patch.object(asg_module, "create_or_update_asg_tags")
    def test_only_set_tags(self, mock_create_update, mock_delete):
        """Test setting tags without deleting any"""
        connection = MagicMock()
        tags_to_set = [
            {
                "Key": "NewTag",
                "Value": "new-value",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        changed = asg_module.apply_asg_tag_changes(connection, "test-asg", [], tags_to_set)

        assert changed is True
        mock_delete.assert_not_called()
        mock_create_update.assert_called_once_with(connection, tags_to_set)

    @patch.object(asg_module, "delete_asg_tags")
    @patch.object(asg_module, "create_or_update_asg_tags")
    def test_delete_and_set_tags(self, mock_create_update, mock_delete):
        """Test both deleting and setting tags"""
        connection = MagicMock()
        tags_to_delete = [
            {
                "Key": "OldTag",
                "Value": "old-value",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        tags_to_set = [
            {
                "Key": "NewTag",
                "Value": "new-value",
                "PropagateAtLaunch": False,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        changed = asg_module.apply_asg_tag_changes(connection, "test-asg", tags_to_delete, tags_to_set)

        assert changed is True
        mock_delete.assert_called_once()
        mock_create_update.assert_called_once_with(connection, tags_to_set)

    @patch.object(asg_module, "delete_asg_tags")
    @patch.object(asg_module, "create_or_update_asg_tags")
    def test_multiple_tags_to_delete(self, mock_create_update, mock_delete):
        """Test deleting multiple tags"""
        connection = MagicMock()
        tags_to_delete = [
            {
                "Key": "Tag1",
                "Value": "value1",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            },
            {
                "Key": "Tag2",
                "Value": "value2",
                "PropagateAtLaunch": False,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            },
        ]

        changed = asg_module.apply_asg_tag_changes(connection, "test-asg", tags_to_delete, None)

        assert changed is True
        mock_delete.assert_called_once()
        delete_call_args = mock_delete.call_args[0]
        delete_tags = delete_call_args[1]
        assert len(delete_tags) == 2
        # Verify both tags are in the delete list
        delete_keys = {tag["Key"] for tag in delete_tags}
        assert delete_keys == {"Tag1", "Tag2"}

    @patch.object(asg_module, "delete_asg_tags")
    @patch.object(asg_module, "create_or_update_asg_tags")
    def test_delete_tag_format(self, mock_create_update, mock_delete):
        """Test that delete tags are formatted correctly (no Value/PropagateAtLaunch)"""
        connection = MagicMock()
        tags_to_delete = [
            {
                "Key": "DeleteMe",
                "Value": "this-should-not-be-in-delete-call",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]

        asg_module.apply_asg_tag_changes(connection, "test-asg", tags_to_delete, None)

        delete_call_args = mock_delete.call_args[0]
        delete_tags = delete_call_args[1]
        # Delete format should only have ResourceId, ResourceType, and Key
        assert delete_tags[0].keys() == {"ResourceId", "ResourceType", "Key"}
        assert delete_tags[0]["Key"] == "DeleteMe"
        assert delete_tags[0]["ResourceId"] == "test-asg"
        assert delete_tags[0]["ResourceType"] == "auto-scaling-group"

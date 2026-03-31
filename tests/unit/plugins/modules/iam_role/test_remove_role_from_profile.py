# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.modules.iam_role import remove_role_from_instance_profiles


class TestRemoveRoleFromInstanceProfiles:
    """Tests for the remove_role_from_instance_profiles() function."""

    def test_no_instance_profiles_attached(self):
        """Test when role has no attached instance profiles."""
        client = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=[]
        ):
            result = remove_role_from_instance_profiles(client, False, "test-role")

        assert result is False

    def test_check_mode_with_profiles_attached(self):
        """Test check mode returns True without making changes when profiles exist."""
        client = MagicMock()
        profiles = [{"InstanceProfileName": "profile1"}]

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=profiles
        ):
            with patch(
                "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_role_from_iam_instance_profile"
            ) as mock_remove:
                result = remove_role_from_instance_profiles(client, True, "test-role")

        assert result is True
        mock_remove.assert_not_called()  # Should not actually remove in check mode

    def test_removes_role_from_single_profile(self):
        """Test removing role from a single instance profile."""
        client = MagicMock()
        profiles = [{"InstanceProfileName": "profile1"}]

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=profiles
        ):
            with patch(
                "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_role_from_iam_instance_profile"
            ) as mock_remove:
                result = remove_role_from_instance_profiles(client, False, "test-role")

        assert result is True
        mock_remove.assert_called_once_with(client, "profile1", "test-role")

    def test_removes_role_from_multiple_profiles(self):
        """Test removing role from multiple instance profiles."""
        client = MagicMock()
        profiles = [
            {"InstanceProfileName": "profile1"},
            {"InstanceProfileName": "profile2"},
            {"InstanceProfileName": "profile3"},
        ]

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=profiles
        ):
            with patch(
                "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_role_from_iam_instance_profile"
            ) as mock_remove:
                result = remove_role_from_instance_profiles(client, False, "test-role")

        assert result is True
        assert mock_remove.call_count == 3
        mock_remove.assert_has_calls(
            [
                call(client, "profile1", "test-role"),
                call(client, "profile2", "test-role"),
                call(client, "profile3", "test-role"),
            ]
        )

    def test_processes_profiles_in_order(self):
        """Test that profiles are processed in the order returned."""
        client = MagicMock()
        profiles = [
            {"InstanceProfileName": "alpha-profile"},
            {"InstanceProfileName": "beta-profile"},
            {"InstanceProfileName": "gamma-profile"},
        ]

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=profiles
        ):
            with patch(
                "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_role_from_iam_instance_profile"
            ) as mock_remove:
                remove_role_from_instance_profiles(client, False, "test-role")

        # Verify calls were made in the correct order
        calls = mock_remove.call_args_list
        assert calls[0] == call(client, "alpha-profile", "test-role")
        assert calls[1] == call(client, "beta-profile", "test-role")
        assert calls[2] == call(client, "gamma-profile", "test-role")

    def test_check_mode_with_no_profiles(self):
        """Test check mode with no profiles attached returns False."""
        client = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=[]
        ):
            result = remove_role_from_instance_profiles(client, True, "test-role")

        assert result is False

    def test_profile_names_passed_correctly(self):
        """Test that instance profile names are correctly extracted and passed."""
        client = MagicMock()
        profiles = [
            {"InstanceProfileName": "my-custom-profile-name"},
        ]

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role.list_iam_instance_profiles", return_value=profiles
        ):
            with patch(
                "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_role_from_iam_instance_profile"
            ) as mock_remove:
                remove_role_from_instance_profiles(client, False, "my-role-name")

        # Verify the exact profile name and role name were passed
        mock_remove.assert_called_once_with(client, "my-custom-profile-name", "my-role-name")

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.modules.iam_role_info import describe_iam_roles


class TestDescribeIamRoles:
    """Tests for the describe_iam_roles() function."""

    def test_describe_by_name_filters_none(self):
        """Test that None values from get_iam_role are filtered out."""
        client = MagicMock()

        with patch("ansible_collections.amazon.aws.plugins.modules.iam_role_info.get_iam_role", return_value=None):
            result = describe_iam_roles(client, name="non-existent-role", path_prefix=None)

        assert result == []

    def test_describe_by_path_filters_none(self):
        """Test that None values from list are filtered out."""
        client = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.modules.iam_role_info.list_iam_roles",
            return_value=[{"RoleName": "role1"}, None, {"RoleName": "role2"}],
        ):
            with patch(
                "ansible_collections.amazon.aws.plugins.modules.iam_role_info.expand_iam_role",
                side_effect=lambda c, r: r,
            ):
                with patch(
                    "ansible_collections.amazon.aws.plugins.modules.iam_role_info.normalize_iam_role",
                    side_effect=lambda r: {"role_name": r["RoleName"]},
                ):
                    result = describe_iam_roles(client, name=None, path_prefix="/test/")

        assert len(result) == 2
        assert result[0] == {"role_name": "role1"}
        assert result[1] == {"role_name": "role2"}

    def test_describe_with_empty_list(self):
        """Test describing roles when list_iam_roles returns empty list."""
        client = MagicMock()

        with patch("ansible_collections.amazon.aws.plugins.modules.iam_role_info.list_iam_roles", return_value=[]):
            result = describe_iam_roles(client, name=None, path_prefix="/test/")

        assert result == []

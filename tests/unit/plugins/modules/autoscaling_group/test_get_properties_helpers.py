# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestResolveTargetGroupNames:
    @patch.object(asg_module, "module", create=True)
    @patch.object(asg_module, "describe_target_groups")
    def test_no_target_groups(self, mock_describe, mock_module):
        """Test with empty target group list"""
        result = asg_module._resolve_target_group_names([])

        assert result == []
        mock_describe.assert_not_called()

    @patch.object(asg_module, "module", create=True)
    @patch.object(asg_module, "describe_target_groups")
    def test_single_target_group(self, mock_describe, mock_module):
        """Test with single target group"""
        mock_elbv2_conn = MagicMock()
        mock_module.client.return_value = mock_elbv2_conn
        mock_describe.return_value = [{"TargetGroupName": "tg-1"}]

        result = asg_module._resolve_target_group_names(
            ["arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-1/abc"]
        )

        assert result == ["tg-1"]
        mock_describe.assert_called_once_with(
            mock_elbv2_conn,
            TargetGroupArns=["arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-1/abc"],
        )

    @patch.object(asg_module, "module", create=True)
    @patch.object(asg_module, "describe_target_groups")
    def test_multiple_target_groups_single_chunk(self, mock_describe, mock_module):
        """Test with multiple target groups in single chunk"""
        mock_elbv2_conn = MagicMock()
        mock_module.client.return_value = mock_elbv2_conn
        mock_describe.return_value = [
            {"TargetGroupName": "tg-1"},
            {"TargetGroupName": "tg-2"},
            {"TargetGroupName": "tg-3"},
        ]

        arns = [
            "arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-1/abc",
            "arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-2/def",
            "arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-3/ghi",
        ]

        result = asg_module._resolve_target_group_names(arns)

        assert result == ["tg-1", "tg-2", "tg-3"]
        mock_describe.assert_called_once_with(mock_elbv2_conn, TargetGroupArns=arns)

    @patch.object(asg_module, "module", create=True)
    @patch.object(asg_module, "describe_target_groups")
    def test_chunking_at_limit(self, mock_describe, mock_module):
        """Test chunking with exactly 20 target groups"""
        mock_elbv2_conn = MagicMock()
        mock_module.client.return_value = mock_elbv2_conn

        # Create 20 target groups
        arns = [f"arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-{i}/abc" for i in range(20)]
        mock_describe.return_value = [{"TargetGroupName": f"tg-{i}"} for i in range(20)]

        result = asg_module._resolve_target_group_names(arns)

        assert len(result) == 20
        assert result == [f"tg-{i}" for i in range(20)]
        mock_describe.assert_called_once()

    @patch.object(asg_module, "module", create=True)
    @patch.object(asg_module, "describe_target_groups")
    def test_chunking_multiple_chunks(self, mock_describe, mock_module):
        """Test chunking with 25 target groups (2 chunks)"""
        mock_elbv2_conn = MagicMock()
        mock_module.client.return_value = mock_elbv2_conn

        # Create 25 target groups
        arns = [f"arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-{i}/abc" for i in range(25)]

        # Mock returns for two chunks
        def describe_side_effect(conn, TargetGroupArns):
            return [{"TargetGroupName": arn.split("/")[1]} for arn in TargetGroupArns]

        mock_describe.side_effect = describe_side_effect

        result = asg_module._resolve_target_group_names(arns)

        assert len(result) == 25
        assert result == [f"tg-{i}" for i in range(25)]
        assert mock_describe.call_count == 2  # Should be called twice for 25 items

    @patch.object(asg_module, "module", create=True)
    @patch.object(asg_module, "describe_target_groups")
    def test_chunking_large_number(self, mock_describe, mock_module):
        """Test chunking with 50 target groups (3 chunks)"""
        mock_elbv2_conn = MagicMock()
        mock_module.client.return_value = mock_elbv2_conn

        # Create 50 target groups
        arns = [f"arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/tg-{i}/abc" for i in range(50)]

        def describe_side_effect(conn, TargetGroupArns):
            return [{"TargetGroupName": arn.split("/")[1]} for arn in TargetGroupArns]

        mock_describe.side_effect = describe_side_effect

        result = asg_module._resolve_target_group_names(arns)

        assert len(result) == 50
        assert result == [f"tg-{i}" for i in range(50)]
        assert mock_describe.call_count == 3  # Should be called 3 times: 20, 20, 10

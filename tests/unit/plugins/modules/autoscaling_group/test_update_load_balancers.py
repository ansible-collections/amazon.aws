# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestUpdateLoadBalancers:
    @patch.object(asg_module, "attach_load_balancers")
    @patch.object(asg_module, "detach_load_balancers")
    def test_no_change_requested(self, mock_detach, mock_attach):
        """Test when desired_elbs is None (no change requested)"""
        connection = MagicMock()
        changed = asg_module.update_load_balancers(connection, "test-asg", ["elb-1"], None)

        assert changed is False
        mock_attach.assert_not_called()
        mock_detach.assert_not_called()

    @patch.object(asg_module, "attach_load_balancers")
    @patch.object(asg_module, "detach_load_balancers")
    def test_no_changes_needed(self, mock_detach, mock_attach):
        """Test when current and desired are identical"""
        connection = MagicMock()
        changed = asg_module.update_load_balancers(connection, "test-asg", ["elb-1", "elb-2"], ["elb-1", "elb-2"])

        assert changed is False
        mock_attach.assert_not_called()
        mock_detach.assert_not_called()

    @patch.object(asg_module, "attach_load_balancers")
    @patch.object(asg_module, "detach_load_balancers")
    def test_attach_only(self, mock_detach, mock_attach):
        """Test attaching new load balancers"""
        connection = MagicMock()
        changed = asg_module.update_load_balancers(connection, "test-asg", ["elb-1"], ["elb-1", "elb-2"])

        assert changed is True
        mock_attach.assert_called_once_with(connection, "test-asg", ["elb-2"])
        mock_detach.assert_not_called()

    @patch.object(asg_module, "attach_load_balancers")
    @patch.object(asg_module, "detach_load_balancers")
    def test_detach_only(self, mock_detach, mock_attach):
        """Test detaching load balancers"""
        connection = MagicMock()
        changed = asg_module.update_load_balancers(connection, "test-asg", ["elb-1", "elb-2"], ["elb-1"])

        assert changed is True
        mock_detach.assert_called_once_with(connection, "test-asg", ["elb-2"])
        mock_attach.assert_not_called()

    @patch.object(asg_module, "attach_load_balancers")
    @patch.object(asg_module, "detach_load_balancers")
    def test_attach_and_detach(self, mock_detach, mock_attach):
        """Test both attaching and detaching load balancers"""
        connection = MagicMock()
        changed = asg_module.update_load_balancers(connection, "test-asg", ["elb-1", "elb-2"], ["elb-2", "elb-3"])

        assert changed is True
        mock_detach.assert_called_once_with(connection, "test-asg", ["elb-1"])
        mock_attach.assert_called_once_with(connection, "test-asg", ["elb-3"])

    @patch.object(asg_module, "attach_load_balancers")
    @patch.object(asg_module, "detach_load_balancers")
    def test_remove_all(self, mock_detach, mock_attach):
        """Test removing all load balancers"""
        connection = MagicMock()
        changed = asg_module.update_load_balancers(connection, "test-asg", ["elb-1", "elb-2"], [])

        assert changed is True
        # The set could be ordered differently, so check for both possibilities
        called_elbs = set(mock_detach.call_args[0][2])
        assert called_elbs == {"elb-1", "elb-2"}
        mock_attach.assert_not_called()


class TestUpdateTargetGroups:
    @patch.object(asg_module, "attach_lb_target_groups")
    @patch.object(asg_module, "detach_lb_target_groups")
    def test_no_change_requested(self, mock_detach, mock_attach):
        """Test when desired_tgs is None (no change requested)"""
        connection = MagicMock()
        changed = asg_module.update_target_groups(connection, "test-asg", ["arn:aws:tg1"], None)

        assert changed is False
        mock_attach.assert_not_called()
        mock_detach.assert_not_called()

    @patch.object(asg_module, "attach_lb_target_groups")
    @patch.object(asg_module, "detach_lb_target_groups")
    def test_no_changes_needed(self, mock_detach, mock_attach):
        """Test when current and desired are identical"""
        connection = MagicMock()
        changed = asg_module.update_target_groups(
            connection, "test-asg", ["arn:aws:tg1", "arn:aws:tg2"], ["arn:aws:tg1", "arn:aws:tg2"]
        )

        assert changed is False
        mock_attach.assert_not_called()
        mock_detach.assert_not_called()

    @patch.object(asg_module, "attach_lb_target_groups")
    @patch.object(asg_module, "detach_lb_target_groups")
    def test_attach_only(self, mock_detach, mock_attach):
        """Test attaching new target groups"""
        connection = MagicMock()
        changed = asg_module.update_target_groups(
            connection, "test-asg", ["arn:aws:tg1"], ["arn:aws:tg1", "arn:aws:tg2"]
        )

        assert changed is True
        mock_attach.assert_called_once_with(connection, "test-asg", ["arn:aws:tg2"])
        mock_detach.assert_not_called()

    @patch.object(asg_module, "attach_lb_target_groups")
    @patch.object(asg_module, "detach_lb_target_groups")
    def test_detach_only(self, mock_detach, mock_attach):
        """Test detaching target groups"""
        connection = MagicMock()
        changed = asg_module.update_target_groups(
            connection, "test-asg", ["arn:aws:tg1", "arn:aws:tg2"], ["arn:aws:tg1"]
        )

        assert changed is True
        mock_detach.assert_called_once_with(connection, "test-asg", ["arn:aws:tg2"])
        mock_attach.assert_not_called()

    @patch.object(asg_module, "attach_lb_target_groups")
    @patch.object(asg_module, "detach_lb_target_groups")
    def test_attach_and_detach(self, mock_detach, mock_attach):
        """Test both attaching and detaching target groups"""
        connection = MagicMock()
        changed = asg_module.update_target_groups(
            connection, "test-asg", ["arn:aws:tg1", "arn:aws:tg2"], ["arn:aws:tg2", "arn:aws:tg3"]
        )

        assert changed is True
        mock_detach.assert_called_once_with(connection, "test-asg", ["arn:aws:tg1"])
        mock_attach.assert_called_once_with(connection, "test-asg", ["arn:aws:tg3"])

    @patch.object(asg_module, "attach_lb_target_groups")
    @patch.object(asg_module, "detach_lb_target_groups")
    def test_remove_all(self, mock_detach, mock_attach):
        """Test removing all target groups"""
        connection = MagicMock()
        changed = asg_module.update_target_groups(connection, "test-asg", ["arn:aws:tg1", "arn:aws:tg2"], [])

        assert changed is True
        # The set could be ordered differently, so check for both possibilities
        called_tgs = set(mock_detach.call_args[0][2])
        assert called_tgs == {"arn:aws:tg1", "arn:aws:tg2"}
        mock_attach.assert_not_called()

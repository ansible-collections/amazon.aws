# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils._elbv2 import api


class TestGetLoadBalancerByName:
    """Tests for get_load_balancer_by_name helper function"""

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.describe_load_balancers")
    def test_returns_load_balancer_when_found(self, m_describe):
        connection = MagicMock()
        expected_lb = {"LoadBalancerArn": "arn:aws:...", "LoadBalancerName": "test-lb"}
        m_describe.return_value = [expected_lb]

        result = api.get_load_balancer_by_name(connection, "test-lb")

        assert result == expected_lb
        m_describe.assert_called_once_with(connection, names=["test-lb"])

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.describe_load_balancers")
    def test_returns_none_when_not_found(self, m_describe):
        connection = MagicMock()
        m_describe.return_value = []

        result = api.get_load_balancer_by_name(connection, "nonexistent")

        assert result is None
        m_describe.assert_called_once_with(connection, names=["nonexistent"])


class TestGetListenerRules:
    """Tests for get_listener_rules helper function"""

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.describe_rules")
    def test_returns_rules_for_listener(self, m_describe):
        connection = MagicMock()
        listener_arn = "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/test/abc/def"
        expected_rules = [
            {"RuleArn": "arn:aws:...rule/1", "Priority": "1"},
            {"RuleArn": "arn:aws:...rule/2", "Priority": "2"},
        ]
        m_describe.return_value = expected_rules

        result = api.get_listener_rules(connection, listener_arn)

        assert result == expected_rules
        m_describe.assert_called_once_with(connection, ListenerArn=listener_arn)


class TestGetTargetGroupArnByName:
    """Tests for get_target_group_arn_by_name helper function"""

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.describe_target_groups")
    def test_returns_arn_when_found(self, m_describe):
        connection = MagicMock()
        expected_arn = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/test-tg/abc123"
        m_describe.return_value = [{"TargetGroupArn": expected_arn, "TargetGroupName": "test-tg"}]

        result = api.get_target_group_arn_by_name(connection, "test-tg")

        assert result == expected_arn
        m_describe.assert_called_once_with(connection, Names=["test-tg"])

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.describe_target_groups")
    def test_raises_when_not_found(self, m_describe):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.common import AnsibleELBv2Error

        connection = MagicMock()
        m_describe.return_value = []

        with pytest.raises(AnsibleELBv2Error, match="Target group 'nonexistent' does not exist"):
            api.get_target_group_arn_by_name(connection, "nonexistent")

        m_describe.assert_called_once_with(connection, Names=["nonexistent"])

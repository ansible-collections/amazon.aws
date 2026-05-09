#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils import elbv2


class TestBuildApplicationLoadBalancerDescription:
    """Tests for build_application_load_balancer_description function"""

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_rules")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_with_all_includes(
        self,
        m_describe_attributes,
        m_describe_listeners,
        m_describe_rules,
        m_normalize,
    ):
        """Test with all include flags set to True"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }

        # Mock return values
        mock_attributes = [{"Key": "deletion_protection.enabled", "Value": "true"}]
        mock_listeners = [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/test/123/abc",
                "Port": 80,
            }
        ]
        mock_rules = [{"RuleArn": "arn:aws:...rule/1", "Priority": "1"}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_attributes.return_value = mock_attributes
        m_describe_listeners.return_value = mock_listeners
        m_describe_rules.return_value = mock_rules
        m_normalize.return_value = mock_normalized

        result = elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=True,
            include_listeners=True,
            include_listener_rules=True,
        )

        # Verify all describe functions were called
        m_describe_attributes.assert_called_once_with(connection, load_balancer["LoadBalancerArn"])
        m_describe_listeners.assert_called_once_with(connection, load_balancer_arn=load_balancer["LoadBalancerArn"])
        m_describe_rules.assert_called_once_with(connection, ListenerArn=mock_listeners[0]["ListenerArn"])

        # Verify normalize was called with the enriched ALB
        call_args = m_normalize.call_args[0][0]
        assert call_args["Attributes"] == mock_attributes
        assert call_args["Listeners"] == mock_listeners
        assert call_args["Listeners"][0]["Rules"] == mock_rules

        assert result == mock_normalized

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_rules")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_without_attributes(
        self,
        m_describe_attributes,
        m_describe_listeners,
        m_describe_rules,
        m_normalize,
    ):
        """Test with include_attributes=False"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }

        mock_listeners = [{"ListenerArn": "arn:aws:...listener/1", "Port": 80}]
        mock_rules = [{"RuleArn": "arn:aws:...rule/1", "Priority": "1"}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_listeners.return_value = mock_listeners
        m_describe_rules.return_value = mock_rules
        m_normalize.return_value = mock_normalized

        result = elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=False,
            include_listeners=True,
            include_listener_rules=True,
        )

        # Verify attributes were not fetched
        m_describe_attributes.assert_not_called()

        # Verify listeners and rules were fetched
        m_describe_listeners.assert_called_once()
        m_describe_rules.assert_called_once()

        # Verify normalize was called without Attributes
        call_args = m_normalize.call_args[0][0]
        assert "Attributes" not in call_args
        assert result == mock_normalized

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_rules")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_without_listeners(
        self,
        m_describe_attributes,
        m_describe_listeners,
        m_describe_rules,
        m_normalize,
    ):
        """Test with include_listeners=False and include_listener_rules=False"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }

        mock_attributes = [{"Key": "deletion_protection.enabled", "Value": "true"}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_attributes.return_value = mock_attributes
        m_normalize.return_value = mock_normalized

        result = elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=True,
            include_listeners=False,
            include_listener_rules=False,
        )

        # Verify listeners and rules were not fetched
        m_describe_listeners.assert_not_called()
        m_describe_rules.assert_not_called()

        # Verify attributes were fetched
        m_describe_attributes.assert_called_once()

        # Verify normalize was called without Listeners
        call_args = m_normalize.call_args[0][0]
        assert "Listeners" not in call_args
        assert result == mock_normalized

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_rules")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_with_listeners_but_without_rules(
        self,
        m_describe_attributes,
        m_describe_listeners,
        m_describe_rules,
        m_normalize,
    ):
        """Test with include_listeners=True but include_listener_rules=False"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }

        mock_listeners = [{"ListenerArn": "arn:aws:...listener/1", "Port": 80}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_listeners.return_value = mock_listeners
        m_normalize.return_value = mock_normalized

        result = elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=False,
            include_listeners=True,
            include_listener_rules=False,
        )

        # Verify listeners were fetched but rules were not
        m_describe_listeners.assert_called_once()
        m_describe_rules.assert_not_called()

        # Verify normalize was called with listeners but without rules
        call_args = m_normalize.call_args[0][0]
        assert call_args["Listeners"] == mock_listeners
        assert "Rules" not in call_args["Listeners"][0]
        assert result == mock_normalized

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_rules")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_with_multiple_listeners(
        self,
        m_describe_attributes,
        m_describe_listeners,
        m_describe_rules,
        m_normalize,
    ):
        """Test that rules are fetched for each listener"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }

        mock_listeners = [
            {"ListenerArn": "arn:aws:...listener/1", "Port": 80},
            {"ListenerArn": "arn:aws:...listener/2", "Port": 443},
        ]
        mock_rules = [{"RuleArn": "arn:aws:...rule/1", "Priority": "1"}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_listeners.return_value = mock_listeners
        m_describe_rules.return_value = mock_rules
        m_normalize.return_value = mock_normalized

        result = elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=False,
            include_listeners=True,
            include_listener_rules=True,
        )

        # Verify describe_rules was called for each listener
        assert m_describe_rules.call_count == 2
        m_describe_rules.assert_any_call(connection, ListenerArn="arn:aws:...listener/1")
        m_describe_rules.assert_any_call(connection, ListenerArn="arn:aws:...listener/2")

        # Verify both listeners have rules attached
        call_args = m_normalize.call_args[0][0]
        assert call_args["Listeners"][0]["Rules"] == mock_rules
        assert call_args["Listeners"][1]["Rules"] == mock_rules
        assert result == mock_normalized

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_rules")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_include_listener_rules_implies_listeners(
        self,
        m_describe_attributes,
        m_describe_listeners,
        m_describe_rules,
        m_normalize,
    ):
        """Test that include_listener_rules=True implies fetching listeners even if include_listeners=False"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }

        mock_listeners = [{"ListenerArn": "arn:aws:...listener/1", "Port": 80}]
        mock_rules = [{"RuleArn": "arn:aws:...rule/1", "Priority": "1"}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_listeners.return_value = mock_listeners
        m_describe_rules.return_value = mock_rules
        m_normalize.return_value = mock_normalized

        result = elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=False,
            include_listeners=False,
            include_listener_rules=True,
        )

        # Verify listeners were still fetched because rules were requested
        m_describe_listeners.assert_called_once()
        m_describe_rules.assert_called_once()

        assert result == mock_normalized

    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.normalize_application_load_balancer")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_load_balancer_attributes")
    def test_does_not_modify_original_load_balancer(
        self,
        m_describe_attributes,
        m_normalize,
    ):
        """Test that the original load_balancer dict is not modified"""
        connection = MagicMock()
        load_balancer = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }
        original_load_balancer = load_balancer.copy()

        mock_attributes = [{"Key": "deletion_protection.enabled", "Value": "true"}]
        mock_normalized = {"load_balancer_name": "test-alb"}

        m_describe_attributes.return_value = mock_attributes
        m_normalize.return_value = mock_normalized

        elbv2.build_application_load_balancer_description(
            connection,
            load_balancer,
            include_attributes=True,
            include_listeners=False,
            include_listener_rules=False,
        )

        # Verify the original dict was not modified
        assert load_balancer == original_load_balancer
        assert "Attributes" not in load_balancer


class TestAttributeDiffers:
    """Tests for ElasticLoadBalancerV2._attribute_differs helper method"""

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_false_when_new_value_is_none(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"access_logs_s3_enabled": "true"}

        result = elb._attribute_differs(None, "access_logs_s3_enabled")
        assert result is False

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_true_when_bool_values_differ(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"access_logs_s3_enabled": "true"}

        result = elb._attribute_differs(False, "access_logs_s3_enabled")
        assert result is True

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_false_when_bool_values_match(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"access_logs_s3_enabled": "true"}

        result = elb._attribute_differs(True, "access_logs_s3_enabled")
        assert result is False

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_true_when_int_values_differ(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"idle_timeout_timeout_seconds": "60"}

        result = elb._attribute_differs(120, "idle_timeout_timeout_seconds")
        assert result is True

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_false_when_int_values_match(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"idle_timeout_timeout_seconds": "60"}

        result = elb._attribute_differs(60, "idle_timeout_timeout_seconds")
        assert result is False

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_auto_lowercases_bool_values(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"deletion_protection_enabled": "false"}

        # Bool values are automatically lowercased: True -> "true", which differs from "false"
        result = elb._attribute_differs(True, "deletion_protection_enabled")
        assert result is True

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_handles_string_values(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.elb_attributes = {"access_logs_s3_bucket": "my-bucket"}

        result = elb._attribute_differs("different-bucket", "access_logs_s3_bucket")
        assert result is True

        result = elb._attribute_differs("my-bucket", "access_logs_s3_bucket")
        assert result is False


class TestAddAttributeUpdate:
    """Tests for ElasticLoadBalancerV2._add_attribute_update helper method"""

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_adds_bool_attribute_as_lowercase_string(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        update_list = []

        elb._add_attribute_update(update_list, "access_logs.s3.enabled", True)

        assert update_list == [{"Key": "access_logs.s3.enabled", "Value": "true"}]

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_adds_int_attribute_as_string(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        update_list = []

        elb._add_attribute_update(update_list, "idle_timeout.timeout_seconds", 120)

        assert update_list == [{"Key": "idle_timeout.timeout_seconds", "Value": "120"}]

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_adds_string_attribute(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        update_list = []

        elb._add_attribute_update(update_list, "access_logs.s3.bucket", "my-bucket")

        assert update_list == [{"Key": "access_logs.s3.bucket", "Value": "my-bucket"}]

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_appends_to_existing_list(self):
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        update_list = [{"Key": "existing.attribute", "Value": "value"}]

        elb._add_attribute_update(update_list, "new.attribute", "new-value")

        assert len(update_list) == 2
        assert update_list[1] == {"Key": "new.attribute", "Value": "new-value"}


class TestInheritedHelperMethods:
    """Tests that both ALB and NLB can use inherited helper methods from ElasticLoadBalancerV2"""

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_alb_can_use_attribute_differs(self):
        """ApplicationLoadBalancer can use _attribute_differs from parent class"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {"deletion_protection_enabled": "true"}

        result = alb._attribute_differs(True, "deletion_protection_enabled")
        assert result is False

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_alb_can_use_add_attribute_update(self):
        """ApplicationLoadBalancer can use _add_attribute_update from parent class"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        update_list = []

        alb._add_attribute_update(update_list, "deletion_protection.enabled", True)
        assert update_list == [{"Key": "deletion_protection.enabled", "Value": "true"}]

    @patch.object(elbv2.NetworkLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_nlb_can_use_attribute_differs(self):
        """NetworkLoadBalancer can use _attribute_differs from parent class"""
        nlb = elbv2.NetworkLoadBalancer(None, None)
        nlb.elb_attributes = {"load_balancing_cross_zone_enabled": "false"}

        result = nlb._attribute_differs(True, "load_balancing_cross_zone_enabled")
        assert result is True

    @patch.object(elbv2.NetworkLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_nlb_can_use_add_attribute_update(self):
        """NetworkLoadBalancer can use _add_attribute_update from parent class"""
        nlb = elbv2.NetworkLoadBalancer(None, None)
        update_list = []

        nlb._add_attribute_update(update_list, "load_balancing.cross_zone.enabled", False)
        assert update_list == [{"Key": "load_balancing.cross_zone.enabled", "Value": "false"}]

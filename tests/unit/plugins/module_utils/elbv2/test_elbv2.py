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


class TestBuildElbAttributesUpdateList:
    """Tests for ApplicationLoadBalancer._build_elb_attributes_update_list method"""

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_empty_list_when_no_changes(self):
        """Returns empty list when all attributes match"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {
            "access_logs_s3_enabled": "false",
            "deletion_protection_enabled": "false",
        }
        alb.access_logs_enabled = False
        alb.access_logs_s3_bucket = None
        alb.access_logs_s3_prefix = None
        alb.deletion_protection = False
        alb.idle_timeout = None
        alb.http2 = None
        alb.http_desync_mitigation_mode = None
        alb.http_drop_invalid_header_fields = None
        alb.http_x_amzn_tls_version_and_cipher_suite = None
        alb.http_xff_client_port = None
        alb.waf_fail_open = None

        result = alb._build_elb_attributes_update_list()
        assert result == []

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_updates_for_changed_boolean_attributes(self):
        """Returns update list for changed boolean attributes"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {
            "access_logs_s3_enabled": "false",
            "deletion_protection_enabled": "false",
            "routing_http2_enabled": "true",
        }
        alb.access_logs_enabled = True  # Changed
        alb.access_logs_s3_bucket = None
        alb.access_logs_s3_prefix = None
        alb.deletion_protection = True  # Changed
        alb.idle_timeout = None
        alb.http2 = False  # Changed
        alb.http_desync_mitigation_mode = None
        alb.http_drop_invalid_header_fields = None
        alb.http_x_amzn_tls_version_and_cipher_suite = None
        alb.http_xff_client_port = None
        alb.waf_fail_open = None

        result = alb._build_elb_attributes_update_list()
        assert len(result) == 3
        assert {"Key": "access_logs.s3.enabled", "Value": "true"} in result
        assert {"Key": "deletion_protection.enabled", "Value": "true"} in result
        assert {"Key": "routing.http2.enabled", "Value": "false"} in result

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_updates_for_changed_string_attributes(self):
        """Returns update list for changed string attributes"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {
            "access_logs_s3_bucket": "old-bucket",
            "access_logs_s3_prefix": "old-prefix",
        }
        alb.access_logs_enabled = None
        alb.access_logs_s3_bucket = "new-bucket"  # Changed
        alb.access_logs_s3_prefix = "new-prefix"  # Changed
        alb.deletion_protection = None
        alb.idle_timeout = None
        alb.http2 = None
        alb.http_desync_mitigation_mode = None
        alb.http_drop_invalid_header_fields = None
        alb.http_x_amzn_tls_version_and_cipher_suite = None
        alb.http_xff_client_port = None
        alb.waf_fail_open = None

        result = alb._build_elb_attributes_update_list()
        assert len(result) == 2
        assert {"Key": "access_logs.s3.bucket", "Value": "new-bucket"} in result
        assert {"Key": "access_logs.s3.prefix", "Value": "new-prefix"} in result

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_updates_for_changed_integer_attributes(self):
        """Returns update list for changed integer attributes"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {
            "idle_timeout_timeout_seconds": "60",
        }
        alb.access_logs_enabled = None
        alb.access_logs_s3_bucket = None
        alb.access_logs_s3_prefix = None
        alb.deletion_protection = None
        alb.idle_timeout = 120  # Changed
        alb.http2 = None
        alb.http_desync_mitigation_mode = None
        alb.http_drop_invalid_header_fields = None
        alb.http_x_amzn_tls_version_and_cipher_suite = None
        alb.http_xff_client_port = None
        alb.waf_fail_open = None

        result = alb._build_elb_attributes_update_list()
        assert len(result) == 1
        assert {"Key": "idle_timeout.timeout_seconds", "Value": "120"} in result

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_updates_for_http_routing_attributes(self):
        """Returns update list for changed HTTP routing attributes"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {
            "routing_http_desync_mitigation_mode": "defensive",
            "routing_http_drop_invalid_header_fields_enabled": "false",
            "routing_http_x_amzn_tls_version_and_cipher_suite_enabled": "false",
            "routing_http_xff_client_port_enabled": "false",
            "waf_fail_open_enabled": "false",
        }
        alb.access_logs_enabled = None
        alb.access_logs_s3_bucket = None
        alb.access_logs_s3_prefix = None
        alb.deletion_protection = None
        alb.idle_timeout = None
        alb.http2 = None
        alb.http_desync_mitigation_mode = "strictest"  # Changed
        alb.http_drop_invalid_header_fields = True  # Changed
        alb.http_x_amzn_tls_version_and_cipher_suite = True  # Changed
        alb.http_xff_client_port = True  # Changed
        alb.waf_fail_open = True  # Changed

        result = alb._build_elb_attributes_update_list()
        assert len(result) == 5
        assert {"Key": "routing.http.desync_mitigation_mode", "Value": "strictest"} in result
        assert {"Key": "routing.http.drop_invalid_header_fields.enabled", "Value": "true"} in result
        assert {
            "Key": "routing.http.x_amzn_tls_version_and_cipher_suite.enabled",
            "Value": "true",
        } in result
        assert {"Key": "routing.http.xff_client_port.enabled", "Value": "true"} in result
        assert {"Key": "waf.fail_open.enabled", "Value": "true"} in result


class TestCompareElbAttributes:
    """Tests for ApplicationLoadBalancer.compare_elb_attributes method"""

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_true_when_attributes_match(self):
        """Returns True when all attributes match current state"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {"deletion_protection_enabled": "true"}
        alb.access_logs_enabled = None
        alb.access_logs_s3_bucket = None
        alb.access_logs_s3_prefix = None
        alb.deletion_protection = True  # Matches
        alb.idle_timeout = None
        alb.http2 = None
        alb.http_desync_mitigation_mode = None
        alb.http_drop_invalid_header_fields = None
        alb.http_x_amzn_tls_version_and_cipher_suite = None
        alb.http_xff_client_port = None
        alb.waf_fail_open = None

        result = alb.compare_elb_attributes()
        assert result is True

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_false_when_attributes_differ(self):
        """Returns False when attributes differ from current state"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.elb_attributes = {"deletion_protection_enabled": "false"}
        alb.access_logs_enabled = None
        alb.access_logs_s3_bucket = None
        alb.access_logs_s3_prefix = None
        alb.deletion_protection = True  # Different
        alb.idle_timeout = None
        alb.http2 = None
        alb.http_desync_mitigation_mode = None
        alb.http_drop_invalid_header_fields = None
        alb.http_x_amzn_tls_version_and_cipher_suite = None
        alb.http_xff_client_port = None
        alb.waf_fail_open = None

        result = alb.compare_elb_attributes()
        assert result is False


class TestElbCreateParams:
    """Tests for ElasticLoadBalancerV2._elb_create_params method"""

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_basic_params(self):
        """Returns basic required parameters"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.name = "test-elb"
        elb.type = "application"
        elb.elb_ip_addr_type = None
        elb.subnets = None
        elb.subnet_mappings = None
        elb.tags = None

        result = elb._elb_create_params()
        assert result == {"Name": "test-elb", "Type": "application"}

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_includes_optional_ip_address_type(self):
        """Includes IpAddressType when set"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.name = "test-elb"
        elb.type = "application"
        elb.elb_ip_addr_type = "dualstack"
        elb.subnets = None
        elb.subnet_mappings = None
        elb.tags = None

        result = elb._elb_create_params()
        assert result["IpAddressType"] == "dualstack"

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_includes_subnets_when_set(self):
        """Includes Subnets when set"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.name = "test-elb"
        elb.type = "application"
        elb.elb_ip_addr_type = None
        elb.subnets = ["subnet-12345", "subnet-67890"]
        elb.subnet_mappings = None
        elb.tags = None

        result = elb._elb_create_params()
        assert result["Subnets"] == ["subnet-12345", "subnet-67890"]

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_includes_subnet_mappings_when_set(self):
        """Includes SubnetMappings when set"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.name = "test-elb"
        elb.type = "network"
        elb.elb_ip_addr_type = None
        elb.subnets = None
        elb.subnet_mappings = [{"SubnetId": "subnet-12345", "AllocationId": "eipalloc-abc"}]
        elb.tags = None

        result = elb._elb_create_params()
        assert result["SubnetMappings"] == [{"SubnetId": "subnet-12345", "AllocationId": "eipalloc-abc"}]

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_includes_tags_when_set(self):
        """Includes Tags when set"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.name = "test-elb"
        elb.type = "application"
        elb.elb_ip_addr_type = None
        elb.subnets = None
        elb.subnet_mappings = None
        elb.tags = [{"Key": "Environment", "Value": "test"}]

        result = elb._elb_create_params()
        assert result["Tags"] == [{"Key": "Environment", "Value": "test"}]


class TestAlbElbCreateParams:
    """Tests for ApplicationLoadBalancer._elb_create_params method"""

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_adds_security_groups_and_scheme(self):
        """Adds SecurityGroups and Scheme to base params"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.name = "test-alb"
        alb.type = "application"
        alb.scheme = "internet-facing"
        alb.security_groups = ["sg-12345", "sg-67890"]
        alb.elb_ip_addr_type = None
        alb.subnets = ["subnet-12345"]
        alb.subnet_mappings = None
        alb.tags = None

        result = alb._elb_create_params()
        assert result["Name"] == "test-alb"
        assert result["Type"] == "application"
        assert result["Scheme"] == "internet-facing"
        assert result["SecurityGroups"] == ["sg-12345", "sg-67890"]
        assert result["Subnets"] == ["subnet-12345"]

    @patch.object(elbv2.ApplicationLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_omits_security_groups_when_none(self):
        """Doesn't include SecurityGroups when None"""
        alb = elbv2.ApplicationLoadBalancer(None, None, None)
        alb.name = "test-alb"
        alb.type = "application"
        alb.scheme = "internal"
        alb.security_groups = None
        alb.elb_ip_addr_type = None
        alb.subnets = None
        alb.subnet_mappings = None
        alb.tags = None

        result = alb._elb_create_params()
        assert "SecurityGroups" not in result
        assert result["Scheme"] == "internal"


class TestNlbElbCreateParams:
    """Tests for NetworkLoadBalancer._elb_create_params method"""

    @patch.object(elbv2.NetworkLoadBalancer, "__init__", lambda self, *args, **kwargs: None)
    def test_adds_scheme_to_base_params(self):
        """Adds Scheme to base params"""
        nlb = elbv2.NetworkLoadBalancer(None, None)
        nlb.name = "test-nlb"
        nlb.type = "network"
        nlb.scheme = "internet-facing"
        nlb.elb_ip_addr_type = None
        nlb.subnets = ["subnet-12345"]
        nlb.subnet_mappings = None
        nlb.tags = None

        result = nlb._elb_create_params()
        assert result["Name"] == "test-nlb"
        assert result["Type"] == "network"
        assert result["Scheme"] == "internet-facing"
        assert result["Subnets"] == ["subnet-12345"]


class TestCompareSubnets:
    """Tests for ElasticLoadBalancerV2.compare_subnets method"""

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_true_when_subnets_match(self):
        """Returns True when subnet list matches current ELB subnets"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.subnets = ["subnet-12345", "subnet-67890"]
        elb.subnet_mappings = None
        elb.elb = {
            "AvailabilityZones": [
                {"SubnetId": "subnet-12345", "LoadBalancerAddresses": []},
                {"SubnetId": "subnet-67890", "LoadBalancerAddresses": []},
            ]
        }

        result = elb.compare_subnets()
        assert result is True

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_false_when_subnets_differ(self):
        """Returns False when subnet list differs from current ELB subnets"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.subnets = ["subnet-12345", "subnet-99999"]  # Different subnet
        elb.subnet_mappings = None
        elb.elb = {
            "AvailabilityZones": [
                {"SubnetId": "subnet-12345", "LoadBalancerAddresses": []},
                {"SubnetId": "subnet-67890", "LoadBalancerAddresses": []},
            ]
        }

        result = elb.compare_subnets()
        assert result is False

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_true_when_subnet_mappings_match(self):
        """Returns True when subnet mappings match current ELB"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.subnets = None
        elb.subnet_mappings = [{"SubnetId": "subnet-12345"}, {"SubnetId": "subnet-67890"}]
        elb.elb = {
            "AvailabilityZones": [
                {"SubnetId": "subnet-12345", "LoadBalancerAddresses": []},
                {"SubnetId": "subnet-67890", "LoadBalancerAddresses": []},
            ]
        }

        result = elb.compare_subnets()
        assert result is True

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_true_when_subnet_mappings_with_allocation_ids_match(self):
        """Returns True when subnet mappings with AllocationIds match"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.subnets = None
        elb.subnet_mappings = [
            {"SubnetId": "subnet-12345", "AllocationId": "eipalloc-abc123"},
            {"SubnetId": "subnet-67890"},
        ]
        elb.elb = {
            "AvailabilityZones": [
                {
                    "SubnetId": "subnet-12345",
                    "LoadBalancerAddresses": [{"AllocationId": "eipalloc-abc123"}],
                },
                {"SubnetId": "subnet-67890", "LoadBalancerAddresses": []},
            ]
        }

        result = elb.compare_subnets()
        assert result is True

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_returns_false_when_allocation_ids_differ(self):
        """Returns False when AllocationIds differ"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.subnets = None
        elb.subnet_mappings = [
            {"SubnetId": "subnet-12345", "AllocationId": "eipalloc-different"},
            {"SubnetId": "subnet-67890"},
        ]
        elb.elb = {
            "AvailabilityZones": [
                {
                    "SubnetId": "subnet-12345",
                    "LoadBalancerAddresses": [{"AllocationId": "eipalloc-abc123"}],
                },
                {"SubnetId": "subnet-67890", "LoadBalancerAddresses": []},
            ]
        }

        result = elb.compare_subnets()
        assert result is False

    @patch.object(elbv2.ElasticLoadBalancerV2, "__init__", lambda self, *args, **kwargs: None)
    def test_handles_different_subnet_order(self):
        """Returns True when subnets match regardless of order"""
        elb = elbv2.ElasticLoadBalancerV2(None, None)
        elb.subnets = ["subnet-67890", "subnet-12345"]  # Reversed order
        elb.subnet_mappings = None
        elb.elb = {
            "AvailabilityZones": [
                {"SubnetId": "subnet-12345", "LoadBalancerAddresses": []},
                {"SubnetId": "subnet-67890", "LoadBalancerAddresses": []},
            ]
        }

        result = elb.compare_subnets()
        assert result is True

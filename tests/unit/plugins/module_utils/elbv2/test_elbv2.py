#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2


def createListener(**kwargs):
    result = {
        "Port": 80,
        "Protocol": "TCP",
        "DefaultActions": [
            {
                "Type": "fixed-response",
                "TargetGroupArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/my-targets/73e2d6bc24d8a067",
            }
        ],
    }
    if kwargs.get("port"):
        result["Port"] = kwargs.get("port")
    if kwargs.get("protocol"):
        result["Protocol"] = kwargs.get("protocol")
    if kwargs.get("certificate_arn") and kwargs.get("protocol") in ("TLS", "HTTPS"):
        result["Certificates"] = [{"CertificateArn": kwargs.get("certificate_arn")}]
    if kwargs.get("sslPolicy") and kwargs.get("protocol") in ("TLS", "HTTPS"):
        result["SslPolicy"] = kwargs.get("sslPolicy")
    if kwargs.get("alpnPolicy") and kwargs.get("protocol") == "TLS":
        result["AlpnPolicy"] = kwargs.get("alpnPolicy")
    if kwargs.get("default_actions"):
        result["DefaultActions"] = kwargs.get("default_actions")
    return result


@pytest.mark.parametrize("current_protocol", ["TCP", "TLS", "UDP"])
@pytest.mark.parametrize(
    "current_alpn,new_alpn",
    [
        (None, "None"),
        (None, "HTTP1Only"),
        ("HTTP1Only", "HTTP2Only"),
        ("HTTP1Only", "HTTP1Only"),
    ],
)
def test__compare_listener_alpn_policy(current_protocol, current_alpn, new_alpn):
    current_listener = createListener(protocol=current_protocol, alpnPolicy=[current_alpn])
    new_listener = createListener(protocol="TLS", alpnPolicy=[new_alpn])
    result = {}
    if current_protocol != "TLS":
        result["Protocol"] = "TLS"
    if new_alpn and any((current_protocol != "TLS", not current_alpn, current_alpn and current_alpn != new_alpn)):
        result["AlpnPolicy"] = [new_alpn]

    assert result == elbv2._compare_listener(current_listener, new_listener)


@pytest.mark.parametrize(
    "current_protocol,new_protocol",
    [
        ("TCP", "TCP"),
        ("TLS", "HTTPS"),
        ("HTTPS", "HTTPS"),
        ("TLS", "TLS"),
        ("HTTPS", "TLS"),
        ("HTTPS", "TCP"),
        ("TLS", "TCP"),
    ],
)
@pytest.mark.parametrize(
    "current_ssl,new_ssl",
    [
        (None, "ELBSecurityPolicy-TLS-1-0-2015-04"),
        ("ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06", "ELBSecurityPolicy-TLS-1-0-2015-04"),
        ("ELBSecurityPolicy-TLS-1-0-2015-04", None),
        ("ELBSecurityPolicy-TLS-1-0-2015-04", "ELBSecurityPolicy-TLS-1-0-2015-04"),
    ],
)
def test__compare_listener_sslpolicy(current_protocol, new_protocol, current_ssl, new_ssl):
    current_listener = createListener(protocol=current_protocol, sslPolicy=current_ssl)

    new_listener = createListener(protocol=new_protocol, sslPolicy=new_ssl)

    expected = {}
    if new_protocol != current_protocol:
        expected["Protocol"] = new_protocol
    if new_protocol in ("HTTPS", "TLS") and new_ssl and new_ssl != current_ssl:
        expected["SslPolicy"] = new_ssl
    assert expected == elbv2._compare_listener(current_listener, new_listener)


@pytest.mark.parametrize(
    "current_protocol,new_protocol",
    [
        ("TCP", "TCP"),
        ("TLS", "HTTPS"),
        ("HTTPS", "HTTPS"),
        ("TLS", "TLS"),
        ("HTTPS", "TLS"),
        ("HTTPS", "TCP"),
        ("TLS", "TCP"),
    ],
)
@pytest.mark.parametrize(
    "current_certificate,new_certificate",
    [
        (None, "arn:aws:iam::012345678901:server-certificate/ansible-test-1"),
        (
            "arn:aws:iam::012345678901:server-certificate/ansible-test-1",
            "arn:aws:iam::012345678901:server-certificate/ansible-test-2",
        ),
        ("arn:aws:iam::012345678901:server-certificate/ansible-test-1", None),
        (
            "arn:aws:iam::012345678901:server-certificate/ansible-test-1",
            "arn:aws:iam::012345678901:server-certificate/ansible-test-1",
        ),
    ],
)
def test__compare_listener_certificates(current_protocol, new_protocol, current_certificate, new_certificate):
    current_listener = createListener(protocol=current_protocol, certificate_arn=current_certificate)

    new_listener = createListener(protocol=new_protocol, certificate_arn=new_certificate)

    expected = {}
    if new_protocol != current_protocol:
        expected["Protocol"] = new_protocol
    if new_protocol in ("HTTPS", "TLS") and new_certificate and new_certificate != current_certificate:
        expected["Certificates"] = [{"CertificateArn": new_certificate}]
    assert expected == elbv2._compare_listener(current_listener, new_listener)


@pytest.mark.parametrize(
    "current_actions,new_actions,expected_listener",
    [
        # When Order field differs between current and new actions, modification is expected
        # because Order is now included in the comparison logic
        (
            [
                {"TargetGroupArn": "ansible1", "Type": "a", "Order": 1},
                {"TargetGroupArn": "ansible0", "Type": "b", "Order": 2},
                {"TargetGroupArn": "ansible0", "Type": "a"},
            ],
            [
                {"TargetGroupArn": "ansible1", "Type": "a"},
                {"TargetGroupArn": "ansible0", "Type": "b"},
                {"TargetGroupArn": "ansible0", "Type": "a"},
            ],
            {
                "DefaultActions": [
                    {"TargetGroupArn": "ansible1", "Type": "a"},
                    {"TargetGroupArn": "ansible0", "Type": "b"},
                    {"TargetGroupArn": "ansible0", "Type": "a"},
                ]
            },
        ),
        (
            [
                {"TargetGroupArn": "ansible0", "Type": "b", "Order": 1},
                {"TargetGroupArn": "ansible1", "Type": "a", "Order": 2},
                {"TargetGroupArn": "ansible0", "Type": "a"},
            ],
            [
                {"TargetGroupArn": "ansible1", "Type": "a"},
                {"TargetGroupArn": "ansible0", "Type": "b"},
                {"TargetGroupArn": "ansible0", "Type": "a"},
            ],
            {
                "DefaultActions": [
                    {"TargetGroupArn": "ansible1", "Type": "a"},
                    {"TargetGroupArn": "ansible0", "Type": "b"},
                    {"TargetGroupArn": "ansible0", "Type": "a"},
                ]
            },
        ),
        (
            [{"TargetGroupArn": "ansible1", "Type": "a", "Order": 1}],
            [{"TargetGroupArn": "ansible1", "Type": "a"}],
            {"DefaultActions": [{"TargetGroupArn": "ansible1", "Type": "a"}]},
        ),
        # When actions are identical (no Order difference), no modification expected
        (
            [{"TargetGroupArn": "ansible1", "Type": "a"}],
            [{"TargetGroupArn": "ansible1", "Type": "a"}],
            {},
        ),
        (
            [{"TargetGroupArn": "ansible1", "Type": "a", "Order": 1}],
            [{"TargetGroupArn": "ansible2", "Type": "a"}],
            {"DefaultActions": [{"TargetGroupArn": "ansible2", "Type": "a"}]},
        ),
        (
            [{"TargetGroupArn": "ansible1", "Type": "a"}, {"TargetGroupArn": "ansible2", "Type": "a"}],
            [{"TargetGroupArn": "ansible1", "Type": "a"}, {"TargetGroupArn": "ansible2", "Type": "b"}],
            {
                "DefaultActions": [
                    {"TargetGroupArn": "ansible1", "Type": "a"},
                    {"TargetGroupArn": "ansible2", "Type": "b"},
                ]
            },
        ),
    ],
)
def test__compare_listener_default_actions(current_actions, new_actions, expected_listener):
    current_listener = createListener(default_actions=current_actions)
    new_listener = createListener(default_actions=new_actions)
    assert expected_listener == elbv2._compare_listener(current_listener, new_listener)


@pytest.mark.parametrize(
    "current_listeners,new_listeners,expected",
    [
        (
            [
                {
                    "Port": 80,
                    "Protocol": "TCP",
                    "ListenerArn": "arn80",
                    "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward", "Order": 1}],
                },
                {
                    "Port": 90,
                    "Protocol": "UDP",
                    "ListenerArn": "arn90",
                    "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward", "Order": 1}],
                },
                {
                    "Port": 100,
                    "Protocol": "TLS",
                    "ListenerArn": "arn100",
                    "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward", "Order": 1}],
                },
            ],
            [
                {"Port": 80, "Protocol": "TCP", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]},
                {"Port": 90, "Protocol": "HTTPS", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]},
                {"Port": 101, "Protocol": "UDP", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]},
            ],
            {
                "add": [
                    {"Port": 101, "Protocol": "UDP", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
                ],
                # Port 80: DefaultActions Order changed (current has Order:1, new doesn't)
                # Port 90: Protocol changed (UDP->HTTPS) AND DefaultActions Order changed
                "modify": [
                    {
                        "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}],
                        "Port": 80,
                        "ListenerArn": "arn80",
                    },
                    {
                        "Protocol": "HTTPS",
                        "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}],
                        "Port": 90,
                        "ListenerArn": "arn90",
                    },
                ],
                "delete": ["arn100"],
            },
        )
    ],
)
def test__group_listeners(current_listeners, new_listeners, expected):
    to_add, to_modify, to_delete = elbv2._group_listeners(current_listeners, new_listeners)
    assert to_add == expected.get("add", [])
    assert to_modify == expected.get("modify", [])
    assert to_delete == expected.get("delete", [])


def test__prepare_listeners__no_listeners():
    module = MagicMock()
    connection = MagicMock()
    assert elbv2._prepare_listeners(connection, module, None) == []


def test__prepare_listeners__scrub_none_parameters():
    module = MagicMock()
    connection = MagicMock()
    listeners = [
        {
            "Port": 123,
            "Protocol": "TCP",
            "SslPolicy": None,
            "Rules": None,
            "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}],
        }
    ]
    assert elbv2._prepare_listeners(connection, module, listeners) == [
        {"Port": 123, "Protocol": "TCP", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
    ]


def test__prepare_listeners__alpn_policy():
    module = MagicMock()
    connection = MagicMock()
    listeners = [
        {"Port": 123, "AlpnPolicy": "MyPolicy1", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
    ]
    assert elbv2._prepare_listeners(connection, module, listeners) == [
        {"Port": 123, "AlpnPolicy": ["MyPolicy1"], "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
    ]


@patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.convert_tg_name_to_arn")
def test__prepare_listeners__target_group_name_unique_name(m_convert_tg_name_to_arn):
    module = MagicMock()
    connection = MagicMock()
    m_convert_tg_name_to_arn.return_value = MagicMock()
    target_group_name = MagicMock()
    listeners = [
        {
            "DefaultActions": [
                {"TargetGroupName": target_group_name, "Type": "forward"},
                {"TargetGroupName": target_group_name, "Type": "redirect"},
            ]
        }
    ]
    assert elbv2._prepare_listeners(connection, module, listeners) == [
        {
            "DefaultActions": [
                {"TargetGroupArn": m_convert_tg_name_to_arn.return_value, "Type": "forward"},
                {"TargetGroupArn": m_convert_tg_name_to_arn.return_value, "Type": "redirect"},
            ]
        }
    ]
    m_convert_tg_name_to_arn.assert_called_once_with(connection, module, target_group_name)


@patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.convert_tg_name_to_arn")
def test__prepare_listeners__target_group_name_multiple_name(m_convert_tg_name_to_arn):
    module = MagicMock()
    connection = MagicMock()
    tg_name1 = MagicMock()
    tg_name2 = MagicMock()
    arn_values = {
        tg_name1: MagicMock(),
        tg_name2: MagicMock(),
    }
    m_convert_tg_name_to_arn.side_effect = lambda conn, module, name: arn_values.get(name)

    listeners = [
        {
            "DefaultActions": [
                {"TargetGroupName": tg_name1, "Type": "forward"},
                {"TargetGroupName": tg_name2, "Type": "redirect"},
            ]
        }
    ]
    assert elbv2._prepare_listeners(connection, module, listeners) == [
        {
            "DefaultActions": [
                {"TargetGroupArn": arn_values.get(tg_name1), "Type": "forward"},
                {"TargetGroupArn": arn_values.get(tg_name2), "Type": "redirect"},
            ]
        }
    ]
    m_convert_tg_name_to_arn.assert_has_calls([call(connection, module, tg_name1), call(connection, module, tg_name2)])


@patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.describe_listeners")
@patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2._prepare_listeners")
def testELBListenersInit(
    m__prepare_listeners,
    m_describe_listeners,
):
    connection = MagicMock()
    module = MagicMock()
    purge_listeners = MagicMock()
    elb_arn = MagicMock()
    listeners = MagicMock()
    module.params = {"listeners": listeners, "purge_listeners": purge_listeners}

    m__prepare_listeners.return_value = MagicMock()
    m_describe_listeners.return_value = MagicMock()

    elb_listener = elbv2.ELBListeners(connection, module, elb_arn)

    m__prepare_listeners.assert_called_once_with(connection, module, listeners)
    m_describe_listeners.assert_called_once_with(connection, load_balancer_arn=elb_arn)

    assert elb_listener.listeners == m__prepare_listeners.return_value
    assert elb_listener.current_listeners == m_describe_listeners.return_value
    assert elb_listener.purge_listeners == purge_listeners
    assert elb_listener.elb_arn == elb_arn
    assert elb_listener.module == module
    assert elb_listener.changed is False


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

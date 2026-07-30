#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import ELBListeners
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_listener
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _group_listeners
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _prepare_listeners


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

    assert result == _compare_listener(current_listener, new_listener)


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
    assert expected == _compare_listener(current_listener, new_listener)


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
    assert expected == _compare_listener(current_listener, new_listener)


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
    assert expected_listener == _compare_listener(current_listener, new_listener)


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
    to_add, to_modify, to_delete = _group_listeners(current_listeners, new_listeners)
    assert to_add == expected.get("add", [])
    assert to_modify == expected.get("modify", [])
    assert to_delete == expected.get("delete", [])


def test__prepare_listeners__no_listeners():
    module = MagicMock()
    connection = MagicMock()
    assert _prepare_listeners(connection, module, None) == []


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
    assert _prepare_listeners(connection, module, listeners) == [
        {"Port": 123, "Protocol": "TCP", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
    ]


def test__prepare_listeners__alpn_policy():
    module = MagicMock()
    connection = MagicMock()
    listeners = [
        {"Port": 123, "AlpnPolicy": "MyPolicy1", "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
    ]
    assert _prepare_listeners(connection, module, listeners) == [
        {"Port": 123, "AlpnPolicy": ["MyPolicy1"], "DefaultActions": [{"TargetGroupArn": "arn1", "Type": "forward"}]}
    ]


@patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.get_target_group_arn_by_name")
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
    assert _prepare_listeners(connection, module, listeners) == [
        {
            "DefaultActions": [
                {"TargetGroupArn": m_convert_tg_name_to_arn.return_value, "Type": "forward"},
                {"TargetGroupArn": m_convert_tg_name_to_arn.return_value, "Type": "redirect"},
            ]
        }
    ]
    m_convert_tg_name_to_arn.assert_called_once_with(connection, target_group_name)


@patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.get_target_group_arn_by_name")
def test__prepare_listeners__target_group_name_multiple_name(m_convert_tg_name_to_arn):
    module = MagicMock()
    connection = MagicMock()
    tg_name1 = MagicMock()
    tg_name2 = MagicMock()
    arn_values = {
        tg_name1: MagicMock(),
        tg_name2: MagicMock(),
    }
    m_convert_tg_name_to_arn.side_effect = lambda conn, name: arn_values.get(name)

    listeners = [
        {
            "DefaultActions": [
                {"TargetGroupName": tg_name1, "Type": "forward"},
                {"TargetGroupName": tg_name2, "Type": "redirect"},
            ]
        }
    ]
    assert _prepare_listeners(connection, module, listeners) == [
        {
            "DefaultActions": [
                {"TargetGroupArn": arn_values.get(tg_name1), "Type": "forward"},
                {"TargetGroupArn": arn_values.get(tg_name2), "Type": "redirect"},
            ]
        }
    ]
    m_convert_tg_name_to_arn.assert_has_calls([call(connection, tg_name1), call(connection, tg_name2)])


@patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.api.describe_listeners")
@patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners._prepare_listeners")
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

    elb_listener = ELBListeners(connection, module, elb_arn)

    m__prepare_listeners.assert_called_once_with(connection, module, listeners)
    m_describe_listeners.assert_called_once_with(connection, load_balancer_arn=elb_arn)

    assert elb_listener.listeners == m__prepare_listeners.return_value
    assert elb_listener.current_listeners == m_describe_listeners.return_value
    assert elb_listener.purge_listeners == purge_listeners
    assert elb_listener.elb_arn == elb_arn
    assert elb_listener.module == module
    assert elb_listener.changed is False


class TestCompareSslPolicy:
    """Tests for _compare_ssl_policy helper function"""

    def test_returns_new_policy_when_current_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_ssl_policy

        current = {"Protocol": "HTTPS"}
        new = {"Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-TLS13-1-2-2021-06"}

        result = _compare_ssl_policy(current, new)
        assert result == "ELBSecurityPolicy-TLS13-1-2-2021-06"

    def test_returns_new_policy_when_different(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_ssl_policy

        current = {"Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-2016-08"}
        new = {"Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-TLS13-1-2-2021-06"}

        result = _compare_ssl_policy(current, new)
        assert result == "ELBSecurityPolicy-TLS13-1-2-2021-06"

    def test_returns_none_when_same(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_ssl_policy

        current = {"Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-TLS13-1-2-2021-06"}
        new = {"Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-TLS13-1-2-2021-06"}

        result = _compare_ssl_policy(current, new)
        assert result is None

    def test_returns_none_when_new_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_ssl_policy

        current = {"Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-2016-08"}
        new = {"Protocol": "HTTPS"}

        result = _compare_ssl_policy(current, new)
        assert result is None


class TestCompareCertificates:
    """Tests for _compare_certificates helper function"""

    def test_returns_new_cert_when_current_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_certificates

        current = {"Protocol": "HTTPS"}
        new = {"Protocol": "HTTPS", "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/new"}]}

        result = _compare_certificates(current, new)
        assert result == [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/new"}]

    def test_returns_new_cert_when_different(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_certificates

        current = {"Protocol": "HTTPS", "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/old"}]}
        new = {"Protocol": "HTTPS", "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/new"}]}

        result = _compare_certificates(current, new)
        assert result == [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/new"}]

    def test_returns_none_when_same(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_certificates

        current = {"Protocol": "HTTPS", "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/same"}]}
        new = {"Protocol": "HTTPS", "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/same"}]}

        result = _compare_certificates(current, new)
        assert result is None

    def test_returns_none_when_new_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_certificates

        current = {"Protocol": "HTTPS", "Certificates": [{"CertificateArn": "arn:aws:acm:us-east-1:123:cert/old"}]}
        new = {"Protocol": "HTTPS"}

        result = _compare_certificates(current, new)
        assert result is None


class TestCompareDefaultActions:
    """Tests for _compare_default_actions helper function"""

    def test_returns_new_actions_when_current_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_default_actions

        current = {"Protocol": "HTTP"}
        new = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}]}

        result = _compare_default_actions(current, new)
        assert result == [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}]

    def test_returns_new_actions_when_different_length(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_default_actions

        current = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}]}
        new = {
            "Protocol": "HTTP",
            "DefaultActions": [
                {"Type": "forward", "TargetGroupArn": "arn:aws:...1"},
                {"Type": "forward", "TargetGroupArn": "arn:aws:...2"},
            ],
        }

        result = _compare_default_actions(current, new)
        assert result == new["DefaultActions"]

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners._rules._compare_rule_actions")
    def test_returns_new_actions_when_compare_returns_false(self, m_compare):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_default_actions

        m_compare.return_value = False
        current = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:...old"}]}
        new = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:...new"}]}

        result = _compare_default_actions(current, new)
        assert result == new["DefaultActions"]
        m_compare.assert_called_once_with(current["DefaultActions"], new["DefaultActions"])

    @patch("ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners._rules._compare_rule_actions")
    def test_returns_none_when_same(self, m_compare):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_default_actions

        m_compare.return_value = True
        current = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:...same"}]}
        new = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:...same"}]}

        result = _compare_default_actions(current, new)
        assert result is None

    def test_returns_none_when_new_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_default_actions

        current = {"Protocol": "HTTP", "DefaultActions": [{"Type": "forward", "TargetGroupArn": "arn:aws:..."}]}
        new = {"Protocol": "HTTP"}

        result = _compare_default_actions(current, new)
        assert result is None


class TestCompareAlpnPolicy:
    """Tests for _compare_alpn_policy helper function"""

    def test_returns_new_policy_when_protocol_changes_to_tls(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_alpn_policy

        current = {"Protocol": "TCP"}
        new = {"Protocol": "TLS", "AlpnPolicy": ["HTTP2Preferred"]}

        result = _compare_alpn_policy(current, new, "TLS")
        assert result == ["HTTP2Preferred"]

    def test_returns_new_policy_when_current_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_alpn_policy

        current = {"Protocol": "TLS"}
        new = {"Protocol": "TLS", "AlpnPolicy": ["HTTP2Preferred"]}

        result = _compare_alpn_policy(current, new, "TLS")
        assert result == ["HTTP2Preferred"]

    def test_returns_new_policy_when_different(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_alpn_policy

        current = {"Protocol": "TLS", "AlpnPolicy": ["HTTP1Only"]}
        new = {"Protocol": "TLS", "AlpnPolicy": ["HTTP2Preferred"]}

        result = _compare_alpn_policy(current, new, "TLS")
        assert result == ["HTTP2Preferred"]

    def test_returns_none_when_same(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_alpn_policy

        current = {"Protocol": "TLS", "AlpnPolicy": ["HTTP2Preferred"]}
        new = {"Protocol": "TLS", "AlpnPolicy": ["HTTP2Preferred"]}

        result = _compare_alpn_policy(current, new, "TLS")
        assert result is None

    def test_returns_none_when_new_missing(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_alpn_policy

        current = {"Protocol": "TLS", "AlpnPolicy": ["HTTP2Preferred"]}
        new = {"Protocol": "TLS"}

        result = _compare_alpn_policy(current, new, "TLS")
        assert result is None

    def test_returns_none_when_protocol_not_tls(self):
        from ansible_collections.amazon.aws.plugins.module_utils._elbv2.listeners import _compare_alpn_policy

        current = {"Protocol": "HTTPS"}
        new = {"Protocol": "HTTPS", "AlpnPolicy": ["HTTP2Preferred"]}

        result = _compare_alpn_policy(current, new, "HTTPS")
        assert result is None

#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2


class TestElBV2Utils:
    def setup_method(self):
        self.connection = MagicMock(name="connection")
        self.module = MagicMock(name="module")

        self.module.params = dict()

        self.conn_paginator = MagicMock(name="connection.paginator")
        self.paginate = MagicMock(name="paginator.paginate")

        self.connection.get_paginator.return_value = self.conn_paginator
        self.conn_paginator.paginate.return_value = self.paginate

        self.loadbalancer = {
            "Type": "application",
            "Scheme": "internet-facing",
            "IpAddressType": "ipv4",
            "VpcId": "vpc-3ac0fb5f",
            "AvailabilityZones": [
                {"ZoneName": "us-west-2a", "SubnetId": "subnet-8360a9e7"},
                {"ZoneName": "us-west-2b", "SubnetId": "subnet-b7d581c0"},
            ],
            "CreatedTime": "2016-03-25T21:26:12.920Z",
            "CanonicalHostedZoneId": "Z2P70J7EXAMPLE",
            "DNSName": "my-load-balancer-424835706.us-west-2.elb.amazonaws.com",
            "SecurityGroups": ["sg-5943793c"],
            "LoadBalancerName": "my-load-balancer",
            "State": {"Code": "active"},
            "LoadBalancerArn": (
                "arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/my-load-balancer/50dc6c495c0c9188"
            ),
        }
        self.paginate.build_full_result.return_value = {"LoadBalancers": [self.loadbalancer]}

        self.connection.describe_load_balancer_attributes.return_value = {
            "Attributes": [
                {"Value": "false", "Key": "access_logs.s3.enabled"},
                {"Value": "", "Key": "access_logs.s3.bucket"},
                {"Value": "", "Key": "access_logs.s3.prefix"},
                {"Value": "60", "Key": "idle_timeout.timeout_seconds"},
                {"Value": "false", "Key": "deletion_protection.enabled"},
                {"Value": "true", "Key": "routing.http2.enabled"},
                {"Value": "defensive", "Key": "routing.http.desync_mitigation_mode"},
                {"Value": "true", "Key": "routing.http.drop_invalid_header_fields.enabled"},
                {"Value": "true", "Key": "routing.http.x_amzn_tls_version_and_cipher_suite.enabled"},
                {"Value": "true", "Key": "routing.http.xff_client_port.enabled"},
                {"Value": "true", "Key": "waf.fail_open.enabled"},
            ]
        }
        self.connection.describe_tags.return_value = {
            "TagDescriptions": [
                {
                    "ResourceArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/my-load-balancer/50dc6c495c0c9188",
                    "Tags": [{"Value": "ansible", "Key": "project"}, {"Value": "RedHat", "Key": "company"}],
                }
            ]
        }
        self.elbv2obj = elbv2.ElasticLoadBalancerV2(self.connection, self.module)

    # Test the simplest case - Read the ip address type
    def test_get_elb_ip_address_type(self):
        # Run module
        return_value = self.elbv2obj.get_elb_ip_address_type()
        # check that no method was called and this has been retrieved from elb attributes
        self.connection.describe_load_balancer_attributes.assert_called_once()
        self.connection.get_paginator.assert_called_once()
        self.connection.describe_tags.assert_called_once()
        self.conn_paginator.paginate.assert_called_once()
        # assert we got the expected value
        assert return_value == "ipv4"

    # Test modify_ip_address_type idempotency
    def test_modify_ip_address_type_idempotency(self):
        # Run module
        self.elbv2obj.modify_ip_address_type("ipv4")
        # check that no method was called and this has been retrieved from elb attributes
        self.connection.set_ip_address_type.assert_not_called()
        # assert we got the expected value
        assert self.elbv2obj.changed is False

    # Test modify_ip_address_type
    def test_modify_ip_address_type_update(self):
        # Run module
        self.elbv2obj.modify_ip_address_type("dualstack")
        # check that no method was called and this has been retrieved from elb attributes
        self.connection.set_ip_address_type.assert_called_once()
        # assert we got the expected value
        assert self.elbv2obj.changed is True

    # Test get_elb_attributes
    def test_get_elb_attributes(self):
        # Build expected result
        expected_elb_attributes = {
            "access_logs_s3_bucket": "",
            "access_logs_s3_enabled": "false",
            "access_logs_s3_prefix": "",
            "deletion_protection_enabled": "false",
            "idle_timeout_timeout_seconds": "60",
            "routing_http2_enabled": "true",
            "routing_http_desync_mitigation_mode": "defensive",
            "routing_http_drop_invalid_header_fields_enabled": "true",
            "routing_http_x_amzn_tls_version_and_cipher_suite_enabled": "true",
            "routing_http_xff_client_port_enabled": "true",
            "waf_fail_open_enabled": "true",
        }
        # Run module
        actual_elb_attributes = self.elbv2obj.get_elb_attributes()
        # Assert we got the expected result
        assert actual_elb_attributes == expected_elb_attributes

    @pytest.mark.parametrize(
        "subnets,subnet_mappings,elb_subnets,expected",
        [
            (
                None,
                [{"SubnetId": "subnet-abc", "AllocationId": "eipalloc-abc"}],
                [{"SubnetId": "subnet-abc", "LoadBalancerAddresses": [{"AllocationId": "eipalloc-abc"}]}],
                True,
            ),
            (
                ["subnet-abc"],
                None,
                [{"SubnetId": "subnet-abc", "LoadBalancerAddresses": [{"AllocationId": "eipalloc-abc"}]}],
                False,
            ),
            (["subnet-abc"], None, [{"SubnetId": "subnet-abc"}], True),
            (
                None,
                [
                    {"SubnetId": "subnet-123", "AllocationId": "eipalloc-123"},
                    {"SubnetId": "subnet-abc", "AllocationId": "eipalloc-abc"},
                ],
                [
                    {"SubnetId": "subnet-abc", "LoadBalancerAddresses": [{"AllocationId": "eipalloc-abc"}]},
                    {"SubnetId": "subnet-123", "LoadBalancerAddresses": [{"AllocationId": "eipalloc-123"}]},
                ],
                True,
            ),
        ],
    )
    def test_compare_subnets(self, subnets, subnet_mappings, elb_subnets, expected):
        self.elbv2obj.subnets = subnets
        self.elbv2obj.subnet_mappings = subnet_mappings
        self.elbv2obj.elb = {"AvailabilityZones": elb_subnets}
        assert expected == self.elbv2obj.compare_subnets()


def createListener(**kwargs):
    result = {"Port": 80, "Protocol": "TCP"}
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
    "listeners,expected",
    [
        ([{"Port": 20, "AlpnPolicy": "HTTP2Optional"}], [{"Port": 20, "AlpnPolicy": ["HTTP2Optional"]}]),
        (
            [{"Port": 20, "AlpnPolicy": "HTTP2Optional"}, {"Port": 10, "AlpnPolicy": "HTTP2Only"}, {"Port": 30}],
            [{"Port": 20, "AlpnPolicy": ["HTTP2Optional"]}, {"Port": 10, "AlpnPolicy": ["HTTP2Only"]}, {"Port": 30}],
        ),
    ],
)
def test___ensure_listeners_alpn_policy(listeners, expected):
    assert expected == elbv2._ensure_listeners_alpn_policy(listeners)


def test__ensure_listeners_default_action_has_arn(mocker):
    connection = MagicMock()
    module = MagicMock()

    target_group = "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/my-targets/00000"
    listeners = [
        {"DefaultActions": [{"TargetGroupName": "a"}]},
        {"DefaultActions": [{"TargetGroupArn": target_group + "b"}]},
    ]

    expected = [
        {"DefaultActions": [{"TargetGroupArn": target_group + "a"}]},
        {"DefaultActions": [{"TargetGroupArn": target_group + "b"}]},
    ]

    mocker.patch("ansible_collections.amazon.aws.plugins.module_utils.elbv2.convert_tg_name_to_arn").side_effect = (
        lambda connection, module, name: target_group + name
    )
    assert expected == elbv2._ensure_listeners_default_action_has_arn(connection, module, listeners)


@pytest.mark.parametrize(
    "current_listeners,new_listeners,expected",
    [
        (
            [
                {"Port": 80, "Protocol": "TCP", "ListenerArn": "arn80"},
                {"Port": 90, "Protocol": "UDP", "ListenerArn": "arn90"},
                {"Port": 100, "Protocol": "TLS", "ListenerArn": "arn100"},
            ],
            [{"Port": 80, "Protocol": "TCP"}, {"Port": 90, "Protocol": "HTTPS"}, {"Port": 101, "Protocol": "UDP"}],
            {
                "add": [{"Port": 101, "Protocol": "UDP"}],
                "modify": [{"Port": 90, "Protocol": "HTTPS", "ListenerArn": "arn90"}],
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

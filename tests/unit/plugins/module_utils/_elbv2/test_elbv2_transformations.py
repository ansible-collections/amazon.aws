# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _normalize_attributes
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _normalize_listener_actions
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _normalize_listener_rules
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _normalize_listeners
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _sort_actions
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import (
    normalize_application_load_balancer,
)

# The various normalize_ functions are based upon ..transformation.boto3_resource_to_ansible_dict
# As such these tests will be relatively light touch.


class TestNormalizeAttributes:
    def test_normalize_attributes_converts_format(self):
        """Test that attributes are converted from boto3 format to dict with underscored keys"""
        INPUT = [
            {"Key": "access_logs.s3.enabled", "Value": "true"},
            {"Key": "access_logs.s3.bucket", "Value": "my-bucket"},
            {"Key": "deletion_protection.enabled", "Value": "false"},
            {"Key": "idle_timeout.timeout_seconds", "Value": "60"},
        ]
        OUTPUT = {
            "access_logs_s3_enabled": "true",
            "access_logs_s3_bucket": "my-bucket",
            "deletion_protection_enabled": "false",
            "idle_timeout_timeout_seconds": "60",
        }

        assert OUTPUT == _normalize_attributes(INPUT)

    def test_normalize_attributes_handles_empty_list(self):
        """Test that empty attributes list returns empty dict"""
        assert {} == _normalize_attributes([])

    def test_normalize_attributes_handles_none(self):
        """Test that None attributes returns empty dict"""
        assert {} == _normalize_attributes(None)


class TestSortActions:
    def test_sort_actions_by_order(self):
        """Test that actions are sorted by Order field"""
        INPUT = [
            {"Order": 3, "Type": "forward"},
            {"Order": 1, "Type": "authenticate-oidc"},
            {"Order": 2, "Type": "forward"},
        ]
        OUTPUT = [
            {"Order": 1, "Type": "authenticate-oidc"},
            {"Order": 2, "Type": "forward"},
            {"Order": 3, "Type": "forward"},
        ]

        assert OUTPUT == _sort_actions(INPUT)

    def test_sort_actions_by_order_and_type(self):
        """Test that actions with same Order are sorted by Type for stability"""
        INPUT = [
            {"Order": 1, "Type": "forward"},
            {"Order": 1, "Type": "authenticate-oidc"},
            {"Order": 1, "Type": "fixed-response"},
        ]
        OUTPUT = [
            {"Order": 1, "Type": "authenticate-oidc"},
            {"Order": 1, "Type": "fixed-response"},
            {"Order": 1, "Type": "forward"},
        ]

        assert OUTPUT == _sort_actions(INPUT)

    def test_sort_actions_with_default_order(self):
        """Test that actions without Order default to 0"""
        INPUT = [
            {"Type": "forward", "TargetGroupArn": "arn:aws:..."},
            {"Order": 2, "Type": "authenticate-oidc"},
            {"Order": 1, "Type": "fixed-response"},
        ]
        OUTPUT = [
            {"Type": "forward", "TargetGroupArn": "arn:aws:..."},
            {"Order": 1, "Type": "fixed-response"},
            {"Order": 2, "Type": "authenticate-oidc"},
        ]

        assert OUTPUT == _sort_actions(INPUT)

    def test_sort_actions_empty_list(self):
        """Test that empty actions list is handled correctly"""
        assert [] == _sort_actions([])

    def test_sort_actions_none(self):
        """Test that None actions list is handled correctly"""
        assert _sort_actions(None) is None


class TestNormalizeListenerActions:
    def test_normalize_listener_actions_sorts_and_converts(self):
        """Test that listener actions are sorted and converted to snake_case"""
        INPUT = [
            {"Order": 2, "Type": "forward", "TargetGroupArn": "arn:aws:...2"},
            {"Order": 1, "Type": "authenticate-oidc", "AuthenticateOidcConfig": {}},
        ]
        OUTPUT = [
            {"order": 1, "type": "authenticate-oidc", "authenticate_oidc_config": {}},
            {"order": 2, "type": "forward", "target_group_arn": "arn:aws:...2"},
        ]

        assert OUTPUT == _normalize_listener_actions(INPUT)

    def test_normalize_listener_actions_empty_list(self):
        """Test that empty actions list is handled correctly"""
        assert [] == _normalize_listener_actions([])

    def test_normalize_listener_actions_none(self):
        """Test that None actions list is handled correctly"""
        assert _normalize_listener_actions(None) is None


class TestNormalizeListenerRules:
    def test_sort_listener_rules_by_priority(self):
        """Test that listener rules are sorted numerically by priority"""
        INPUT = [
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/3", "Priority": "10", "IsDefault": False},
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/1", "Priority": "1", "IsDefault": False},
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/4", "Priority": "default", "IsDefault": True},
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/2", "Priority": "5", "IsDefault": False},
        ]
        OUTPUT = [
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/1", "priority": "1", "is_default": False},
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/2", "priority": "5", "is_default": False},
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/3", "priority": "10", "is_default": False},
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/4", "priority": "default", "is_default": True},
        ]

        assert OUTPUT == _normalize_listener_rules(INPUT)

    def test_default_rule_appears_last(self):
        """Test that the default rule always appears last regardless of input order"""
        INPUT = [
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/1", "Priority": "default", "IsDefault": True},
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/2", "Priority": "1", "IsDefault": False},
            {"RuleArn": "arn:aws:elasticloadbalancing:::rule/3", "Priority": "2", "IsDefault": False},
        ]
        OUTPUT = [
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/2", "priority": "1", "is_default": False},
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/3", "priority": "2", "is_default": False},
            {"rule_arn": "arn:aws:elasticloadbalancing:::rule/1", "priority": "default", "is_default": True},
        ]

        assert OUTPUT == _normalize_listener_rules(INPUT)

    def test_empty_rules_list(self):
        """Test that empty rules list is handled correctly"""
        assert [] == _normalize_listener_rules([])

    def test_none_rules_list(self):
        """Test that None rules list is handled correctly"""
        assert _normalize_listener_rules(None) is None


class TestNormalizeListeners:
    def test_normalize_listeners_with_rules(self):
        """Test that listeners are normalized and rules are sorted"""
        INPUT = [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:::listener/1",
                "Port": 80,
                "Protocol": "HTTP",
                "Rules": [
                    {"RuleArn": "arn:aws:elasticloadbalancing:::rule/2", "Priority": "5", "IsDefault": False},
                    {"RuleArn": "arn:aws:elasticloadbalancing:::rule/1", "Priority": "1", "IsDefault": False},
                    {"RuleArn": "arn:aws:elasticloadbalancing:::rule/3", "Priority": "default", "IsDefault": True},
                ],
            }
        ]
        OUTPUT = [
            {
                "listener_arn": "arn:aws:elasticloadbalancing:::listener/1",
                "port": 80,
                "protocol": "HTTP",
                "rules": [
                    {"rule_arn": "arn:aws:elasticloadbalancing:::rule/1", "priority": "1", "is_default": False},
                    {"rule_arn": "arn:aws:elasticloadbalancing:::rule/2", "priority": "5", "is_default": False},
                    {"rule_arn": "arn:aws:elasticloadbalancing:::rule/3", "priority": "default", "is_default": True},
                ],
            }
        ]

        assert OUTPUT == _normalize_listeners(INPUT)

    def test_normalize_listeners_without_rules(self):
        """Test that listeners without rules are handled correctly"""
        INPUT = [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:::listener/1",
                "Port": 443,
                "Protocol": "HTTPS",
            }
        ]
        OUTPUT = [
            {
                "listener_arn": "arn:aws:elasticloadbalancing:::listener/1",
                "port": 443,
                "protocol": "HTTPS",
            }
        ]

        assert OUTPUT == _normalize_listeners(INPUT)

    def test_normalize_listeners_with_default_actions(self):
        """Test that DefaultActions are sorted by Order and Type"""
        INPUT = [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:::listener/1",
                "Port": 80,
                "Protocol": "HTTP",
                "DefaultActions": [
                    {"Order": 2, "Type": "forward", "TargetGroupArn": "arn:aws:..."},
                    {"Order": 1, "Type": "authenticate-oidc", "AuthenticateOidcConfig": {}},
                ],
            }
        ]
        OUTPUT = [
            {
                "listener_arn": "arn:aws:elasticloadbalancing:::listener/1",
                "port": 80,
                "protocol": "HTTP",
                "default_actions": [
                    {"order": 1, "type": "authenticate-oidc", "authenticate_oidc_config": {}},
                    {"order": 2, "type": "forward", "target_group_arn": "arn:aws:..."},
                ],
            }
        ]

        assert OUTPUT == _normalize_listeners(INPUT)

    def test_normalize_listeners_with_rules_containing_actions(self):
        """Test that Actions within Rules are sorted by Order and Type"""
        INPUT = [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:::listener/1",
                "Port": 80,
                "Protocol": "HTTP",
                "Rules": [
                    {
                        "RuleArn": "arn:aws:elasticloadbalancing:::rule/1",
                        "Priority": "1",
                        "IsDefault": False,
                        "Actions": [
                            {"Order": 2, "Type": "forward", "TargetGroupArn": "arn:aws:..."},
                            {"Order": 1, "Type": "authenticate-oidc", "AuthenticateOidcConfig": {}},
                        ],
                    },
                ],
            }
        ]
        OUTPUT = [
            {
                "listener_arn": "arn:aws:elasticloadbalancing:::listener/1",
                "port": 80,
                "protocol": "HTTP",
                "rules": [
                    {
                        "rule_arn": "arn:aws:elasticloadbalancing:::rule/1",
                        "priority": "1",
                        "is_default": False,
                        "actions": [
                            {"order": 1, "type": "authenticate-oidc", "authenticate_oidc_config": {}},
                            {"order": 2, "type": "forward", "target_group_arn": "arn:aws:..."},
                        ],
                    },
                ],
            }
        ]

        assert OUTPUT == _normalize_listeners(INPUT)


class TestNormalizeApplicationLoadBalancer:
    def test_normalize_application_load_balancer(self):
        """Test complete ALB normalization with listeners and sorted rules"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "IpAddressType": "ipv4",
            "Tags": [
                {"Key": "Name", "Value": "test-alb"},
                {"Key": "Environment", "Value": "test"},
            ],
            "Listeners": [
                {
                    "ListenerArn": "arn:aws:elasticloadbalancing:::listener/1",
                    "Port": 80,
                    "Protocol": "HTTP",
                    "Rules": [
                        {"RuleArn": "arn:aws:elasticloadbalancing:::rule/3", "Priority": "default", "IsDefault": True},
                        {"RuleArn": "arn:aws:elasticloadbalancing:::rule/1", "Priority": "1", "IsDefault": False},
                        {"RuleArn": "arn:aws:elasticloadbalancing:::rule/2", "Priority": "10", "IsDefault": False},
                    ],
                }
            ],
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "ip_address_type": "ipv4",
            "tags": {
                "Name": "test-alb",
                "Environment": "test",
            },
            "listeners": [
                {
                    "listener_arn": "arn:aws:elasticloadbalancing:::listener/1",
                    "port": 80,
                    "protocol": "HTTP",
                    "rules": [
                        {"rule_arn": "arn:aws:elasticloadbalancing:::rule/1", "priority": "1", "is_default": False},
                        {"rule_arn": "arn:aws:elasticloadbalancing:::rule/2", "priority": "10", "is_default": False},
                        {
                            "rule_arn": "arn:aws:elasticloadbalancing:::rule/3",
                            "priority": "default",
                            "is_default": True,
                        },
                    ],
                }
            ],
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_without_listeners(self):
        """Test ALB normalization without listeners"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "IpAddressType": "dualstack",
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "ip_address_type": "dualstack",
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_with_empty_tags(self):
        """Test ALB normalization with empty tags list converts to empty dict"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "Tags": [],
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "tags": {},
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_with_tags(self):
        """Test ALB normalization with tags are properly converted"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "Tags": [
                {"Key": "Name", "Value": "test-alb"},
                {"Key": "Environment", "Value": "production"},
            ],
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "tags": {
                "Name": "test-alb",
                "Environment": "production",
            },
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_without_tags(self):
        """Test ALB normalization without Tags key - tags should not be added"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_none_alb(self):
        """Test that None ALB is handled correctly"""
        assert normalize_application_load_balancer(None) is None

    def test_normalize_alb_with_attributes(self):
        """Test ALB normalization with attributes are flattened and converted"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "Attributes": [
                {"Key": "access_logs.s3.enabled", "Value": "true"},
                {"Key": "access_logs.s3.bucket", "Value": "my-bucket"},
                {"Key": "deletion_protection.enabled", "Value": "false"},
            ],
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "access_logs_s3_enabled": "true",
            "access_logs_s3_bucket": "my-bucket",
            "deletion_protection_enabled": "false",
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_with_attributes_and_tags(self):
        """Test ALB normalization with both attributes and tags"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "Attributes": [
                {"Key": "access_logs.s3.enabled", "Value": "true"},
                {"Key": "deletion_protection.enabled", "Value": "false"},
            ],
            "Tags": [
                {"Key": "Name", "Value": "test-alb"},
                {"Key": "Owner", "Value": "devops"},
            ],
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "access_logs_s3_enabled": "true",
            "deletion_protection_enabled": "false",
            "tags": {
                "Name": "test-alb",
                "Owner": "devops",
            },
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_without_attributes(self):
        """Test ALB normalization without Attributes key"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_alb_with_empty_attributes(self):
        """Test ALB normalization with empty Attributes list"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
            "Attributes": [],
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

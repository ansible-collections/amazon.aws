# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _normalize_listener_rules
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import _normalize_listeners
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.transformations import (
    normalize_application_load_balancer,
)

# The various normalize_ functions are based upon ..transformation.boto3_resource_to_ansible_dict
# As such these tests will be relatively light touch.


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
            "tags": {},
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

    def test_normalize_alb_without_tags(self):
        """Test ALB normalization without Tags key"""
        INPUT = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "LoadBalancerName": "test-alb",
        }
        OUTPUT = {
            "load_balancer_arn": "arn:aws:elasticloadbalancing:::loadbalancer/app/test/123",
            "load_balancer_name": "test-alb",
            "tags": {},
        }

        assert OUTPUT == normalize_application_load_balancer(INPUT)

    def test_normalize_none_alb(self):
        """Test that None ALB is handled correctly"""
        assert normalize_application_load_balancer(None) is None

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2
from ansible_collections.amazon.aws.plugins.module_utils._elbv2 import rules

example_arn = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/73e2d6bc24d8a067"
example_arn2 = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/other-targets/abcdef0123456789"


class TestCompareRuleActions:
    """Tests for _compare_rule_actions function"""

    def test_empty_actions(self):
        """Empty action lists should match"""
        assert elbv2._compare_rule_actions([], []) is True

    def test_different_lengths(self):
        """Actions with different lengths should not match"""
        current = [{"Type": "forward", "TargetGroupArn": example_arn}]
        new = []
        assert elbv2._compare_rule_actions(current, new) is False

        current = []
        new = [{"Type": "forward", "TargetGroupArn": example_arn}]
        assert elbv2._compare_rule_actions(current, new) is False

    def test_simple_forward_action_match(self):
        """Simple forward actions that match"""
        current = [{"Type": "forward", "TargetGroupArn": example_arn}]
        new = [{"Type": "forward", "TargetGroupArn": example_arn}]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_simple_forward_action_different_arn(self):
        """Simple forward actions with different ARNs should not match"""
        current = [{"Type": "forward", "TargetGroupArn": example_arn}]
        new = [{"Type": "forward", "TargetGroupArn": example_arn2}]
        assert elbv2._compare_rule_actions(current, new) is False

    def test_forward_config_pruning(self):
        """ForwardConfig should be pruned when redundant"""
        current = [
            {
                "Type": "forward",
                "TargetGroupArn": example_arn,
                "ForwardConfig": {
                    "TargetGroupStickinessConfig": {"Enabled": False},
                    "TargetGroups": [{"TargetGroupArn": example_arn, "Weight": 1}],
                },
            }
        ]
        new = [{"Type": "forward", "TargetGroupArn": example_arn}]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_forward_config_not_pruned_when_complex(self):
        """ForwardConfig should not be pruned when it contains non-default config"""
        current = [
            {
                "Type": "forward",
                "TargetGroupArn": example_arn,
                "ForwardConfig": {
                    "TargetGroupStickinessConfig": {"Enabled": True, "DurationSeconds": 3600},
                    "TargetGroups": [{"TargetGroupArn": example_arn}],
                },
            }
        ]
        new = [{"Type": "forward", "TargetGroupArn": example_arn}]
        assert elbv2._compare_rule_actions(current, new) is False

    def test_forward_config_multiple_target_groups(self):
        """ForwardConfig with multiple target groups should not be simplified"""
        current = [
            {
                "Type": "forward",
                "TargetGroupArn": example_arn,
                "ForwardConfig": {
                    "TargetGroupStickinessConfig": {"Enabled": False},
                    "TargetGroups": [
                        {"TargetGroupArn": example_arn, "Weight": 1},
                        {"TargetGroupArn": example_arn2, "Weight": 1},
                    ],
                },
            }
        ]
        new = [
            {
                "Type": "forward",
                "TargetGroupArn": example_arn,
                "ForwardConfig": {
                    "TargetGroupStickinessConfig": {"Enabled": False},
                    "TargetGroups": [
                        {"TargetGroupArn": example_arn, "Weight": 1},
                        {"TargetGroupArn": example_arn2, "Weight": 1},
                    ],
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_oidc_action_without_client_secret(self):
        """OIDC actions without ClientSecret should match when UseExistingClientSecret is added"""
        current = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            }
        ]
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "UseExistingClientSecret": True,
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_oidc_action_with_client_secret_removed(self):
        """OIDC actions should match when ClientSecret is removed due to UseExistingClientSecret"""
        current = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            }
        ]
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "ClientSecret": "my-secret",
                    "UseExistingClientSecret": True,
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_oidc_action_different_config(self):
        """OIDC actions with different configs should not match"""
        current = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            }
        ]
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://different.com",
                    "AuthorizationEndpoint": "https://different.com/auth",
                    "TokenEndpoint": "https://different.com/token",
                    "UserInfoEndpoint": "https://different.com/userinfo",
                    "ClientId": "different-client-id",
                    "UseExistingClientSecret": True,
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is False

    def test_multiple_actions_same_order(self):
        """Multiple actions in the same order should match"""
        current = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            },
            {"Type": "forward", "Order": 2, "TargetGroupArn": example_arn},
        ]
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "UseExistingClientSecret": True,
                },
            },
            {"Type": "forward", "Order": 2, "TargetGroupArn": example_arn},
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_multiple_actions_different_order(self):
        """Actions are sorted by Order before comparison, so different input order should still match"""
        current = [
            {"Type": "forward", "Order": 2, "TargetGroupArn": example_arn},
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            },
        ]
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "UseExistingClientSecret": True,
                },
            },
            {"Type": "forward", "Order": 2, "TargetGroupArn": example_arn},
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_redirect_action(self):
        """Redirect actions should be compared correctly"""
        current = [
            {
                "Type": "redirect",
                "Order": 1,
                "RedirectConfig": {
                    "Protocol": "HTTPS",
                    "Port": "443",
                    "Host": "#{host}",
                    "Path": "/#{path}",
                    "Query": "#{query}",
                    "StatusCode": "HTTP_301",
                },
            }
        ]
        new = [
            {
                "Type": "redirect",
                "Order": 1,
                "RedirectConfig": {
                    "Protocol": "HTTPS",
                    "Port": "443",
                    "Host": "#{host}",
                    "Path": "/#{path}",
                    "Query": "#{query}",
                    "StatusCode": "HTTP_301",
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_fixed_response_action(self):
        """Fixed response actions should be compared correctly"""
        current = [
            {
                "Type": "fixed-response",
                "Order": 1,
                "FixedResponseConfig": {
                    "StatusCode": "200",
                    "ContentType": "text/plain",
                    "MessageBody": "OK",
                },
            }
        ]
        new = [
            {
                "Type": "fixed-response",
                "Order": 1,
                "FixedResponseConfig": {
                    "StatusCode": "200",
                    "ContentType": "text/plain",
                    "MessageBody": "OK",
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_cognito_action(self):
        """Cognito authentication actions should be compared correctly"""
        current = [
            {
                "Type": "authenticate-cognito",
                "Order": 1,
                "AuthenticateCognitoConfig": {
                    "UserPoolArn": "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_abcdefghi",
                    "UserPoolClientId": "my-client-id",
                    "UserPoolDomain": "my-domain",
                    "SessionTimeout": 604800,
                    "Scope": "openid",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                    "OnUnauthenticatedRequest": "authenticate",
                },
            }
        ]
        new = [
            {
                "Type": "authenticate-cognito",
                "Order": 1,
                "AuthenticateCognitoConfig": {
                    "UserPoolArn": "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_abcdefghi",
                    "UserPoolClientId": "my-client-id",
                    "UserPoolDomain": "my-domain",
                    "SessionTimeout": 604800,
                    "Scope": "openid",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                    "OnUnauthenticatedRequest": "authenticate",
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_oidc_default_values_added(self):
        """OIDC actions should match when default values are added during pruning"""
        current = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            }
        ]
        # New action without optional fields - defaults should be added during comparison
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "UseExistingClientSecret": True,
                    # Defaults will be added: Scope, SessionTimeout, OnUnauthenticatedRequest, SessionCookieName
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is True

    def test_oidc_non_default_scope(self):
        """OIDC actions with non-default scope should not match default"""
        current = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "Scope": "openid profile email",
                    "SessionTimeout": 604800,
                    "OnUnauthenticatedRequest": "authenticate",
                    "SessionCookieName": "AWSELBAuthSessionCookie",
                },
            }
        ]
        new = [
            {
                "Type": "authenticate-oidc",
                "Order": 1,
                "AuthenticateOidcConfig": {
                    "Issuer": "https://example.com",
                    "AuthorizationEndpoint": "https://example.com/auth",
                    "TokenEndpoint": "https://example.com/token",
                    "UserInfoEndpoint": "https://example.com/userinfo",
                    "ClientId": "my-client-id",
                    "UseExistingClientSecret": True,
                    # Will get default Scope: "openid"
                },
            }
        ]
        assert elbv2._compare_rule_actions(current, new) is False


@pytest.fixture(name="elb_listener_rules")
def fixture_elb_listener_rules(mocker):
    module = MagicMock()
    connection = MagicMock()
    rules = MagicMock()
    listener_arn = MagicMock()

    return elbv2.ELBListenerRules(connection, module, listener_arn, rules)


example_arn = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/nlb-123456789abc/abcdef0123456789"
example_arn2 = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/nlb-0123456789ab/0123456789abcdef"


test_rules = [
    (
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                        "OnUnauthenticatedRequest": "authenticate",
                        "SessionCookieName": "AWSELBAuthSessionCookie",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UseExistingClientSecret": True,
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {},
    ),
    (
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                        "OnUnauthenticatedRequest": "authenticate",
                        "SessionCookieName": "AWSELBAuthSessionCookie",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UseExistingClientSecret": True,
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                        "OnUnauthenticatedRequest": "authenticate",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {},
    ),
    (
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                        "OnUnauthenticatedRequest": "authenticate",
                        "SessionCookieName": "AWSELBAuthSessionCookie",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UseExistingClientSecret": True,
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                        "OnUnauthenticatedRequest": "deny",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {
            "Actions": [
                {
                    "AuthenticateOidcConfig": {
                        "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                        "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        "Issuer": "https://samples.auth0.com",
                        "Scope": "openid",
                        "SessionTimeout": 604800,
                        "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                        "UseExistingClientSecret": True,
                        "UserInfoEndpoint": "https://samples.auth0.com/userinfo",
                        "OnUnauthenticatedRequest": "deny",
                    },
                    "Order": 1,
                    "Type": "authenticate-oidc",
                }
            ],
        },
    ),
    (
        {
            "Actions": [{"TargetGroupName": "my_target_group", "Type": "forward"}],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test", "/prod"]}],
            "Priority": 2,
        },
        {
            "Actions": [{"TargetGroupName": "my_target_group", "Type": "forward"}],
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
            "Priority": 2,
        },
        {
            "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
        },
    ),
]


@pytest.mark.parametrize("current_rule,new_rule,modified_rule", test_rules)
def test__compare_rule(current_rule, new_rule, modified_rule):
    assert modified_rule == elbv2._compare_rule(current_rule, new_rule)


test_listener_arn = "arn:aws:elasticloadbalancing:us-west-2:123456789012:listener/app/my-load-balancer/50dc6c495c0c9188/f2f7dc8efc522ab2"

test_listeners_rules = [
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/abc",
            },
            {
                "Priority": "2",
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/123",
            },
        ],
        [
            {
                "Priority": 2,
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
            },
            {
                "Priority": 1,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
            },
        ],
        {},
    ),
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/abc",
            },
            {
                "Priority": "2",
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/123",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
            },
            {
                "Priority": 2,
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "Issuer": "https://sample.oauth.com/issuer",
                            "AuthorizationEndpoint": "https://sample.oauth.com",
                            "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                            "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                            "ClientId": "id123645",
                            "ClientSecret": "testSecret123!@#$",
                            "UseExistingClientSecret": True,
                        },
                    },
                ],
            },
            {
                "Priority": 3,
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
            },
        ],
        {
            "to_set_priority": [
                {
                    "Priority": 3,
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/123",
                }
            ],
            "to_add": [
                {
                    "Priority": 2,
                    "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                    "ListenerArn": test_listener_arn,
                    "Actions": [
                        {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                        {
                            "Type": "authenticate-oidc",
                            "Order": 1,
                            "AuthenticateOidcConfig": {
                                "Issuer": "https://sample.oauth.com/issuer",
                                "AuthorizationEndpoint": "https://sample.oauth.com",
                                "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                                "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                                "ClientId": "id123645",
                                "ClientSecret": "testSecret123!@#$",
                                "UseExistingClientSecret": False,
                            },
                        },
                    ],
                },
            ],
        },
    ),
    (
        [
            {
                "Priority": "2",
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/abc",
            },
            {
                "Priority": "1",
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/123",
            },
        ],
        [
            {
                "Priority": 2,
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
            },
            {
                "Priority": 1,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
            },
        ],
        {
            "to_set_priority": [
                {
                    "Priority": 2,
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/123",
                },
                {
                    "Priority": 1,
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/abc",
                },
            ]
        },
    ),
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/abc",
            },
            {
                "Priority": "2",
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/123",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
            },
            {
                "Priority": 2,
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
            },
            {
                "Priority": 3,
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "Issuer": "https://sample.oauth.com/issuer",
                            "AuthorizationEndpoint": "https://sample.oauth.com",
                            "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                            "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                            "ClientId": "id123645",
                            "ClientSecret": "testSecret123!@#$",
                            "UseExistingClientSecret": True,
                        },
                    },
                ],
            },
        ],
        {
            "to_add": [
                {
                    "Priority": 3,
                    "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                    "ListenerArn": test_listener_arn,
                    "Actions": [
                        {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                        {
                            "Type": "authenticate-oidc",
                            "Order": 1,
                            "AuthenticateOidcConfig": {
                                "Issuer": "https://sample.oauth.com/issuer",
                                "AuthorizationEndpoint": "https://sample.oauth.com",
                                "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                                "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                                "ClientId": "id123645",
                                "ClientSecret": "testSecret123!@#$",
                                "UseExistingClientSecret": False,
                            },
                        },
                    ],
                },
            ]
        },
    ),
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/abc",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
            },
            {
                "Priority": 2,
                "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
            },
        ],
        {
            "to_add": [
                {
                    "Priority": 2,
                    "ListenerArn": test_listener_arn,
                    "Conditions": [{"Field": "host-header", "Values": ["yolo.rocks"]}],
                    "Actions": [{"TargetGroupName": "target2", "Type": "forward"}],
                },
            ]
        },
    ),
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "Issuer": "https://sample.oauth.com/issuer",
                            "AuthorizationEndpoint": "https://sample.oauth.com",
                            "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                            "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                            "ClientId": "id123645",
                        },
                    },
                ],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/oidc",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "Issuer": "https://sample.oauth.com/issuer",
                            "AuthorizationEndpoint": "https://sample.oauth.com",
                            "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                            "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                            "ClientId": "id123645",
                            "ClientSecret": "testSecret123!@#$",
                            "UseExistingClientSecret": True,
                        },
                    },
                ],
            }
        ],
        {
            "to_modify": [
                {
                    "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                    "Actions": [
                        {"TargetGroupName": "oidc-target-01", "Type": "forward", "Order": 2},
                        {
                            "Type": "authenticate-oidc",
                            "Order": 1,
                            "AuthenticateOidcConfig": {
                                "Issuer": "https://sample.oauth.com/issuer",
                                "AuthorizationEndpoint": "https://sample.oauth.com",
                                "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                                "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                                "ClientId": "id123645",
                                "ClientSecret": "testSecret123!@#$",
                                "UseExistingClientSecret": False,
                            },
                        },
                    ],
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/oidc",
                },
            ]
        },
    ),
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "Issuer": "https://sample.oauth.com/issuer",
                            "AuthorizationEndpoint": "https://sample.oauth.com",
                            "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                            "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                            "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                        },
                    },
                ],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/oidc",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "Issuer": "https://sample.oauth.com/issuer",
                            "AuthorizationEndpoint": "https://sample.oauth.com",
                            "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                            "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                            "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                            "ClientSecret": "testSecret123!@#$",
                        },
                    },
                ],
            }
        ],
        {
            "to_modify": [
                {
                    "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                    "Actions": [
                        {
                            "Type": "authenticate-oidc",
                            "Order": 1,
                            "AuthenticateOidcConfig": {
                                "Issuer": "https://sample.oauth.com/issuer",
                                "AuthorizationEndpoint": "https://sample.oauth.com",
                                "TokenEndpoint": "https://sample.oauth.com/oauth/token",
                                "UserInfoEndpoint": "https://sample.oauth.com/userinfo",
                                "ClientId": "kbyuFDidLLm280LIwVFiazOqjO3ty8KH",
                                "ClientSecret": "testSecret123!@#$",
                                "UseExistingClientSecret": False,
                            },
                        },
                    ],
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/oidc",
                },
            ]
        },
    ),
    (
        [
            {
                "Priority": "1",
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                            "ClientId": "abcdef1234567890",
                            "Issuer": "https://samples.auth0.com/",
                            "OnUnauthenticatedRequest": "authenticate",
                            "Scope": "openid",
                            "SessionCookieName": "AWSELBAuthSessionCookie",
                            "SessionTimeout": 604800,
                            "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                            "UserInfoEndpoint": "https://samples.auth0.com/oauth/userinfo",
                        },
                    },
                ],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/oidc",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "path-pattern", "Values": ["/test"]}],
                "Actions": [
                    {
                        "Type": "authenticate-oidc",
                        "Order": 1,
                        "AuthenticateOidcConfig": {
                            "AuthorizationEndpoint": "https://samples.auth0.com/authorize",
                            "ClientId": "abcdef1234567890",
                            "Issuer": "https://samples.auth0.com/",
                            "OnUnauthenticatedRequest": "authenticate",
                            "Scope": "openid",
                            "TokenEndpoint": "https://samples.auth0.com/oauth/token",
                            "UserInfoEndpoint": "https://samples.auth0.com/oauth/userinfo",
                            "UseExistingClientSecret": True,
                        },
                    },
                ],
            }
        ],
        {},
    ),
    (
        [
            {
                "Priority": "default",
                "IsDefault": True,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/default",
            },
            {
                "Priority": "1",
                "IsDefault": False,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/rule-1",
            },
        ],
        [
            {
                "Priority": 1,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "another_target", "Type": "forward"}],
            },
        ],
        {
            "to_modify": [
                {
                    "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                    "Actions": [{"TargetGroupName": "another_target", "Type": "forward"}],
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/rule-1",
                },
            ]
        },
    ),
    (
        [
            {
                "Priority": "default",
                "IsDefault": True,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/default",
            },
            {
                "Priority": "1",
                "IsDefault": False,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
                "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/rule-1",
            },
        ],
        [
            {
                "Priority": 2,
                "Conditions": [{"Field": "host-header", "Values": ["bla.tld"]}],
                "Actions": [{"TargetGroupName": "target1", "Type": "forward"}],
            },
        ],
        {
            "to_set_priority": [
                {
                    "Priority": 2,
                    "RuleArn": "arn:aws:elasticloadbalancing:::listener-rule/app/ansible-test/rule-1",
                },
            ]
        },
    ),
]


@pytest.mark.parametrize("current_rules,rules,expected", test_listeners_rules)
def test_compare_rules(elb_listener_rules, current_rules, rules, expected):
    elb_listener_rules.rules = rules
    elb_listener_rules.current_rules = current_rules
    elb_listener_rules.listener_arn = test_listener_arn
    rules_to_add, rules_to_set_priority, rules_to_modify, rules_to_delete = elb_listener_rules.compare_rules()

    assert sorted(rules_to_add, key=lambda x: x.get("Priority", 0)) == sorted(
        expected.get("to_add", []), key=lambda x: x.get("Priority", 0)
    )
    assert sorted(rules_to_modify, key=lambda x: x.get("Priority", 0)) == sorted(
        expected.get("to_modify", []), key=lambda x: x.get("Priority", 0)
    )
    assert sorted(rules_to_set_priority, key=lambda x: x.get("Priority", 0)) == sorted(
        expected.get("to_set_priority", []), key=lambda x: x.get("Priority", 0)
    )
    assert sorted(rules_to_delete) == sorted(expected.get("to_delete", []))


@pytest.mark.parametrize(
    "current_conditions,condition,expected",
    [
        (
            [{"Field": "test", "HostHeaderConfig": {"Values": ["a", "b"]}}],
            {"Field": "test", "HostHeaderConfig": {"Values": ["b", "a"]}},
            True,
        ),
        (
            [{"Field": "test", "HostHeaderConfig": {"Values": ["a", "b"]}}],
            {"Field": "prod", "HostHeaderConfig": {"Values": ["b", "a"]}},
            False,
        ),
        (
            [{"Field": "test", "HostHeaderConfig": {"Values": ["a", "b"]}, "Values": ["a", "a"]}],
            {"Field": "test", "HostHeaderConfig": {"Values": ["a", "a"]}, "Values": ["a", "a"]},
            False,
        ),
        (
            [{"Field": "test", "Values": ["a", "a"]}],
            {"Field": "test", "HostHeaderConfig": {"Values": ["a", "a"]}, "Values": ["a", "a"]},
            True,
        ),
        (
            [{"Field": "test", "Values": ["a", "b"]}],
            {"Field": "test", "Values": ["b", "a"]},
            True,
        ),
        (
            [{"Field": "test", "SourceIpConfig": {"Values": ["c", "a", "b"]}}],
            {"Field": "test", "SourceIpConfig": {"Values": ["a", "c", "b"]}},
            True,
        ),
        (
            [{"Field": "test", "PathPatternConfig": {"Values": ["c", "a", "b"]}}],
            {"Field": "test", "PathPatternConfig": {"Values": ["a", "c", "b"]}},
            True,
        ),
        (
            [{"Field": "test", "HttpRequestMethodConfig": {"Values": ["c", "a", "b"]}}],
            {"Field": "test", "HttpRequestMethodConfig": {"Values": ["a", "c", "b"]}},
            True,
        ),
        (
            [{"Field": "test", "HttpHeaderConfig": {"Values": ["c", "a", "b"], "HttpHeaderName": "header-a"}}],
            {"Field": "test", "HttpHeaderConfig": {"Values": ["a", "c", "b"], "HttpHeaderName": "header-a"}},
            True,
        ),
        (
            [{"Field": "test", "HttpHeaderConfig": {"Values": ["c", "a", "b"], "HttpHeaderName": "header-a"}}],
            {"Field": "test", "HttpHeaderConfig": {"Values": ["a", "c", "b"], "HttpHeaderName": "header-b"}},
            False,
        ),
        (
            [
                {"Field": "prod", "HttpHeaderConfig": {"Values": ["c", "a", "b"], "HttpHeaderName": "header-a"}},
                {"Field": "test", "HttpHeaderConfig": {"Values": ["c", "a", "b"], "HttpHeaderName": "header-a"}},
            ],
            {"Field": "test", "HttpHeaderConfig": {"Values": ["a", "c", "b"], "HttpHeaderName": "header-a"}},
            True,
        ),
    ],
)
def test__check_rule_condition(current_conditions, condition, expected):
    assert elbv2._check_rule_condition(current_conditions, condition) == expected


@pytest.mark.parametrize(
    "condition,expected_result",
    [
        (
            {"Field": "host-header", "HostHeaderConfig": {"Values": ["z.example.com", "a.example.com"]}},
            {"Field": "host-header", "HostHeaderConfig": {"Values": ["a.example.com", "z.example.com"]}},
        ),
        (
            {"Field": "path-pattern", "PathPatternConfig": {"Values": ["/z/*", "/a/*"]}},
            {"Field": "path-pattern", "PathPatternConfig": {"Values": ["/a/*", "/z/*"]}},
        ),
        (
            {"Field": "http-header", "HttpHeaderConfig": {"HttpHeaderName": "X-Custom", "Values": ["z", "a", "m"]}},
            {"Field": "http-header", "HttpHeaderConfig": {"HttpHeaderName": "X-Custom", "Values": ["a", "m", "z"]}},
        ),
        (
            {"Field": "host-header", "Values": ["z.example.com", "a.example.com"]},
            {"Field": "host-header", "Values": ["a.example.com", "z.example.com"]},
        ),
    ],
)
def test__normalize_condition_values(condition, expected_result):
    """Test _normalize_condition_values sorts values correctly"""
    result = rules._normalize_condition_values(condition)
    assert result == expected_result
    # Verify it's a deep copy
    assert result is not condition


@pytest.mark.parametrize(
    "current,target,config_key,expected",
    [
        (
            {"HostHeaderConfig": {"Values": ["b.com", "a.com"]}},
            {"HostHeaderConfig": {"Values": ["a.com", "b.com"]}},
            "HostHeaderConfig",
            True,
        ),
        (
            {"HostHeaderConfig": {"Values": ["b.com", "a.com"]}},
            {"HostHeaderConfig": {"Values": ["c.com", "d.com"]}},
            "HostHeaderConfig",
            False,
        ),
        (
            {"PathPatternConfig": {"Values": ["/a/*", "/b/*"]}},
            {"PathPatternConfig": {"Values": ["/a/*"]}},
            "PathPatternConfig",
            False,
        ),
        (
            {"SourceIpConfig": {"Values": ["192.168.1.0/24", "10.0.0.0/8"]}},
            {"SourceIpConfig": {"Values": ["10.0.0.0/8", "192.168.1.0/24"]}},
            "SourceIpConfig",
            True,
        ),
    ],
)
def test__sorted_values_match(current, target, config_key, expected):
    """Test _sorted_values_match compares sorted values correctly"""
    assert rules._sorted_values_match(current, target, config_key) is expected


@pytest.mark.parametrize(
    "current,target,config_key,expected",
    [
        (
            {"HttpHeaderConfig": {"HttpHeaderName": "X-Custom-Header"}},
            {"HttpHeaderConfig": {"HttpHeaderName": "X-Custom-Header"}},
            "HttpHeaderConfig",
            True,
        ),
        (
            {"HttpHeaderConfig": {"HttpHeaderName": "X-Custom-Header"}},
            {"HttpHeaderConfig": {"HttpHeaderName": "X-Different-Header"}},
            "HttpHeaderConfig",
            False,
        ),
        (
            {"HttpHeaderConfig": {"HttpHeaderName": "X-Custom-Header"}},
            {"HttpHeaderConfig": {"HttpHeaderName": "x-custom-header"}},
            "HttpHeaderConfig",
            False,
        ),
    ],
)
def test__http_header_name_matches(current, target, config_key, expected):
    """Test _http_header_name_matches compares header names correctly (case-sensitive)"""
    assert rules._http_header_name_matches(current, target, config_key) is expected


@pytest.mark.parametrize(
    "current_condition,target_condition,expected",
    [
        (
            {"Field": "host-header", "HostHeaderConfig": {"Values": ["example.com"]}},
            {"Field": "host-header", "HostHeaderConfig": {"Values": ["example.com"]}},
            True,
        ),
        (
            {"Field": "http-header", "HttpHeaderConfig": {"HttpHeaderName": "X-Custom", "Values": ["value1"]}},
            {"Field": "http-header", "HttpHeaderConfig": {"HttpHeaderName": "X-Custom", "Values": ["value1"]}},
            True,
        ),
        (
            {"Field": "http-header", "HttpHeaderConfig": {"HttpHeaderName": "X-Header-A", "Values": ["value1"]}},
            {"Field": "http-header", "HttpHeaderConfig": {"HttpHeaderName": "X-Header-B", "Values": ["value1"]}},
            False,
        ),
        (
            {"Field": "query-string", "QueryStringConfig": {"Values": [{"Key": "version", "Value": "1"}]}},
            {"Field": "query-string", "QueryStringConfig": {"Values": [{"Key": "version", "Value": "1"}]}},
            True,
        ),
        (
            {"Field": "host-header", "Values": ["example.com", "test.com"]},
            {"Field": "host-header", "Values": ["example.com", "test.com"]},
            True,
        ),
    ],
)
def test__conditions_match(current_condition, target_condition, expected):
    """Test _conditions_match handles different condition types correctly"""
    assert rules._conditions_match(current_condition, target_condition) is expected


class TestProcessExactMatchesAndPriorityChanges:
    """Tests for _process_exact_matches_and_priority_changes helper function"""

    def test_exact_match_removes_from_rules_to_add(self):
        """Test that exact matches are removed from rules_to_add"""
        current_rules = [
            {
                "Priority": "1",
                "Actions": [{"Type": "forward", "TargetGroupArn": "arn:tg1"}],
                "Conditions": [{"Field": "host-header", "Values": ["example.com"]}],
            }
        ]
        rules_to_add = [
            {
                "Priority": "1",
                "Actions": [{"Type": "forward", "TargetGroupArn": "arn:tg1"}],
                "Conditions": [{"Field": "host-header", "Values": ["example.com"]}],
            }
        ]

        remaining_current, remaining_to_add, priority_changes = rules._process_exact_matches_and_priority_changes(
            current_rules, rules_to_add
        )

        assert remaining_current == []
        assert remaining_to_add == []
        assert priority_changes == []

    def test_priority_only_change_detected(self):
        """Test that priority-only changes are detected"""
        current_rules = [
            {
                "Priority": "1",
                "RuleArn": "arn:rule1",
                "Actions": [{"Type": "forward", "TargetGroupArn": "arn:tg1"}],
                "Conditions": [{"Field": "host-header", "Values": ["example.com"]}],
            }
        ]
        rules_to_add = [
            {
                "Priority": "2",
                "Actions": [{"Type": "forward", "TargetGroupArn": "arn:tg1"}],
                "Conditions": [{"Field": "host-header", "Values": ["example.com"]}],
            }
        ]

        remaining_current, remaining_to_add, priority_changes = rules._process_exact_matches_and_priority_changes(
            current_rules, rules_to_add
        )

        assert remaining_current == []
        assert remaining_to_add == []
        assert len(priority_changes) == 1
        assert priority_changes[0]["Priority"] == 2
        assert priority_changes[0]["RuleArn"] == "arn:rule1"

    def test_default_rule_skipped(self):
        """Test that default rules are skipped"""
        current_rules = [
            {"Priority": "default", "IsDefault": True, "Actions": [{"Type": "forward"}]}
        ]
        rules_to_add = []

        remaining_current, remaining_to_add, priority_changes = rules._process_exact_matches_and_priority_changes(
            current_rules, rules_to_add
        )

        assert remaining_current == []
        assert remaining_to_add == []
        assert priority_changes == []

    def test_inputs_not_mutated(self):
        """Test that input parameters are not mutated"""
        from copy import deepcopy

        current_rules = [
            {
                "Priority": "1",
                "RuleArn": "arn:rule1",
                "Actions": [{"Type": "forward", "TargetGroupArn": "arn:tg1"}],
                "Conditions": [{"Field": "host-header", "Values": ["example.com"]}],
            }
        ]
        rules_to_add = [
            {
                "Priority": "2",
                "Actions": [{"Type": "forward", "TargetGroupArn": "arn:tg1"}],
                "Conditions": [{"Field": "host-header", "Values": ["example.com"]}],
            }
        ]

        original_current = deepcopy(current_rules)
        original_to_add = deepcopy(rules_to_add)

        rules._process_exact_matches_and_priority_changes(current_rules, rules_to_add)

        assert current_rules == original_current
        assert rules_to_add == original_to_add


class TestProcessPriorityBasedModifications:
    """Tests for _process_priority_based_modifications helper function"""

    def test_priority_match_creates_modification(self):
        """Test that rules with matching priority create modifications"""
        remaining_rules = [
            {
                "Priority": "1",
                "RuleArn": "arn:rule1",
                "Actions": [{"Type": "forward", "TargetGroupArn": "old"}],
                "Conditions": [{"Field": "host-header", "Values": ["old.com"]}],
            }
        ]
        rules_to_add = [
            {
                "Priority": "1",
                "Actions": [{"Type": "forward", "TargetGroupArn": "new"}],
                "Conditions": [{"Field": "host-header", "Values": ["new.com"]}],
            }
        ]

        remaining_to_add, modifications, deletions = rules._process_priority_based_modifications(
            remaining_rules, rules_to_add
        )

        assert remaining_to_add == []
        assert len(modifications) == 1
        assert modifications[0]["RuleArn"] == "arn:rule1"
        assert modifications[0]["Actions"][0]["TargetGroupArn"] == "new"
        assert deletions == []

    def test_unmatched_rule_marked_for_deletion(self):
        """Test that unmatched rules are marked for deletion"""
        remaining_rules = [
            {"Priority": "1", "RuleArn": "arn:rule1", "Actions": [], "Conditions": []}
        ]
        rules_to_add = [
            {"Priority": "2", "Actions": [], "Conditions": []}
        ]

        remaining_to_add, modifications, deletions = rules._process_priority_based_modifications(
            remaining_rules, rules_to_add
        )

        assert len(remaining_to_add) == 1
        assert modifications == []
        assert deletions == ["arn:rule1"]

    def test_default_rule_not_deleted(self):
        """Test that default rules are not marked for deletion"""
        remaining_rules = [
            {"Priority": "default", "IsDefault": True, "RuleArn": "arn:default", "Actions": [], "Conditions": []}
        ]
        rules_to_add = []

        remaining_to_add, modifications, deletions = rules._process_priority_based_modifications(
            remaining_rules, rules_to_add
        )

        assert remaining_to_add == []
        assert modifications == []
        assert deletions == []

    def test_inputs_not_mutated(self):
        """Test that input parameters are not mutated"""
        from copy import deepcopy

        remaining_rules = [
            {"Priority": "1", "RuleArn": "arn:rule1", "Actions": [], "Conditions": []}
        ]
        rules_to_add = [
            {"Priority": "2", "Actions": [], "Conditions": []}
        ]

        original_remaining = deepcopy(remaining_rules)
        original_to_add = deepcopy(rules_to_add)

        rules._process_priority_based_modifications(remaining_rules, rules_to_add)

        assert remaining_rules == original_remaining
        assert rules_to_add == original_to_add

# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2

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

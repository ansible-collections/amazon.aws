#
# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2

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
def test__compare_rule(mocker, current_rule, new_rule, modified_rule):
    mocker.patch(
        "ansible_collections.amazon.aws.plugins.module_utils.elbv2.ELBListenerRules._get_elb_listener_rules"
    ).return_value = MagicMock()
    mocker.patch(
        "ansible_collections.amazon.aws.plugins.module_utils.elbv2.get_elb_listener"
    ).return_value = MagicMock()
    module = MagicMock()
    connection = MagicMock()
    elb_arn = MagicMock()

    elb_listener_rules = elbv2.ELBListenerRules(connection, module, elb_arn, [], [])

    assert modified_rule == elb_listener_rules._compare_rule(current_rule, new_rule)


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
                    "Priority": 1,
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
def test_compare_rules(mocker, current_rules, rules, expected):
    mocker.patch(
        "ansible_collections.amazon.aws.plugins.module_utils.elbv2.get_elb_listener"
    ).return_value = MagicMock()
    mocker.patch(
        "ansible_collections.amazon.aws.plugins.module_utils.elbv2.ELBListenerRules._ensure_rules_action_has_arn"
    ).return_value = rules
    mocker.patch(
        "ansible_collections.amazon.aws.plugins.module_utils.elbv2.ELBListenerRules._get_elb_listener_rules"
    ).return_value = current_rules
    module = MagicMock()
    connection = MagicMock()
    elb_arn = MagicMock()

    elb_listener_rules = elbv2.ELBListenerRules(connection, module, elb_arn, rules, 8009)
    elb_listener_rules.current_rules = current_rules
    rules_to_add, rules_to_modify, rules_to_delete, rules_to_set_priority = elb_listener_rules.compare_rules()

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

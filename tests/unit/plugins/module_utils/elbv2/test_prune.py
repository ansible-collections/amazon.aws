#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2

example_arn = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/nlb-123456789abc/abcdef0123456789"
example_arn2 = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/nlb-0123456789ab/0123456789abcdef"

one_action = [
    dict(
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False),
            TargetGroups=[
                dict(TargetGroupArn=example_arn, Weight=1),
            ],
        ),
        TargetGroupArn=example_arn,
        Type="forward",
    )
]

one_action_two_tg = [
    dict(
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False),
            TargetGroups=[
                dict(TargetGroupArn=example_arn, Weight=1),
                dict(TargetGroupArn=example_arn2, Weight=1),
            ],
        ),
        TargetGroupArn=example_arn,
        Type="forward",
    )
]

simplified_action = dict(Type="forward", TargetGroupArn=example_arn)
# Examples of various minimalistic actions which are all the same
simple_actions = [
    dict(Type="forward", TargetGroupArn=example_arn),
    dict(
        Type="forward", TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn)])
    ),
    dict(Type="forward", ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn)])),
    dict(
        Type="forward",
        TargetGroupArn=example_arn,
        ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)]),
    ),
    dict(Type="forward", ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)])),
    dict(
        Type="forward",
        TargetGroupArn=example_arn,
        ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)]),
    ),
    dict(Type="forward", ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)])),
    dict(
        Type="forward",
        TargetGroupArn=example_arn,
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn)]
        ),
    ),
    dict(
        Type="forward",
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn)]
        ),
    ),
    dict(
        Type="forward",
        TargetGroupArn=example_arn,
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)]
        ),
    ),
    dict(
        Type="forward",
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)]
        ),
    ),
    dict(
        Type="forward",
        TargetGroupArn=example_arn,
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)]
        ),
    ),
    dict(
        Type="forward",
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)]
        ),
    ),
]

# Test that _prune_ForwardConfig() doesn't mangle things we don't expect
complex_actions = [
    # Non-Forwarding
    dict(
        Type="authenticate-oidc",
        TargetGroupArn=example_arn,
        AuthenticateOidcConfig=dict(
            Issuer="https://idp.ansible.test/oidc-config",
            AuthorizationEndpoint="https://idp.ansible.test/authz",
            TokenEndpoint="https://idp.ansible.test/token",
            UserInfoEndpoint="https://idp.ansible.test/user",
            ClientId="ExampleClient",
            UseExistingClientSecret=False,
        ),
    ),
    dict(
        Type="redirect",
        RedirectConfig=dict(Protocol="HTTPS", Port=443, Host="redirect.ansible.test", Path="/", StatusCode="HTTP_302"),
    ),
    # Multiple TGs
    dict(
        TargetGroupArn=example_arn,
        Type="forward",
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False),
            TargetGroups=[
                dict(TargetGroupArn=example_arn, Weight=1),
                dict(TargetGroupArn=example_arn2, Weight=1),
            ],
        ),
    ),
    # Sticky-Sessions
    dict(
        Type="forward",
        TargetGroupArn=example_arn,
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=True, DurationSeconds=3600),
            TargetGroups=[dict(TargetGroupArn=example_arn)],
        ),
    ),
]

simplified_oidc_action = dict(
    Type="authenticate-oidc",
    TargetGroupArn=example_arn,
    AuthenticateOidcConfig=dict(
        Issuer="https://idp.ansible.test/oidc-config",
        AuthorizationEndpoint="https://idp.ansible.test/authz",
        TokenEndpoint="https://idp.ansible.test/token",
        UserInfoEndpoint="https://idp.ansible.test/user",
        ClientId="ExampleClient",
        Scope="openid",
        SessionTimeout=604800,
        UseExistingClientSecret=True,
        OnUnauthenticatedRequest="authenticate",
        SessionCookieName="AWSELBAuthSessionCookie",
    ),
)
oidc_actions = [
    dict(
        Type="authenticate-oidc",
        TargetGroupArn=example_arn,
        AuthenticateOidcConfig=dict(
            Issuer="https://idp.ansible.test/oidc-config",
            AuthorizationEndpoint="https://idp.ansible.test/authz",
            TokenEndpoint="https://idp.ansible.test/token",
            UserInfoEndpoint="https://idp.ansible.test/user",
            ClientId="ExampleClient",
            UseExistingClientSecret=True,
            Scope="openid",
            SessionTimeout=604800,
        ),
    ),
    dict(
        Type="authenticate-oidc",
        TargetGroupArn=example_arn,
        AuthenticateOidcConfig=dict(
            Issuer="https://idp.ansible.test/oidc-config",
            AuthorizationEndpoint="https://idp.ansible.test/authz",
            TokenEndpoint="https://idp.ansible.test/token",
            UserInfoEndpoint="https://idp.ansible.test/user",
            ClientId="ExampleClient",
            ClientSecret="MyVerySecretString",
            UseExistingClientSecret=True,
        ),
    ),
]


####


# Original tests
def test__prune_secret():
    assert elbv2._prune_secret(one_action[0]) == one_action[0]


def test__prune_ForwardConfig():
    expectation = {"TargetGroupArn": example_arn, "Type": "forward"}
    pruned_config = elbv2._prune_ForwardConfig(one_action[0])
    assert pruned_config == expectation

    # https://github.com/ansible-collections/community.aws/issues/1089
    pruned_config = elbv2._prune_ForwardConfig(one_action_two_tg[0])
    assert pruned_config == one_action_two_tg[0]


####


@pytest.mark.parametrize("action", simple_actions)
def test__prune_ForwardConfig_simplifiable_actions(action):
    pruned_config = elbv2._prune_ForwardConfig(action)
    assert pruned_config == simplified_action


@pytest.mark.parametrize("action", complex_actions)
def test__prune_ForwardConfig_non_simplifiable_actions(action):
    pruned_config = elbv2._prune_ForwardConfig(action)
    assert pruned_config == action


@pytest.mark.parametrize("action", oidc_actions)
def test__prune_secret_simplifiable_actions(action):
    pruned_config = elbv2._prune_secret(action)
    assert pruned_config == simplified_oidc_action


@pytest.mark.parametrize("action", complex_actions)
def test__prune_secret_non_simplifiable_actions(action):
    pruned_config = elbv2._prune_secret(action)
    assert pruned_config == action


# Test _simple_forward_config_arn
@pytest.mark.parametrize(
    "config,parent_arn,expected",
    [
        ({}, None, None),
        ({"TargetGroupStickinessConfig": {"Enabled": True}}, None, None),
        ({"TargetGroupStickinessConfig": {"Enabled": False}}, None, None),
        ({"Some": "info"}, None, None),
        ({"TargetGroups": ["group1", "group2"]}, None, None),
        ({"TargetGroupStickinessConfig": {"Enabled": False}}, "parent_arn", "parent_arn"),
        ({"TargetGroups": [{"Weight": 2, "TargetGroupArn": "group_arn", "other": "key"}]}, None, None),
        ({"TargetGroups": [{"Weight": 2, "other": "key"}]}, None, None),
        ({"TargetGroups": [{"Weight": 2, "TargetGroupArn": "group_arn", "other": "key"}]}, None, None),
        ({"TargetGroups": [{"Weight": 2}]}, "parent_arn", "parent_arn"),
        (
            {
                "TargetGroupStickinessConfig": {"Enabled": False},
                "TargetGroups": [{"Weight": 2, "TargetGroupArn": "group_arn"}],
            },
            "parent_arn",
            None,
        ),
        (
            {
                "TargetGroupStickinessConfig": {"Enabled": False},
                "TargetGroups": [{"Weight": 2, "TargetGroupArn": "group_arn"}],
            },
            "group_arn",
            "group_arn",
        ),
    ],
)
def test__simple_forward_config_arn(config, parent_arn, expected):
    assert elbv2._simple_forward_config_arn(config, parent_arn) == expected


@pytest.mark.parametrize(
    "action,expected",
    [
        ({"Type": "logger"}, {"Type": "logger"}),
        (
            {"Type": "authenticate-oidc", "AuthenticateOidcConfig": {}},
            {"Type": "authenticate-oidc", "AuthenticateOidcConfig": {"UseExistingClientSecret": True}},
        ),
    ],
)
def test__append_use_existing_client_secretn(action, expected):
    assert elbv2._append_use_existing_client_secretn(action) == expected


@pytest.mark.parametrize(
    "actions,expected",
    [
        ([{"Order": 2}, {"Order": 1}], [{"Order": 1}, {"Order": 2}]),
        ([{"Order": 2}, {}, {"Order": 1}], [{}, {"Order": 1}, {"Order": 2}]),
    ],
)
def test__sort_actions(actions, expected):
    assert elbv2._sort_actions(actions) == expected

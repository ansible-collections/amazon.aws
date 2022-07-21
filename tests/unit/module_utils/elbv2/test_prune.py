#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import elbv2

example_arn = 'arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/nlb-123456789abc/abcdef0123456789'
example_arn2 = 'arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/nlb-0123456789ab/0123456789abcdef'

one_action = [
    dict(
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False),
            TargetGroups=[
                dict(TargetGroupArn=example_arn, Weight=1),
            ]
        ),
        TargetGroupArn=example_arn, Type='forward',
    )
]

one_action_two_tg = [
    dict(
        ForwardConfig=dict(
            TargetGroupStickinessConfig=dict(Enabled=False),
            TargetGroups=[
                dict(TargetGroupArn=example_arn, Weight=1),
                dict(TargetGroupArn=example_arn2, Weight=1),
            ]
        ),
        TargetGroupArn=example_arn, Type='forward',
    )
]

simplified_action = dict(Type='forward', TargetGroupArn=example_arn)
# Examples of various minimalistic actions which are all the same
simple_actions = [
    dict(Type='forward', TargetGroupArn=example_arn),

    dict(Type='forward', TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn)])),
    dict(Type='forward', ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn)])),
    dict(Type='forward', TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)])),
    dict(Type='forward', ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)])),
    dict(Type='forward', TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)])),
    dict(Type='forward', ForwardConfig=dict(TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)])),

    dict(Type='forward', TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn)])),
    dict(Type='forward', ForwardConfig=dict(TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn)])),
    dict(Type='forward', TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)])),
    dict(Type='forward', ForwardConfig=dict(TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=1)])),
    dict(Type='forward', TargetGroupArn=example_arn, ForwardConfig=dict(TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)])),
    dict(Type='forward', ForwardConfig=dict(TargetGroupStickinessConfig=dict(Enabled=False), TargetGroups=[dict(TargetGroupArn=example_arn, Weight=42)])),
]


def test_prune_secret():
    assert elbv2._prune_secret(one_action[0]) == one_action[0]


# Original tests
def test__prune_ForwardConfig():
    expectation = {"TargetGroupArn": example_arn, "Type": "forward"}
    pruned_config = elbv2._prune_ForwardConfig(one_action[0])
    assert pruned_config == expectation

    # https://github.com/ansible-collections/community.aws/issues/1089
    pruned_config = elbv2._prune_ForwardConfig(one_action_two_tg[0])
    assert pruned_config == one_action_two_tg[0]


@pytest.mark.parametrize("action", simple_actions)
def test_simpliifable_actions(action):
    pruned_config = elbv2._prune_ForwardConfig(action)
    assert pruned_config == simplified_action

#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ansible_collections.amazon.aws.plugins.module_utils.elbv2 as elbv2


one_action = [
    {
        "ForwardConfig": {
            "TargetGroupStickinessConfig": {"Enabled": False},
            "TargetGroups": [
                {
                    "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:966509639900:targetgroup/my-tg-58045486/5b231e04f663ae21",
                    "Weight": 1,
                }
            ],
        },
        "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:966509639900:targetgroup/my-tg-58045486/5b231e04f663ae21",
        "Type": "forward",
    }
]


def test__prune_ForwardConfig():
    expectation = {
        "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:966509639900:targetgroup/my-tg-58045486/5b231e04f663ae21",
        "Type": "forward",
    }
    assert elbv2._prune_ForwardConfig(one_action[0]) == expectation


def _prune_secret():
    assert elbv2._prune_secret(one_action[0]) == one_action[0]


def _sort_actions_one_entry():
    assert elbv2._sort_actions(one_action) == one_action

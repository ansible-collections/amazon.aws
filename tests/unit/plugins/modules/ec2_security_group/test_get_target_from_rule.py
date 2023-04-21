# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy
import pytest
from unittest.mock import sentinel

import ansible_collections.amazon.aws.plugins.modules.ec2_security_group as ec2_security_group_module


@pytest.fixture
def ec2_security_group(monkeypatch):
    # monkey patches various ec2_security_group module functions, we'll separately test the operation of
    # these functions, we just care that it's passing the results into the right place in the
    # instance spec.
    monkeypatch.setattr(ec2_security_group_module, "current_account_id", sentinel.CURRENT_ACCOUNT_ID)
    return ec2_security_group_module


def test_target_from_rule_with_group_id_local_group(ec2_security_group):
    groups = dict()
    original_groups = deepcopy(groups)
    rule_type, target, created = ec2_security_group._target_from_rule_with_group_id(
        dict(group_id="sg-123456789abcdef01"),
        groups,
    )
    assert groups == original_groups
    assert rule_type == "group"
    assert created is False
    assert target[0] is sentinel.CURRENT_ACCOUNT_ID
    assert target[1] == "sg-123456789abcdef01"
    assert target[2] is None


def test_target_from_rule_with_group_id_peer_group(ec2_security_group):
    groups = dict()
    rule_type, target, created = ec2_security_group._target_from_rule_with_group_id(
        dict(group_id="123456789012/sg-123456789abcdef02/example-group-name"),
        groups,
    )
    assert rule_type == "group"
    assert created is False
    assert target[0] == "123456789012"
    assert target[1] == "sg-123456789abcdef02"
    assert target[2] is None

    assert sorted(groups.keys()) == ["example-group-name", "sg-123456789abcdef02"]
    rule_by_id = groups["sg-123456789abcdef02"]
    rule_by_name = groups["example-group-name"]

    assert rule_by_id is rule_by_name
    assert rule_by_id["UserId"] == "123456789012"
    assert rule_by_id["GroupId"] == "sg-123456789abcdef02"
    assert rule_by_id["GroupName"] == "example-group-name"


def test_target_from_rule_with_group_id_elb(ec2_security_group):
    groups = dict()
    rule_type, target, created = ec2_security_group._target_from_rule_with_group_id(
        dict(group_id="amazon-elb/amazon-elb-sg"),
        groups,
    )
    assert rule_type == "group"
    assert created is False
    assert target[0] == "amazon-elb"
    assert target[1] is None
    assert target[2] == "amazon-elb-sg"

    assert "amazon-elb-sg" in groups.keys()
    rule_by_name = groups["amazon-elb-sg"]

    assert rule_by_name["UserId"] == "amazon-elb"
    assert rule_by_name["GroupId"] is None
    assert rule_by_name["GroupName"] == "amazon-elb-sg"


def test_target_from_rule_with_group_id_elb_with_sg(ec2_security_group):
    groups = dict()
    rule_type, target, created = ec2_security_group._target_from_rule_with_group_id(
        dict(group_id="amazon-elb/sg-5a9c116a/amazon-elb-sg"),
        groups,
    )
    assert rule_type == "group"
    assert created is False
    assert target[0] == "amazon-elb"
    assert target[1] is None
    assert target[2] == "amazon-elb-sg"

    assert sorted(groups.keys()) == ["amazon-elb-sg", "sg-5a9c116a"]
    rule_by_id = groups["sg-5a9c116a"]
    rule_by_name = groups["amazon-elb-sg"]

    assert rule_by_id is rule_by_name
    assert rule_by_id["UserId"] == "amazon-elb"
    assert rule_by_id["GroupId"] == "sg-5a9c116a"
    assert rule_by_id["GroupName"] == "amazon-elb-sg"

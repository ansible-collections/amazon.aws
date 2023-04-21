# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.policy import _hashable_policy


def test_hashable_policy_none():
    assert _hashable_policy(None, []) == []


def test_hashable_policy_boolean():
    assert _hashable_policy(True, []) == ("true",)
    assert _hashable_policy(False, []) == ("false",)


def test_hashable_policy_int():
    assert _hashable_policy(1, []) == ("1",)
    assert _hashable_policy(42, []) == ("42",)
    assert _hashable_policy(0, []) == ("0",)


def test_hashable_policy_string():
    assert _hashable_policy("simple_string", []) == ["simple_string"]
    assert _hashable_policy("123456789012", []) == ["123456789012"]
    # This is a special case, we generally expect to have gone via _canonify_root_arn
    assert _hashable_policy("arn:aws:iam::123456789012:root", []) == ["123456789012"]

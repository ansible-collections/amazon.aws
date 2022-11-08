# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import sentinel

from ansible_collections.amazon.aws.plugins.module_utils.policy import _canonify_root_arn
from ansible_collections.amazon.aws.plugins.module_utils.policy import _canonify_policy_dict_item
from ansible_collections.amazon.aws.plugins.module_utils.policy import _tuplify_list


def test_tuplify_list():
    my_list = ["one", 2, sentinel.list_item, False]
    # Lists are tuplified
    assert _tuplify_list(my_list) == tuple(my_list)
    # Other types are not
    assert _tuplify_list("one") == "one"
    assert _tuplify_list(2) == 2
    assert _tuplify_list(sentinel.single_item) is sentinel.single_item
    assert _tuplify_list(False) is False


def test_canonify_root_arn():
    assert _canonify_root_arn("Some String") == "Some String"
    assert _canonify_root_arn("123456789012") == "123456789012"
    assert _canonify_root_arn("arn:aws:iam::123456789012:root") == "123456789012"


def test_canonify_policy_dict_item_principal():
    assert _canonify_policy_dict_item("*", "Principal") == {"AWS": "*"}
    assert _canonify_policy_dict_item("*", "NotPrincipal") == {"AWS": "*"}
    assert _canonify_policy_dict_item("*", "AnotherKey") == "*"
    assert _canonify_policy_dict_item("NotWildCard", "Principal") == "NotWildCard"
    assert _canonify_policy_dict_item("NotWildCard", "NotPrincipal") == "NotWildCard"
    assert _canonify_policy_dict_item(sentinel.single_item, "Principal") is sentinel.single_item
    assert _canonify_policy_dict_item(False, "Principal") is False
    assert _canonify_policy_dict_item(True, "Principal") is True

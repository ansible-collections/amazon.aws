# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.policy import sort_json_policy_dict


def test_nothing_to_sort():
    simple_dict = {"key1": "a"}
    nested_dict = {"key1": {"key2": "a"}}
    very_nested_dict = {"key1": {"key2": {"key3": "a"}}}
    assert sort_json_policy_dict(simple_dict) == simple_dict
    assert sort_json_policy_dict(nested_dict) == nested_dict
    assert sort_json_policy_dict(very_nested_dict) == very_nested_dict


def test_basic_sort():
    simple_dict = {"key1": [1, 2, 3, 4], "key2": [9, 8, 7, 6]}
    sorted_dict = {"key1": [1, 2, 3, 4], "key2": [6, 7, 8, 9]}
    assert sort_json_policy_dict(simple_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict
    simple_dict = {"key1": ["a", "b", "c", "d"], "key2": ["z", "y", "x", "w"]}
    sorted_dict = {"key1": ["a", "b", "c", "d"], "key2": ["w", "x", "y", "z"]}
    assert sort_json_policy_dict(sorted_dict) == sorted_dict


def test_nested_list_sort():
    nested_dict = {"key1": {"key2": [9, 8, 7, 6]}}
    sorted_dict = {"key1": {"key2": [6, 7, 8, 9]}}
    assert sort_json_policy_dict(nested_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict
    nested_dict = {"key1": {"key2": ["z", "y", "x", "w"]}}
    sorted_dict = {"key1": {"key2": ["w", "x", "y", "z"]}}
    assert sort_json_policy_dict(nested_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict


def test_nested_dict_list_sort():
    nested_dict = {"key1": {"key2": {"key3": [9, 8, 7, 6]}}}
    sorted_dict = {"key1": {"key2": {"key3": [6, 7, 8, 9]}}}
    assert sort_json_policy_dict(nested_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict
    nested_dict = {"key1": {"key2": {"key3": ["z", "y", "x", "w"]}}}
    sorted_dict = {"key1": {"key2": {"key3": ["w", "x", "y", "z"]}}}
    assert sort_json_policy_dict(nested_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict


def test_list_of_dict_sort():
    nested_dict = {"key1": [{"key2": [4, 3, 2, 1]}, {"key3": [9, 8, 7, 6]}]}
    sorted_dict = {"key1": [{"key2": [1, 2, 3, 4]}, {"key3": [6, 7, 8, 9]}]}
    assert sort_json_policy_dict(nested_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict


def test_list_of_list_sort():
    nested_dict = {"key1": [[4, 3, 2, 1], [9, 8, 7, 6]]}
    sorted_dict = {"key1": [[1, 2, 3, 4], [6, 7, 8, 9]]}
    assert sort_json_policy_dict(nested_dict) == sorted_dict
    assert sort_json_policy_dict(sorted_dict) == sorted_dict

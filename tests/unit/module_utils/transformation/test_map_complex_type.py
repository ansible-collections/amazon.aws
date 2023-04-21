# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import sentinel

from ansible_collections.amazon.aws.plugins.module_utils.transformation import map_complex_type


def test_map_complex_type_over_dict():
    type_map = {"minimum_healthy_percent": "int", "maximum_percent": "int"}
    complex_type_dict = {"minimum_healthy_percent": "75", "maximum_percent": "150"}
    complex_type_expected = {"minimum_healthy_percent": 75, "maximum_percent": 150}

    complex_type_mapped = map_complex_type(complex_type_dict, type_map)

    assert complex_type_mapped == complex_type_expected


def test_map_complex_type_empty():
    type_map = {"minimum_healthy_percent": "int", "maximum_percent": "int"}
    assert map_complex_type({}, type_map) == {}
    assert map_complex_type([], type_map) == []
    assert map_complex_type(None, type_map) is None


def test_map_complex_type_no_type():
    type_map = {"some_entry": "int"}
    complex_dict = {"another_entry": sentinel.UNSPECIFIED_MAPPING}
    mapped_dict = map_complex_type(complex_dict, type_map)
    assert mapped_dict == complex_dict
    # we should have the original sentinel object, even if it's a new dictionary
    assert mapped_dict["another_entry"] is sentinel.UNSPECIFIED_MAPPING


def test_map_complex_type_list():
    type_map = {"some_entry": "int"}
    complex_dict = {"some_entry": ["1", "2", "3"]}
    expected_dict = {"some_entry": [1, 2, 3]}
    mapped_dict = map_complex_type(complex_dict, type_map)
    assert mapped_dict == expected_dict


def test_map_complex_type_list_type():
    type_map = {"some_entry": ["int"]}
    complex_dict = {"some_entry": ["1", "2", "3"]}
    expected_dict = {"some_entry": [1, 2, 3]}
    mapped_dict = map_complex_type(complex_dict, type_map)
    assert mapped_dict == expected_dict

    type_map = {"some_entry": ["int"]}
    complex_dict = {"some_entry": "1"}
    expected_dict = {"some_entry": 1}
    mapped_dict = map_complex_type(complex_dict, type_map)
    assert mapped_dict == expected_dict


def test_map_complex_type_complex():
    type_map = {
        "my_integer": "int",
        "my_bool": "bool",
        "my_string": "str",
        "my_typelist_of_int": ["int"],
        "my_maplist_of_int": "int",
        "my_unused": "bool",
    }
    complex_dict = {
        "my_integer": "-24",
        "my_bool": "true",
        "my_string": 43,
        "my_typelist_of_int": "5",
        "my_maplist_of_int": ["-26", "47"],
        "my_unconverted": sentinel.UNSPECIFIED_MAPPING,
    }
    expected_dict = {
        "my_integer": -24,
        "my_bool": True,
        "my_string": "43",
        "my_typelist_of_int": 5,
        "my_maplist_of_int": [-26, 47],
        "my_unconverted": sentinel.UNSPECIFIED_MAPPING,
    }

    mapped_dict = map_complex_type(complex_dict, type_map)

    assert mapped_dict == expected_dict
    assert mapped_dict["my_unconverted"] is sentinel.UNSPECIFIED_MAPPING
    assert mapped_dict["my_bool"] is True


def test_map_complex_type_nested_list():
    type_map = {"my_integer": "int"}
    complex_dict = [{"my_integer": "5"}, {"my_integer": "-24"}]
    expected_dict = [{"my_integer": 5}, {"my_integer": -24}]
    mapped_dict = map_complex_type(complex_dict, type_map)
    assert mapped_dict == expected_dict

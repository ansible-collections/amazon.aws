# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy
from unittest.mock import sentinel

import dateutil
import pytest

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict

example_date_txt = "2020-12-30T00:00:00.000Z"
example_date_iso = "2020-12-30T00:00:00+00:00"
example_date = dateutil.parser.parse(example_date_txt)

EXAMPLE_BOTO3 = [
    None,
    {},
    {"ExampleDate": example_date},
    {"ExampleTxtDate": example_date_txt},
    {"Tags": [{"Key": "MyKey", "Value": "MyValue"}, {"Key": "Normal case", "Value": "Normal Value"}]},
    {
        "Name": "ExampleResource",
        "ExampleDate": example_date,
        "Tags": [{"Key": "MyKey", "Value": "MyValue"}, {"Key": "Normal case", "Value": "Normal Value"}],
    },
    {"ExampleNested": {"ExampleKey": "Example Value"}},
]

EXAMPLE_DICT = [
    None,
    {},
    {"example_date": example_date_iso, "tags": {}},
    {"example_txt_date": example_date_txt, "tags": {}},
    {"tags": {"MyKey": "MyValue", "Normal case": "Normal Value"}},
    {
        "name": "ExampleResource",
        "example_date": example_date_iso,
        "tags": {"MyKey": "MyValue", "Normal case": "Normal Value"},
    },
    {"example_nested": {"example_key": "Example Value"}, "tags": {}},
]

TEST_DATA = zip(EXAMPLE_BOTO3, EXAMPLE_DICT)

NESTED_DATA = {"sentinal": sentinel.MY_VALUE}


def do_transform_nested(resource):
    return {"sentinal": sentinel.MY_VALUE}


class TestBoto3ResourceToAnsibleDict:
    def setup_method(self):
        pass

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_default_conversion(self, input_params, output_params):
        # Test default behaviour
        assert boto3_resource_to_ansible_dict(input_params) == output_params

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_normalize(self, input_params, output_params):
        # Test with normalize explicitly enabled
        assert boto3_resource_to_ansible_dict(input_params, normalize=True) == output_params

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_no_normalize(self, input_params, output_params):
        # Test with normalize explicitly disabled
        expected_value = deepcopy(output_params)
        if input_params and "ExampleDate" in input_params:
            expected_value["example_date"] = example_date
        assert expected_value == boto3_resource_to_ansible_dict(input_params, normalize=False)

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_no_skip(self, input_params, output_params):
        # Test with ignore_list explicitly set to []
        assert boto3_resource_to_ansible_dict(input_params, ignore_list=[]) == output_params
        assert boto3_resource_to_ansible_dict(input_params, ignore_list=["NotUsed"]) == output_params

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_skip(self, input_params, output_params):
        # Test with ignore_list explicitly set
        expected_value = deepcopy(output_params)
        if input_params and "ExampleNested" in input_params:
            expected_value["example_nested"] = input_params["ExampleNested"]
        assert expected_value == boto3_resource_to_ansible_dict(input_params, ignore_list=["ExampleNested"])
        assert expected_value == boto3_resource_to_ansible_dict(input_params, ignore_list=["NotUsed", "ExampleNested"])
        assert expected_value == boto3_resource_to_ansible_dict(input_params, ignore_list=["ExampleNested", "NotUsed"])

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_tags(self, input_params, output_params):
        # Test with transform_tags explicitly enabled
        assert boto3_resource_to_ansible_dict(input_params, transform_tags=True) == output_params

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_no_tags(self, input_params, output_params):
        # Test with transform_tags explicitly disabled
        expected_value = deepcopy(output_params)
        if input_params and "Tags" in input_params:
            camel_tags = camel_dict_to_snake_dict({"tags": input_params["Tags"]})
            expected_value.update(camel_tags)
        assert expected_value == boto3_resource_to_ansible_dict(input_params, transform_tags=False)

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_no_nested(self, input_params, output_params):
        # Test with transform_nested explicitly set to an empty dictionary
        assert boto3_resource_to_ansible_dict(input_params, nested_transforms={}) == output_params

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_nested(self, input_params, output_params):
        # Test with a custom transformation of nested resources
        transform_map = {"ExampleNested": do_transform_nested}
        expected_value = deepcopy(output_params)

        actual_value = boto3_resource_to_ansible_dict(input_params, nested_transforms=transform_map)

        if input_params and "ExampleNested" in input_params:
            assert actual_value["example_nested"] == NESTED_DATA
            del actual_value["example_nested"]
            del expected_value["example_nested"]

        assert expected_value == actual_value

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_force_tags(self, input_params, output_params):
        # Test with force_tags explicitly enabled
        assert boto3_resource_to_ansible_dict(input_params, force_tags=True) == output_params

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_no_force_tags(self, input_params, output_params):
        # Test with force_tags explicitly enabled
        expected_value = deepcopy(output_params)
        if input_params and "Tags" not in input_params:
            del expected_value["tags"]
        assert boto3_resource_to_ansible_dict(input_params, force_tags=False) == expected_value

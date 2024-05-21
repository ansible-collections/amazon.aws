# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_tag_filter_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


class TestTagging:
    # ========================================================
    # Setup some initial data that we can use within our tests
    # ========================================================
    def setup_method(self):
        self.tag_example_boto3_list = [
            {"Key": "lowerCamel", "Value": "lowerCamelValue"},
            {"Key": "UpperCamel", "Value": "upperCamelValue"},
            {"Key": "Normal case", "Value": "Normal Value"},
            {"Key": "lower case", "Value": "lower case value"},
        ]

        self.tag_example_boto3_list_custom_key = [
            {"MyKey": "lowerCamel", "MyValue": "lowerCamelValue"},
            {"MyKey": "UpperCamel", "MyValue": "upperCamelValue"},
            {"MyKey": "Normal case", "MyValue": "Normal Value"},
            {"MyKey": "lower case", "MyValue": "lower case value"},
        ]

        self.tag_example_dict = {
            "lowerCamel": "lowerCamelValue",
            "UpperCamel": "upperCamelValue",
            "Normal case": "Normal Value",
            "lower case": "lower case value",
        }

        self.tag_filter_dict = {
            "tag:lowerCamel": "lowerCamelValue",
            "tag:UpperCamel": "upperCamelValue",
            "tag:Normal case": "Normal Value",
            "tag:lower case": "lower case value",
        }

        self.tag_minimal_boto3_list = [
            {"Key": "mykey", "Value": "myvalue"},
        ]

        self.tag_minimal_dict = {"mykey": "myvalue"}

        self.tag_aws_dict = {"aws:cloudformation:stack-name": "ExampleStack"}
        self.tag_aws_changed = {"aws:cloudformation:stack-name": "AnotherStack"}

    # ========================================================
    #   tagging.ansible_dict_to_boto3_tag_list
    # ========================================================

    def test_ansible_dict_to_boto3_tag_list(self):
        converted_list = ansible_dict_to_boto3_tag_list(self.tag_example_dict)
        sorted_converted_list = sorted(converted_list, key=lambda i: (i["Key"]))
        sorted_list = sorted(self.tag_example_boto3_list, key=lambda i: (i["Key"]))
        assert sorted_converted_list == sorted_list

    def test_ansible_dict_to_boto3_tag_list_empty(self):
        assert ansible_dict_to_boto3_tag_list({}) == []
        assert ansible_dict_to_boto3_tag_list(None) == []

    def test_ansible_dict_to_boto3_tag_list_boolean(self):
        dict_with_bool = dict(boolean=True)
        list_with_bool = [{"Key": "boolean", "Value": "True"}]
        assert ansible_dict_to_boto3_tag_list(dict_with_bool) == list_with_bool
        dict_with_bool = dict(boolean=False)
        list_with_bool = [{"Key": "boolean", "Value": "False"}]
        assert ansible_dict_to_boto3_tag_list(dict_with_bool) == list_with_bool

    # ========================================================
    #   tagging.boto3_tag_list_to_ansible_dict
    # ========================================================

    def test_boto3_tag_list_to_ansible_dict(self):
        converted_dict = boto3_tag_list_to_ansible_dict(self.tag_example_boto3_list)
        assert converted_dict == self.tag_example_dict

    def test_boto3_tag_list_to_ansible_dict_empty(self):
        # AWS returns [] when there are no tags
        assert boto3_tag_list_to_ansible_dict([]) == {}
        # Minio returns [{}] when there are no tags
        assert boto3_tag_list_to_ansible_dict([{}]) == {}

    def test_boto3_tag_list_to_ansible_dict_nondefault_keys(self):
        converted_dict = boto3_tag_list_to_ansible_dict(self.tag_example_boto3_list_custom_key, "MyKey", "MyValue")
        assert converted_dict == self.tag_example_dict

        with pytest.raises(ValueError) as context:
            boto3_tag_list_to_ansible_dict(self.tag_example_boto3_list, "MyKey", "MyValue")
        assert "Couldn't find tag key" in str(context.value)

    # ========================================================
    #   tagging.compare_aws_tags
    # ========================================================

    def test_compare_aws_tags_equal(self):
        new_dict = dict(self.tag_example_dict)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        assert {} == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        assert {} == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        assert {} == keys_to_set
        assert [] == keys_to_unset

    def test_compare_aws_tags_removed(self):
        new_dict = dict(self.tag_example_dict)
        del new_dict["lowerCamel"]
        del new_dict["Normal case"]
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        assert {} == keys_to_set
        assert set(["lowerCamel", "Normal case"]) == set(keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        assert {} == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        assert {} == keys_to_set
        assert set(["lowerCamel", "Normal case"]) == set(keys_to_unset)

    def test_compare_aws_tags_added(self):
        new_dict = dict(self.tag_example_dict)
        new_keys = {"add_me": "lower case", "Me too!": "Contributing"}
        new_dict.update(new_keys)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset

    def test_compare_aws_tags_changed(self):
        new_dict = dict(self.tag_example_dict)
        new_keys = {"UpperCamel": "anotherCamelValue", "Normal case": "normal value"}
        new_dict.update(new_keys)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset

    def test_compare_aws_tags_boolean(self):
        dict_with_bool = dict(boolean=True)
        dict_with_text_bool = dict(boolean="True")
        # AWS always returns tag values as strings, so we only test this way around
        keys_to_set, keys_to_unset = compare_aws_tags(dict_with_text_bool, dict_with_bool)
        assert {} == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(dict_with_text_bool, dict_with_bool, purge_tags=False)
        assert {} == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(dict_with_text_bool, dict_with_bool, purge_tags=True)
        assert {} == keys_to_set
        assert [] == keys_to_unset

    def test_compare_aws_tags_complex_update(self):
        # Adds 'Me too!', Changes 'UpperCamel' and removes 'Normal case'
        new_dict = dict(self.tag_example_dict)
        new_keys = {"UpperCamel": "anotherCamelValue", "Me too!": "Contributing"}
        new_dict.update(new_keys)
        del new_dict["Normal case"]
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        assert new_keys == keys_to_set
        assert ["Normal case"] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        assert new_keys == keys_to_set
        assert ["Normal case"] == keys_to_unset

    def test_compare_aws_tags_aws(self):
        starting_tags = dict(self.tag_aws_dict)
        desired_tags = dict(self.tag_minimal_dict)
        tags_to_set, tags_to_unset = compare_aws_tags(starting_tags, desired_tags, purge_tags=True)
        assert desired_tags == tags_to_set
        assert [] == tags_to_unset
        # If someone explicitly passes a changed 'aws:' key the APIs will probably
        # throw an error, but this is their responsibility.
        desired_tags.update(self.tag_aws_changed)
        tags_to_set, tags_to_unset = compare_aws_tags(starting_tags, desired_tags, purge_tags=True)
        assert desired_tags == tags_to_set
        assert [] == tags_to_unset

    def test_compare_aws_tags_aws_complex(self):
        old_dict = dict(self.tag_example_dict)
        old_dict.update(self.tag_aws_dict)
        # Adds 'Me too!', Changes 'UpperCamel' and removes 'Normal case'
        new_dict = dict(self.tag_example_dict)
        new_keys = {"UpperCamel": "anotherCamelValue", "Me too!": "Contributing"}
        new_dict.update(new_keys)
        del new_dict["Normal case"]
        keys_to_set, keys_to_unset = compare_aws_tags(old_dict, new_dict)
        assert new_keys == keys_to_set
        assert ["Normal case"] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(old_dict, new_dict, purge_tags=False)
        assert new_keys == keys_to_set
        assert [] == keys_to_unset
        keys_to_set, keys_to_unset = compare_aws_tags(old_dict, new_dict, purge_tags=True)
        assert new_keys == keys_to_set
        assert ["Normal case"] == keys_to_unset

    # ========================================================
    #   tagging.boto3_tag_specifications
    # ========================================================

    def test_boto3_tag_specifications_empty(self):
        assert boto3_tag_specifications(None) is None
        assert boto3_tag_specifications({}) is None

    # Builds upon ansible_dict_to_boto3_tag_list, assume that if a minimal tag
    # dictionary behaves as expected, then all will behave
    def test_boto3_tag_specifications_no_type(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict)
        expected_specification = [{"Tags": self.tag_minimal_boto3_list}]
        assert tag_specification == expected_specification

    def test_boto3_tag_specifications_string_type(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict, "instance")
        expected_specification = [{"ResourceType": "instance", "Tags": self.tag_minimal_boto3_list}]
        assert tag_specification == expected_specification

    def test_boto3_tag_specifications_single_type(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict, ["instance"])
        expected_specification = [{"ResourceType": "instance", "Tags": self.tag_minimal_boto3_list}]
        assert tag_specification == expected_specification

    def test_boto3_tag_specifications_multipe_types(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict, ["instance", "volume"])
        expected_specification = [
            {"ResourceType": "instance", "Tags": self.tag_minimal_boto3_list},
            {"ResourceType": "volume", "Tags": self.tag_minimal_boto3_list},
        ]
        sorted_tag_spec = sorted(tag_specification, key=lambda i: (i["ResourceType"]))
        sorted_expected = sorted(expected_specification, key=lambda i: (i["ResourceType"]))
        assert sorted_tag_spec == sorted_expected

    def test_ansible_dict_to_tag_filter_dict_empty(self):
        assert ansible_dict_to_tag_filter_dict(None) == {}
        assert ansible_dict_to_tag_filter_dict({}) == {}

    def test_ansible_dict_to_tag_filter_dict_example(self):
        assert ansible_dict_to_tag_filter_dict(self.tag_example_dict) == self.tag_filter_dict

    def test_ansible_dict_to_tag_filter_dict_boolean(self):
        dict_with_bool = {"boolean": True}
        filter_dict_with_bool = {"tag:boolean": "True"}
        assert ansible_dict_to_tag_filter_dict(dict_with_bool) == filter_dict_with_bool

# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import map_complex_type


class Ec2Utils(unittest.TestCase):

    # ========================================================
    # Setup some initial data that we can use within our tests
    # ========================================================
    def setUp(self):

        self.tag_example_boto3_list = [
            {'Key': 'lowerCamel', 'Value': 'lowerCamelValue'},
            {'Key': 'UpperCamel', 'Value': 'upperCamelValue'},
            {'Key': 'Normal case', 'Value': 'Normal Value'},
            {'Key': 'lower case', 'Value': 'lower case value'}
        ]

        self.tag_example_dict = {
            'lowerCamel': 'lowerCamelValue',
            'UpperCamel': 'upperCamelValue',
            'Normal case': 'Normal Value',
            'lower case': 'lower case value'
        }

    # ========================================================
    #   ec2.map_complex_type
    # ========================================================
    def test_map_complex_type_over_dict(self):
        complex_type = {'minimum_healthy_percent': "75", 'maximum_percent': "150"}
        type_map = {'minimum_healthy_percent': 'int', 'maximum_percent': 'int'}
        complex_type_mapped = map_complex_type(complex_type, type_map)
        complex_type_expected = {'minimum_healthy_percent': 75, 'maximum_percent': 150}
        self.assertEqual(complex_type_mapped, complex_type_expected)

    # ========================================================
    #   ec2.ansible_dict_to_boto3_filter_list
    # ========================================================

    def test_ansible_dict_with_string_to_boto3_filter_list(self):
        filters = {'some-aws-id': 'i-01234567'}
        filter_list_string = [
            {
                'Name': 'some-aws-id',
                'Values': [
                    'i-01234567',
                ]
            }
        ]

        converted_filters_list = ansible_dict_to_boto3_filter_list(filters)
        self.assertEqual(converted_filters_list, filter_list_string)

    def test_ansible_dict_with_boolean_to_boto3_filter_list(self):
        filters = {'enabled': True}
        filter_list_boolean = [
            {
                'Name': 'enabled',
                'Values': [
                    'true',
                ]
            }
        ]

        converted_filters_bool = ansible_dict_to_boto3_filter_list(filters)
        self.assertEqual(converted_filters_bool, filter_list_boolean)

    def test_ansible_dict_with_integer_to_boto3_filter_list(self):
        filters = {'version': 1}
        filter_list_integer = [
            {
                'Name': 'version',
                'Values': [
                    '1',
                ]
            }
        ]

        converted_filters_int = ansible_dict_to_boto3_filter_list(filters)
        self.assertEqual(converted_filters_int, filter_list_integer)

    # ========================================================
    #   ec2.ansible_dict_to_boto3_tag_list
    # ========================================================

    def test_ansible_dict_to_boto3_tag_list(self):
        converted_list = ansible_dict_to_boto3_tag_list(self.tag_example_dict)
        sorted_converted_list = sorted(converted_list, key=lambda i: (i['Key']))
        sorted_list = sorted(self.tag_example_boto3_list, key=lambda i: (i['Key']))
        self.assertEqual(sorted_converted_list, sorted_list)

    # ========================================================
    #   ec2.boto3_tag_list_to_ansible_dict
    # ========================================================

    def test_boto3_tag_list_to_ansible_dict(self):
        converted_dict = boto3_tag_list_to_ansible_dict(self.tag_example_boto3_list)
        self.assertEqual(converted_dict, self.tag_example_dict)

    def test_boto3_tag_list_to_ansible_dict_empty(self):
        # AWS returns [] when there are no tags
        self.assertEqual(boto3_tag_list_to_ansible_dict([]), {})
        # Minio returns [{}] when there are no tags
        self.assertEqual(boto3_tag_list_to_ansible_dict([{}]), {})

    # ========================================================
    #   ec2.compare_aws_tags
    # ========================================================

    def test_compare_aws_tags_equal(self):
        new_dict = dict(self.tag_example_dict)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        self.assertEqual({}, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        self.assertEqual({}, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        self.assertEqual({}, keys_to_set)
        self.assertEqual([], keys_to_unset)

    def test_compare_aws_tags_removed(self):
        new_dict = dict(self.tag_example_dict)
        del new_dict['lowerCamel']
        del new_dict['Normal case']
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        self.assertEqual({}, keys_to_set)
        self.assertEqual(set(['lowerCamel', 'Normal case']), set(keys_to_unset))
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        self.assertEqual({}, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        self.assertEqual({}, keys_to_set)
        self.assertEqual(set(['lowerCamel', 'Normal case']), set(keys_to_unset))

    def test_compare_aws_tags_added(self):
        new_dict = dict(self.tag_example_dict)
        new_keys = {'add_me': 'lower case', 'Me too!': 'Contributing'}
        new_dict.update(new_keys)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)

    def test_compare_aws_tags_changed(self):
        new_dict = dict(self.tag_example_dict)
        new_keys = {'UpperCamel': 'anotherCamelValue', 'Normal case': 'normal value'}
        new_dict.update(new_keys)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)

    def test_compare_aws_tags_complex_update(self):
        # Adds 'Me too!', Changes 'UpperCamel' and removes 'Normal case'
        new_dict = dict(self.tag_example_dict)
        new_keys = {'UpperCamel': 'anotherCamelValue', 'Me too!': 'Contributing'}
        new_dict.update(new_keys)
        del new_dict['Normal case']
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual(['Normal case'], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=False)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual([], keys_to_unset)
        keys_to_set, keys_to_unset = compare_aws_tags(self.tag_example_dict, new_dict, purge_tags=True)
        self.assertEqual(new_keys, keys_to_set)
        self.assertEqual(['Normal case'], keys_to_unset)

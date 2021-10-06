# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


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

        self.tag_minimal_boto3_list = [
            {'Key': 'mykey', 'Value': 'myvalue'},
        ]

        self.tag_minimal_dict = {'mykey': 'myvalue'}

    # ========================================================
    #   tagging.ansible_dict_to_boto3_tag_list
    # ========================================================

    def test_ansible_dict_to_boto3_tag_list(self):
        converted_list = ansible_dict_to_boto3_tag_list(self.tag_example_dict)
        sorted_converted_list = sorted(converted_list, key=lambda i: (i['Key']))
        sorted_list = sorted(self.tag_example_boto3_list, key=lambda i: (i['Key']))
        self.assertEqual(sorted_converted_list, sorted_list)

    # ========================================================
    #   tagging.boto3_tag_list_to_ansible_dict
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
    #   tagging.compare_aws_tags
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

    # ========================================================
    #   tagging.boto3_tag_specifications
    # ========================================================

    # Builds upon ansible_dict_to_boto3_tag_list, assume that if a minimal tag
    # dictionary behaves as expected, then all will behave
    def test_boto3_tag_specifications_no_type(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict)
        expected_specification = [{'Tags': self.tag_minimal_boto3_list}]
        self.assertEqual(tag_specification, expected_specification)

    def test_boto3_tag_specifications_string_type(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict, 'instance')
        expected_specification = [{'ResourceType': 'instance', 'Tags': self.tag_minimal_boto3_list}]
        self.assertEqual(tag_specification, expected_specification)

    def test_boto3_tag_specifications_single_type(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict, ['instance'])
        expected_specification = [{'ResourceType': 'instance', 'Tags': self.tag_minimal_boto3_list}]
        self.assertEqual(tag_specification, expected_specification)

    def test_boto3_tag_specifications_multipe_types(self):
        tag_specification = boto3_tag_specifications(self.tag_minimal_dict, ['instance', 'volume'])
        expected_specification = [
            {'ResourceType': 'instance', 'Tags': self.tag_minimal_boto3_list},
            {'ResourceType': 'volume', 'Tags': self.tag_minimal_boto3_list},
        ]
        sorted_tag_spec = sorted(tag_specification, key=lambda i: (i['ResourceType']))
        sorted_expected = sorted(expected_specification, key=lambda i: (i['ResourceType']))
        self.assertEqual(sorted_tag_spec, sorted_expected)

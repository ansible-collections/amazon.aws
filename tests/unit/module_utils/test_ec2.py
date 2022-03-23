# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import unittest

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import map_complex_type


class Ec2Utils(unittest.TestCase):

    # ========================================================
    # Setup some initial data that we can use within our tests
    # ========================================================
    def setUp(self):
        pass

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

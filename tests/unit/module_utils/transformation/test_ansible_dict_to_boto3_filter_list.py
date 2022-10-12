# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


class TestAnsibleDictToBoto3FilterList():

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
        assert converted_filters_list == filter_list_string

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
        assert converted_filters_bool == filter_list_boolean

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
        assert converted_filters_int == filter_list_integer

    def test_ansible_dict_with_list_to_boto3_filter_list(self):
        filters = {'version': ['1', '2', '3']}
        filter_list_integer = [
            {
                'Name': 'version',
                'Values': [
                    '1', '2', '3'
                ]
            }
        ]

        converted_filters_int = ansible_dict_to_boto3_filter_list(filters)
        assert converted_filters_int == filter_list_integer

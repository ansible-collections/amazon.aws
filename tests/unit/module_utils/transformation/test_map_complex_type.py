# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.transformation import map_complex_type


class TestMapComplexTypeTestSuite():

    def test_map_complex_type_over_dict(self):
        type_map = {'minimum_healthy_percent': 'int', 'maximum_percent': 'int'}
        complex_type_dict = {'minimum_healthy_percent': "75", 'maximum_percent': "150"}
        complex_type_expected = {'minimum_healthy_percent': 75, 'maximum_percent': 150}

        complex_type_mapped = map_complex_type(complex_type_dict, type_map)

        assert complex_type_mapped == complex_type_expected

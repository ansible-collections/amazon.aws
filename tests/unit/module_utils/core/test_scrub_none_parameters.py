from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.core import scrub_none_parameters

scrub_none_test_data = [
    (dict(),  # Input
     dict(),  # Output with descend_into_lists=False
     dict(),  # Output with descend_into_lists=True
     ),
    (dict(param1=None, param2=None),
     dict(),
     dict(),
     ),
    (dict(param1='something'),
     dict(param1='something'),
     dict(param1='something'),
     ),
    (dict(param1=False),
     dict(param1=False),
     dict(param1=False),
     ),
    (dict(param1=None, param2=[]),
     dict(param2=[]),
     dict(param2=[]),
     ),
    (dict(param1=None, param2=["list_value"]),
     dict(param2=["list_value"]),
     dict(param2=["list_value"]),
     ),
    (dict(param1='something', param2='something_else'),
     dict(param1='something', param2='something_else'),
     dict(param1='something', param2='something_else'),
     ),
    (dict(param1='something', param2=dict()),
     dict(param1='something', param2=dict()),
     dict(param1='something', param2=dict()),
     ),
    (dict(param1='something', param2=None),
     dict(param1='something'),
     dict(param1='something'),
     ),
    (dict(param1='something', param2=None, param3=None),
     dict(param1='something'),
     dict(param1='something'),
     ),
    (dict(param1='something', param2=None, param3=None, param4='something_else'),
     dict(param1='something', param4='something_else'),
     dict(param1='something', param4='something_else'),
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param4='something_else'),
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=dict()), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=dict()), param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=dict()), param4='something_else'),
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=False), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=False), param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=False), param4='something_else'),
     ),
    (dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[]),
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[]),
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[]),
     ),
    (dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2=None)], param2=[]),
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2=None)], param2=[]),
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1')], param2=[]),
     ),
    (dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)], param2=[]),
     dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)], param2=[]),
     dict(param1=[dict(sub_param1=[dict()])], param2=[]),
     ),
    (dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)], param2=None),
     dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)]),
     dict(param1=[dict(sub_param1=[dict()])]),
     ),
]


@pytest.mark.parametrize("input_params, output_params_no_descend, output_params_descend", scrub_none_test_data)
def test_scrub_none_parameters(input_params, output_params_no_descend, output_params_descend):
    assert scrub_none_parameters(input_params) == output_params_no_descend
    assert scrub_none_parameters(input_params, descend_into_lists=False) == output_params_no_descend
    assert scrub_none_parameters(input_params, descend_into_lists=True) == output_params_descend

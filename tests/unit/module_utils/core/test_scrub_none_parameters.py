from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

#from ansible_collections.amazon.aws.plugins.module_utils.core import scrub_none_parameters
from plugins.module_utils.core import scrub_none_parameters
import pytest
scrub_none_test_data = [
    (dict(),
     True,
     dict()
     ),
    (dict(param1='something'),
     True,
     dict(param1='something')
     ),
    (dict(param1=False),
     True,
     dict(param1=False)
     ),
    (dict(param1='something', param2='something_else'),
     True,
     dict(param1='something', param2='something_else')
     ),
    (dict(param1='something', param2=dict()),
     True,
     dict(param1='something', param2=dict())
     ),
    (dict(param1='something', param2=None),
     True,
     dict(param1='something')
     ),
    (dict(param1='something', param2=None, param3=None),
     True,
     dict(param1='something')
     ),
    (dict(param1='something', param2=None, param3=None, param4='something_else'),
     True,
     dict(param1='something', param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=None), param2=None, param3=None, param4='something_else'),
     True,
     dict(param1=dict(sub_param1='something'), param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param2=None, param3=None, param4='something_else'),
     True,
     dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=dict()), param2=None, param3=None, param4='something_else'),
     True,
     dict(param1=dict(sub_param1='something', sub_param2=dict()), param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=False), param2=None, param3=None, param4='something_else'),
     True,
     dict(param1=dict(sub_param1='something', sub_param2=False), param4='something_else')
     ),
    (dict(param1=None, param2=None),
     True,
     dict()
     ),
    (dict(param1=None, param2=[]),
     True,
     dict(param2=[])
     ),
    (dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[]),
     True,
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[])
     ),
    (dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[]),
     False,
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2='my_dict_nested_in_a_list_2')], param2=[])
     ),
    (dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2=None)], param2=[]),
     True,
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1')], param2=[])
     ),
    (dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2=None)], param2=[]),
     False,
     dict(param1=[dict(sub_param1='my_dict_nested_in_a_list_1', sub_param2=None)], param2=[])
     ),
    (dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)], param2=[]),
     True,
     dict(param1=[dict(sub_param1=[{}])], param2=[])
     ),
    (dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)], param2=None),
     False,
     dict(param1=[dict(sub_param1=[dict(sub_sub_param1=None)], sub_param2=None)]),
     )
]


@pytest.mark.parametrize("input_params, descend_into_lists_flag, output_params", scrub_none_test_data)
def test_scrub_none_parameters(input_params, descend_into_lists_flag, output_params):

    assert scrub_none_parameters(input_params, descend_into_lists_flag) == output_params

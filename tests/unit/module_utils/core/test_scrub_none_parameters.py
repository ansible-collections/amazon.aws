from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.core import scrub_none_parameters
import pytest

scrub_none_test_data = [
    (dict(),
     dict()
     ),
    (dict(param1='something'),
     dict(param1='something')
     ),
    (dict(param1=False),
     dict(param1=False)
     ),
    (dict(param1='something', param2='something_else'),
     dict(param1='something', param2='something_else')
     ),
    (dict(param1='something', param2=dict()),
     dict(param1='something', param2=dict())
     ),
    (dict(param1='something', param2=None),
     dict(param1='something')
     ),
    (dict(param1='something', param2=None, param3=None),
     dict(param1='something')
     ),
    (dict(param1='something', param2=None, param3=None, param4='something_else'),
     dict(param1='something', param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=None), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something'), param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=dict(sub_sub_param1='another_thing')), param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=dict()), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=dict()), param4='something_else')
     ),
    (dict(param1=dict(sub_param1='something', sub_param2=False), param2=None, param3=None, param4='something_else'),
     dict(param1=dict(sub_param1='something', sub_param2=False), param4='something_else')
     ),
    (dict(param1=None, param2=None),
     dict()
     ),
    (dict(param1=None, param2=[]),
     dict(param2=[])
     )
]


@pytest.mark.parametrize("input_params, output_params", scrub_none_test_data)
def test_scrub_none_parameters(input_params, output_params):

    assert scrub_none_parameters(input_params) == output_params

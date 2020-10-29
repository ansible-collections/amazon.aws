from plugins.module_utils.core import scrub_none_parameters
import pytest

scrub_none_test_data = [
    (dict(),
     dict()
     ),
    (dict(param1='something'),
     dict(param1='something')
     ),
    (dict(param1='something', param2='something_else'),
     dict(param1='something', param2='something_else')
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
    (dict(param1=None, param2=None),
     dict()
     )
]


@pytest.mark.parametrize("input_params, output_params", scrub_none_test_data)
def test_scrub_none_parameters(input_params, output_params):

    assert scrub_none_parameters(input_params) == output_params

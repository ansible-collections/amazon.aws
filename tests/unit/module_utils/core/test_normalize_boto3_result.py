from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from dateutil import parser as date_parser

from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result

example_date_txt = '2020-12-30T00:00:00.000Z'
example_date_iso = '2020-12-30T00:00:00+00:00'
example_date = date_parser.parse(example_date_txt)


normalize_boto3_result_data = [
    (dict(),
     dict()
     ),
    # Bool
    (dict(param1=False),
     dict(param1=False)
     ),
    # Simple string (shouldn't be touched
    (dict(date_example=example_date_txt),
     dict(date_example=example_date_txt)
     ),
    (dict(date_example=example_date_iso),
     dict(date_example=example_date_iso)
     ),
    # Datetime -> String
    (dict(date_example=example_date),
     dict(date_example=example_date_iso)
     ),
    (list(),
     list()
     ),
    (list([False]),
     list([False])
     ),
    (list([example_date_txt]),
     list([example_date_txt])
     ),
    (list([example_date_iso]),
     list([example_date_iso])
     ),
    (list([example_date]),
     list([example_date_iso])
     ),
]


@pytest.mark.parametrize("input_params, output_params", normalize_boto3_result_data)
def test_normalize_boto3_result(input_params, output_params):

    assert normalize_boto3_result(input_params) == output_params

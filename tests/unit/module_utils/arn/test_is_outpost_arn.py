# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.arn import is_outpost_arn

outpost_arn_test_inputs = [
    ("arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0", True),
    ("arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0123", False),
    ("arn:aws:outpost:us-east-1:123456789012:outpost/op-1234567890abcdef0", False),
    ("ars:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0", False),
    ("arn:was:outposts:us-east-1:123456789012:outpost/ op-1234567890abcdef0", False),
    ("arn:aws:outpost:us-east-1: 123456789012:outpost/ op-1234567890abcdef0", False),
    ("ars:aws:outposts:us-east-1: 123456789012:outpost/ op-1234567890abcdef0", False),
    ("arn:was:outposts:us-east-1: 123456789012:outpost/ op-1234567890abcdef0", False),
]


@pytest.mark.parametrize("outpost_arn, result", outpost_arn_test_inputs)
def test_is_outpost_arn(outpost_arn, result):
    assert is_outpost_arn(outpost_arn) == result

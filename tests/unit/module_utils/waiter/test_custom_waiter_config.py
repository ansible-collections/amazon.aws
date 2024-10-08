# -*- coding: utf-8 -*-
# Copyright: Ansible Project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.waiter import custom_waiter_config

# Total time = (MaxAttempts - 1) * Delay
# There's no pause before the first attempt, or after the last attempt
TEST_DATA = [
    # Only performs a single attempt, no retries
    [dict(timeout=0), {"Delay": 1, "MaxAttempts": 1}],
    # 1 second
    [dict(timeout=1), {"Delay": 1, "MaxAttempts": 2}],
    # 2 seconds
    [dict(timeout=2), {"Delay": 1, "MaxAttempts": 3}],
    # 4 seconds
    [dict(timeout=4), {"Delay": 1, "MaxAttempts": 5}],
    # 6 seconds
    [dict(timeout=6), {"Delay": 2, "MaxAttempts": 4}],
    # 10 seconds
    [dict(timeout=10), {"Delay": 2, "MaxAttempts": 6}],
    # 12 seconds
    [dict(timeout=11), {"Delay": 2, "MaxAttempts": 7}],
    # 12 seconds
    [dict(timeout=10, default_pause=10), {"Delay": 3, "MaxAttempts": 5}],
    # 12 seconds
    [dict(timeout=10, default_pause=15), {"Delay": 3, "MaxAttempts": 5}],
    # 105 seconds
    [dict(timeout=100, default_pause=15), {"Delay": 15, "MaxAttempts": 8}],
    # 150 seconds
    [dict(timeout=150, default_pause=15), {"Delay": 15, "MaxAttempts": 11}],
]


class TestCustomWaiterConfig:
    def setup_method(self):
        pass

    @pytest.mark.parametrize("input_params, output_params", deepcopy(TEST_DATA))
    def test_custom_waiter(self, input_params, output_params):
        # Test default behaviour
        assert custom_waiter_config(**input_params) == output_params

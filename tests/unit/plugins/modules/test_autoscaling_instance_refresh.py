# (c) 2024 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.modules.autoscaling_instance_refresh import validate_healthy_percentage


@pytest.mark.parametrize(
    "min_healthy, max_healthy, expected_error",
    [
        (90, None, None),
        (-1, None, "The value range for the min_healthy_percentage is 0 to 100."),
        (101, None, "The value range for the min_healthy_percentage is 0 to 100."),
        (None, 90, "The value range for the max_healthy_percentage is 100 to 200."),
        (None, 201, "The value range for the max_healthy_percentage is 100 to 200."),
        (None, 100, "You must also specify min_healthy_percentage when max_healthy_percentage is specified."),
        (10, 100, None),
        (
            10,
            150,
            "The difference between the max_healthy_percentage and min_healthy_percentage cannot be greater than 100.",
        ),
    ],
)
def test_validate_healthy_percentage(min_healthy, max_healthy, expected_error):
    preferences = dict(min_healthy_percentage=min_healthy, max_healthy_percentage=max_healthy)
    assert expected_error == validate_healthy_percentage(preferences)

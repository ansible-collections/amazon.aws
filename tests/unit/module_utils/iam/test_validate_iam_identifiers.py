# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers

# See also: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html
validate_test_data = [
    (
        dict(),  # Input
        None,  # Output role
        None,  # Output user
        None,  # Output generic
    ),
    (dict(path="/"), None, None, None),
    (dict(name="Example"), None, None, None),
    # Path tests
    (
        dict(path="/12345abcd"),
        "path must begin and end with /",
        "path must begin and end with /",
        "path must begin and end with /",
    ),
    (dict(path="/12345abcd/"), None, None, None),
    (dict(path=f"/{'12345abcd0' * 51}/"), None, None, None),  # Max length 512 chars
    (
        dict(path=f"/{'12345abcd/' * 51}a/"),
        "path may not exceed 512",
        "path may not exceed 512",
        "path may not exceed 512",
    ),
    (dict(path="/12345+=,.@_-abcd/"), None, None, None),  # limited allowed special characters
    (dict(path="/12345&abcd/"), "path must match pattern", "path must match pattern", "path must match pattern"),
    (dict(path="/12345:abcd/"), "path must match pattern", "path must match pattern", "path must match pattern"),
    # Name tests
    (dict(name="12345abcd"), None, None, None),
    (dict(name=f"{'12345abcd0' * 6}1234"), None, None, None),  # Max length
    (dict(name=f"{'12345abcd0' * 6}12345"), "name may not exceed 64", "name may not exceed 64", None),
    (dict(name=f"{'12345abcd0' * 12}12345678"), "name may not exceed 64", "name may not exceed 64", None),
    (
        dict(name=f"{'12345abcd0' * 12}123456789"),
        "name may not exceed 64",
        "name may not exceed 64",
        "name may not exceed 128",
    ),
    (dict(name="12345+=,.@_-abcd"), None, None, None),  # limited allowed special characters
    (dict(name="12345&abcd"), "name must match pattern", "name must match pattern", "name must match pattern"),
    (dict(name="12345:abcd"), "name must match pattern", "name must match pattern", "name must match pattern"),
    (dict(name="/12345/abcd/"), "name must match pattern", "name must match pattern", "name must match pattern"),
    # Dual tests
    (dict(path="/example/", name="Example"), None, None, None),
    (dict(path="/exa:ple/", name="Example"), "path", "path", "path"),
    (dict(path="/example/", name="Exa:ple"), "name", "name", "name"),
]


@pytest.mark.parametrize("input_params, output_role, output_user, output_generic", validate_test_data)
def test_scrub_none_parameters(input_params, output_role, output_user, output_generic):
    # Role and User have additional length constraints
    return_role = validate_iam_identifiers("role", **input_params)
    return_user = validate_iam_identifiers("user", **input_params)
    return_generic = validate_iam_identifiers("generic", **input_params)

    if output_role is None:
        assert return_role is None
    else:
        assert return_role is not None
        assert output_role in return_role
    if output_user is None:
        assert return_user is None
    else:
        assert return_user is not None
        assert output_user in return_user

    # Defaults
    if output_generic is None:
        assert return_generic is None
    else:
        assert return_generic is not None
        assert output_generic in return_generic

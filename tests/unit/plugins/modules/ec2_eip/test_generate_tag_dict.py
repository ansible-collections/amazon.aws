# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import ANY
from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_eip


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.params = {}
    module.fail_json.side_effect = SystemExit(1)
    return module


@pytest.mark.parametrize(
    "tag_name,tag_value,expected",
    [
        (None, ANY, None),
        ("tag:SomeKey", None, {"tag-key": "SomeKey"}),
        ("SomeKey", None, {"tag-key": "SomeKey"}),
        ("tag:AnotherKey", "SomeValue", {"tag:AnotherKey": "SomeValue"}),
        ("AnotherKey", "AnotherValue", {"tag:AnotherKey": "AnotherValue"}),
    ],
)
def test_generate_tag_dict(ansible_module, tag_name, tag_value, expected):
    ansible_module.params.update({"tag_name": tag_name, "tag_value": tag_value})
    assert expected == ec2_eip.generate_tag_dict(ansible_module)

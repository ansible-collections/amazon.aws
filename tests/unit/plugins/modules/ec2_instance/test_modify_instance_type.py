# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_instance

module_path = "ansible_collections.amazon.aws.plugins.modules.ec2_instance"


@pytest.fixture(name="ansible_aws_module")
def fixture_ansible_aws_module():
    module = MagicMock()
    module.params = {}
    module.check_mode = False
    module.fail_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(1)
    return module


@pytest.mark.parametrize("state", ["present", "started", "running", "stopped", "restarted", "rebooted"])
@patch(module_path + ".modify_instance_attribute")
@patch(module_path + ".await_instances")
@patch(module_path + ".ensure_instance_state")
def test_modify_instance_type(
    m_ensure_instance_state, m_await_instances, m_modify_instance_attribute, ansible_aws_module, state
):
    instance_id = MagicMock()
    client = MagicMock()
    state = "present"
    changes = MagicMock()
    desired_module_state = "running" if state == "present" else state

    ec2_instance.modify_instance_type(client, ansible_aws_module, state, instance_id, changes)
    m_await_instances.assert_called_once_with(
        client, ansible_aws_module, ids=[instance_id], desired_module_state="stopped", force_wait=True
    )
    m_modify_instance_attribute.assert_called_once_with(client, instance_id=instance_id, **changes)
    filters = {"instance-id": [instance_id]}
    m_ensure_instance_state.assert_has_calls(
        [
            call(client, ansible_aws_module, "stopped", filters),
            call(client, ansible_aws_module, desired_module_state, filters),
        ]
    )


@pytest.mark.parametrize("check_mode", [True, False])
@pytest.mark.parametrize("attribute", ["InstanceType", "Ramdisk", "DisableApiTermination"])
@patch(module_path + ".modify_instance_attribute")
@patch(module_path + ".modify_instance_type")
def test_modify_ec2_instance_attribute(
    m_modify_instance_type, m_modify_instance_attribute, ansible_aws_module, check_mode, attribute
):
    client = MagicMock()
    state = MagicMock()
    instance_id = MagicMock()
    attribute_value = MagicMock()

    ansible_aws_module.check_mode = check_mode

    ec2_instance.modify_ec2_instance_attribute(
        client, ansible_aws_module, state, [{"InstanceId": instance_id, attribute: attribute_value}]
    )
    if check_mode:
        m_modify_instance_type.assert_not_called()
        m_modify_instance_attribute.assert_not_called()
    elif "InstanceType" == attribute:
        m_modify_instance_type.assert_called_once_with(
            client, ansible_aws_module, state, instance_id, {attribute: attribute_value}
        )
        m_modify_instance_attribute.assert_not_called()
    else:
        m_modify_instance_type.assert_not_called()
        m_modify_instance_attribute.assert_called_once_with(
            client, instance_id=instance_id, **{attribute: attribute_value}
        )

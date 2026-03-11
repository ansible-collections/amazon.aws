# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory


def test_get_role_session_name_with_ansible_name():
    """Test _get_role_session_name when ansible_name is set."""
    inventory_plugin = utils_inventory.AWSInventoryBase()
    inventory_plugin.ansible_name = "aws_ec2"

    session_name = inventory_plugin._get_role_session_name()

    assert session_name == "ansible_aws_aws_ec2_dynamic_inventory"


def test_get_role_session_name_without_ansible_name():
    """Test _get_role_session_name when ansible_name is not set."""
    inventory_plugin = utils_inventory.AWSInventoryBase()

    session_name = inventory_plugin._get_role_session_name()

    assert session_name == "ansible_aws_dynamic_inventory"


def test_get_role_session_name_with_custom_plugin_name():
    """Test _get_role_session_name with a custom plugin name."""
    inventory_plugin = utils_inventory.AWSInventoryBase()
    inventory_plugin.ansible_name = "my_custom_inventory"

    session_name = inventory_plugin._get_role_session_name()

    assert session_name == "ansible_aws_my_custom_inventory_dynamic_inventory"


def test_get_role_session_name_with_none_ansible_name():
    """Test _get_role_session_name when ansible_name is explicitly None."""
    inventory_plugin = utils_inventory.AWSInventoryBase()
    inventory_plugin.ansible_name = None

    session_name = inventory_plugin._get_role_session_name()

    assert session_name == "ansible_aws_dynamic_inventory"

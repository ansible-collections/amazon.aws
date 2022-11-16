# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import sentinel

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory


@patch("ansible.plugins.inventory.BaseInventoryPlugin.parse", MagicMock)
def test_parse(monkeypatch):
    require_aws_sdk = MagicMock(name='require_aws_sdk')
    require_aws_sdk.return_value = sentinel.RETURNED_SDK
    config_data = MagicMock(name='_read_config_data')
    config_data.return_value = sentinel.RETURNED_OPTIONS
    frozen_credentials = MagicMock(name='_set_frozen_credentials')
    frozen_credentials.return_value = sentinel.RETURNED_CREDENTIALS

    inventory_plugin = utils_inventory.AWSInventoryBase()
    monkeypatch.setattr(inventory_plugin, 'require_aws_sdk', require_aws_sdk)
    monkeypatch.setattr(inventory_plugin, '_read_config_data', config_data)
    monkeypatch.setattr(inventory_plugin, '_set_frozen_credentials', frozen_credentials)

    inventory_plugin.parse(sentinel.PARAM_INVENTORY, sentinel.PARAM_LOADER, sentinel.PARAM_PATH)
    assert require_aws_sdk.call_args == call(botocore_version=None, boto3_version=None)
    assert config_data.call_args == call(sentinel.PARAM_PATH)
    assert frozen_credentials.call_args == call()

# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import sentinel

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory
import ansible_collections.amazon.aws.plugins.plugin_utils.base as utils_base

# import ansible_collections.amazon.aws.plugins.module_utils.


def test_client(monkeypatch):
    super_client = MagicMock(name="client")
    super_client.return_value = sentinel.SUPER_CLIENT
    monkeypatch.setattr(utils_base.AWSPluginBase, "client", super_client)
    inventory_plugin = utils_inventory.AWSInventoryBase()

    client = inventory_plugin.client(sentinel.SERVICE_NAME)
    assert super_client.call_args == call(sentinel.SERVICE_NAME)
    assert client is sentinel.SUPER_CLIENT

    client = inventory_plugin.client(sentinel.SERVICE_NAME, extra_arg=sentinel.EXTRA_ARG)
    assert super_client.call_args == call(sentinel.SERVICE_NAME, extra_arg=sentinel.EXTRA_ARG)
    assert client is sentinel.SUPER_CLIENT

    frozen_creds = {"credential_one": sentinel.CREDENTIAL_ONE}
    inventory_plugin._frozen_credentials = frozen_creds

    client = inventory_plugin.client(sentinel.SERVICE_NAME)
    assert super_client.call_args == call(sentinel.SERVICE_NAME, credential_one=sentinel.CREDENTIAL_ONE)
    assert client is sentinel.SUPER_CLIENT

    client = inventory_plugin.client(sentinel.SERVICE_NAME, extra_arg=sentinel.EXTRA_ARG)
    assert super_client.call_args == call(
        sentinel.SERVICE_NAME, credential_one=sentinel.CREDENTIAL_ONE, extra_arg=sentinel.EXTRA_ARG
    )
    assert client is sentinel.SUPER_CLIENT

    client = inventory_plugin.client(sentinel.SERVICE_NAME, credential_one=sentinel.CREDENTIAL_ARG)
    assert super_client.call_args == call(
        sentinel.SERVICE_NAME,
        credential_one=sentinel.CREDENTIAL_ARG,
    )
    assert client is sentinel.SUPER_CLIENT


def test_resource(monkeypatch):
    super_resource = MagicMock(name="resource")
    super_resource.return_value = sentinel.SUPER_RESOURCE
    monkeypatch.setattr(utils_base.AWSPluginBase, "resource", super_resource)
    inventory_plugin = utils_inventory.AWSInventoryBase()

    resource = inventory_plugin.resource(sentinel.SERVICE_NAME)
    assert super_resource.call_args == call(sentinel.SERVICE_NAME)
    assert resource is sentinel.SUPER_RESOURCE

    resource = inventory_plugin.resource(sentinel.SERVICE_NAME, extra_arg=sentinel.EXTRA_ARG)
    assert super_resource.call_args == call(sentinel.SERVICE_NAME, extra_arg=sentinel.EXTRA_ARG)
    assert resource is sentinel.SUPER_RESOURCE

    frozen_creds = {"credential_one": sentinel.CREDENTIAL_ONE}
    inventory_plugin._frozen_credentials = frozen_creds

    resource = inventory_plugin.resource(sentinel.SERVICE_NAME)
    assert super_resource.call_args == call(sentinel.SERVICE_NAME, credential_one=sentinel.CREDENTIAL_ONE)
    assert resource is sentinel.SUPER_RESOURCE

    resource = inventory_plugin.resource(sentinel.SERVICE_NAME, extra_arg=sentinel.EXTRA_ARG)
    assert super_resource.call_args == call(
        sentinel.SERVICE_NAME, credential_one=sentinel.CREDENTIAL_ONE, extra_arg=sentinel.EXTRA_ARG
    )
    assert resource is sentinel.SUPER_RESOURCE

    resource = inventory_plugin.resource(sentinel.SERVICE_NAME, credential_one=sentinel.CREDENTIAL_ARG)
    assert super_resource.call_args == call(
        sentinel.SERVICE_NAME,
        credential_one=sentinel.CREDENTIAL_ARG,
    )
    assert resource is sentinel.SUPER_RESOURCE


def test_all_clients(monkeypatch):
    test_regions = ["us-east-1", "us-east-2"]
    inventory_plugin = utils_inventory.AWSInventoryBase()
    mock_client = MagicMock(name="client")
    mock_client.return_value = sentinel.RETURN_CLIENT
    monkeypatch.setattr(inventory_plugin, "client", mock_client)
    boto3_regions = MagicMock(name="_boto3_regions")
    boto3_regions.return_value = test_regions
    monkeypatch.setattr(inventory_plugin, "_boto3_regions", boto3_regions)

    regions = []
    for client, region in inventory_plugin.all_clients(sentinel.ARG_SERVICE):
        assert boto3_regions.call_args == call(service=sentinel.ARG_SERVICE)
        assert mock_client.call_args == call(sentinel.ARG_SERVICE, region=region)
        assert client is sentinel.RETURN_CLIENT
        regions.append(region)

    assert set(regions) == set(test_regions)

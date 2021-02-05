# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
try:
    from botocore.exceptions import ClientError
except ImportError:
    pass

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO3
from ansible_collections.community.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.community.aws.tests.unit.compat.mock import patch
from ansible_collections.community.aws.tests.unit.compat.mock import call
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import AnsibleExitJson
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import AnsibleFailJson
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import ModuleTestCase
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import set_module_args

from ansible_collections.community.aws.plugins.modules import aws_direct_connect_confirm_connection

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_aws_direct_connect_confirm_connection.py requires the `boto3` and `botocore` modules")


@patch('ansible_collections.amazon.aws.plugins.module_utils.core.HAS_BOTO3', new=True)
@patch.object(aws_direct_connect_confirm_connection.AnsibleAWSModule, "client")
class TestAWSDirectConnectConfirmConnection(ModuleTestCase):
    def test_missing_required_parameters(self, *args):
        set_module_args({})
        with self.assertRaises(AnsibleFailJson) as exec_info:
            aws_direct_connect_confirm_connection.main()

        result = exec_info.exception.args[0]
        assert result["failed"] is True
        assert "name" in result["msg"]
        assert "connection_id" in result["msg"]

    def test_get_by_connection_id(self, mock_client):
        mock_client.return_value.describe_connections.return_value = {
            "connections": [
                {
                    "connectionState": "requested",
                    "connectionId": "dxcon-fgq9rgot",
                    "location": "EqSe2",
                    "connectionName": "ansible-test-connection",
                    "bandwidth": "1Gbps",
                    "ownerAccount": "448830907657",
                    "region": "us-west-2"
                }
            ]
        }
        set_module_args({
            "connection_id": "dxcon-fgq9rgot"
        })
        with self.assertRaises(AnsibleExitJson) as exec_info:
            aws_direct_connect_confirm_connection.main()

        result = exec_info.exception.args[0]
        assert result["changed"] is False
        assert result["connection_state"] == "requested"
        mock_client.return_value.describe_connections.assert_has_calls([
            call(connectionId="dxcon-fgq9rgot")
        ])
        mock_client.return_value.confirm_connection.assert_not_called()

    def test_get_by_name(self, mock_client):
        mock_client.return_value.describe_connections.return_value = {
            "connections": [
                {
                    "connectionState": "requested",
                    "connectionId": "dxcon-fgq9rgot",
                    "location": "EqSe2",
                    "connectionName": "ansible-test-connection",
                    "bandwidth": "1Gbps",
                    "ownerAccount": "448830907657",
                    "region": "us-west-2"
                }
            ]
        }
        set_module_args({
            "name": "ansible-test-connection"
        })
        with self.assertRaises(AnsibleExitJson) as exec_info:
            aws_direct_connect_confirm_connection.main()

        result = exec_info.exception.args[0]
        assert result["changed"] is False
        assert result["connection_state"] == "requested"
        mock_client.return_value.describe_connections.assert_has_calls([
            call(),
            call(connectionId="dxcon-fgq9rgot")
        ])
        mock_client.return_value.confirm_connection.assert_not_called()

    def test_missing_connection_id(self, mock_client):
        mock_client.return_value.describe_connections.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'DescribeConnection')
        set_module_args({
            "connection_id": "dxcon-aaaabbbb"
        })
        with self.assertRaises(AnsibleFailJson) as exec_info:
            aws_direct_connect_confirm_connection.main()

        result = exec_info.exception.args[0]
        assert result["failed"] is True
        mock_client.return_value.describe_connections.assert_has_calls([
            call(connectionId="dxcon-aaaabbbb")
        ])

    def test_missing_name(self, mock_client):
        mock_client.return_value.describe_connections.return_value = {
            "connections": [
                {
                    "connectionState": "requested",
                    "connectionId": "dxcon-fgq9rgot",
                    "location": "EqSe2",
                    "connectionName": "ansible-test-connection",
                    "bandwidth": "1Gbps",
                    "ownerAccount": "448830907657",
                    "region": "us-west-2"
                }
            ]
        }
        set_module_args({
            "name": "foobar"
        })
        with self.assertRaises(AnsibleFailJson) as exec_info:
            aws_direct_connect_confirm_connection.main()

        result = exec_info.exception.args[0]
        assert result["failed"] is True
        mock_client.return_value.describe_connections.assert_has_calls([
            call()
        ])

    def test_confirm(self, mock_client):
        mock_client.return_value.describe_connections.return_value = {
            "connections": [
                {
                    "connectionState": "ordering",
                    "connectionId": "dxcon-fgq9rgot",
                    "location": "EqSe2",
                    "connectionName": "ansible-test-connection",
                    "bandwidth": "1Gbps",
                    "ownerAccount": "448830907657",
                    "region": "us-west-2"
                }
            ]
        }
        mock_client.return_value.confirm_connection.return_value = [{}]
        set_module_args({
            "connection_id": "dxcon-fgq9rgot"
        })
        with self.assertRaises(AnsibleExitJson) as exec_info:
            aws_direct_connect_confirm_connection.main()

        result = exec_info.exception.args[0]
        assert result["changed"] is True
        mock_client.return_value.describe_connections.assert_has_calls([
            call(connectionId="dxcon-fgq9rgot"),
            call(connectionId="dxcon-fgq9rgot"),
            call(connectionId="dxcon-fgq9rgot")
        ])
        mock_client.return_value.confirm_connection.assert_called_once_with(connectionId="dxcon-fgq9rgot")

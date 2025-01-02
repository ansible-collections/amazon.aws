# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_eip

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_eip"


class FailJsonException(Exception):
    def __init__(self):
        pass


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.fail_json.side_effect = FailJsonException()
    module.fail_json_aws.side_effect = FailJsonException()
    module.check_mode = False
    return module


def mock_address():
    return {
        "InstanceId": "i-12345678",
        "PublicIp": "1.2.3.4",
        "AllocationId": "eipalloc-12345678",
        "AssociationId": "eipassoc-12345678",
        "Domain": "vpc",
        "NetworkInterfaceId": "eni-12345678",
        "NetworkInterfaceOwnerId": "123456789012",
        "PrivateIpAddress": "10.0.0.1",
        "Tags": [{"Key": "Name", "Value": "MyElasticIP"}],
        "PublicIpv4Pool": "my-ipv4-pool",
        "NetworkBorderGroup": "my-border-group",
        "CustomerOwnedIp": "192.0.2.0",
        "CustomerOwnedIpv4Pool": "my-customer-owned-pool",
        "CarrierIp": "203.0.113.0",
    }


def mock_return_value_describe_addresses_attribute():
    return {
        "Addresses": [
            {
                "PublicIp": "1.2.3.4",
                "AllocationId": "eipalloc-12345678",
                "PtrRecord": "current.example.com.",
                "PtrRecordUpdate": {
                    "Value": "current.example.com.",
                    "Status": "successful",
                    "Reason": "updated",
                },
            }
        ]
    }


def test_update_reverse_dns_record_of_eip_no_change_in_dns_record(ansible_module):
    client = MagicMock()

    address = mock_address()
    mock_domain_name = "current.example.com"

    client.describe_addresses_attribute.return_value = mock_return_value_describe_addresses_attribute()

    client.modify_address_attribute.return_value = None
    client.reset_address_attribute.return_value = None

    assert ec2_eip.update_reverse_dns_record_of_eip(client, ansible_module, address, mock_domain_name) == (
        False,
        {"ptr_record": mock_domain_name + "."},
    )

    assert client.describe_addresses_attribute.call_count == 1
    assert client.modify_address_attribute.call_count == 0
    assert client.reset_address_attribute.call_count == 0

    client.describe_addresses_attribute.assert_called_once_with(
        AllocationIds=["eipalloc-12345678"], Attribute="domain-name"
    )


def test_update_reverse_dns_record_of_eip_reset_dns_record(ansible_module):
    client = MagicMock()

    address = mock_address()
    mock_domain_name = ""

    client.describe_addresses_attribute.return_value = mock_return_value_describe_addresses_attribute()

    client.modify_address_attribute.return_value = None
    client.reset_address_attribute.return_value = {
        "Addresses": [
            {
                "PublicIp": "1.2.3.4",
                "AllocationId": "eipalloc-12345678",
                "PtrRecord": "current.example.com.",
                "PtrRecordUpdate": {
                    "Value": "",
                    "Status": "PENDING",
                    "Reason": "update in progress",
                },
            }
        ]
    }

    assert ec2_eip.update_reverse_dns_record_of_eip(client, ansible_module, address, mock_domain_name) == (
        True,
        {
            "addresses": [
                {
                    "public_ip": "1.2.3.4",
                    "allocation_id": "eipalloc-12345678",
                    "ptr_record": "current.example.com.",
                    "ptr_record_update": {"value": "", "status": "PENDING", "reason": "update in progress"},
                }
            ]
        },
    )

    assert client.describe_addresses_attribute.call_count == 1
    assert client.modify_address_attribute.call_count == 0
    assert client.reset_address_attribute.call_count == 1

    client.describe_addresses_attribute.assert_called_once_with(
        AllocationIds=["eipalloc-12345678"], Attribute="domain-name"
    )
    client.reset_address_attribute.assert_called_once_with(AllocationId="eipalloc-12345678", Attribute="domain-name")


def test_update_reverse_dns_record_of_eip_modify_dns_record(ansible_module):
    client = MagicMock()

    address = mock_address()

    mock_domain_name = "new.example.com"

    client.describe_addresses_attribute.return_value = mock_return_value_describe_addresses_attribute()

    client.modify_address_attribute.return_value = {
        "Addresses": [
            {
                "PublicIp": "1.2.3.4",
                "AllocationId": "eipalloc-12345678",
                "PtrRecord": "current.example.com.",
                "PtrRecordUpdate": {
                    "Value": "new.example.com",
                    "Status": "PENDING",
                    "Reason": "update in progress",
                },
            }
        ]
    }
    client.reset_address_attribute.return_value = None

    assert ec2_eip.update_reverse_dns_record_of_eip(client, ansible_module, address, mock_domain_name) == (
        True,
        {
            "addresses": [
                {
                    "public_ip": "1.2.3.4",
                    "allocation_id": "eipalloc-12345678",
                    "ptr_record": "current.example.com.",
                    "ptr_record_update": {
                        "value": "new.example.com",
                        "status": "PENDING",
                        "reason": "update in progress",
                    },
                }
            ]
        },
    )

    assert client.describe_addresses_attribute.call_count == 1
    assert client.modify_address_attribute.call_count == 1
    assert client.reset_address_attribute.call_count == 0

    client.describe_addresses_attribute.assert_called_once_with(
        AllocationIds=["eipalloc-12345678"], Attribute="domain-name"
    )
    client.modify_address_attribute.assert_called_once_with(
        AllocationId="eipalloc-12345678", DomainName=mock_domain_name
    )

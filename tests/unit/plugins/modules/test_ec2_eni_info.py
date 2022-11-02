# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock, patch, ANY, call
import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_eni_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_eni_info"


@pytest.mark.parametrize("eni_id,filters,expected", [('', {}, {}), ('eni-1234567890', {}, {'NetworkInterfaceIds': ['eni-1234567890']})])
def test_build_request_args(eni_id, filters, expected):
    assert ec2_eni_info.build_request_args(eni_id, filters) == expected


def test_get_network_interfaces():
    connection = MagicMock()
    module = MagicMock()

    connection.describe_network_interfaces.return_value = {
        'NetworkInterfaces': [
            {
                "AvailabilityZone": "us-east-2b",
                "Description": "",
                "Groups": [
                    {
                        "GroupId": "sg-05db20a1234567890",
                        "GroupName": "TestGroup1"
                    }
                ],
                "InterfaceType": "interface",
                "Ipv6Addresses": [],
                "MacAddress": "00:11:66:77:11:bb",
                "NetworkInterfaceId": "eni-1234567890",
                "OwnerId": "1234567890",
                "PrivateIpAddress": "11.22.33.44",
                "PrivateIpAddresses": [
                    {
                        "Primary": "True",
                        "PrivateIpAddress": "11.22.33.44"
                    }
                ],
                "RequesterManaged": False,
                "SourceDestCheck": True,
                "Status": "available",
                "SubnetId": "subnet-07d906b8358869bda",
                "TagSet": [],
                "VpcId": "vpc-0cb60952be96c9cd8"
            }
        ]
    }

    request_args = {'NetworkInterfaceIds': ['eni-1234567890']}

    network_interfaces_result = ec2_eni_info.get_network_interfaces(connection, module, request_args)

    connection.describe_network_interfaces.call_count == 1
    connection.describe_network_interfaces.assert_called_with(aws_retry=True, **request_args)
    assert len(network_interfaces_result['NetworkInterfaces']) == 1


@patch(module_name + '.get_network_interfaces')
@patch(module_name + '.build_request_args')
def test_list_eni(m_build_request_args, m_get_network_interfaces):
    connection = MagicMock()
    module = MagicMock()

    m_build_request_args.return_value = {
        'Filters': [{
            'Name': 'owner-id',
            'Values': [
                '1234567890'
            ]
        }]
    }

    m_get_network_interfaces.return_value = {
        'NetworkInterfaces': [
            {
                "AvailabilityZone": "us-east-2b",
                "Description": "",
                "Groups": [
                    {
                        "GroupId": "sg-05db20a1234567890",
                        "GroupName": "TestGroup1"
                    }
                ],
                "InterfaceType": "interface",
                "Ipv6Addresses": [],
                "MacAddress": "00:11:66:77:11:bb",
                "NetworkInterfaceId": "eni-1234567890",
                "OwnerId": "1234567890",
                "PrivateIpAddress": "11.22.33.44",
                "PrivateIpAddresses": [
                    {
                        "Primary": "True",
                        "PrivateIpAddress": "11.22.33.44"
                    }
                ],
                "RequesterManaged": False,
                "SourceDestCheck": True,
                "Status": "available",
                "SubnetId": "subnet-07d906b8358869bda",
                "TagSet": [],
                "VpcId": "vpc-0cb60952be96c9cd8"
            },
            {
                "AvailabilityZone": "us-east-2b",
                "Description": "",
                "Groups": [
                    {
                        "GroupId": "sg-05db20a1234567890",
                        "GroupName": "TestGroup1"
                    }
                ],
                "InterfaceType": "interface",
                "Ipv6Addresses": [],
                "MacAddress": "00:11:66:77:11:bb",
                "NetworkInterfaceId": "eni-0987654321",
                "OwnerId": "1234567890",
                "PrivateIpAddress": "11.22.33.44",
                "PrivateIpAddresses": [
                    {
                        "Primary": "True",
                        "PrivateIpAddress": "11.22.33.44"
                    }
                ],
                "RequesterManaged": False,
                "SourceDestCheck": True,
                "Status": "available",
                "SubnetId": "subnet-07d906b8358869bda",
                "TagSet": [{
                    'Key': 'Name',
                    'Value': 'my-test-eni-name'
                }, ],
                "VpcId": "vpc-0cb60952be96c9cd8"
            },
        ]
    }

    request_args = ec2_eni_info.build_request_args()

    camel_network_interfaces = ec2_eni_info.list_eni(connection, module, request_args)

    m_get_network_interfaces.call_count == 1
    m_get_network_interfaces.assert_has_calls(
        [
            call(connection, module, request_args),
        ]
    )
    assert len(camel_network_interfaces) == 2

    assert camel_network_interfaces[0].get('id', None) == 'eni-1234567890'
    assert camel_network_interfaces[0].get('tags', None) == {}
    assert camel_network_interfaces[0].get('name', None) is None

    assert camel_network_interfaces[1].get('id', None) == 'eni-0987654321'
    assert camel_network_interfaces[1].get('tags', None) == {'Name': 'my-test-eni-name'}
    assert camel_network_interfaces[1].get('name', None) == 'my-test-eni-name'


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_eni_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)

# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock, patch, ANY
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
            },
        ]
    }

    request_args = {'NetworkInterfaceIds': ['eni-1234567890']}

    network_interfaces_result = ec2_eni_info.get_network_interfaces(connection, module, request_args)

    connection.describe_network_interfaces.call_count == 1
    connection.describe_network_interfaces.assert_called_with(aws_retry=True, **request_args)
    assert len(network_interfaces_result['NetworkInterfaces']) == 1


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_eni_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)

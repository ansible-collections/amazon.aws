# -*- coding: utf-8 -*-

# Copyright 2017 Sloane Hertel <shertel@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import datetime
from unittest.mock import Mock, MagicMock

from ansible.errors import AnsibleError
from ansible.parsing.dataloader import DataLoader
from ansible_collections.amazon.aws.plugins.inventory.aws_ec2 import InventoryModule, instance_data_filter_to_boto_attr


instances = {
    'Instances': [
        {'Monitoring': {'State': 'disabled'},
         'PublicDnsName': 'ec2-12-345-67-890.compute-1.amazonaws.com',
         'State': {'Code': 16, 'Name': 'running'},
         'EbsOptimized': False,
         'LaunchTime': datetime.datetime(2017, 10, 31, 12, 59, 25),
         'PublicIpAddress': '12.345.67.890',
         'PrivateIpAddress': '098.76.54.321',
         'ProductCodes': [],
         'VpcId': 'vpc-12345678',
         'StateTransitionReason': '',
         'InstanceId': 'i-00000000000000000',
         'EnaSupport': True,
         'ImageId': 'ami-12345678',
         'PrivateDnsName': 'ip-098-76-54-321.ec2.internal',
         'KeyName': 'testkey',
         'SecurityGroups': [{'GroupName': 'default', 'GroupId': 'sg-12345678'}],
         'ClientToken': '',
         'SubnetId': 'subnet-12345678',
         'InstanceType': 't2.micro',
         'NetworkInterfaces': [
            {'Status': 'in-use',
             'MacAddress': '12:a0:50:42:3d:a4',
             'SourceDestCheck': True,
             'VpcId': 'vpc-12345678',
             'Description': '',
             'NetworkInterfaceId': 'eni-12345678',
             'PrivateIpAddresses': [
                 {'PrivateDnsName': 'ip-098-76-54-321.ec2.internal',
                  'PrivateIpAddress': '098.76.54.321',
                  'Primary': True,
                  'Association':
                      {'PublicIp': '12.345.67.890',
                       'PublicDnsName': 'ec2-12-345-67-890.compute-1.amazonaws.com',
                       'IpOwnerId': 'amazon'}}],
             'PrivateDnsName': 'ip-098-76-54-321.ec2.internal',
             'Attachment':
                 {'Status': 'attached',
                  'DeviceIndex': 0,
                  'DeleteOnTermination': True,
                  'AttachmentId': 'eni-attach-12345678',
                  'AttachTime': datetime.datetime(2017, 10, 31, 12, 59, 25)},
             'Groups': [
                 {'GroupName': 'default',
                  'GroupId': 'sg-12345678'}],
             'Ipv6Addresses': [],
             'OwnerId': '123456789012',
             'PrivateIpAddress': '098.76.54.321',
             'SubnetId': 'subnet-12345678',
             'Association':
                {'PublicIp': '12.345.67.890',
                 'PublicDnsName': 'ec2-12-345-67-890.compute-1.amazonaws.com',
                 'IpOwnerId': 'amazon'}}],
         'SourceDestCheck': True,
         'Placement':
            {'Tenancy': 'default',
             'GroupName': '',
             'AvailabilityZone': 'us-east-1c'},
         'Hypervisor': 'xen',
         'BlockDeviceMappings': [
            {'DeviceName': '/dev/xvda',
             'Ebs':
                {'Status': 'attached',
                 'DeleteOnTermination': True,
                 'VolumeId': 'vol-01234567890000000',
                 'AttachTime': datetime.datetime(2017, 10, 31, 12, 59, 26)}}],
         'Architecture': 'x86_64',
         'RootDeviceType': 'ebs',
         'RootDeviceName': '/dev/xvda',
         'VirtualizationType': 'hvm',
         'Tags': [{'Value': 'test', 'Key': 'ansible'}, {'Value': 'aws_ec2', 'Key': 'Name'}],
         'AmiLaunchIndex': 0}],
    'ReservationId': 'r-01234567890000000',
    'Groups': [],
    'OwnerId': '123456789012'
}


@pytest.fixture()
def inventory():
    inventory = InventoryModule()
    inventory._options = {
        "aws_profile": "first_precedence",
        "aws_access_key": "test_access_key",
        "aws_secret_key": "test_secret_key",
        "aws_security_token": "test_security_token",
        "iam_role_arn": None,
        "use_contrib_script_compatible_ec2_tag_keys": False,
        "hostvars_prefix": "",
        "hostvars_suffix": "",
        "strict": True,
        "compose": {},
        "groups": {},
        "keyed_groups": [],
        "regions": ["us-east-1"],
        "filters": [],
        "include_filters": [],
        "exclude_filters": [],
        "hostnames": [],
        "strict_permissions": False,
        "allow_duplicated_hosts": False,
        "cache": False,
        "include_extra_api_calls": False,
        "use_contrib_script_compatible_sanitization": False,
    }
    inventory.inventory = MagicMock()
    return inventory


def test_compile_values(inventory):
    found_value = instances['Instances'][0]
    chain_of_keys = instance_data_filter_to_boto_attr['instance.group-id']
    for attr in chain_of_keys:
        found_value = inventory._compile_values(found_value, attr)
    assert found_value == "sg-12345678"


def test_get_boto_attr_chain(inventory):
    instance = instances['Instances'][0]
    assert inventory._get_boto_attr_chain('network-interface.addresses.private-ip-address', instance) == "098.76.54.321"


def test_boto3_conn(inventory):
    inventory._options = {"aws_profile": "first_precedence",
                          "aws_access_key": "test_access_key",
                          "aws_secret_key": "test_secret_key",
                          "aws_security_token": "test_security_token",
                          "iam_role_arn": None}
    loader = DataLoader()
    inventory._set_credentials(loader)
    with pytest.raises(AnsibleError) as error_message:
        for _connection, _region in inventory._boto3_conn(regions=['us-east-1']):
            assert "Insufficient credentials found" in error_message


def testget_all_hostnames_default(inventory):
    instance = instances['Instances'][0]
    assert inventory.get_all_hostnames(instance, hostnames=None) == ["ec2-12-345-67-890.compute-1.amazonaws.com", "ip-098-76-54-321.ec2.internal"]


def testget_all_hostnames(inventory):
    hostnames = ['ip-address', 'dns-name']
    instance = instances['Instances'][0]
    assert inventory.get_all_hostnames(instance, hostnames) == ["12.345.67.890", "ec2-12-345-67-890.compute-1.amazonaws.com"]


def testget_all_hostnames_dict(inventory):
    hostnames = [{'name': 'private-ip-address', 'separator': '_', 'prefix': 'tag:Name'}]
    instance = instances['Instances'][0]
    assert inventory.get_all_hostnames(instance, hostnames) == ["aws_ec2_098.76.54.321"]


def testget_all_hostnames_with_2_tags(inventory):
    hostnames = ['tag:ansible', 'tag:Name']
    instance = instances['Instances'][0]
    assert inventory.get_all_hostnames(instance, hostnames) == ["test", "aws_ec2"]


def test_get_preferred_hostname_default(inventory):
    instance = instances['Instances'][0]
    assert inventory._get_preferred_hostname(instance, hostnames=None) == "ec2-12-345-67-890.compute-1.amazonaws.com"


def test_get_preferred_hostname(inventory):
    hostnames = ['ip-address', 'dns-name']
    instance = instances['Instances'][0]
    assert inventory._get_preferred_hostname(instance, hostnames) == "12.345.67.890"


def test_get_preferred_hostname_dict(inventory):
    hostnames = [{'name': 'private-ip-address', 'separator': '_', 'prefix': 'tag:Name'}]
    instance = instances['Instances'][0]
    assert inventory._get_preferred_hostname(instance, hostnames) == "aws_ec2_098.76.54.321"


def test_get_preferred_hostname_with_2_tags(inventory):
    hostnames = ['tag:ansible', 'tag:Name']
    instance = instances['Instances'][0]
    assert inventory._get_preferred_hostname(instance, hostnames) == "test"


def test_set_credentials(inventory):
    inventory._options = {'aws_access_key': 'test_access_key',
                          'aws_secret_key': 'test_secret_key',
                          'aws_security_token': 'test_security_token',
                          'aws_profile': 'test_profile',
                          'iam_role_arn': 'arn:aws:iam::123456789012:role/test-role'}
    loader = DataLoader()
    inventory._set_credentials(loader)

    assert inventory.boto_profile == "test_profile"
    assert inventory.aws_access_key_id == "test_access_key"
    assert inventory.aws_secret_access_key == "test_secret_key"
    assert inventory.aws_security_token == "test_security_token"
    assert inventory.iam_role_arn == "arn:aws:iam::123456789012:role/test-role"


def test_insufficient_credentials(inventory):
    inventory._options = {
        'aws_access_key': None,
        'aws_secret_key': None,
        'aws_security_token': None,
        'aws_profile': None,
        'iam_role_arn': None
    }
    with pytest.raises(AnsibleError) as error_message:
        loader = DataLoader()
        inventory._set_credentials(loader)
        assert "Insufficient credentials found" in error_message


def test_verify_file_bad_config(inventory):
    assert inventory.verify_file('not_aws_config.yml') is False


def test_include_filters_with_no_filter(inventory):
    inventory._options = {
        'filters': {},
        'include_filters': [],
    }
    print(inventory.build_include_filters())
    assert inventory.build_include_filters() == [{}]


def test_include_filters_with_include_filters_only(inventory):
    inventory._options = {
        'filters': {},
        'include_filters': [{"foo": "bar"}],
    }
    assert inventory.build_include_filters() == [{"foo": "bar"}]


def test_include_filters_with_filter_and_include_filters(inventory):
    inventory._options = {
        'filters': {"from_filter": 1},
        'include_filters': [{"from_include_filter": "bar"}],
    }
    print(inventory.build_include_filters())
    assert inventory.build_include_filters() == [
        {"from_filter": 1},
        {"from_include_filter": "bar"}]


def test_add_host_empty_hostnames(inventory):
    hosts = [
        {
            "Placement": {
                "AvailabilityZone": "us-east-1a",
            },
            "PublicDnsName": "ip-10-85-0-4.ec2.internal"
        },
    ]
    inventory._add_hosts(hosts, "aws_ec2", [])
    inventory.inventory.add_host.assert_called_with("ip-10-85-0-4.ec2.internal", group="aws_ec2")


def test_add_host_with_hostnames_no_criteria(inventory):
    hosts = [{}]

    inventory._add_hosts(
        hosts, "aws_ec2", hostnames=["tag:Name", "private-dns-name", "dns-name"]
    )
    assert inventory.inventory.add_host.call_count == 0


def test_add_host_with_hostnames_and_one_criteria(inventory):
    hosts = [
        {
            "Placement": {
                "AvailabilityZone": "us-east-1a",
            },
            "PublicDnsName": "sample-host",
        }
    ]

    inventory._add_hosts(
        hosts, "aws_ec2", hostnames=["tag:Name", "private-dns-name", "dns-name"]
    )
    assert inventory.inventory.add_host.call_count == 1
    inventory.inventory.add_host.assert_called_with("sample-host", group="aws_ec2")


def test_add_host_with_hostnames_and_two_matching_criteria(inventory):
    hosts = [
        {
            "Placement": {
                "AvailabilityZone": "us-east-1a",
            },
            "PublicDnsName": "name-from-PublicDnsName",
            "Tags": [{"Value": "name-from-tag-Name", "Key": "Name"}],
        }
    ]

    inventory._add_hosts(
        hosts, "aws_ec2", hostnames=["tag:Name", "private-dns-name", "dns-name"]
    )
    assert inventory.inventory.add_host.call_count == 1
    inventory.inventory.add_host.assert_called_with(
        "name-from-tag-Name", group="aws_ec2"
    )


def test_add_host_with_hostnames_and_two_matching_criteria_and_allow_duplicated_hosts(
    inventory,
):
    hosts = [
        {
            "Placement": {
                "AvailabilityZone": "us-east-1a",
            },
            "PublicDnsName": "name-from-PublicDnsName",
            "Tags": [{"Value": "name-from-tag-Name", "Key": "Name"}],
        }
    ]

    inventory._add_hosts(
        hosts,
        "aws_ec2",
        hostnames=["tag:Name", "private-dns-name", "dns-name"],
        allow_duplicated_hosts=True,
    )
    assert inventory.inventory.add_host.call_count == 2
    inventory.inventory.add_host.assert_any_call(
        "name-from-PublicDnsName", group="aws_ec2"
    )
    inventory.inventory.add_host.assert_any_call("name-from-tag-Name", group="aws_ec2")


def test_sanitize_hostname(inventory):
    assert inventory._sanitize_hostname(1) == "1"
    assert inventory._sanitize_hostname("a:b") == "a_b"
    assert inventory._sanitize_hostname("a:/b") == "a__b"
    assert inventory._sanitize_hostname("example") == "example"


def test_sanitize_hostname_legacy(inventory):
    inventory._sanitize_group_name = (
        inventory._legacy_script_compatible_group_sanitization
    )
    assert inventory._sanitize_hostname("a:/b") == "a__b"


@pytest.mark.parametrize(
    "hostvars_prefix,hostvars_suffix,use_contrib_script_compatible_ec2_tag_keys,expectation",
    [
        (
            None,
            None,
            False,
            {
                "my_var": 1,
                "placement": {"availability_zone": "us-east-1a", "region": "us-east-1"},
                "tags": {"Name": "my-name"},
            },
        ),
        (
            "pre",
            "post",
            False,
            {
                "premy_varpost": 1,
                "preplacementpost": {
                    "availability_zone": "us-east-1a",
                    "region": "us-east-1",
                },
                "pretagspost": {"Name": "my-name"},
            },
        ),
        (
            None,
            None,
            True,
            {
                "my_var": 1,
                "ec2_tag_Name": "my-name",
                "placement": {"availability_zone": "us-east-1a", "region": "us-east-1"},
                "tags": {"Name": "my-name"},
            },
        ),
    ],
)
def test_prepare_host_vars(
    inventory,
    hostvars_prefix,
    hostvars_suffix,
    use_contrib_script_compatible_ec2_tag_keys,
    expectation,
):
    original_host_vars = {
        "my_var": 1,
        "placement": {"availability_zone": "us-east-1a"},
        "Tags": [{"Key": "Name", "Value": "my-name"}],
    }
    assert (
        inventory.prepare_host_vars(
            original_host_vars,
            hostvars_prefix,
            hostvars_suffix,
            use_contrib_script_compatible_ec2_tag_keys,
        )
        == expectation
    )


def test_iter_entry(inventory):
    hosts = [
        {
            "Placement": {
                "AvailabilityZone": "us-east-1a",
            },
            "PublicDnsName": "first-host://",
        },
        {
            "Placement": {
                "AvailabilityZone": "us-east-1a",
            },
            "PublicDnsName": "second-host",
            "Tags": [{"Key": "Name", "Value": "my-name"}],
        },
    ]

    entries = list(inventory.iter_entry(hosts, hostnames=[]))
    assert len(entries) == 2
    assert entries[0][0] == "first_host___"
    assert entries[1][0] == "second-host"
    assert entries[1][1]["tags"]["Name"] == "my-name"

    entries = list(
        inventory.iter_entry(
            hosts,
            hostnames=[],
            hostvars_prefix="a_",
            hostvars_suffix="_b",
            use_contrib_script_compatible_ec2_tag_keys=True,
        )
    )
    assert len(entries) == 2
    assert entries[0][0] == "first_host___"
    assert entries[1][1]["a_tags_b"]["Name"] == "my-name"


def test_query_empty(inventory):
    result = inventory._query("us-east-1", [], [], strict_permissions=True)
    assert result == {"aws_ec2": []}


instance_foobar = {"InstanceId": "foobar"}
instance_barfoo = {"InstanceId": "barfoo"}


def test_query_empty_include_only(inventory):
    inventory._get_instances_by_region = Mock(side_effect=[[instance_foobar]])
    result = inventory._query("us-east-1", [{"tag:Name": ["foobar"]}], [], strict_permissions=True)
    assert result == {"aws_ec2": [instance_foobar]}


def test_query_empty_include_ordered(inventory):
    inventory._get_instances_by_region = Mock(side_effect=[[instance_foobar], [instance_barfoo]])
    result = inventory._query("us-east-1", [{"tag:Name": ["foobar"]}, {"tag:Name": ["barfoo"]}], [], strict_permissions=True)
    assert result == {"aws_ec2": [instance_barfoo, instance_foobar]}
    inventory._get_instances_by_region.assert_called_with('us-east-1', [{'Name': 'tag:Name', 'Values': ['barfoo']}], True)


def test_query_empty_include_exclude(inventory):
    inventory._get_instances_by_region = Mock(side_effect=[[instance_foobar], [instance_foobar]])
    result = inventory._query("us-east-1", [{"tag:Name": ["foobar"]}], [{"tag:Name": ["foobar"]}], strict_permissions=True)
    assert result == {"aws_ec2": []}


def test_include_extra_api_calls_deprecated(inventory):
    inventory.display.deprecate = Mock()
    inventory._read_config_data = Mock()
    inventory._set_credentials = Mock()
    inventory._query = Mock(return_value=[])

    inventory.parse(inventory=[], loader=None, path=None)
    assert inventory.display.deprecate.call_count == 0

    inventory._options["include_extra_api_calls"] = True
    inventory.parse(inventory=[], loader=None, path=None)
    assert inventory.display.deprecate.call_count == 1

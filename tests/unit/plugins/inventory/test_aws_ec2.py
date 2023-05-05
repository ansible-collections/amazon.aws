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

import pytest
from unittest.mock import MagicMock, patch, call

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible.errors import AnsibleError
from ansible_collections.amazon.aws.plugins.inventory.aws_ec2 import (
    InventoryModule,
    _get_tag_hostname,
    _prepare_host_vars,
    _compile_values,
    _get_boto_attr_chain,
)


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


@pytest.mark.parametrize(
    "obj,expected",
    [
        (None, None),
        ({}, None),
        ({"GroupId": "test01"}, "test01"),
        ({"GroupId": ["test01"]}, "test01"),
        ({"GroupId": "test01"}, "test01"),
        ({"GroupId": ["test01", "test02"]}, ["test01", "test02"]),
        ([{"GroupId": ["test01", "test02"]}], ["test01", "test02"]),
        ([{"GroupId": ["test01"]}], "test01"),
        (
            [{"GroupId": ["test01", "test02"]}, {"GroupId": ["test03", "test04"]}],
            [["test01", "test02"], ["test03", "test04"]],
        ),
        (
            ({"GroupId": ["test01", "test02"]}, {"GroupId": ["test03", "test04"]}),
            [["test01", "test02"], ["test03", "test04"]],
        ),
        (({"GroupId": ["test01", "test02"]}, {}), ["test01", "test02"]),
    ],
)
def test_compile_values(obj, expected):
    assert _compile_values(obj, "GroupId") == expected


@pytest.mark.parametrize(
    "filter_name,expected",
    [
        ("ansible.aws.unexpected.file", "ansible.aws.unexpected.file"),
        ("instance.group-id", "sg-0123456789"),
        ("instance.group-name", "default"),
        ("owner-id", "id-012345678L"),
    ],
)
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._compile_values")
def test_get_boto_attr_chain(m_compile_values, filter_name, expected):
    m_compile_values.side_effect = lambda obj, attr: obj.get(attr)

    instance = {"SecurityGroups": {"GroupName": "default", "GroupId": "sg-0123456789"}, "OwnerId": "id-012345678L"}

    assert _get_boto_attr_chain(filter_name, instance) == expected


@pytest.mark.parametrize(
    "hostnames,expected",
    [
        ([], "test-instance.ansible.com"),
        (["private-dns-name"], "test-instance.localhost"),
        (["tag:os_version"], "RHEL"),
        (["tag:os_version", "dns-name"], "RHEL"),
        ([{"name": "Name", "prefix": "Phase"}], "dev_test-instance-01"),
        ([{"name": "Name", "prefix": "Phase", "separator": "-"}], "dev-test-instance-01"),
        ([{"name": "Name", "prefix": "OSVersion", "separator": "-"}], "test-instance-01"),
        ([{"name": "Name", "separator": "-"}], "test-instance-01"),
        ([{"name": "Name", "prefix": "Phase"}, "private-dns-name"], "dev_test-instance-01"),
        ([{"name": "Name", "prefix": "Phase"}, "tag:os_version"], "dev_test-instance-01"),
        (["private-dns-name", "dns-name"], "test-instance.localhost"),
        (["private-dns-name", {"name": "Name", "separator": "-"}], "test-instance.localhost"),
        (["private-dns-name", "tag:os_version"], "test-instance.localhost"),
        (["OSRelease"], None),
    ],
)
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_tag_hostname")
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_boto_attr_chain")
def test_inventory_get_preferred_hostname(m_get_boto_attr_chain, m_get_tag_hostname, inventory, hostnames, expected):
    instance = {
        "Name": "test-instance-01",
        "Phase": "dev",
        "tag:os_version": ["RHEL", "CoreOS"],
        "another_key": "another_value",
        "dns-name": "test-instance.ansible.com",
        "private-dns-name": "test-instance.localhost",
    }

    inventory._sanitize_hostname = MagicMock()
    inventory._sanitize_hostname.side_effect = lambda x: x

    m_get_boto_attr_chain.side_effect = lambda pref, instance: instance.get(pref)
    m_get_tag_hostname.side_effect = lambda pref, instance: instance.get(pref)

    assert expected == inventory._get_preferred_hostname(instance, hostnames)


def test_inventory_get_preferred_hostname_failure(inventory):
    instance = {}
    hostnames = [{"value": "saome_value"}]

    inventory._sanitize_hostname = MagicMock()
    inventory._sanitize_hostname.side_effect = lambda x: x

    with pytest.raises(AnsibleError) as err:
        inventory._get_preferred_hostname(instance, hostnames)
        assert "A 'name' key must be defined in a hostnames dictionary." in err


@pytest.mark.parametrize("base_verify_file_return", [True, False])
@pytest.mark.parametrize(
    "filename,result",
    [
        ("inventory_aws_ec2.yml", True),
        ("inventory_aws_ec2.yaml", True),
        ("inventory_aws_EC2.yaml", False),
        ("inventory_Aws_ec2.yaml", False),
        ("aws_ec2_inventory.yml", False),
        ("aws_ec2.yml_inventory", False),
        ("aws_ec2.yml", True),
        ("aws_ec2.yaml", True),
    ],
)
@patch("ansible.plugins.inventory.BaseInventoryPlugin.verify_file")
def test_inventory_verify_file(m_base_verify_file, inventory, base_verify_file_return, filename, result):
    m_base_verify_file.return_value = base_verify_file_return
    if not base_verify_file_return:
        assert not inventory.verify_file(filename)
    else:
        assert result == inventory.verify_file(filename)


@pytest.mark.parametrize(
    "preference,instance,expected",
    [
        ("tag:os_provider", {"Tags": []}, []),
        ("tag:os_provider", {}, []),
        ("tag:os_provider", {"Tags": [{"Key": "os_provider", "Value": "RedHat"}]}, ["RedHat"]),
        ("tag:OS_Provider", {"Tags": [{"Key": "os_provider", "Value": "RedHat"}]}, []),
        ("tag:tag:os_provider", {"Tags": [{"Key": "os_provider", "Value": "RedHat"}]}, []),
        ("tag:os_provider=RedHat", {"Tags": [{"Key": "os_provider", "Value": "RedHat"}]}, ["os_provider_RedHat"]),
        ("tag:os_provider=CoreOS", {"Tags": [{"Key": "os_provider", "Value": "RedHat"}]}, []),
        (
            "tag:os_provider=RedHat,os_release=7",
            {"Tags": [{"Key": "os_provider", "Value": "RedHat"}, {"Key": "os_release", "Value": "8"}]},
            ["os_provider_RedHat"],
        ),
        (
            "tag:os_provider=RedHat,os_release=7",
            {"Tags": [{"Key": "os_provider", "Value": "RedHat"}, {"Key": "os_release", "Value": "7"}]},
            ["os_provider_RedHat", "os_release_7"],
        ),
        (
            "tag:os_provider,os_release",
            {"Tags": [{"Key": "os_provider", "Value": "RedHat"}, {"Key": "os_release", "Value": "7"}]},
            ["RedHat", "7"],
        ),
        (
            "tag:os_provider=RedHat,os_release",
            {"Tags": [{"Key": "os_provider", "Value": "RedHat"}, {"Key": "os_release", "Value": "7"}]},
            ["os_provider_RedHat", "7"],
        ),
    ],
)
def test_get_tag_hostname(preference, instance, expected):
    assert expected == _get_tag_hostname(preference, instance)


@pytest.mark.parametrize(
    "_options, expected",
    [
        ({"filters": {}, "include_filters": []}, [{}]),
        ({"filters": {}, "include_filters": [{"foo": "bar"}]}, [{"foo": "bar"}]),
        (
            {
                "filters": {"from_filter": 1},
                "include_filters": [{"from_include_filter": "bar"}],
            },
            [{"from_filter": 1}, {"from_include_filter": "bar"}],
        ),
    ],
)
def test_inventory_build_include_filters(inventory, _options, expected):
    inventory._options = _options
    assert inventory.build_include_filters() == expected


@pytest.mark.parametrize("hostname,expected", [(1, "1"), ("a:b", "a_b"), ("a:/b", "a__b"), ("example", "example")])
def test_sanitize_hostname(inventory, hostname, expected):
    assert inventory._sanitize_hostname(hostname) == expected


def test_sanitize_hostname_legacy(inventory):
    inventory._sanitize_group_name = inventory._legacy_script_compatible_group_sanitization
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
        _prepare_host_vars(
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


@pytest.mark.parametrize(
    "include_filters,exclude_filters,instances_by_region,instances",
    [
        ([], [], [], []),
        (
            [4, 1, 2],
            [],
            [
                [{"InstanceId": 4, "name": "instance-4"}],
                [{"InstanceId": 1, "name": "instance-1"}],
                [{"InstanceId": 2, "name": "instance-2"}],
            ],
            [
                {"InstanceId": 1, "name": "instance-1"},
                {"InstanceId": 2, "name": "instance-2"},
                {"InstanceId": 4, "name": "instance-4"},
            ],
        ),
        (
            [],
            [4, 1, 2],
            [
                [{"InstanceId": 4, "name": "instance-4"}],
                [{"InstanceId": 1, "name": "instance-1"}],
                [{"InstanceId": 2, "name": "instance-2"}],
            ],
            [],
        ),
        (
            [1, 2],
            [4],
            [
                [{"InstanceId": 4, "name": "instance-4"}],
                [{"InstanceId": 1, "name": "instance-1"}],
                [{"InstanceId": 2, "name": "instance-2"}],
            ],
            [{"InstanceId": 1, "name": "instance-1"}, {"InstanceId": 2, "name": "instance-2"}],
        ),
        (
            [1, 2],
            [1],
            [
                [{"InstanceId": 1, "name": "instance-1"}],
                [{"InstanceId": 1, "name": "instance-1"}],
                [{"InstanceId": 2, "name": "instance-2"}],
            ],
            [{"InstanceId": 2, "name": "instance-2"}],
        ),
    ],
)
def test_inventory_query(inventory, include_filters, exclude_filters, instances_by_region, instances):
    inventory._get_instances_by_region = MagicMock()
    inventory._get_instances_by_region.side_effect = instances_by_region

    regions = ["us-east-1", "us-east-2"]
    strict = False

    params = {
        "regions": regions,
        "strict_permissions": strict,
        "include_filters": [],
        "exclude_filters": [],
        "use_ssm_inventory": False,
    }

    for u in include_filters:
        params["include_filters"].append({"Name": f"in_filters_{int(u)}", "Values": [u]})

    for u in exclude_filters:
        params["exclude_filters"].append({"Name": f"ex_filters_{int(u)}", "Values": [u]})

    assert inventory._query(**params) == {"aws_ec2": instances}
    if not instances_by_region:
        inventory._get_instances_by_region.assert_not_called()


@pytest.mark.parametrize(
    "filters",
    [
        [],
        [{"Name": "provider", "Values": "sample"}, {"Name": "instance-state-name", "Values": ["active"]}],
        [
            {"Name": "tags", "Values": "one_tag"},
        ],
    ],
)
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._describe_ec2_instances")
def test_inventory_get_instances_by_region(m_describe_ec2_instances, inventory, filters):
    boto3_conn = [(MagicMock(), "us-east-1"), (MagicMock(), "us-east-2")]

    inventory.all_clients = MagicMock()
    inventory.all_clients.return_value = boto3_conn

    m_describe_ec2_instances.side_effect = [
        {
            "Reservations": [
                {
                    "OwnerId": "owner01",
                    "RequesterId": "requester01",
                    "ReservationId": "id-0123",
                    "Instances": [
                        {"name": "id-1-0", "os": "RedHat"},
                        {"name": "id-1-1", "os": "CoreOS"},
                        {"name": "id-1-2", "os": "Fedora"},
                    ],
                },
                {
                    "OwnerId": "owner01",
                    "ReservationId": "id-0456",
                    "Instances": [{"name": "id-2-0", "phase": "uat"}, {"name": "id-2-1", "phase": "prod"}],
                },
            ]
        },
        {
            "Reservations": [
                {
                    "OwnerId": "owner02",
                    "ReservationId": "id-0789",
                    "Instances": [
                        {"name": "id012345789", "tags": {"phase": "units"}},
                    ],
                }
            ],
            "Metadata": {"Status": "active"},
        },
    ]

    expected = [
        {
            "name": "id-1-0",
            "os": "RedHat",
            "OwnerId": "owner01",
            "RequesterId": "requester01",
            "ReservationId": "id-0123",
        },
        {
            "name": "id-1-1",
            "os": "CoreOS",
            "OwnerId": "owner01",
            "RequesterId": "requester01",
            "ReservationId": "id-0123",
        },
        {
            "name": "id-1-2",
            "os": "Fedora",
            "OwnerId": "owner01",
            "RequesterId": "requester01",
            "ReservationId": "id-0123",
        },
        {"name": "id-2-0", "phase": "uat", "OwnerId": "owner01", "ReservationId": "id-0456", "RequesterId": ""},
        {"name": "id-2-1", "phase": "prod", "OwnerId": "owner01", "ReservationId": "id-0456", "RequesterId": ""},
        {
            "name": "id012345789",
            "tags": {"phase": "units"},
            "OwnerId": "owner02",
            "ReservationId": "id-0789",
            "RequesterId": "",
        },
    ]

    default_filter = {"Name": "instance-state-name", "Values": ["running", "pending", "stopping", "stopped"]}
    regions = ["us-east-2", "us-east-4"]

    assert inventory._get_instances_by_region(regions, filters, False) == expected
    inventory.all_clients.assert_called_with("ec2")

    if any((f["Name"] == "instance-state-name" for f in filters)):
        filters.append(default_filter)

    m_describe_ec2_instances.assert_has_calls([call(conn, filters) for conn, region in boto3_conn], any_order=True)


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize(
    "error",
    [
        botocore.exceptions.ClientError(
            {"Error": {"Code": 1, "Message": "Something went wrong"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
            "some_botocore_client_error",
        ),
        botocore.exceptions.ClientError(
            {
                "Error": {"Code": "UnauthorizedOperation", "Message": "Something went wrong"},
                "ResponseMetadata": {"HTTPStatusCode": 403},
            },
            "some_botocore_client_error",
        ),
        botocore.exceptions.PaginationError(message="some pagination error"),
    ],
)
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._describe_ec2_instances")
def test_inventory_get_instances_by_region_failures(m_describe_ec2_instances, inventory, strict, error):
    inventory.all_clients = MagicMock()
    inventory.all_clients.return_value = [(MagicMock(), "us-west-2")]
    inventory.fail_aws = MagicMock()
    inventory.fail_aws.side_effect = SystemExit(1)

    m_describe_ec2_instances.side_effect = error
    regions = ["us-east-2", "us-east-4"]

    if (
        isinstance(error, botocore.exceptions.ClientError)
        and error.response["ResponseMetadata"]["HTTPStatusCode"] == 403
        and not strict
    ):
        assert inventory._get_instances_by_region(regions, [], strict) == []
    else:
        with pytest.raises(SystemExit):
            inventory._get_instances_by_region(regions, [], strict)


@pytest.mark.parametrize(
    "hostnames,expected",
    [
        ([], ["test-instance.ansible.com", "test-instance.localhost"]),
        (["private-dns-name"], ["test-instance.localhost"]),
        (["tag:os_version"], ["RHEL", "CoreOS"]),
        (["tag:os_version", "dns-name"], ["RHEL", "CoreOS", "test-instance.ansible.com"]),
        ([{"name": "Name", "prefix": "Phase"}], ["dev_test-instance-01"]),
        ([{"name": "Name", "prefix": "Phase", "separator": "-"}], ["dev-test-instance-01"]),
        ([{"name": "Name", "prefix": "OSVersion", "separator": "-"}], ["test-instance-01"]),
        ([{"name": "Name", "separator": "-"}], ["test-instance-01"]),
        (
            [{"name": "Name", "prefix": "Phase"}, "private-dns-name"],
            ["dev_test-instance-01", "test-instance.localhost"],
        ),
        ([{"name": "Name", "prefix": "Phase"}, "tag:os_version"], ["dev_test-instance-01", "RHEL", "CoreOS"]),
        (["private-dns-name", {"name": "Name", "separator": "-"}], ["test-instance.localhost", "test-instance-01"]),
        (["OSRelease"], []),
    ],
)
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_tag_hostname")
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_boto_attr_chain")
def test_inventory_get_all_hostnames(m_get_boto_attr_chain, m_get_tag_hostname, inventory, hostnames, expected):
    instance = {
        "Name": "test-instance-01",
        "Phase": "dev",
        "tag:os_version": ["RHEL", "CoreOS"],
        "another_key": "another_value",
        "dns-name": "test-instance.ansible.com",
        "private-dns-name": "test-instance.localhost",
    }

    inventory._sanitize_hostname = MagicMock()
    inventory._sanitize_hostname.side_effect = lambda x: x

    m_get_boto_attr_chain.side_effect = lambda pref, instance: instance.get(pref)
    m_get_tag_hostname.side_effect = lambda pref, instance: instance.get(pref)

    assert expected == inventory._get_all_hostnames(instance, hostnames)


def test_inventory_get_all_hostnames_failure(inventory):
    instance = {}
    hostnames = [{"value": "some_value"}]

    with pytest.raises(AnsibleError) as err:
        inventory._get_all_hostnames(instance, hostnames)
        assert "A 'name' key must be defined in a hostnames dictionary." in err


@patch("ansible_collections.amazon.aws.plugins.inventory.aws_ec2._get_ssm_information")
def test_inventory__add_ssm_information(m_get_ssm_information, inventory):
    instances = [
        {"InstanceId": "i-001", "Name": "first-instance"},
        {"InstanceId": "i-002", "Name": "another-instance"},
    ]

    result = {
        "StatusCode": 200,
        "Entities": [
            {"Id": "i-001", "Data": {}},
            {
                "Id": "i-002",
                "Data": {
                    "AWS:InstanceInformation": {
                        "Content": [{"os_type": "Linux", "os_name": "Fedora", "os_version": 37}]
                    }
                },
            },
        ],
    }
    m_get_ssm_information.return_value = result

    connection = MagicMock()

    expected = [
        {"InstanceId": "i-001", "Name": "first-instance"},
        {
            "InstanceId": "i-002",
            "Name": "another-instance",
            "SsmInventory": {"os_type": "Linux", "os_name": "Fedora", "os_version": 37},
        },
    ]

    inventory._add_ssm_information(connection, instances)
    assert expected == instances

    filters = [{"Key": "AWS:InstanceInformation.InstanceId", "Values": [x["InstanceId"] for x in instances]}]
    m_get_ssm_information.assert_called_once_with(connection, filters)

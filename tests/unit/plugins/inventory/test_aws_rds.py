# -*- coding: utf-8 -*-

# Copyright 2022 Aubin Bikouo <@abikouo>
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

import copy
import random
import string
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible.errors import AnsibleError

from ansible_collections.amazon.aws.plugins.inventory.aws_rds import InventoryModule
from ansible_collections.amazon.aws.plugins.inventory.aws_rds import _add_tags_for_rds_hosts
from ansible_collections.amazon.aws.plugins.inventory.aws_rds import _describe_db_clusters
from ansible_collections.amazon.aws.plugins.inventory.aws_rds import _describe_db_instances
from ansible_collections.amazon.aws.plugins.inventory.aws_rds import _find_hosts_with_valid_statuses
from ansible_collections.amazon.aws.plugins.inventory.aws_rds import _get_rds_hostname
from ansible_collections.amazon.aws.plugins.inventory.aws_rds import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_aws_rds.py requires the python modules 'boto3' and 'botocore'")


def make_clienterror_exception(code="AccessDenied"):
    return botocore.exceptions.ClientError(
        {
            "Error": {"Code": code, "Message": "User is not authorized to perform: xxx on resource: user yyyy"},
            "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
        },
        "getXXX",
    )


@pytest.fixture(name="inventory")
def fixture_inventory():
    inventory = InventoryModule()
    inventory.inventory = MagicMock()
    inventory._populate_host_vars = MagicMock()

    inventory.all_clients = MagicMock()
    inventory.get_option = MagicMock()

    inventory._set_composite_vars = MagicMock()
    inventory._add_host_to_composed_groups = MagicMock()
    inventory._add_host_to_keyed_groups = MagicMock()
    inventory._read_config_data = MagicMock()
    inventory._set_credentials = MagicMock()

    inventory.get_cache_key = MagicMock()

    inventory._cache = {}
    return inventory


@pytest.fixture(name="connection")
def fixture_connection():
    conn = MagicMock()
    return conn


@pytest.mark.parametrize(
    "suffix,result",
    [
        ("aws_rds.yml", True),
        ("aws_rds.yaml", True),
        ("aws_RDS.yml", False),
        ("AWS_rds.yaml", False),
    ],
)
def test_inventory_verify_file_suffix(inventory, suffix, result, tmp_path):
    test_dir = tmp_path / "test_aws_rds"
    test_dir.mkdir()
    inventory_file = "inventory" + suffix
    inventory_file = test_dir / inventory_file
    inventory_file.write_text("my inventory")
    assert result == inventory.verify_file(str(inventory_file))


def test_inventory_verify_file_with_missing_file(inventory):
    inventory_file = "this_file_does_not_exist_aws_rds.yml"
    assert not inventory.verify_file(inventory_file)


def generate_random_string(with_digits=True, with_punctuation=True, length=16):
    data = string.ascii_letters
    if with_digits:
        data += string.digits
    if with_punctuation:
        data += string.punctuation
    return "".join([random.choice(data) for i in range(length)])


@pytest.mark.parametrize(
    "hosts,statuses,expected",
    [
        (
            [
                {"host": "host1", "DBInstanceStatus": "Available", "Status": "active"},
                {"host": "host2", "DBInstanceStatus": "Creating", "Status": "active"},
                {"host": "host3", "DBInstanceStatus": "Stopped", "Status": "active"},
                {"host": "host4", "DBInstanceStatus": "Configuring", "Status": "active"},
            ],
            ["Available"],
            [{"host": "host1", "DBInstanceStatus": "Available", "Status": "active"}],
        ),
        (
            [
                {"host": "host1", "DBInstanceStatus": "Available", "Status": "active"},
                {"host": "host2", "DBInstanceStatus": "Creating", "Status": "active"},
                {"host": "host3", "DBInstanceStatus": "Stopped", "Status": "active"},
                {"host": "host4", "DBInstanceStatus": "Configuring", "Status": "active"},
            ],
            ["all"],
            [
                {"host": "host1", "DBInstanceStatus": "Available", "Status": "active"},
                {"host": "host2", "DBInstanceStatus": "Creating", "Status": "active"},
                {"host": "host3", "DBInstanceStatus": "Stopped", "Status": "active"},
                {"host": "host4", "DBInstanceStatus": "Configuring", "Status": "active"},
            ],
        ),
        (
            [
                {"host": "host1", "DBInstanceStatus": "Available", "Status": "active"},
                {"host": "host2", "DBInstanceStatus": "Creating", "Status": "Available"},
                {"host": "host3", "DBInstanceStatus": "Stopped", "Status": "active"},
                {"host": "host4", "DBInstanceStatus": "Configuring", "Status": "active"},
            ],
            ["Available"],
            [
                {"host": "host1", "DBInstanceStatus": "Available", "Status": "active"},
                {"host": "host2", "DBInstanceStatus": "Creating", "Status": "Available"},
            ],
        ),
    ],
)
def test_find_hosts_with_valid_statuses(hosts, statuses, expected):
    assert expected == _find_hosts_with_valid_statuses(hosts, statuses)


@pytest.mark.parametrize(
    "host,expected",
    [
        ({"DBClusterIdentifier": "my_cluster_id"}, "my_cluster_id"),
        ({"DBClusterIdentifier": "my_cluster_id", "DBInstanceIdentifier": "my_instance_id"}, "my_instance_id"),
    ],
)
def test_get_rds_hostname(host, expected):
    assert expected == _get_rds_hostname(host)


@pytest.mark.parametrize("hosts", ["", "host1", "host2,host3", "host2,host3,host1"])
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_rds._get_rds_hostname")
def test_inventory_format_inventory(m_get_rds_hostname, inventory, hosts):
    hosts_vars = {
        "host1": {"var10": "value10"},
        "host2": {"var20": "value20", "var21": "value21"},
        "host3": {"var30": "value30", "var31": "value31", "var32": "value32"},
    }

    m_get_rds_hostname.side_effect = lambda h: h["name"]

    class _inventory_host(object):
        def __init__(self, name, host_vars):
            self.name = name
            self.vars = host_vars

    inventory.inventory = MagicMock()
    inventory.inventory.get_host.side_effect = lambda x: _inventory_host(name=x, host_vars=hosts_vars.get(x))

    hosts = [{"name": x} for x in hosts.split(",") if x]
    expected = {
        "_meta": {"hostvars": {x["name"]: hosts_vars.get(x["name"]) for x in hosts}},
        "aws_rds": {"hosts": [x["name"] for x in hosts]},
    }

    assert expected == inventory._format_inventory(hosts)
    if hosts == []:
        m_get_rds_hostname.assert_not_called()


@pytest.mark.parametrize("length", range(0, 10, 2))
def test_inventory_populate(inventory, length):
    group = "aws_rds"
    hosts = [f"host_{int(i)}" for i in range(length)]

    inventory._add_hosts = MagicMock()
    inventory._populate(hosts=hosts)

    inventory.inventory.add_group.assert_called_with("aws_rds")

    if len(hosts) == 0:
        inventory.inventory._add_hosts.assert_not_called()
        inventory.inventory.add_child.assert_not_called()
    else:
        inventory._add_hosts.assert_called_with(hosts=hosts, group=group)
        inventory.inventory.add_child.assert_called_with("all", group)


def test_inventory_populate_from_source(inventory):
    source_data = {
        "_meta": {
            "hostvars": {
                "host_1_0": {"var10": "value10"},
                "host_2": {"var2": "value2"},
                "host_3": {"var3": ["value30", "value31", "value32"]},
            }
        },
        "all": {"hosts": ["host_1_0", "host_1_1", "host_2", "host_3"]},
        "aws_host_1": {"hosts": ["host_1_0", "host_1_1"]},
        "aws_host_2": {"hosts": ["host_2"]},
        "aws_host_3": {"hosts": ["host_3"]},
    }

    inventory._populate_from_source(source_data)
    inventory.inventory.add_group.assert_has_calls(
        [
            call("aws_host_1"),
            call("aws_host_2"),
            call("aws_host_3"),
        ],
        any_order=True,
    )
    inventory.inventory.add_child.assert_has_calls(
        [
            call("all", "aws_host_1"),
            call("all", "aws_host_2"),
            call("all", "aws_host_3"),
        ],
        any_order=True,
    )

    inventory._populate_host_vars.assert_has_calls(
        [
            call(["host_1_0"], {"var10": "value10"}, "aws_host_1"),
            call(["host_1_1"], {}, "aws_host_1"),
            call(["host_2"], {"var2": "value2"}, "aws_host_2"),
            call(["host_3"], {"var3": ["value30", "value31", "value32"]}, "aws_host_3"),
        ],
        any_order=True,
    )


@pytest.mark.parametrize("strict", [True, False])
def test_add_tags_for_rds_hosts_with_no_hosts(connection, strict):
    hosts = []

    _add_tags_for_rds_hosts(connection, hosts, strict)
    connection.list_tags_for_resource.assert_not_called()


def test_add_tags_for_rds_hosts_with_hosts(connection):
    hosts = [
        {"DBInstanceArn": "dbarn1"},
        {"DBInstanceArn": "dbarn2"},
        {"DBClusterArn": "clusterarn1"},
    ]

    rds_hosts_tags = {
        "dbarn1": {"TagList": ["tag1=dbarn1", "phase=units"]},
        "dbarn2": {"TagList": ["tag2=dbarn2", "collection=amazon.aws"]},
        "clusterarn1": {"TagList": ["tag1=clusterarn1", "tool=ansible-test"]},
    }
    connection.list_tags_for_resource.side_effect = lambda **kwargs: rds_hosts_tags.get(kwargs.get("ResourceName"))

    _add_tags_for_rds_hosts(connection, hosts, strict=False)

    assert hosts == [
        {"DBInstanceArn": "dbarn1", "Tags": ["tag1=dbarn1", "phase=units"]},
        {"DBInstanceArn": "dbarn2", "Tags": ["tag2=dbarn2", "collection=amazon.aws"]},
        {"DBClusterArn": "clusterarn1", "Tags": ["tag1=clusterarn1", "tool=ansible-test"]},
    ]


def test_add_tags_for_rds_hosts_with_failure_not_strict(connection):
    hosts = [{"DBInstanceArn": "dbarn1"}]

    connection.list_tags_for_resource.side_effect = make_clienterror_exception()

    _add_tags_for_rds_hosts(connection, hosts, strict=False)

    assert hosts == [
        {"DBInstanceArn": "dbarn1", "Tags": []},
    ]


def test_add_tags_for_rds_hosts_with_failure_strict(connection):
    hosts = [{"DBInstanceArn": "dbarn1"}]

    connection.list_tags_for_resource.side_effect = make_clienterror_exception()

    with pytest.raises(botocore.exceptions.ClientError):
        _add_tags_for_rds_hosts(connection, hosts, strict=True)


ADD_TAGS_FOR_RDS_HOSTS = "ansible_collections.amazon.aws.plugins.inventory.aws_rds._add_tags_for_rds_hosts"


@patch(ADD_TAGS_FOR_RDS_HOSTS)
def test_describe_db_clusters(m_add_tags_for_rds_hosts, connection):
    db_cluster = {
        "DatabaseName": "my_sample_db",
        "DBClusterIdentifier": "db_id_01",
        "Status": "Stopped",
        "DbClusterResourceId": "cluster_resource_id",
        "DBClusterArn": "arn:xxx:xxxx",
        "DeletionProtection": True,
    }

    connection.describe_db_clusters.return_value = {"DBClusters": [db_cluster]}

    filters = generate_random_string(with_punctuation=False)
    strict = False

    result = _describe_db_clusters(connection=connection, filters=filters, strict=strict)

    assert result == [db_cluster]

    m_add_tags_for_rds_hosts.assert_called_with(connection, result, strict)


@pytest.mark.parametrize("strict", [True, False])
@patch(ADD_TAGS_FOR_RDS_HOSTS)
def test_describe_db_clusters_with_access_denied(m_add_tags_for_rds_hosts, connection, strict):
    connection.describe_db_clusters.side_effect = make_clienterror_exception()

    filters = generate_random_string(with_punctuation=False)

    if strict:
        with pytest.raises(AnsibleError):
            _describe_db_clusters(connection=connection, filters=filters, strict=strict)
    else:
        assert _describe_db_clusters(connection=connection, filters=filters, strict=strict) == []

    m_add_tags_for_rds_hosts.assert_not_called()


@patch(ADD_TAGS_FOR_RDS_HOSTS)
def test_describe_db_clusters_with_client_error(m_add_tags_for_rds_hosts, connection):
    connection.describe_db_clusters.side_effect = make_clienterror_exception(code="Unknown")

    filters = generate_random_string(with_punctuation=False)
    with pytest.raises(AnsibleError):
        _describe_db_clusters(connection=connection, filters=filters, strict=False)

    m_add_tags_for_rds_hosts.assert_not_called()


@patch(ADD_TAGS_FOR_RDS_HOSTS)
def test_describe_db_instances(m_add_tags_for_rds_hosts, connection):
    db_instance = {
        "DBInstanceIdentifier": "db_id_01",
        "Status": "Stopped",
        "DBName": "my_sample_db_01",
        "DBClusterIdentifier": "db_cluster_001",
        "DBInstanceArn": "arn:db:xxxx:xxxx:xxxx",
        "Engine": "mysql",
    }

    conn_paginator = MagicMock()
    paginate = MagicMock()

    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate

    paginate.build_full_result.return_value = {"DBInstances": [db_instance]}

    filters = generate_random_string(with_punctuation=False)
    strict = False

    result = _describe_db_instances(connection=connection, filters=filters, strict=strict)

    assert result == [db_instance]

    m_add_tags_for_rds_hosts.assert_called_with(connection, result, strict)
    connection.get_paginator.assert_called_with("describe_db_instances")
    conn_paginator.paginate.assert_called_with(Filters=filters)


DESCRIBE_DB_INSTANCES = "ansible_collections.amazon.aws.plugins.inventory.aws_rds._describe_db_instances"
DESCRIBE_DB_CLUSTERS = "ansible_collections.amazon.aws.plugins.inventory.aws_rds._describe_db_clusters"
FIND_HOSTS_WITH_VALID_STATUSES = (
    "ansible_collections.amazon.aws.plugins.inventory.aws_rds._find_hosts_with_valid_statuses"
)


@pytest.mark.parametrize("gather_clusters", [True, False])
@pytest.mark.parametrize("regions", range(1, 5))
@patch(DESCRIBE_DB_INSTANCES)
@patch(DESCRIBE_DB_CLUSTERS)
@patch(FIND_HOSTS_WITH_VALID_STATUSES)
def test_inventory_get_all_db_hosts(
    m_find_hosts, m_describe_db_clusters, m_describe_db_instances, inventory, gather_clusters, regions
):
    params = {
        "gather_clusters": gather_clusters,
        "regions": [f"us-east-{int(i)}" for i in range(regions)],
        "instance_filters": generate_random_string(),
        "cluster_filters": generate_random_string(),
        "strict": random.choice((True, False)),
        "statuses": [random.choice(["Available", "Stopped", "Running", "Creating"]) for i in range(3)],
    }

    connections = [MagicMock() for i in range(regions)]

    inventory.all_clients.return_value = [(connections[i], f"us-east-{int(i)}") for i in range(regions)]

    ids = list(reversed(range(regions)))
    db_instances = [{"DBInstanceIdentifier": f"db_00{int(i)}"} for i in ids]
    db_clusters = [{"DBClusterIdentifier": f"cluster_00{int(i)}"} for i in ids]

    m_describe_db_instances.side_effect = [[i] for i in db_instances]
    m_describe_db_clusters.side_effect = [[i] for i in db_clusters]

    result = list(sorted(db_instances, key=lambda x: x["DBInstanceIdentifier"]))
    if gather_clusters:
        result += list(sorted(db_clusters, key=lambda x: x["DBClusterIdentifier"]))

    m_find_hosts.return_value = result

    assert result == inventory._get_all_db_hosts(**params)
    inventory.all_clients.assert_called_with("rds")
    m_describe_db_instances.assert_has_calls(
        [call(connections[i], params["instance_filters"], strict=params["strict"]) for i in range(regions)]
    )

    if gather_clusters:
        m_describe_db_clusters.assert_has_calls(
            [call(connections[i], params["cluster_filters"], strict=params["strict"]) for i in range(regions)]
        )

    m_find_hosts.assert_called_with(result, params["statuses"])


@pytest.mark.parametrize("hostvars_prefix", [True])
@pytest.mark.parametrize("hostvars_suffix", [True])
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_rds._get_rds_hostname")
def test_inventory_add_hosts(m_get_rds_hostname, inventory, hostvars_prefix, hostvars_suffix):
    _options = {
        "strict": random.choice((False, True)),
        "compose": random.choice((False, True)),
        "keyed_groups": "keyed_group_test_inventory_add_hosts",
        "groups": ["all", "test_inventory_add_hosts"],
    }

    if hostvars_prefix:
        _options["hostvars_prefix"] = f"prefix_{generate_random_string(length=8, with_punctuation=False)}"
    if hostvars_suffix:
        _options["hostvars_suffix"] = f"suffix_{generate_random_string(length=8, with_punctuation=False)}"

    def _get_option_side_effect(x):
        return _options.get(x)

    inventory.get_option.side_effect = _get_option_side_effect

    m_get_rds_hostname.side_effect = lambda h: (
        h["DBInstanceIdentifier"] if "DBInstanceIdentifier" in h else h["DBClusterIdentifier"]
    )

    hosts = [
        {
            "DBInstanceIdentifier": "db_i_001",
            "Tags": [{"Key": "Name", "Value": "db_001"}, {"Key": "RunningEngine", "Value": "mysql"}],
            "availability_zone": "us-east-1a",
        },
        {
            "DBInstanceIdentifier": "db_i_002",
            "Tags": [{"Key": "ClusterName", "Value": "test_cluster"}, {"Key": "RunningOS", "Value": "CoreOS"}],
        },
        {
            "DBClusterIdentifier": "test_cluster",
            "Tags": [{"Key": "CluserVersionOrigin", "Value": "2.0"}, {"Key": "Provider", "Value": "RedHat"}],
        },
        {
            "DBClusterIdentifier": "another_cluster",
            "Tags": [{"Key": "TestingPurpose", "Value": "Ansible"}],
            "availability_zones": ["us-west-1a", "us-east-1b"],
        },
    ]

    group = f"test_add_hosts_group_{generate_random_string(length=10, with_punctuation=False)}"
    inventory._add_hosts(hosts, group)

    m_get_rds_hostname.assert_has_calls([call(h) for h in hosts], any_order=True)

    hosts_names = ["db_i_001", "db_i_002", "test_cluster", "another_cluster"]
    inventory.inventory.add_host.assert_has_calls([call(name, group=group) for name in hosts_names], any_order=True)

    camel_hosts = [
        {
            "db_instance_identifier": "db_i_001",
            "tags": {"Name": "db_001", "RunningEngine": "mysql"},
            "availability_zone": "us-east-1a",
            "region": "us-east-1",
        },
        {"db_instance_identifier": "db_i_002", "tags": {"ClusterName": "test_cluster", "RunningOS": "CoreOS"}},
        {"db_cluster_identifier": "test_cluster", "tags": {"CluserVersionOrigin": "2.0", "Provider": "RedHat"}},
        {
            "db_cluster_identifier": "another_cluster",
            "tags": {"TestingPurpose": "Ansible"},
            "availability_zones": ["us-west-1a", "us-east-1b"],
            "region": "us-west-1",
        },
    ]

    set_variable_calls = []
    for i in range(len(camel_hosts)):
        for var, value in camel_hosts[i].items():
            if hostvars_prefix:
                var = _options["hostvars_prefix"] + var
            if hostvars_suffix:
                var += _options["hostvars_suffix"]
            set_variable_calls.append(call(hosts_names[i], var, value))

    inventory.inventory.set_variable.assert_has_calls(set_variable_calls, any_order=True)

    if hostvars_prefix or hostvars_suffix:
        tmp = []
        for host in camel_hosts:
            new_host = copy.deepcopy(host)
            for key, value in host.items():
                new_key = key
                if hostvars_prefix:
                    new_key = _options["hostvars_prefix"] + new_key
                if hostvars_suffix:
                    new_key += _options["hostvars_suffix"]
                new_host[new_key] = value
            tmp.append(new_host)
        camel_hosts = tmp

    inventory._set_composite_vars.assert_has_calls(
        [
            call(_options["compose"], camel_hosts[i], hosts_names[i], strict=_options["strict"])
            for i in range(len(camel_hosts))
        ],
        any_order=True,
    )
    inventory._add_host_to_composed_groups.assert_has_calls(
        [
            call(_options["groups"], camel_hosts[i], hosts_names[i], strict=_options["strict"])
            for i in range(len(camel_hosts))
        ],
        any_order=True,
    )
    inventory._add_host_to_keyed_groups.assert_has_calls(
        [
            call(_options["keyed_groups"], camel_hosts[i], hosts_names[i], strict=_options["strict"])
            for i in range(len(camel_hosts))
        ],
        any_order=True,
    )


BASE_INVENTORY_PARSE = "ansible_collections.amazon.aws.plugins.inventory.aws_rds.AWSInventoryBase.parse"


@pytest.mark.parametrize("include_clusters", [True, False])
@pytest.mark.parametrize("filter_db_cluster_id", [True, False])
@pytest.mark.parametrize("user_cache_directive", [True, False])
@pytest.mark.parametrize("cache", [True, False])
@pytest.mark.parametrize("cache_hit", [True, False])
@patch(BASE_INVENTORY_PARSE)
def test_inventory_parse(
    m_parse, inventory, include_clusters, filter_db_cluster_id, user_cache_directive, cache, cache_hit
):
    inventory_data = MagicMock()
    loader = MagicMock()
    path = generate_random_string(with_punctuation=False, with_digits=False)

    options = {}
    options["regions"] = [f"us-east-{d}" for d in range(random.randint(1, 5))]
    options["strict_permissions"] = random.choice((True, False))
    options["statuses"] = generate_random_string(with_punctuation=False)
    options["include_clusters"] = include_clusters
    options["filters"] = {
        "db-instance-id": [
            f"arn:db:{generate_random_string(with_punctuation=False)}" for i in range(random.randint(1, 10))
        ],
        "dbi-resource-id": generate_random_string(with_punctuation=False),
        "domain": generate_random_string(with_digits=False, with_punctuation=False),
        "engine": generate_random_string(with_digits=False, with_punctuation=False),
    }
    if filter_db_cluster_id:
        options["filters"]["db-cluster-id"] = [
            f"arn:cluster:{generate_random_string(with_punctuation=False)}" for i in range(random.randint(1, 10))
        ]

    options["cache"] = user_cache_directive

    def get_option_side_effect(v):
        return options.get(v)

    inventory.get_option.side_effect = get_option_side_effect

    cache_key = path + generate_random_string()
    inventory.get_cache_key.return_value = cache_key

    cache_key_value = generate_random_string()
    if cache_hit:
        inventory._cache[cache_key] = cache_key_value

    inventory._populate = MagicMock()
    inventory._populate_from_source = MagicMock()
    inventory._get_all_db_hosts = MagicMock()
    all_db_hosts = [
        {"host": f"host_{int(random.randint(1, 1000))}"},
        {"host": f"host_{int(random.randint(1, 1000))}"},
        {"host": f"host_{int(random.randint(1, 1000))}"},
        {"host": f"host_{int(random.randint(1, 1000))}"},
    ]
    inventory._get_all_db_hosts.return_value = all_db_hosts

    format_cache_key_value = f"format_inventory_{all_db_hosts}"
    inventory._format_inventory = MagicMock()
    inventory._format_inventory.return_value = format_cache_key_value

    inventory.parse(inventory_data, loader, path, cache)

    m_parse.assert_called_with(inventory_data, loader, path, cache=cache)

    boto3_instance_filters = ansible_dict_to_boto3_filter_list(options["filters"])
    boto3_cluster_filters = []
    if filter_db_cluster_id and include_clusters:
        boto3_cluster_filters = ansible_dict_to_boto3_filter_list(
            {"db-cluster-id": options["filters"]["db-cluster-id"]}
        )

    if not cache or not user_cache_directive or (cache and user_cache_directive and not cache_hit):
        inventory._get_all_db_hosts.assert_called_with(
            options["regions"],
            boto3_instance_filters,
            boto3_cluster_filters,
            options["strict_permissions"],
            options["statuses"],
            include_clusters,
        )
        inventory._populate.assert_called_with(all_db_hosts)
        inventory._format_inventory.assert_called_with(all_db_hosts)
    else:
        inventory._get_all_db_hosts.assert_not_called()
        inventory._populate.assert_not_called()
        inventory._format_inventory.assert_not_called()

    if cache and user_cache_directive and cache_hit:
        inventory._populate_from_source.assert_called_with(cache_key_value)

    if cache and user_cache_directive and not cache_hit or (not cache and user_cache_directive):
        # validate that cache was populated
        assert inventory._cache[cache_key] == format_cache_key_value

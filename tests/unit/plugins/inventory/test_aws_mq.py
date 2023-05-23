# -*- coding: utf-8 -*-

# Copyright 2023 Ali AlKhalidi <@doteast>
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
import pytest
import random
import string
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible.errors import AnsibleError
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.inventory.aws_mq import (
    InventoryModule,
    _find_hosts_matching_statuses,
    _get_mq_hostname,
    _get_broker_host_tags,
    _add_details_to_hosts
)

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_aws_mq.py requires the python modules 'boto3' and 'botocore'")


def make_clienterror_exception(code="AccessDenied"):
    return botocore.exceptions.ClientError(
        {
            "Error": {"Code": code, "Message": "User is not authorized to perform: xxx on resource: user yyyy"},
            "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
        },
        "getXXX",
    )


@pytest.fixture()
def inventory():
    inventory = InventoryModule()
    inventory.inventory = MagicMock()
    inventory.inventory.set_variable = MagicMock()

    inventory.all_clients = MagicMock()
    inventory.get_option = MagicMock()

    inventory._populate_host_vars = MagicMock()
    inventory._set_composite_vars = MagicMock()
    inventory._add_host_to_composed_groups = MagicMock()
    inventory._add_host_to_keyed_groups = MagicMock()

    inventory.get_cache_key = MagicMock()

    inventory._cache = {}

    return inventory


@pytest.fixture()
def connection():
    conn = MagicMock()
    return conn


@pytest.mark.parametrize(
    "suffix,result",
    [
        ("aws_mq.yml", True),
        ("aws_mq.yaml", True),
        ("aws_MQ.yml", False),
        ("AWS_mq.yaml", False),
    ],
)
def test_inventory_verify_file_suffix(inventory, suffix, result, tmp_path):
    test_dir = tmp_path / "test_aws_mq"
    test_dir.mkdir()
    inventory_file = "inventory" + suffix
    inventory_file = test_dir / inventory_file
    inventory_file.write_text("my inventory")
    assert result == inventory.verify_file(str(inventory_file))


def test_inventory_verify_file_with_missing_file(inventory):
    inventory_file = "this_file_does_not_exist_aws_mq.yml"
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
                {"host": "host1", "BrokerState": "DELETION_IN_PROGRESS"},
                {"host": "host2", "BrokerState": "RUNNING"},
                {"host": "host3", "BrokerState": "REBOOT_IN_PROGRESS"},
                {"host": "host4", "BrokerState": "CRITICAL_ACTION_REQUIRED"},
                {"host": "host5", "BrokerState": "CREATION_FAILED"},
                {"host": "host6", "BrokerState": "CREATION_IN_PROGRESS"},
            ],
            ["RUNNING"],
            [{"host": "host2", "BrokerState": "RUNNING"}],
        ),
        (
            [
                {"host": "host1", "BrokerState": "DELETION_IN_PROGRESS"},
                {"host": "host2", "BrokerState": "RUNNING"},
                {"host": "host3", "BrokerState": "REBOOT_IN_PROGRESS"},
                {"host": "host4", "BrokerState": "CRITICAL_ACTION_REQUIRED"},
                {"host": "host5", "BrokerState": "CREATION_FAILED"},
                {"host": "host6", "BrokerState": "CREATION_IN_PROGRESS"},
            ],
            ["all"],
            [
                {"host": "host1", "BrokerState": "DELETION_IN_PROGRESS"},
                {"host": "host2", "BrokerState": "RUNNING"},
                {"host": "host3", "BrokerState": "REBOOT_IN_PROGRESS"},
                {"host": "host4", "BrokerState": "CRITICAL_ACTION_REQUIRED"},
                {"host": "host5", "BrokerState": "CREATION_FAILED"},
                {"host": "host6", "BrokerState": "CREATION_IN_PROGRESS"},
            ],
        ),
        (
            [
                {"host": "host1", "BrokerState": "DELETION_IN_PROGRESS"},
                {"host": "host2", "BrokerState": "RUNNING"},
                {"host": "host3", "BrokerState": "CREATION_FAILED"},
                {"host": "host4", "BrokerState": "CRITICAL_ACTION_REQUIRED"},
                {"host": "host5", "BrokerState": "RUNNING"},
                {"host": "host6", "BrokerState": "CREATION_IN_PROGRESS"},
            ],
            ["RUNNING"],
            [
                {"host": "host2", "BrokerState": "RUNNING"},
                {"host": "host5", "BrokerState": "RUNNING"},
            ],
        ),
    ],
)
def test_find_hosts_matching_statuses(hosts, statuses, expected):
    assert expected == _find_hosts_matching_statuses(hosts, statuses)


@pytest.mark.parametrize("hosts", ["", "host1", "host2,host3", "host2,host3,host1"])
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_mq._get_mq_hostname")
def test_inventory_format_inventory(m_get_mq_hostname, inventory, hosts):
    hosts_vars = {
        "host1": {"var10": "value10"},
        "host2": {"var20": "value20", "var21": "value21"},
        "host3": {"var30": "value30", "var31": "value31", "var32": "value32"},
    }

    m_get_mq_hostname.side_effect = lambda h: h["name"]

    class _inventory_host(object):
        def __init__(self, name, host_vars):
            self.name = name
            self.vars = host_vars

    inventory.inventory = MagicMock()
    inventory.inventory.get_host.side_effect = lambda x: _inventory_host(name=x, host_vars=hosts_vars.get(x))

    hosts = [{"name": x} for x in hosts.split(",") if x]
    expected = {
        "_meta": {"hostvars": {x["name"]: hosts_vars.get(x["name"]) for x in hosts}},
        "aws_mq": {"hosts": [x["name"] for x in hosts]},
    }

    assert expected == inventory._format_inventory(hosts)
    if hosts == []:
        m_get_mq_hostname.assert_not_called()


@pytest.mark.parametrize("length", range(0, 10, 2))
def test_inventory_populate(inventory, length):
    group = "aws_mq"
    hosts = [f"host_{int(i)}" for i in range(length)]

    inventory._add_hosts = MagicMock()
    inventory._populate(hosts=hosts)

    inventory.inventory.add_group.assert_called_with("aws_mq")

    if len(hosts) == 0:
        inventory.inventory._add_hosts.assert_not_called()
        inventory.inventory.add_child.assert_not_called()
    else:
        inventory._add_hosts.assert_called_with(hosts=hosts, group=group)
        inventory.inventory.add_child.assert_called_with("all", group)

def test_inventory_populate_from_cache(inventory):
    cache_data = {
        "_meta": {
            "hostvars": {
                "broker_A": {"var10": "value10"},
                "broker_B": {"var2": "value2"},
                "broker_C": {"var3": ["value30", "value31", "value32"]},
            }
        },
        "all": {"hosts": ["broker_A", "broker_D", "broker_B", "broker_C"]},
        "aws_broker_group_A": {"hosts": ["broker_A", "broker_D"]},
        "aws_broker_group_B": {"hosts": ["broker_B"]},
        "aws_broker_group_C": {"hosts": ["broker_C"]},
    }

    inventory._populate_from_cache(cache_data)
    inventory.inventory.add_group.assert_has_calls(
        [
            call("aws_broker_group_A"),
            call("aws_broker_group_B"),
            call("aws_broker_group_C"),
        ],
        any_order=True,
    )
    inventory.inventory.add_child.assert_has_calls(
        [
            call("all", "aws_broker_group_A"),
            call("all", "aws_broker_group_B"),
            call("all", "aws_broker_group_C"),
        ],
        any_order=True,
    )

    inventory._populate_host_vars.assert_has_calls(
        [
            call(["broker_A"], {"var10": "value10"}, "aws_broker_group_A"),
            call(["broker_D"], {}, "aws_broker_group_A"),
            call(["broker_B"], {"var2": "value2"}, "aws_broker_group_B"),
            call(["broker_C"], {"var3": ["value30", "value31", "value32"]}, "aws_broker_group_C"),
        ],
        any_order=True,
    )


@pytest.mark.parametrize("detail", [{}, {"Tags": {"tag1": "value1", "tag2": "value2", "Tag3": "Value2"}}])
def test_get_broker_host_tags(detail):
    expected_tags = [
        {"Key": "tag1", "Value": "value1"},
        {"Key": "tag2", "Value": "value2"},
        {"Key": "Tag3", "Value": "Value2"}
    ]

    tags = _get_broker_host_tags(detail)

    if not detail:
        assert tags == []
    else:
        assert tags == expected_tags


@pytest.mark.parametrize("strict", [True, False])
def test_add_details_to_hosts_with_no_hosts(connection, strict):
    hosts = []

    _add_details_to_hosts(connection, hosts, strict)
    connection.describe_broker.assert_not_called()


def test_add_details_to_hosts_with_failure_not_strict(connection):
    hosts = [{"BrokerId": "1"}]

    connection.describe_broker.side_effect = make_clienterror_exception()

    _add_details_to_hosts(connection, hosts, strict=False)

    assert hosts == [{"BrokerId": "1"}]


def test_add_details_to_hosts_with_failure_strict(connection):
    hosts = [{"BrokerId": "1"}]

    connection.describe_broker.side_effect = make_clienterror_exception()

    with pytest.raises(AnsibleError):
        _add_details_to_hosts(connection, hosts, strict=True)


def test_add_details_to_hosts_with_hosts(connection):
    hosts = [
        {"BrokerId": "1"},
        {"BrokerId": "2"}
    ]
    broker_hosts_tags = {
        "1": {"Tags": {"tag10": "value10", "tag11": "value11"}},
        "2": {"Tags": {"tag20": "value20", "tag21": "value21", "tag22": "value22"}}
    }
    connection.describe_broker.side_effect = lambda **kwargs: broker_hosts_tags.get(kwargs.get("BrokerId"))

    _add_details_to_hosts(connection, hosts, strict=False)

    assert hosts == [
        {"BrokerId": "1", "Tags":
            [
                {"Key": "tag10", "Value": "value10"},
                {"Key": "tag11", "Value": "value11"},
            ]},
        {"BrokerId": "2", "Tags":
            [
                {"Key": "tag20", "Value": "value20"},
                {"Key": "tag21", "Value": "value21"},
                {"Key": "tag22", "Value": "value22"}
            ]},
    ]


ADD_DETAILS_TO_HOSTS = "ansible_collections.amazon.aws.plugins.inventory.aws_mq._add_details_to_hosts"


@patch(ADD_DETAILS_TO_HOSTS)
def test_get_broker_hosts(m_add_details_to_hosts, inventory, connection):
    broker = {
        "BrokerArn": "arn:xxx:xxxx",
        "BrokerId": "resource_id",
        "BrokerName": "brk1",
        "BrokerState": "RUNNING",
        "EngineType": "RABBITMQ",
        "DeploymentMode": "CLUSTER_MULTI_AZ"
    }

    conn_paginator = MagicMock()
    paginate = MagicMock()

    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate

    paginate.build_full_result.side_effect = lambda **kwargs: {"BrokerSummaries": [broker]}

    connection.describe_broker.return_value = {}
    connection.list_brokers.return_value = {"BrokerSummaries": [broker]}

    strict = False

    result = inventory._get_broker_hosts(connection=connection, strict=strict)(paginate.build_full_result)

    assert result == [broker]

    m_add_details_to_hosts.assert_called_with(connection, result, strict)


@pytest.mark.parametrize("strict", [True, False])
@patch(ADD_DETAILS_TO_HOSTS)
def test_get_broker_hosts_with_access_denied(m_add_details_to_hosts, inventory, connection, strict):
    conn_paginator = MagicMock()
    paginate = MagicMock()

    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate

    paginate.build_full_result.side_effect = make_clienterror_exception()

    if strict:
        with pytest.raises(AnsibleError):
            inventory._get_broker_hosts(connection=connection, strict=strict)(paginate.build_full_result)
    else:
        assert inventory._get_broker_hosts(connection=connection, strict=strict)(paginate.build_full_result) == []

    m_add_details_to_hosts.assert_not_called()


@patch(ADD_DETAILS_TO_HOSTS)
def test_get_broker_hosts_with_client_error(m_add_details_to_hosts, inventory, connection):
    conn_paginator = MagicMock()
    paginate = MagicMock()

    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate

    paginate.build_full_result.side_effect = make_clienterror_exception(code="Unknown")

    with pytest.raises(AnsibleError):
        inventory._get_broker_hosts(connection=connection, strict=False)(paginate.build_full_result)

    m_add_details_to_hosts.assert_not_called()


FIND_HOSTS_MATCHING_STATUSES = (
    "ansible_collections.amazon.aws.plugins.inventory.aws_mq._find_hosts_matching_statuses"
)


@pytest.mark.parametrize("regions", range(1, 5))
@patch(FIND_HOSTS_MATCHING_STATUSES)
def test_inventory_get_all_hosts(m_find_hosts, inventory, regions):
    params = {
        "regions": [f"us-east-{int(i)}" for i in range(regions)],
        "strict": random.choice((True, False)),
        "statuses": [random.choice(
            [
                "RUNNING",
                "CREATION_IN_PROGRESS",
                "REBOOT_IN_PROGRESS",
                "DELETION_IN_PROGRESS",
                "CRITICAL_ACTION_REQUIRED"
            ]) for i in range(3)],
    }

    connections = [MagicMock() for i in range(regions)]

    inventory.all_clients.return_value = [(connections[i], f"us-east-{int(i)}") for i in range(regions)]

    ids = list(reversed(range(regions)))
    broker_hosts = [{"BrokerName": f"broker_00{int(i)}"} for i in ids]

    inventory._get_broker_hosts = MagicMock()
    inventory._get_broker_hosts._boto3_paginate_wrapper = MagicMock()
    inventory._get_broker_hosts._boto3_paginate_wrapper.side_effect = [[i] for i in broker_hosts]
    inventory._get_broker_hosts.return_value = inventory._get_broker_hosts._boto3_paginate_wrapper

    result = list(sorted(broker_hosts, key=lambda x: x["BrokerName"]))

    m_find_hosts.return_value = result

    assert result == inventory._get_all_hosts(**params)
    inventory.all_clients.assert_called_with("mq")
    inventory._get_broker_hosts.assert_has_calls(
        [call(connections[i], params["strict"]) for i in range(regions)],
        any_order=True
    )

    m_find_hosts.assert_called_with(result, params["statuses"])


@pytest.mark.parametrize("hostvars_prefix", [True])
@pytest.mark.parametrize("hostvars_suffix", [True])
@patch("ansible_collections.amazon.aws.plugins.inventory.aws_mq._get_mq_hostname")
def test_inventory_add_hosts(m_get_mq_hostname, inventory, hostvars_prefix, hostvars_suffix):
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

    m_get_mq_hostname.side_effect = lambda h: h["BrokerName"]

    hosts = [
        {
            "BrokerName": "broker_i_001",
            "Tags": [{"Key": "Name", "Value": "broker_001"}, {"Key": "RunningEngine", "Value": "ActiveMQ"}],
            "availability_zone": "us-east-1a",
        },
        {
            "BrokerName": "broker_i_002",
            "Tags": [{"Key": "ClusterName", "Value": "test_cluster"}, {"Key": "RunningOS", "Value": "CoreOS"}],
        },
        {
            "BrokerName": "test_cluster",
            "Tags": [{"Key": "CluserVersionOrigin", "Value": "2.0"}, {"Key": "Provider", "Value": "RedHat"}],
        },
        {
            "BrokerName": "another_cluster",
            "Tags": [{"Key": "TestingPurpose", "Value": "Ansible"}],
            "availability_zones": ["us-west-1a", "us-east-1b"],
        },
    ]

    group = f"test_add_hosts_group_{generate_random_string(length=10, with_punctuation=False)}"
    inventory._add_hosts(hosts, group)

    m_get_mq_hostname.assert_has_calls([call(h) for h in hosts], any_order=True)

    hosts_names = ["broker_i_001", "broker_i_002", "test_cluster", "another_cluster"]
    inventory.inventory.add_host.assert_has_calls([call(name, group=group) for name in hosts_names], any_order=True)

    camel_hosts = [
        {
            "broker_name": "broker_i_001",
            "tags": {"Name": "broker_001", "RunningEngine": "ActiveMQ"},
            "availability_zone": "us-east-1a",
        },
        {"broker_name": "broker_i_002", "tags": {"ClusterName": "test_cluster", "RunningOS": "CoreOS"}},
        {"broker_name": "test_cluster", "tags": {"CluserVersionOrigin": "2.0", "Provider": "RedHat"}},
        {
            "broker_name": "another_cluster",
            "tags": {"TestingPurpose": "Ansible"},
            "availability_zones": ["us-west-1a", "us-east-1b"],
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

    inventory.get_option.assert_has_calls([call("hostvars_prefix"), call("hostvars_suffix")])
    inventory.inventory.set_variable.assert_has_calls(set_variable_calls)

    if hostvars_prefix or hostvars_suffix:
        tmp = []
        for host in camel_hosts:
            new_host = copy.deepcopy(host)
            for key in host:
                new_key = key
                if hostvars_prefix:
                    new_key = _options["hostvars_prefix"] + new_key
                if hostvars_suffix:
                    new_key += _options["hostvars_suffix"]
                new_host[new_key] = host[key]
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


BASE_INVENTORY_PARSE = "ansible_collections.amazon.aws.plugins.inventory.aws_mq.AWSInventoryBase.parse"


@pytest.mark.parametrize("user_cache_directive", [True, False])
@pytest.mark.parametrize("cache", [True, False])
@pytest.mark.parametrize("cache_hit", [True, False])
@patch(BASE_INVENTORY_PARSE)
def test_inventory_parse(
    m_parse, inventory, user_cache_directive, cache, cache_hit
):
    inventory_data = MagicMock()
    loader = MagicMock()
    path = generate_random_string(with_punctuation=False, with_digits=False)

    options = {}
    options["regions"] = [f"us-east-{d}" for d in range(random.randint(1, 5))]
    options["strict_permissions"] = random.choice((True, False))
    options["statuses"] = generate_random_string(with_punctuation=False)

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
    inventory._populate_from_cache = MagicMock()
    inventory._get_all_hosts = MagicMock()
    all_hosts = [
        {"host": f"host_{int(random.randint(1, 1000))}"},
        {"host": f"host_{int(random.randint(1, 1000))}"},
        {"host": f"host_{int(random.randint(1, 1000))}"},
        {"host": f"host_{int(random.randint(1, 1000))}"},
    ]
    inventory._get_all_hosts.return_value = all_hosts

    format_cache_key_value = f"format_inventory_{all_hosts}"
    inventory._format_inventory = MagicMock()
    inventory._format_inventory.return_value = format_cache_key_value

    inventory.parse(inventory_data, loader, path, cache)

    m_parse.assert_called_with(inventory_data, loader, path, cache=cache)

    if not cache or not user_cache_directive or (cache and user_cache_directive and not cache_hit):
        inventory._get_all_hosts.assert_called_with(
            options["regions"],
            options["strict_permissions"],
            options["statuses"],
        )
        inventory._populate.assert_called_with(all_hosts)
        inventory._format_inventory.assert_called_with(all_hosts)
    else:
        inventory._get_all_hosts.assert_not_called()

    if cache and user_cache_directive and cache_hit:
        inventory._populate_from_cache.assert_called_with(cache_key_value)

    if cache and user_cache_directive and not cache_hit or (not cache and user_cache_directive):
        # validate that cache was populated
        assert inventory._cache[cache_key] == format_cache_key_value

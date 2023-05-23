# -*- coding: utf-8 -*-

# Copyright (c) 2023 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: aws_mq
short_description: MQ broker inventory source
description:
  - Get brokers from Amazon Web Services MQ.
  - Uses a YAML configuration file that ends with aws_mq.(yml|yaml).
options:
  regions:
    description:
      - A list of regions in which to describe MQ brokers. Available regions are listed here
        U(https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/)
    type: list
    elements: str
    default: []
  strict_permissions:
    description: By default if an AccessDenied exception is encountered this plugin will fail. You can set strict_permissions to
      False in the inventory config file which will allow the restrictions to be gracefully skipped.
    type: bool
    default: True
  statuses:
    description:
      - A list of desired states for brokers to be added to inventory. Set to ['all'] as a shorthand to find everything.
        Possible value are listed here U(https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/broker-statuses.html)
    type: list
    elements: str
    default:
      - RUNNING
      - CREATION_IN_PROGRESS
  hostvars_prefix:
    description:
      - The prefix for host variables names coming from AWS.
    type: str
  hostvars_suffix:
    description:
      - The suffix for host variables names coming from AWS.
    type: str
notes:
  - Ansible versions prior to 2.10 should use the fully qualified plugin name 'amazon.aws.aws_mq'.
extends_documentation_fragment:
  - inventory_cache
  - constructed
  - amazon.aws.boto3
  - amazon.aws.common.plugins
  - amazon.aws.region.plugins
  - amazon.aws.assume_role.plugins
author:
  - Ali AlKhalidi (@doteast)
"""

EXAMPLES = r"""
plugin: aws_mq
regions:
  - ca-central-1
keyed_groups:
  - key: engine_type
    prefix: mq
compose:
  app: 'tags.Applications|split(",")'
hostvars_prefix: aws_
hostvars_suffix: _mq
"""

try:
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AWSInventoryBase

broker_attr = [
    "MaintenanceWindowStartTime",
    "AutoMinorVersionUpgrade",
    "AuthenticationStrategy",
    "PubliclyAccessible",
    "EncryptionOptions",
    "HostInstanceType",
    "BrokerInstances",
    "SecurityGroups",
    "DeploymentMode",
    "EngineVersion",
    "StorageType",
    "BrokerState",
    "EngineType",
    "SubnetIds",
    "BrokerArn",
    "BrokerId",
    "Created",
    "Logs",
]

inventory_group = "aws_mq"


def _find_hosts_matching_statuses(hosts, statuses):
    if not statuses:
      statuses = ["RUNNING", "CREATION_IN_PROGRESS"]
    if "all" in statuses:
        return hosts
    valid_hosts = []
    for host in hosts:
        if host.get("BrokerState") in statuses:
            valid_hosts.append(host)
    return valid_hosts

def _get_mq_hostname(host):
    if host.get("BrokerName"):
        return host["BrokerName"]

def _get_broker_host_tags(detail):
    tags = []
    if "Tags" in detail:
        for key, value in detail["Tags"].items():
            tags.append({"Key": key, "Value": value})
    return tags

def _add_details_to_hosts(connection, hosts, strict):
    for host in hosts:
        detail=None
        resource_id = host["BrokerId"]
        try:
            detail = connection.describe_broker(BrokerId=resource_id)
        except is_boto3_error_code("AccessDenied") as e:
            if not strict:
                pass
            else:
                raise AnsibleError(f"Failed to query MQ: {to_native(e)}")
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            raise AnsibleError(f"Failed to query MQ: {to_native(e)}")

        if detail:
            # special handling of tags
            host['Tags'] = _get_broker_host_tags(detail)

            # collect rest of attributes
            for attr in broker_attr:
                if attr in detail:
                    host[attr] = detail[attr]

class InventoryModule(AWSInventoryBase):

    NAME = "amazon.aws.aws_mq"
    INVENTORY_FILE_SUFFIXES = ("aws_mq.yml", "aws_mq.yaml")

    def __init__(self):
        super(InventoryModule, self).__init__()

    def _get_broker_hosts(self, connection, strict):

        def _boto3_paginate_wrapper(func, *args, **kwargs):
            results = []
            try:
                results = func(*args, **kwargs)
                results = results["BrokerSummaries"]
                _add_details_to_hosts(connection, results, strict)
            except is_boto3_error_code("AccessDenied") as e:  # pylint: disable=duplicate-except
                if not strict:
                    results = []
                else:
                    raise AnsibleError(f"Failed to query MQ: {to_native(e)}")
            except (
                botocore.exceptions.ClientError,
                botocore.exceptions.BotoCoreError,
             ) as e:  # pylint: disable=duplicate-except
                raise AnsibleError(f"Failed to query MQ: {to_native(e)}")
            return results
        return _boto3_paginate_wrapper

    def _get_all_hosts(self, regions, strict, statuses):
        """
        :param regions: a list of regions in which to describe hosts
        :param strict: a boolean determining whether to fail or ignore 403 error codes
        :param statuses: a list of statuses that the returned hosts should match
        :return A list of host dictionaries
        """
        all_instances = []

        for connection, _region in self.all_clients("mq"):
            paginator = connection.get_paginator("list_brokers")
            all_instances.extend(
                self._get_broker_hosts(connection, strict)
                (paginator.paginate().build_full_result)
            )
        sorted_hosts = list(
            sorted(all_instances, key=lambda x: x["BrokerName"])
        )
        return _find_hosts_matching_statuses(sorted_hosts, statuses)

    def _populate_from_cache(self, cache_data):
        hostvars = cache_data.pop("_meta", {}).get("hostvars", {})
        for group in cache_data:
            if group == "all":
                continue
            self.inventory.add_group(group)
            hosts = cache_data[group].get("hosts", [])
            for host in hosts:
                self._populate_host_vars([host], hostvars.get(host, {}), group)
            self.inventory.add_child("all", group)

    def _populate(self, hosts):
        group = inventory_group
        self.inventory.add_group(group)
        if hosts:
            self._add_hosts(
                hosts=hosts,
                group=group
            )
            self.inventory.add_child("all", group)

    def _format_inventory(self, hosts):
        results = {"_meta": {"hostvars": {}}}
        group = inventory_group
        results[group] = {"hosts": []}
        for host in hosts:
            hostname = _get_mq_hostname(host)
            results[group]["hosts"].append(hostname)
            h = self.inventory.get_host(hostname)
            results["_meta"]['hostvars'][h.name] = h.vars
        return results

    def _add_hosts(self, hosts, group):
        """
        :param hosts: a list of hosts to add to the group
        :param group: name of the group the host list belongs to
        """
        for host in hosts:
            hostname = _get_mq_hostname(host)
            host = camel_dict_to_snake_dict(host, ignore_list=["Tags", "EngineType"])
            host["tags"] = boto3_tag_list_to_ansible_dict(host.get("tags", []))
            if host.get("engine_type"):
              # align value with API spec of all upper
              host["engine_type"] = host.get("engine_type", "").upper()

            self.inventory.add_host(hostname, group=group)
            new_vars = dict()
            hostvars_prefix = self.get_option("hostvars_prefix")
            hostvars_suffix = self.get_option("hostvars_suffix")
            for hostvar, hostval in host.items():
                if hostvars_prefix:
                    hostvar = hostvars_prefix + hostvar
                if hostvars_suffix:
                    hostvar = hostvar + hostvars_suffix
                new_vars[hostvar] = hostval
                self.inventory.set_variable(hostname, hostvar, hostval)
            host.update(new_vars)

            strict = self.get_option("strict")
            self._set_composite_vars(self.get_option("compose"), host, hostname, strict=strict)
            self._add_host_to_composed_groups(self.get_option("groups"), host, hostname, strict=strict)
            self._add_host_to_keyed_groups(self.get_option("keyed_groups"), host, hostname, strict=strict)

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache=cache)

        # get user specifications
        regions = self.get_option("regions")
        strict_permissions = self.get_option("strict_permissions")
        statuses = self.get_option("statuses")

        result_was_cached, results = self.get_cached_result(path, cache)
        if result_was_cached:
          self._populate_from_cache(results)
          return

        results = self._get_all_hosts(regions, strict_permissions, statuses)
        self._populate(results)

        formatted_inventory = self._format_inventory(results)
        self.update_cached_result(path, cache, formatted_inventory)

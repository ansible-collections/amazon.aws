# -*- coding: utf-8 -*-

# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: aws_rds
short_description: RDS instance inventory source
description:
  - Get instances and clusters from Amazon Web Services RDS.
  - Uses a YAML configuration file that ends with aws_rds.(yml|yaml).
options:
  regions:
    description:
      - A list of regions in which to describe RDS instances and clusters. Available regions are listed here
        U(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html).
    default: []
  filters:
    description:
      - A dictionary of filter value pairs. Available filters are listed here
        U(https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-instances.html#options). If you filter by
        db-cluster-id and I(include_clusters) is True it will apply to clusters as well.
    default: {}
  strict_permissions:
    description:
      - By default if an AccessDenied exception is encountered this plugin will fail. You can set strict_permissions to
        False in the inventory config file which will allow the restrictions to be gracefully skipped.
    type: bool
    default: true
  include_clusters:
    description: Whether or not to query for Aurora clusters as well as instances.
    type: bool
    default: false
  statuses:
    description: A list of desired states for instances/clusters to be added to inventory. Set to ['all'] as a shorthand to find everything.
    type: list
    elements: str
    default:
      - creating
      - available
  hostvars_prefix:
    description:
      - The prefix for host variables names coming from AWS.
    type: str
    version_added: 3.1.0
  hostvars_suffix:
    description:
      - The suffix for host variables names coming from AWS.
    type: str
    version_added: 3.1.0
notes:
  - Ansible versions prior to 2.10 should use the fully qualified plugin name 'amazon.aws.aws_rds'.
extends_documentation_fragment:
  - inventory_cache
  - constructed
  - amazon.aws.boto3
  - amazon.aws.common.plugins
  - amazon.aws.region.plugins
  - amazon.aws.assume_role.plugins
author:
  - Sloane Hertel (@s-hertel)
"""

EXAMPLES = r"""
plugin: aws_rds
regions:
  - us-east-1
  - ca-central-1
keyed_groups:
  - key: 'db_parameter_groups|json_query("[].db_parameter_group_name")'
    prefix: rds_parameter_group
  - key: engine
    prefix: rds
  - key: tags
  - key: region
hostvars_prefix: aws_
hostvars_suffix: _rds
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
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AWSInventoryBase


def _find_hosts_with_valid_statuses(hosts, statuses):
    if "all" in statuses:
        return hosts
    valid_hosts = []
    for host in hosts:
        if host.get("DBInstanceStatus") in statuses:
            valid_hosts.append(host)
        elif host.get("Status") in statuses:
            valid_hosts.append(host)
    return valid_hosts


def _get_rds_hostname(host):
    if host.get("DBInstanceIdentifier"):
        return host["DBInstanceIdentifier"]
    else:
        return host["DBClusterIdentifier"]


def _add_tags_for_rds_hosts(connection, hosts, strict):
    for host in hosts:
        if "DBInstanceArn" in host:
            resource_arn = host["DBInstanceArn"]
        else:
            resource_arn = host["DBClusterArn"]

        try:
            tags = connection.list_tags_for_resource(ResourceName=resource_arn)["TagList"]
        except is_boto3_error_code("AccessDenied") as e:
            if not strict:
                tags = []
            else:
                raise e
        host["Tags"] = tags


def describe_resource_with_tags(func):
    def describe_wrapper(connection, filters, strict=False):
        try:
            results = func(connection=connection, filters=filters)
            if "DBInstances" in results:
                results = results["DBInstances"]
            else:
                results = results["DBClusters"]
            _add_tags_for_rds_hosts(connection, results, strict)
        except is_boto3_error_code("AccessDenied") as e:  # pylint: disable=duplicate-except
            if not strict:
                return []
            raise AnsibleError(f"Failed to query RDS: {to_native(e)}")
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            raise AnsibleError(f"Failed to query RDS: {to_native(e)}")

        return results

    return describe_wrapper


@describe_resource_with_tags
def _describe_db_instances(connection, filters):
    paginator = connection.get_paginator("describe_db_instances")
    return paginator.paginate(Filters=filters).build_full_result()


@describe_resource_with_tags
def _describe_db_clusters(connection, filters):
    return connection.describe_db_clusters(Filters=filters)


class InventoryModule(AWSInventoryBase):
    NAME = "amazon.aws.aws_rds"
    INVENTORY_FILE_SUFFIXES = ("aws_rds.yml", "aws_rds.yaml")

    def __init__(self):
        super().__init__()
        self.credentials = {}

    def _populate(self, hosts):
        group = "aws_rds"
        self.inventory.add_group(group)
        if hosts:
            self._add_hosts(hosts=hosts, group=group)
            self.inventory.add_child("all", group)

    def _populate_from_source(self, source_data):
        hostvars = source_data.pop("_meta", {}).get("hostvars", {})
        for group in source_data:
            if group == "all":
                continue
            self.inventory.add_group(group)
            hosts = source_data[group].get("hosts", [])
            for host in hosts:
                self._populate_host_vars([host], hostvars.get(host, {}), group)
            self.inventory.add_child("all", group)

    def _format_inventory(self, hosts):
        results = {"_meta": {"hostvars": {}}}
        group = "aws_rds"
        results[group] = {"hosts": []}
        for host in hosts:
            hostname = _get_rds_hostname(host)
            results[group]["hosts"].append(hostname)
            h = self.inventory.get_host(hostname)
            results["_meta"]["hostvars"][h.name] = h.vars
        return results

    def _add_hosts(self, hosts, group):
        """
        :param hosts: a list of hosts to be added to a group
        :param group: the name of the group to which the hosts belong
        """
        for host in hosts:
            hostname = _get_rds_hostname(host)
            host = camel_dict_to_snake_dict(host, ignore_list=["Tags"])
            host["tags"] = boto3_tag_list_to_ansible_dict(host.get("tags", []))

            # Allow easier grouping by region
            if "availability_zone" in host:
                host["region"] = host["availability_zone"][:-1]
            elif "availability_zones" in host:
                host["region"] = host["availability_zones"][0][:-1]

            self.inventory.add_host(hostname, group=group)
            hostvars_prefix = self.get_option("hostvars_prefix")
            hostvars_suffix = self.get_option("hostvars_suffix")
            new_vars = dict()
            for hostvar, hostval in host.items():
                if hostvars_prefix:
                    hostvar = hostvars_prefix + hostvar
                if hostvars_suffix:
                    hostvar = hostvar + hostvars_suffix
                new_vars[hostvar] = hostval
                self.inventory.set_variable(hostname, hostvar, hostval)
            host.update(new_vars)

            # Use constructed if applicable
            strict = self.get_option("strict")
            # Composed variables
            self._set_composite_vars(self.get_option("compose"), host, hostname, strict=strict)
            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option("groups"), host, hostname, strict=strict)
            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option("keyed_groups"), host, hostname, strict=strict)

    def _get_all_db_hosts(self, regions, instance_filters, cluster_filters, strict, statuses, gather_clusters=False):
        """
        :param regions: a list of regions in which to describe hosts
        :param instance_filters: a list of boto3 filter dictionaries
        :param cluster_filters: a list of boto3 filter dictionaries
        :param strict: a boolean determining whether to fail or ignore 403 error codes
        :param statuses: a list of statuses that the returned hosts should match
        :return A list of host dictionaries
        """
        all_instances = []
        all_clusters = []

        for connection, _region in self.all_clients("rds"):
            all_instances += _describe_db_instances(connection, instance_filters, strict=strict)
            if gather_clusters:
                all_clusters += _describe_db_clusters(connection, cluster_filters, strict=strict)
        sorted_hosts = list(
            sorted(all_instances, key=lambda x: x["DBInstanceIdentifier"])
            + sorted(all_clusters, key=lambda x: x["DBClusterIdentifier"])
        )
        return _find_hosts_with_valid_statuses(sorted_hosts, statuses)

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache=cache)

        # get user specifications
        regions = self.get_option("regions")
        filters = self.get_option("filters")
        strict_permissions = self.get_option("strict_permissions")
        statuses = self.get_option("statuses")
        include_clusters = self.get_option("include_clusters")
        instance_filters = ansible_dict_to_boto3_filter_list(filters)
        cluster_filters = []
        if "db-cluster-id" in filters and include_clusters:
            cluster_filters = ansible_dict_to_boto3_filter_list({"db-cluster-id": filters["db-cluster-id"]})

        result_was_cached, cached_result = self.get_cached_result(path, cache)
        if result_was_cached:
            self._populate_from_source(cached_result)
            return

        results = self._get_all_db_hosts(
            regions,
            instance_filters,
            cluster_filters,
            strict_permissions,
            statuses,
            include_clusters,
        )
        self._populate(results)

        # Update the cache once we're done
        formatted_inventory = self._format_inventory(results)
        self.update_cached_result(path, cache, formatted_inventory)

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: elasticache
version_added: 1.0.0
short_description: Manage cache clusters in Amazon ElastiCache
description:
  - Manage cache clusters in Amazon ElastiCache.
  - Returns information about the specified cache cluster.
author:
  - "Jim Dalton (@jsdalton)"
options:
  state:
    description:
      - C(absent) or C(present) are idempotent actions that will create or destroy a cache cluster as needed.
      - C(rebooted) will reboot the cluster, resulting in a momentary outage.
    choices: ['present', 'absent', 'rebooted']
    required: true
    type: str
  name:
    description:
      - The cache cluster identifier.
    required: true
    type: str
  engine:
    description:
      - Name of the cache engine to be used.
      - Supported values are C(redis) and C(memcached).
    default: memcached
    type: str
  cache_engine_version:
    description:
      - The version number of the cache engine.
    type: str
    default: ''
  node_type:
    description:
      - The compute and memory capacity of the nodes in the cache cluster.
    default: cache.t2.small
    type: str
  num_nodes:
    description:
      - The initial number of cache nodes that the cache cluster will have.
      - Required when I(state=present).
    type: int
    default: 1
  cache_port:
    description:
      - The port number on which each of the cache nodes will accept
        connections.
    type: int
  cache_parameter_group:
    description:
      - The name of the cache parameter group to associate with this cache cluster. If this argument is omitted, the default cache parameter group
        for the specified engine will be used.
    aliases: [ 'parameter_group' ]
    type: str
    default: ''
  cache_subnet_group:
    description:
      - The subnet group name to associate with. Only use if inside a VPC.
      - Required if inside a VPC.
    type: str
    default: ''
  security_group_ids:
    description:
      - A list of VPC security group IDs to associate with this cache cluster. Only use if inside a VPC.
    type: list
    elements: str
    default: []
  cache_security_groups:
    description:
      - A list of cache security group names to associate with this cache cluster.
      - Don't use if your Cache is inside a VPC. In that case use I(security_group_ids) instead!
    type: list
    elements: str
    default: []
  zone:
    description:
      - The EC2 Availability Zone in which the cache cluster will be created.
    type: str
  wait:
    description:
      - Wait for cache cluster result before returning.
    type: bool
    default: true
  hard_modify:
    description:
      - Whether to destroy and recreate an existing cache cluster if necessary in order to modify its state.
      - Defaults to C(false).
    type: bool
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

RETURN = r""" # """

EXAMPLES = r"""
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

- name: Basic example
  community.aws.elasticache:
    name: "test-please-delete"
    state: present
    engine: memcached
    cache_engine_version: 1.4.14
    node_type: cache.m3.small
    num_nodes: 1
    cache_port: 11211
    cache_security_groups:
      - default
    zone: us-east-1d


- name: Ensure cache cluster is gone
  community.aws.elasticache:
    name: "test-please-delete"
    state: absent

- name: Reboot cache cluster
  community.aws.elasticache:
    name: "test-please-delete"
    state: rebooted
"""

from time import sleep

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class ElastiCacheManager:

    """Handles elasticache creation and destruction"""

    EXIST_STATUSES = ["available", "creating", "rebooting", "modifying"]

    def __init__(
        self,
        module,
        name,
        engine,
        cache_engine_version,
        node_type,
        num_nodes,
        cache_port,
        cache_parameter_group,
        cache_subnet_group,
        cache_security_groups,
        security_group_ids,
        zone,
        wait,
        hard_modify,
    ):
        self.module = module
        self.name = name
        self.engine = engine.lower()
        self.cache_engine_version = cache_engine_version
        self.node_type = node_type
        self.num_nodes = num_nodes
        self.cache_port = cache_port
        self.cache_parameter_group = cache_parameter_group
        self.cache_subnet_group = cache_subnet_group
        self.cache_security_groups = cache_security_groups
        self.security_group_ids = security_group_ids
        self.zone = zone
        self.wait = wait
        self.hard_modify = hard_modify

        self.changed = False
        self.data = None
        self.status = "gone"
        self.conn = self._get_elasticache_connection()
        self._refresh_data()

    def ensure_present(self):
        """Ensure cache cluster exists or create it if not"""
        if self.exists():
            self.sync()
        else:
            self.create()

    def ensure_absent(self):
        """Ensure cache cluster is gone or delete it if not"""
        self.delete()

    def ensure_rebooted(self):
        """Ensure cache cluster is gone or delete it if not"""
        self.reboot()

    def exists(self):
        """Check if cache cluster exists"""
        return self.status in self.EXIST_STATUSES

    def create(self):
        """Create an ElastiCache cluster"""
        if self.status == "available":
            return
        if self.status in ["creating", "rebooting", "modifying"]:
            if self.wait:
                self._wait_for_status("available")
            return
        if self.status == "deleting":
            if self.wait:
                self._wait_for_status("gone")
            else:
                self.module.fail_json(msg=f"'{self.name}' is currently deleting. Cannot create.")

        kwargs = dict(
            CacheClusterId=self.name,
            NumCacheNodes=self.num_nodes,
            CacheNodeType=self.node_type,
            Engine=self.engine,
            EngineVersion=self.cache_engine_version,
            CacheSecurityGroupNames=self.cache_security_groups,
            SecurityGroupIds=self.security_group_ids,
            CacheParameterGroupName=self.cache_parameter_group,
            CacheSubnetGroupName=self.cache_subnet_group,
        )
        if self.cache_port is not None:
            kwargs["Port"] = self.cache_port
        if self.zone is not None:
            kwargs["PreferredAvailabilityZone"] = self.zone

        try:
            self.conn.create_cache_cluster(**kwargs)

        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Failed to create cache cluster")

        self._refresh_data()

        self.changed = True
        if self.wait:
            self._wait_for_status("available")
        return True

    def delete(self):
        """Destroy an ElastiCache cluster"""
        if self.status == "gone":
            return
        if self.status == "deleting":
            if self.wait:
                self._wait_for_status("gone")
            return
        if self.status in ["creating", "rebooting", "modifying"]:
            if self.wait:
                self._wait_for_status("available")
            else:
                self.module.fail_json(msg=f"'{self.name}' is currently {self.status}. Cannot delete.")

        try:
            response = self.conn.delete_cache_cluster(CacheClusterId=self.name)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Failed to delete cache cluster")

        cache_cluster_data = response["CacheCluster"]
        self._refresh_data(cache_cluster_data)

        self.changed = True
        if self.wait:
            self._wait_for_status("gone")

    def sync(self):
        """Sync settings to cluster if required"""
        if not self.exists():
            self.module.fail_json(msg=f"'{self.name}' is {self.status}. Cannot sync.")

        if self.status in ["creating", "rebooting", "modifying"]:
            if self.wait:
                self._wait_for_status("available")
            else:
                # Cluster can only be synced if available. If we can't wait
                # for this, then just be done.
                return

        if self._requires_destroy_and_create():
            if not self.hard_modify:
                self.module.fail_json(
                    msg=f"'{self.name}' requires destructive modification. 'hard_modify' must be set to true to proceed."
                )
            if not self.wait:
                self.module.fail_json(
                    msg=f"'{self.name}' requires destructive modification. 'wait' must be set to true to proceed."
                )
            self.delete()
            self.create()
            return

        if self._requires_modification():
            self.modify()

    def modify(self):
        """Modify the cache cluster. Note it's only possible to modify a few select options."""
        nodes_to_remove = self._get_nodes_to_remove()
        try:
            self.conn.modify_cache_cluster(
                CacheClusterId=self.name,
                NumCacheNodes=self.num_nodes,
                CacheNodeIdsToRemove=nodes_to_remove,
                CacheSecurityGroupNames=self.cache_security_groups,
                CacheParameterGroupName=self.cache_parameter_group,
                SecurityGroupIds=self.security_group_ids,
                ApplyImmediately=True,
                EngineVersion=self.cache_engine_version,
            )
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Failed to modify cache cluster")

        self._refresh_data()

        self.changed = True
        if self.wait:
            self._wait_for_status("available")

    def reboot(self):
        """Reboot the cache cluster"""
        if not self.exists():
            self.module.fail_json(msg=f"'{self.name}' is {self.status}. Cannot reboot.")
        if self.status == "rebooting":
            return
        if self.status in ["creating", "modifying"]:
            if self.wait:
                self._wait_for_status("available")
            else:
                self.module.fail_json(msg=f"'{self.name}' is currently {self.status}. Cannot reboot.")

        # Collect ALL nodes for reboot
        cache_node_ids = [cn["CacheNodeId"] for cn in self.data["CacheNodes"]]
        try:
            self.conn.reboot_cache_cluster(CacheClusterId=self.name, CacheNodeIdsToReboot=cache_node_ids)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Failed to reboot cache cluster")

        self._refresh_data()

        self.changed = True
        if self.wait:
            self._wait_for_status("available")

    def get_info(self):
        """Return basic info about the cache cluster"""
        info = {"name": self.name, "status": self.status}
        if self.data:
            info["data"] = self.data
        return info

    def _wait_for_status(self, awaited_status):
        """Wait for status to change from present status to awaited_status"""
        status_map = {"creating": "available", "rebooting": "available", "modifying": "available", "deleting": "gone"}
        if self.status == awaited_status:
            # No need to wait, we're already done
            return
        if status_map[self.status] != awaited_status:
            self.module.fail_json(
                msg=f"Invalid awaited status. '{self.status}' cannot transition to '{awaited_status}'"
            )

        if awaited_status not in set(status_map.values()):
            self.module.fail_json(msg=f"'{awaited_status}' is not a valid awaited status.")

        while True:
            sleep(1)
            self._refresh_data()
            if self.status == awaited_status:
                break

    def _requires_modification(self):
        """Check if cluster requires (nondestructive) modification"""
        # Check modifiable data attributes
        modifiable_data = {"NumCacheNodes": self.num_nodes, "EngineVersion": self.cache_engine_version}
        for key, value in modifiable_data.items():
            if value is not None and value and self.data[key] != value:
                return True

        # Check cache security groups
        cache_security_groups = []
        for sg in self.data["CacheSecurityGroups"]:
            cache_security_groups.append(sg["CacheSecurityGroupName"])
        if set(cache_security_groups) != set(self.cache_security_groups):
            return True

        # check vpc security groups
        if self.security_group_ids:
            vpc_security_groups = []
            security_groups = self.data.get("SecurityGroups", [])
            for sg in security_groups:
                vpc_security_groups.append(sg["SecurityGroupId"])
            if set(vpc_security_groups) != set(self.security_group_ids):
                return True

        return False

    def _requires_destroy_and_create(self):
        """
        Check whether a destroy and create is required to synchronize cluster.
        """
        unmodifiable_data = {
            "node_type": self.data["CacheNodeType"],
            "engine": self.data["Engine"],
            "cache_port": self._get_port(),
        }
        # Only check for modifications if zone is specified
        if self.zone is not None:
            unmodifiable_data["zone"] = self.data["PreferredAvailabilityZone"]
        for key, value in unmodifiable_data.items():
            if getattr(self, key) is not None and getattr(self, key) != value:
                return True
        return False

    def _get_elasticache_connection(self):
        """Get an elasticache connection"""
        try:
            return self.module.client("elasticache")
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Failed to connect to AWS")

    def _get_port(self):
        """Get the port. Where this information is retrieved from is engine dependent."""
        if self.data["Engine"] == "memcached":
            return self.data["ConfigurationEndpoint"]["Port"]
        elif self.data["Engine"] == "redis":
            # Redis only supports a single node (presently) so just use
            # the first and only
            return self.data["CacheNodes"][0]["Endpoint"]["Port"]

    def _refresh_data(self, cache_cluster_data=None):
        """Refresh data about this cache cluster"""

        if cache_cluster_data is None:
            try:
                response = self.conn.describe_cache_clusters(CacheClusterId=self.name, ShowCacheNodeInfo=True)
            except is_boto3_error_code("CacheClusterNotFound"):
                self.data = None
                self.status = "gone"
                return
            except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
                self.module.fail_json_aws(e, msg="Failed to describe cache clusters")
            cache_cluster_data = response["CacheClusters"][0]
        self.data = cache_cluster_data
        self.status = self.data["CacheClusterStatus"]

        # The documentation for elasticache lies -- status on rebooting is set
        # to 'rebooting cache cluster nodes' instead of 'rebooting'. Fix it
        # here to make status checks etc. more sane.
        if self.status == "rebooting cache cluster nodes":
            self.status = "rebooting"

    def _get_nodes_to_remove(self):
        """If there are nodes to remove, it figures out which need to be removed"""
        num_nodes_to_remove = self.data["NumCacheNodes"] - self.num_nodes
        if num_nodes_to_remove <= 0:
            return []

        if not self.hard_modify:
            self.module.fail_json(
                msg=f"'{self.name}' requires removal of cache nodes. 'hard_modify' must be set to true to proceed."
            )

        cache_node_ids = [cn["CacheNodeId"] for cn in self.data["CacheNodes"]]
        return cache_node_ids[-num_nodes_to_remove:]


def main():
    """elasticache ansible module"""
    argument_spec = dict(
        state=dict(required=True, choices=["present", "absent", "rebooted"]),
        name=dict(required=True),
        engine=dict(default="memcached"),
        cache_engine_version=dict(default=""),
        node_type=dict(default="cache.t2.small"),
        num_nodes=dict(default=1, type="int"),
        # alias for compat with the original PR 1950
        cache_parameter_group=dict(default="", aliases=["parameter_group"]),
        cache_port=dict(type="int"),
        cache_subnet_group=dict(default=""),
        cache_security_groups=dict(default=[], type="list", elements="str"),
        security_group_ids=dict(default=[], type="list", elements="str"),
        zone=dict(),
        wait=dict(default=True, type="bool"),
        hard_modify=dict(type="bool"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
    )

    name = module.params["name"]
    state = module.params["state"]
    engine = module.params["engine"]
    cache_engine_version = module.params["cache_engine_version"]
    node_type = module.params["node_type"]
    num_nodes = module.params["num_nodes"]
    cache_port = module.params["cache_port"]
    cache_subnet_group = module.params["cache_subnet_group"]
    cache_security_groups = module.params["cache_security_groups"]
    security_group_ids = module.params["security_group_ids"]
    zone = module.params["zone"]
    wait = module.params["wait"]
    hard_modify = module.params["hard_modify"]
    cache_parameter_group = module.params["cache_parameter_group"]

    if cache_subnet_group and cache_security_groups:
        module.fail_json(msg="Can't specify both cache_subnet_group and cache_security_groups")

    if state == "present" and not num_nodes:
        module.fail_json(msg="'num_nodes' is a required parameter. Please specify num_nodes > 0")

    elasticache_manager = ElastiCacheManager(
        module,
        name,
        engine,
        cache_engine_version,
        node_type,
        num_nodes,
        cache_port,
        cache_parameter_group,
        cache_subnet_group,
        cache_security_groups,
        security_group_ids,
        zone,
        wait,
        hard_modify,
    )

    if state == "present":
        elasticache_manager.ensure_present()
    elif state == "absent":
        elasticache_manager.ensure_absent()
    elif state == "rebooted":
        elasticache_manager.ensure_rebooted()

    facts_result = dict(changed=elasticache_manager.changed, elasticache=elasticache_manager.get_info())

    module.exit_json(**facts_result)


if __name__ == "__main__":
    main()

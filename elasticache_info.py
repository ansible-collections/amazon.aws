#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
module: elasticache_info
short_description: Retrieve information for AWS ElastiCache clusters
version_added: 1.0.0
description:
  - Retrieve information from AWS ElastiCache clusters.
options:
  name:
    description:
      - The name of an ElastiCache cluster.
    type: str
author:
  - Will Thames (@willthames)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = '''
- name: obtain all ElastiCache information
  community.aws.elasticache_info:

- name: obtain all information for a single ElastiCache cluster
  community.aws.elasticache_info:
    name: test_elasticache
'''

RETURN = '''
elasticache_clusters:
  description: List of ElastiCache clusters.
  returned: always
  type: list
  elements: dict
  contains:
    arn:
      description: ARN of the cache cluster.
      returned: always
      type: str
      sample: 'arn:aws:elasticache:us-east-1:123456789012:cluster:ansible-test'
    auto_minor_version_upgrade:
      description: Whether to automatically upgrade to minor versions.
      returned: always
      type: bool
      sample: true
    cache_cluster_create_time:
      description: Date and time cluster was created.
      returned: always
      type: str
      sample: '2017-09-15T05:43:46.038000+00:00'
    cache_cluster_id:
      description: ID of the cache cluster.
      returned: always
      type: str
      sample: abcd-1234-001
    cache_cluster_status:
      description: Status of ElastiCache cluster.
      returned: always
      type: str
      sample: available
    cache_node_type:
      description: Instance type of ElastiCache nodes.
      returned: always
      type: str
      sample: cache.t2.micro
    cache_nodes:
      description: List of ElastiCache nodes in the cluster.
      returned: always
      type: list
      elements: dict
      contains:
        cache_node_create_time:
          description: Date and time node was created.
          returned: always
          type: str
          sample: '2017-09-15T05:43:46.038000+00:00'
        cache_node_id:
          description: ID of the cache node.
          returned: always
          type: str
          sample: '0001'
        cache_node_status:
          description: Status of the cache node.
          returned: always
          type: str
          sample: available
        customer_availability_zone:
          description: Availability Zone in which the cache node was created.
          returned: always
          type: str
          sample: ap-southeast-2b
        endpoint:
          description: Connection details for the cache node.
          returned: always
          type: dict
          contains:
            address:
              description: URL of the cache node endpoint.
              returned: always
              type: str
              sample: abcd-1234-001.bgiz2p.0001.apse2.cache.amazonaws.com
            port:
              description: Port of the cache node endpoint.
              returned: always
              type: int
              sample: 6379
        parameter_group_status:
          description: Status of the Cache Parameter Group.
          returned: always
          type: str
          sample: in-sync
    cache_parameter_group:
      description: Contents of the Cache Parameter Group.
      returned: always
      type: dict
      contains:
        cache_node_ids_to_reboot:
          description: Cache nodes which need to be rebooted for parameter changes to be applied.
          returned: always
          type: list
          elements: str
          sample: []
        cache_parameter_group_name:
          description: Name of the cache parameter group.
          returned: always
          type: str
          sample: default.redis3.2
        parameter_apply_status:
          description: Status of parameter updates.
          returned: always
          type: str
          sample: in-sync
    cache_security_groups:
      description: Security Groups used by the cache.
      returned: always
      type: list
      elements: str
      sample:
        - 'sg-abcd1234'
    cache_subnet_group_name:
      description: ElastiCache Subnet Group used by the cache.
      returned: always
      type: str
      sample: abcd-subnet-group
    client_download_landing_page:
      description: URL of client download web page.
      returned: always
      type: str
      sample: 'https://console.aws.amazon.com/elasticache/home#client-download:'
    engine:
      description: Engine used by ElastiCache.
      returned: always
      type: str
      sample: redis
    engine_version:
      description: Version of ElastiCache engine.
      returned: always
      type: str
      sample: 3.2.4
    notification_configuration:
      description: Configuration of notifications.
      returned: if notifications are enabled
      type: dict
      contains:
        topic_arn:
          description: ARN of notification destination topic.
          returned: if notifications are enabled
          type: str
          sample: arn:aws:sns:*:123456789012:my_topic
        topic_name:
          description: Name of notification destination topic.
          returned: if notifications are enabled
          type: str
          sample: MyTopic
    num_cache_nodes:
      description: Number of Cache Nodes.
      returned: always
      type: int
      sample: 1
    pending_modified_values:
      description: Values that are pending modification.
      returned: always
      type: dict
    preferred_availability_zone:
      description: Preferred Availability Zone.
      returned: always
      type: str
      sample: ap-southeast-2b
    preferred_maintenance_window:
      description: Time slot for preferred maintenance window.
      returned: always
      type: str
      sample: sat:12:00-sat:13:00
    replication_group:
      description: Informations about the associated replication group.
      version_added: 4.1.0
      returned: if replication is enabled
      type: dict
      contains:
        arn:
          description: The ARN (Amazon Resource Name) of the replication group.
          returned: always
          type: str
        at_rest_encryption_enabled:
          description: A flag that enables encryption at-rest when set to true.
          returned: always
          type: bool
        auth_token_enabled:
          description: A flag that enables using an AuthToken (password) when issuing Redis commands.
          returned: always
          type: bool
        automatic_failover:
          description: Indicates the status of automatic failover for this Redis replication group.
          returned: always
          type: str
          sample: enabled
        cache_node_type:
          description: The name of the compute and memory capacity node type for each node in the replication group.
          returned: always
          type: str
          sample: cache.t3.medium
        cluster_enabled:
          description: A flag indicating whether or not this replication group is cluster enabled.
          returned: always
          type: bool
        description:
          description: The user supplied description of the replication group.
          returned: always
          type: str
        global_replication_group_info:
          description: The name of the Global datastore and role of this replication group in the Global datastore.
          returned: always
          type: dict
          contains:
            global_replication_group_id:
              description: The name of the Global datastore.
              returned: always
              type: str
            global_replication_group_member_role:
              description: The role of the replication group in a Global datastore. Can be primary or secondary.
              returned: always
              type: str
        kms_key_id:
          description: The ID of the KMS key used to encrypt the disk in the cluster.
          returned: always
          type: str
        member_clusters:
          description: The names of all the cache clusters that are part of this replication group.
          returned: always
          type: list
          elements: str
        multi_az:
          description: A flag indicating if you have Multi-AZ enabled to enhance fault tolerance.
          returned: always
          type: str
          sample: enabled
        node_groups:
          description: A list of node groups in this replication group.
          returned: always
          type: list
          elements: dict
          contains:
            node_group_id:
              description: The identifier for the node group (shard).
              returned: always
              type: str
            node_group_members:
              description: A list containing information about individual nodes within the node group (shard).
              returned: always
              type: list
              elements: dict
              contains:
                cache_cluster_id:
                  description: The ID of the cluster to which the node belongs.
                  returned: always
                  type: str
                cache_node_id:
                  description: The ID of the node within its cluster.
                  returned: always
                  type: str
                current_role:
                  description: The role that is currently assigned to the node - primary or replica.
                  returned: always
                  type: str
                  sample: primary
                preferred_availability_zone:
                  description: The name of the Availability Zone in which the node is located.
                  returned: always
                  type: str
                read_endpoint:
                  description: The information required for client programs to connect to a node for read operations.
                  returned: always
                  type: list
                  elements: dict
                  contains:
                    address:
                      description: The DNS hostname of the cache node.
                      returned: always
                      type: str
                    port:
                      description: The port number that the cache engine is listening on.
                      returned: always
                      type: int
                      sample: 6379
            primary_endpoint:
              description: The endpoint of the primary node in this node group (shard).
              returned: always
              type: list
              elements: dict
              contains:
                address:
                  description: The DNS hostname of the cache node.
                  returned: always
                  type: str
                port:
                  description: The port number that the cache engine is listening on.
                  returned: always
                  type: int
                  sample: 6379
            reader_endpoint:
              description: The endpoint of the cache node.
              returned: always
              type: dict
              contains:
                address:
                  description: The DNS hostname of the cache node.
                  returned: always
                  type: str
                port:
                  description: The port number that the cache engine is listening on.
                  returned: always
                  type: int
                  sample: 6379
            status:
              description: The current state of this replication group - C(creating), C(available), C(modifying), C(deleting).
              returned: always
              type: str
              sample: available
        pending_modified_values:
          description: A group of settings to be applied to the replication group, either immediately or during the next maintenance window.
          returned: always
          type: dict
        replication_group_id:
          description: Replication Group Id.
          returned: always
          type: str
          sample: replication-001
        snapshot_retention_limit:
          description: The number of days for which ElastiCache retains automatic cluster snapshots before deleting them.
          returned: always
          type: int
        snapshot_window:
          description: The daily time range (in UTC) during which ElastiCache begins taking a daily snapshot of your node group (shard).
          returned: always
          type: str
          sample: 07:00-09:00
        snapshotting_cluster_id:
          description: The cluster ID that is used as the daily snapshot source for the replication group.
          returned: always
          type: str
        status:
          description: The current state of this replication group - C(creating), C(available), C(modifying), C(deleting), C(create-failed), C(snapshotting)
          returned: always
          type: str
        transit_encryption_enabled:
          description: A flag that enables in-transit encryption when set to C(true).
          returned: always
          type: bool
    replication_group_id:
      description: Replication Group Id.
      returned: if replication is enabled
      type: str
      sample: replication-001
    security_groups:
      description: List of Security Groups associated with ElastiCache.
      returned: always
      type: list
      elements: dict
      contains:
        security_group_id:
          description: Security Group ID
          returned: always
          type: str
          sample: sg-abcd1234
        status:
          description: Status of Security Group
          returned: always
          type: str
          sample: active
    tags:
      description: Tags applied to the ElastiCache cluster
      returned: always
      type: dict
      sample:
        Application: web
        Environment: test
'''

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


@AWSRetry.exponential_backoff()
def describe_cache_clusters_with_backoff(client, cluster_id=None):
    paginator = client.get_paginator('describe_cache_clusters')
    params = dict(ShowCacheNodeInfo=True)
    if cluster_id:
        params['CacheClusterId'] = cluster_id
    try:
        response = paginator.paginate(**params).build_full_result()
    except is_boto3_error_code('CacheClusterNotFound'):
        return []
    return response['CacheClusters']


@AWSRetry.exponential_backoff()
def describe_replication_group_with_backoff(client, replication_group_id):
    try:
        response = client.describe_replication_groups(ReplicationGroupId=replication_group_id)
    except is_boto3_error_code('ReplicationGroupNotFoundFault'):
        return None

    return response['ReplicationGroups'][0]


@AWSRetry.exponential_backoff()
def get_elasticache_tags_with_backoff(client, cluster_id):
    return client.list_tags_for_resource(ResourceName=cluster_id)['TagList']


def get_aws_account_id(module):
    try:
        client = module.client('sts')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Can't authorize connection")

    try:
        return client.get_caller_identity()['Account']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain AWS account id")


def get_elasticache_clusters(client, module):
    region = module.region
    try:
        clusters = describe_cache_clusters_with_backoff(client, cluster_id=module.params.get('name'))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain cache cluster info")

    account_id = get_aws_account_id(module)
    results = []
    for cluster in clusters:

        cluster = camel_dict_to_snake_dict(cluster)
        arn = "arn:aws:elasticache:%s:%s:cluster:%s" % (region, account_id, cluster['cache_cluster_id'])
        try:
            tags = get_elasticache_tags_with_backoff(client, arn)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get tags for cluster %s")

        cluster['tags'] = boto3_tag_list_to_ansible_dict(tags)

        if cluster.get('replication_group_id', None):
            try:
                replication_group = describe_replication_group_with_backoff(client, cluster['replication_group_id'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't obtain replication group info")

            if replication_group is not None:
                replication_group = camel_dict_to_snake_dict(replication_group)
                cluster['replication_group'] = replication_group

        results.append(cluster)
    return results


def main():
    argument_spec = dict(
        name=dict(required=False),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    client = module.client('elasticache')

    module.exit_json(elasticache_clusters=get_elasticache_clusters(client, module))


if __name__ == '__main__':
    main()

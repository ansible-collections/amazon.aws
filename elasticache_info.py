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
  - Retrieve information from AWS ElastiCache clusters
  - This module was called C(elasticache_facts) before Ansible 2.9. The usage did not change.
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
  description: List of ElastiCache clusters
  returned: always
  type: complex
  contains:
    auto_minor_version_upgrade:
      description: Whether to automatically upgrade to minor versions
      returned: always
      type: bool
      sample: true
    cache_cluster_create_time:
      description: Date and time cluster was created
      returned: always
      type: str
      sample: '2017-09-15T05:43:46.038000+00:00'
    cache_cluster_id:
      description: ID of the cache cluster
      returned: always
      type: str
      sample: abcd-1234-001
    cache_cluster_status:
      description: Status of ElastiCache cluster
      returned: always
      type: str
      sample: available
    cache_node_type:
      description: Instance type of ElastiCache nodes
      returned: always
      type: str
      sample: cache.t2.micro
    cache_nodes:
      description: List of ElastiCache nodes in the cluster
      returned: always
      type: complex
      contains:
        cache_node_create_time:
          description: Date and time node was created
          returned: always
          type: str
          sample: '2017-09-15T05:43:46.038000+00:00'
        cache_node_id:
          description: ID of the cache node
          returned: always
          type: str
          sample: '0001'
        cache_node_status:
          description: Status of the cache node
          returned: always
          type: str
          sample: available
        customer_availability_zone:
          description: Availability Zone in which the cache node was created
          returned: always
          type: str
          sample: ap-southeast-2b
        endpoint:
          description: Connection details for the cache node
          returned: always
          type: complex
          contains:
            address:
              description: URL of the cache node endpoint
              returned: always
              type: str
              sample: abcd-1234-001.bgiz2p.0001.apse2.cache.amazonaws.com
            port:
              description: Port of the cache node endpoint
              returned: always
              type: int
              sample: 6379
        parameter_group_status:
          description: Status of the Cache Parameter Group
          returned: always
          type: str
          sample: in-sync
    cache_parameter_group:
      description: Contents of the Cache Parameter Group
      returned: always
      type: complex
      contains:
        cache_node_ids_to_reboot:
          description: Cache nodes which need to be rebooted for parameter changes to be applied
          returned: always
          type: list
          sample: []
        cache_parameter_group_name:
          description: Name of the cache parameter group
          returned: always
          type: str
          sample: default.redis3.2
        parameter_apply_status:
          description: Status of parameter updates
          returned: always
          type: str
          sample: in-sync
    cache_security_groups:
      description: Security Groups used by the cache
      returned: always
      type: list
      sample:
        - 'sg-abcd1234'
    cache_subnet_group_name:
      description: ElastiCache Subnet Group used by the cache
      returned: always
      type: str
      sample: abcd-subnet-group
    client_download_landing_page:
      description: URL of client download web page
      returned: always
      type: str
      sample: 'https://console.aws.amazon.com/elasticache/home#client-download:'
    engine:
      description: Engine used by ElastiCache
      returned: always
      type: str
      sample: redis
    engine_version:
      description: Version of ElastiCache engine
      returned: always
      type: str
      sample: 3.2.4
    notification_configuration:
      description: Configuration of notifications
      returned: if notifications are enabled
      type: complex
      contains:
        topic_arn:
          description: ARN of notification destination topic
          returned: if notifications are enabled
          type: str
          sample: arn:aws:sns:*:123456789012:my_topic
        topic_name:
          description: Name of notification destination topic
          returned: if notifications are enabled
          type: str
          sample: MyTopic
    num_cache_nodes:
      description: Number of Cache Nodes
      returned: always
      type: int
      sample: 1
    pending_modified_values:
      description: Values that are pending modification
      returned: always
      type: complex
      contains: {}
    preferred_availability_zone:
      description: Preferred Availability Zone
      returned: always
      type: str
      sample: ap-southeast-2b
    preferred_maintenance_window:
      description: Time slot for preferred maintenance window
      returned: always
      type: str
      sample: sat:12:00-sat:13:00
    replication_group_id:
      description: Replication Group Id
      returned: always
      type: str
      sample: replication-001
    security_groups:
      description: List of Security Groups associated with ElastiCache
      returned: always
      type: complex
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
      type: complex
      contains: {}
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
        results.append(cluster)
    return results


def main():
    argument_spec = dict(
        name=dict(required=False),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'elasticache_facts':
        module.deprecate("The 'elasticache_facts' module has been renamed to 'elasticache_info'", date='2021-12-01', collection_name='community.aws')

    client = module.client('elasticache')

    module.exit_json(elasticache_clusters=get_elasticache_clusters(client, module))


if __name__ == '__main__':
    main()

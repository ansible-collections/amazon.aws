#!/usr/bin/python
# Copyright (c) 2022 Ansible Project
# Copyright (c) 2022 Alina Buzachis (@alinabuzachis)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: rds_cluster_info
version_added: 5.0.0
short_description: Obtain information about one or more RDS clusters
description:
  - Obtain information about one or more RDS clusters.
  - This module was originally added to C(community.aws) in release 3.2.0.
options:
    db_cluster_identifier:
        description:
          - The user-supplied DB cluster identifier.
          - If this parameter is specified, information from only the specific DB cluster is returned.
        aliases:
          - cluster_id
          - id
          - cluster_name
        type: str
    filters:
        description:
            - A filter that specifies one or more DB clusters to describe.
              See U(https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeDBClusters.html).
        type: dict
author:
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3

'''

EXAMPLES = r'''
- name: Get info of all existing DB clusters
  amazon.aws.rds_cluster_info:
  register: _result_cluster_info

- name: Get info on a specific DB cluster
  amazon.aws.rds_cluster_info:
    cluster_id: "{{ cluster_id }}"
  register: _result_cluster_info

- name: Get info all DB clusters with specific engine
  amazon.aws.rds_cluster_info:
    engine: "aurora"
  register: _result_cluster_info
'''

RETURN = r'''
clusters:
  description: List of RDS clusters.
  returned: always
  type: list
  contains:
    activity_stream_status:
        description: The status of the database activity stream.
        type: str
        sample: stopped
    allocated_storage:
        description:
        - The allocated storage size in gigabytes. Since aurora storage size is not fixed this is
          always 1 for aurora database engines.
        type: int
        sample: 1
    associated_roles:
        description:
        - A list of dictionaries of the AWS Identity and Access Management (IAM) roles that are associated
          with the DB cluster. Each dictionary contains the role_arn and the status of the role.
        type: list
        sample: []
    availability_zones:
        description: The list of availability zones that instances in the DB cluster can be created in.
        type: list
        sample:
        - us-east-1c
        - us-east-1a
        - us-east-1e
    backup_retention_period:
        description: The number of days for which automatic DB snapshots are retained.
        type: int
        sample: 1
    cluster_create_time:
        description: The time in UTC when the DB cluster was created.
        type: str
        sample: '2018-06-29T14:08:58.491000+00:00'
    copy_tags_to_snapshot:
        description:
        - Specifies whether tags are copied from the DB cluster to snapshots of the DB cluster.
        type: bool
        sample: false
    cross_account_clone:
        description:
        - Specifies whether the DB cluster is a clone of a DB cluster owned by a different Amazon Web Services account.
        type: bool
        sample: false
    db_cluster_arn:
        description: The Amazon Resource Name (ARN) for the DB cluster.
        type: str
        sample: arn:aws:rds:us-east-1:123456789012:cluster:rds-cluster-demo
    db_cluster_identifier:
        description: The lowercase user-supplied DB cluster identifier.
        type: str
        sample: rds-cluster-demo
    db_cluster_members:
        description:
        - A list of dictionaries containing information about the instances in the cluster.
          Each dictionary contains the I(db_instance_identifier), I(is_cluster_writer) (bool),
          I(db_cluster_parameter_group_status), and I(promotion_tier) (int).
        type: list
        sample: []
    db_cluster_parameter_group:
        description: The parameter group associated with the DB cluster.
        type: str
        sample: default.aurora5.6
    db_cluster_resource_id:
        description: The AWS Region-unique, immutable identifier for the DB cluster.
        type: str
        sample: cluster-D2MEQDN3BQNXDF74K6DQJTHASU
    db_subnet_group:
        description: The name of the subnet group associated with the DB Cluster.
        type: str
        sample: default
    deletion_protection:
        description:
        - Indicates if the DB cluster has deletion protection enabled.
          The database can't be deleted when deletion protection is enabled.
        type: bool
        sample: false
    domain_memberships:
        description:
        - The Active Directory Domain membership records associated with the DB cluster.
        type: list
        sample: []
    earliest_restorable_time:
        description: The earliest time to which a database can be restored with point-in-time restore.
        type: str
        sample: '2018-06-29T14:09:34.797000+00:00'
    endpoint:
        description: The connection endpoint for the primary instance of the DB cluster.
        type: str
        sample: rds-cluster-demo.cluster-cvlrtwiennww.us-east-1.rds.amazonaws.com
    engine:
        description: The database engine of the DB cluster.
        type: str
        sample: aurora
    engine_mode:
        description: The DB engine mode of the DB cluster.
        type: str
        sample: provisioned
    engine_version:
        description: The database engine version.
        type: str
        sample: 5.6.10a
    hosted_zone_id:
        description: The ID that Amazon Route 53 assigns when you create a hosted zone.
        type: str
        sample: Z2R2ITUGPM61AM
    http_endpoint_enabled:
        description:
        - A value that indicates whether the HTTP endpoint for an Aurora Serverless DB cluster is enabled.
        type: bool
        sample: false
    iam_database_authentication_enabled:
        description: Whether IAM accounts may be mapped to database accounts.
        type: bool
        sample: false
    latest_restorable_time:
        description: The latest time to which a database can be restored with point-in-time restore.
        type: str
        sample: '2018-06-29T14:09:34.797000+00:00'
    master_username:
        description: The master username for the DB cluster.
        type: str
        sample: username
    multi_az:
        description: Whether the DB cluster has instances in multiple availability zones.
        type: bool
        sample: false
    port:
        description: The port that the database engine is listening on.
        type: int
        sample: 3306
    preferred_backup_window:
        description: The UTC weekly time range during which system maintenance can occur.
        type: str
        sample: 10:18-10:48
    preferred_maintenance_window:
        description: The UTC weekly time range during which system maintenance can occur.
        type: str
        sample: tue:03:23-tue:03:53
    read_replica_identifiers:
        description: A list of read replica ID strings associated with the DB cluster.
        type: list
        sample: []
    reader_endpoint:
        description: The reader endpoint for the DB cluster.
        type: str
        sample: rds-cluster-demo.cluster-ro-cvlrtwiennww.us-east-1.rds.amazonaws.com
    status:
        description: The status of the DB cluster.
        type: str
        sample: available
    storage_encrypted:
        description: Whether the DB cluster is storage encrypted.
        type: bool
        sample: false
    tag_list:
        description: A list of tags consisting of key-value pairs.
        type: list
        elements: dict
        sample: [
            {
                "key": "Created_By",
                "value": "Ansible_rds_cluster_integration_test"
            }
        ]
    tags:
        description: A dictionary of key value pairs.
        type: dict
        sample: {
            "Name": "rds-cluster-demo"
        }
    vpc_security_groups:
        description: A list of the DB cluster's security groups and their status.
        type: complex
        contains:
            status:
                description: Status of the security group.
                type: str
                sample: active
            vpc_security_group_id:
                description: Security group of the cluster.
                type: str
                sample: sg-12345678
'''


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags


@AWSRetry.jittered_backoff(retries=10)
def _describe_db_clusters(client, **params):
    try:
        paginator = client.get_paginator('describe_db_clusters')
        return paginator.paginate(**params).build_full_result()['DBClusters']
    except is_boto3_error_code('DBClusterNotFoundFault'):
        return []


def cluster_info(client, module):
    cluster_id = module.params.get('db_cluster_identifier')
    filters = module.params.get('filters')

    params = dict()
    if cluster_id:
        params['DBClusterIdentifier'] = cluster_id
    if filters:
        params['Filters'] = ansible_dict_to_boto3_filter_list(filters)

    try:
        result = _describe_db_clusters(client, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Couldn't get RDS cluster information.")

    for cluster in result:
        cluster['Tags'] = get_tags(client, module, cluster['DBClusterArn'])

    return dict(changed=False, clusters=[camel_dict_to_snake_dict(cluster, ignore_list=['Tags']) for cluster in result])


def main():
    argument_spec = dict(
        db_cluster_identifier=dict(aliases=['cluster_id', 'id', 'cluster_name']),
        filters=dict(type='dict'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client('rds', retry_decorator=AWSRetry.jittered_backoff(retries=10))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS.')

    module.exit_json(**cluster_info(client, module))


if __name__ == '__main__':
    main()

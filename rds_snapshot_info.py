#!/usr/bin/python
# Copyright (c) 2014-2017 Ansible Project
# Copyright (c) 2017, 2018 Will Thames
# Copyright (c) 2017, 2018 Michael De La Rue
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: rds_snapshot_info
version_added: 1.0.0
short_description: obtain information about one or more RDS snapshots
description:
  - Obtain information about one or more RDS snapshots. These can be for unclustered snapshots or snapshots of clustered DBs (Aurora).
  - Aurora snapshot information may be obtained if no identifier parameters are passed or if one of the cluster parameters are passed.
  - This module was called C(rds_snapshot_facts) before Ansible 2.9. The usage did not change.
options:
  db_snapshot_identifier:
    description:
      - Name of an RDS (unclustered) snapshot.
      - Mutually exclusive with I(db_instance_identifier), I(db_cluster_identifier), I(db_cluster_snapshot_identifier)
    required: false
    aliases:
      - snapshot_name
    type: str
  db_instance_identifier:
    description:
      - RDS instance name for which to find snapshots.
      - Mutually exclusive with I(db_snapshot_identifier), I(db_cluster_identifier), I(db_cluster_snapshot_identifier)
    required: false
    type: str
  db_cluster_identifier:
    description:
      - RDS cluster name for which to find snapshots.
      - Mutually exclusive with I(db_snapshot_identifier), I(db_instance_identifier), I(db_cluster_snapshot_identifier)
    required: false
    type: str
  db_cluster_snapshot_identifier:
    description:
      - Name of an RDS cluster snapshot.
      - Mutually exclusive with I(db_instance_identifier), I(db_snapshot_identifier), I(db_cluster_identifier)
    required: false
    type: str
  snapshot_type:
    description:
      - Type of snapshot to find.
      - By default both automated and manual snapshots will be returned.
    required: false
    choices: ['automated', 'manual', 'shared', 'public']
    type: str
requirements:
    - "python >= 2.6"
    - "boto3"
author:
    - "Will Thames (@willthames)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: Get information about an snapshot
  community.aws.rds_snapshot_info:
    db_snapshot_identifier: snapshot_name
  register: new_database_info

- name: Get all RDS snapshots for an RDS instance
  community.aws.rds_snapshot_info:
    db_instance_identifier: helloworld-rds-master
'''

RETURN = '''
snapshots:
  description: List of non-clustered snapshots
  returned: When cluster parameters are not passed
  type: complex
  contains:
    allocated_storage:
      description: How many gigabytes of storage are allocated
      returned: always
      type: int
      sample: 10
    availability_zone:
      description: The availability zone of the database from which the snapshot was taken
      returned: always
      type: str
      sample: us-west-2b
    db_instance_identifier:
      description: Database instance identifier
      returned: always
      type: str
      sample: hello-world-rds
    db_snapshot_arn:
      description: Snapshot ARN
      returned: always
      type: str
      sample: arn:aws:rds:us-west-2:111111111111:snapshot:rds:hello-world-rds-us1-2018-05-16-04-03
    db_snapshot_identifier:
      description: Snapshot name
      returned: always
      type: str
      sample: rds:hello-world-rds-us1-2018-05-16-04-03
    encrypted:
      description: Whether the snapshot was encrypted
      returned: always
      type: bool
      sample: true
    engine:
      description: Database engine
      returned: always
      type: str
      sample: postgres
    engine_version:
      description: Database engine version
      returned: always
      type: str
      sample: 9.5.10
    iam_database_authentication_enabled:
      description: Whether database authentication through IAM is enabled
      returned: always
      type: bool
      sample: false
    instance_create_time:
      description: Time the Instance was created
      returned: always
      type: str
      sample: '2017-10-10T04:00:07.434000+00:00'
    kms_key_id:
      description: ID of the KMS Key encrypting the snapshot
      returned: always
      type: str
      sample: arn:aws:kms:us-west-2:111111111111:key/abcd1234-1234-aaaa-0000-1234567890ab
    license_model:
      description: License model
      returned: always
      type: str
      sample: postgresql-license
    master_username:
      description: Database master username
      returned: always
      type: str
      sample: dbadmin
    option_group_name:
      description: Database option group name
      returned: always
      type: str
      sample: default:postgres-9-5
    percent_progress:
      description: Percent progress of snapshot
      returned: always
      type: int
      sample: 100
    snapshot_create_time:
      description: Time snapshot was created
      returned: always
      type: str
      sample: '2018-05-16T04:03:33.871000+00:00'
    snapshot_type:
      description: Type of snapshot
      returned: always
      type: str
      sample: automated
    status:
      description: Status of snapshot
      returned: always
      type: str
      sample: available
    storage_type:
      description: Storage type of underlying DB
      returned: always
      type: str
      sample: gp2
    tags:
      description: Snapshot tags
      returned: when snapshot is not shared
      type: complex
      contains: {}
    vpc_id:
      description: ID of VPC containing the DB
      returned: always
      type: str
      sample: vpc-abcd1234
cluster_snapshots:
  description: List of cluster snapshots
  returned: always
  type: complex
  contains:
    allocated_storage:
      description: How many gigabytes of storage are allocated
      returned: always
      type: int
      sample: 1
    availability_zones:
      description: The availability zones of the database from which the snapshot was taken
      returned: always
      type: list
      sample:
      - ca-central-1a
      - ca-central-1b
    cluster_create_time:
      description: Date and time the cluster was created
      returned: always
      type: str
      sample: '2018-05-17T00:13:40.223000+00:00'
    db_cluster_identifier:
      description: Database cluster identifier
      returned: always
      type: str
      sample: test-aurora-cluster
    db_cluster_snapshot_arn:
      description: ARN of the database snapshot
      returned: always
      type: str
      sample: arn:aws:rds:ca-central-1:111111111111:cluster-snapshot:test-aurora-snapshot
    db_cluster_snapshot_identifier:
      description: Snapshot identifier
      returned: always
      type: str
      sample: test-aurora-snapshot
    engine:
      description: Database engine
      returned: always
      type: str
      sample: aurora
    engine_version:
      description: Database engine version
      returned: always
      type: str
      sample: 5.6.10a
    iam_database_authentication_enabled:
      description: Whether database authentication through IAM is enabled
      returned: always
      type: bool
      sample: false
    kms_key_id:
      description: ID of the KMS Key encrypting the snapshot
      returned: always
      type: str
      sample: arn:aws:kms:ca-central-1:111111111111:key/abcd1234-abcd-1111-aaaa-0123456789ab
    license_model:
      description: License model
      returned: always
      type: str
      sample: aurora
    master_username:
      description: Database master username
      returned: always
      type: str
      sample: shertel
    percent_progress:
      description: Percent progress of snapshot
      returned: always
      type: int
      sample: 0
    port:
      description: Database port
      returned: always
      type: int
      sample: 0
    snapshot_create_time:
      description: Date and time when the snapshot was created
      returned: always
      type: str
      sample: '2018-05-17T00:23:23.731000+00:00'
    snapshot_type:
      description: Type of snapshot
      returned: always
      type: str
      sample: manual
    status:
      description: Status of snapshot
      returned: always
      type: str
      sample: creating
    storage_encrypted:
      description: Whether the snapshot is encrypted
      returned: always
      type: bool
      sample: true
    tags:
      description: Tags of the snapshot
      returned: when snapshot is not shared
      type: complex
      contains: {}
    vpc_id:
      description: VPC of the database
      returned: always
      type: str
      sample: vpc-abcd1234
'''

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule, is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


def common_snapshot_info(module, conn, method, prefix, params):
    paginator = conn.get_paginator(method)
    try:
        results = paginator.paginate(**params).build_full_result()['%ss' % prefix]
    except is_boto3_error_code('%sNotFound' % prefix):
        results = []
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, "trying to get snapshot information")

    for snapshot in results:
        try:
            if snapshot['SnapshotType'] != 'shared':
                snapshot['Tags'] = boto3_tag_list_to_ansible_dict(conn.list_tags_for_resource(ResourceName=snapshot['%sArn' % prefix],
                                                                                              aws_retry=True)['TagList'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, "Couldn't get tags for snapshot %s" % snapshot['%sIdentifier' % prefix])

    return [camel_dict_to_snake_dict(snapshot, ignore_list=['Tags']) for snapshot in results]


def cluster_snapshot_info(module, conn):
    snapshot_name = module.params.get('db_cluster_snapshot_identifier')
    snapshot_type = module.params.get('snapshot_type')
    instance_name = module.params.get('db_cluster_identifier')

    params = dict()
    if snapshot_name:
        params['DBClusterSnapshotIdentifier'] = snapshot_name
    if instance_name:
        params['DBClusterIdentifier'] = instance_name
    if snapshot_type:
        params['SnapshotType'] = snapshot_type
        if snapshot_type == 'public':
            params['IncludePublic'] = True
        elif snapshot_type == 'shared':
            params['IncludeShared'] = True

    return common_snapshot_info(module, conn, 'describe_db_cluster_snapshots', 'DBClusterSnapshot', params)


def standalone_snapshot_info(module, conn):
    snapshot_name = module.params.get('db_snapshot_identifier')
    snapshot_type = module.params.get('snapshot_type')
    instance_name = module.params.get('db_instance_identifier')

    params = dict()
    if snapshot_name:
        params['DBSnapshotIdentifier'] = snapshot_name
    if instance_name:
        params['DBInstanceIdentifier'] = instance_name
    if snapshot_type:
        params['SnapshotType'] = snapshot_type
        if snapshot_type == 'public':
            params['IncludePublic'] = True
        elif snapshot_type == 'shared':
            params['IncludeShared'] = True

    return common_snapshot_info(module, conn, 'describe_db_snapshots', 'DBSnapshot', params)


def main():
    argument_spec = dict(
        db_snapshot_identifier=dict(aliases=['snapshot_name']),
        db_instance_identifier=dict(),
        db_cluster_identifier=dict(),
        db_cluster_snapshot_identifier=dict(),
        snapshot_type=dict(choices=['automated', 'manual', 'shared', 'public'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['db_snapshot_identifier', 'db_instance_identifier', 'db_cluster_identifier', 'db_cluster_snapshot_identifier']]
    )
    if module._name == 'rds_snapshot_facts':
        module.deprecate("The 'rds_snapshot_facts' module has been renamed to 'rds_snapshot_info'", date='2021-12-01', collection_name='community.aws')

    conn = module.client('rds', retry_decorator=AWSRetry.jittered_backoff(retries=10))
    results = dict()
    if not module.params['db_cluster_identifier'] and not module.params['db_cluster_snapshot_identifier']:
        results['snapshots'] = standalone_snapshot_info(module, conn)
    if not module.params['db_snapshot_identifier'] and not module.params['db_instance_identifier']:
        results['cluster_snapshots'] = cluster_snapshot_info(module, conn)

    module.exit_json(changed=False, **results)


if __name__ == '__main__':
    main()

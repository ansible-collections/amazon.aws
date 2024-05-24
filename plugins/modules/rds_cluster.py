#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Ansible Project
# Copyright (c) 2022 Alina Buzachis (@alinabuzachis)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_cluster
version_added: 5.0.0
short_description: rds_cluster module
description:
  - Create, modify, and delete RDS clusters.
  - This module was originally added to C(community.aws) in release 3.2.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
author:
  - Sloane Hertel (@s-hertel)
  - Alina Buzachis (@alinabuzachis)
options:
  # General module options
    state:
        description:
          - Whether the snapshot should exist or not.
          - C(started) and C(stopped) can only be used with aurora clusters
          - Support for C(started) and C(stopped) was added in release 6.3.0.
        choices: ['present', 'absent', 'started', 'stopped']
        default: 'present'
        type: str
    creation_source:
        description: Which source to use if creating from a template (an existing cluster, S3 bucket, or snapshot).
        choices: ['snapshot', 's3', 'cluster']
        type: str
    force_update_password:
        description:
          - Set to C(true) to update your cluster password with I(master_user_password).
          - Since comparing passwords to determine if it needs to be updated is not possible this is set to C(false) by default to allow idempotence.
        type: bool
        default: false
    promote:
        description: Set to C(true) to promote a read replica cluster.
        type: bool
        default: false
    purge_cloudwatch_logs_exports:
        description:
          - Whether or not to disable Cloudwatch logs enabled for the DB cluster that are not provided in I(enable_cloudwatch_logs_exports).
            Set I(enable_cloudwatch_logs_exports) to an empty list to disable all.
        type: bool
        default: true
    purge_security_groups:
        description:
          - Set to C(false) to retain any enabled security groups that aren't specified in the task and are associated with the cluster.
          - Can be applied to I(vpc_security_group_ids)
        type: bool
        default: true
    wait:
        description: Whether to wait for the cluster to be available or deleted.
        type: bool
        default: true
    # Options that have a corresponding boto3 parameter
    apply_immediately:
        description:
          - A value that specifies whether modifying a cluster with I(new_db_cluster_identifier) and I(master_user_password)
            should be applied as soon as possible, regardless of the I(preferred_maintenance_window) setting. If C(false), changes
            are applied during the next maintenance window.
        type: bool
        default: false
    availability_zones:
        description:
          - A list of EC2 Availability Zones that instances in the DB cluster can be created in.
            May be used when creating a cluster or when restoring from S3 or a snapshot.
        aliases:
          - zones
          - az
        type: list
        elements: str
    backtrack_to:
        description:
          - The timestamp of the time to backtrack the DB cluster to in ISO 8601 format, such as "2017-07-08T18:00Z".
        type: str
    backtrack_window:
        description:
          - The target backtrack window, in seconds. To disable backtracking, set this value to C(0).
          - If specified, this value must be set to a number from C(0) to C(259,200) (72 hours).
        type: int
    backup_retention_period:
        description:
          - The number of days for which automated backups are retained (must be within C(1) to C(35)).
            May be used when creating a new cluster, when restoring from S3, or when modifying a cluster.
        type: int
        default: 1
    character_set_name:
        description:
          - The character set to associate with the DB cluster.
        type: str
    database_name:
        description:
          - The name for your database. If a name is not provided Amazon RDS will not create a database.
        aliases:
          - db_name
        type: str
    db_cluster_identifier:
        description:
          - The DB cluster (lowercase) identifier. The identifier must contain from 1 to 63 letters, numbers, or
            hyphens and the first character must be a letter and may not end in a hyphen or contain consecutive hyphens.
        aliases:
          - cluster_id
          - id
          - cluster_name
        type: str
        required: true
    db_cluster_parameter_group_name:
        description:
          - The name of the DB cluster parameter group to associate with this DB cluster.
            If this argument is omitted when creating a cluster, the default DB cluster parameter group for the specified DB engine and version is used.
        type: str
    db_subnet_group_name:
        description:
          - A DB subnet group to associate with this DB cluster if not using the default.
        type: str
    enable_cloudwatch_logs_exports:
        description:
          - A list of log types that need to be enabled for exporting to CloudWatch Logs.
          - Engine aurora-mysql supports C(audit), C(error), C(general) and C(slowquery).
          - Engine aurora-postgresql supports C(postgresql).
        type: list
        elements: str
    deletion_protection:
        description:
          -  A value that indicates whether the DB cluster has deletion protection enabled.
             The database can't be deleted when deletion protection is enabled.
             By default, deletion protection is disabled.
        type: bool
    global_cluster_identifier:
        description:
          -  The global cluster ID of an Aurora cluster that becomes the primary cluster in the new global database cluster.
        type: str
    enable_http_endpoint:
        description:
          -  A value that indicates whether to enable the HTTP endpoint for an Aurora Serverless DB cluster.
             By default, the HTTP endpoint is disabled.
        type: bool
    copy_tags_to_snapshot:
        description:
          - Indicates whether to copy all tags from the DB cluster to snapshots of the DB cluster.
            The default is not to copy them.
        type: bool
    domain:
        description:
          - The Active Directory directory ID to create the DB cluster in.
        type: str
    domain_iam_role_name:
        description:
          - Specify the name of the IAM role to be used when making API calls to the Directory Service.
        type: str
    enable_global_write_forwarding:
        description:
          - A value that indicates whether to enable this DB cluster to forward write operations to the primary cluster of an Aurora global database.
            By default, write operations are not allowed on Aurora DB clusters that are secondary clusters in an Aurora global database.
          - This value can be only set on Aurora DB clusters that are members of an Aurora global database.
        type: bool
    db_cluster_instance_class:
        description:
          - The compute and memory capacity of each DB instance in the Multi-AZ DB cluster, for example C(db.m6gd.xlarge).
          - Not all DB instance classes are available in all Amazon Web Services Regions, or for all database engines.
          - For the full list of DB instance classes and availability for your engine visit
            U(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html).
          - This setting is required to create a Multi-AZ DB cluster.
        type: str
        version_added: 5.5.0
    enable_iam_database_authentication:
        description:
          - Enable mapping of AWS Identity and Access Management (IAM) accounts to database accounts.
            If this option is omitted when creating the cluster, Amazon RDS sets this to C(false).
        type: bool
    allocated_storage:
        description:
          - The amount of storage in gibibytes (GiB) to allocate to each DB instance in the Multi-AZ DB cluster.
          - This setting is required to create a Multi-AZ DB cluster.
        type: int
        version_added: 5.5.0
    storage_type:
        description:
          - Specifies the storage type to be associated with the DB cluster.
          - This setting is required to create a Multi-AZ DB cluster.
          - When specified, a value for the I(iops) parameter is required.
          - Defaults to C(io1).
        type: str
        choices:
          - io1
        version_added: 5.5.0
    iops:
        description:
          - The amount of Provisioned IOPS (input/output operations per second) to be initially allocated for each DB instance in the Multi-AZ DB cluster.
          - This setting is required to create a Multi-AZ DB cluster
          - Must be a multiple between .5 and 50 of the storage amount for the DB cluster.
        type: int
        version_added: 5.5.0
    engine:
        description:
          - The name of the database engine to be used for this DB cluster. This is required to create a cluster.
          - The combinaison of I(engine) and I(engine_mode) may not be supported.
          - "See AWS documentation for details:
            L(Amazon RDS Documentation,https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_CreateDBCluster.html)."
          - When I(engine=mysql), I(allocated_storage), I(iops) and I(db_cluster_instance_class) must also be specified.
          - When I(engine=postgres), I(allocated_storage), I(iops) and I(db_cluster_instance_class) must also be specified.
          - Support for C(postgres) and C(mysql) was added in amazon.aws 5.5.0.
        choices:
          - aurora
          - aurora-mysql
          - aurora-postgresql
          - mysql
          - postgres
        type: str
    engine_mode:
        description:
          - The DB engine mode of the DB cluster. The combination of I(engine) and I(engine_mode) may not be supported.
          - "See AWS documentation for details:
            L(Amazon RDS Documentation,https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_CreateDBCluster.html)."
        choices:
          - provisioned
          - serverless
          - parallelquery
          - global
          - multimaster
        type: str
        version_added: 5.5.0
    engine_version:
        description:
          - The version number of the database engine to use.
          - For Aurora MySQL that could be C(5.6.10a), C(5.7.12).
          - Aurora PostgreSQL example, C(9.6.3).
        type: str
    final_snapshot_identifier:
        description:
          - The DB cluster snapshot identifier of the new DB cluster snapshot created when I(skip_final_snapshot=false).
        type: str
    force_backtrack:
        description:
          - A boolean to indicate if the DB cluster should be forced to backtrack when binary logging is enabled.
            Otherwise, an error occurs when binary logging is enabled.
        type: bool
    kms_key_id:
        description:
          - The AWS KMS key identifier (the ARN, unless you are creating a cluster in the same account that owns the
            KMS key, in which case the KMS key alias may be used).
          - If I(replication_source_identifier) specifies an encrypted source Amazon RDS will use the key used toe encrypt the source.
          - If I(storage_encrypted=true) and and I(replication_source_identifier) is not provided, the default encryption key is used.
        type: str
    master_user_password:
        description:
          - An 8-41 character password for the master database user.
          - The password can contain any printable ASCII character except C(/), C("), or C(@).
          - To modify the password use I(force_password_update). Use I(apply immediately) to change
            the password immediately, otherwise it is updated during the next maintenance window.
        aliases:
          - password
        type: str
    master_username:
        description:
          - The name of the master user for the DB cluster. Must be 1-16 letters or numbers and begin with a letter.
        aliases:
          - username
        type: str
    new_db_cluster_identifier:
        description:
          - The new DB cluster (lowercase) identifier for the DB cluster when renaming a DB cluster.
          - The identifier must contain from 1 to 63 letters, numbers, or hyphens and the first character must be a
            letter and may not end in a hyphen or contain consecutive hyphens.
          - Use I(apply_immediately) to rename immediately, otherwise it is updated during the next maintenance window.
        aliases:
          - new_cluster_id
          - new_id
          - new_cluster_name
        type: str
    option_group_name:
        description:
          - The option group to associate with the DB cluster.
        type: str
    port:
        description:
          - The port number on which the instances in the DB cluster accept connections. If not specified, Amazon RDS
            defaults this to C(3306) if the I(engine) is C(aurora) and c(5432) if the I(engine) is C(aurora-postgresql).
        type: int
    preferred_backup_window:
        description:
          - The daily time range (in UTC) of at least 30 minutes, during which automated backups are created if automated backups are
            enabled using I(backup_retention_period). The option must be in the format of "hh24:mi-hh24:mi" and not conflict with
            I(preferred_maintenance_window).
        aliases:
          - backup_window
        type: str
    preferred_maintenance_window:
        description:
          - The weekly time range (in UTC) of at least 30 minutes, during which system maintenance can occur. The option must
            be in the format "ddd:hh24:mi-ddd:hh24:mi" where ddd is one of Mon, Tue, Wed, Thu, Fri, Sat, Sun.
        aliases:
          - maintenance_window
        type: str
    remove_from_global_db:
        description:
          - If set to C(true), the cluster will be removed from global DB.
          - Parameters I(global_cluster_identifier), I(db_cluster_identifier) must be specified when I(remove_from_global_db=true).
        type: bool
        required: false
        version_added: 6.5.0
    replication_source_identifier:
        description:
          - The Amazon Resource Name (ARN) of the source DB instance or DB cluster if this DB cluster is created as a Read Replica.
        aliases:
          - replication_src_id
        type: str
    restore_to_time:
        description:
          - The UTC date and time to restore the DB cluster to. Must be in the format "2015-03-07T23:45:00Z".
          - If this is not provided while restoring a cluster, I(use_latest_restorable_time) must be.
            May not be specified if I(restore_type) is copy-on-write.
        type: str
    restore_type:
        description:
          - The type of restore to be performed. If not provided, Amazon RDS uses full-copy.
        choices:
          - full-copy
          - copy-on-write
        type: str
    role_arn:
        description:
          - The Amazon Resource Name (ARN) of the IAM role to associate with the Aurora DB cluster, for example
            "arn:aws:iam::123456789012:role/AuroraAccessRole"
        type: str
    s3_bucket_name:
        description:
          - The name of the Amazon S3 bucket that contains the data used to create the Amazon Aurora DB cluster.
        type: str
    s3_ingestion_role_arn:
        description:
          - The Amazon Resource Name (ARN) of the AWS Identity and Access Management (IAM) role that authorizes Amazon RDS to access
            the Amazon S3 bucket on your behalf.
        type: str
    s3_prefix:
        description:
          - The prefix for all of the file names that contain the data used to create the Amazon Aurora DB cluster.
          - If you do not specify a SourceS3Prefix value, then the Amazon Aurora DB cluster is created by using all of the files in the Amazon S3 bucket.
        type: str
    serverless_v2_scaling_configuration:
        description:
          - Contains the scaling configuration of an Aurora Serverless v2 DB cluster.
        type: dict
        suboptions:
          min_capacity:
            description:
              - The minimum number of Aurora capacity units (ACUs) for a DB instance in an Aurora Serverless v2 cluster.
              - ACU values can be specified in in half-step increments, such as C(8), C(8.5), C(9), and so on.
              - The smallest possible value is C(0.5).
            type: float
          max_capacity:
            description:
              - The maximum number of Aurora capacity units (ACUs) for a DB instance in an Aurora Serverless v2 cluster.
              - ACU values can be specified in in half-step increments, such as C(40), C(40.5), C(41), and so on.
              - The largest possible value is C(128).
            type: float
        version_added: 7.3.0
    skip_final_snapshot:
        description:
          - Whether a final DB cluster snapshot is created before the DB cluster is deleted.
          - If this is C(false), I(final_snapshot_identifier) must be provided.
        type: bool
        default: false
    snapshot_identifier:
        description:
          - The identifier for the DB snapshot or DB cluster snapshot to restore from.
          - You can use either the name or the ARN to specify a DB cluster snapshot. However, you can use only the ARN to specify a DB snapshot.
        type: str
    source_db_cluster_identifier:
        description:
          - The identifier of the source DB cluster from which to restore.
        type: str
    source_engine:
        description:
          - The identifier for the database engine that was backed up to create the files stored in the Amazon S3 bucket.
        choices:
          - mysql
        type: str
    source_engine_version:
        description:
          - The version of the database that the backup files were created from.
        type: str
    source_region:
        description:
          - The ID of the region that contains the source for the DB cluster.
        type: str
    storage_encrypted:
        description:
          - Whether the DB cluster is encrypted.
        type: bool
    use_earliest_time_on_point_in_time_unavailable:
        description:
          - If I(backtrack_to) is set to a timestamp earlier than the earliest backtrack time, this value backtracks the DB cluster to
            the earliest possible backtrack time. Otherwise, an error occurs.
        type: bool
    use_latest_restorable_time:
        description:
          - Whether to restore the DB cluster to the latest restorable backup time. Only one of I(use_latest_restorable_time)
            and I(restore_to_time) may be provided.
        type: bool
    vpc_security_group_ids:
        description:
          - A list of EC2 VPC security groups to associate with the DB cluster.
        type: list
        elements: str
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Create minimal aurora cluster in default VPC and default subnet group
  amazon.aws.rds_cluster:
    cluster_id: "{{ cluster_id }}"
    engine: "aurora"
    password: "{{ password }}"
    username: "{{ username }}"

- name: Add a new security group without purge
  amazon.aws.rds_cluster:
    id: "{{ cluster_id }}"
    state: present
    vpc_security_group_ids:
      - sg-0be17ba10c9286b0b
    purge_security_groups: false

- name: Modify password
  amazon.aws.rds_cluster:
    id: "{{ cluster_id }}"
    state: present
    password: "{{ new_password }}"
    force_update_password: true
    apply_immediately: true

- name: Rename the cluster
  amazon.aws.rds_cluster:
    engine: aurora
    password: "{{ password }}"
    username: "{{ username }}"
    cluster_id: "cluster-{{ resource_prefix }}"
    new_cluster_id: "cluster-{{ resource_prefix }}-renamed"
    apply_immediately: true

- name: Delete aurora cluster without creating a final snapshot
  amazon.aws.rds_cluster:
    engine: aurora
    password: "{{ password }}"
    username: "{{ username }}"
    cluster_id: "{{ cluster_id }}"
    skip_final_snapshot: true
    tags:
      Name: "cluster-{{ resource_prefix }}"
      Created_By: "Ansible_rds_cluster_integration_test"
    state: absent

- name: Restore cluster from source snapshot
  amazon.aws.rds_cluster:
    engine: aurora
    password: "{{ password }}"
    username: "{{ username }}"
    cluster_id: "cluster-{{ resource_prefix }}-restored"
    snapshot_identifier: "cluster-{{ resource_prefix }}-snapshot"

- name: Create an Aurora PostgreSQL cluster and attach an intance
  amazon.aws.rds_cluster:
    state: present
    engine: aurora-postgresql
    engine_mode: provisioned
    cluster_id: '{{ cluster_id }}'
    username: '{{ username }}'
    password: '{{ password }}'

- name: Attach a new instance to the cluster
  amazon.aws.rds_instance:
    id: '{{ instance_id }}'
    cluster_id: '{{ cluster_id }}'
    engine: aurora-postgresql
    state: present
    db_instance_class: 'db.t3.medium'

- name: Remove a cluster from global DB (do not delete)
  amazon.aws.rds_cluster:
    db_cluster_identifier: '{{ cluster_id }}'
    global_cluster_identifier: '{{ global_cluster_id }}'
    remove_from_global_db: true

- name: Remove a cluster from global DB and Delete without creating a final snapshot
  amazon.aws.rds_cluster:
    engine: aurora
    password: "{{ password }}"
    username: "{{ username }}"
    cluster_id: "{{ cluster_id }}"
    skip_final_snapshot: true
    remove_from_global_db: true
    wait: true
    state: absent

- name: Update cluster port and WAIT for remove secondary DB cluster from global DB to complete
  amazon.aws.rds_cluster:
    db_cluster_identifier: "{{ secondary_cluster_name }}"
    global_cluster_identifier: "{{ global_cluster_name }}"
    remove_from_global_db: true
    state: present
    port: 3389
    region: "{{ secondary_cluster_region }}"

- name: Update cluster port and DO NOT WAIT for remove secondary DB cluster from global DB to complete
  amazon.aws.rds_cluster:
    db_cluster_identifier: "{{ secondary_cluster_name }}"
    global_cluster_identifier: "{{ global_cluster_name }}"
    remove_from_global_db: true
    state: present
    port: 3389
    region: "{{ secondary_cluster_region }}"
    wait: false
"""

RETURN = r"""
activity_stream_status:
  description: The status of the database activity stream.
  returned: always
  type: str
  sample: stopped
allocated_storage:
  description:
    - The allocated storage size in gigabytes. Since aurora storage size is not fixed this is
      always 1 for aurora database engines.
  returned: always
  type: int
  sample: 1
associated_roles:
  description:
    - A list of dictionaries of the AWS Identity and Access Management (IAM) roles that are associated
      with the DB cluster. Each dictionary contains the role_arn and the status of the role.
  returned: always
  type: list
  sample: []
availability_zones:
  description: The list of availability zones that instances in the DB cluster can be created in.
  returned: always
  type: list
  sample:
  - us-east-1c
  - us-east-1a
  - us-east-1e
backup_retention_period:
  description: The number of days for which automatic DB snapshots are retained.
  returned: always
  type: int
  sample: 1
changed:
  description: If the RDS cluster has changed.
  returned: always
  type: bool
  sample: true
cluster_create_time:
  description: The time in UTC when the DB cluster was created.
  returned: always
  type: str
  sample: '2018-06-29T14:08:58.491000+00:00'
copy_tags_to_snapshot:
  description:
    - Specifies whether tags are copied from the DB cluster to snapshots of the DB cluster.
  returned: always
  type: bool
  sample: false
cross_account_clone:
  description:
    - Specifies whether the DB cluster is a clone of a DB cluster owned by a different Amazon Web Services account.
  returned: always
  type: bool
  sample: false
db_cluster_arn:
  description: The Amazon Resource Name (ARN) for the DB cluster.
  returned: always
  type: str
  sample: arn:aws:rds:us-east-1:123456789012:cluster:rds-cluster-demo
db_cluster_identifier:
  description: The lowercase user-supplied DB cluster identifier.
  returned: always
  type: str
  sample: rds-cluster-demo
db_cluster_members:
  description:
    - A list of dictionaries containing information about the instances in the cluster.
      Each dictionary contains the db_instance_identifier, is_cluster_writer (bool),
      db_cluster_parameter_group_status, and promotion_tier (int).
  returned: always
  type: list
  sample: []
db_cluster_parameter_group:
  description: The parameter group associated with the DB cluster.
  returned: always
  type: str
  sample: default.aurora5.6
db_cluster_resource_id:
  description: The AWS Region-unique, immutable identifier for the DB cluster.
  returned: always
  type: str
  sample: cluster-D2MEQDN3BQNXDF74K6DQJTHASU
db_subnet_group:
  description: The name of the subnet group associated with the DB Cluster.
  returned: always
  type: str
  sample: default
deletion_protection:
  description:
    - Indicates if the DB cluster has deletion protection enabled.
      The database can't be deleted when deletion protection is enabled.
  returned: always
  type: bool
  sample: false
domain_memberships:
  description:
    - The Active Directory Domain membership records associated with the DB cluster.
  returned: always
  type: list
  sample: []
earliest_restorable_time:
  description: The earliest time to which a database can be restored with point-in-time restore.
  returned: always
  type: str
  sample: '2018-06-29T14:09:34.797000+00:00'
endpoint:
  description: The connection endpoint for the primary instance of the DB cluster.
  returned: always
  type: str
  sample: rds-cluster-demo.cluster-cvlrtwiennww.us-east-1.rds.amazonaws.com
engine:
  description: The database engine of the DB cluster.
  returned: always
  type: str
  sample: aurora
engine_mode:
  description: The DB engine mode of the DB cluster.
  returned: always
  type: str
  sample: provisioned
engine_version:
  description: The database engine version.
  returned: always
  type: str
  sample: 5.6.10a
hosted_zone_id:
  description: The ID that Amazon Route 53 assigns when you create a hosted zone.
  returned: always
  type: str
  sample: Z2R2ITUGPM61AM
http_endpoint_enabled:
  description:
    - A value that indicates whether the HTTP endpoint for an Aurora Serverless DB cluster is enabled.
  returned: always
  type: bool
  sample: false
iam_database_authentication_enabled:
  description: Whether IAM accounts may be mapped to database accounts.
  returned: always
  type: bool
  sample: false
latest_restorable_time:
  description: The latest time to which a database can be restored with point-in-time restore.
  returned: always
  type: str
  sample: '2018-06-29T14:09:34.797000+00:00'
master_username:
  description: The master username for the DB cluster.
  returned: always
  type: str
  sample: username
multi_az:
  description: Whether the DB cluster has instances in multiple availability zones.
  returned: always
  type: bool
  sample: false
port:
  description: The port that the database engine is listening on.
  returned: always
  type: int
  sample: 3306
preferred_backup_window:
  description: The UTC weekly time range during which system maintenance can occur.
  returned: always
  type: str
  sample: 10:18-10:48
preferred_maintenance_window:
  description: The UTC weekly time range during which system maintenance can occur.
  returned: always
  type: str
  sample: tue:03:23-tue:03:53
read_replica_identifiers:
  description: A list of read replica ID strings associated with the DB cluster.
  returned: always
  type: list
  sample: []
reader_endpoint:
  description: The reader endpoint for the DB cluster.
  returned: always
  type: str
  sample: rds-cluster-demo.cluster-ro-cvlrtwiennww.us-east-1.rds.amazonaws.com
serverless_v2_scaling_configuration:
  description: The scaling configuration for an Aurora Serverless v2 DB cluster.
  returned: when configured
  type: dict
  sample: {
      "max_capacity": 4.5,
      "min_capacity": 2.5
  }
  version_added: 7.3.0
status:
  description: The status of the DB cluster.
  returned: always
  type: str
  sample: available
storage_encrypted:
  description: Whether the DB cluster is storage encrypted.
  returned: always
  type: bool
  sample: false
tag_list:
  description: A list of tags consisting of key-value pairs.
  returned: always
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
  returned: always
  type: dict
  sample: {
    "Name": "rds-cluster-demo"
  }
vpc_security_groups:
  description: A list of the DB cluster's security groups and their status.
  returned: always
  type: complex
  contains:
    status:
      description: Status of the security group.
      returned: always
      type: str
      sample: active
    vpc_security_group_id:
      description: Security group of the cluster.
      returned: always
      type: str
      sample: sg-12345678
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import arg_spec_to_rds_params
from ansible_collections.amazon.aws.plugins.module_utils.rds import call_method
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import wait_for_cluster_status
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list


@AWSRetry.jittered_backoff(retries=10)
def _describe_db_clusters(**params):
    try:
        paginator = client.get_paginator("describe_db_clusters")
        return paginator.paginate(**params).build_full_result()["DBClusters"][0]
    except is_boto3_error_code("DBClusterNotFoundFault"):
        return {}


def get_add_role_options(params_dict, cluster):
    current_role_arns = [role["RoleArn"] for role in cluster.get("AssociatedRoles", [])]
    role = params_dict["RoleArn"]
    if role is not None and role not in current_role_arns:
        return {"RoleArn": role, "DBClusterIdentifier": params_dict["DBClusterIdentifier"]}
    return {}


def get_backtrack_options(params_dict):
    options = ["BacktrackTo", "DBClusterIdentifier", "UseEarliestTimeOnPointInTimeUnavailable"]
    if params_dict["BacktrackTo"] is not None:
        options = dict((k, params_dict[k]) for k in options if params_dict[k] is not None)
        if "ForceBacktrack" in params_dict:
            options["Force"] = params_dict["ForceBacktrack"]
        return options
    return {}


def get_create_options(params_dict):
    options = [
        "AvailabilityZones",
        "BacktrackWindow",
        "BackupRetentionPeriod",
        "PreferredBackupWindow",
        "CharacterSetName",
        "DBClusterIdentifier",
        "DBClusterParameterGroupName",
        "DBSubnetGroupName",
        "DatabaseName",
        "EnableCloudwatchLogsExports",
        "EnableIAMDatabaseAuthentication",
        "KmsKeyId",
        "Engine",
        "EngineMode",
        "EngineVersion",
        "PreferredMaintenanceWindow",
        "MasterUserPassword",
        "MasterUsername",
        "OptionGroupName",
        "Port",
        "ReplicationSourceIdentifier",
        "SourceRegion",
        "StorageEncrypted",
        "Tags",
        "VpcSecurityGroupIds",
        "EngineMode",
        "ScalingConfiguration",
        "DeletionProtection",
        "EnableHttpEndpoint",
        "CopyTagsToSnapshot",
        "Domain",
        "DomainIAMRoleName",
        "EnableGlobalWriteForwarding",
        "GlobalClusterIdentifier",
        "AllocatedStorage",
        "DBClusterInstanceClass",
        "StorageType",
        "Iops",
        "EngineMode",
        "ServerlessV2ScalingConfiguration",
    ]

    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_modify_options(params_dict, force_update_password):
    options = [
        "ApplyImmediately",
        "BacktrackWindow",
        "BackupRetentionPeriod",
        "PreferredBackupWindow",
        "DBClusterIdentifier",
        "DBClusterParameterGroupName",
        "EnableIAMDatabaseAuthentication",
        "EngineVersion",
        "PreferredMaintenanceWindow",
        "MasterUserPassword",
        "NewDBClusterIdentifier",
        "OptionGroupName",
        "Port",
        "VpcSecurityGroupIds",
        "EnableIAMDatabaseAuthentication",
        "CloudwatchLogsExportConfiguration",
        "DeletionProtection",
        "EnableHttpEndpoint",
        "CopyTagsToSnapshot",
        "EnableGlobalWriteForwarding",
        "Domain",
        "DomainIAMRoleName",
        "AllocatedStorage",
        "DBClusterInstanceClass",
        "StorageType",
        "Iops",
        "EngineMode",
        "ServerlessV2ScalingConfiguration",
    ]
    modify_options = dict((k, v) for k, v in params_dict.items() if k in options and v is not None)
    if not force_update_password:
        modify_options.pop("MasterUserPassword", None)
    return modify_options


def get_delete_options(params_dict):
    options = ["DBClusterIdentifier", "FinalSnapshotIdentifier", "SkipFinalSnapshot"]
    return dict((k, params_dict[k]) for k in options if params_dict[k] is not None)


def get_restore_s3_options(params_dict):
    options = [
        "AvailabilityZones",
        "BacktrackWindow",
        "BackupRetentionPeriod",
        "CharacterSetName",
        "DBClusterIdentifier",
        "DBClusterParameterGroupName",
        "DBSubnetGroupName",
        "DatabaseName",
        "EnableCloudwatchLogsExports",
        "EnableIAMDatabaseAuthentication",
        "Engine",
        "EngineVersion",
        "KmsKeyId",
        "MasterUserPassword",
        "MasterUsername",
        "OptionGroupName",
        "Port",
        "PreferredBackupWindow",
        "PreferredMaintenanceWindow",
        "S3BucketName",
        "S3IngestionRoleArn",
        "S3Prefix",
        "SourceEngine",
        "SourceEngineVersion",
        "StorageEncrypted",
        "Tags",
        "VpcSecurityGroupIds",
        "DeletionProtection",
        "EnableHttpEndpoint",
        "CopyTagsToSnapshot",
        "Domain",
        "DomainIAMRoleName",
    ]

    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_restore_snapshot_options(params_dict):
    options = [
        "AvailabilityZones",
        "BacktrackWindow",
        "DBClusterIdentifier",
        "DBSubnetGroupName",
        "DatabaseName",
        "EnableCloudwatchLogsExports",
        "EnableIAMDatabaseAuthentication",
        "Engine",
        "EngineVersion",
        "KmsKeyId",
        "OptionGroupName",
        "Port",
        "SnapshotIdentifier",
        "Tags",
        "VpcSecurityGroupIds",
        "DBClusterParameterGroupName",
        "DeletionProtection",
        "CopyTagsToSnapshot",
        "Domain",
        "DomainIAMRoleName",
    ]
    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_restore_cluster_options(params_dict):
    options = [
        "BacktrackWindow",
        "DBClusterIdentifier",
        "DBSubnetGroupName",
        "EnableCloudwatchLogsExports",
        "EnableIAMDatabaseAuthentication",
        "KmsKeyId",
        "OptionGroupName",
        "Port",
        "RestoreToTime",
        "RestoreType",
        "SourceDBClusterIdentifier",
        "Tags",
        "UseLatestRestorableTime",
        "VpcSecurityGroupIds",
        "DeletionProtection",
        "CopyTagsToSnapshot",
        "Domain",
        "DomainIAMRoleName",
    ]
    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_rds_method_attribute_name(cluster):
    state = module.params["state"]
    creation_source = module.params["creation_source"]
    method_name = None
    method_options_name = None

    if state == "absent":
        if cluster and cluster["Status"] not in ["deleting", "deleted"]:
            method_name = "delete_db_cluster"
            method_options_name = "get_delete_options"
    elif state == "started":
        if cluster and cluster["Status"] not in ["starting", "started", "available"]:
            method_name = "start_db_cluster"
            method_options_name = "get_modify_options"
    elif state == "stopped":
        if cluster and cluster["Status"] not in ["stopping", "stopped"]:
            method_name = "stop_db_cluster"
            method_options_name = "get_modify_options"
    else:
        if cluster:
            method_name = "modify_db_cluster"
            method_options_name = "get_modify_options"
        elif creation_source == "snapshot":
            method_name = "restore_db_cluster_from_snapshot"
            method_options_name = "get_restore_snapshot_options"
        elif creation_source == "s3":
            method_name = "restore_db_cluster_from_s3"
            method_options_name = "get_restore_s3_options"
        elif creation_source == "cluster":
            method_name = "restore_db_cluster_to_point_in_time"
            method_options_name = "get_restore_cluster_options"
        else:
            method_name = "create_db_cluster"
            method_options_name = "get_create_options"

    return method_name, method_options_name


def add_role(params):
    if not module.check_mode:
        try:
            client.add_role_to_db_cluster(**params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(
                e, msg=f"Unable to add role {params['RoleArn']} to cluster {params['DBClusterIdentifier']}"
            )
        wait_for_cluster_status(client, module, params["DBClusterIdentifier"], "cluster_available")


def backtrack_cluster(params):
    if not module.check_mode:
        try:
            client.backtrack_db_cluster(**params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg=f"Unable to backtrack cluster {params['DBClusterIdentifier']}")
        wait_for_cluster_status(client, module, params["DBClusterIdentifier"], "cluster_available")


def get_cluster(db_cluster_id):
    try:
        return _describe_db_clusters(DBClusterIdentifier=db_cluster_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe DB clusters")


def changing_cluster_options(modify_params, current_cluster):
    changing_params = {}
    apply_immediately = modify_params.pop("ApplyImmediately")
    db_cluster_id = modify_params.pop("DBClusterIdentifier")

    enable_cloudwatch_logs_export = modify_params.pop("EnableCloudwatchLogsExports", None)
    if enable_cloudwatch_logs_export is not None:
        desired_cloudwatch_logs_configuration = {"EnableLogTypes": [], "DisableLogTypes": []}
        provided_cloudwatch_logs = set(enable_cloudwatch_logs_export)
        current_cloudwatch_logs_export = set(current_cluster["EnabledCloudwatchLogsExports"])

        desired_cloudwatch_logs_configuration["EnableLogTypes"] = list(
            provided_cloudwatch_logs.difference(current_cloudwatch_logs_export)
        )
        if module.params["purge_cloudwatch_logs_exports"]:
            desired_cloudwatch_logs_configuration["DisableLogTypes"] = list(
                current_cloudwatch_logs_export.difference(provided_cloudwatch_logs)
            )
        changing_params["CloudwatchLogsExportConfiguration"] = desired_cloudwatch_logs_configuration

    password = modify_params.pop("MasterUserPassword", None)
    if password:
        changing_params["MasterUserPassword"] = password

    new_cluster_id = modify_params.pop("NewDBClusterIdentifier", None)
    if new_cluster_id and new_cluster_id != current_cluster["DBClusterIdentifier"]:
        changing_params["NewDBClusterIdentifier"] = new_cluster_id

    option_group = modify_params.pop("OptionGroupName", None)
    if option_group and option_group not in [
        g["DBClusterOptionGroupName"] for g in current_cluster["DBClusterOptionGroupMemberships"]
    ]:
        changing_params["OptionGroupName"] = option_group

    vpc_sgs = modify_params.pop("VpcSecurityGroupIds", None)
    if vpc_sgs:
        desired_vpc_sgs = []
        provided_vpc_sgs = set(vpc_sgs)
        current_vpc_sgs = set([sg["VpcSecurityGroupId"] for sg in current_cluster["VpcSecurityGroups"]])
        if module.params["purge_security_groups"]:
            desired_vpc_sgs = vpc_sgs
        else:
            if provided_vpc_sgs - current_vpc_sgs:
                desired_vpc_sgs = list(provided_vpc_sgs | current_vpc_sgs)

        if desired_vpc_sgs:
            changing_params["VpcSecurityGroupIds"] = desired_vpc_sgs

    desired_db_cluster_parameter_group = modify_params.pop("DBClusterParameterGroupName", None)
    if desired_db_cluster_parameter_group:
        if desired_db_cluster_parameter_group != current_cluster["DBClusterParameterGroup"]:
            changing_params["DBClusterParameterGroupName"] = desired_db_cluster_parameter_group

    for param in modify_params:
        if modify_params[param] != current_cluster[param]:
            changing_params[param] = modify_params[param]

    if changing_params:
        changing_params["DBClusterIdentifier"] = db_cluster_id
        if apply_immediately is not None:
            changing_params["ApplyImmediately"] = apply_immediately

    if module.params["state"] == "started":
        if current_cluster["Engine"] in ["mysql", "postgres"]:
            module.fail_json("Only aurora clusters can use the state started")
        changing_params["DBClusterIdentifier"] = db_cluster_id

    if module.params["state"] == "stopped":
        if current_cluster["Engine"] in ["mysql", "postgres"]:
            module.fail_json("Only aurora clusters can use the state stopped")
        changing_params["DBClusterIdentifier"] = db_cluster_id

    return changing_params


def ensure_present(cluster, parameters, method_name, method_options_name):
    changed = False

    if not cluster:
        if parameters.get("Tags") is not None:
            parameters["Tags"] = ansible_dict_to_boto3_tag_list(parameters["Tags"])

        call_method(client, module, method_name, eval(method_options_name)(parameters))
        changed = True
    else:
        if get_backtrack_options(parameters):
            backtrack_cluster(client, module, get_backtrack_options(parameters))
            changed = True
        else:
            modifiable_options = eval(method_options_name)(
                parameters, force_update_password=module.params["force_update_password"]
            )
            modify_options = changing_cluster_options(modifiable_options, cluster)
            if modify_options:
                call_method(client, module, method_name, modify_options)
                changed = True
            if module.params["tags"] is not None:
                existing_tags = get_tags(client, module, cluster["DBClusterArn"])
                changed |= ensure_tags(
                    client,
                    module,
                    cluster["DBClusterArn"],
                    existing_tags,
                    module.params["tags"],
                    module.params["purge_tags"],
                )

    add_role_params = get_add_role_options(parameters, cluster)
    if add_role_params:
        add_role(client, module, add_role_params)
        changed = True

    if module.params["promote"] and cluster.get("ReplicationSourceIdentifier"):
        call_method(
            client,
            module,
            "promote_read_replica_db_cluster",
            parameters={"DBClusterIdentifier": module.params["db_cluster_identifier"]},
        )
        changed = True

    return changed


def handle_remove_from_global_db(cluster):
    global_cluster_id = module.params.get("global_cluster_identifier")
    db_cluster_id = module.params.get("db_cluster_identifier")
    db_cluster_arn = cluster["DBClusterArn"]

    if module.check_mode:
        return True

    try:
        client.remove_from_global_cluster(DbClusterIdentifier=db_cluster_arn, GlobalClusterIdentifier=global_cluster_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(
            e, msg=f"Failed to remove cluster {db_cluster_id} from global DB cluster {global_cluster_id}."
        )

    # for replica cluster - wait for cluster to change status from 'available' to 'promoting'
    # only replica/secondary clusters have "GlobalWriteForwardingStatus" field
    if "GlobalWriteForwardingStatus" in cluster:
        wait_for_cluster_status(client, module, db_cluster_id, "db_cluster_promoting")

    # if wait=true, wait for db cluster remove from global db operation to complete
    if module.params.get("wait"):
        wait_for_cluster_status(client, module, db_cluster_id, "cluster_available")

    return True


def main():
    global module
    global client

    arg_spec = dict(
        state=dict(choices=["present", "absent", "started", "stopped"], default="present"),
        creation_source=dict(type="str", choices=["snapshot", "s3", "cluster"]),
        force_update_password=dict(type="bool", default=False),
        promote=dict(type="bool", default=False),
        purge_cloudwatch_logs_exports=dict(type="bool", default=True),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        purge_security_groups=dict(type="bool", default=True),
    )

    parameter_options = dict(
        apply_immediately=dict(type="bool", default=False),
        availability_zones=dict(type="list", elements="str", aliases=["zones", "az"]),
        backtrack_to=dict(),
        backtrack_window=dict(type="int"),
        backup_retention_period=dict(type="int", default=1),
        character_set_name=dict(),
        database_name=dict(aliases=["db_name"]),
        db_cluster_identifier=dict(required=True, aliases=["cluster_id", "id", "cluster_name"]),
        db_cluster_parameter_group_name=dict(),
        db_subnet_group_name=dict(),
        enable_cloudwatch_logs_exports=dict(type="list", elements="str"),
        deletion_protection=dict(type="bool"),
        global_cluster_identifier=dict(),
        enable_http_endpoint=dict(type="bool"),
        copy_tags_to_snapshot=dict(type="bool"),
        domain=dict(),
        domain_iam_role_name=dict(),
        enable_global_write_forwarding=dict(type="bool"),
        db_cluster_instance_class=dict(type="str"),
        enable_iam_database_authentication=dict(type="bool"),
        engine=dict(choices=["aurora", "aurora-mysql", "aurora-postgresql", "mysql", "postgres"]),
        engine_mode=dict(choices=["provisioned", "serverless", "parallelquery", "global", "multimaster"]),
        engine_version=dict(),
        allocated_storage=dict(type="int"),
        storage_type=dict(type="str", choices=["io1"]),
        iops=dict(type="int"),
        final_snapshot_identifier=dict(),
        force_backtrack=dict(type="bool"),
        kms_key_id=dict(),
        master_user_password=dict(aliases=["password"], no_log=True),
        master_username=dict(aliases=["username"]),
        new_db_cluster_identifier=dict(aliases=["new_cluster_id", "new_id", "new_cluster_name"]),
        option_group_name=dict(),
        port=dict(type="int"),
        preferred_backup_window=dict(aliases=["backup_window"]),
        preferred_maintenance_window=dict(aliases=["maintenance_window"]),
        remove_from_global_db=dict(type="bool"),
        replication_source_identifier=dict(aliases=["replication_src_id"]),
        restore_to_time=dict(),
        restore_type=dict(choices=["full-copy", "copy-on-write"]),
        role_arn=dict(),
        s3_bucket_name=dict(),
        s3_ingestion_role_arn=dict(),
        s3_prefix=dict(),
        serverless_v2_scaling_configuration=dict(
            type="dict",
            options=dict(
                min_capacity=dict(type="float"),
                max_capacity=dict(type="float"),
            ),
        ),
        skip_final_snapshot=dict(type="bool", default=False),
        snapshot_identifier=dict(),
        source_db_cluster_identifier=dict(),
        source_engine=dict(choices=["mysql"]),
        source_engine_version=dict(),
        source_region=dict(),
        storage_encrypted=dict(type="bool"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        use_earliest_time_on_point_in_time_unavailable=dict(type="bool"),
        use_latest_restorable_time=dict(type="bool"),
        vpc_security_group_ids=dict(type="list", elements="str"),
    )
    arg_spec.update(parameter_options)

    required_by_s3_creation_source = [
        "s3_bucket_name",
        "engine",
        "master_username",
        "master_user_password",
        "source_engine",
        "source_engine_version",
        "s3_ingestion_role_arn",
    ]

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        required_if=[
            ["creation_source", "snapshot", ["snapshot_identifier", "engine"]],
            ["creation_source", "s3", required_by_s3_creation_source],
            ["remove_from_global_db", True, ["global_cluster_identifier", "db_cluster_identifier"]],
        ],
        mutually_exclusive=[
            ["s3_bucket_name", "source_db_cluster_identifier", "snapshot_identifier"],
            ["use_latest_restorable_time", "restore_to_time"],
        ],
        supports_check_mode=True,
    )

    retry_decorator = AWSRetry.jittered_backoff(retries=10)

    try:
        client = module.client("rds", retry_decorator=retry_decorator)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    if module.params.get("engine") and module.params["engine"] in ("mysql", "postgres"):
        if module.params["state"] == "present":
            if not (
                module.params.get("allocated_storage")
                and module.params.get("iops")
                and module.params.get("db_cluster_instance_class")
            ):
                module.fail_json(
                    f"When engine={module.params['engine']} allocated_storage, iops and db_cluster_instance_class must be specified"
                )
            else:
                # Fall to default value
                if not module.params.get("storage_type"):
                    module.params["storage_type"] = "io1"

    module.params["db_cluster_identifier"] = module.params["db_cluster_identifier"].lower()
    cluster = get_cluster(module.params["db_cluster_identifier"])

    if module.params["new_db_cluster_identifier"]:
        module.params["new_db_cluster_identifier"] = module.params["new_db_cluster_identifier"].lower()

        if get_cluster(module.params["new_db_cluster_identifier"]):
            module.fail_json(
                f"A new cluster ID {module.params['new_db_cluster_identifier']} was provided but it already exists"
            )
        if not cluster:
            module.fail_json(
                f"A new cluster ID {module.params['new_db_cluster_identifier']} was provided but the cluster to be renamed does not exist"
            )

    if (
        module.params["state"] == "absent"
        and module.params["skip_final_snapshot"] is False
        and module.params["final_snapshot_identifier"] is None
    ):
        module.fail_json(
            msg="skip_final_snapshot is False but all of the following are missing: final_snapshot_identifier"
        )

    changed = False

    parameters = arg_spec_to_rds_params(dict((k, module.params[k]) for k in module.params if k in parameter_options))
    method_name, method_options_name = get_rds_method_attribute_name(cluster)

    if method_name:
        if method_name == "delete_db_cluster":
            if cluster and module.params.get("remove_from_global_db"):
                if cluster["Engine"] in ["aurora", "aurora-mysql", "aurora-postgresql"]:
                    changed = handle_remove_from_global_db(cluster)

            call_method(client, module, method_name, eval(method_options_name)(parameters))
            changed = True
        else:
            changed |= ensure_present(cluster, parameters, method_name, method_options_name)

    if not module.check_mode and module.params["new_db_cluster_identifier"] and module.params["apply_immediately"]:
        cluster_id = module.params["new_db_cluster_identifier"]
    else:
        cluster_id = module.params["db_cluster_identifier"]

    if cluster_id and get_cluster(cluster_id) and module.params.get("remove_from_global_db"):
        if cluster["Engine"] in ["aurora", "aurora-mysql", "aurora-postgresql"]:
            if changed:
                wait_for_cluster_status(client, module, cluster_id, "cluster_available")
        changed |= handle_remove_from_global_db(cluster)

    result = camel_dict_to_snake_dict(get_cluster(cluster_id))

    if result:
        result["tags"] = get_tags(client, module, result["db_cluster_arn"])

    module.exit_json(changed=changed, **result)


if __name__ == "__main__":
    main()

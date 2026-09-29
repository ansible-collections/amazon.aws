#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2017 Ansible Project
# Copyright (c) 2017, 2018 Will Thames
# Copyright (c) 2017, 2018 Michael De La Rue
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_snapshot_info
version_added: 5.0.0
short_description: obtain information about one or more RDS snapshots
description:
  - Obtain information about one or more RDS snapshots. These can be for unclustered snapshots or snapshots of clustered DBs (Aurora).
  - Aurora snapshot information may be obtained if no identifier parameters are passed or if one of the cluster parameters are passed.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  db_snapshot_identifier:
    description:
      - Name of an RDS (unclustered) snapshot.
      - Mutually exclusive with O(db_instance_identifier), O(db_cluster_identifier), O(db_cluster_snapshot_identifier).
    required: false
    aliases:
      - snapshot_name
    type: str
  db_instance_identifier:
    description:
      - RDS instance name for which to find snapshots.
      - Mutually exclusive with O(db_snapshot_identifier), O(db_cluster_identifier), O(db_cluster_snapshot_identifier).
    required: false
    type: str
  db_cluster_identifier:
    description:
      - RDS cluster name for which to find snapshots.
      - Mutually exclusive with O(db_snapshot_identifier), O(db_instance_identifier), O(db_cluster_snapshot_identifier).
    required: false
    type: str
  db_cluster_snapshot_identifier:
    description:
      - Name of an RDS cluster snapshot.
      - Mutually exclusive with O(db_instance_identifier), O(db_snapshot_identifier), O(db_cluster_identifier).
    required: false
    type: str
  snapshot_type:
    description:
      - Type of snapshot to find.
      - By default both automated and manual snapshots will be returned.
    required: false
    choices: ['automated', 'manual', 'shared', 'public']
    type: str
author:
  - "Will Thames (@willthames)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Get information about an snapshot
  amazon.aws.rds_snapshot_info:
    db_snapshot_identifier: snapshot_name
  register: new_database_info

- name: Get all RDS snapshots for an RDS instance
  amazon.aws.rds_snapshot_info:
    db_instance_identifier: helloworld-rds-master
"""

RETURN = r"""
snapshots:
  description: List of non-clustered snapshots.
  returned: When cluster parameters are not passed.
  type: complex
  contains:
    allocated_storage:
      description: The allocated storage size in gibibytes (GiB).
      returned: always
      type: int
      sample: 10
    availability_zone:
      description: The name of the Availability Zone the DB instance was located in at the time of the DB snapshot.
      returned: always
      type: str
      sample: "us-west-2b"
    db_instance_identifier:
      description: The DB instance identifier of the DB instance this DB snapshot was created from.
      returned: always
      type: str
      sample: "hello-world-rds"
    db_snapshot_arn:
      description: The Amazon Resource Name (ARN) for the DB snapshot.
      returned: always
      type: str
      sample: "arn:aws:rds:us-west-2:123456789012:snapshot:rds:hello-world-rds-us1-2018-05-16-04-03"
    db_snapshot_identifier:
      description: The identifier for the DB snapshot.
      returned: always
      type: str
      sample: "rds:hello-world-rds-us1-2018-05-16-04-03"
    dbi_resource_id:
      description: The identifier for the source DB instance, which can't be changed and which is unique to an Amazon Web Services Region.
      returned: always
      type: str
      sample: "db-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    dedicated_log_volume:
      description: Whether the DB instance has a dedicated log volume (DLV) enabled.
      returned: always
      type: bool
      sample: false
    encrypted:
      description: Whether the DB snapshot is encrypted.
      returned: always
      type: bool
      sample: true
    engine:
      description: The name of the database engine.
      returned: always
      type: str
      sample: "postgres"
    engine_version:
      description: The version of the database engine.
      returned: always
      type: str
      sample: "9.5.10"
    iam_database_authentication_enabled:
      description: Whether mapping of Amazon Web Services Identity and Access Management (IAM) accounts to database accounts is enabled.
      returned: always
      type: bool
      sample: false
    instance_create_time:
      description: The time when the DB instance, from which the snapshot was taken, was created.
      returned: always
      type: str
      sample: "2017-10-10T04:00:07.434000+00:00"
    iops:
      description: The Provisioned IOPS (I/O operations per second) value of the DB instance at the time of the snapshot.
      returned: always
      type: int
      sample: 3000
    kms_key_id:
      description: The Amazon Web Services KMS key identifier for the encrypted DB snapshot.
      returned: when encrypted is true
      type: str
      sample: "arn:aws:kms:us-west-2:123456789012:key/abcd1234-1234-aaaa-0000-1234567890ab"
    license_model:
      description: License model information for the restored DB instance.
      returned: always
      type: str
      sample: "postgresql-license"
    master_username:
      description: The master username for the DB snapshot.
      returned: always
      type: str
      sample: "dbadmin"
    multi_tenant:
      description: Whether the snapshot is of a DB instance using the multi-tenant configuration (TRUE) or the single-tenant configuration (FALSE).
      returned: always
      type: bool
      sample: false
    option_group_name:
      description: The option group name for the DB snapshot.
      returned: always
      type: str
      sample: "default:postgres-9-5"
    original_snapshot_create_time:
      description: The time of the CreateDBSnapshot operation. Doesn't change when the snapshot is copied.
      returned: always
      type: str
      sample: "2017-10-10T04:00:07.434000+00:00"
    percent_progress:
      description: The percentage of the estimated data that has been transferred.
      returned: always
      type: int
      sample: 100
    port:
      description: The port that the database engine was listening on at the time of the snapshot.
      returned: always
      type: int
      sample: 0
    snapshot_create_time:
      description: When the snapshot was taken.
      returned: always
      type: str
      sample: "2018-05-16T04:03:33.871000+00:00"
    snapshot_target:
      description: "Where manual snapshots are stored: Amazon Web Services Outposts or the Amazon Web Services Region."
      returned: always
      type: str
      sample: "region"
    snapshot_type:
      description: The type of the DB snapshot.
      returned: always
      type: str
      sample: "automated"
    status:
      description: The status of this DB snapshot.
      returned: always
      type: str
      sample: "available"
    storage_throughput:
      description: The storage throughput for the DB snapshot.
      returned: always
      type: int
      sample: 500
    storage_type:
      description: The storage type associated with DB snapshot.
      returned: always
      type: str
      sample: "gp2"
    tags:
      description: Tags of the snapshot.
      returned: when snapshot is not shared.
      type: complex
      contains: {}
    vpc_id:
      description: The VPC ID associated with the DB snapshot.
      returned: always
      type: str
      sample: "vpc-abcd1234"
cluster_snapshots:
  description: List of cluster snapshots.
  returned: When cluster parameters are passed.
  type: complex
  contains:
    allocated_storage:
      description: The allocated storage size in gibibytes (GiB).
      returned: always
      type: int
      sample: 1
    availability_zones:
      description: The list of Availability Zones (AZs) where instances in the DB cluster snapshot can be restored.
      returned: always
      type: list
      sample:
      - "ca-central-1a"
      - "ca-central-1b"
    cluster_create_time:
      description: The time when the DB cluster was created.
      returned: always
      type: str
      sample: "2018-05-17T00:13:40.223000+00:00"
    db_cluster_identifier:
      description: The DB cluster identifier of the DB cluster that this DB cluster snapshot was created from.
      returned: always
      type: str
      sample: "test-aurora-cluster"
    db_cluster_resource_id:
      description: The resource ID of the DB cluster that this DB cluster snapshot was created from.
      returned: always
      type: str
      sample: "cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    db_cluster_snapshot_arn:
      description: The Amazon Resource Name (ARN) for the DB cluster snapshot.6
      returned: always
      type: str
      sample: "arn:aws:rds:ca-central-1:123456789012:cluster-snapshot:test-aurora-snapshot"
    db_cluster_snapshot_identifier:
      description: The identifier for the DB cluster snapshot.
      returned: always
      type: str
      sample: "test-aurora-snapshot"
    engine:
      description: The name of the database engine for this DB cluster snapshot.
      returned: always
      type: str
      sample: "aurora"
    engine_mode:
      description: The engine mode of the database engine for this DB cluster snapshot.
      returned: always
      type: str
      sample: "provisioned"
    engine_version:
      description: The version of the database engine for this DB cluster snapshot.
      returned: always
      type: str
      sample: "5.6.10a"
    iam_database_authentication_enabled:
      description: Whether mapping of Amazon Web Services Identity and Access Management (IAM) accounts to database accounts is enabled.
      returned: always
      type: bool
      sample: false
    kms_key_id:
      description: the Amazon Web Services KMS key identifier for the encrypted DB cluster snapshot.
      returned: when storage_encrypted is true
      type: str
      sample: "arn:aws:kms:us-west-2:123456789012:key/abcd1234-1234-aaaa-0000-1234567890ab"
    license_model:
      description: The license model information for this DB cluster snapshot.
      returned: always
      type: str
      sample: "aurora"
    master_username:
      description: The master username for this DB cluster snapshot.
      returned: always
      type: str
      sample: "shertel"
    percent_progress:
      description: The percentage of the estimated data that has been transferred.
      returned: always
      type: int
      sample: 0
    port:
      description: The port that the DB cluster was listening on at the time of the snapshot.
      returned: always
      type: int
      sample: 0
    snapshot_create_time:
      description: The time when the snapshot was taken.
      returned: always
      type: str
      sample: "2018-05-17T00:23:23.731000+00:00"
    snapshot_type:
      description: The type of the DB cluster snapshot.
      returned: always
      type: str
      sample: "manual"
    status:
      description: The status of this DB cluster snapshot.
      returned: always
      type: str
      sample: "creating"
    storage_encrypted:
      description: Indicates whether the DB cluster snapshot is encrypted.
      returned: always
      type: bool
      sample: true
    tags:
      description: Tags of the snapshot.
      returned: when snapshot is not shared.
      type: complex
      contains: {}
    vpc_id:
      description: The VPC ID associated with the DB cluster snapshot.
      returned: always
      type: str
      sample: "vpc-abcd1234"
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_cluster_snapshots
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_snapshots
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def common_snapshot_info(
    client, module: AnsibleAWSModule, describe_snapshots_method: Callable, params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    try:
        results = describe_snapshots_method(client, **params)
    except AnsibleRDSError as e:
        module.fail_json_aws(e, "Failed to get snapshot information")

    for snapshot in results:
        if snapshot["SnapshotType"] != "shared":
            snapshot["Tags"] = boto3_tag_list_to_ansible_dict(snapshot.pop("Tags", []))

    return [camel_dict_to_snake_dict(snapshot, ignore_list=["Tags"]) for snapshot in results]


def cluster_snapshot_info(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    snapshot_id = module.params.get("db_cluster_snapshot_identifier")
    snapshot_type = module.params.get("snapshot_type")
    instance_name = module.params.get("db_cluster_identifier")

    params = dict()
    if snapshot_id:
        params["DBClusterSnapshotIdentifier"] = snapshot_id
    if instance_name:
        params["DBClusterIdentifier"] = instance_name
    if snapshot_type:
        params["SnapshotType"] = snapshot_type
        if snapshot_type == "public":
            params["IncludePublic"] = True
        elif snapshot_type == "shared":
            params["IncludeShared"] = True

    return common_snapshot_info(client, module, describe_db_cluster_snapshots, params)


def instance_snapshot_info(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    snapshot_id = module.params.get("db_snapshot_identifier")
    snapshot_type = module.params.get("snapshot_type")
    instance_name = module.params.get("db_instance_identifier")

    params = dict()
    if snapshot_id:
        params["DBSnapshotIdentifier"] = snapshot_id
    if instance_name:
        params["DBInstanceIdentifier"] = instance_name
    if snapshot_type:
        params["SnapshotType"] = snapshot_type
        if snapshot_type == "public":
            params["IncludePublic"] = True
        elif snapshot_type == "shared":
            params["IncludeShared"] = True

    return common_snapshot_info(client, module, describe_db_snapshots, params)


def main():
    argument_spec = dict(
        db_snapshot_identifier=dict(aliases=["snapshot_name"]),
        db_instance_identifier=dict(),
        db_cluster_identifier=dict(),
        db_cluster_snapshot_identifier=dict(),
        snapshot_type=dict(choices=["automated", "manual", "shared", "public"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            [
                "db_snapshot_identifier",
                "db_instance_identifier",
                "db_cluster_identifier",
                "db_cluster_snapshot_identifier",
            ]
        ],
    )

    client = module.client("rds")
    results = dict()
    if not module.params["db_cluster_identifier"] and not module.params["db_cluster_snapshot_identifier"]:
        results["snapshots"] = instance_snapshot_info(client, module)
    if not module.params["db_snapshot_identifier"] and not module.params["db_instance_identifier"]:
        results["cluster_snapshots"] = cluster_snapshot_info(client, module)

    module.exit_json(changed=False, **results)


if __name__ == "__main__":
    main()

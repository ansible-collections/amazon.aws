#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Ansible Project
# Copyright (c) 2021 Alina Buzachis (@alinabuzachis)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_cluster_snapshot
version_added: 5.0.0
short_description: Manage Amazon RDS snapshots of DB clusters
description:
  - Create, modify and delete RDS snapshots of DB clusters.
  - This module was originally added to C(community.aws) in release 4.0.0.
options:
  state:
    description:
      - Specify the desired state of the snapshot.
    default: present
    choices: [ 'present', 'absent']
    type: str
  db_cluster_snapshot_identifier:
    description:
      - The identifier of the DB cluster snapshot.
    required: true
    aliases:
      - snapshot_id
      - id
      - snapshot_name
    type: str
  db_cluster_identifier:
    description:
      - The identifier of the DB cluster to create a snapshot for.
      - Required when O(state=present).
    aliases:
      - cluster_id
      - cluster_name
    type: str
  source_db_cluster_snapshot_identifier:
     description:
      - The identifier of the DB cluster snapshot to copy.
      - If the source snapshot is in the same AWS region as the copy, specify the snapshot's identifier.
      - If the source snapshot is in a different AWS region as the copy, specify the snapshot's ARN.
     aliases:
      - source_id
      - source_snapshot_id
     type: str
  source_region:
    description:
      - The region that contains the snapshot to be copied.
    type: str
  copy_tags:
    description:
      - Whether to copy all tags from O(source_db_cluster_snapshot_identifier) to O(db_cluster_snapshot_identifier).
    type: bool
    default: false
  wait:
    description:
      - Whether or not to wait for snapshot creation or deletion.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 300
    type: int
notes:
  - Retrieve the information about a specific DB cluster or list the DB cluster snapshots for a specific DB cluster
    can de done using M(community.aws.rds_snapshot_info).
author:
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create a DB cluster snapshot
  amazon.aws.rds_cluster_snapshot:
    db_cluster_identifier: "{{ cluster_id }}"
    db_cluster_snapshot_identifier: new-cluster-snapshot

- name: Delete a DB cluster snapshot
  amazon.aws.rds_cluster_snapshot:
    db_cluster_snapshot_identifier: new-cluster-snapshot
    state: absent

- name: Copy snapshot from a different region and copy its tags
  amazon.aws.rds_cluster_snapshot:
    id: new-database-snapshot-copy
    region: us-east-1
    source_id: "{{ snapshot.db_snapshot_arn }}"
    source_region: us-east-2
    copy_tags: true
"""

RETURN = r"""
availability_zone:
  description: Availability zone of the database from which the snapshot was created.
  returned: always
  type: str
  sample: "us-west-2a"
allocated_storage:
  description: The allocated storage size of the DB cluster snapshot in gibibytes (GiB).
  returned: always
  type: int
  sample: 0
cluster_create_time:
  description: The time when the DB cluster was created, in Universal Coordinated Time (UTC).
  returned: always
  type: str
  sample: "2024-07-01T05:27:53.478000+00:00"
db_cluster_snapshot_identifier:
  description: Specifies the identifier for the DB cluster snapshot.
  returned: always
  type: str
  sample: "ansible-test-16638696-test-snapshot"
db_cluster_identifier:
  description: Specifies the DB cluster identifier of the DB cluster that this DB cluster snapshot was created from.
  returned: always
  type: str
  sample: "ansible-test-16638696"
snapshot_create_time:
  description: Provides the time when the snapshot was taken, in Universal Coordinated Time (UTC).
  returned: always
  type: str
  sample: "2019-06-15T10:46:23.776000+00:00"
engine:
  description: Specifies the name of the database engine for this DB cluster snapshot.
  returned: always
  type: str
  sample: "aurora"
engine_mode:
  description: Provides the engine mode of the database engine for this DB cluster snapshot.
  returned: always
  type: str
  sample: "5.6.mysql_aurora.1.22.5"
status:
  description: Specifies the status of this DB cluster snapshot.
  returned: always
  type: str
  sample: available
port:
  description: Port on which the database is listening.
  returned: always
  type: int
  sample: 3306
vpc_id:
  description: ID of the VPC in which the DB lives.
  returned: always
  type: str
  sample: vpc-09ff232e222710ae0
master_username:
  description: Provides the master username for this DB cluster snapshot.
  returned: always
  type: str
  sample: "test"
engine_version:
  description: Version of the cluster from which the snapshot was created.
  returned: always
  type: str
  sample: "5.6.mysql_aurora.1.22.5"
license_model:
  description: Provides the license model information for this DB cluster snapshot.
  returned: always
  type: str
  sample: "general-public-license"
snapshot_type:
  description: How the snapshot was created (always manual for this module!).
  returned: always
  type: str
  sample: "manual"
percent_progress:
  description: Specifies the percentage of the estimated data that has been transferred.
  returned: always
  type: int
  sample: 100
storage_encrypted:
  description: Specifies whether the DB cluster snapshot is encrypted.
  returned: always
  type: bool
  sample: false
kms_key_id:
  description: The Amazon Web Services KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the KMS key.
  returned: always
  type: str
db_cluster_snapshot_arn:
  description: Amazon Resource Name for the snapshot.
  returned: always
  type: str
  sample: "arn:aws:rds:us-west-2:123456789012:snapshot:ansible-test-16638696-test-snapshot"
source_db_cluster_snapshot_arn:
  description: If the DB cluster snapshot was copied from a source DB cluster snapshot, the ARN for the source DB cluster snapshot, otherwise, null.
  returned: always
  type: str
  sample: null
iam_database_authentication_enabled:
  description: Whether IAM database authentication is enabled.
  returned: always
  type: bool
  sample: false
tag_list:
  description: A list of tags.
  returned: always
  type: list
  sample: [
        {
            "key": "tag_one",
            "value": "ansible-test-123456789012-rds-cluster-snapshot-b One"
        }]
tags:
  description: Tags applied to the snapshot.
  returned: always
  type: dict
  sample: {
        "Tag Two": "two ansible-test-123456789012-rds-cluster-snapshot-b"
        }
"""

from typing import Any
from typing import Dict

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import arg_spec_to_rds_params
from ansible_collections.amazon.aws.plugins.module_utils.rds import call_method
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import format_rds_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_snapshot


def ensure_snapshot_absent(client, module: AnsibleAWSModule) -> None:
    snapshot_id = module.params.get("db_cluster_snapshot_identifier")
    changed = False

    try:
        snapshot = get_snapshot(client, snapshot_id, "cluster")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")
    if snapshot and snapshot["Status"] != "deleting":
        snapshot, changed = call_method(
            client, module, "delete_db_cluster_snapshot", {"DBClusterSnapshotIdentifier": snapshot_id}
        )

    module.exit_json(changed=changed)


def copy_snapshot(client, module: AnsibleAWSModule, params: Dict[str, Any]) -> bool:
    changed = False
    snapshot_id = module.params.get("db_cluster_snapshot_identifier")

    try:
        snapshot = get_snapshot(client, snapshot_id, "cluster")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")
    if not snapshot:
        params["TargetDBClusterSnapshotIdentifier"] = snapshot_id
        method_params = format_rds_client_method_parameters(
            client, module, params, "copy_db_cluster_snapshot", format_tags=True
        )
        _result, changed = call_method(client, module, "copy_db_cluster_snapshot", method_params)

    return changed


def ensure_snapshot_present(client, module: AnsibleAWSModule, params: Dict[str, Any]) -> None:
    source_id = module.params.get("source_db_cluster_snapshot_identifier")
    snapshot_id = module.params.get("db_cluster_snapshot_identifier")
    changed = False

    try:
        snapshot = get_snapshot(client, snapshot_id, "cluster")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")

    # Copy snapshot
    if source_id:
        changed |= copy_snapshot(client, module, params)

    # Create snapshot
    elif not snapshot:
        changed |= create_snapshot(client, module, params)

    # Snapshot exists and we're not creating a copy - modify exising snapshot
    else:
        changed |= modify_snapshot(client, module)

    try:
        snapshot = get_snapshot(client, snapshot_id, "cluster")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(snapshot, ignore_list=["Tags"]))


def create_snapshot(client, module: AnsibleAWSModule, params: Dict[str, Any]) -> bool:
    method_params = format_rds_client_method_parameters(
        client, module, params, "create_db_cluster_snapshot", format_tags=True
    )
    _snapshot, changed = call_method(client, module, "create_db_cluster_snapshot", method_params)

    return changed


def modify_snapshot(client, module: AnsibleAWSModule) -> bool:
    # TODO - add other modifications aside from purely tags
    changed = False
    snapshot_id = module.params.get("db_cluster_snapshot_identifier")

    try:
        snapshot = get_snapshot(client, snapshot_id, "cluster")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")

    if module.params.get("tags"):
        changed |= ensure_tags(
            client,
            module,
            snapshot["DBClusterSnapshotArn"],
            snapshot["Tags"],
            module.params["tags"],
            module.params["purge_tags"],
        )

    return changed


def main():
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        db_cluster_snapshot_identifier=dict(type="str", aliases=["id", "snapshot_id", "snapshot_name"], required=True),
        db_cluster_identifier=dict(type="str", aliases=["cluster_id", "cluster_name"]),
        source_db_cluster_snapshot_identifier=dict(type="str", aliases=["source_id", "source_snapshot_id"]),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=300),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        copy_tags=dict(type="bool", default=False),
        source_region=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    client = module.client("rds")
    state = module.params.get("state")

    if state == "absent":
        ensure_snapshot_absent(client, module)
    elif state == "present":
        params = arg_spec_to_rds_params(dict((k, module.params[k]) for k in module.params if k in argument_spec))
        ensure_snapshot_present(client, module, params)


if __name__ == "__main__":
    main()

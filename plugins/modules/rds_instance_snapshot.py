#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Ansible Project
# Copyright (c) 2017, 2018, 2019 Will Thames
# Copyright (c) 2017, 2018 Michael De La Rue
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_instance_snapshot
version_added: 5.0.0
short_description: Manage Amazon RDS instance snapshots
description:
  - Creates or deletes RDS snapshots.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  state:
    description:
      - Specify the desired state of the snapshot.
    default: present
    choices: [ 'present', 'absent']
    type: str
  db_snapshot_identifier:
    description:
      - The snapshot to manage.
    required: true
    aliases:
      - id
      - snapshot_id
    type: str
  db_instance_identifier:
    description:
      - Database instance identifier. Required when creating a snapshot.
    aliases:
      - instance_id
    type: str
  source_db_snapshot_identifier:
    description:
      - The identifier of the source DB snapshot.
      - Required when copying a snapshot.
      - If the source snapshot is in the same AWS region as the copy, specify the snapshot's identifier.
      - If the source snapshot is in a different AWS region as the copy, specify the snapshot's ARN.
    aliases:
      - source_id
      - source_snapshot_id
    type: str
    version_added: 3.3.0
    version_added_collection: community.aws
  source_region:
    description:
      - The region that contains the snapshot to be copied.
    type: str
    version_added: 3.3.0
    version_added_collection: community.aws
  copy_tags:
    description:
      - Whether to copy all tags from O(source_db_snapshot_identifier) to O(db_instance_identifier).
    type: bool
    default: false
    version_added: 3.3.0
    version_added_collection: community.aws
  wait:
    description:
      - Whether or not to wait for snapshot creation or deletion.
    type: bool
    default: false
  wait_timeout:
    description:
      - how long before wait gives up, in seconds.
    default: 300
    type: int
author:
  - "Will Thames (@willthames)"
  - "Michael De La Rue (@mikedlr)"
  - "Alina Buzachis (@alinabuzachis)"
  - "Joseph Torcasso (@jatorcasso)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create snapshot
  amazon.aws.rds_instance_snapshot:
    db_instance_identifier: new-database
    db_snapshot_identifier: new-database-snapshot
  register: snapshot

- name: Copy snapshot from a different region and copy its tags
  amazon.aws.rds_instance_snapshot:
    id: new-database-snapshot-copy
    region: us-east-1
    source_id: "{{ snapshot.db_snapshot_arn }}"
    source_region: us-east-2
    copy_tags: true

- name: Delete snapshot
  amazon.aws.rds_instance_snapshot:
    db_snapshot_identifier: new-database-snapshot
    state: absent
"""

RETURN = r"""
allocated_storage:
  description: How much storage is allocated in GB.
  returned: always
  type: int
  sample: 20
availability_zone:
  description: Availability zone of the database from which the snapshot was created.
  returned: always
  type: str
  sample: us-west-2a
db_instance_identifier:
  description: Database from which the snapshot was created.
  returned: always
  type: str
  sample: ansible-test-16638696
db_snapshot_arn:
  description: Amazon Resource Name for the snapshot.
  returned: always
  type: str
  sample: arn:aws:rds:us-west-2:123456789012:snapshot:ansible-test-16638696-test-snapshot
db_snapshot_identifier:
  description: Name of the snapshot.
  returned: always
  type: str
  sample: ansible-test-16638696-test-snapshot
dbi_resource_id:
  description: The identifier for the source DB instance, which can't be changed and which is unique to an AWS Region.
  returned: always
  type: str
  sample: db-MM4P2U35RQRAMWD3QDOXWPZP4U
encrypted:
  description: Whether the snapshot is encrypted.
  returned: always
  type: bool
  sample: false
engine:
  description: Engine of the database from which the snapshot was created.
  returned: always
  type: str
  sample: mariadb
engine_version:
  description: Version of the database from which the snapshot was created.
  returned: always
  type: str
  sample: 10.2.21
iam_database_authentication_enabled:
  description: Whether IAM database authentication is enabled.
  returned: always
  type: bool
  sample: false
instance_create_time:
  description: Creation time of the instance from which the snapshot was created.
  returned: always
  type: str
  sample: '2019-06-15T10:15:56.221000+00:00'
license_model:
  description: License model of the database.
  returned: always
  type: str
  sample: general-public-license
master_username:
  description: Master username of the database.
  returned: always
  type: str
  sample: test
option_group_name:
  description: Option group of the database.
  returned: always
  type: str
  sample: default:mariadb-10-2
percent_progress:
  description: How much progress has been made taking the snapshot. Will be 100 for an available snapshot.
  returned: always
  type: int
  sample: 100
port:
  description: Port on which the database is listening.
  returned: always
  type: int
  sample: 3306
processor_features:
  description: List of processor features of the database.
  returned: always
  type: list
  sample: []
source_db_snapshot_identifier:
  description: The DB snapshot ARN that the DB snapshot was copied from.
  returned: when snapshot is a copy
  type: str
  sample: arn:aws:rds:us-west-2:123456789012:snapshot:ansible-test-16638696-test-snapshot-source
  version_added: 3.3.0
  version_added_collection: community.aws
snapshot_create_time:
  description: Creation time of the snapshot.
  returned: always
  type: str
  sample: '2019-06-15T10:46:23.776000+00:00'
snapshot_type:
  description: How the snapshot was created (always manual for this module!).
  returned: always
  type: str
  sample: manual
status:
  description: Status of the snapshot.
  returned: always
  type: str
  sample: available
storage_type:
  description: Storage type of the database.
  returned: always
  type: str
  sample: gp2
tags:
  description: Tags applied to the snapshot.
  returned: always
  type: complex
  contains: {}
vpc_id:
  description: ID of the VPC in which the DB lives.
  returned: always
  type: str
  sample: vpc-09ff232e222710ae0
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
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def ensure_snapshot_absent(client, module: AnsibleAWSModule) -> None:
    snapshot_id = module.params.get("db_snapshot_identifier")
    params = {"DBSnapshotIdentifier": snapshot_id}
    changed = False

    try:
        snapshot = get_snapshot(client, snapshot_id, "instance")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")
    if not snapshot:
        module.exit_json(changed=changed)
    elif snapshot and snapshot["Status"] != "deleting":
        snapshot, changed = call_method(client, module, "delete_db_snapshot", params)

    module.exit_json(changed=changed)


def ensure_snapshot_present(client, module: AnsibleAWSModule, params: Dict[str, Any]) -> None:
    source_id = module.params.get("source_db_snapshot_identifier")
    snapshot_id = module.params.get("db_snapshot_identifier")
    changed = False

    try:
        snapshot = get_snapshot(client, snapshot_id, "instance")
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
        snapshot = get_snapshot(client, snapshot_id, "instance")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(snapshot, ignore_list=["Tags"]))


def create_snapshot(client, module: AnsibleAWSModule, params: Dict[str, Any]) -> bool:
    method_params = format_rds_client_method_parameters(client, module, params, "create_db_snapshot", format_tags=True)
    _snapshot, changed = call_method(client, module, "create_db_snapshot", method_params)

    return changed


def copy_snapshot(client, module: AnsibleAWSModule, params: Dict[str, Any]) -> bool:
    changed = False
    snapshot_id = module.params.get("db_snapshot_identifier")
    try:
        snapshot = get_snapshot(client, snapshot_id, "instance")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")

    if not snapshot:
        params["TargetDBSnapshotIdentifier"] = module.params["db_snapshot_identifier"]
        method_params = format_rds_client_method_parameters(
            client, module, params, "copy_db_snapshot", format_tags=True
        )
        _result, changed = call_method(client, module, "copy_db_snapshot", method_params)

    return changed


def modify_snapshot(client, module: AnsibleAWSModule) -> bool:
    # TODO - add other modifications aside from purely tags
    changed = False
    snapshot_id = module.params.get("db_snapshot_identifier")
    try:
        snapshot = get_snapshot(client, snapshot_id, "instance")
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Failed to get snapshot: {snapshot_id}")

    if module.params.get("tags"):
        changed |= ensure_tags(
            client,
            module,
            snapshot["DBSnapshotArn"],
            snapshot["Tags"],
            module.params["tags"],
            module.params["purge_tags"],
        )

    return changed


def main():
    argument_spec = dict(
        state=dict(choices=["present", "absent"], default="present"),
        db_snapshot_identifier=dict(aliases=["id", "snapshot_id"], required=True),
        db_instance_identifier=dict(aliases=["instance_id"]),
        source_db_snapshot_identifier=dict(aliases=["source_id", "source_snapshot_id"]),
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
    client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")
    if state == "absent":
        ensure_snapshot_absent(client, module)

    elif state == "present":
        params = arg_spec_to_rds_params(dict((k, module.params[k]) for k in module.params if k in argument_spec))
        ensure_snapshot_present(client, module, params)


if __name__ == "__main__":
    main()

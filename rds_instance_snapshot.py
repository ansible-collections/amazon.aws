#!/usr/bin/python
# Copyright (c) 2014 Ansible Project
# Copyright (c) 2017, 2018, 2019 Will Thames
# Copyright (c) 2017, 2018 Michael De La Rue
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: rds_instance_snapshot
version_added: 1.0.0
short_description: Manage Amazon RDS instance snapshots
description:
     - Creates or deletes RDS snapshots.
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
  source_region:
    description:
      - The region that contains the snapshot to be copied.
    type: str
    version_added: 3.3.0
  copy_tags:
    description:
      - Whether to copy all tags from I(source_db_snapshot_identifier) to I(db_instance_identifier).
    type: bool
    default: False
    version_added: 3.3.0
  wait:
    description:
      - Whether or not to wait for snapshot creation or deletion.
    type: bool
    default: False
  wait_timeout:
    description:
      - how long before wait gives up, in seconds.
    default: 300
    type: int
  tags:
    description:
      - tags dict to apply to a snapshot.
    type: dict
  purge_tags:
    description:
      - whether to remove tags not present in the I(tags) parameter.
    default: True
    type: bool
author:
    - "Will Thames (@willthames)"
    - "Michael De La Rue (@mikedlr)"
    - "Alina Buzachis (@alinabuzachis)"
    - "Joseph Torcasso (@jatorcasso)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
- name: Create snapshot
  community.aws.rds_instance_snapshot:
    db_instance_identifier: new-database
    db_snapshot_identifier: new-database-snapshot
  register: snapshot

- name: Copy snapshot from a different region and copy its tags
  community.aws.rds_instance_snapshot:
    id: new-database-snapshot-copy
    region: us-east-1
    source_id: "{{ snapshot.db_snapshot_arn }}"
    source_region: us-east-2
    copy_tags: yes

- name: Delete snapshot
  community.aws.rds_instance_snapshot:
    db_snapshot_identifier: new-database-snapshot
    state: absent
'''

RETURN = r'''
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
'''

try:
    import botocore
except ImportError:
    pass  # protected by AnsibleAWSModule

# import module snippets
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.rds import arg_spec_to_rds_params
from ansible_collections.amazon.aws.plugins.module_utils.rds import call_method
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_rds_method_attribute
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags


def get_snapshot(snapshot_id):
    try:
        snapshot = client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)['DBSnapshots'][0]
        snapshot['Tags'] = get_tags(client, module, snapshot['DBSnapshotArn'])
    except is_boto3_error_code("DBSnapshotNotFound"):
        return {}
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't get snapshot {0}".format(snapshot_id))
    return snapshot


def get_parameters(parameters, method_name):
    if method_name == 'copy_db_snapshot':
        parameters['TargetDBSnapshotIdentifier'] = module.params['db_snapshot_identifier']

    required_options = get_boto3_client_method_parameters(client, method_name, required=True)
    if any(parameters.get(k) is None for k in required_options):
        module.fail_json(msg='To {0} requires the parameters: {1}'.format(
            get_rds_method_attribute(method_name, module).operation_description, required_options))
    options = get_boto3_client_method_parameters(client, method_name)
    parameters = dict((k, v) for k, v in parameters.items() if k in options and v is not None)

    return parameters


def ensure_snapshot_absent():
    snapshot_name = module.params.get("db_snapshot_identifier")
    params = {"DBSnapshotIdentifier": snapshot_name}
    changed = False

    snapshot = get_snapshot(snapshot_name)
    if not snapshot:
        module.exit_json(changed=changed)
    elif snapshot and snapshot["Status"] != "deleting":
        snapshot, changed = call_method(client, module, "delete_db_snapshot", params)

    module.exit_json(changed=changed)


def ensure_snapshot_present(params):
    source_id = module.params.get('source_db_snapshot_identifier')
    snapshot_name = module.params.get('db_snapshot_identifier')
    changed = False
    snapshot = get_snapshot(snapshot_name)

    # Copy snapshot
    if source_id:
        changed |= copy_snapshot(params)

    # Create snapshot
    elif not snapshot:
        changed |= create_snapshot(params)

    # Snapshot exists and we're not creating a copy - modify exising snapshot
    else:
        changed |= modify_snapshot()

    snapshot = get_snapshot(snapshot_name)
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(snapshot, ignore_list=['Tags']))


def create_snapshot(params):
    method_params = get_parameters(params, 'create_db_snapshot')
    if method_params.get('Tags'):
        method_params['Tags'] = ansible_dict_to_boto3_tag_list(method_params['Tags'])
    snapshot, changed = call_method(client, module, 'create_db_snapshot', method_params)

    return changed


def copy_snapshot(params):
    changed = False
    snapshot_id = module.params.get('db_snapshot_identifier')
    snapshot = get_snapshot(snapshot_id)

    if not snapshot:
        method_params = get_parameters(params, 'copy_db_snapshot')
        if method_params.get('Tags'):
            method_params['Tags'] = ansible_dict_to_boto3_tag_list(method_params['Tags'])
        result, changed = call_method(client, module, 'copy_db_snapshot', method_params)

    return changed


def modify_snapshot():
    # TODO - add other modifications aside from purely tags
    changed = False
    snapshot_id = module.params.get('db_snapshot_identifier')
    snapshot = get_snapshot(snapshot_id)

    if module.params.get('tags'):
        changed |= ensure_tags(client, module, snapshot['DBSnapshotArn'], snapshot['Tags'], module.params['tags'], module.params['purge_tags'])

    return changed


def main():
    global client
    global module

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        db_snapshot_identifier=dict(aliases=['id', 'snapshot_id'], required=True),
        db_instance_identifier=dict(aliases=['instance_id']),
        source_db_snapshot_identifier=dict(aliases=['source_id', 'source_snapshot_id']),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=300),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=True),
        copy_tags=dict(type='bool', default=False),
        source_region=dict(type='str'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    retry_decorator = AWSRetry.jittered_backoff(retries=10)
    try:
        client = module.client('rds', retry_decorator=retry_decorator)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    state = module.params.get("state")
    if state == 'absent':
        ensure_snapshot_absent()

    elif state == 'present':
        params = arg_spec_to_rds_params(dict((k, module.params[k]) for k in module.params if k in argument_spec))
        ensure_snapshot_present(params)


if __name__ == '__main__':
    main()

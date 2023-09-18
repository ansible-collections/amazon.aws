#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: dynamodb_table
version_added: 1.0.0
short_description: Create, update or delete AWS Dynamo DB tables
description:
  - Create or delete AWS Dynamo DB tables.
  - Can update the provisioned throughput on existing tables.
  - Returns the status of the specified table.
author: Alan Loi (@loia)
requirements:
  - "boto >= 2.37.0"
  - "boto3 >= 1.4.4 (for tagging)"
options:
  state:
    description:
      - Create or delete the table.
    choices: ['present', 'absent']
    default: 'present'
    type: str
  name:
    description:
      - Name of the table.
    required: true
    type: str
  hash_key_name:
    description:
      - Name of the hash key.
      - Required when C(state=present).
    type: str
  hash_key_type:
    description:
      - Type of the hash key.
    choices: ['STRING', 'NUMBER', 'BINARY']
    default: 'STRING'
    type: str
  range_key_name:
    description:
      - Name of the range key.
    type: str
  range_key_type:
    description:
      - Type of the range key.
    choices: ['STRING', 'NUMBER', 'BINARY']
    default: 'STRING'
    type: str
  read_capacity:
    description:
      - Read throughput capacity (units) to provision.
    default: 1
    type: int
  write_capacity:
    description:
      - Write throughput capacity (units) to provision.
    default: 1
    type: int
  indexes:
    description:
      - list of dictionaries describing indexes to add to the table. global indexes can be updated. local indexes don't support updates or have throughput.
      - "required options: ['name', 'type', 'hash_key_name']"
      - "other options: ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']"
    suboptions:
      name:
        description: The name of the index.
        type: str
        required: true
      type:
        description:
          - The type of index.
          - "Valid types: C(all), C(global_all), C(global_include), C(global_keys_only), C(include), C(keys_only)"
        type: str
        required: true
      hash_key_name:
        description: The name of the hash-based key.
        required: true
        type: str
      hash_key_type:
        description: The type of the hash-based key.
        type: str
      range_key_name:
        description: The name of the range-based key.
        type: str
      range_key_type:
        type: str
        description: The type of the range-based key.
      includes:
        type: list
        description: A list of fields to include when using C(global_include) or C(include) indexes.
      read_capacity:
        description:
          - Read throughput capacity (units) to provision for the index.
        type: int
      write_capacity:
        description:
          - Write throughput capacity (units) to provision for the index.
        type: int
    default: []
    type: list
    elements: dict
  tags:
    description:
      - A hash/dictionary of tags to add to the new instance or for starting/stopping instance by tag.
      - 'For example: C({"key":"value"}) and C({"key":"value","key2":"value2"})'
    type: dict
  wait_for_active_timeout:
    description:
      - how long before wait gives up, in seconds. only used when tags is set
    default: 60
    type: int
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
- name: Create dynamo table with hash and range primary key
  community.aws.dynamodb_table:
    name: my-table
    region: us-east-1
    hash_key_name: id
    hash_key_type: STRING
    range_key_name: create_time
    range_key_type: NUMBER
    read_capacity: 2
    write_capacity: 2
    tags:
      tag_name: tag_value

- name: Update capacity on existing dynamo table
  community.aws.dynamodb_table:
    name: my-table
    region: us-east-1
    read_capacity: 10
    write_capacity: 10

- name: set index on existing dynamo table
  community.aws.dynamodb_table:
    name: my-table
    region: us-east-1
    indexes:
      - name: NamedIndex
        type: global_include
        hash_key_name: id
        range_key_name: create_time
        includes:
          - other_field
          - other_field2
        read_capacity: 10
        write_capacity: 10

- name: Delete dynamo table
  community.aws.dynamodb_table:
    name: my-table
    region: us-east-1
    state: absent
'''

RETURN = r'''
table_status:
    description: The current status of the table.
    returned: success
    type: str
    sample: ACTIVE
'''

import time
import traceback

try:
    import boto
    import boto.dynamodb2
    from boto.dynamodb2.table import Table
    from boto.dynamodb2.fields import HashKey, RangeKey, AllIndex, GlobalAllIndex, GlobalIncludeIndex, GlobalKeysOnlyIndex, IncludeIndex, KeysOnlyIndex
    from boto.dynamodb2.types import STRING, NUMBER, BINARY
    from boto.exception import BotoServerError, NoAuthHandlerFound, JSONResponseError
    from boto.dynamodb2.exceptions import ValidationException
    DYNAMO_TYPE_MAP = {
        'STRING': STRING,
        'NUMBER': NUMBER,
        'BINARY': BINARY
    }
    # Boto 2 is mandatory, Boto3 is only needed for tagging
    import botocore
except ImportError:
    pass  # Handled by ec2.HAS_BOTO and ec2.HAS_BOTO3

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import connect_to_aws
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO3


DYNAMO_TYPE_DEFAULT = 'STRING'
INDEX_REQUIRED_OPTIONS = ['name', 'type', 'hash_key_name']
INDEX_OPTIONS = INDEX_REQUIRED_OPTIONS + ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']
INDEX_TYPE_OPTIONS = ['all', 'global_all', 'global_include', 'global_keys_only', 'include', 'keys_only']


def create_or_update_dynamo_table(connection, module, boto3_dynamodb=None, boto3_sts=None, region=None):
    table_name = module.params.get('name')
    hash_key_name = module.params.get('hash_key_name')
    hash_key_type = module.params.get('hash_key_type')
    range_key_name = module.params.get('range_key_name')
    range_key_type = module.params.get('range_key_type')
    read_capacity = module.params.get('read_capacity')
    write_capacity = module.params.get('write_capacity')
    all_indexes = module.params.get('indexes')
    tags = module.params.get('tags')
    wait_for_active_timeout = module.params.get('wait_for_active_timeout')

    for index in all_indexes:
        validate_index(index, module)

    schema = get_schema_param(hash_key_name, hash_key_type, range_key_name, range_key_type)

    throughput = {
        'read': read_capacity,
        'write': write_capacity
    }

    indexes, global_indexes = get_indexes(all_indexes)

    result = dict(
        region=region,
        table_name=table_name,
        hash_key_name=hash_key_name,
        hash_key_type=hash_key_type,
        range_key_name=range_key_name,
        range_key_type=range_key_type,
        read_capacity=read_capacity,
        write_capacity=write_capacity,
        indexes=all_indexes,
    )

    try:
        table = Table(table_name, connection=connection)

        if dynamo_table_exists(table):
            result['changed'] = update_dynamo_table(table, throughput=throughput, check_mode=module.check_mode, global_indexes=global_indexes)
        else:
            if not module.check_mode:
                Table.create(table_name, connection=connection, schema=schema, throughput=throughput, indexes=indexes, global_indexes=global_indexes)
            result['changed'] = True

        if not module.check_mode:
            result['table_status'] = table.describe()['Table']['TableStatus']

        if tags:
            # only tables which are active can be tagged
            wait_until_table_active(module, table, wait_for_active_timeout)
            account_id = get_account_id(boto3_sts)
            boto3_dynamodb.tag_resource(
                ResourceArn='arn:aws:dynamodb:' +
                region +
                ':' +
                account_id +
                ':table/' +
                table_name,
                Tags=ansible_dict_to_boto3_tag_list(tags))
            result['tags'] = tags

    except BotoServerError:
        result['msg'] = 'Failed to create/update dynamo table due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def get_account_id(boto3_sts):
    return boto3_sts.get_caller_identity()["Account"]


def wait_until_table_active(module, table, wait_timeout):
    max_wait_time = time.time() + wait_timeout
    while (max_wait_time > time.time()) and (table.describe()['Table']['TableStatus'] != 'ACTIVE'):
        time.sleep(5)
    if max_wait_time <= time.time():
        # waiting took too long
        module.fail_json(msg="timed out waiting for table to exist")


def delete_dynamo_table(connection, module):
    table_name = module.params.get('name')

    result = dict(
        region=module.params.get('region'),
        table_name=table_name,
    )

    try:
        table = Table(table_name, connection=connection)

        if dynamo_table_exists(table):
            if not module.check_mode:
                table.delete()
            result['changed'] = True

        else:
            result['changed'] = False

    except BotoServerError:
        result['msg'] = 'Failed to delete dynamo table due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def dynamo_table_exists(table):
    try:
        table.describe()
        return True

    except JSONResponseError as e:
        if e.message and e.message.startswith('Requested resource not found'):
            return False
        else:
            raise e


def update_dynamo_table(table, throughput=None, check_mode=False, global_indexes=None):
    table.describe()  # populate table details
    throughput_changed = False
    global_indexes_changed = False
    if has_throughput_changed(table, throughput):
        if not check_mode:
            throughput_changed = table.update(throughput=throughput)
        else:
            throughput_changed = True

    removed_indexes, added_indexes, index_throughput_changes = get_changed_global_indexes(table, global_indexes)
    if removed_indexes:
        if not check_mode:
            for name, index in removed_indexes.items():
                global_indexes_changed = table.delete_global_secondary_index(name) or global_indexes_changed
        else:
            global_indexes_changed = True

    if added_indexes:
        if not check_mode:
            for name, index in added_indexes.items():
                global_indexes_changed = table.create_global_secondary_index(global_index=index) or global_indexes_changed
        else:
            global_indexes_changed = True

    if index_throughput_changes:
        if not check_mode:
            # todo: remove try once boto has https://github.com/boto/boto/pull/3447 fixed
            try:
                global_indexes_changed = table.update_global_secondary_index(global_indexes=index_throughput_changes) or global_indexes_changed
            except ValidationException:
                pass
        else:
            global_indexes_changed = True

    return throughput_changed or global_indexes_changed


def has_throughput_changed(table, new_throughput):
    if not new_throughput:
        return False

    return new_throughput['read'] != table.throughput['read'] or \
        new_throughput['write'] != table.throughput['write']


def get_schema_param(hash_key_name, hash_key_type, range_key_name, range_key_type):
    if range_key_name:
        schema = [
            HashKey(hash_key_name, DYNAMO_TYPE_MAP.get(hash_key_type, DYNAMO_TYPE_MAP[DYNAMO_TYPE_DEFAULT])),
            RangeKey(range_key_name, DYNAMO_TYPE_MAP.get(range_key_type, DYNAMO_TYPE_MAP[DYNAMO_TYPE_DEFAULT]))
        ]
    else:
        schema = [
            HashKey(hash_key_name, DYNAMO_TYPE_MAP.get(hash_key_type, DYNAMO_TYPE_MAP[DYNAMO_TYPE_DEFAULT]))
        ]
    return schema


def get_changed_global_indexes(table, global_indexes):
    table.describe()

    table_index_info = dict((index.name, index.schema()) for index in table.global_indexes)
    table_index_objects = dict((index.name, index) for index in table.global_indexes)
    set_index_info = dict((index.name, index.schema()) for index in global_indexes)
    set_index_objects = dict((index.name, index) for index in global_indexes)

    removed_indexes = dict((name, index) for name, index in table_index_info.items() if name not in set_index_info)
    added_indexes = dict((name, set_index_objects[name]) for name, index in set_index_info.items() if name not in table_index_info)
    # todo: uncomment once boto has https://github.com/boto/boto/pull/3447 fixed
    # for name, index in set_index_objects.items():
    #      if (name not in added_indexes and
    #             (index.throughput['read'] != str(table_index_objects[name].throughput['read']) or
    #              index.throughput['write'] != str(table_index_objects[name].throughput['write']))):
    #         index_throughput_changes[name] = index.throughput
    # todo: remove once boto has https://github.com/boto/boto/pull/3447 fixed
    index_throughput_changes = dict((name, index.throughput) for name, index in set_index_objects.items() if name not in added_indexes)

    return removed_indexes, added_indexes, index_throughput_changes


def validate_index(index, module):
    for key, val in index.items():
        if key not in INDEX_OPTIONS:
            module.fail_json(msg='%s is not a valid option for an index' % key)
    for required_option in INDEX_REQUIRED_OPTIONS:
        if required_option not in index:
            module.fail_json(msg='%s is a required option for an index' % required_option)
    if index['type'] not in INDEX_TYPE_OPTIONS:
        module.fail_json(msg='%s is not a valid index type, must be one of %s' % (index['type'], INDEX_TYPE_OPTIONS))


def get_indexes(all_indexes):
    indexes = []
    global_indexes = []
    for index in all_indexes:
        name = index['name']
        schema = get_schema_param(index.get('hash_key_name'), index.get('hash_key_type'), index.get('range_key_name'), index.get('range_key_type'))
        throughput = {
            'read': index.get('read_capacity', 1),
            'write': index.get('write_capacity', 1)
        }

        if index['type'] == 'all':
            indexes.append(AllIndex(name, parts=schema))

        elif index['type'] == 'global_all':
            global_indexes.append(GlobalAllIndex(name, parts=schema, throughput=throughput))

        elif index['type'] == 'global_include':
            global_indexes.append(GlobalIncludeIndex(name, parts=schema, throughput=throughput, includes=index['includes']))

        elif index['type'] == 'global_keys_only':
            global_indexes.append(GlobalKeysOnlyIndex(name, parts=schema, throughput=throughput))

        elif index['type'] == 'include':
            indexes.append(IncludeIndex(name, parts=schema, includes=index['includes']))

        elif index['type'] == 'keys_only':
            indexes.append(KeysOnlyIndex(name, parts=schema))

    return indexes, global_indexes


def main():
    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        hash_key_name=dict(type='str'),
        hash_key_type=dict(default='STRING', type='str', choices=['STRING', 'NUMBER', 'BINARY']),
        range_key_name=dict(type='str'),
        range_key_type=dict(default='STRING', type='str', choices=['STRING', 'NUMBER', 'BINARY']),
        read_capacity=dict(default=1, type='int'),
        write_capacity=dict(default=1, type='int'),
        indexes=dict(default=[], type='list', elements='dict'),
        tags=dict(type='dict'),
        wait_for_active_timeout=dict(default=60, type='int'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        check_boto3=False,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    if not HAS_BOTO3 and module.params.get('tags'):
        module.fail_json(msg='boto3 required when using tags for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg='region must be specified')

    try:
        connection = connect_to_aws(boto.dynamodb2, region, **aws_connect_params)
    except (NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))

    if module.params.get('tags'):
        try:
            boto3_dynamodb = module.client('dynamodb')
            if not hasattr(boto3_dynamodb, 'tag_resource'):
                module.fail_json(msg='boto3 connection does not have tag_resource(), likely due to using an old version')
            boto3_sts = module.client('sts')
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to connect to AWS')
    else:
        boto3_dynamodb = None
        boto3_sts = None

    state = module.params.get('state')
    if state == 'present':
        create_or_update_dynamo_table(connection, module, boto3_dynamodb, boto3_sts, region)
    elif state == 'absent':
        delete_dynamo_table(connection, module)


if __name__ == '__main__':
    main()

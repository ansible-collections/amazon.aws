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
author:
  - Alan Loi (@loia)
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
      - Required when I(state=present) and table doesn't exist.
    type: str
  hash_key_type:
    description:
      - Type of the hash key.
      - Defaults to C('STRING') when creating a new table.
    choices: ['STRING', 'NUMBER', 'BINARY']
    type: str
  range_key_name:
    description:
      - Name of the range key.
    type: str
  range_key_type:
    description:
      - Type of the range key.
      - Defaults to C('STRING') when creating a new range key.
    choices: ['STRING', 'NUMBER', 'BINARY']
    type: str
  billing_mode:
    description:
      - Controls whether provisoned pr on-demand tables are created.
    choices: ['PROVISIONED', 'PAY_PER_REQUEST']
    type: str
  read_capacity:
    description:
      - Read throughput capacity (units) to provision.
      - Defaults to C(1) when creating a new table.
    type: int
  write_capacity:
    description:
      - Write throughput capacity (units) to provision.
      - Defaults to C(1) when creating a new table.
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
        type: str
        required: true
        choices: ['all', 'global_all', 'global_include', 'global_keys_only', 'include', 'keys_only']
      hash_key_name:
        description:
          - The name of the hash-based key.
          - Required if index doesn't already exist.
          - Can not be modified once the index has been created.
        required: false
        type: str
      hash_key_type:
        description:
          - The type of the hash-based key.
          - Defaults to C('STRING') when creating a new index.
          - Can not be modified once the index has been created.
        type: str
        choices: ['STRING', 'NUMBER', 'BINARY']
      range_key_name:
        description:
          - The name of the range-based key.
          - Can not be modified once the index has been created.
        type: str
      range_key_type:
        type: str
        description:
          - The type of the range-based key.
          - Defaults to C('STRING') when creating a new index.
          - Can not be modified once the index has been created.
        choices: ['STRING', 'NUMBER', 'BINARY']
      includes:
        type: list
        description: A list of fields to include when using C(global_include) or C(include) indexes.
        elements: str
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
  table_class:
    description:
      - The class of the table.
      - Requires at least botocore version 1.23.18.
    choices: ['STANDARD', 'STANDARD_INFREQUENT_ACCESS']
    type: str
    version_added: 3.1.0
  wait_timeout:
    description:
      - How long (in seconds) to wait for creation / update / deletion to complete.
    aliases: ['wait_for_active_timeout']
    default: 300
    type: int
  wait:
    description:
      - When I(wait=True) the module will wait for up to I(wait_timeout) seconds
        for table creation or deletion to complete before returning.
    default: True
    type: bool
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
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

- name: Create pay-per-request table
  community.aws.dynamodb_table:
    name: my-table
    region: us-east-1
    hash_key_name: id
    hash_key_type: STRING
    billing_mode: PAY_PER_REQUEST

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
table:
  description: The returned table params from the describe API call.
  returned: success
  type: complex
  contains: {}
  sample: {
    "arn": "arn:aws:dynamodb:us-east-1:721066863947:table/ansible-test-table",
    "attribute_definitions": [
        {
            "attribute_name": "id",
            "attribute_type": "N"
        }
    ],
    "billing_mode": "PROVISIONED",
    "creation_date_time": "2022-02-04T13:36:01.578000+00:00",
    "id": "533b45fe-0870-4b66-9b00-d2afcfe96f19",
    "item_count": 0,
    "key_schema": [
        {
            "attribute_name": "id",
            "key_type": "HASH"
        }
    ],
    "name": "ansible-test-14482047-alinas-mbp",
    "provisioned_throughput": {
        "number_of_decreases_today": 0,
        "read_capacity_units": 1,
        "write_capacity_units": 1
    },
    "size": 0,
    "status": "ACTIVE",
    "table_arn": "arn:aws:dynamodb:us-east-1:721066863947:table/ansible-test-table",
    "table_id": "533b45fe-0870-4b66-9b00-d2afcfe96f19",
    "table_name": "ansible-test-table",
    "table_size_bytes": 0,
    "table_status": "ACTIVE",
    "tags": {}
  }
table_status:
  description: The current status of the table.
  returned: success
  type: str
  sample: ACTIVE
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags


DYNAMO_TYPE_DEFAULT = 'STRING'
INDEX_REQUIRED_OPTIONS = ['name', 'type', 'hash_key_name']
INDEX_OPTIONS = INDEX_REQUIRED_OPTIONS + ['hash_key_type', 'range_key_name', 'range_key_type', 'includes', 'read_capacity', 'write_capacity']
INDEX_TYPE_OPTIONS = ['all', 'global_all', 'global_include', 'global_keys_only', 'include', 'keys_only']
# Map in both directions
DYNAMO_TYPE_MAP_LONG = {'STRING': 'S', 'NUMBER': 'N', 'BINARY': 'B'}
DYNAMO_TYPE_MAP_SHORT = dict((v, k) for k, v in DYNAMO_TYPE_MAP_LONG.items())
KEY_TYPE_CHOICES = list(DYNAMO_TYPE_MAP_LONG.keys())


# If you try to update an index while another index is updating, it throws
# LimitExceededException/ResourceInUseException exceptions at you.  This can be
# pretty slow, so add plenty of retries...
@AWSRetry.jittered_backoff(
    retries=45, delay=5, max_delay=30,
    catch_extra_error_codes=['LimitExceededException', 'ResourceInUseException', 'ResourceNotFoundException'],
)
def _update_table_with_long_retry(**changes):
    return client.update_table(
        TableName=module.params.get('name'),
        **changes
    )


# ResourceNotFoundException is expected here if the table doesn't exist
@AWSRetry.jittered_backoff(catch_extra_error_codes=['LimitExceededException', 'ResourceInUseException'])
def _describe_table(**params):
    return client.describe_table(**params)


def wait_exists():
    table_name = module.params.get('name')
    wait_timeout = module.params.get('wait_timeout')

    delay = min(wait_timeout, 5)
    max_attempts = wait_timeout // delay

    try:
        waiter = client.get_waiter('table_exists')
        waiter.wait(
            WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts},
            TableName=table_name,
        )
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg='Timeout while waiting on table creation')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed while waiting on table creation')


def wait_not_exists():
    table_name = module.params.get('name')
    wait_timeout = module.params.get('wait_timeout')

    delay = min(wait_timeout, 5)
    max_attempts = wait_timeout // delay

    try:
        waiter = client.get_waiter('table_not_exists')
        waiter.wait(
            WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts},
            TableName=table_name,
        )
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg='Timeout while waiting on table deletion')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed while waiting on table deletion')


def _short_type_to_long(short_key):
    if not short_key:
        return None
    return DYNAMO_TYPE_MAP_SHORT.get(short_key, None)


def _long_type_to_short(long_key):
    if not long_key:
        return None
    return DYNAMO_TYPE_MAP_LONG.get(long_key, None)


def _schema_dict(key_name, key_type):
    return dict(
        AttributeName=key_name,
        KeyType=key_type,
    )


def _merge_index_params(index, current_index):
    idx = dict(current_index)
    idx.update(index)
    return idx


def _decode_primary_index(current_table):
    """
    Decodes the primary index info from the current table definition
    splitting it up into the keys we use as parameters
    """
    # The schema/attribute definitions are a list of dicts which need the same
    # treatment as boto3's tag lists
    schema = boto3_tag_list_to_ansible_dict(
        current_table.get('key_schema', []),
        # Map from 'HASH'/'RANGE' to attribute name
        tag_name_key_name='key_type',
        tag_value_key_name='attribute_name',
    )
    attributes = boto3_tag_list_to_ansible_dict(
        current_table.get('attribute_definitions', []),
        # Map from attribute name to 'S'/'N'/'B'.
        tag_name_key_name='attribute_name',
        tag_value_key_name='attribute_type',
    )

    hash_key_name = schema.get('HASH')
    hash_key_type = _short_type_to_long(attributes.get(hash_key_name, None))
    range_key_name = schema.get('RANGE', None)
    range_key_type = _short_type_to_long(attributes.get(range_key_name, None))

    return dict(
        hash_key_name=hash_key_name,
        hash_key_type=hash_key_type,
        range_key_name=range_key_name,
        range_key_type=range_key_type,
    )


def _decode_index(index_data, attributes, type_prefix=''):
    try:
        index_map = dict(
            name=index_data['index_name'],
        )

        index_data = dict(index_data)
        index_data['attribute_definitions'] = attributes

        index_map.update(_decode_primary_index(index_data))

        throughput = index_data.get('provisioned_throughput', {})
        index_map['provisioned_throughput'] = throughput
        if throughput:
            index_map['read_capacity'] = throughput.get('read_capacity_units')
            index_map['write_capacity'] = throughput.get('write_capacity_units')

        projection = index_data.get('projection', {})
        if projection:
            index_map['type'] = type_prefix + projection.get('projection_type')
            index_map['includes'] = projection.get('non_key_attributes', [])

        return index_map
    except Exception as e:
        module.fail_json_aws(e, msg='Decode failure', index_data=index_data)


def compatability_results(current_table):
    if not current_table:
        return dict()

    billing_mode = current_table.get('billing_mode')

    primary_indexes = _decode_primary_index(current_table)

    hash_key_name = primary_indexes.get('hash_key_name')
    hash_key_type = primary_indexes.get('hash_key_type')
    range_key_name = primary_indexes.get('range_key_name')
    range_key_type = primary_indexes.get('range_key_type')

    indexes = list()
    global_indexes = current_table.get('_global_index_map', {})
    local_indexes = current_table.get('_local_index_map', {})
    for index in global_indexes:
        idx = dict(global_indexes[index])
        idx.pop('provisioned_throughput', None)
        indexes.append(idx)
    for index in local_indexes:
        idx = dict(local_indexes[index])
        idx.pop('provisioned_throughput', None)
        indexes.append(idx)

    compat_results = dict(
        hash_key_name=hash_key_name,
        hash_key_type=hash_key_type,
        range_key_name=range_key_name,
        range_key_type=range_key_type,
        indexes=indexes,
        billing_mode=billing_mode,
        region=module.region,
        table_name=current_table.get('table_name', None),
        table_class=current_table.get('table_class_summary', {}).get('table_class', None),
        table_status=current_table.get('table_status', None),
        tags=current_table.get('tags', {}),
    )

    if billing_mode == "PROVISIONED":
        throughput = current_table.get('provisioned_throughput', {})
        compat_results['read_capacity'] = throughput.get('read_capacity_units', None)
        compat_results['write_capacity'] = throughput.get('write_capacity_units', None)

    return compat_results


def get_dynamodb_table():
    table_name = module.params.get('name')
    try:
        table = _describe_table(TableName=table_name)
    except is_boto3_error_code('ResourceNotFoundException'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to describe table')

    table = table['Table']
    try:
        tags = client.list_tags_of_resource(aws_retry=True, ResourceArn=table['TableArn'])['Tags']
    except is_boto3_error_code('AccessDeniedException'):
        module.warn('Permission denied when listing tags')
        tags = []
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to list table tags')

    tags = boto3_tag_list_to_ansible_dict(tags)

    table = camel_dict_to_snake_dict(table)

    # Put some of the values into places people will expect them
    table['arn'] = table['table_arn']
    table['name'] = table['table_name']
    table['status'] = table['table_status']
    table['id'] = table['table_id']
    table['size'] = table['table_size_bytes']
    table['tags'] = tags

    if 'table_class_summary' in table:
        table['table_class'] = table['table_class_summary']['table_class']

    # billing_mode_summary doesn't always seem to be set but is always set for PAY_PER_REQUEST
    # and when updating the billing_mode
    if 'billing_mode_summary' in table:
        table['billing_mode'] = table['billing_mode_summary']['billing_mode']
    else:
        table['billing_mode'] = "PROVISIONED"

    # convert indexes into something we can easily search against
    attributes = table['attribute_definitions']
    global_index_map = dict()
    local_index_map = dict()
    for index in table.get('global_secondary_indexes', []):
        idx = _decode_index(index, attributes, type_prefix='global_')
        global_index_map[idx['name']] = idx
    for index in table.get('local_secondary_indexes', []):
        idx = _decode_index(index, attributes)
        local_index_map[idx['name']] = idx
    table['_global_index_map'] = global_index_map
    table['_local_index_map'] = local_index_map

    return table


def _generate_attribute_map():
    """
    Builds a map of Key Names to Type
    """
    attributes = dict()

    for index in (module.params, *module.params.get('indexes')):
        # run through hash_key_name and range_key_name
        for t in ['hash', 'range']:
            key_name = index.get(t + '_key_name')
            if not key_name:
                continue
            key_type = index.get(t + '_key_type') or DYNAMO_TYPE_DEFAULT
            _type = _long_type_to_short(key_type)
            if key_name in attributes:
                if _type != attributes[key_name]:
                    module.fail_json(msg='Conflicting attribute type',
                                     type_1=_type, type_2=attributes[key_name],
                                     key_name=key_name)
            else:
                attributes[key_name] = _type

    return attributes


def _generate_attributes():
    attributes = _generate_attribute_map()

    # Use ansible_dict_to_boto3_tag_list to generate the list of dicts
    # format we need
    attrs = ansible_dict_to_boto3_tag_list(
        attributes,
        tag_name_key_name='AttributeName',
        tag_value_key_name='AttributeType'
    )
    return list(attrs)


def _generate_throughput(params=None):
    if not params:
        params = module.params

    read_capacity = params.get('read_capacity') or 1
    write_capacity = params.get('write_capacity') or 1
    throughput = dict(
        ReadCapacityUnits=read_capacity,
        WriteCapacityUnits=write_capacity,
    )

    return throughput


def _generate_schema(params=None):
    if not params:
        params = module.params

    schema = list()
    hash_key_name = params.get('hash_key_name')
    range_key_name = params.get('range_key_name')

    if hash_key_name:
        entry = _schema_dict(hash_key_name, 'HASH')
        schema.append(entry)
    if range_key_name:
        entry = _schema_dict(range_key_name, 'RANGE')
        schema.append(entry)

    return schema


def _primary_index_changes(current_table):

    primary_index = _decode_primary_index(current_table)

    hash_key_name = primary_index.get('hash_key_name')
    _hash_key_name = module.params.get('hash_key_name')
    hash_key_type = primary_index.get('hash_key_type')
    _hash_key_type = module.params.get('hash_key_type')
    range_key_name = primary_index.get('range_key_name')
    _range_key_name = module.params.get('range_key_name')
    range_key_type = primary_index.get('range_key_type')
    _range_key_type = module.params.get('range_key_type')

    changed = list()

    if _hash_key_name and (_hash_key_name != hash_key_name):
        changed.append('hash_key_name')
    if _hash_key_type and (_hash_key_type != hash_key_type):
        changed.append('hash_key_type')
    if _range_key_name and (_range_key_name != range_key_name):
        changed.append('range_key_name')
    if _range_key_type and (_range_key_type != range_key_type):
        changed.append('range_key_type')

    return changed


def _throughput_changes(current_table, params=None):

    if not params:
        params = module.params

    throughput = current_table.get('provisioned_throughput', {})
    read_capacity = throughput.get('read_capacity_units', None)
    _read_capacity = params.get('read_capacity') or read_capacity
    write_capacity = throughput.get('write_capacity_units', None)
    _write_capacity = params.get('write_capacity') or write_capacity

    if (read_capacity != _read_capacity) or (write_capacity != _write_capacity):
        return dict(
            ReadCapacityUnits=_read_capacity,
            WriteCapacityUnits=_write_capacity,
        )

    return dict()


def _generate_global_indexes(billing_mode):
    index_exists = dict()
    indexes = list()

    include_throughput = True

    if billing_mode == "PAY_PER_REQUEST":
        include_throughput = False

    for index in module.params.get('indexes'):
        if index.get('type') not in ['global_all', 'global_include', 'global_keys_only']:
            continue
        name = index.get('name')
        if name in index_exists:
            module.fail_json(msg='Duplicate key {0} in list of global indexes'.format(name))
        # Convert the type name to upper case and remove the global_
        index['type'] = index['type'].upper()[7:]
        index = _generate_index(index, include_throughput)
        index_exists[name] = True
        indexes.append(index)

    return indexes


def _generate_local_indexes():
    index_exists = dict()
    indexes = list()

    for index in module.params.get('indexes'):
        index = dict()
        if index.get('type') not in ['all', 'include', 'keys_only']:
            continue
        name = index.get('name')
        if name in index_exists:
            module.fail_json(msg='Duplicate key {0} in list of local indexes'.format(name))
        index['type'] = index['type'].upper()
        index = _generate_index(index, False)
        index_exists[name] = True
        indexes.append(index)

    return indexes


def _generate_global_index_map(current_table):
    global_index_map = dict()
    existing_indexes = current_table['_global_index_map']
    for index in module.params.get('indexes'):
        if index.get('type') not in ['global_all', 'global_include', 'global_keys_only']:
            continue
        name = index.get('name')
        if name in global_index_map:
            module.fail_json(msg='Duplicate key {0} in list of global indexes'.format(name))
        idx = _merge_index_params(index, existing_indexes.get(name, {}))
        # Convert the type name to upper case and remove the global_
        idx['type'] = idx['type'].upper()[7:]
        global_index_map[name] = idx
    return global_index_map


def _generate_local_index_map(current_table):
    local_index_map = dict()
    existing_indexes = current_table['_local_index_map']
    for index in module.params.get('indexes'):
        if index.get('type') not in ['all', 'include', 'keys_only']:
            continue
        name = index.get('name')
        if name in local_index_map:
            module.fail_json(msg='Duplicate key {0} in list of local indexes'.format(name))
        idx = _merge_index_params(index, existing_indexes.get(name, {}))
        # Convert the type name to upper case
        idx['type'] = idx['type'].upper()
        local_index_map[name] = idx
    return local_index_map


def _generate_index(index, include_throughput=True):
    key_schema = _generate_schema(index)
    throughput = _generate_throughput(index)
    non_key_attributes = index['includes'] or []
    projection = dict(
        ProjectionType=index['type'],
    )
    if index['type'] != 'ALL':
        if non_key_attributes:
            projection['NonKeyAttributes'] = non_key_attributes
    else:
        if non_key_attributes:
            module.fail_json(
                "DynamoDB does not support specifying non-key-attributes ('includes') for "
                "indexes of type 'all'. Index name: {0}".format(index['name']))

    idx = dict(
        IndexName=index['name'],
        KeySchema=key_schema,
        Projection=projection,
    )

    if include_throughput:
        idx['ProvisionedThroughput'] = throughput

    return idx


def _attribute_changes(current_table):
    # TODO (future) It would be nice to catch attempts to change types here.
    return _generate_attributes()


def _global_index_changes(current_table):
    current_global_index_map = current_table['_global_index_map']
    global_index_map = _generate_global_index_map(current_table)

    current_billing_mode = current_table.get('billing_mode')

    if module.params.get('billing_mode') is None:
        billing_mode = current_billing_mode
    else:
        billing_mode = module.params.get('billing_mode')

    include_throughput = True

    if billing_mode == "PAY_PER_REQUEST":
        include_throughput = False

    index_changes = list()

    # TODO (future) it would be nice to add support for deleting an index
    for name in global_index_map:

        idx = dict(_generate_index(global_index_map[name], include_throughput=include_throughput))
        if name not in current_global_index_map:
            index_changes.append(dict(Create=idx))
        else:
            # The only thing we can change is the provisioned throughput.
            # TODO (future) it would be nice to throw a deprecation here
            # rather than dropping other changes on the floor
            _current = current_global_index_map[name]
            _new = global_index_map[name]

            if include_throughput:
                change = dict(_throughput_changes(_current, _new))
                if change:
                    update = dict(
                        IndexName=name,
                        ProvisionedThroughput=change,
                    )
                    index_changes.append(dict(Update=update))

    return index_changes


def _local_index_changes(current_table):
    # TODO (future) Changes to Local Indexes aren't possible after creation,
    # we should probably throw a deprecation warning here (original module
    # also just dropped these changes on the floor)
    return []


def _update_table(current_table):
    changes = dict()
    additional_global_index_changes = list()

    # Get throughput / billing_mode changes
    throughput_changes = _throughput_changes(current_table)
    if throughput_changes:
        changes['ProvisionedThroughput'] = throughput_changes

    current_billing_mode = current_table.get('billing_mode')
    new_billing_mode = module.params.get('billing_mode')

    if new_billing_mode is None:
        new_billing_mode = current_billing_mode

    if current_billing_mode != new_billing_mode:
        changes['BillingMode'] = new_billing_mode

    # Update table_class use exisiting if none is defined
    if module.params.get('table_class'):
        if module.params.get('table_class') != current_table.get('table_class'):
            changes['TableClass'] = module.params.get('table_class')

    global_index_changes = _global_index_changes(current_table)
    if global_index_changes:
        changes['GlobalSecondaryIndexUpdates'] = global_index_changes
        # Only one index can be changed at a time except if changing the billing mode, pass the first during the
        # main update and deal with the others on a slow retry to wait for
        # completion

        if current_billing_mode == new_billing_mode:
            if len(global_index_changes) > 1:
                changes['GlobalSecondaryIndexUpdates'] = [global_index_changes[0]]
                additional_global_index_changes = global_index_changes[1:]

    local_index_changes = _local_index_changes(current_table)
    if local_index_changes:
        changes['LocalSecondaryIndexUpdates'] = local_index_changes

    if not changes:
        return False

    if module.check_mode:
        return True

    if global_index_changes or local_index_changes:
        changes['AttributeDefinitions'] = _generate_attributes()

    try:
        client.update_table(
            aws_retry=True,
            TableName=module.params.get('name'),
            **changes
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update table")

    if additional_global_index_changes:
        for index in additional_global_index_changes:
            try:
                _update_table_with_long_retry(GlobalSecondaryIndexUpdates=[index], AttributeDefinitions=changes['AttributeDefinitions'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to update table", changes=changes,
                                     additional_global_index_changes=additional_global_index_changes)

    if module.params.get('wait'):
        wait_exists()

    return True


def _update_tags(current_table):
    _tags = module.params.get('tags')
    if _tags is None:
        return False

    tags_to_add, tags_to_remove = compare_aws_tags(current_table['tags'], module.params.get('tags'),
                                                   purge_tags=module.params.get('purge_tags'))

    # If neither need updating we can return already
    if not (tags_to_add or tags_to_remove):
        return False

    if module.check_mode:
        return True

    if tags_to_add:
        try:
            client.tag_resource(
                aws_retry=True,
                ResourceArn=current_table['arn'],
                Tags=ansible_dict_to_boto3_tag_list(tags_to_add),
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to tag table")
    if tags_to_remove:
        try:
            client.untag_resource(
                aws_retry=True,
                ResourceArn=current_table['arn'],
                TagKeys=tags_to_remove,
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to untag table")

    return True


def update_table(current_table):
    primary_index_changes = _primary_index_changes(current_table)
    if primary_index_changes:
        module.fail_json("DynamoDB does not support updating the Primary keys on a table. Changed paramters are: {0}".format(primary_index_changes))

    changed = False
    changed |= _update_table(current_table)
    changed |= _update_tags(current_table)

    if module.params.get('wait'):
        wait_exists()

    return changed


def create_table():
    table_name = module.params.get('name')
    table_class = module.params.get('table_class')
    hash_key_name = module.params.get('hash_key_name')
    billing_mode = module.params.get('billing_mode')

    if billing_mode is None:
        billing_mode = "PROVISIONED"

    tags = ansible_dict_to_boto3_tag_list(module.params.get('tags') or {})

    if not hash_key_name:
        module.fail_json('"hash_key_name" must be provided when creating a new table.')

    if module.check_mode:
        return True

    if billing_mode == "PROVISIONED":
        throughput = _generate_throughput()

    attributes = _generate_attributes()
    key_schema = _generate_schema()
    local_indexes = _generate_local_indexes()
    global_indexes = _generate_global_indexes(billing_mode)

    params = dict(
        TableName=table_name,
        AttributeDefinitions=attributes,
        KeySchema=key_schema,
        Tags=tags,
        BillingMode=billing_mode
        # TODO (future)
        # StreamSpecification,
        # SSESpecification,
    )

    if table_class:
        params['TableClass'] = table_class
    if billing_mode == "PROVISIONED":
        params['ProvisionedThroughput'] = throughput
    if local_indexes:
        params['LocalSecondaryIndexes'] = local_indexes
    if global_indexes:
        params['GlobalSecondaryIndexes'] = global_indexes

    try:
        client.create_table(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to create table')

    if module.params.get('wait'):
        wait_exists()

    return True


def delete_table(current_table):
    if not current_table:
        return False

    if module.check_mode:
        return True

    table_name = module.params.get('name')

    # If an index is mid-update then we have to wait for the update to complete
    # before deletion will succeed
    long_retry = AWSRetry.jittered_backoff(
        retries=45, delay=5, max_delay=30,
        catch_extra_error_codes=['LimitExceededException', 'ResourceInUseException'],
    )

    try:
        long_retry(client.delete_table)(TableName=table_name)
    except is_boto3_error_code('ResourceNotFoundException'):
        return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to delete table')

    if module.params.get('wait'):
        wait_not_exists()

    return True


def main():

    global module
    global client

    # TODO (future) It would be good to split global and local indexes.  They have
    # different parameters, use a separate namespace for names,
    #  and local indexes can't be updated.
    index_options = dict(
        name=dict(type='str', required=True),
        # It would be nice to make this optional, but because Local and Global
        # indexes are mixed in here we need this to be able to tell to which
        # group of indexes the index belongs.
        type=dict(type='str', required=True, choices=INDEX_TYPE_OPTIONS),
        hash_key_name=dict(type='str', required=False),
        hash_key_type=dict(type='str', required=False, choices=KEY_TYPE_CHOICES),
        range_key_name=dict(type='str', required=False),
        range_key_type=dict(type='str', required=False, choices=KEY_TYPE_CHOICES),
        includes=dict(type='list', required=False, elements='str'),
        read_capacity=dict(type='int', required=False),
        write_capacity=dict(type='int', required=False),
    )

    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        hash_key_name=dict(type='str'),
        hash_key_type=dict(type='str', choices=KEY_TYPE_CHOICES),
        range_key_name=dict(type='str'),
        range_key_type=dict(type='str', choices=KEY_TYPE_CHOICES),
        billing_mode=dict(type='str', choices=['PROVISIONED', 'PAY_PER_REQUEST']),
        read_capacity=dict(type='int'),
        write_capacity=dict(type='int'),
        indexes=dict(default=[], type='list', elements='dict', options=index_options),
        table_class=dict(type='str', choices=['STANDARD', 'STANDARD_INFREQUENT_ACCESS']),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
        wait=dict(type='bool', default=True),
        wait_timeout=dict(default=300, type='int', aliases=['wait_for_active_timeout']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        check_boto3=False,
    )

    retry_decorator = AWSRetry.jittered_backoff(
        catch_extra_error_codes=['LimitExceededException', 'ResourceInUseException', 'ResourceNotFoundException'],
    )
    client = module.client('dynamodb', retry_decorator=retry_decorator)

    if module.params.get('table_class'):
        module.require_botocore_at_least('1.23.18', reason='to set table_class')

    current_table = get_dynamodb_table()
    changed = False
    table = None
    results = dict()

    state = module.params.get('state')
    if state == 'present':
        if current_table:
            changed |= update_table(current_table)
        else:
            changed |= create_table()
        table = get_dynamodb_table()
    elif state == 'absent':
        changed |= delete_table(current_table)

    compat_results = compatability_results(table)
    if compat_results:
        results.update(compat_results)

    results['changed'] = changed
    if table:
        # These are used to pass computed data about, not needed for users
        table.pop('_global_index_map', None)
        table.pop('_local_index_map', None)
        results['table'] = table

    module.exit_json(**results)


if __name__ == '__main__':
    main()

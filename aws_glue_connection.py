#!/usr/bin/python
# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: aws_glue_connection
version_added: 1.0.0
short_description: Manage an AWS Glue connection
description:
    - Manage an AWS Glue connection. See U(https://aws.amazon.com/glue/) for details.
author: "Rob White (@wimnat)"
options:
  availability_zone:
    description:
      - Availability Zone used by the connection
      - Required when I(connection_type=NETWORK).
    type: str
    version_added: 1.5.0
  catalog_id:
    description:
      - The ID of the Data Catalog in which to create the connection. If none is supplied,
        the AWS account ID is used by default.
    type: str
  connection_properties:
    description:
      - A dict of key-value pairs used as parameters for this connection.
      - Required when I(state=present).
    type: dict
  connection_type:
    description:
      - The type of the connection. Currently, SFTP is not supported.
    default: JDBC
    choices: [ 'CUSTOM', 'JDBC', 'KAFKA', 'MARKETPLACE', 'MONGODB', 'NETWORK' ]
    type: str
  description:
    description:
      - The description of the connection.
    type: str
  match_criteria:
    description:
      - A list of UTF-8 strings that specify the criteria that you can use in selecting this connection.
    type: list
    elements: str
  name:
    description:
      - The name of the connection.
    required: true
    type: str
  security_groups:
    description:
      - A list of security groups to be used by the connection. Use either security group name or ID.
      - Required when I(connection_type=NETWORK).
    type: list
    elements: str
  state:
    description:
      - Create or delete the AWS Glue connection.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  subnet_id:
    description:
      - The subnet ID used by the connection.
      - Required when I(connection_type=NETWORK).
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an AWS Glue connection
- community.aws.aws_glue_connection:
    name: my-glue-connection
    connection_properties:
      JDBC_CONNECTION_URL: jdbc:mysql://mydb:3306/databasename
      USERNAME: my-username
      PASSWORD: my-password
    state: present

# Create an AWS Glue network connection
- community.aws.aws_glue_connection:
    name: my-glue-network-connection
    availability_zone: us-east-1a
    connection_properties:
      JDBC_ENFORCE_SSL: "false"
    connection_type: NETWORK
    description: Test connection
    security_groups:
      - sg-glue
    subnet_id: subnet-123abc
    state: present

# Delete an AWS Glue connection
- community.aws.aws_glue_connection:
    name: my-glue-connection
    state: absent

'''

RETURN = r'''
connection_properties:
    description: A dict of key-value pairs used as parameters for this connection.
    returned: when state is present
    type: dict
    sample: {'JDBC_CONNECTION_URL':'jdbc:mysql://mydb:3306/databasename','USERNAME':'x','PASSWORD':'y'}
connection_type:
    description: The type of the connection.
    returned: when state is present
    type: str
    sample: JDBC
creation_time:
    description: The time this connection definition was created.
    returned: when state is present
    type: str
    sample: "2018-04-21T05:19:58.326000+00:00"
description:
    description: Description of the job being defined.
    returned: when state is present
    type: str
    sample: My first Glue job
last_updated_time:
    description: The last time this connection definition was updated.
    returned: when state is present
    type: str
    sample: "2018-04-21T05:19:58.326000+00:00"
match_criteria:
    description: A list of criteria that can be used in selecting this connection.
    returned: when state is present
    type: list
    sample: []
name:
    description: The name of the connection definition.
    returned: when state is present
    type: str
    sample: my-glue-connection
physical_connection_requirements:
    description: A dict of physical connection requirements, such as VPC and SecurityGroup,
                 needed for making this connection successfully.
    returned: when state is present
    type: dict
    sample: {'subnet-id':'subnet-aabbccddee'}
'''

# Non-ansible imports
import copy
import time
try:
    import botocore
except ImportError:
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_ec2_security_group_ids_from_names


def _get_glue_connection(connection, module):
    """
    Get an AWS Glue connection based on name. If not found, return None.

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :return: boto3 Glue connection dict or None if not found
    """

    connection_name = module.params.get("name")
    connection_catalog_id = module.params.get("catalog_id")

    params = {'Name': connection_name}
    if connection_catalog_id is not None:
        params['CatalogId'] = connection_catalog_id

    try:
        return connection.get_connection(aws_retry=True, **params)['Connection']
    except is_boto3_error_code('EntityNotFoundException'):
        return None


def _compare_glue_connection_params(user_params, current_params):
    """
    Compare Glue connection params. If there is a difference, return True immediately else return False

    :param user_params: the Glue connection parameters passed by the user
    :param current_params: the Glue connection parameters currently configured
    :return: True if any parameter is mismatched else False
    """

    # Weirdly, boto3 doesn't return some keys if the value is empty e.g. Description
    # To counter this, add the key if it's missing with a blank value

    if 'Description' not in current_params:
        current_params['Description'] = ""
    if 'MatchCriteria' not in current_params:
        current_params['MatchCriteria'] = list()
    if 'PhysicalConnectionRequirements' not in current_params:
        current_params['PhysicalConnectionRequirements'] = dict()
        current_params['PhysicalConnectionRequirements']['SecurityGroupIdList'] = []
        current_params['PhysicalConnectionRequirements']['SubnetId'] = ""

    if 'ConnectionProperties' in user_params['ConnectionInput'] and user_params['ConnectionInput']['ConnectionProperties'] \
            != current_params['ConnectionProperties']:
        return True
    if 'ConnectionType' in user_params['ConnectionInput'] and user_params['ConnectionInput']['ConnectionType'] \
            != current_params['ConnectionType']:
        return True
    if 'Description' in user_params['ConnectionInput'] and user_params['ConnectionInput']['Description'] != current_params['Description']:
        return True
    if 'MatchCriteria' in user_params['ConnectionInput'] and set(user_params['ConnectionInput']['MatchCriteria']) != set(current_params['MatchCriteria']):
        return True
    if 'PhysicalConnectionRequirements' in user_params['ConnectionInput']:
        if 'SecurityGroupIdList' in user_params['ConnectionInput']['PhysicalConnectionRequirements'] and \
                set(user_params['ConnectionInput']['PhysicalConnectionRequirements']['SecurityGroupIdList']) \
                != set(current_params['PhysicalConnectionRequirements']['SecurityGroupIdList']):
            return True
        if 'SubnetId' in user_params['ConnectionInput']['PhysicalConnectionRequirements'] and \
                user_params['ConnectionInput']['PhysicalConnectionRequirements']['SubnetId'] \
                != current_params['PhysicalConnectionRequirements']['SubnetId']:
            return True
        if 'AvailabilityZone' in user_params['ConnectionInput']['PhysicalConnectionRequirements'] and \
                user_params['ConnectionInput']['PhysicalConnectionRequirements']['AvailabilityZone'] \
                != current_params['PhysicalConnectionRequirements']['AvailabilityZone']:
            return True

    return False


# Glue module doesn't appear to have any waiters, unlike EC2 or RDS
def _await_glue_connection(connection, module):
    start_time = time.time()
    wait_timeout = start_time + 30
    check_interval = 5

    while wait_timeout > time.time():
        glue_connection = _get_glue_connection(connection, module)
        if glue_connection and glue_connection.get('Name'):
            return glue_connection
        time.sleep(check_interval)

    module.fail_json(msg='Timeout waiting for Glue connection %s' % module.params.get('name'))


def create_or_update_glue_connection(connection, connection_ec2, module, glue_connection):
    """
    Create or update an AWS Glue connection

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_connection: a dict of AWS Glue connection parameters or None
    :return:
    """
    changed = False

    params = dict()
    params['ConnectionInput'] = dict()
    params['ConnectionInput']['Name'] = module.params.get("name")
    params['ConnectionInput']['ConnectionType'] = module.params.get("connection_type")
    params['ConnectionInput']['ConnectionProperties'] = module.params.get("connection_properties")
    if module.params.get("catalog_id") is not None:
        params['CatalogId'] = module.params.get("catalog_id")
    if module.params.get("description") is not None:
        params['ConnectionInput']['Description'] = module.params.get("description")
    if module.params.get("match_criteria") is not None:
        params['ConnectionInput']['MatchCriteria'] = module.params.get("match_criteria")
    if module.params.get("security_groups") is not None or module.params.get("subnet_id") is not None:
        params['ConnectionInput']['PhysicalConnectionRequirements'] = dict()
    if module.params.get("security_groups") is not None:
        # Get security group IDs from names
        security_group_ids = get_ec2_security_group_ids_from_names(module.params.get('security_groups'), connection_ec2, boto3=True)
        params['ConnectionInput']['PhysicalConnectionRequirements']['SecurityGroupIdList'] = security_group_ids
    if module.params.get("subnet_id") is not None:
        params['ConnectionInput']['PhysicalConnectionRequirements']['SubnetId'] = module.params.get("subnet_id")
    if module.params.get("availability_zone") is not None:
        params['ConnectionInput']['PhysicalConnectionRequirements']['AvailabilityZone'] = module.params.get("availability_zone")

    # If glue_connection is not None then check if it needs to be modified, else create it
    if glue_connection:
        if _compare_glue_connection_params(params, glue_connection):
            try:
                # We need to slightly modify the params for an update
                update_params = copy.deepcopy(params)
                update_params['Name'] = update_params['ConnectionInput']['Name']
                if not module.check_mode:
                    connection.update_connection(aws_retry=True, **update_params)
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e)
    else:
        try:
            if not module.check_mode:
                connection.create_connection(aws_retry=True, **params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e)

    # If changed, get the Glue connection again
    if changed and not module.check_mode:
        glue_connection = _await_glue_connection(connection, module)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(glue_connection or {}))


def delete_glue_connection(connection, module, glue_connection):
    """
    Delete an AWS Glue connection

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_connection: a dict of AWS Glue connection parameters or None
    :return:
    """
    changed = False

    params = {'ConnectionName': module.params.get("name")}
    if module.params.get("catalog_id") is not None:
        params['CatalogId'] = module.params.get("catalog_id")

    if glue_connection:
        try:
            if not module.check_mode:
                connection.delete_connection(aws_retry=True, **params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed)


def main():

    argument_spec = (
        dict(
            availability_zone=dict(type='str'),
            catalog_id=dict(type='str'),
            connection_properties=dict(type='dict'),
            connection_type=dict(type='str', default='JDBC', choices=['CUSTOM', 'JDBC', 'KAFKA', 'MARKETPLACE', 'MONGODB', 'NETWORK']),
            description=dict(type='str'),
            match_criteria=dict(type='list', elements='str'),
            name=dict(required=True, type='str'),
            security_groups=dict(type='list', elements='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            subnet_id=dict(type='str')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ('state', 'present', ['connection_properties']),
                                  ('connection_type', 'NETWORK', ['availability_zone', 'security_groups', 'subnet_id'])
                              ],
                              supports_check_mode=True
                              )

    retry_decorator = AWSRetry.jittered_backoff(retries=10)
    connection_glue = module.client('glue', retry_decorator=retry_decorator)
    connection_ec2 = module.client('ec2', retry_decorator=retry_decorator)

    glue_connection = _get_glue_connection(connection_glue, module)

    if module.params.get("state") == 'present':
        create_or_update_glue_connection(connection_glue, connection_ec2, module, glue_connection)
    else:
        delete_glue_connection(connection_glue, module, glue_connection)


if __name__ == '__main__':
    main()

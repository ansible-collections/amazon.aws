#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: dms_endpoint
version_added: 1.0.0
short_description: Creates or destroys a data migration services endpoint
description:
  - Creates or destroys a data migration services endpoint,
    that can be used to replicate data.
options:
    state:
      description:
        - State of the endpoint.
      default: present
      choices: ['present', 'absent']
      type: str
    endpointidentifier:
      description:
        - An identifier name for the endpoint.
      type: str
      required: true
    endpointtype:
      description:
        - Type of endpoint we want to manage.
        - Required when I(state=present).
      choices: ['source', 'target']
      type: str
    enginename:
      description:
        - Database engine that we want to use, please refer to
          the AWS DMS for more information on the supported
          engines and their limitations.
        - Required when I(state=present).
      choices: ['mysql', 'oracle', 'postgres', 'mariadb', 'aurora',
                         'redshift', 's3', 'db2', 'azuredb', 'sybase',
                         'dynamodb', 'mongodb', 'sqlserver']
      type: str
    username:
      description:
        - Username our endpoint will use to connect to the database.
      type: str
    password:
      description:
        - Password used to connect to the database
          this attribute can only be written
          the AWS API does not return this parameter.
      type: str
    servername:
      description:
        - Servername that the endpoint will connect to.
      type: str
    port:
      description:
        - TCP port for access to the database.
      type: int
    databasename:
      description:
        - Name for the database on the origin or target side.
      type: str
    extraconnectionattributes:
      description:
        - Extra attributes for the database connection, the AWS documentation
          states " For more information about extra connection attributes,
          see the documentation section for your data store."
      type: str
    kmskeyid:
      description:
        - Encryption key to use to encrypt replication storage and
          connection information.
      type: str
    tags:
      description:
        - A list of tags to add to the endpoint.
      type: dict
    certificatearn:
      description:
        -  Amazon Resource Name (ARN) for the certificate.
      type: str
    sslmode:
      description:
        - Mode used for the SSL connection.
      default: none
      choices: ['none', 'require', 'verify-ca', 'verify-full']
      type: str
    serviceaccessrolearn:
      description:
        -  Amazon Resource Name (ARN) for the service access role that you
           want to use to create the endpoint.
      type: str
    externaltabledefinition:
      description:
        - The external table definition.
      type: str
    dynamodbsettings:
      description:
        - Settings in JSON format for the target Amazon DynamoDB endpoint
          if source or target is dynamodb.
      type: dict
    s3settings:
      description:
        - S3 buckets settings for the target Amazon S3 endpoint.
      type: dict
    dmstransfersettings:
      description:
        - The settings in JSON format for the DMS transfer type of
          source endpoint.
      type: dict
    mongodbsettings:
      description:
        - Settings in JSON format for the source MongoDB endpoint.
      type: dict
    kinesissettings:
      description:
        - Settings in JSON format for the target Amazon Kinesis
          Data Streams endpoint.
      type: dict
    elasticsearchsettings:
      description:
        - Settings in JSON format for the target Elasticsearch endpoint.
      type: dict
    wait:
      description:
        - Whether Ansible should wait for the object to be deleted when I(state=absent).
      type: bool
      default: false
    timeout:
      description:
        - Time in seconds we should wait for when deleting a resource.
        - Required when I(wait=true).
      type: int
    retries:
      description:
        - number of times we should retry when deleting a resource
        - Required when I(wait=true).
      type: int
author:
  - "Rui Moreira (@ruimoreira)"
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
'''

EXAMPLES = '''
# Note: These examples do not set authentication details
- name: Endpoint Creation
  community.aws.dms_endpoint:
    state: absent
    endpointidentifier: 'testsource'
    endpointtype: source
    enginename: aurora
    username: testing1
    password: testint1234
    servername: testing.domain.com
    port: 3306
    databasename: 'testdb'
    sslmode: none
    wait: false
'''

RETURN = '''
endpoint:
  description:
    - A description of the DMS endpoint.
  returned: success
  type: dict
  contains:
    database_name:
      description:
        - The name of the database at the endpoint.
      type: str
      returned: success
      example: "exampledb"
    endpoint_arn:
      description:
        - The ARN that uniquely identifies the endpoint.
      type: str
      returned: success
      example: "arn:aws:dms:us-east-1:012345678901:endpoint:1234556789ABCDEFGHIJKLMNOPQRSTUVWXYZ012"
    endpoint_identifier:
      description:
        - The database endpoint identifier.
      type: str
      returned: success
      example: "ansible-test-12345678-dms"
    endpoint_type:
      description:
        - The type of endpoint. Valid values are C(SOURCE) and C(TARGET).
      type: str
      returned: success
      example: "SOURCE"
    engine_display_name:
      description:
        - The expanded name for the engine name.
      type: str
      returned: success
      example: "Amazon Aurora MySQL"
    engine_name:
      description:
        - The database engine name.
      type: str
      returned: success
      example: "aurora"
    kms_key_id:
      description:
        - An KMS key ID that is used to encrypt the connection parameters for the endpoint.
      type: str
      returned: success
      example: "arn:aws:kms:us-east-1:012345678901:key/01234567-abcd-12ab-98fe-123456789abc"
    port:
      description:
        - The port used to access the endpoint.
      type: str
      returned: success
      example: 3306
    server_name:
      description:
        - The name of the server at the endpoint.
      type: str
      returned: success
      example: "ansible-test-123456789.example.com"
    ssl_mode:
      description:
        - The SSL mode used to connect to the endpoint.
      type: str
      returned: success
      example: "none"
    tags:
      description:
        - A dictionary representing the tags attached to the endpoint.
      type: dict
      returned: success
      example: {"MyTagKey": "MyTagValue"}
    username:
      description:
        - The user name used to connect to the endpoint.
      type: str
      returned: success
      example: "example-username"
    dms_transfer_settings:
      description:
        - Additional transfer related settings.
      type: dict
      returned: when additional DMS Transfer settings have been configured.
    s3_settings:
      description:
        - Additional settings for S3 endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(s3)
    mongo_db_settings:
      description:
        - Additional settings for MongoDB endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(mongodb)
    kinesis_settings:
      description:
        - Additional settings for Kinesis endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(kinesis)
    kafka_settings:
      description:
        - Additional settings for Kafka endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(kafka)
    elasticsearch_settings:
      description:
        - Additional settings for Elasticsearch endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(elasticsearch)
    neptune_settings:
      description:
        - Additional settings for Amazon Neptune endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(neptune)
    redshift_settings:
      description:
        - Additional settings for Redshift endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(redshift)
    postgre_sql_settings:
      description:
        - Additional settings for PostgrSQL endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(postgres)
    my_sql_settings:
      description:
        - Additional settings for MySQL endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(mysql)
    oracle_settings:
      description:
        - Additional settings for Oracle endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(oracle)
    sybase_settings:
      description:
        - Additional settings for Sybase endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(sybase)
    microsoft_sql_server_settings:
      description:
        - Additional settings for Microsoft SQL Server endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(sqlserver)
    i_b_m_db_settings:
      description:
        - Additional settings for IBM DB2 endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(db2)
    doc_db_settings:
      description:
        - Additional settings for DocumentDB endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(documentdb)
    redis_settings:
      description:
        - Additional settings for Redis endpoints.
      type: dict
      returned: when the I(endpoint_type) is C(redshift)
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

backoff_params = dict(retries=5, delay=1, backoff=1.5)


@AWSRetry.jittered_backoff(**backoff_params)
def dms_describe_tags(connection, **params):
    """ checks if the endpoint exists """
    tags = connection.list_tags_for_resource(**params).get('TagList', [])
    return boto3_tag_list_to_ansible_dict(tags)


@AWSRetry.jittered_backoff(**backoff_params)
def dms_describe_endpoints(connection, **params):
    try:
        endpoints = connection.describe_endpoints(**params)
    except is_boto3_error_code('ResourceNotFoundFault'):
        return None
    return endpoints.get('Endpoints', None)


def describe_endpoint(connection, endpoint_identifier):
    """ checks if the endpoint exists """
    endpoint_filter = dict(Name='endpoint-id',
                           Values=[endpoint_identifier])
    try:
        endpoints = dms_describe_endpoints(connection, Filters=[endpoint_filter])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe the DMS endpoint.")

    if not endpoints:
        return None

    endpoint = endpoints[0]
    try:
        tags = dms_describe_tags(connection, ResourceArn=endpoint['EndpointArn'])
        endpoint['tags'] = tags
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe the DMS endpoint tags")
    return endpoint


@AWSRetry.jittered_backoff(**backoff_params)
def dms_delete_endpoint(client, **params):
    """deletes the DMS endpoint based on the EndpointArn"""
    if module.params.get('wait'):
        return delete_dms_endpoint(client)
    else:
        return client.delete_endpoint(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def dms_create_endpoint(client, **params):
    """ creates the DMS endpoint"""
    return client.create_endpoint(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def dms_modify_endpoint(client, **params):
    """ updates the endpoint"""
    return client.modify_endpoint(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def get_endpoint_deleted_waiter(client):
    return client.get_waiter('endpoint_deleted')


@AWSRetry.jittered_backoff(**backoff_params)
def dms_remove_tags(client, **params):
    return client.remove_tags_from_resource(**params)


@AWSRetry.jittered_backoff(**backoff_params)
def dms_add_tags(client, **params):
    return client.add_tags_to_resource(**params)


def endpoint_exists(endpoint):
    """ Returns boolean based on the existence of the endpoint
    :param endpoint: dict containing the described endpoint
    :return: bool
    """
    return bool(len(endpoint['Endpoints']))


def delete_dms_endpoint(connection, endpoint_arn):
    try:
        delete_arn = dict(
            EndpointArn=endpoint_arn
        )
        if module.params.get('wait'):

            delete_output = connection.delete_endpoint(**delete_arn)
            delete_waiter = get_endpoint_deleted_waiter(connection)
            delete_waiter.wait(
                Filters=[{
                    'Name': 'endpoint-arn',
                    'Values': [endpoint_arn]

                }],
                WaiterConfig={
                    'Delay': module.params.get('timeout'),
                    'MaxAttempts': module.params.get('retries')
                }
            )
            return delete_output
        else:
            return connection.delete_endpoint(**delete_arn)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to delete the  DMS endpoint.")


def create_module_params():
    """
    Reads the module parameters and returns a dict
    :return: dict
    """
    endpoint_parameters = dict(
        EndpointIdentifier=module.params.get('endpointidentifier'),
        EndpointType=module.params.get('endpointtype'),
        EngineName=module.params.get('enginename'),
        Username=module.params.get('username'),
        Password=module.params.get('password'),
        ServerName=module.params.get('servername'),
        Port=module.params.get('port'),
        DatabaseName=module.params.get('databasename'),
        SslMode=module.params.get('sslmode')
    )
    if module.params.get('EndpointArn'):
        endpoint_parameters['EndpointArn'] = module.params.get('EndpointArn')
    if module.params.get('certificatearn'):
        endpoint_parameters['CertificateArn'] = \
            module.params.get('certificatearn')

    if module.params.get('dmstransfersettings'):
        endpoint_parameters['DmsTransferSettings'] = \
            module.params.get('dmstransfersettings')

    if module.params.get('extraconnectionattributes'):
        endpoint_parameters['ExtraConnectionAttributes'] =\
            module.params.get('extraconnectionattributes')

    if module.params.get('kmskeyid'):
        endpoint_parameters['KmsKeyId'] = module.params.get('kmskeyid')

    if module.params.get('tags'):
        endpoint_parameters['Tags'] = module.params.get('tags')

    if module.params.get('serviceaccessrolearn'):
        endpoint_parameters['ServiceAccessRoleArn'] = \
            module.params.get('serviceaccessrolearn')

    if module.params.get('externaltabledefinition'):
        endpoint_parameters['ExternalTableDefinition'] = \
            module.params.get('externaltabledefinition')

    if module.params.get('dynamodbsettings'):
        endpoint_parameters['DynamoDbSettings'] = \
            module.params.get('dynamodbsettings')

    if module.params.get('s3settings'):
        endpoint_parameters['S3Settings'] = module.params.get('s3settings')

    if module.params.get('mongodbsettings'):
        endpoint_parameters['MongoDbSettings'] = \
            module.params.get('mongodbsettings')

    if module.params.get('kinesissettings'):
        endpoint_parameters['KinesisSettings'] = \
            module.params.get('kinesissettings')

    if module.params.get('elasticsearchsettings'):
        endpoint_parameters['ElasticsearchSettings'] = \
            module.params.get('elasticsearchsettings')

    if module.params.get('wait'):
        endpoint_parameters['wait'] = module.boolean(module.params.get('wait'))

    if module.params.get('timeout'):
        endpoint_parameters['timeout'] = module.params.get('timeout')

    if module.params.get('retries'):
        endpoint_parameters['retries'] = module.params.get('retries')

    return endpoint_parameters


def compare_params(param_described):
    """
    Compares the dict obtained from the describe DMS endpoint and
    what we are reading from the values in the template We can
    never compare the password as boto3's method for describing
    a DMS endpoint does not return the value for
    the password for security reasons ( I assume )
    """
    param_described = dict(param_described)
    modparams = create_module_params()
    # modify can't update tags
    param_described.pop('Tags', None)
    modparams.pop('Tags', None)
    changed = False
    for paramname in modparams:
        if paramname == 'Password' or paramname in param_described \
                and param_described[paramname] == modparams[paramname] or \
                str(param_described[paramname]).lower() \
                == modparams[paramname]:
            pass
        else:
            changed = True
    return changed


def modify_dms_endpoint(connection, endpoint):
    arn = endpoint['EndpointArn']
    try:
        params = create_module_params()
        # modify can't update tags
        params.pop('Tags', None)
        return dms_modify_endpoint(connection, EndpointArn=arn, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update DMS endpoint.", params=params)


def ensure_tags(connection, endpoint):
    desired_tags = module.params.get('tags', None)
    if desired_tags is None:
        return False

    current_tags = endpoint.get('tags', {})

    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, desired_tags,
                                                   module.params.get('purge_tags'))

    if not tags_to_remove and not tags_to_add:
        return False

    if module.check_mode:
        return True

    arn = endpoint.get('EndpointArn')

    try:
        if tags_to_remove:
            dms_remove_tags(connection, ResourceArn=arn, TagKeys=tags_to_remove)
        if tags_to_add:
            tag_list = ansible_dict_to_boto3_tag_list(tags_to_add)
            dms_add_tags(connection, ResourceArn=arn, Tags=tag_list)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update DMS endpoint tags.")

    return True


def create_dms_endpoint(connection):
    """
    Function to create the dms endpoint
    :param connection: boto3 aws connection
    :return: information about the dms endpoint object
    """

    try:
        params = create_module_params()
        return dms_create_endpoint(connection, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create DMS endpoint.")


def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        endpointidentifier=dict(required=True),
        endpointtype=dict(choices=['source', 'target']),
        enginename=dict(choices=['mysql', 'oracle', 'postgres', 'mariadb',
                                 'aurora', 'redshift', 's3', 'db2', 'azuredb',
                                 'sybase', 'dynamodb', 'mongodb', 'sqlserver'],
                        required=False),
        username=dict(),
        password=dict(no_log=True),
        servername=dict(),
        port=dict(type='int'),
        databasename=dict(),
        extraconnectionattributes=dict(),
        kmskeyid=dict(no_log=False),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
        certificatearn=dict(),
        sslmode=dict(choices=['none', 'require', 'verify-ca', 'verify-full'],
                     default='none'),
        serviceaccessrolearn=dict(),
        externaltabledefinition=dict(),
        dynamodbsettings=dict(type='dict'),
        s3settings=dict(type='dict'),
        dmstransfersettings=dict(type='dict'),
        mongodbsettings=dict(type='dict'),
        kinesissettings=dict(type='dict'),
        elasticsearchsettings=dict(type='dict'),
        wait=dict(type='bool', default=False),
        timeout=dict(type='int'),
        retries=dict(type='int')
    )
    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ["state", "present", ["endpointtype"]],
            ["state", "present", ["enginename"]],
            ["state", "absent", ["wait"]],
            ["wait", "True", ["timeout"]],
            ["wait", "True", ["retries"]],
        ],
        supports_check_mode=False
    )
    exit_message = None
    changed = False

    state = module.params.get('state')

    dmsclient = module.client('dms')
    endpoint = describe_endpoint(dmsclient,
                                 module.params.get('endpointidentifier'))
    if state == 'present':
        if endpoint:
            changed |= ensure_tags(dmsclient, endpoint)
            params_changed = compare_params(endpoint)
            if params_changed:
                updated_dms = modify_dms_endpoint(dmsclient, endpoint)
                exit_message = updated_dms
                endpoint = exit_message.get('Endpoint')
                changed = True
            else:
                exit_message = "Endpoint Already Exists"
        else:
            exit_message = create_dms_endpoint(dmsclient)
            endpoint = exit_message.get('Endpoint')
            changed = True

        if changed:
            # modify and create don't return tags
            tags = dms_describe_tags(dmsclient, ResourceArn=endpoint['EndpointArn'])
            endpoint['tags'] = tags
    elif state == 'absent':
        if endpoint:
            delete_results = delete_dms_endpoint(dmsclient, endpoint['EndpointArn'])
            exit_message = delete_results
            endpoint = None
            changed = True
        else:
            changed = False
            exit_message = 'DMS Endpoint does not exist'

    endpoint = camel_dict_to_snake_dict(endpoint or {}, ignore_list=['tags'])
    module.exit_json(changed=changed, endpoint=endpoint, msg=exit_message)


if __name__ == '__main__':
    main()

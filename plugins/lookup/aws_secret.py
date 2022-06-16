# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: aws_secret
author:
  - Aaron Smith (!UNKNOWN) <ajsmith10381@gmail.com>
extends_documentation_fragment:
- amazon.aws.aws_boto3
- amazon.aws.aws_credentials
- amazon.aws.aws_region

short_description: Look up secrets stored in AWS Secrets Manager.
description:
  - Look up secrets stored in AWS Secrets Manager provided the caller
    has the appropriate permissions to read the secret.
  - Lookup is based on the secret's I(Name) value.
  - Optional parameters can be passed into this lookup; I(version_id) and I(version_stage)
options:
  _terms:
    description: Name of the secret to look up in AWS Secrets Manager.
    required: True
  bypath:
    description: A boolean to indicate whether the parameter is provided as a hierarchy.
    default: false
    type: boolean
    version_added: 1.4.0
  nested:
    description: A boolean to indicate the secret contains nested values.
    type: boolean
    default: false
    version_added: 1.4.0
  version_id:
    description: Version of the secret(s).
    required: False
  version_stage:
    description: Stage of the secret version.
    required: False
  join:
    description:
        - Join two or more entries to form an extended secret.
        - This is useful for overcoming the 4096 character limit imposed by AWS.
        - No effect when used with I(bypath).
    type: boolean
    default: false
  on_deleted:
    description:
        - Action to take if the secret has been marked for deletion.
        - C(error) will raise a fatal error when the secret has been marked for deletion.
        - C(skip) will silently ignore the deleted secret.
        - C(warn) will skip over the deleted secret but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
    version_added: 2.0.0
  on_missing:
    description:
        - Action to take if the secret is missing.
        - C(error) will raise a fatal error when the secret is missing.
        - C(skip) will silently ignore the missing secret.
        - C(warn) will skip over the missing secret but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
  on_denied:
    description:
        - Action to take if access to the secret is denied.
        - C(error) will raise a fatal error when access to the secret is denied.
        - C(skip) will silently ignore the denied secret.
        - C(warn) will skip over the denied secret but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
'''

EXAMPLES = r"""
 - name: lookup secretsmanager secret in the current region
   debug: msg="{{ lookup('amazon.aws.aws_secret', '/path/to/secrets', bypath=true) }}"

 - name: Create RDS instance with aws_secret lookup for password param
   rds:
     command: create
     instance_name: app-db
     db_engine: MySQL
     size: 10
     instance_type: db.m1.small
     username: dbadmin
     password: "{{ lookup('amazon.aws.aws_secret', 'DbSecret') }}"
     tags:
       Environment: staging

 - name: skip if secret does not exist
   debug: msg="{{ lookup('amazon.aws.aws_secret', 'secret-not-exist', on_missing='skip')}}"

 - name: warn if access to the secret is denied
   debug: msg="{{ lookup('amazon.aws.aws_secret', 'secret-denied', on_denied='warn')}}"

 - name: lookup secretsmanager secret in the current region using the nested feature
   debug: msg="{{ lookup('amazon.aws.aws_secret', 'secrets.environments.production.password', nested=true) }}"
   # The secret can be queried using the following syntax: `aws_secret_object_name.key1.key2.key3`.
   # If an object is of the form `{"key1":{"key2":{"key3":1}}}` the query would return the value `1`.
 - name: lookup secretsmanager secret in a specific region using specified region and aws profile using nested feature
   debug: >
    msg="{{ lookup('amazon.aws.aws_secret', 'secrets.environments.production.password', region=region, aws_profile=aws_profile,
    aws_access_key=aws_access_key, aws_secret_key=aws_secret_key, nested=true) }}"
   # The secret can be queried using the following syntax: `aws_secret_object_name.key1.key2.key3`.
   # If an object is of the form `{"key1":{"key2":{"key3":1}}}` the query would return the value `1`.
   # Region is the AWS region where the AWS secret is stored.
   # AWS_profile is the aws profile to use, that has access to the AWS secret.
"""

RETURN = r"""
_raw:
  description:
    Returns the value of the secret stored in AWS Secrets Manager.
"""

import json

try:
    import botocore
except ImportError:
    pass  # will be captured by imported AWSLookupModule

from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.plugin_utils.modules import AWSLookupModule


class LookupModule(AWSLookupModule):
    @AWSLookupModule.aws_error_handler('retreive secret')
    @AWSRetry.jittered_backoff()
    def _list_secrets(self, client, **params):
        paginator = client.get_paginator('list_secrets')
        return paginator.paginate(**params).build_full_result()['SecretList']

    @AWSRetry.jittered_backoff()
    def _get_secret_value(self, client, **params):
        return client.get_secret_value(**params)

    @AWSLookupModule.aws_error_handler('retreive secret')
    def get_secret_value(self, term, client, version_stage=None, version_id=None, on_missing=None, on_denied=None, on_deleted=None, nested=False):
        params = {}
        params['SecretId'] = term
        if version_id:
            params['VersionId'] = version_id
        if version_stage:
            params['VersionStage'] = version_stage
        if nested:
            if len(term.split('.')) < 2:
                self.fail("Nested query must use the following syntax: `aws_secret_name.<key_name>.<key_name>")
            secret_name = term.split('.')[0]
            params['SecretId'] = secret_name

        try:
            response = self._get_secret_value(client, **params)
            if 'SecretBinary' in response:
                return response['SecretBinary']
            if 'SecretString' in response:
                if nested:
                    secrets = []
                    query = term.split('.')[1:]
                    secret_string = json.loads(response['SecretString'])
                    ret_val = secret_string
                    for key in query:
                        if key in ret_val:
                            ret_val = ret_val[key]
                        else:
                            self.fail("Successfully retrieved secret but there exists no key {0} in the secret".format(key))
                    return str(ret_val)
                else:
                    return response['SecretString']
        except is_boto3_error_message('marked for deletion'):
            if on_deleted == 'error':
                self.fail("Failed to find secret {0} (marked for deletion)".format(term))
            elif on_deleted == 'warn':
                self.warn('Skipping, did not find secret (marked for deletion) {0}'.format(term))
        except is_boto3_error_code('ResourceNotFoundException'):  # pylint: disable=duplicate-except
            if on_missing == 'error':
                self.fail("Failed to find secret {0} (ResourceNotFound)".format(term))
            elif on_missing == 'warn':
                self.warn('Skipping, did not find secret {0}'.format(term))
        except is_boto3_error_code('AccessDeniedException'):  # pylint: disable=duplicate-except
            if on_denied == 'error':
                self.fail("Failed to access secret {0} (AccessDenied)".format(term))
            elif on_denied == 'warn':
                self.warn('Skipping, access denied for secret {0}'.format(term))

        return None

    def run(self, terms, variables=None, **kwargs):
        '''
                   :arg terms: a list of lookups to run.
                       e.g. ['parameter_name', 'parameter_name_too' ]
                   :kwarg variables: ansible variables active at the time of the lookup
                   :kwarg aws_secret_key: identity of the AWS key to use
                   :kwarg aws_access_key: AWS secret key (matching identity)
                   :kwarg aws_security_token: AWS session key if using STS
                   :kwarg decrypt: Set to True to get decrypted parameters
                   :kwarg region: AWS region in which to do the lookup
                   :kwarg bypath: Set to True to do a lookup of variables under a path
                   :kwarg nested: Set to True to do a lookup of nested secrets
                   :kwarg join: Join two or more entries to form an extended secret
                   :kwarg version_stage: Stage of the secret version
                   :kwarg version_id: Version of the secret(s)
                   :kwarg on_missing: Action to take if the secret is missing
                   :kwarg on_deleted: Action to take if the secret is marked for deletion
                   :kwarg on_denied: Action to take if access to the secret is denied
                   :returns: A list of parameter values or a list of dictionaries if bypath=True.
               '''
        super(LookupModule, self).run(terms, variables, **kwargs)
        bypath = kwargs.get('bypath', False)
        nested = kwargs.get('nested', False)
        join = kwargs.get('join', False)
        version_stage = kwargs.get('version_stage', None)
        version_id = kwargs.get('version_id', None)
        missing = kwargs.get('on_missing', 'error').lower()
        denied = kwargs.get('on_denied', 'error').lower()
        deleted = kwargs.get('on_deleted', 'error').lower()

        if not isinstance(deleted, string_types) or deleted not in ['error', 'warn', 'skip']:
            self.fail('"on_deleted" must be a string and one of "error", "warn" or "skip", not {0}'.format(deleted))

        if not isinstance(missing, string_types) or missing not in ['error', 'warn', 'skip']:
            self.fail('"on_missing" must be a string and one of "error", "warn" or "skip", not {0}'.format(missing))

        if not isinstance(denied, string_types) or denied not in ['error', 'warn', 'skip']:
            self.fail('"on_denied" must be a string and one of "error", "warn" or "skip", not {0}'.format(denied))

        client = self.client('secretsmanager')

        if bypath:
            secrets = {}
            for term in terms:
                secrets_list = self._list_secrets(client, Filters=[{'Key': 'name', 'Values': [term]}])
                for secret_obj in secrets_list:
                    secrets.update({secret_obj['Name']: self.get_secret_value(
                        secret_obj['Name'], client, on_missing=missing, on_denied=denied)})
                secrets = [secrets]
        else:
            secrets = []
            for term in terms:
                value = self.get_secret_value(term, client,
                                              version_stage=version_stage, version_id=version_id,
                                              on_missing=missing, on_denied=denied, on_deleted=deleted,
                                              nested=nested)
                if value:
                    secrets.append(value)
            if join:
                joined_secret = []
                joined_secret.append(''.join(secrets))
                return joined_secret

        return secrets

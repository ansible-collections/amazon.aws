# (c) 2016, Bill Wang <ozbillwang(at)gmail.com>
# (c) 2017, Marat Bakeev <hawara(at)gmail.com>
# (c) 2018, Michael De La Rue <siblemitcom.mddlr(at)spamgourmet.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
name: aws_ssm
author:
  - Bill Wang (!UNKNOWN) <ozbillwang(at)gmail.com>
  - Marat Bakeev (!UNKNOWN) <hawara(at)gmail.com>
  - Michael De La Rue (!UNKNOWN) <siblemitcom.mddlr@spamgourmet.com>
short_description: Get the value for a SSM parameter or all parameters under a path.
description:
  - Get the value for an Amazon Simple Systems Manager parameter or a hierarchy of parameters.
    The first argument you pass the lookup can either be a parameter name or a hierarchy of
    parameters. Hierarchies start with a forward slash and end with the parameter name. Up to
    5 layers may be specified.
  - If looking up an explicitly listed parameter by name which does not exist then the lookup
    will generate an error. You can use the ```default``` filter to give a default value in
    this case but must set the ```on_missing``` parameter to ```skip``` or ```warn```. You must
    also set the second parameter of the ```default``` filter to ```true``` (see examples below).
  - When looking up a path for parameters under it a dictionary will be returned for each path.
    If there is no parameter under that path then the lookup will generate an error.
  - If the lookup fails due to lack of permissions or due to an AWS client error then the aws_ssm
    will generate an error. If you want to continue in this case then you will have to set up
    two ansible tasks, one which sets a variable and ignores failures and one which uses the value
    of that variable with a default.  See the examples below.

options:
  decrypt:
    description: A boolean to indicate whether to decrypt the parameter.
    default: true
    type: boolean
  bypath:
    description: A boolean to indicate whether the parameter is provided as a hierarchy.
    default: false
    type: boolean
  recursive:
    description: A boolean to indicate whether to retrieve all parameters within a hierarchy.
    default: false
    type: boolean
  shortnames:
    description: Indicates whether to return the name only without path if using a parameter hierarchy.
    default: false
    type: boolean
  on_missing:
    description:
        - Action to take if the SSM parameter is missing.
        - C(error) will raise a fatal error when the SSM parameter is missing.
        - C(skip) will silently ignore the missing SSM parameter.
        - C(warn) will skip over the missing SSM parameter but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
    version_added: 2.0.0
  on_denied:
    description:
        - Action to take if access to the SSM parameter is denied.
        - C(error) will raise a fatal error when access to the SSM parameter is denied.
        - C(skip) will silently ignore the denied SSM parameter.
        - C(warn) will skip over the denied SSM parameter but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
    version_added: 2.0.0
  endpoint:
    description: Use a custom endpoint when connecting to SSM service.
    type: string
    version_added: 3.3.0
extends_documentation_fragment:
- amazon.aws.aws_boto3
- amazon.aws.aws_credentials
- amazon.aws.aws_region
'''

EXAMPLES = '''
# lookup sample:
- name: lookup ssm parameter store in the current region
  debug: msg="{{ lookup('aws_ssm', 'Hello' ) }}"

- name: lookup ssm parameter store in specified region
  debug: msg="{{ lookup('aws_ssm', 'Hello', region='us-east-2' ) }}"

- name: lookup ssm parameter store without decryption
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=False ) }}"

- name: lookup ssm parameter store using a specified aws profile
  debug: msg="{{ lookup('aws_ssm', 'Hello', aws_profile='myprofile' ) }}"

- name: lookup ssm parameter store using explicit aws credentials
  debug: msg="{{ lookup('aws_ssm', 'Hello', aws_access_key=my_aws_access_key, aws_secret_key=my_aws_secret_key, aws_security_token=my_security_token ) }}"

- name: lookup ssm parameter store with all options
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=false, region='us-east-2', aws_profile='myprofile') }}"

- name: lookup ssm parameter and fail if missing
  debug: msg="{{ lookup('aws_ssm', 'missing-parameter') }}"

- name: lookup a key which doesn't exist, returning a default ('root')
  debug: msg="{{ lookup('aws_ssm', 'AdminID', on_missing="skip") | default('root', true) }}"

- name: lookup a key which doesn't exist failing to store it in a fact
  set_fact:
    temp_secret: "{{ lookup('aws_ssm', '/NoAccess/hiddensecret') }}"
  ignore_errors: true

- name: show fact default to "access failed" if we don't have access
  debug: msg="{{ 'the secret was:' ~ temp_secret | default('could not access secret') }}"

- name: return a dictionary of ssm parameters from a hierarchy path
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region='ap-southeast-2', bypath=true, recursive=true ) }}"

- name: return a dictionary of ssm parameters from a hierarchy path with shortened names (param instead of /PATH/to/param)
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region='ap-southeast-2', shortnames=true, bypath=true, recursive=true ) }}"

- name: Iterate over a parameter hierarchy (one iteration per parameter)
  debug: msg='Key contains {{ item.key }} , with value {{ item.value }}'
  loop: '{{ lookup("aws_ssm", "/demo/", region="ap-southeast-2", bypath=True) | dict2items }}'

- name: Iterate over multiple paths as dictionaries (one iteration per path)
  debug: msg='Path contains {{ item }}'
  loop: '{{ lookup("aws_ssm", "/demo/", "/demo1/", bypath=True)}}'

- name: lookup ssm parameter warn if access is denied
  debug: msg="{{ lookup('aws_ssm', 'missing-parameter', on_denied="warn" ) }}"
'''

try:
    import botocore
except ImportError:
    pass  # will be captured by imported AWSLookupModule

from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code

from ansible_collections.amazon.aws.plugins.plugin_utils.modules import AWSLookupModule


class LookupModule(AWSLookupModule):
    @AWSRetry.jittered_backoff()
    def _get_parameter(self, client, **params):
        response = client.get_parameter(**params)
        return response['Parameter']['Value']

    @AWSRetry.jittered_backoff()
    def _get_parameters_by_path(self, client, **params):
        paginator = client.get_paginator('get_parameters_by_path')
        return paginator.paginate(**params).build_full_result()['Parameters']

    @AWSLookupModule.aws_error_handler('retreive parameters by path')
    def get_path_parameters(self, client, ssm_dict, term, on_missing, on_denied):
        ssm_dict["Path"] = term
        try:
            paramlist = self._get_parameters_by_path(client, **ssm_dict)
        except is_boto3_error_code('AccessDeniedException'):
            if on_denied == 'error':
                self.fail("Failed to access SSM parameter path %s (AccessDenied)" % term)
            elif on_denied == 'warn':
                self.warn('Skipping, access denied for SSM parameter path %s' % term)
                paramlist = [{}]
            elif on_denied == 'skip':
                paramlist = [{}]

        if not len(paramlist):
            if on_missing == "error":
                self.fail("Failed to find SSM parameter path %s (ResourceNotFound)" % term)
            elif on_missing == "warn":
                self.warn('Skipping, did not find SSM parameter path %s' % term)

        return paramlist

    @AWSLookupModule.aws_error_handler('retreive parameter')
    def get_parameter_value(self, client, ssm_dict, term, on_missing, on_denied):
        ssm_dict["Name"] = term
        try:
            return self._get_parameter(client, **ssm_dict)
        except is_boto3_error_code('ParameterNotFound'):
            if on_missing == 'error':
                self.fail("Failed to find SSM parameter %s (ResourceNotFound)" % term)
            elif on_missing == 'warn':
                self.warn('Skipping, did not find SSM parameter %s' % term)
        except is_boto3_error_code('AccessDeniedException'):  # pylint: disable=duplicate-except
            if on_denied == 'error':
                self.fail("Failed to access SSM parameter %s (AccessDenied)" % term)
            elif on_denied == 'warn':
                self.warn('Skipping, access denied for SSM parameter %s' % term)
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
            :kwarg recursive: Set to True to recurse below the path (requires bypath=True)
            :kwarg on_missing: Action to take if the SSM parameter is missing
            :kwarg on_denied: Action to take if access to the SSM parameter is denied
            :kwarg endpoint: Endpoint for SSM client
            :returns: A list of parameter values or a list of dictionaries if bypath=True.
        '''

        super(LookupModule, self).run(terms, variables, **kwargs)

        bypath = kwargs.get('bypath', False)
        shortnames = kwargs.get('shortnames', False)
        recursive = kwargs.get('recursive', False)
        decrypt = kwargs.get('decrypt', True)
        on_missing = kwargs.get('on_missing', 'error').lower()
        on_denied = kwargs.get('on_denied', 'error').lower()

        # validate arguments 'on_missing' and 'on_denied'
        if not isinstance(on_missing, string_types) or on_missing not in ['error', 'warn', 'skip']:
            self.fail('"on_missing" must be a string and one of "error", "warn" or "skip", not {0}'.format(on_missing))
        if not isinstance(on_denied, string_types) or on_denied not in ['error', 'warn', 'skip']:
            self.fail('"on_denied" must be a string and one of "error", "warn" or "skip", not {0}'.format(on_denied))

        ret = []
        ssm_dict = {}

        client = self.client('ssm')

        ssm_dict['WithDecryption'] = decrypt

        # Lookup by path
        if bypath:
            ssm_dict['Recursive'] = recursive
            for term in terms:
                self.debug("AWS_ssm path lookup term: %s" % (term))

                paramlist = self.get_path_parameters(client, ssm_dict, term, on_missing.lower(), on_denied.lower())
                # Shorten parameter names. Yes, this will return
                # duplicate names with different values.
                if shortnames:
                    for x in paramlist:
                        x['Name'] = x['Name'][x['Name'].rfind('/') + 1:]

                self.debug("AWS_ssm path lookup returned: %s" % str(paramlist))

                ret.append(boto3_tag_list_to_ansible_dict(paramlist,
                                                          tag_name_key_name="Name",
                                                          tag_value_key_name="Value"))
        # Lookup by parameter name - always returns a list with one or
        # no entry.
        else:
            self.debug("AWS_ssm name lookup term: %s" % terms)
            for term in terms:
                ret.append(self.get_parameter_value(client, ssm_dict, term, on_missing, on_denied))
        self.debug("AWS_ssm path lookup returning: %s " % str(ret))
        return ret

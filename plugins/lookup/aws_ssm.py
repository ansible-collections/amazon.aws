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
  - If looking up an explicitly listed parameter by name which does not exist then the lookup will
    return a None value which will be interpreted by Jinja2 as an empty string.  You can use the
    ```default``` filter to give a default value in this case but must set the second parameter to
    true (see examples below)
  - When looking up a path for parameters under it a dictionary will be returned for each path.
    If there is no parameter under that path then the return will be successful but the
    dictionary will be empty.
  - If the lookup fails due to lack of permissions or due to an AWS client error then the aws_ssm
    will generate an error, normally crashing the current ansible task.  This is normally the right
    thing since ignoring a value that IAM isn't giving access to could cause bigger problems and
    wrong behaviour or loss of data.  If you want to continue in this case then you will have to set
    up two ansible tasks, one which sets a variable and ignores failures one which uses the value
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
'''

EXAMPLES = '''
# lookup sample:
- name: lookup ssm parameter store in the current region
  debug: msg="{{ lookup('aws_ssm', 'Hello' ) }}"

- name: lookup ssm parameter store in nominated region
  debug: msg="{{ lookup('aws_ssm', 'Hello', region='us-east-2' ) }}"

- name: lookup ssm parameter store without decrypted
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=False ) }}"

- name: lookup ssm parameter store in nominated aws profile
  debug: msg="{{ lookup('aws_ssm', 'Hello', aws_profile='myprofile' ) }}"

- name: lookup ssm parameter store using explicit aws credentials
  debug: msg="{{ lookup('aws_ssm', 'Hello', aws_access_key=my_aws_access_key, aws_secret_key=my_aws_secret_key, aws_security_token=my_security_token ) }}"

- name: lookup ssm parameter store with all options.
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=false, region='us-east-2', aws_profile='myprofile') }}"

- name: lookup a key which doesn't exist, returns ""
  debug: msg="{{ lookup('aws_ssm', 'NoKey') }}"

- name: lookup a key which doesn't exist, returning a default ('root')
  debug: msg="{{ lookup('aws_ssm', 'AdminID') | default('root', true) }}"

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

- name: lookup ssm parameter and fail if missing
  debug: msg="{{ lookup('aws_ssm', 'missing-parameter', on_missing="error" ) }}"

- name: lookup ssm parameter warn if access is denied
  debug: msg="{{ lookup('aws_ssm', 'missing-parameter', on_denied="warn" ) }}"
'''

try:
    import botocore
    import boto3
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_conn
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code

display = Display()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, boto_profile=None, aws_profile=None,
            aws_secret_key=None, aws_access_key=None, aws_security_token=None, region=None,
            bypath=False, shortnames=False, recursive=False, decrypt=True, on_missing="skip",
            on_denied="skip", endpoint=None):
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

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required for aws_ssm lookup.')

        # validate arguments 'on_missing' and 'on_denied'
        if on_missing is not None and (not isinstance(on_missing, string_types) or on_missing.lower() not in ['error', 'warn', 'skip']):
            raise AnsibleError('"on_missing" must be a string and one of "error", "warn" or "skip", not %s' % on_missing)
        if on_denied is not None and (not isinstance(on_denied, string_types) or on_denied.lower() not in ['error', 'warn', 'skip']):
            raise AnsibleError('"on_denied" must be a string and one of "error", "warn" or "skip", not %s' % on_denied)

        ret = []
        ssm_dict = {}

        self.params = variables

        cli_region, cli_endpoint, cli_boto_params = get_aws_connection_info(self, boto3=True)

        if region:
            cli_region = region

        if endpoint:
            cli_endpoint = endpoint

        # For backward  compatibility
        if aws_access_key:
            cli_boto_params.update({'aws_access_key_id': aws_access_key})
        if aws_secret_key:
            cli_boto_params.update({'aws_secret_access_key': aws_secret_key})
        if aws_security_token:
            cli_boto_params.update({'aws_session_token': aws_security_token})
        if boto_profile:
            cli_boto_params.update({'profile_name': boto_profile})
        if aws_profile:
            cli_boto_params.update({'profile_name': aws_profile})

        cli_boto_params.update(dict(
            conn_type='client',
            resource='ssm',
            region=cli_region,
            endpoint=cli_endpoint,
        ))

        client = boto3_conn(module=self, **cli_boto_params)

        ssm_dict['WithDecryption'] = decrypt

        # Lookup by path
        if bypath:
            ssm_dict['Recursive'] = recursive
            for term in terms:
                ssm_dict["Path"] = term
                display.vvv("AWS_ssm path lookup term: %s in region: %s" % (term, region))
                try:
                    response = client.get_parameters_by_path(**ssm_dict)
                except botocore.exceptions.ClientError as e:
                    raise AnsibleError("SSM lookup exception: {0}".format(to_native(e)))
                paramlist = list()
                paramlist.extend(response['Parameters'])

                # Manual pagination, since boto doesn't support it yet for get_parameters_by_path
                while 'NextToken' in response:
                    response = client.get_parameters_by_path(NextToken=response['NextToken'], **ssm_dict)
                    paramlist.extend(response['Parameters'])

                # shorten parameter names. yes, this will return duplicate names with different values.
                if shortnames:
                    for x in paramlist:
                        x['Name'] = x['Name'][x['Name'].rfind('/') + 1:]

                display.vvvv("AWS_ssm path lookup returned: %s" % str(paramlist))
                if len(paramlist):
                    ret.append(boto3_tag_list_to_ansible_dict(paramlist,
                                                              tag_name_key_name="Name",
                                                              tag_value_key_name="Value"))
                else:
                    ret.append({})
            # Lookup by parameter name - always returns a list with one or no entry.
        else:
            display.vvv("AWS_ssm name lookup term: %s" % terms)
            for term in terms:
                ret.append(self.get_parameter_value(client, ssm_dict, term, on_missing.lower(), on_denied.lower()))
        display.vvvv("AWS_ssm path lookup returning: %s " % str(ret))
        return ret

    def get_parameter_value(self, client, ssm_dict, term, on_missing, on_denied):
        ssm_dict["Name"] = term
        try:
            response = client.get_parameter(**ssm_dict)
            return response['Parameter']['Value']
        except is_boto3_error_code('ParameterNotFound'):
            if on_missing == 'error':
                raise AnsibleError("Failed to find SSM parameter %s (ResourceNotFound)" % term)
            elif on_missing == 'warn':
                self._display.warning('Skipping, did not find SSM parameter %s' % term)
        except is_boto3_error_code('AccessDeniedException'):  # pylint: disable=duplicate-except
            if on_denied == 'error':
                raise AnsibleError("Failed to access SSM parameter %s (AccessDenied)" % term)
            elif on_denied == 'warn':
                self._display.warning('Skipping, access denied for SSM parameter %s' % term)
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            raise AnsibleError("SSM lookup exception: {0}".format(to_native(e)))
        return None

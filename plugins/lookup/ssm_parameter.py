# -*- coding: utf-8 -*-

# (c) 2016, Bill Wang <ozbillwang(at)gmail.com>
# (c) 2017, Marat Bakeev <hawara(at)gmail.com>
# (c) 2018, Michael De La Rue <siblemitcom.mddlr(at)spamgourmet.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: ssm_parameter
author:
  - Bill Wang (!UNKNOWN) <ozbillwang(at)gmail.com>
  - Marat Bakeev (!UNKNOWN) <hawara(at)gmail.com>
  - Michael De La Rue (!UNKNOWN) <siblemitcom.mddlr@spamgourmet.com>
short_description: gets the value for a SSM parameter or all parameters under a path
description:
  - Get the value for an Amazon Simple Systems Manager parameter or a hierarchy of parameters.
    The first argument you pass the lookup can either be a parameter name or a hierarchy of
    parameters. Hierarchies start with a forward slash and end with the parameter name. Up to
    5 layers may be specified.
  - If looking up an explicitly listed parameter by name which does not exist then the lookup
    will generate an error. You can use the C(default) filter to give a default value in
    this case but must set the I(on_missing) parameter to C(skip) or C(warn). You must
    also set the second parameter of the C(default) filter to C(true) (see examples below).
  - When looking up a path for parameters under it a dictionary will be returned for each path.
    If there is no parameter under that path then the lookup will generate an error.
  - If the lookup fails due to lack of permissions or due to an AWS client error then the aws_ssm
    will generate an error. If you want to continue in this case then you will have to set up
    two ansible tasks, one which sets a variable and ignores failures and one which uses the value
    of that variable with a default.  See the examples below.
  - Prior to release 6.0.0 this module was known as C(aws_ssm), the usage remains the same.

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
extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.plugins
  - amazon.aws.region.plugins
"""

EXAMPLES = r"""
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
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AWSLookupBase

from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_native
from ansible.utils.display import Display
from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import AWSLookupBase

display = Display()


class LookupModule(AWSLookupBase):
    def run(self, terms, variables, **kwargs):
        """
        :arg terms: a list of lookups to run.
            e.g. ['parameter_name', 'parameter_name_too' ]
        :kwarg variables: ansible variables active at the time of the lookup
        :returns: A list of parameter values or a list of dictionaries if bypath=True.
        """

        super().run(terms, variables, **kwargs)

        on_missing = self.get_option("on_missing")
        on_denied = self.get_option("on_denied")

        # validate arguments 'on_missing' and 'on_denied'
        if on_missing is not None and (
            not isinstance(on_missing, string_types) or on_missing.lower() not in ["error", "warn", "skip"]
        ):
            raise AnsibleLookupError(
                f'"on_missing" must be a string and one of "error", "warn" or "skip", not {on_missing}'
            )
        if on_denied is not None and (
            not isinstance(on_denied, string_types) or on_denied.lower() not in ["error", "warn", "skip"]
        ):
            raise AnsibleLookupError(
                f'"on_denied" must be a string and one of "error", "warn" or "skip", not {on_denied}'
            )

        ret = []
        ssm_dict = {}

        client = self.client("ssm", AWSRetry.jittered_backoff())

        ssm_dict["WithDecryption"] = self.get_option("decrypt")

        # Lookup by path
        if self.get_option("bypath"):
            ssm_dict["Recursive"] = self.get_option("recursive")
            for term in terms:
                display.vvv(f"AWS_ssm path lookup term: {term} in region: {self.region}")

                paramlist = self.get_path_parameters(client, ssm_dict, term, on_missing.lower(), on_denied.lower())
                # Shorten parameter names. Yes, this will return
                # duplicate names with different values.
                if self.get_option("shortnames"):
                    for x in paramlist:
                        x["Name"] = x["Name"][x["Name"].rfind("/") + 1:]  # fmt: skip

                display.vvvv(f"AWS_ssm path lookup returned: {to_native(paramlist)}")

                ret.append(
                    boto3_tag_list_to_ansible_dict(paramlist, tag_name_key_name="Name", tag_value_key_name="Value")
                )
        # Lookup by parameter name - always returns a list with one or
        # no entry.
        else:
            display.vvv(f"AWS_ssm name lookup term: {terms}")
            for term in terms:
                ret.append(self.get_parameter_value(client, ssm_dict, term, on_missing.lower(), on_denied.lower()))
        display.vvvv(f"AWS_ssm path lookup returning: {to_native(ret)} ")
        return ret

    def get_path_parameters(self, client, ssm_dict, term, on_missing, on_denied):
        ssm_dict["Path"] = term
        paginator = client.get_paginator("get_parameters_by_path")
        try:
            paramlist = paginator.paginate(**ssm_dict).build_full_result()["Parameters"]
        except is_boto3_error_code("AccessDeniedException"):
            if on_denied == "error":
                raise AnsibleLookupError(f"Failed to access SSM parameter path {term} (AccessDenied)")
            elif on_denied == "warn":
                self.warn(f"Skipping, access denied for SSM parameter path {term}")
                paramlist = [{}]
            elif on_denied == "skip":
                paramlist = [{}]
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            raise AnsibleLookupError(f"SSM lookup exception: {to_native(e)}")

        if not len(paramlist):
            if on_missing == "error":
                raise AnsibleLookupError(f"Failed to find SSM parameter path {term} (ResourceNotFound)")
            elif on_missing == "warn":
                self.warn(f"Skipping, did not find SSM parameter path {term}")

        return paramlist

    def get_parameter_value(self, client, ssm_dict, term, on_missing, on_denied):
        ssm_dict["Name"] = term
        try:
            response = client.get_parameter(aws_retry=True, **ssm_dict)
            return response["Parameter"]["Value"]
        except is_boto3_error_code("ParameterNotFound"):
            if on_missing == "error":
                raise AnsibleLookupError(f"Failed to find SSM parameter {term} (ResourceNotFound)")
            elif on_missing == "warn":
                self.warn(f"Skipping, did not find SSM parameter {term}")
        except is_boto3_error_code("AccessDeniedException"):  # pylint: disable=duplicate-except
            if on_denied == "error":
                raise AnsibleLookupError(f"Failed to access SSM parameter {term} (AccessDenied)")
            elif on_denied == "warn":
                self.warn(f"Skipping, access denied for SSM parameter {term}")
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            raise AnsibleLookupError(f"SSM lookup exception: {to_native(e)}")
        return None

# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: secretsmanager_secret
author:
  - Aaron Smith (!UNKNOWN) <ajsmith10381@gmail.com>

short_description: Look up secrets stored in AWS Secrets Manager
description:
  - Look up secrets stored in AWS Secrets Manager provided the caller
    has the appropriate permissions to read the secret.
  - Lookup is based on the secret's I(Name) value.
  - Optional parameters can be passed into this lookup; O(version_id) and O(version_stage).
  - Prior to release 6.0.0 this module was known as C(aws_ssm), the usage remains the same.

options:
  _terms:
    description: Name of the secret to look up in AWS Secrets Manager.
    required: true
  bypath:
    description: A boolean to indicate whether the parameter is provided as a hierarchy.
    default: false
    type: bool
    version_added: 1.4.0
  nested:
    description: A boolean to indicate the secret contains nested values.
    type: bool
    default: false
    version_added: 1.4.0
  version_id:
    description: Version of the secret(s).
    required: false
  version_stage:
    description: Stage of the secret version.
    required: false
  join:
    description:
      - Join two or more entries to form an extended secret.
      - This is useful for overcoming the 4096 character limit imposed by AWS.
      - No effect when used with O(bypath).
    type: bool
    default: false
  on_deleted:
    description:
      - Action to take if the secret has been marked for deletion.
      - V(error) will raise a fatal error when the secret has been marked for deletion.
      - V(skip) will silently ignore the deleted secret.
      - V(warn) will skip over the deleted secret but issue a warning.
    default: "error"
    type: str
    choices: ["error", "skip", "warn"]
    version_added: 2.0.0
  on_missing:
    description:
      - Action to take if the secret is missing.
      - C(error) will raise a fatal error when the secret is missing.
      - C(skip) will silently ignore the missing secret.
      - C(warn) will skip over the missing secret but issue a warning.
    default: "error"
    type: str
    choices: ["error", "skip", "warn"]
  on_denied:
    description:
      - Action to take if access to the secret is denied.
      - C(error) will raise a fatal error when access to the secret is denied.
      - C(skip) will silently ignore the denied secret.
      - C(warn) will skip over the denied secret but issue a warning.
    default: "error"
    type: str
    choices: ["error", "skip", "warn"]
extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.plugins
  - amazon.aws.region.plugins
"""

EXAMPLES = r"""
- name: Lookup secretsmanager secret in the current region
  ansible.builtin.debug: msg="{{ lookup('amazon.aws.aws_secret', '/path/to/secrets', bypath=true) }}"

- name: Create RDS instance with aws_secret lookup for password param
  amazon.aws.rds_instance:
    state: present
    db_instance_identifier: app-db
    engine: mysql
    instance_type: db.m1.small
    username: dbadmin
    password: "{{ lookup('amazon.aws.aws_secret', 'DbSecret') }}"
    tags:
      Environment: staging

- name: Skip if secret does not exist
  ansible.builtin.debug: msg="{{ lookup('amazon.aws.aws_secret', 'secret-not-exist', on_missing='skip')}}"

- name: Warn if access to the secret is denied
  ansible.builtin.debug: msg="{{ lookup('amazon.aws.aws_secret', 'secret-denied', on_denied='warn')}}"

- name: Lookup secretsmanager secret in the current region using the nested feature
  ansible.builtin.debug: msg="{{ lookup('amazon.aws.aws_secret', 'secrets.environments.production.password', nested=true) }}"
  # The secret can be queried using the following syntax: `aws_secret_object_name.key1.key2.key3`.
  # If an object is of the form `{"key1":{"key2":{"key3":1}}}` the query would return the value `1`.
- name: Lookup secretsmanager secret in a specific region using specified region and aws profile using nested feature
  ansible.builtin.debug: >
   msg="{{ lookup('amazon.aws.aws_secret', 'secrets.environments.production.password', region=region, profile=aws_profile,
   access_key=aws_access_key, secret_key=aws_secret_key, nested=true) }}"
  # The secret can be queried using the following syntax: `aws_secret_object_name.key1.key2.key3`.
  # If an object is of the form `{"key1":{"key2":{"key3":1}}}` the query would return the value `1`.
  # Region is the AWS region where the AWS secret is stored.
  # AWS_profile is the aws profile to use, that has access to the AWS secret.
"""

RETURN = r"""
_raw:
  description: Returns the value of the secret stored in AWS Secrets Manager.
"""

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AWSLookupBase

from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import AWSLookupBase
from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import LookupErrorHandler
from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import NestedKeyNotFoundError


class LookupModule(AWSLookupBase):
    _SERVICE = "secretsmanager"

    def run(self, terms, variables, **kwargs):
        """
        :arg terms: a list of lookups to run.
            e.g. ['example_secret_name', 'example_secret_too' ]
        :variables: ansible variables active at the time of the lookup
        :returns: A list of parameter values or a list of dictionaries if bypath=True.
        """

        super().run(terms, variables, **kwargs)

        on_missing = self.get_option("on_missing")
        on_denied = self.get_option("on_denied")
        on_deleted = self.get_option("on_deleted")

        self._validate_options(on_missing, on_denied, on_deleted)

        if self.get_option("bypath"):
            return self._lookup_by_path(terms, on_missing, on_denied)
        else:
            return self._lookup_by_name(terms, on_missing, on_denied, on_deleted)

    def _validate_options(self, on_missing, on_denied, on_deleted):
        """Validate on_missing, on_denied and on_deleted options"""
        if on_missing is not None and (
            not isinstance(on_missing, str) or on_missing.lower() not in ["error", "warn", "skip"]
        ):
            raise AnsibleLookupError(
                f'"on_missing" must be a string and one of "error", "warn" or "skip", not {on_missing}'
            )
        if on_denied is not None and (
            not isinstance(on_denied, str) or on_denied.lower() not in ["error", "warn", "skip"]
        ):
            raise AnsibleLookupError(
                f'"on_denied" must be a string and one of "error", "warn" or "skip", not {on_denied}'
            )
        if on_deleted is not None and (
            not isinstance(on_deleted, str) or on_deleted.lower() not in ["error", "warn", "skip"]
        ):
            raise AnsibleLookupError(
                f'"on_deleted" must be a string and one of "error", "warn" or "skip", not {on_deleted}'
            )

    def _list_secrets(self, term):
        """List secrets matching the given term"""
        paginator = self.aws_client.get_paginator("list_secrets")
        return paginator.paginate(Filters=[{"Key": "name", "Values": [term]}])

    def _lookup_by_path(self, terms, on_missing, on_denied):
        """Lookup secrets by path"""
        secrets = {}
        for term in terms:
            try:
                for secret_wrapper in self._list_secrets(term):
                    if "SecretList" in secret_wrapper:
                        for secret_obj in secret_wrapper["SecretList"]:
                            secrets.update({secret_obj["Name"]: self.get_secret_value(secret_obj["Name"])})
                secrets = [secrets]

            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                raise AnsibleLookupError(f"Failed to retrieve secret: {to_native(e)}")

        return secrets

    def _lookup_by_name(self, terms, on_missing, on_denied, on_deleted):
        """Lookup secrets by name"""
        secrets = []
        for term in terms:
            value = self.get_secret_value(
                term,
                version_stage=self.get_option("version_stage"),
                version_id=self.get_option("version_id"),
                nested=self.get_option("nested"),
            )
            if value:
                secrets.append(value)

        if self.get_option("join"):
            return ["".join(secrets)]

        return secrets

    @LookupErrorHandler.handle_lookup_errors("secret")
    def get_secret_value(
        self,
        term,
        version_stage=None,
        version_id=None,
        nested=False,
    ):
        """
        Retrieve a secret value from AWS Secrets Manager.

        Note: on_missing, on_denied, and on_deleted are read by the decorator from self.get_option().
        """
        params = self._build_secret_params(term, version_id, version_stage, nested)
        response = self.aws_client.get_secret_value(aws_retry=True, **params)
        return self._process_secret_response(response, term, nested)

    def _build_secret_params(self, term, version_id, version_stage, nested):
        """Build parameters for get_secret_value API call"""
        params = {"SecretId": term}

        if version_id:
            params["VersionId"] = version_id
        if version_stage:
            params["VersionStage"] = version_stage

        if nested:
            if len(term.split(".")) < 2:
                raise AnsibleLookupError(
                    "Nested query must use the following syntax: `aws_secret_name.<key_name>.<key_name>"
                )
            secret_name = term.split(".")[0]
            params["SecretId"] = secret_name

        return params

    def _process_secret_response(self, response, term, nested):
        """Process the secret response from AWS"""
        if "SecretBinary" in response:
            return response["SecretBinary"]

        if "SecretString" in response:
            if nested:
                return self._extract_nested_value(response["SecretString"], term)
            else:
                return response["SecretString"]

        return None

    def _extract_nested_value(self, secret_string, term):
        """
        Extract nested value from secret JSON.

        Raises NestedKeyNotFoundError if any key in the path is not found,
        which is caught by the @handle_lookup_errors decorator.
        """
        query = term.split(".")[1:]
        secret_data = json.loads(secret_string)
        ret_val = secret_data
        path = None

        for key in query:
            path = key if not path else path + "." + key
            try:
                ret_val = ret_val[key]
            except (KeyError, TypeError) as e:
                # KeyError: key not in dict
                # TypeError: trying to access a non-dict (e.g., string) as a dict
                raise NestedKeyNotFoundError(path) from e

        return str(ret_val)

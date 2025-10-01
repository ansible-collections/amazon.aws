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

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import AWSLookupBase


def _list_secrets(client, term):
    paginator = client.get_paginator("list_secrets")
    return paginator.paginate(Filters=[{"Key": "name", "Values": [term]}])


class LookupModule(AWSLookupBase):
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

        # validate arguments 'on_missing' and 'on_denied'
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

        client = self.client("secretsmanager", AWSRetry.jittered_backoff())

        if self.get_option("bypath"):
            secrets = {}
            for term in terms:
                try:
                    for secret_wrapper in _list_secrets(client, term):
                        if "SecretList" in secret_wrapper:
                            for secret_obj in secret_wrapper["SecretList"]:
                                secrets.update(
                                    {
                                        secret_obj["Name"]: self.get_secret_value(
                                            secret_obj["Name"], client, on_missing=on_missing, on_denied=on_denied
                                        )
                                    }
                                )
                    secrets = [secrets]

                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    raise AnsibleLookupError(f"Failed to retrieve secret: {to_native(e)}")
        else:
            secrets = []
            for term in terms:
                value = self.get_secret_value(
                    term,
                    client,
                    version_stage=self.get_option("version_stage"),
                    version_id=self.get_option("version_id"),
                    on_missing=on_missing,
                    on_denied=on_denied,
                    on_deleted=on_deleted,
                    nested=self.get_option("nested"),
                )
                if value:
                    secrets.append(value)
            if self.get_option("join"):
                joined_secret = []
                joined_secret.append("".join(secrets))
                return joined_secret

        return secrets

    def get_secret_value(
        self,
        term,
        client,
        version_stage=None,
        version_id=None,
        on_missing=None,
        on_denied=None,
        on_deleted=None,
        nested=False,
    ):
        params = {}
        params["SecretId"] = term
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

        try:
            response = client.get_secret_value(aws_retry=True, **params)
            if "SecretBinary" in response:
                return response["SecretBinary"]
            if "SecretString" in response:
                if nested:
                    query = term.split(".")[1:]
                    path = None
                    secret_string = json.loads(response["SecretString"])
                    ret_val = secret_string
                    while query:
                        key = query.pop(0)
                        path = key if not path else path + "." + key
                        if key in ret_val:
                            ret_val = ret_val[key]
                        elif on_missing == "warn":
                            self._display.warning(
                                f"Skipping, Successfully retrieved secret but there exists no key {path} in the secret"
                            )
                            return None
                        elif on_missing == "error":
                            raise AnsibleLookupError(
                                f"Successfully retrieved secret but there exists no key {path} in the secret"
                            )
                    return str(ret_val)
                else:
                    return response["SecretString"]
        except is_boto3_error_message("marked for deletion"):
            if on_deleted == "error":
                raise AnsibleLookupError(f"Failed to find secret {term} (marked for deletion)")
            elif on_deleted == "warn":
                self._display.warning(f"Skipping, did not find secret (marked for deletion) {term}")
        except is_boto3_error_code("ResourceNotFoundException"):  # pylint: disable=duplicate-except
            if on_missing == "error":
                raise AnsibleLookupError(f"Failed to find secret {term} (ResourceNotFound)")
            elif on_missing == "warn":
                self._display.warning(f"Skipping, did not find secret {term}")
        except is_boto3_error_code("AccessDeniedException"):  # pylint: disable=duplicate-except
            if on_denied == "error":
                raise AnsibleLookupError(f"Failed to access secret {term} (AccessDenied)")
            elif on_denied == "warn":
                self._display.warning(f"Skipping, access denied for secret {term}")
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:  # pylint: disable=duplicate-except
            raise AnsibleLookupError(f"Failed to retrieve secret: {to_native(e)}")

        return None

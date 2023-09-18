#!/usr/bin/python

# Copyright: (c) 2018, REY Remi
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: secretsmanager_secret
version_added: 1.0.0
short_description: Manage secrets stored in AWS Secrets Manager
description:
  - Create, update, and delete secrets stored in AWS Secrets Manager.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_secret).
    The usage did not change.
author:
  - "REY Remi (@rrey)"
options:
  name:
    description:
    - Friendly name for the secret you are creating.
    required: true
    type: str
  state:
    description:
    - Whether the secret should be exist or not.
    default: 'present'
    choices: ['present', 'absent']
    type: str
  recovery_window:
    description:
    - Only used if state is absent.
    - Specifies the number of days that Secrets Manager waits before it can delete the secret.
    - If set to 0, the deletion is forced without recovery.
    default: 30
    type: int
  description:
    description:
    - Specifies a user-provided description of the secret.
    type: str
  kms_key_id:
    description:
    - Specifies the ARN or alias of the AWS KMS customer master key (CMK) to be
      used to encrypt the I(secret) values in the versions stored in this secret.
    type: str
  secret_type:
    description:
    - Specifies the type of data that you want to encrypt.
    choices: ['binary', 'string']
    default: 'string'
    type: str
  secret:
    description:
    - Specifies string or binary data that you want to encrypt and store in the new version of the secret.
    - Mutually exclusive with the I(json_secret) option.
    default: ""
    type: str
  json_secret:
    description:
    - Specifies JSON-formatted data that you want to encrypt and store in the new version of the
      secret.
    - Mutually exclusive with the I(secret) option.
    type: json
    version_added: 4.1.0
  resource_policy:
    description:
    - Specifies JSON-formatted resource policy to attach to the secret. Useful when granting cross-account access
       to secrets.
    required: false
    type: json
    version_added: 3.1.0
  rotation_lambda:
    description:
    - Specifies the ARN of the Lambda function that can rotate the secret.
    type: str
  rotation_interval:
    description:
    - Specifies the number of days between automatic scheduled rotations of the secret.
    default: 30
    type: int
extends_documentation_fragment:
  - amazon.aws.ec2
  - amazon.aws.aws
  - amazon.aws.boto3
  - amazon.aws.tags
notes:
  - Support for I(purge_tags) was added in release 4.0.0.
'''

EXAMPLES = r'''
- name: Add string to AWS Secrets Manager
  community.aws.secretsmanager_secret:
    name: 'test_secret_string'
    state: present
    secret_type: 'string'
    secret: "{{ super_secret_string }}"

- name: Add a secret with resource policy attached
  community.aws.secretsmanager_secret:
    name: 'test_secret_string'
    state: present
    secret_type: 'string'
    secret: "{{ super_secret_string }}"
    resource_policy: "{{ lookup('template', 'templates/resource_policy.json.j2', convert_data=False) | string }}"

- name: remove string from AWS Secrets Manager
  community.aws.secretsmanager_secret:
    name: 'test_secret_string'
    state: absent
    secret_type: 'string'
    secret: "{{ super_secret_string }}"
'''

RETURN = r'''
secret:
  description: The secret information
  returned: always
  type: complex
  contains:
    arn:
      description: The ARN of the secret.
      returned: always
      type: str
      sample: arn:aws:secretsmanager:eu-west-1:xxxxxxxxxx:secret:xxxxxxxxxxx
    description:
      description: A description of the secret.
      returned: when the secret has a description
      type: str
      sample: An example description
    last_accessed_date:
      description: The date the secret was last accessed.
      returned: always
      type: str
      sample: '2018-11-20T01:00:00+01:00'
    last_changed_date:
      description: The date the secret was last modified.
      returned: always
      type: str
      sample: '2018-11-20T12:16:38.433000+01:00'
    name:
      description: The secret name.
      returned: always
      type: str
      sample: my_secret
    rotation_enabled:
      description: The secret rotation status.
      returned: always
      type: bool
      sample: false
    version_ids_to_stages:
      description: Provide the secret version ids and the associated secret stage.
      returned: always
      type: dict
      sample: { "dc1ed59b-6d8e-4450-8b41-536dfe4600a9": [ "AWSCURRENT" ] }
    tags:
      description:
        - A list of dictionaries representing the tags associated with the secret in the standard boto3 format.
      returned: when the secret has tags
      type: list
      elements: dict
      contains:
        key:
          description: The name or key of the tag.
          type: str
          example: MyTag
          returned: success
        value:
          description: The value of the tag.
          type: str
          example: Some value.
          returned: success
    tags_dict:
      description: A dictionary representing the tags associated with the secret.
      type: dict
      returned: when the secret has tags
      example: {'MyTagName': 'Some Value'}
      version_added: 4.0.0
'''

from ansible.module_utils._text import to_bytes
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict, compare_aws_tags, ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_policies
from traceback import format_exc
import json

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


class Secret(object):
    """An object representation of the Secret described by the self.module args"""
    def __init__(self, name, secret_type, secret, resource_policy=None, description="", kms_key_id=None,
                 tags=None, lambda_arn=None, rotation_interval=None):
        self.name = name
        self.description = description
        self.kms_key_id = kms_key_id
        if secret_type == "binary":
            self.secret_type = "SecretBinary"
        else:
            self.secret_type = "SecretString"
        self.secret = secret
        self.resource_policy = resource_policy
        self.tags = tags or {}
        self.rotation_enabled = False
        if lambda_arn:
            self.rotation_enabled = True
            self.rotation_lambda_arn = lambda_arn
            self.rotation_rules = {"AutomaticallyAfterDays": int(rotation_interval)}

    @property
    def create_args(self):
        args = {
            "Name": self.name
        }
        if self.description:
            args["Description"] = self.description
        if self.kms_key_id:
            args["KmsKeyId"] = self.kms_key_id
        if self.tags:
            args["Tags"] = ansible_dict_to_boto3_tag_list(self.tags)
        args[self.secret_type] = self.secret
        return args

    @property
    def update_args(self):
        args = {
            "SecretId": self.name
        }
        if self.description:
            args["Description"] = self.description
        if self.kms_key_id:
            args["KmsKeyId"] = self.kms_key_id
        args[self.secret_type] = self.secret
        return args

    @property
    def secret_resource_policy_args(self):
        args = {
            "SecretId": self.name
        }
        if self.resource_policy:
            args["ResourcePolicy"] = self.resource_policy
        return args

    @property
    def boto3_tags(self):
        return ansible_dict_to_boto3_tag_list(self.Tags)

    def as_dict(self):
        result = self.__dict__
        result.pop("tags")
        return snake_dict_to_camel_dict(result)


class SecretsManagerInterface(object):
    """An interface with SecretsManager"""

    def __init__(self, module):
        self.module = module
        self.client = self.module.client('secretsmanager')

    def get_secret(self, name):
        try:
            secret = self.client.describe_secret(SecretId=name)
        except self.client.exceptions.ResourceNotFoundException:
            secret = None
        except Exception as e:
            self.module.fail_json_aws(e, msg="Failed to describe secret")
        return secret

    def get_resource_policy(self, name):
        try:
            resource_policy = self.client.get_resource_policy(SecretId=name)
        except self.client.exceptions.ResourceNotFoundException:
            resource_policy = None
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to get secret resource policy")
        return resource_policy

    def create_secret(self, secret):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            created_secret = self.client.create_secret(**secret.create_args)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to create secret")

        if secret.rotation_enabled:
            response = self.update_rotation(secret)
            created_secret["VersionId"] = response.get("VersionId")
        return created_secret

    def update_secret(self, secret):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            response = self.client.update_secret(**secret.update_args)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to update secret")
        return response

    def put_resource_policy(self, secret):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            json.loads(secret.secret_resource_policy_args.get("ResourcePolicy"))
        except (TypeError, ValueError) as e:
            self.module.fail_json(msg="Failed to parse resource policy as JSON: %s" % (str(e)), exception=format_exc())

        try:
            response = self.client.put_resource_policy(**secret.secret_resource_policy_args)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to update secret resource policy")
        return response

    def restore_secret(self, name):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            response = self.client.restore_secret(SecretId=name)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to restore secret")
        return response

    def delete_secret(self, name, recovery_window):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            if recovery_window == 0:
                response = self.client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
            else:
                response = self.client.delete_secret(SecretId=name, RecoveryWindowInDays=recovery_window)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to delete secret")
        return response

    def delete_resource_policy(self, name):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            response = self.client.delete_resource_policy(SecretId=name)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to delete secret resource policy")
        return response

    def update_rotation(self, secret):
        if secret.rotation_enabled:
            try:
                response = self.client.rotate_secret(
                    SecretId=secret.name,
                    RotationLambdaARN=secret.rotation_lambda_arn,
                    RotationRules=secret.rotation_rules)
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg="Failed to rotate secret secret")
        else:
            try:
                response = self.client.cancel_rotate_secret(SecretId=secret.name)
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg="Failed to cancel rotation")
        return response

    def tag_secret(self, secret_name, tags):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            self.client.tag_resource(SecretId=secret_name, Tags=tags)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to add tag(s) to secret")

    def untag_secret(self, secret_name, tag_keys):
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        try:
            self.client.untag_resource(SecretId=secret_name, TagKeys=tag_keys)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to remove tag(s) from secret")

    def secrets_match(self, desired_secret, current_secret):
        """Compare secrets except tags and rotation

        Args:
            desired_secret: camel dict representation of the desired secret state.
            current_secret: secret reference as returned by the secretsmanager api.

        Returns: bool
        """
        if desired_secret.description != current_secret.get("Description", ""):
            return False
        if desired_secret.kms_key_id != current_secret.get("KmsKeyId"):
            return False
        current_secret_value = self.client.get_secret_value(SecretId=current_secret.get("Name"))
        if desired_secret.secret_type == 'SecretBinary':
            desired_value = to_bytes(desired_secret.secret)
        else:
            desired_value = desired_secret.secret
        if desired_value != current_secret_value.get(desired_secret.secret_type):
            return False
        return True


def rotation_match(desired_secret, current_secret):
    """Compare secrets rotation configuration

    Args:
        desired_secret: camel dict representation of the desired secret state.
        current_secret: secret reference as returned by the secretsmanager api.

    Returns: bool
    """
    if desired_secret.rotation_enabled != current_secret.get("RotationEnabled", False):
        return False
    if desired_secret.rotation_enabled:
        if desired_secret.rotation_lambda_arn != current_secret.get("RotationLambdaARN"):
            return False
        if desired_secret.rotation_rules != current_secret.get("RotationRules"):
            return False
    return True


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(required=True),
            'state': dict(choices=['present', 'absent'], default='present'),
            'description': dict(default=""),
            'kms_key_id': dict(),
            'secret_type': dict(choices=['binary', 'string'], default="string"),
            'secret': dict(default="", no_log=True),
            'json_secret': dict(type='json', no_log=True),
            'resource_policy': dict(type='json', default=None),
            'tags': dict(type='dict', default=None, aliases=['resource_tags']),
            'purge_tags': dict(type='bool', default=True),
            'rotation_lambda': dict(),
            'rotation_interval': dict(type='int', default=30),
            'recovery_window': dict(type='int', default=30),
        },
        mutually_exclusive=[['secret', 'json_secret']],
        supports_check_mode=True,
    )

    changed = False
    state = module.params.get('state')
    secrets_mgr = SecretsManagerInterface(module)
    recovery_window = module.params.get('recovery_window')
    secret = Secret(
        module.params.get('name'),
        module.params.get('secret_type'),
        module.params.get('secret') or module.params.get('json_secret'),
        description=module.params.get('description'),
        kms_key_id=module.params.get('kms_key_id'),
        resource_policy=module.params.get('resource_policy'),
        tags=module.params.get('tags'),
        lambda_arn=module.params.get('rotation_lambda'),
        rotation_interval=module.params.get('rotation_interval')
    )
    purge_tags = module.params.get('purge_tags')

    current_secret = secrets_mgr.get_secret(secret.name)

    if state == 'absent':
        if current_secret:
            if not current_secret.get("DeletedDate"):
                result = camel_dict_to_snake_dict(secrets_mgr.delete_secret(secret.name, recovery_window=recovery_window))
                changed = True
            elif current_secret.get("DeletedDate") and recovery_window == 0:
                result = camel_dict_to_snake_dict(secrets_mgr.delete_secret(secret.name, recovery_window=recovery_window))
                changed = True
            else:
                result = "secret already scheduled for deletion"
        else:
            result = "secret does not exist"
    if state == 'present':
        if current_secret is None:
            result = secrets_mgr.create_secret(secret)
            if secret.resource_policy and result.get("ARN"):
                result = secrets_mgr.put_resource_policy(secret)
            changed = True
        else:
            if current_secret.get("DeletedDate"):
                secrets_mgr.restore_secret(secret.name)
                changed = True
            if not secrets_mgr.secrets_match(secret, current_secret):
                result = secrets_mgr.update_secret(secret)
                changed = True
            if not rotation_match(secret, current_secret):
                result = secrets_mgr.update_rotation(secret)
                changed = True
            current_resource_policy_response = secrets_mgr.get_resource_policy(secret.name)
            current_resource_policy = current_resource_policy_response.get("ResourcePolicy")
            if compare_policies(secret.resource_policy, current_resource_policy):
                if secret.resource_policy is None and current_resource_policy:
                    result = secrets_mgr.delete_resource_policy(secret.name)
                else:
                    result = secrets_mgr.put_resource_policy(secret)
                changed = True
            if module.params.get('tags') is not None:
                current_tags = boto3_tag_list_to_ansible_dict(current_secret.get('Tags', []))
                tags_to_add, tags_to_remove = compare_aws_tags(current_tags, secret.tags, purge_tags)
                if tags_to_add:
                    secrets_mgr.tag_secret(secret.name, ansible_dict_to_boto3_tag_list(tags_to_add))
                    changed = True
                if tags_to_remove:
                    secrets_mgr.untag_secret(secret.name, tags_to_remove)
                    changed = True
        result = camel_dict_to_snake_dict(secrets_mgr.get_secret(secret.name))
        if result.get('tags', None) is not None:
            result['tags_dict'] = boto3_tag_list_to_ansible_dict(result.get('tags', []))
        result.pop("response_metadata")

    module.exit_json(changed=changed, secret=result)


if __name__ == '__main__':
    main()

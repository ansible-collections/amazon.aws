#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: iam_role_info
version_added: 1.0.0
short_description: Gather information on IAM roles
description:
    - Gathers information about IAM roles.
    - This module was called C(iam_role_facts) before Ansible 2.9. The usage did not change.
requirements: [ boto3 ]
author:
    - "Will Thames (@willthames)"
options:
    name:
        description:
            - Name of a role to search for.
            - Mutually exclusive with I(path_prefix).
        aliases:
            - role_name
        type: str
    path_prefix:
        description:
            - Prefix of role to restrict IAM role search for.
            - Mutually exclusive with I(name).
        type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: find all existing IAM roles
  community.aws.iam_role_info:
  register: result

- name: describe a single role
  community.aws.iam_role_info:
    name: MyIAMRole

- name: describe all roles matching a path prefix
  community.aws.iam_role_info:
    path_prefix: /application/path
'''

RETURN = '''
iam_roles:
  description: List of IAM roles
  returned: always
  type: complex
  contains:
    arn:
      description: Amazon Resource Name for IAM role.
      returned: always
      type: str
      sample: arn:aws:iam::123456789012:role/AnsibleTestRole
    assume_role_policy_document:
      description: Policy Document describing what can assume the role.
      returned: always
      type: str
    create_date:
      description: Date IAM role was created.
      returned: always
      type: str
      sample: '2017-10-23T00:05:08+00:00'
    inline_policies:
      description: List of names of inline policies.
      returned: always
      type: list
      sample: []
    managed_policies:
      description: List of attached managed policies.
      returned: always
      type: complex
      contains:
        policy_arn:
          description: Amazon Resource Name for the policy.
          returned: always
          type: str
          sample: arn:aws:iam::123456789012:policy/AnsibleTestEC2Policy
        policy_name:
          description: Name of managed policy.
          returned: always
          type: str
          sample: AnsibleTestEC2Policy
    instance_profiles:
      description: List of attached instance profiles.
      returned: always
      type: complex
      contains:
        arn:
          description: Amazon Resource Name for the instance profile.
          returned: always
          type: str
          sample: arn:aws:iam::123456789012:instance-profile/AnsibleTestEC2Policy
        create_date:
          description: Date instance profile was created.
          returned: always
          type: str
          sample: '2017-10-23T00:05:08+00:00'
        instance_profile_id:
          description: Amazon Identifier for the instance profile.
          returned: always
          type: str
          sample: AROAII7ABCD123456EFGH
        instance_profile_name:
          description: Name of instance profile.
          returned: always
          type: str
          sample: AnsibleTestEC2Policy
        path:
          description: Path of instance profile.
          returned: always
          type: str
          sample: /
        roles:
          description: List of roles associated with this instance profile.
          returned: always
          type: list
          sample: []
    path:
      description: Path of role.
      returned: always
      type: str
      sample: /
    role_id:
      description: Amazon Identifier for the role.
      returned: always
      type: str
      sample: AROAII7ABCD123456EFGH
    role_name:
      description: Name of the role.
      returned: always
      type: str
      sample: AnsibleTestRole
    tags:
      description: Role tags.
      type: dict
      returned: always
      sample: '{"Env": "Prod"}'
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


@AWSRetry.exponential_backoff()
def list_iam_roles_with_backoff(client, **kwargs):
    paginator = client.get_paginator('list_roles')
    return paginator.paginate(**kwargs).build_full_result()


@AWSRetry.exponential_backoff()
def list_iam_role_policies_with_backoff(client, role_name):
    paginator = client.get_paginator('list_role_policies')
    return paginator.paginate(RoleName=role_name).build_full_result()['PolicyNames']


@AWSRetry.exponential_backoff()
def list_iam_attached_role_policies_with_backoff(client, role_name):
    paginator = client.get_paginator('list_attached_role_policies')
    return paginator.paginate(RoleName=role_name).build_full_result()['AttachedPolicies']


@AWSRetry.exponential_backoff()
def list_iam_instance_profiles_for_role_with_backoff(client, role_name):
    paginator = client.get_paginator('list_instance_profiles_for_role')
    return paginator.paginate(RoleName=role_name).build_full_result()['InstanceProfiles']


def describe_iam_role(module, client, role):
    name = role['RoleName']
    try:
        role['InlinePolicies'] = list_iam_role_policies_with_backoff(client, name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get inline policies for role %s" % name)
    try:
        role['ManagedPolicies'] = list_iam_attached_role_policies_with_backoff(client, name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get managed  policies for role %s" % name)
    try:
        role['InstanceProfiles'] = list_iam_instance_profiles_for_role_with_backoff(client, name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get instance profiles for role %s" % name)
    try:
        role['tags'] = boto3_tag_list_to_ansible_dict(role['Tags'])
        del role['Tags']
    except KeyError:
        role['tags'] = {}
    return role


def describe_iam_roles(module, client):
    name = module.params['name']
    path_prefix = module.params['path_prefix']
    if name:
        try:
            roles = [client.get_role(RoleName=name)['Role']]
        except is_boto3_error_code('NoSuchEntity'):
            return []
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Couldn't get IAM role %s" % name)
    else:
        params = dict()
        if path_prefix:
            if not path_prefix.startswith('/'):
                path_prefix = '/' + path_prefix
            if not path_prefix.endswith('/'):
                path_prefix = path_prefix + '/'
            params['PathPrefix'] = path_prefix
        try:
            roles = list_iam_roles_with_backoff(client, **params)['Roles']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't list IAM roles")
    return [camel_dict_to_snake_dict(describe_iam_role(module, client, role), ignore_list=['tags']) for role in roles]


def main():
    """
     Module action handler
    """
    argument_spec = dict(
        name=dict(aliases=['role_name']),
        path_prefix=dict(),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              mutually_exclusive=[['name', 'path_prefix']])
    if module._name == 'iam_role_facts':
        module.deprecate("The 'iam_role_facts' module has been renamed to 'iam_role_info'", date='2021-12-01', collection_name='community.aws')

    client = module.client('iam')

    module.exit_json(changed=False, iam_roles=describe_iam_roles(module, client))


if __name__ == '__main__':
    main()

#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = '''
---
module: iam_instance_profile_info
version_added: 1.0.0
short_description: Gather information about IAM instances profiles
description:
  - Gather information about IAM instance profiles in AWS.
author:
  - "Aubin Bikouo (@abikouo)"
options:
  instance_profile_names:
    description:
      - A list of IAM instance profile names that exist in your account.
      - Mutually exclusive with parameter I(path_prefix).
    type: list
    elements: str
    aliases:
      - names
  path_prefix:
    description:
      - The path prefix for filtering IAM instance profiles.
      - For example, the prefix /application_abc/component_xyz/ gets all instance profiles whose path starts
        with /application_abc/component_xyz/.
      - Mutually exclusive with parameter I(instance_profile_names).
    type: str
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all IAM instance profiles
- amazon.aws.iam_instance_profile_info:

# Gather information about a particular IAM instance profiles
- amazon.aws.iam_instance_profile_info:
    instance_profile_names:
      - ecsInstanceProfile

'''

RETURN = '''
instance_profiles:
  description: List of matching IAM Instance profiles.
  returned: always
  type: complex
  contains:
    path:
      description:
        - The path to the instance profile.
      type: str
      returned: always
    instance_profile_name:
      description:
        - The name identifying the instance profile.
      type: str
      returned: always
    instance_profile_id:
      description:
        - The stable and unique string identifying the instance profile.
      type: str
      returned: always
    arn:
      description:
        - The Amazon Resource Name (ARN) specifying the instance profile. 
      type: str
      returned: always
    create_date:
      description:
        - The date when the instance profile was created.
      type: str
      returned: always
    roles:
      description:
        - The role associated with the instance profile.
      returned: always
      type: complex
      contains:
        path:
          description:
            - The path to the role.
          type: str
          returned: always
        role_name:
          description:
            - The friendly name that identifies the role.
          type: str
          returned: always
        role_id:
          description:
            - The stable and unique string identifying the role.
          type: str
          returned: always
        arn:
          description:
            - The Amazon Resource Name (ARN) specifying the role.
          type: str
          returned: always
        create_date:
          description:
            - The date and time, in ISO 8601 date-time format , when the role was created.
          type: str
          returned: always
        assume_role_policy_document:
          description:
            - The policy that grants an entity permission to assume the role.
          type: str
          returned: always
        description:
          description:
            - A description of the role that you provide.
          type: str
          returned: always
        max_session_duration:
          description:
            - The maximum session duration (in seconds) for the specified role.
          type: str
          returned: always
        permissions_boundary:
          description:
            - The ARN of the policy used to set the permissions boundary for the role.
          type: complex
          returned: always
          contains:
            permissions_boundary_type:
              description:
                - The permissions boundary usage type that indicates what type of IAM
                  resource is used as the permissions boundary for an entity.
              type: str
              returned: always
            permissions_boundary_arn:
              description:
                - The ARN of the policy used to set the permissions boundary for the user or role.
              type: str
              returned: always
        tags:
          description:
            - A dict of tags that are attached to the role.
          returned: always
          type: dict
        role_last_used:
          description:
            - Contains information about the last time that an IAM role was used.
            - This includes the date and time and the Region in which the role was last used.
          type: complex
          returned: always
          contains:
            last_used_date:
              description:
                - The date and time, in ISO 8601 date-time format that the role was last used.
              type: str
              returned: always
            region:
              description:
                - The name of the Amazon Web Services Region in which the role was last used.
              type: str
              returned: always
    tags:
      description: 
        - A dict of tags that are attached to the instance profile.
      returned: always
      type: dict
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def list_instance_profiles(module, client):

    try:
        params = {}
        if module.params.get("path_prefix"):
            params["PathPrefix"] = module.params.get("path_prefix")
        paginator = client.get_paginator('list_instance_profiles')
        return paginator.paginate(**params).build_full_result()['InstanceProfiles']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to list instance profiles with path prefix {0}".format(module.params.get("path_prefix")))


def get_instance_profile(module, client):

    result = []
    last_error = None
    last_name = None

    for name in module.params.get("instance_profile_names"):
        try:
            result.append(client.get_instance_profile(InstanceProfileName=name, aws_retry=True)['InstanceProfile'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            last_error = e
            last_name = name

    if len(result) == 0:
        module.fail_json_aws(last_error, msg="Unable to get instance profile with name {0}".format(last_name))

    return result

def main():

    argument_spec = dict(
        instance_profile_names=dict(type='list', elements='str', aliases=['names']),
        path_prefix=dict(type='str'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[
                                  ['instance_profile_names', 'path_prefix'],
                              ],
                              supports_check_mode=True)

    client = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())

    if module.params.get("instance_profile_names"):
        result = get_instance_profile(module, client)
    else:
        result = list_instance_profiles(module, client)

    # Modify boto3 tags list to be ansible friendly dict and then camel_case
    camel_instance_profiles = []
    for camel_profile in result:
        camel_profile['tags'] = boto3_tag_list_to_ansible_dict(camel_profile.get('Tags', []))
        camel_roles = []
        for role in camel_profile.get("Roles", []):
            role["tags"] = boto3_tag_list_to_ansible_dict(role.get('Tags', []))
            camel_roles.append(role)
        camel_profile["Roles"] = camel_roles
        camel_instance_profiles.append(camel_dict_to_snake_dict(camel_profile, ignore_list=["tags"]))

    module.exit_json(instance_profiles=camel_instance_profiles)


if __name__ == '__main__':
    main()

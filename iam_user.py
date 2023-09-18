#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: iam_user
version_added: 1.0.0
short_description: Manage AWS IAM users
description:
  - Manage AWS IAM users.
author: Josh Souza (@joshsouza)
options:
  name:
    description:
      - The name of the user to create.
    required: true
    type: str
  managed_policies:
    description:
      - A list of managed policy ARNs or friendly names to attach to the user.
      - To embed an inline policy, use M(community.aws.iam_policy).
    required: false
    type: list
    elements: str
    aliases: ['managed_policy']
  state:
    description:
      - Create or remove the IAM user.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  purge_policies:
    description:
      - When I(purge_policies=true) any managed policies not listed in I(managed_policies) will be detatched.
    required: false
    default: false
    type: bool
    aliases: ['purge_policy', 'purge_managed_policies']
  tags:
    description:
      - Tag dict to apply to the user.
    required: false
    type: dict
    version_added: 2.1.0
  purge_tags:
    description:
      - Remove tags not listed in I(tags) when tags is specified.
    default: true
    type: bool
    version_added: 2.1.0
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Note: This module does not allow management of groups that users belong to.
#       Groups should manage their membership directly using `iam_group`,
#       as users belong to them.

- name: Create a user
  community.aws.iam_user:
    name: testuser1
    state: present

- name: Create a user and attach a managed policy using its ARN
  community.aws.iam_user:
    name: testuser1
    managed_policies:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    state: present

- name: Remove all managed policies from an existing user with an empty list
  community.aws.iam_user:
    name: testuser1
    state: present
    purge_policies: true

- name: Create user with tags
  community.aws.iam_user:
    name: testuser1
    state: present
    tags:
      Env: Prod

- name: Delete the user
  community.aws.iam_user:
    name: testuser1
    state: absent

'''
RETURN = r'''
user:
    description: dictionary containing all the user information
    returned: success
    type: complex
    contains:
        arn:
            description: the Amazon Resource Name (ARN) specifying the user
            type: str
            sample: "arn:aws:iam::1234567890:user/testuser1"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the user was created
            type: str
            sample: "2017-02-08T04:36:28+00:00"
        user_id:
            description: the stable and unique string identifying the user
            type: str
            sample: AGPAIDBWE12NSFINE55TM
        user_name:
            description: the friendly name that identifies the user
            type: str
            sample: testuser1
        path:
            description: the path to the user
            type: str
            sample: /
        tags:
            description: user tags
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
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags


def compare_attached_policies(current_attached_policies, new_attached_policies):

    # If new_attached_policies is None it means we want to remove all policies
    if len(current_attached_policies) > 0 and new_attached_policies is None:
        return False

    current_attached_policies_arn_list = []
    for policy in current_attached_policies:
        current_attached_policies_arn_list.append(policy['PolicyArn'])

    if not set(current_attached_policies_arn_list).symmetric_difference(set(new_attached_policies)):
        return True
    else:
        return False


def convert_friendly_names_to_arns(connection, module, policy_names):

    # List comprehension that looks for any policy in the 'policy_names' list
    # that does not begin with 'arn'. If there aren't any, short circuit.
    # If there are, translate friendly name to the full arn
    if not any(not policy.startswith('arn:') for policy in policy_names if policy is not None):
        return policy_names
    allpolicies = {}
    paginator = connection.get_paginator('list_policies')
    policies = paginator.paginate().build_full_result()['Policies']

    for policy in policies:
        allpolicies[policy['PolicyName']] = policy['Arn']
        allpolicies[policy['Arn']] = policy['Arn']
    try:
        return [allpolicies[policy] for policy in policy_names]
    except KeyError as e:
        module.fail_json(msg="Couldn't find policy: " + str(e))


def create_or_update_user(connection, module):

    params = dict()
    params['UserName'] = module.params.get('name')
    managed_policies = module.params.get('managed_policies')
    purge_policies = module.params.get('purge_policies')
    if module.params.get('tags') is not None:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params.get('tags'))
    changed = False
    if managed_policies:
        managed_policies = convert_friendly_names_to_arns(connection, module, managed_policies)

    # Get user
    user = get_user(connection, module, params['UserName'])

    # If user is None, create it
    if user is None:
        # Check mode means we would create the user
        if module.check_mode:
            module.exit_json(changed=True)

        try:
            connection.create_user(**params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to create user")
    else:
        changed = update_user_tags(connection, module, params, user)

    # Manage managed policies
    current_attached_policies = get_attached_policy_list(connection, module, params['UserName'])
    if not compare_attached_policies(current_attached_policies, managed_policies):
        current_attached_policies_arn_list = []
        for policy in current_attached_policies:
            current_attached_policies_arn_list.append(policy['PolicyArn'])

        # If managed_policies has a single empty element we want to remove all attached policies
        if purge_policies:
            # Detach policies not present
            for policy_arn in list(set(current_attached_policies_arn_list) - set(managed_policies)):
                changed = True
                if not module.check_mode:
                    try:
                        connection.detach_user_policy(UserName=params['UserName'], PolicyArn=policy_arn)
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, msg="Unable to detach policy {0} from user {1}".format(
                                             policy_arn, params['UserName']))

        # If there are policies to adjust that aren't in the current list, then things have changed
        # Otherwise the only changes were in purging above
        if set(managed_policies).difference(set(current_attached_policies_arn_list)):
            changed = True
            # If there are policies in managed_policies attach each policy
            if managed_policies != [None] and not module.check_mode:
                for policy_arn in managed_policies:
                    try:
                        connection.attach_user_policy(UserName=params['UserName'], PolicyArn=policy_arn)
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, msg="Unable to attach policy {0} to user {1}".format(
                                             policy_arn, params['UserName']))

    if module.check_mode:
        module.exit_json(changed=changed)

    # Get the user again
    user = get_user(connection, module, params['UserName'])

    module.exit_json(changed=changed, iam_user=user)


def destroy_user(connection, module):

    user_name = module.params.get('name')

    user = get_user(connection, module, user_name)
    # User is not present
    if not user:
        module.exit_json(changed=False)

    # Check mode means we would remove this user
    if module.check_mode:
        module.exit_json(changed=True)

    # Remove any attached policies otherwise deletion fails
    try:
        for policy in get_attached_policy_list(connection, module, user_name):
            connection.detach_user_policy(UserName=user_name, PolicyArn=policy['PolicyArn'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to delete user {0}".format(user_name))

    try:
        # Remove user's access keys
        access_keys = connection.list_access_keys(UserName=user_name)["AccessKeyMetadata"]
        for access_key in access_keys:
            connection.delete_access_key(UserName=user_name, AccessKeyId=access_key["AccessKeyId"])

        # Remove user's login profile (console password)
        delete_user_login_profile(connection, module, user_name)

        # Remove user's ssh public keys
        ssh_public_keys = connection.list_ssh_public_keys(UserName=user_name)["SSHPublicKeys"]
        for ssh_public_key in ssh_public_keys:
            connection.delete_ssh_public_key(UserName=user_name, SSHPublicKeyId=ssh_public_key["SSHPublicKeyId"])

        # Remove user's service specific credentials
        service_credentials = connection.list_service_specific_credentials(UserName=user_name)["ServiceSpecificCredentials"]
        for service_specific_credential in service_credentials:
            connection.delete_service_specific_credential(
                UserName=user_name,
                ServiceSpecificCredentialId=service_specific_credential["ServiceSpecificCredentialId"]
            )

        # Remove user's signing certificates
        signing_certificates = connection.list_signing_certificates(UserName=user_name)["Certificates"]
        for signing_certificate in signing_certificates:
            connection.delete_signing_certificate(
                UserName=user_name,
                CertificateId=signing_certificate["CertificateId"]
            )

        # Remove user's MFA devices
        mfa_devices = connection.list_mfa_devices(UserName=user_name)["MFADevices"]
        for mfa_device in mfa_devices:
            connection.deactivate_mfa_device(UserName=user_name, SerialNumber=mfa_device["SerialNumber"])

        # Remove user's inline policies
        inline_policies = connection.list_user_policies(UserName=user_name)["PolicyNames"]
        for policy_name in inline_policies:
            connection.delete_user_policy(UserName=user_name, PolicyName=policy_name)

        # Remove user's group membership
        user_groups = connection.list_groups_for_user(UserName=user_name)["Groups"]
        for group in user_groups:
            connection.remove_user_from_group(UserName=user_name, GroupName=group["GroupName"])

        connection.delete_user(UserName=user_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to delete user {0}".format(user_name))

    module.exit_json(changed=True)


def get_user(connection, module, name):

    params = dict()
    params['UserName'] = name

    try:
        user = connection.get_user(**params)
    except is_boto3_error_code('NoSuchEntity'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Unable to get user {0}".format(name))

    tags = boto3_tag_list_to_ansible_dict(user['User'].pop('Tags', []))
    user = camel_dict_to_snake_dict(user)
    user['user']['tags'] = tags
    return user


def get_attached_policy_list(connection, module, name):

    try:
        return connection.list_attached_user_policies(UserName=name)['AttachedPolicies']
    except is_boto3_error_code('NoSuchEntity'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Unable to get policies for user {0}".format(name))


def delete_user_login_profile(connection, module, user_name):

    try:
        return connection.delete_login_profile(UserName=user_name)
    except is_boto3_error_code('NoSuchEntity'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Unable to delete login profile for user {0}".format(user_name))


def update_user_tags(connection, module, params, user):
    user_name = params['UserName']
    existing_tags = user['user']['tags']
    new_tags = params.get('Tags')
    if new_tags is None:
        return False
    new_tags = boto3_tag_list_to_ansible_dict(new_tags)

    purge_tags = module.params.get('purge_tags')

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)

    if not module.check_mode:
        try:
            if tags_to_remove:
                connection.untag_user(UserName=user_name, TagKeys=tags_to_remove)
            if tags_to_add:
                connection.tag_user(UserName=user_name, Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Unable to set tags for user %s' % user_name)

    changed = bool(tags_to_add) or bool(tags_to_remove)
    return changed


def main():

    argument_spec = dict(
        name=dict(required=True, type='str'),
        managed_policies=dict(default=[], type='list', aliases=['managed_policy'], elements='str'),
        state=dict(choices=['present', 'absent'], required=True),
        purge_policies=dict(default=False, type='bool', aliases=['purge_policy', 'purge_managed_policies']),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    connection = module.client('iam')

    state = module.params.get("state")

    if state == 'present':
        create_or_update_user(connection, module)
    else:
        destroy_user(connection, module)


if __name__ == '__main__':
    main()

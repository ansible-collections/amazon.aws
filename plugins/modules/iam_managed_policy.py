#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: iam_managed_policy
version_added: 1.0.0
short_description: Manage User Managed IAM policies
description:
    - Allows creating and removing managed IAM policies
options:
  policy_name:
    description:
      - The name of the managed policy.
    required: True
    type: str
  policy_description:
    description:
      - A helpful description of this policy, this value is immutable and only set when creating a new policy.
    default: ''
    type: str
  policy:
    description:
      - A properly json formatted policy
    type: json
  make_default:
    description:
      - Make this revision the default revision.
    default: True
    type: bool
  only_version:
    description:
      - Remove all other non default revisions, if this is used with C(make_default) it will result in all other versions of this policy being deleted.
    type: bool
    default: false
  state:
    description:
      - Should this managed policy be present or absent. Set to absent to detach all entities from this policy and remove it if found.
    default: present
    choices: [ "present", "absent" ]
    type: str
  fail_on_delete:
    description:
    - The I(fail_on_delete) option does nothing and will be removed after 2022-06-01
    type: bool

author: "Dan Kozlowski (@dkhenry)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

requirements:
    - boto3
    - botocore
'''

EXAMPLES = '''
# Create Policy ex nihilo
- name: Create IAM Managed Policy
  community.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy_description: "A Helpful managed policy"
    policy: "{{ lookup('template', 'managed_policy.json.j2') }}"
    state: present

# Update a policy with a new default version
- name: Create IAM Managed Policy
  community.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy: "{{ lookup('file', 'managed_policy_update.json') }}"
    state: present

# Update a policy with a new non default version
- name: Create IAM Managed Policy
  community.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy:
      Version: "2012-10-17"
      Statement:
      - Effect: "Allow"
        Action: "logs:CreateLogGroup"
        Resource: "*"
    make_default: false
    state: present

# Update a policy and make it the only version and the default version
- name: Create IAM Managed Policy
  community.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy: |
      {
        "Version": "2012-10-17",
        "Statement":[{
          "Effect": "Allow",
          "Action": "logs:PutRetentionPolicy",
          "Resource": "*"
        }]
      }
    only_version: true
    state: present

# Remove a policy
- name: Create IAM Managed Policy
  community.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    state: absent
'''

RETURN = '''
policy:
  description: Returns the policy json structure, when state == absent this will return the value of the removed policy.
  returned: success
  type: str
  sample: '{
        "arn": "arn:aws:iam::aws:policy/AdministratorAccess "
        "attachment_count": 0,
        "create_date": "2017-03-01T15:42:55.981000+00:00",
        "default_version_id": "v1",
        "is_attachable": true,
        "path": "/",
        "policy_id": "ANPALM4KLDMTFXGOOJIHL",
        "policy_name": "AdministratorAccess",
        "update_date": "2017-03-01T15:42:55.981000+00:00"
  }'
'''

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_policies


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_policies_with_backoff(iam):
    paginator = iam.get_paginator('list_policies')
    return paginator.paginate(Scope='Local').build_full_result()


def get_policy_by_name(module, iam, name):
    try:
        response = list_policies_with_backoff(iam)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list policies")
    for policy in response['Policies']:
        if policy['PolicyName'] == name:
            return policy
    return None


def delete_oldest_non_default_version(module, iam, policy):
    try:
        versions = [v for v in iam.list_policy_versions(PolicyArn=policy['Arn'])['Versions']
                    if not v['IsDefaultVersion']]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list policy versions")
    versions.sort(key=lambda v: v['CreateDate'], reverse=True)
    for v in versions[-1:]:
        try:
            iam.delete_policy_version(PolicyArn=policy['Arn'], VersionId=v['VersionId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete policy version")


# This needs to return policy_version, changed
def get_or_create_policy_version(module, iam, policy, policy_document):
    try:
        versions = iam.list_policy_versions(PolicyArn=policy['Arn'])['Versions']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list policy versions")
    for v in versions:
        try:
            document = iam.get_policy_version(PolicyArn=policy['Arn'],
                                              VersionId=v['VersionId'])['PolicyVersion']['Document']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get policy version {0}".format(v['VersionId']))
        # If the current policy matches the existing one
        if not compare_policies(document, json.loads(to_native(policy_document))):
            return v, False

    # No existing version so create one
    # There is a service limit (typically 5) of policy versions.
    #
    # Rather than assume that it is 5, we'll try to create the policy
    # and if that doesn't work, delete the oldest non default policy version
    # and try again.
    try:
        version = iam.create_policy_version(PolicyArn=policy['Arn'], PolicyDocument=policy_document)['PolicyVersion']
        return version, True
    except is_boto3_error_code('LimitExceeded'):
        delete_oldest_non_default_version(module, iam, policy)
        try:
            version = iam.create_policy_version(PolicyArn=policy['Arn'], PolicyDocument=policy_document)['PolicyVersion']
            return version, True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as second_e:
            module.fail_json_aws(second_e, msg="Couldn't create policy version")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't create policy version")


def set_if_default(module, iam, policy, policy_version, is_default):
    if is_default and not policy_version['IsDefaultVersion']:
        try:
            iam.set_default_policy_version(PolicyArn=policy['Arn'], VersionId=policy_version['VersionId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't set default policy version")
        return True
    return False


def set_if_only(module, iam, policy, policy_version, is_only):
    if is_only:
        try:
            versions = [v for v in iam.list_policy_versions(PolicyArn=policy['Arn'])[
                'Versions'] if not v['IsDefaultVersion']]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't list policy versions")
        for v in versions:
            try:
                iam.delete_policy_version(PolicyArn=policy['Arn'], VersionId=v['VersionId'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't delete policy version")
        return len(versions) > 0
    return False


def detach_all_entities(module, iam, policy, **kwargs):
    try:
        entities = iam.list_entities_for_policy(PolicyArn=policy['Arn'], **kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't detach list entities for policy {0}".format(policy['PolicyName']))

    for g in entities['PolicyGroups']:
        try:
            iam.detach_group_policy(PolicyArn=policy['Arn'], GroupName=g['GroupName'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't detach group policy {0}".format(g['GroupName']))
    for u in entities['PolicyUsers']:
        try:
            iam.detach_user_policy(PolicyArn=policy['Arn'], UserName=u['UserName'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't detach user policy {0}".format(u['UserName']))
    for r in entities['PolicyRoles']:
        try:
            iam.detach_role_policy(PolicyArn=policy['Arn'], RoleName=r['RoleName'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't detach role policy {0}".format(r['RoleName']))
    if entities['IsTruncated']:
        detach_all_entities(module, iam, policy, marker=entities['Marker'])


def main():
    argument_spec = dict(
        policy_name=dict(required=True),
        policy_description=dict(default=''),
        policy=dict(type='json'),
        make_default=dict(type='bool', default=True),
        only_version=dict(type='bool', default=False),
        fail_on_delete=dict(type='bool', removed_at_date='2022-06-01', removed_from_collection='community.aws'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[['state', 'present', ['policy']]],
    )

    name = module.params.get('policy_name')
    description = module.params.get('policy_description')
    state = module.params.get('state')
    default = module.params.get('make_default')
    only = module.params.get('only_version')

    policy = None

    if module.params.get('policy') is not None:
        policy = json.dumps(json.loads(module.params.get('policy')))

    try:
        iam = module.client('iam')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    p = get_policy_by_name(module, iam, name)
    if state == 'present':
        if p is None:
            # No Policy so just create one
            try:
                rvalue = iam.create_policy(PolicyName=name, Path='/',
                                           PolicyDocument=policy, Description=description)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't create policy {0}".format(name))

            module.exit_json(changed=True, policy=camel_dict_to_snake_dict(rvalue['Policy']))
        else:
            policy_version, changed = get_or_create_policy_version(module, iam, p, policy)
            changed = set_if_default(module, iam, p, policy_version, default) or changed
            changed = set_if_only(module, iam, p, policy_version, only) or changed
            # If anything has changed we needto refresh the policy
            if changed:
                try:
                    p = iam.get_policy(PolicyArn=p['Arn'])['Policy']
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json(msg="Couldn't get policy")

            module.exit_json(changed=changed, policy=camel_dict_to_snake_dict(p))
    else:
        # Check for existing policy
        if p:
            # Detach policy
            detach_all_entities(module, iam, p)
            # Delete Versions
            try:
                versions = iam.list_policy_versions(PolicyArn=p['Arn'])['Versions']
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't list policy versions")
            for v in versions:
                if not v['IsDefaultVersion']:
                    try:
                        iam.delete_policy_version(PolicyArn=p['Arn'], VersionId=v['VersionId'])
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(
                            e, msg="Couldn't delete policy version {0}".format(v['VersionId']))
            # Delete policy
            try:
                iam.delete_policy(PolicyArn=p['Arn'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't delete policy {0}".format(p['PolicyName']))

            # This is the one case where we will return the old policy
            module.exit_json(changed=True, policy=camel_dict_to_snake_dict(p))
        else:
            module.exit_json(changed=False, policy=None)
# end main


if __name__ == '__main__':
    main()

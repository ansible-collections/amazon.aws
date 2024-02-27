#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_managed_policy
version_added: 1.0.0
version_added_collection: community.aws
short_description: Manage User Managed IAM policies
description:
  - Allows creating and removing managed IAM policies
options:
  name:
    description:
      - The name of the managed policy.
      - >-
        Note: Policy names are unique within an account.  Paths (I(path)) do B(not) affect
        the uniqueness requirements of I(name).  For example it is not permitted to have both
        C(/Path1/MyPolicy) and C(/Path2/MyPolicy) in the same account.
      - The parameter was renamed from C(policy_name) to C(name) in release 7.2.0.
    required: true
    type: str
    aliases: ["policy_name"]
  path:
    description:
      - The path for the managed policy.
      - For more information about IAM paths, see the AWS IAM identifiers documentation
        U(https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    aliases: ['prefix', 'path_prefix']
    required: false
    type: str
    version_added: 7.2.0
  description:
    description:
      - A helpful description of this policy, this value is immutable and only set when creating a new policy.
      - The parameter was renamed from C(policy_description) to C(description) in release 7.2.0.
    aliases: ["policy_description"]
    type: str
  policy:
    description:
      - A properly json formatted policy
    type: json
  make_default:
    description:
      - Make this revision the default revision.
    default: true
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
notes:
  - Support for I(tags) and I(purge_tags) was added in release 7.2.0.

author:
  - "Dan Kozlowski (@dkhenry)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Create a policy
- name: Create IAM Managed Policy
  amazon.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy_description: "A Helpful managed policy"
    policy: "{{ lookup('template', 'managed_policy.json.j2') }}"
    state: present

# Update a policy with a new default version
- name: Update an IAM Managed Policy with new default version
  amazon.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy: "{{ lookup('file', 'managed_policy_update.json') }}"
    state: present

# Update a policy with a new non default version
- name: Update an IAM Managed Policy with a non default version
  amazon.aws.iam_managed_policy:
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
- name: Update an IAM Managed Policy with default version as the only version
  amazon.aws.iam_managed_policy:
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
- name: Remove an existing IAM Managed Policy
  amazon.aws.iam_managed_policy:
    policy_name: "ManagedPolicy"
    state: absent
"""

RETURN = r"""
policy:
  description: Returns the basic policy information, when state == absent this will return the value of the removed policy.
  returned: success
  type: complex
  contains:
    arn:
      description: The Amazon Resource Name (ARN) of the policy.
      type: str
      sample: "arn:aws:iam::123456789012:policy/ansible-test-12345/ansible-test-12345-policy"
    attachment_count:
      description: The number of entities (users, groups, and roles) that the policy is attached to.
      type: int
      sample: "5"
    create_date:
      description: The date and time, in ISO 8601 date-time format, when the policy was created.
      type: str
      sample: "2017-02-08T04:36:28+00:00"
    default_version_id:
      description: The default policy version to use.
      type: str
      sample: "/ansible-test-12345/"
    description:
      description: A friendly description of the policy.
      type: str
      sample: "My Example Policy"
    is_attachable:
      description: Specifies whether the policy can be attached to an IAM entities.
      type: bool
      sample: False
    path:
      description: The path to the policy.
      type: str
      sample: "/ansible-test-12345/"
    permissions_boundary_usage_count:
      description: The number of IAM entities (users, groups, and roles) using the policy as a permissions boundary.
      type: int
      sample: "5"
    policy_id:
      description: The stable and globally unique string identifying the policy.
      type: str
      sample: "ANPA12345EXAMPLE12345"
    policy_name:
      description: The friendly name identifying the policy.
      type: str
      sample: "ansible-test-12345-policy"
    tags:
      description: A dictionary representing the tags attached to the managed policy.
      type: dict
      returned: always
      sample: {"Env": "Prod"}
    update_date:
      description: The date and time, in ISO 8601 date-time format, when the policy was last updated.
      type: str
      sample: "2017-02-08T05:12:13+00:00"
"""

import json

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import IAMErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.iam import detach_iam_group_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import detach_iam_role_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import detach_iam_user_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_managed_policy_by_arn
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_managed_policy_by_name
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_iam_managed_policy_version
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_entities_for_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_managed_policy_versions
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import tag_iam_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import untag_iam_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


@IAMErrorHandler.deletion_error_handler("delete policy version")
def delete_policy_version(arn, version):
    client.delete_policy_version(aws_retry=True, PolicyArn=arn, VersionId=version)


def _create_policy_version(arn, policy_document):
    return client.create_policy_version(aws_retry=True, PolicyArn=arn, PolicyDocument=policy_document)["PolicyVersion"]


@IAMErrorHandler.common_error_handler("create policy version")
def create_policy_version(arn, policy_document):
    if module.check_mode:
        return {}
    try:
        version = _create_policy_version(arn, policy_document)
    # There is a service limit (typically 5) of policy versions.
    #
    # Rather than assume that it is 5, we'll try to create the policy
    # and if that doesn't work, delete the oldest non default policy version
    # and try again.
    except is_boto3_error_code("LimitExceeded"):
        delete_oldest_non_default_version(arn)
        version = _create_policy_version(arn, policy_document)

    return version


def delete_oldest_non_default_version(arn):
    if module.check_mode:
        return True

    versions = [v for v in list_iam_managed_policy_versions(client, arn) if not v["IsDefaultVersion"]]
    if not versions:
        return False

    versions.sort(key=lambda v: v["CreateDate"], reverse=True)
    for v in versions[-1:]:
        delete_policy_version(arn, v["VersionId"])
    return True


# This needs to return policy_version, changed
def get_or_create_policy_version(policy, policy_document):
    versions = list_iam_managed_policy_versions(client, policy["Arn"])

    for v in versions:
        document = get_iam_managed_policy_version(client, policy["Arn"], v["VersionId"])["Document"]

        # If the current policy matches the existing one
        if not compare_policies(document, json.loads(to_native(policy_document))):
            return v, False

    # No existing version so create one
    return create_policy_version(policy["Arn"], policy_document), True


@IAMErrorHandler.common_error_handler("set default policy version")
def set_if_default(policy, policy_version, is_default):
    if not is_default:
        return False
    if policy_version.get("IsDefaultVersion"):
        return False
    if module.check_mode:
        return True

    client.set_default_policy_version(aws_retry=True, PolicyArn=policy["Arn"], VersionId=policy_version["VersionId"])
    return True


def set_if_only(policy, policy_version, is_only):
    if not is_only:
        return False
    versions = [v for v in list_iam_managed_policy_versions(client, policy["Arn"]) if not v["IsDefaultVersion"]]
    if not versions:
        return False
    if module.check_mode:
        return True

    for v in versions:
        delete_policy_version(policy["Arn"], v["VersionId"])

    return True


def detach_all_entities(policy):
    arn = policy["Arn"]
    entities = list_iam_entities_for_policy(client, arn)

    if not entities:
        return False

    for g in entities["PolicyGroups"]:
        detach_iam_group_policy(client, arn, g["GroupName"])
    for u in entities["PolicyUsers"]:
        detach_iam_user_policy(client, arn, u["UserName"])
    for r in entities["PolicyRoles"]:
        detach_iam_role_policy(client, arn, r["RoleName"])

    return True


@IAMErrorHandler.common_error_handler("create policy")
def create_managed_policy(name, path, policy, description, tags):
    if module.check_mode:
        module.exit_json(changed=True)
    if policy is None:
        raise AnsibleIAMError(message="Managed policy would be created but policy parameter is missing")

    params = {"PolicyName": name, "PolicyDocument": policy}

    if path:
        params["Path"] = path
    if description:
        params["Description"] = description
    if tags:
        params["Tags"] = ansible_dict_to_boto3_tag_list(tags)

    rvalue = client.create_policy(aws_retry=True, **params)
    # rvalue is incomplete
    new_policy = get_iam_managed_policy_by_arn(client, rvalue["Policy"]["Arn"])

    module.exit_json(changed=True, policy=normalize_iam_policy(new_policy))


def ensure_path(existing_policy, path):
    if path is None:
        return False

    existing_path = existing_policy["Path"]
    if existing_path == path:
        return False

    # As of botocore 1.34.3, the APIs don't support updating the Name or Path
    module.warn(f"Unable to update path from '{existing_path}' to '{path}'")
    return False


def ensure_description(existing_policy, description):
    if description is None:
        return False

    existing_description = existing_policy.get("Description", "")
    if existing_description == description:
        return False

    # As of botocore 1.34.3, the APIs don't support updating the Description
    module.warn(f"Unable to update description from '{existing_description}' to '{description}'")
    return False


def ensure_policy_document(existing_policy, policy, default, only):
    if policy is None:
        return False
    policy_version, changed = get_or_create_policy_version(existing_policy, policy)
    changed |= set_if_default(existing_policy, policy_version, default)
    changed |= set_if_only(existing_policy, policy_version, only)
    return changed


def ensure_tags(existing_policy, tags, purge_tags):
    if tags is None:
        return False

    original_tags = boto3_tag_list_to_ansible_dict(existing_policy.get("Tags") or [])

    tags_to_set, tag_keys_to_unset = compare_aws_tags(original_tags, tags, purge_tags)
    if not tags_to_set and not tag_keys_to_unset:
        return False

    if module.check_mode:
        return True

    if tag_keys_to_unset:
        untag_iam_policy(client, existing_policy["Arn"], tag_keys_to_unset)
    if tags_to_set:
        tag_iam_policy(client, existing_policy["Arn"], tags_to_set)

    return True


def update_managed_policy(existing_policy, path, policy, description, default, only, tags, purge_tags):
    changed = ensure_path(existing_policy, path)
    changed |= ensure_description(existing_policy, description)
    changed |= ensure_policy_document(existing_policy, policy, default, only)
    changed |= ensure_tags(existing_policy, tags, purge_tags)

    if not changed:
        module.exit_json(changed=changed, policy=normalize_iam_policy(existing_policy))

    # If anything has changed we need to refresh the policy
    updated_policy = get_iam_managed_policy_by_arn(client, existing_policy["Arn"])
    module.exit_json(changed=changed, policy=normalize_iam_policy(updated_policy))


def create_or_update_policy(existing_policy):
    name = module.params.get("name")
    path = module.params.get("path")
    description = module.params.get("description")
    default = module.params.get("make_default")
    only = module.params.get("only_version")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")

    policy = None

    if module.params.get("policy") is not None:
        policy = json.dumps(json.loads(module.params.get("policy")))

    if existing_policy is None:
        create_managed_policy(name, path, policy, description, tags)
    else:
        update_managed_policy(existing_policy, path, policy, description, default, only, tags, purge_tags)


@IAMErrorHandler.deletion_error_handler("delete policy")
def delete_policy(existing_policy):
    if not existing_policy:
        return False

    arn = existing_policy["Arn"]
    if module.check_mode:
        return True

    # Detach policy
    detach_all_entities(existing_policy)
    # Delete Versions
    versions = [v for v in list_iam_managed_policy_versions(client, arn) if not v["IsDefaultVersion"]]
    for v in versions:
        delete_policy_version(arn, v["VersionId"])

    # Delete policy
    client.delete_policy(aws_retry=True, PolicyArn=arn)
    return True


def main():
    global module
    global client

    argument_spec = dict(
        name=dict(required=True, aliases=["policy_name"]),
        path=dict(aliases=["prefix", "path_prefix"]),
        description=dict(aliases=["policy_description"]),
        policy=dict(type="json"),
        make_default=dict(type="bool", default=True),
        only_version=dict(type="bool", default=False),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params.get("name")
    state = module.params.get("state")

    identifier_problem = validate_iam_identifiers("policy", name=name)
    if identifier_problem:
        module.fail_json(msg=identifier_problem)

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    existing_policy = get_iam_managed_policy_by_name(client, name)

    try:
        if state == "present":
            create_or_update_policy(existing_policy)
        else:
            changed = delete_policy(existing_policy)
            module.exit_json(changed=changed, policy=normalize_iam_policy(existing_policy))
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()

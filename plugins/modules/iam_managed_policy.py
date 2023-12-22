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
  description:
    description:
      - A helpful description of this policy, this value is immutable and only set when creating a new policy.
      - The parameter was renamed from C(policy_description) to C(description) in release 7.2.0.
    default: ''
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

author:
  - "Dan Kozlowski (@dkhenry)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
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

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
def list_policies_with_backoff():
    paginator = client.get_paginator("list_policies")
    return paginator.paginate(Scope="Local").build_full_result()


def find_policy_by_name(name):
    try:
        response = list_policies_with_backoff()
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list policies")
    for policy in response["Policies"]:
        if policy["PolicyName"] == name:
            return policy
    return None


def get_policy_by_arn(arn):
    try:
        policy = client.get_policy(aws_retry=True, PolicyArn=arn)["Policy"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json(msg="Couldn't get policy")
    return policy


def get_policy_by_name(name):
    # get_policy() requires an ARN, and list_policies() doesn't return all fields, so we need to do both :(
    policy = find_policy_by_name(name)
    if policy is None:
        return None
    return get_policy_by_arn(policy["Arn"])


def delete_oldest_non_default_version(policy):
    try:
        versions = [
            v
            for v in client.list_policy_versions(aws_retry=True, PolicyArn=policy["Arn"])["Versions"]
            if not v["IsDefaultVersion"]
        ]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list policy versions")
    versions.sort(key=lambda v: v["CreateDate"], reverse=True)
    for v in versions[-1:]:
        try:
            client.delete_policy_version(aws_retry=True, PolicyArn=policy["Arn"], VersionId=v["VersionId"])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete policy version")


# This needs to return policy_version, changed
def get_or_create_policy_version(policy, policy_document):
    try:
        versions = client.list_policy_versions(aws_retry=True, PolicyArn=policy["Arn"])["Versions"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list policy versions")

    for v in versions:
        try:
            document = client.get_policy_version(aws_retry=True, PolicyArn=policy["Arn"], VersionId=v["VersionId"])[
                "PolicyVersion"
            ]["Document"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't get policy version {v['VersionId']}")

        if module.check_mode and compare_policies(document, json.loads(to_native(policy_document))):
            return v, True

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
        version = client.create_policy_version(aws_retry=True, PolicyArn=policy["Arn"], PolicyDocument=policy_document)[
            "PolicyVersion"
        ]
        return version, True
    except is_boto3_error_code("LimitExceeded"):
        delete_oldest_non_default_version(policy)
        try:
            version = client.create_policy_version(
                aws_retry=True, PolicyArn=policy["Arn"], PolicyDocument=policy_document
            )["PolicyVersion"]
            return version, True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as second_e:
            module.fail_json_aws(second_e, msg="Couldn't create policy version")
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't create policy version")


def set_if_default(policy, policy_version, is_default):
    if is_default and not policy_version["IsDefaultVersion"]:
        try:
            client.set_default_policy_version(
                aws_retry=True, PolicyArn=policy["Arn"], VersionId=policy_version["VersionId"]
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't set default policy version")
        return True
    return False


def set_if_only(policy, policy_version, is_only):
    if is_only:
        try:
            versions = [
                v
                for v in client.list_policy_versions(aws_retry=True, PolicyArn=policy["Arn"])["Versions"]
                if not v["IsDefaultVersion"]
            ]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't list policy versions")
        for v in versions:
            try:
                client.delete_policy_version(aws_retry=True, PolicyArn=policy["Arn"], VersionId=v["VersionId"])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't delete policy version")
        return len(versions) > 0
    return False


def detach_all_entities(policy, **kwargs):
    try:
        entities = client.list_entities_for_policy(aws_retry=True, PolicyArn=policy["Arn"], **kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Couldn't detach list entities for policy {policy['PolicyName']}")

    for g in entities["PolicyGroups"]:
        try:
            client.detach_group_policy(aws_retry=True, PolicyArn=policy["Arn"], GroupName=g["GroupName"])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't detach group policy {g['GroupName']}")
    for u in entities["PolicyUsers"]:
        try:
            client.detach_user_policy(aws_retry=True, PolicyArn=policy["Arn"], UserName=u["UserName"])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't detach user policy {u['UserName']}")
    for r in entities["PolicyRoles"]:
        try:
            client.detach_role_policy(aws_retry=True, PolicyArn=policy["Arn"], RoleName=r["RoleName"])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't detach role policy {r['RoleName']}")
    if entities["IsTruncated"]:
        detach_all_entities(policy, marker=entities["Marker"])


def create_or_update_policy(existing_policy):
    name = module.params.get("name")
    description = module.params.get("description")
    default = module.params.get("make_default")
    only = module.params.get("only_version")

    policy = None

    if module.params.get("policy") is not None:
        policy = json.dumps(json.loads(module.params.get("policy")))

    if existing_policy is None:
        if module.check_mode:
            module.exit_json(changed=True)

        # Create policy when none already exists
        try:
            rvalue = client.create_policy(PolicyName=name, Path="/", PolicyDocument=policy, Description=description)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't create policy {name}")

        module.exit_json(changed=True, policy=camel_dict_to_snake_dict(rvalue["Policy"]))
    else:
        policy_version, changed = get_or_create_policy_version(existing_policy, policy)
        changed = set_if_default(existing_policy, policy_version, default) or changed
        changed = set_if_only(existing_policy, policy_version, only) or changed

        # If anything has changed we need to refresh the policy
        if changed:
            try:
                updated_policy = client.get_policy(PolicyArn=existing_policy["Arn"])["Policy"]
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json(msg="Couldn't get policy")

            module.exit_json(changed=changed, policy=camel_dict_to_snake_dict(updated_policy))
        else:
            module.exit_json(changed=changed, policy=camel_dict_to_snake_dict(existing_policy))


def delete_policy(existing_policy):
    # Check for existing policy
    if existing_policy:
        if module.check_mode:
            module.exit_json(changed=True)

        # Detach policy
        detach_all_entities(existing_policy)
        # Delete Versions
        try:
            versions = client.list_policy_versions(aws_retry=True, PolicyArn=existing_policy["Arn"])["Versions"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't list policy versions")
        for v in versions:
            if not v["IsDefaultVersion"]:
                try:
                    client.delete_policy_version(
                        aws_retry=True, PolicyArn=existing_policy["Arn"], VersionId=v["VersionId"]
                    )
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg=f"Couldn't delete policy version {v['VersionId']}")
        # Delete policy
        try:
            client.delete_policy(aws_retry=True, PolicyArn=existing_policy["Arn"])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg=f"Couldn't delete policy {existing_policy['PolicyName']}")

        # This is the one case where we will return the old policy
        module.exit_json(changed=True, policy=camel_dict_to_snake_dict(existing_policy))
    else:
        module.exit_json(changed=False, policy=None)


def main():
    global module
    global client

    argument_spec = dict(
        name=dict(required=True, aliases=["policy_name"]),
        description=dict(default="", aliases=["policy_description"]),
        policy=dict(type="json"),
        make_default=dict(type="bool", default=True),
        only_version=dict(type="bool", default=False),
        state=dict(default="present", choices=["present", "absent"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["policy"]]],
        supports_check_mode=True,
    )

    name = module.params.get("name")
    state = module.params.get("state")

    identifier_problem = validate_iam_identifiers("policy", name=name)
    if identifier_problem:
        module.fail_json(msg=identifier_problem)

    try:
        client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    existing_policy = get_policy_by_name(name)

    if state == "present":
        create_or_update_policy(existing_policy)
    else:
        delete_policy(existing_policy)


if __name__ == "__main__":
    main()

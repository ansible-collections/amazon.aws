#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: eks_fargate_profile
version_added: 4.0.0
short_description: Manage EKS Fargate Profile
description:
  - Manage EKS Fargate Profile.
author:
  - Tiago Jarra (@tjarra)
options:
  name:
    description: Name of EKS Fargate Profile.
    required: True
    type: str
  cluster_name:
    description: Name of EKS Cluster.
    required: True
    type: str
  role_arn:
    description:
      - ARN of IAM role used by the EKS cluster.
      - Required when I(state=present).
    type: str
  subnets:
    description:
      - list of subnet IDs for the Kubernetes cluster.
      - Required when I(state=present).
    type: list
    elements: str
  selectors:
    description:
      - A list of selectors to use in fargate profile.
      - Required when I(state=present).
    type: list
    elements: dict
    suboptions:
      namespace:
        description: A namespace used in fargate profile.
        type: str
      labels:
        description: A dictionary of labels used in fargate profile.
        type: dict
        default: {}
  state:
    description: Create or delete the Fargate Profile.
    choices:
      - absent
      - present
    default: present
    type: str
  wait:
    description: >-
      Specifies whether the module waits until the profile is created or deleted before moving on.
    type: bool
    default: false
  wait_timeout:
    description: >-
      The duration in seconds to wait for the cluster to become active. Defaults
      to 1200 seconds (20 minutes).
    default: 1200
    type: int
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create an EKS Fargate Profile
  community.aws.eks_fargate_profile:
    name: test_fargate
    cluster_name: test_cluster
    role_arn: my_eks_role
    subnets:
      - subnet-aaaa1111
    selectors:
      - namespace: nm-test
        labels:
          - label1: test
    state: present
    wait: true

- name: Remove an EKS Fargate Profile
  community.aws.eks_fargate_profile:
    name: test_fargate
    cluster_name: test_cluster
    wait: true
    state: absent
"""

RETURN = r"""
fargate_profile_name:
  description: Name of Fargate Profile.
  returned: when state is present
  type: str
  sample: test_profile
fargate_profile_arn:
  description: ARN of the Fargate Profile.
  returned: when state is present
  type: str
  sample: arn:aws:eks:us-east-1:1231231123:safd
cluster_name:
  description: Name of EKS Cluster.
  returned: when state is present
  type: str
  sample: test-cluster
created_at:
  description: Fargate Profile creation date and time.
  returned: when state is present
  type: str
  sample: '2022-01-18T20:00:00.111000+00:00'
pod_execution_role_arn:
  description: ARN of the IAM Role used by Fargate Profile.
  returned: when state is present
  type: str
  sample: arn:aws:eks:us-east-1:1231231123:role/asdf
subnets:
  description: List of subnets used in Fargate Profile.
  returned: when state is present
  type: list
  sample:
  - subnet-qwerty123
  - subnet-asdfg456
selectors:
  description: Selector configuration.
  returned: when state is present
  type: complex
  contains:
    namespace:
      description: Name of the kubernetes namespace used in profile.
      returned: when state is present
      type: str
      sample: nm-test
    labels:
      description: List of kubernetes labels used in profile.
      returned: when state is present
      type: list
      sample:
        - label1: test1
        - label2: test2
tags:
  description: A dictionary of resource tags.
  returned: when state is present
  type: dict
  sample:
      foo: bar
      env: test
status:
  description: status of the EKS Fargate Profile.
  returned: when state is present
  type: str
  sample:
  - CREATING
  - ACTIVE
"""

try:
    import botocore
except ImportError:
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def validate_tags(client, module, fargate_profile):
    changed = False

    desired_tags = module.params.get("tags")
    if desired_tags is None:
        return False

    try:
        existing_tags = client.list_tags_for_resource(resourceArn=fargate_profile["fargateProfileArn"])["tags"]
        tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, desired_tags, module.params.get("purge_tags"))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Unable to list or compare tags for Fargate Profile {module.params.get('name')}")

    if tags_to_remove:
        changed = True
        if not module.check_mode:
            try:
                client.untag_resource(resourceArn=fargate_profile["fargateProfileArn"], tagKeys=tags_to_remove)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Fargate Profile {module.params.get('name')}")

    if tags_to_add:
        changed = True
        if not module.check_mode:
            try:
                client.tag_resource(resourceArn=fargate_profile["fargateProfileArn"], tags=tags_to_add)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Fargate Profile {module.params.get('name')}")

    return changed


def create_or_update_fargate_profile(client, module):
    name = module.params.get("name")
    subnets = module.params["subnets"]
    role_arn = module.params["role_arn"]
    cluster_name = module.params["cluster_name"]
    selectors = module.params["selectors"]
    tags = module.params["tags"] or {}
    wait = module.params.get("wait")
    fargate_profile = get_fargate_profile(client, module, name, cluster_name)

    if fargate_profile:
        changed = False
        if set(fargate_profile["podExecutionRoleArn"]) != set(role_arn):
            module.fail_json(msg="Cannot modify Execution Role")
        if set(fargate_profile["subnets"]) != set(subnets):
            module.fail_json(msg="Cannot modify Subnets")
        if fargate_profile["selectors"] != selectors:
            module.fail_json(msg="Cannot modify Selectors")

        changed = validate_tags(client, module, fargate_profile)

        if wait:
            wait_until(client, module, "fargate_profile_active", name, cluster_name)
        fargate_profile = get_fargate_profile(client, module, name, cluster_name)

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(fargate_profile))

    if module.check_mode:
        module.exit_json(changed=True)

    check_profiles_status(client, module, cluster_name)

    try:
        params = dict(
            fargateProfileName=name,
            podExecutionRoleArn=role_arn,
            subnets=subnets,
            clusterName=cluster_name,
            selectors=selectors,
            tags=tags,
        )
        fargate_profile = client.create_fargate_profile(**params)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Couldn't create fargate profile {name}")

    if wait:
        wait_until(client, module, "fargate_profile_active", name, cluster_name)
    fargate_profile = get_fargate_profile(client, module, name, cluster_name)

    module.exit_json(changed=True, **camel_dict_to_snake_dict(fargate_profile))


def delete_fargate_profile(client, module):
    name = module.params.get("name")
    cluster_name = module.params["cluster_name"]
    existing = get_fargate_profile(client, module, name, cluster_name)
    wait = module.params.get("wait")
    if not existing or existing["status"] == "DELETING":
        module.exit_json(changed=False)

    if not module.check_mode:
        check_profiles_status(client, module, cluster_name)
        try:
            client.delete_fargate_profile(clusterName=cluster_name, fargateProfileName=name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg=f"Couldn't delete fargate profile {name}")

        if wait:
            wait_until(client, module, "fargate_profile_deleted", name, cluster_name)

    module.exit_json(changed=True)


def get_fargate_profile(client, module, name, cluster_name):
    try:
        return client.describe_fargate_profile(clusterName=cluster_name, fargateProfileName=name)["fargateProfile"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't get fargate profile")


# Check if any fargate profiles is in changing states, if so, wait for the end
def check_profiles_status(client, module, cluster_name):
    try:
        list_profiles = client.list_fargate_profiles(clusterName=cluster_name)

        for name in list_profiles["fargateProfileNames"]:
            fargate_profile = get_fargate_profile(client, module, name, cluster_name)
            if fargate_profile["status"] == "CREATING":
                wait_until(
                    client, module, "fargate_profile_active", fargate_profile["fargateProfileName"], cluster_name
                )
            elif fargate_profile["status"] == "DELETING":
                wait_until(
                    client, module, "fargate_profile_deleted", fargate_profile["fargateProfileName"], cluster_name
                )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't not find EKS cluster")


def wait_until(client, module, waiter_name, name, cluster_name):
    wait_timeout = module.params.get("wait_timeout")
    waiter = get_waiter(client, waiter_name)
    attempts = 1 + int(wait_timeout / waiter.config.delay)
    try:
        waiter.wait(clusterName=cluster_name, fargateProfileName=name, WaiterConfig={"MaxAttempts": attempts})
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="An error occurred waiting")


def main():
    argument_spec = dict(
        name=dict(required=True),
        cluster_name=dict(required=True),
        role_arn=dict(),
        subnets=dict(type="list", elements="str"),
        selectors=dict(
            type="list",
            elements="dict",
            options=dict(
                namespace=dict(type="str"),
                labels=dict(type="dict", default={}),
            ),
        ),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        state=dict(choices=["absent", "present"], default="present"),
        wait=dict(default=False, type="bool"),
        wait_timeout=dict(default=1200, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["role_arn", "subnets", "selectors"]]],
        supports_check_mode=True,
    )

    try:
        client = module.client("eks")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't connect to AWS")

    if module.params.get("state") == "present":
        create_or_update_fargate_profile(client, module)
    else:
        delete_fargate_profile(client, module)


if __name__ == "__main__":
    main()

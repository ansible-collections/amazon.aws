#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: eks_cluster
version_added: 1.0.0
short_description: Manage Elastic Kubernetes Service (EKS) Clusters
description:
  - Manage Elastic Kubernetes Service (EKS) Clusters.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_eks_cluster).
    The usage did not change.
author:
  - Will Thames (@willthames)
options:
  name:
    description: Name of the EKS cluster.
    required: True
    type: str
  version:
    description:
      - Kubernetes version.
      - Defaults to C(latest).
    type: str
  role_arn:
    description: ARN of IAM role used by the EKS cluster.
    type: str
  subnets:
    description: List of subnet IDs for the Kubernetes cluster.
    type: list
    elements: str
  security_groups:
    description: List of security group names or IDs.
    type: list
    elements: str
  state:
    description: Desired state of the EKS cluster.
    choices:
      - absent
      - present
    default: present
    type: str
  tags:
    description:
      - A dictionary of tags to add the EKS cluster.
    type: dict
    version_added: 5.3.0
  wait:
    description: >-
      Specifies whether the module waits until the cluster is active or deleted
      before moving on. It takes "usually less than 10 minutes" per AWS documentation.
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
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create an EKS cluster
  community.aws.eks_cluster:
    name: my_cluster
    version: 1.14
    role_arn: my_eks_role
    subnets:
      - subnet-aaaa1111
    security_groups:
      - my_eks_sg
      - sg-abcd1234
  register: caller_facts

- name: Remove an EKS cluster
  community.aws.eks_cluster:
    name: my_cluster
    wait: true
    state: absent
"""

RETURN = r"""
arn:
  description: ARN of the EKS cluster
  returned: when state is present
  type: str
  sample: arn:aws:eks:us-west-2:123456789012:cluster/my-eks-cluster
certificate_authority:
  description: Dictionary containing Certificate Authority Data for cluster
  returned: after creation
  type: complex
  contains:
    data:
      description: Base-64 encoded Certificate Authority Data for cluster
      returned: when the cluster has been created and is active
      type: str
endpoint:
  description: Kubernetes API server endpoint
  returned: when the cluster has been created and is active
  type: str
  sample: https://API_SERVER_ENDPOINT.yl4.us-west-2.eks.amazonaws.com
created_at:
  description: Cluster creation date and time
  returned: when state is present
  type: str
  sample: '2018-06-06T11:56:56.242000+00:00'
name:
  description: EKS cluster name
  returned: when state is present
  type: str
  sample: my-eks-cluster
resources_vpc_config:
  description: VPC configuration of the cluster
  returned: when state is present
  type: complex
  contains:
    security_group_ids:
      description: List of security group IDs
      returned: always
      type: list
      sample:
      - sg-abcd1234
      - sg-aaaa1111
    subnet_ids:
      description: List of subnet IDs
      returned: always
      type: list
      sample:
      - subnet-abcdef12
      - subnet-345678ab
      - subnet-cdef1234
    vpc_id:
      description: VPC id
      returned: always
      type: str
      sample: vpc-a1b2c3d4
role_arn:
  description: ARN of the IAM role used by the cluster
  returned: when state is present
  type: str
  sample: arn:aws:iam::123456789012:role/eks_cluster_role
status:
  description: status of the EKS cluster
  returned: when state is present
  type: str
  sample:
  - CREATING
  - ACTIVE
version:
  description: Kubernetes version of the cluster
  returned: when state is present
  type: str
  sample: '1.10'
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_ec2_security_group_ids_from_names
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def ensure_present(client, module):
    name = module.params.get("name")
    subnets = module.params["subnets"]
    groups = module.params["security_groups"]
    wait = module.params.get("wait")
    cluster = get_cluster(client, module)
    try:
        ec2 = module.client("ec2")
        vpc_id = ec2.describe_subnets(SubnetIds=[subnets[0]])["Subnets"][0]["VpcId"]
        groups = get_ec2_security_group_ids_from_names(groups, ec2, vpc_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't lookup security groups")

    if cluster:
        if set(cluster["resourcesVpcConfig"]["subnetIds"]) != set(subnets):
            module.fail_json(msg="Cannot modify subnets of existing cluster")
        if set(cluster["resourcesVpcConfig"]["securityGroupIds"]) != set(groups):
            module.fail_json(msg="Cannot modify security groups of existing cluster")
        if module.params.get("version") and module.params.get("version") != cluster["version"]:
            module.fail_json(msg="Cannot modify version of existing cluster")

        if wait:
            wait_until(client, module, "cluster_active")
            # Ensure that fields that are only available for active clusters are
            # included in the returned value
            cluster = get_cluster(client, module)

        module.exit_json(changed=False, **camel_dict_to_snake_dict(cluster))

    if module.check_mode:
        module.exit_json(changed=True)
    try:
        params = dict(
            name=name,
            roleArn=module.params["role_arn"],
            resourcesVpcConfig=dict(subnetIds=subnets, securityGroupIds=groups),
        )
        if module.params["version"]:
            params["version"] = module.params["version"]
        if module.params["tags"]:
            params["tags"] = module.params["tags"]
        cluster = client.create_cluster(**params)["cluster"]
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json(msg=f"Region {client.meta.region_name} is not supported by EKS")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Couldn't create cluster {name}")

    if wait:
        wait_until(client, module, "cluster_active")
        # Ensure that fields that are only available for active clusters are
        # included in the returned value
        cluster = get_cluster(client, module)

    module.exit_json(changed=True, **camel_dict_to_snake_dict(cluster))


def ensure_absent(client, module):
    name = module.params.get("name")
    existing = get_cluster(client, module)
    wait = module.params.get("wait")
    if not existing:
        module.exit_json(changed=False)
    if not module.check_mode:
        try:
            client.delete_cluster(name=module.params["name"])
        except botocore.exceptions.EndpointConnectionError as e:
            module.fail_json(msg=f"Region {client.meta.region_name} is not supported by EKS")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg=f"Couldn't delete cluster {name}")

    if wait:
        wait_until(client, module, "cluster_deleted")

    module.exit_json(changed=True)


def get_cluster(client, module):
    name = module.params.get("name")
    try:
        return client.describe_cluster(name=name)["cluster"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    except botocore.exceptions.EndpointConnectionError as e:  # pylint: disable=duplicate-except
        module.fail_json(msg=f"Region {client.meta.region_name} is not supported by EKS")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Couldn't get cluster {name}")


def wait_until(client, module, waiter_name="cluster_active"):
    name = module.params.get("name")
    wait_timeout = module.params.get("wait_timeout")

    waiter = get_waiter(client, waiter_name)
    attempts = 1 + int(wait_timeout / waiter.config.delay)
    waiter.wait(name=name, WaiterConfig={"MaxAttempts": attempts})


def main():
    argument_spec = dict(
        name=dict(required=True),
        version=dict(),
        role_arn=dict(),
        subnets=dict(type="list", elements="str"),
        security_groups=dict(type="list", elements="str"),
        state=dict(choices=["absent", "present"], default="present"),
        tags=dict(type="dict", required=False),
        wait=dict(default=False, type="bool"),
        wait_timeout=dict(default=1200, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["role_arn", "subnets", "security_groups"]]],
        supports_check_mode=True,
    )

    client = module.client("eks")

    if module.params.get("state") == "present":
        ensure_present(client, module)
    else:
        ensure_absent(client, module)


if __name__ == "__main__":
    main()

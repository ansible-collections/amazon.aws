#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: eks_nodegroup
version_added: 5.3.0
short_description: Manage EKS Nodegroup module
description:
  - Manage EKS Nodegroup.
author:
  - Tiago Jarra (@tjarra)
options:
  name:
    description: Name of EKS Nodegroup.
    required: True
    type: str
  cluster_name:
    description: Name of EKS Cluster.
    required: True
    type: str
  node_role:
    description: ARN of IAM role used by the EKS cluster Nodegroup.
    type: str
  subnets:
    description: list of subnet IDs for the Kubernetes cluster.
    type: list
    elements: str
  scaling_config:
    description: The scaling configuration details for the Auto Scaling group that is created for your node group.
    type: dict
    default:
      min_size: 1
      max_size: 2
      desired_size: 1
    suboptions:
      min_size:
        description: The minimum number of nodes that the managed node group can scale in to.
        type: int
      max_size:
        description: The maximum number of nodes that the managed node group can scale out to.
        type: int
      desired_size:
        description: The current number of nodes that the managed node group should maintain.
        type: int
  disk_size:
    description:
      - Size of disk in nodegroup nodes.
        If you specify I(launch_template), then don't specify I(disk_size), or the node group deployment will fail.
    type: int
  instance_types:
    description:
      - Specify the instance types for a node group.
        If you specify I(launch_template), then don't specify I(instance_types), or the node group deployment will fail.
    type: list
    elements: str
  ami_type:
    description: The AMI type for your node group.
    type: str
    choices:
      - AL2_x86_64
      - AL2_x86_64_GPU
      - AL2_ARM_64
      - CUSTOM
      - BOTTLEROCKET_ARM_64
      - BOTTLEROCKET_x86_64
  remote_access:
    description:
      - The remote access (SSH) configuration to use with your node group.
        If you specify I(launch_template), then don't specify I(remote_access), or the node group deployment will fail.
    type: dict
    suboptions:
      ec2_ssh_key:
        description: The Amazon EC2 SSH key that provides access for SSH communication with the nodes in the managed node group.
        type: str
      source_sg:
        description: The security groups that are allowed SSH access (port 22) to the nodes.
        type: list
        elements: str
  update_config:
    description: The node group update configuration.
    type: dict
    default:
      max_unavailable: 1
    suboptions:
      max_unavailable:
        description: The maximum number of nodes unavailable at once during a version update.
        type: int
      max_unavailable_percentage:
        description: The maximum percentage of nodes unavailable during a version update.
        type: int
  labels:
    description: The Kubernetes labels to be applied to the nodes in the node group when they are created.
    type: dict
    default: {}
  taints:
    description: The Kubernetes taints to be applied to the nodes in the node group.
    type: list
    elements: dict
    default: []
    suboptions:
      key:
        description: The key of the taint.
        type: str
      value:
        description: The value of the taint.
        type: str
      effect:
        description: The effect of the taint.
        type: str
        choices:
          - NO_SCHEDULE
          - NO_EXECUTE
          - PREFER_NO_SCHEDULE
  launch_template:
    description:
      - An object representing a node group's launch template specification.
      - If specified, then do not specify I(instanceTypes), I(diskSize), or I(remoteAccess).
    type: dict
    suboptions:
      name:
        description: The name of the launch template.
        type: str
      version:
        description:
          - The version of the launch template to use.
          - If no version is specified, then the template's default version is used.
        type: str
      id:
        description: The ID of the launch template.
        type: str
  capacity_type:
    description: The capacity type for your node group.
    default: ON_DEMAND
    type: str
    choices:
      - ON_DEMAND
      - SPOT
  release_version:
    description: The AMI version of the Amazon EKS optimized AMI to use with your node group.
    type: str
  state:
    description: Create or delete the Nodegroup.
    choices:
      - absent
      - present
    default: present
    type: str
  tags:
    description: A dictionary of resource tags.
    type: dict
    aliases: ['resource_tags']
  purge_tags:
    description:
      - Purge existing tags that are not found in the nodegroup.
    type: bool
    default: true
  wait:
    description: Specifies whether the module waits until the profile is created or deleted before moving on.
    type: bool
    default: false
  wait_timeout:
    description: The duration in seconds to wait for the nodegroup to become active. Defaults to C(1200) seconds.
    default: 1200
    type: int
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create nodegroup
  community.aws.eks_nodegroup:
    name: test_nodegroup
    state: present
    cluster_name: test_cluster
    node_role: arn:aws:eks:us-east-1:1231231123:role/asdf
    subnets:
      - subnet-qwerty123
      - subnet-asdfg456
    scaling_config:
      - min_size: 1
      - max_size: 2
      - desired_size: 1
    disk_size: 20
    instance_types: 't3.micro'
    ami_type: 'AL2_x86_64'
    labels:
      - 'teste': 'test'
    taints:
      - key: 'test'
        value: 'test'
        effect: 'NO_SCHEDULE'
    capacity_type: 'on_demand'

- name: Remove an EKS Nodegrop
  community.aws.eks_nodegroup:
    name: test_nodegroup
    cluster_name: test_cluster
    wait: yes
    state: absent
"""

RETURN = r"""
nodegroup_name:
  description: The name associated with an Amazon EKS managed node group.
  returned: when state is present
  type: str
  sample: test_cluster
nodegroup_arn:
  description: The Amazon Resource Name (ARN) associated with the managed node group.
  returned: when state is present
  type: str
  sample: arn:aws:eks:us-east-1:1231231123:safd
cluster_name:
  description: Name of EKS Cluster
  returned: when state is present
  type: str
  sample: test_cluster
version:
  description: The Kubernetes version of the managed node group.
  returned: when state is present
  type: str
  sample: need_validate
release_version:
  description: This is the version of the Amazon EKS optimized AMI that the node group was deployed with.
  returned: when state is present
  type: str
  sample: need_validate
created_at:
  description: Nodegroup creation date and time.
  returned: when state is present
  type: str
  sample: '2022-01-18T20:00:00.111000+00:00'
modified_at:
  description: Nodegroup modified date and time.
  returned: when state is present
  type: str
  sample: '2022-01-18T20:00:00.111000+00:00'
status:
  description: status of the EKS Nodegroup.
  returned: when state is present
  type: str
  sample:
  - CREATING
  - ACTIVE
capacity_type:
  description: The capacity type of your managed node group.
  returned: when state is present
  type: str
  sample: need_validate
scaling_config:
  description: The scaling configuration details for the Auto Scaling group that is associated with your node group.
  returned: when state is present
  type: dict
  sample: need_validate
instance_types:
  description: This is the instance type that is associated with the node group.
  returned: when state is present
  type: list
  sample: need_validate
subnets:
  description: List of subnets used in Fargate Profile.
  returned: when state is present
  type: list
  sample:
  - subnet-qwerty123
  - subnet-asdfg456
remote_access:
  description: This is the remote access configuration that is associated with the node group.
  returned: when state is present
  type: dict
  sample: need_validate
ami_type:
  description: This is the AMI type that was specified in the node group configuration.
  returned: when state is present
  type: str
  sample: need_validate
node_role:
  description: ARN of the IAM Role used by Nodegroup.
  returned: when state is present
  type: str
  sample: arn:aws:eks:us-east-1:1231231123:role/asdf
labels:
  description: The Kubernetes labels applied to the nodes in the node group.
  returned: when state is present
  type: dict
  sample: need_validate
taints:
  description: The Kubernetes taints to be applied to the nodes in the node group when they are created.
  returned: when state is present
  type: list
  sample: need_validate
resources:
  description: The resources associated with the node group.
  returned: when state is present
  type: complex
  contains:
    autoScalingGroups:
      description: The Auto Scaling groups associated with the node group.
      returned: when state is present
      type: list
      elements: dict
    remoteAccessSecurityGroup:
      description: The remote access security group associated with the node group.
      returned: when state is present
      type: str
diskSize:
  description: This is the disk size in the node group configuration.
  returned:  when state is present
  type: int
  sample: 20
health:
  description: The health status of the node group.
  returned: when state is present
  type: dict
  sample: need_validate
update_config:
  description: The node group update configuration.
  returned: when state is present
  type: dict
  contains:
    maxUnavailable:
      description: The maximum number of nodes unavailable at once during a version update.
      type: int
    maxUnavailablePercentage:
      description: The maximum percentage of nodes unavailable during a version update.
      type: int
launch_template:
  description: If a launch template was used to create the node group, then this is the launch template that was used.
  returned: when state is present
  type: dict
  sample: need_validate
tags:
  description: Nodegroup tags.
  returned: when state is present
  type: dict
  sample:
    foo: bar
"""

try:
    import botocore
except ImportError:
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def validate_tags(client, module, nodegroup):
    changed = False

    desired_tags = module.params.get("tags")
    if desired_tags is None:
        return False

    try:
        existing_tags = client.list_tags_for_resource(resourceArn=nodegroup["nodegroupArn"])["tags"]
        tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, desired_tags, module.params.get("purge_tags"))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Unable to list or compare tags for Nodegroup {module.params.get('name')}.")
    if tags_to_remove:
        if not module.check_mode:
            changed = True
            try:
                client.untag_resource(aws_retry=True, ResourceArn=nodegroup["nodegroupArn"], tagKeys=tags_to_remove)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Nodegroup {module.params.get('name')}.")
    if tags_to_add:
        if not module.check_mode:
            changed = True
            try:
                client.tag_resource(aws_retry=True, ResourceArn=nodegroup["nodegroupArn"], tags=tags_to_add)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Nodegroup {module.params.get('name')}.")

    return changed


def compare_taints(nodegroup_taints, param_taints):
    taints_to_unset = []
    taints_to_add_or_update = []
    for taint in nodegroup_taints:
        if taint not in param_taints:
            taints_to_unset.append(taint)
    for taint in param_taints:
        if taint not in nodegroup_taints:
            taints_to_add_or_update.append(taint)

    return taints_to_add_or_update, taints_to_unset


def validate_taints(client, module, nodegroup, param_taints):
    changed = False
    params = dict()
    params["clusterName"] = nodegroup["clusterName"]
    params["nodegroupName"] = nodegroup["nodegroupName"]
    params["taints"] = []
    if "taints" not in nodegroup:
        nodegroup["taints"] = []
    taints_to_add_or_update, taints_to_unset = compare_taints(nodegroup["taints"], param_taints)

    if taints_to_add_or_update:
        params["taints"]["addOrUpdateTaints"] = taints_to_add_or_update
    if taints_to_unset:
        params["taints"]["removeTaints"] = taints_to_unset
    if params["taints"]:
        if not module.check_mode:
            changed = True
            try:
                client.update_nodegroup_config(**params)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set taints for Nodegroup {params['nodegroupName']}.")

    return changed


def compare_labels(nodegroup_labels, param_labels):
    labels_to_unset = []
    labels_to_add_or_update = {}
    for label in nodegroup_labels.keys():
        if label not in param_labels:
            labels_to_unset.append(label)
    for key, value in param_labels.items():
        if key not in nodegroup_labels.keys():
            labels_to_add_or_update[key] = value

    return labels_to_add_or_update, labels_to_unset


def validate_labels(client, module, nodegroup, param_labels):
    changed = False
    params = dict()
    params["clusterName"] = nodegroup["clusterName"]
    params["nodegroupName"] = nodegroup["nodegroupName"]
    params["labels"] = {}
    labels_to_add_or_update, labels_to_unset = compare_labels(nodegroup["labels"], param_labels)

    if labels_to_add_or_update:
        params["labels"]["addOrUpdateLabels"] = labels_to_add_or_update
    if labels_to_unset:
        params["labels"]["removeLabels"] = labels_to_unset
    if params["labels"]:
        if not module.check_mode:
            changed = True
            try:
                client.update_nodegroup_config(**params)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set labels for Nodegroup {params['nodegroupName']}.")

    return changed


def compare_params(module, params, nodegroup):
    for param in ["nodeRole", "subnets", "diskSize", "instanceTypes", "amiTypes", "remoteAccess", "capacityType"]:
        if (param in nodegroup) and (param in params):
            if nodegroup[param] != params[param]:
                module.fail_json(msg=f"Cannot modify parameter {param}.")
    if ("launchTemplate" not in nodegroup) and ("launchTemplate" in params):
        module.fail_json(msg="Cannot add Launch Template in this Nodegroup.")
    if nodegroup["updateConfig"] != params["updateConfig"]:
        return True
    if nodegroup["scalingConfig"] != params["scalingConfig"]:
        return True
    return False


def compare_params_launch_template(module, params, nodegroup):
    if "launchTemplate" not in params:
        module.fail_json(msg="Cannot exclude Launch Template in this Nodegroup.")
    else:
        for key in ["name", "id"]:
            if (key in params["launchTemplate"]) and (
                params["launchTemplate"][key] != nodegroup["launchTemplate"][key]
            ):
                module.fail_json(msg=f"Cannot modify Launch Template {key}.")
        if ("version" in params["launchTemplate"]) and (
            params["launchTemplate"]["version"] != nodegroup["launchTemplate"]["version"]
        ):
            return True
    return False


def create_or_update_nodegroups(client, module):
    changed = False
    params = dict()
    params["nodegroupName"] = module.params["name"]
    params["clusterName"] = module.params["cluster_name"]
    params["nodeRole"] = module.params["node_role"]
    params["subnets"] = module.params["subnets"]
    params["tags"] = module.params["tags"] or {}
    if module.params["ami_type"] is not None:
        params["amiType"] = module.params["ami_type"]
    if module.params["disk_size"] is not None:
        params["diskSize"] = module.params["disk_size"]
    if module.params["instance_types"] is not None:
        params["instanceTypes"] = module.params["instance_types"]
    if module.params["launch_template"] is not None:
        params["launchTemplate"] = dict()
        if module.params["launch_template"]["id"] is not None:
            params["launchTemplate"]["id"] = module.params["launch_template"]["id"]
        if module.params["launch_template"]["version"] is not None:
            params["launchTemplate"]["version"] = module.params["launch_template"]["version"]
        if module.params["launch_template"]["name"] is not None:
            params["launchTemplate"]["name"] = module.params["launch_template"]["name"]
    if module.params["release_version"] is not None:
        params["releaseVersion"] = module.params["release_version"]
    if module.params["remote_access"] is not None:
        params["remoteAccess"] = dict()
        if module.params["remote_access"]["ec2_ssh_key"] is not None:
            params["remoteAccess"]["ec2SshKey"] = module.params["remote_access"]["ec2_ssh_key"]
        if module.params["remote_access"]["source_sg"] is not None:
            params["remoteAccess"]["sourceSecurityGroups"] = module.params["remote_access"]["source_sg"]
    if module.params["capacity_type"] is not None:
        params["capacityType"] = module.params["capacity_type"].upper()
    if module.params["labels"] is not None:
        params["labels"] = module.params["labels"]
    if module.params["taints"] is not None:
        params["taints"] = module.params["taints"]
    if module.params["update_config"] is not None:
        params["updateConfig"] = dict()
        if module.params["update_config"]["max_unavailable"] is not None:
            params["updateConfig"]["maxUnavailable"] = module.params["update_config"]["max_unavailable"]
        if module.params["update_config"]["max_unavailable_percentage"] is not None:
            params["updateConfig"]["maxUnavailablePercentage"] = module.params["update_config"][
                "max_unavailable_percentage"
            ]
    if module.params["scaling_config"] is not None:
        params["scalingConfig"] = snake_dict_to_camel_dict(module.params["scaling_config"])

    wait = module.params.get("wait")
    nodegroup = get_nodegroup(client, module, params["nodegroupName"], params["clusterName"])

    if nodegroup:
        update_params = dict()
        update_params["clusterName"] = params["clusterName"]
        update_params["nodegroupName"] = params["nodegroupName"]

        if "launchTemplate" in nodegroup:
            if compare_params_launch_template(module, params, nodegroup):
                update_params["launchTemplate"] = params["launchTemplate"]
                if not module.check_mode:
                    try:
                        client.update_nodegroup_version(**update_params)
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, msg="Couldn't update nodegroup.")
                changed |= True

        if compare_params(module, params, nodegroup):
            try:
                if "launchTemplate" in update_params:
                    update_params.pop("launchTemplate")
                update_params["scalingConfig"] = params["scalingConfig"]
                update_params["updateConfig"] = params["updateConfig"]

                if not module.check_mode:
                    client.update_nodegroup_config(**update_params)

                changed |= True

            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Couldn't update nodegroup.")

        changed |= validate_tags(client, module, nodegroup)

        changed |= validate_labels(client, module, nodegroup, params["labels"])

        if "taints" in nodegroup:
            changed |= validate_taints(client, module, nodegroup, params["taints"])

        if wait:
            wait_until(client, module, "nodegroup_active", params["nodegroupName"], params["clusterName"])

        nodegroup = get_nodegroup(client, module, params["nodegroupName"], params["clusterName"])

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(nodegroup))

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        nodegroup = client.create_nodegroup(**params)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Couldn't create Nodegroup {params['nodegroupName']}.")

    if wait:
        wait_until(client, module, "nodegroup_active", params["nodegroupName"], params["clusterName"])
        nodegroup = get_nodegroup(client, module, params["nodegroupName"], params["clusterName"])

    module.exit_json(changed=True, **camel_dict_to_snake_dict(nodegroup))


def delete_nodegroups(client, module):
    name = module.params.get("name")
    clusterName = module.params["cluster_name"]
    existing = get_nodegroup(client, module, name, clusterName)
    wait = module.params.get("wait")
    if not existing or existing["status"] == "DELETING":
        module.exit_json(changed=False, msg="Nodegroup not exists or in DELETING status.")
    if not module.check_mode:
        try:
            client.delete_nodegroup(clusterName=clusterName, nodegroupName=name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg=f"Couldn't delete Nodegroup {name}.")

        if wait:
            wait_until(client, module, "nodegroup_deleted", name, clusterName)

    module.exit_json(changed=True)


def get_nodegroup(client, module, nodegroup_name, cluster_name):
    try:
        return client.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)["nodegroup"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Couldn't get Nodegroup {nodegroup_name}.")


def wait_until(client, module, waiter_name, nodegroup_name, cluster_name):
    wait_timeout = module.params.get("wait_timeout")
    waiter = get_waiter(client, waiter_name)
    attempts = 1 + int(wait_timeout / waiter.config.delay)
    try:
        waiter.wait(clusterName=cluster_name, nodegroupName=nodegroup_name, WaiterConfig={"MaxAttempts": attempts})
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="An error occurred waiting")


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        cluster_name=dict(type="str", required=True),
        node_role=dict(),
        subnets=dict(type="list", elements="str"),
        scaling_config=dict(
            type="dict",
            default={"min_size": 1, "max_size": 2, "desired_size": 1},
            options=dict(
                min_size=dict(type="int"),
                max_size=dict(type="int"),
                desired_size=dict(type="int"),
            ),
        ),
        disk_size=dict(type="int"),
        instance_types=dict(type="list", elements="str"),
        ami_type=dict(
            choices=[
                "AL2_x86_64",
                "AL2_x86_64_GPU",
                "AL2_ARM_64",
                "CUSTOM",
                "BOTTLEROCKET_ARM_64",
                "BOTTLEROCKET_x86_64",
            ]
        ),
        remote_access=dict(
            type="dict",
            options=dict(
                ec2_ssh_key=dict(no_log=True),
                source_sg=dict(type="list", elements="str"),
            ),
        ),
        update_config=dict(
            type="dict",
            default={"max_unavailable": 1},
            options=dict(
                max_unavailable=dict(type="int"),
                max_unavailable_percentage=dict(type="int"),
            ),
        ),
        labels=dict(type="dict", default={}),
        taints=dict(
            type="list",
            elements="dict",
            default=[],
            options=dict(
                key=dict(
                    type="str",
                    no_log=False,
                ),
                value=dict(type="str"),
                effect=dict(type="str", choices=["NO_SCHEDULE", "NO_EXECUTE", "PREFER_NO_SCHEDULE"]),
            ),
        ),
        launch_template=dict(
            type="dict",
            options=dict(
                name=dict(type="str"),
                version=dict(type="str"),
                id=dict(type="str"),
            ),
        ),
        capacity_type=dict(choices=["ON_DEMAND", "SPOT"], default="ON_DEMAND"),
        release_version=dict(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        state=dict(choices=["absent", "present"], default="present"),
        wait=dict(default=False, type="bool"),
        wait_timeout=dict(default=1200, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["node_role", "subnets"]]],
        mutually_exclusive=[
            ("launch_template", "instance_types"),
            ("launch_template", "disk_size"),
            ("launch_template", "remote_access"),
            ("launch_template", "ami_type"),
        ],
        supports_check_mode=True,
    )

    if module.params["launch_template"] is None:
        if module.params["disk_size"] is None:
            module.params["disk_size"] = 20
        if module.params["ami_type"] is None:
            module.params["ami_type"] = "AL2_x86_64"
        if module.params["instance_types"] is None:
            module.params["instance_types"] = ["t3.medium"]
    else:
        if (module.params["launch_template"]["id"] is None) and (module.params["launch_template"]["name"] is None):
            module.exit_json(changed=False, msg="To use launch_template, it is necessary to inform the id or name.")
    try:
        client = module.client("eks")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't connect to AWS.")

    if module.params.get("state") == "present":
        create_or_update_nodegroups(client, module)
    else:
        delete_nodegroups(client, module)


if __name__ == "__main__":
    main()

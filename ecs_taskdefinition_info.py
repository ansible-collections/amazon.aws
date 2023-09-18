#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ecs_taskdefinition_info
version_added: 1.0.0
short_description: Describe a task definition in ECS
notes:
    - For details of the parameters and returns see
      U(http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.describe_task_definition)
description:
    - Describes a task definition in ECS.
author:
    - Gustavo Maia (@gurumaia)
    - Mark Chance (@Java1Guy)
    - Darek Kaczynski (@kaczynskid)
options:
    task_definition:
        description:
            - The name of the task definition to get details for
        required: true
        type: str
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- community.aws.ecs_taskdefinition_info:
    task_definition: test-td
"""

RETURN = r"""
container_definitions:
    description: Returns a list of complex objects representing the containers
    returned: success
    type: complex
    contains:
        name:
            description: The name of a container.
            returned: always
            type: str
        image:
            description: The image used to start a container.
            returned: always
            type: str
        cpu:
            description: The number of cpu units reserved for the container.
            returned: always
            type: int
        memoryReservation:
            description: The soft limit (in MiB) of memory to reserve for the container.
            returned: when present
            type: int
        links:
            description: Links to other containers.
            returned: when present
            type: str
        portMappings:
            description: The list of port mappings for the container.
            returned: always
            type: complex
            contains:
                containerPort:
                    description: The port number on the container.
                    returned: when present
                    type: int
                hostPort:
                    description: The port number on the container instance to reserve for your container.
                    returned: when present
                    type: int
                protocol:
                    description: The protocol used for the port mapping.
                    returned: when present
                    type: str
        essential:
            description: Whether this is an essential container or not.
            returned: always
            type: bool
        entryPoint:
            description: The entry point that is passed to the container.
            returned: when present
            type: str
        command:
            description: The command that is passed to the container.
            returned: when present
            type: str
        environment:
            description: The environment variables to pass to a container.
            returned: always
            type: complex
            contains:
                name:
                    description: The name of the environment variable.
                    returned: when present
                    type: str
                value:
                    description: The value of the environment variable.
                    returned: when present
                    type: str
        mountPoints:
            description: The mount points for data volumes in your container.
            returned: always
            type: complex
            contains:
                sourceVolume:
                    description: The name of the volume to mount.
                    returned: when present
                    type: str
                containerPath:
                    description: The path on the container to mount the host volume at.
                    returned: when present
                    type: str
                readOnly:
                    description: If this value is true , the container has read-only access to the volume.
                      If this value is false , then the container can write to the volume.
                    returned: when present
                    type: bool
        volumesFrom:
            description: Data volumes to mount from another container.
            returned: always
            type: complex
            contains:
                sourceContainer:
                    description: The name of another container within the same task definition to mount volumes from.
                    returned: when present
                    type: str
                readOnly:
                    description: If this value is true , the container has read-only access to the volume.
                      If this value is false , then the container can write to the volume.
                    returned: when present
                    type: bool
        hostname:
            description: The hostname to use for your container.
            returned: when present
            type: str
        user:
            description: The user name to use inside the container.
            returned: when present
            type: str
        workingDirectory:
            description: The working directory in which to run commands inside the container.
            returned: when present
            type: str
        disableNetworking:
            description: When this parameter is true, networking is disabled within the container.
            returned: when present
            type: bool
        privileged:
            description: When this parameter is true, the container is given elevated
              privileges on the host container instance (similar to the root user).
            returned: when present
            type: bool
        readonlyRootFilesystem:
            description: When this parameter is true, the container is given read-only access to its root file system.
            returned: when present
            type: bool
        dnsServers:
            description: A list of DNS servers that are presented to the container.
            returned: when present
            type: str
        dnsSearchDomains:
            description: A list of DNS search domains that are presented to the container.
            returned: when present
            type: str
        extraHosts:
            description: A list of hostnames and IP address mappings to append to the /etc/hosts file on the container.
            returned: when present
            type: complex
            contains:
                hostname:
                    description: The hostname to use in the /etc/hosts entry.
                    returned: when present
                    type: str
                ipAddress:
                    description: The IP address to use in the /etc/hosts entry.
                    returned: when present
                    type: str
        dockerSecurityOptions:
            description: A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems.
            returned: when present
            type: str
        dockerLabels:
            description: A key/value map of labels to add to the container.
            returned: when present
            type: str
        ulimits:
            description: A list of ulimits to set in the container.
            returned: when present
            type: complex
            contains:
                name:
                    description: The type of the ulimit .
                    returned: when present
                    type: str
                softLimit:
                    description: The soft limit for the ulimit type.
                    returned: when present
                    type: int
                hardLimit:
                    description: The hard limit for the ulimit type.
                    returned: when present
                    type: int
        logConfiguration:
            description: The log configuration specification for the container.
            returned: when present
            type: str
        options:
            description: The configuration options to send to the log driver.
            returned: when present
            type: str
        healthCheck:
            description: The container health check command and associated configuration parameters for the container.
            returned: when present
            type: dict
            contains:
                command:
                    description: A string array representing the command that the container runs to determine if it is healthy.
                    type: list
                interval:
                    description: The time period in seconds between each health check execution.
                    type: int
                timeout:
                    description: The time period in seconds to wait for a health check to succeed before it is considered a failure.
                    type: int
                retries:
                    description: The number of times to retry a failed health check before the container is considered unhealthy.
                    type: int
                startPeriod:
                    description: The optional grace period to provide containers time to bootstrap before failed.
                    type: int
        resourceRequirements:
            description: The type and amount of a resource to assign to a container.
            returned: when present
            type: dict
            contains:
                value:
                    description: The value for the specified resource type.
                    type: str
                type:
                    description: The type of resource to assign to a container.
                    type: str
        systemControls:
            description: A list of namespaced kernel parameters to set in the container.
            returned: when present
            type: dict
            contains:
                namespace:
                    description: TThe namespaced kernel.
                    type: str
                value:
                    description: The value for the namespaced kernel.
                    type: str
        firelensConfiguration:
            description: The FireLens configuration for the container.
            returned: when present
            type: dict
            contains:
                type:
                    description: The log router.
                    type: str
                options:
                    description: The options to use when configuring the log router.
                    type: dict
family:
    description: The family of your task definition, used as the definition name
    returned: always
    type: str
task_definition_arn:
    description: ARN of the task definition
    returned: always
    type: str
task_role_arn:
    description: The ARN of the IAM role that containers in this task can assume
    returned: when role is set
    type: str
network_mode:
    description: Network mode for the containers
    returned: always
    type: str
revision:
    description: Revision number that was queried
    returned: always
    type: int
volumes:
    description: The list of volumes in a task
    returned: always
    type: complex
    contains:
        name:
            description: The name of the volume.
            returned: when present
            type: str
        host:
            description: The contents of the host parameter determine whether your data volume
              persists on the host container instance and where it is stored.
            returned: when present
            type: bool
        source_path:
            description: The path on the host container instance that is presented to the container.
            returned: when present
            type: str
status:
    description: The status of the task definition
    returned: always
    type: str
requires_attributes:
    description: The container instance attributes required by your task
    returned: when present
    type: complex
    contains:
        name:
            description: The name of the attribute.
            returned: when present
            type: str
        value:
            description: The value of the attribute.
            returned: when present
            type: str
        targetType:
            description: The type of the target with which to attach the attribute.
            returned: when present
            type: str
        targetId:
            description: The ID of the target.
            returned: when present
            type: str
placement_constraints:
    description: A list of placement constraint objects to use for tasks
    returned: always
    type: complex
    contains:
        type:
            description: The type of constraint.
            returned: when present
            type: str
        expression:
            description: A cluster query language expression to apply to the constraint.
            returned: when present
            type: str
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def main():
    argument_spec = dict(
        task_definition=dict(required=True, type="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    ecs = module.client("ecs")

    try:
        ecs_td = ecs.describe_task_definition(taskDefinition=module.params["task_definition"])["taskDefinition"]
    except botocore.exceptions.ClientError:
        ecs_td = {}

    module.exit_json(changed=False, **camel_dict_to_snake_dict(ecs_td))


if __name__ == "__main__":
    main()

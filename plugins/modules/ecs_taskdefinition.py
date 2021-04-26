#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ecs_taskdefinition
version_added: 1.0.0
short_description: register a task definition in ecs
description:
    - Registers or deregisters task definitions in the Amazon Web Services (AWS) EC2 Container Service (ECS).
author: Mark Chance (@Java1Guy)
requirements: [ json, botocore, boto3 ]
options:
    state:
        description:
            - State whether the task definition should exist or be deleted.
        required: true
        choices: ['present', 'absent']
        type: str
    arn:
        description:
            - The ARN of the task description to delete.
        required: false
        type: str
    family:
        description:
            - A Name that would be given to the task definition.
        required: false
        type: str
    revision:
        description:
            - A revision number for the task definition.
        required: False
        type: int
    force_create:
        description:
            - Always create new task definition.
        required: False
        type: bool
        default: false
    containers:
        description:
            - A list of containers definitions.
            - See U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html) for a complete list of parameters.
        required: True
        type: list
        elements: dict
        suboptions:
            name:
                description: The name of a container.
                required: False
                type: str
            image:
                description: The image used to start a container.
                required: False
                type: str
            repositoryCredentials:
                description: The private repository authentication credentials to use.
                required: False
                type: dict
                suboptions:
                    credentialsParameter:
                        description:
                            - The Amazon Resource Name (ARN) of the secret containing the private repository credentials.
                        required: True
                        type: str
            cpu:
                description: The number of cpu units reserved for the container.
                required: False
                type: int
            memory:
                description: The amount (in MiB) of memory to present to the container.
                required: False
                type: int
            memoryReservation:
                description: The soft limit (in MiB) of memory to reserve for the container.
                required: False
                type: int
            links:
                description:
                    - Allows containers to communicate with each other without the need for port mappings.
                    - This parameter is only supported if I(network_mode=bridge).
                required: False
                type: list
            portMappings:
                description: The list of port mappings for the container.
                required: False
                type: list
                elements: dict
                suboptions:
                    containerPort:
                        description: The port number on the container that is bound to the user-specified or automatically assigned host port.
                        required: False
                        type: int
                    hostPort:
                        description: The port number on the container instance to reserve for your container.
                        required: False
                        type: int
                    protocol:
                        description: The protocol used for the port mapping.
                        required: False
                        type: str
                        default: tcp
                        choices: ['tcp', 'udp']
            essential:
                description:
                    - If I(essential=True), and the container fails or stops for any reason, all other containers that are part of the task are stopped.
                required: False
                type: bool
            entryPoint:
                description: The entry point that is passed to the container.
                required: False
                type: str
            command:
                description: The command that is passed to the container.
                required: False
                type: list
            environment:
                description: The environment variables to pass to a container.
                required: False
                type: list
                elements: dict
                suboptions:
                    name:
                        description: The name of the key-value pair.
                        required: False
                        type: str
                    value:
                        description: The value of the key-value pair.
                        required: False
                        type: str
            environmentFiles:
                description: A list of files containing the environment variables to pass to a container.
                required: False
                type: list
                elements: dict
                suboptions:
                    value:
                        description: The Amazon Resource Name (ARN) of the Amazon S3 object containing the environment variable file.
                        required: False
                        type: str
                    type:
                        description: The file type to use. The only supported value is C(s3).
                        required: False
                        type: str
            mountPoints:
                description: The mount points for data volumes in your container.
                required: False
                type: list
                elements: dict
                suboptions:
                    sourceVolume:
                        description: The name of the volume to mount.
                        required: False
                        type: str
                    containerPath:
                        description: The path on the container to mount the host volume at.
                        required: False
                        type: str
                    readOnly:
                        description:
                            - If this value is C(True), the container has read-only access to the volume.
                            - If this value is C(False), then the container can write to the volume.
                        required: False
                        default: False
                        type: bool
            volumesFrom:
                description: Data volumes to mount from another container.
                required: False
                type: list
                elements: dict
                suboptions:
                    sourceContainer:
                        description:
                            - The name of another container within the same task definition from which to mount volumes.
                        required: False
                        type: str
                    readOnly:
                        description:
                            - If this value is C(True), the container has read-only access to the volume.
                            - If this value is C(False), then the container can write to the volume.
                        required: False
                        default: False
                        type: bool
            linuxParameters:
                description: Linux-specific modifications that are applied to the container, such as Linux kernel capabilities.
                required: False
                type: list
                suboptions:
                    capabilities:
                        description:
                            - The Linux capabilities for the container that are added to or dropped from the default configuration provided by Docker.
                        required: False
                        type: dict
                        suboptions:
                            add:
                                description:
                                    - The Linux capabilities for the container that have been added to the default configuration provided by Docker.
                                    - If I(launch_type=FARGATE), this parameter is not supported.
                                required: False
                                type: list
                                choices: ["ALL", "AUDIT_CONTROL", "AUDIT_WRITE", "BLOCK_SUSPEND", "CHOWN", "DAC_OVERRIDE", "DAC_READ_SEARCH", "FOWNER",
                                          "FSETID", "IPC_LOCK", "IPC_OWNER", "KILL", "LEASE", "LINUX_IMMUTABLE", "MAC_ADMIN", "MAC_OVERRIDE", "MKNOD",
                                          "NET_ADMIN", "NET_BIND_SERVICE", "NET_BROADCAST", "NET_RAW", "SETFCAP", "SETGID", "SETPCAP", "SETUID",
                                          "SYS_ADMIN", "SYS_BOOT", "SYS_CHROOT", "SYS_MODULE", "SYS_NICE", "SYS_PACCT", "SYS_PTRACE", "SYS_RAWIO",
                                          "SYS_RESOURCE", "SYS_TIME", "SYS_TTY_CONFIG", "SYSLOG", "WAKE_ALARM"]
                            drop:
                                description:
                                    - The Linux capabilities for the container that have been removed from the default configuration provided by Docker.
                                required: False
                                type: list
                                choices: ["ALL", "AUDIT_CONTROL", "AUDIT_WRITE", "BLOCK_SUSPEND", "CHOWN", "DAC_OVERRIDE", "DAC_READ_SEARCH", "FOWNER",
                                          "FSETID", "IPC_LOCK", "IPC_OWNER", "KILL", "LEASE", "LINUX_IMMUTABLE", "MAC_ADMIN", "MAC_OVERRIDE", "MKNOD",
                                          "NET_ADMIN", "NET_BIND_SERVICE", "NET_BROADCAST", "NET_RAW", "SETFCAP", "SETGID", "SETPCAP", "SETUID",
                                          "SYS_ADMIN", "SYS_BOOT", "SYS_CHROOT", "SYS_MODULE", "SYS_NICE", "SYS_PACCT", "SYS_PTRACE", "SYS_RAWIO",
                                          "SYS_RESOURCE", "SYS_TIME", "SYS_TTY_CONFIG", "SYSLOG", "WAKE_ALARM"]
                    devices:
                        description:
                            - Any host devices to expose to the container.
                            - If I(launch_type=FARGATE), this parameter is not supported.
                        required: False
                        type: list
                        elements: dict
                        suboptions:
                            hostPath:
                                description: The path for the device on the host container instance.
                                required: True
                                type: str
                            containerPath:
                                description: The path inside the container at which to expose the host device.
                                required: False
                                type: str
                            permissions:
                                description: The explicit permissions to provide to the container for the device.
                                required: False
                                type: list
                    initProcessEnabled:
                        description: Run an init process inside the container that forwards signals and reaps processes.
                        required: False
                        type: bool
                    sharedMemorySize:
                        description:
                            - The value for the size (in MiB) of the /dev/shm volume.
                            - If I(launch_type=FARGATE), this parameter is not supported.
                        required: False
                        type: int
                    tmpfs:
                        description:
                            - The container path, mount options, and size (in MiB) of the tmpfs mount.
                            - If I(launch_type=FARGATE), this parameter is not supported.
                        required: False
                        type: list
                        elements: dict
                        suboptions:
                            containerPath:
                                description: The absolute file path where the tmpfs volume is to be mounted.
                                required: True
                                type: str
                            size:
                                description: The size (in MiB) of the tmpfs volume.
                                required: True
                                type: int
                            mountOptions:
                                description: The list of tmpfs volume mount options.
                                required: False
                                type: list
                                choices: ["defaults", "ro", "rw", "suid", "nosuid", "dev", "nodev", "exec", "noexec", "sync", "async", "dirsync",
                                          "remount", "mand", "nomand", "atime", "noatime", "diratime", "nodiratime", "bind", "rbind", "unbindable",
                                          "runbindable", "private", "rprivate", "shared", "rshared", "slave", "rslave", "relatime", "norelatime",
                                          "strictatime", "nostrictatime", "mode", "uid", "gid", "nr_inodes", "nr_blocks", "mpol"]
                    maxSwap:
                        description:
                            - The total amount of swap memory (in MiB) a container can use.
                            - If I(launch_type=FARGATE), this parameter is not supported.
                        required: False
                        type: int
                    swappiness:
                        description:
                            - This allows you to tune a container's memory swappiness behavior.
                            - If I(launch_type=FARGATE), this parameter is not supported.
                        required: False
                        type: int
            secrets:
                description: The secrets to pass to the container.
                required: False
                type: list
                elements: dict
                suboptions:
                    name:
                        description: The value to set as the environment variable on the container.
                        required: True
                        type: str
                    size:
                        description: The secret to expose to the container.
                        required: True
                        type: str
            dependsOn:
                description:
                    - The dependencies defined for container startup and shutdown.
                    - When a dependency is defined for container startup, for container shutdown it is reversed.
                required: False
                type: list
                elements: dict
                suboptions:
                    containerName:
                        description: The name of a container.
                        type: str
                        required: True
                    condition:
                        description: The dependency condition of the container.
                        type: str
                        required: True
                        choices: ["start", "complete", "success", "healthy"]
            startTimeout:
                description: Time duration (in seconds) to wait before giving up on resolving dependencies for a container.
                required: False
                type: int
            stopTimeout:
                description: Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own.
                required: False
                type: int
            hostname:
                description:
                    - The hostname to use for your container.
                    - This parameter is not supported if I(network_mode=awsvpc).
                required: False
                type: str
            user:
                description:
                    - The user to use inside the container.
                    - This parameter is not supported for Windows containers.
                required: False
                type: str
            workingDirectory:
                description: The working directory in which to run commands inside the container.
                required: False
                type: str
            disableNetworking:
                description: When this parameter is C(True), networking is disabled within the container.
                required: False
                type: bool
            privileged:
                description: When this parameter is C(True), the container is given elevated privileges on the host container instance.
                required: False
                type: bool
            readonlyRootFilesystem:
                description: When this parameter is C(True), the container is given read-only access to its root file system.
                required: false
                type: bool
            dnsServers:
                description:
                    - A list of DNS servers that are presented to the container.
                    - This parameter is not supported for Windows containers.
                required: False
                type: list
            dnsSearchDomains:
                description:
                    - A list of DNS search domains that are presented to the container.
                    - This parameter is not supported for Windows containers.
                required: False
                type: list
            extraHosts:
                description:
                    - A list of hostnames and IP address mappings to append to the /etc/hosts file on the container.
                    - This parameter is not supported for Windows containers or tasks that use I(network_mode=awsvpc).
                required: False
                type: list
                elements: dict
                suboptions:
                    hostname:
                        description: The hostname to use in the /etc/hosts entry.
                        type: str
                        required: False
                    ipAddress:
                        description: The IP address to use in the /etc/hosts entry.
                        type: str
                        required: False
            dockerSecurityOptions:
                description:
                    - A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems.
                    - This parameter is not supported for Windows containers.
                required: False
                type: list
            interactive:
                description:
                    - When I(interactive=True), it allows to deploy containerized applications that require stdin or a tty to be allocated.
                required: False
                type: bool
            pseudoTerminal:
                description: When this parameter is C(True), a TTY is allocated.
                required: False
                type: bool
            dockerLabels:
                description: A key/value map of labels to add to the container.
                required: False
                type: dict
            ulimits:
                description:
                    - A list of ulimits to set in the container.
                    - This parameter is not supported for Windows containers.
                required: False
                type: list
                elements: dict
                suboptions:
                    name:
                        description: The type of the ulimit.
                        type: str
                        required: False
                    softLimit:
                        description: The soft limit for the ulimit type.
                        type: int
                        required: False
                    hardLimit:
                        description: The hard limit for the ulimit type.
                        type: int
                        required: False
            logConfiguration:
                description: The log configuration specification for the container.
                required: False
                type: dict
                suboptions:
                    logDriver:
                        description:
                            - The log driver to use for the container.
                            - For tasks on AWS Fargate, the supported log drivers are C(awslogs), C(splunk), and C(awsfirelens).
                            - For tasks hosted on Amazon EC2 instances, the supported log drivers are C(awslogs), C(fluentd),
                              C(gelf), C(json-file), C(journald), C(logentries), C(syslog), C(splunk), and C(awsfirelens).
                        type: str
                        required: False
            options:
                description: The configuration options to send to the log driver.
                required: False
                type: str
            secretOptions:
                description: The secrets to pass to the log configuration.
                required: False
                type: list
                elements: dict
                suboptions:
                    name:
                        description: The name of the secret.
                        type: str
                        required: False
                    valueFrom:
                        description: The secret to expose to the container.
                        type: str
                        required: False
            healthCheck:
                description: The health check command and associated configuration parameters for the container.
                required: False
                type: dict
            systemControls:
                description: A list of namespaced kernel parameters to set in the container.
                required: False
                type: list
            resourceRequirements:
                description:
                    - The type and amount of a resource to assign to a container.
                    - The only supported resource is a C(GPU).
                required: False
                type: list
    network_mode:
        description:
            - The Docker networking mode to use for the containers in the task.
            - C(awsvpc) mode was added in Ansible 2.5
            - Windows containers must use I(network_mode=default), which will utilize docker NAT networking.
            - Setting I(network_mode=default) for a Linux container will use C(bridge) mode.
        required: false
        default: bridge
        choices: [ 'default', 'bridge', 'host', 'none', 'awsvpc' ]
        type: str
    task_role_arn:
        description:
            - The Amazon Resource Name (ARN) of the IAM role that containers in this task can assume. All containers in this task are granted
              the permissions that are specified in this role.
        required: false
        type: str
    execution_role_arn:
        description:
            - The Amazon Resource Name (ARN) of the task execution role that the Amazon ECS container agent and the Docker daemon can assume.
        required: false
        type: str
    volumes:
        description:
            - A list of names of volumes to be attached.
        required: False
        type: list
        elements: dict
        suboptions:
            name:
                type: str
                description: The name of the volume.
                required: true
    launch_type:
        description:
            - The launch type on which to run your task.
        required: false
        type: str
        choices: ["EC2", "FARGATE"]
    cpu:
        description:
            - The number of cpu units used by the task. If I(launch_type=EC2), this field is optional and any value can be used.
            - If I(launch_type=FARGATE), this field is required and you must use one of C(256), C(512), C(1024), C(2048), C(4096).
        required: false
        type: str
    memory:
        description:
            - The amount (in MiB) of memory used by the task. If I(launch_type=EC2), this field is optional and any value can be used.
            - If I(launch_type=FARGATE), this field is required and is limited by the CPU.
        required: false
        type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = r'''
- name: Create task definition
  community.aws.ecs_taskdefinition:
    containers:
    - name: simple-app
      cpu: 10
      essential: true
      image: "httpd:2.4"
      memory: 300
      mountPoints:
      - containerPath: /usr/local/apache2/htdocs
        sourceVolume: my-vol
      portMappings:
      - containerPort: 80
        hostPort: 80
      logConfiguration:
        logDriver: awslogs
        options:
          awslogs-group: /ecs/test-cluster-taskdef
          awslogs-region: us-west-2
          awslogs-stream-prefix: ecs
    - name: busybox
      command:
        - >
          /bin/sh -c "while true; do echo '<html><head><title>Amazon ECS Sample App</title></head><body><div><h1>Amazon ECS Sample App</h1><h2>Congratulations!
          </h2><p>Your application is now running on a container in Amazon ECS.</p>' > top; /bin/date > date ; echo '</div></body></html>' > bottom;
          cat top date bottom > /usr/local/apache2/htdocs/index.html ; sleep 1; done"
      cpu: 10
      entryPoint:
      - sh
      - "-c"
      essential: false
      image: busybox
      memory: 200
      volumesFrom:
      - sourceContainer: simple-app
    volumes:
    - name: my-vol
    family: test-cluster-taskdef
    state: present
  register: task_output

- name: Create task definition
  community.aws.ecs_taskdefinition:
    family: nginx
    containers:
    - name: nginx
      essential: true
      image: "nginx"
      portMappings:
      - containerPort: 8080
        hostPort: 8080
      cpu: 512
      memory: 1024
    state: present

- name: Create task definition
  community.aws.ecs_taskdefinition:
    family: nginx
    containers:
    - name: nginx
      essential: true
      image: "nginx"
      portMappings:
      - containerPort: 8080
        hostPort: 8080
    launch_type: FARGATE
    cpu: 512
    memory: 1024
    state: present
    network_mode: awsvpc

- name: Create task definition
  community.aws.ecs_taskdefinition:
    family: nginx
    containers:
    - name: nginx
      essential: true
      image: "nginx"
      portMappings:
      - containerPort: 8080
        hostPort: 8080
      cpu: 512
      memory: 1024
      dependsOn:
      - containerName: "simple-app"
        condition: "start"

# Create Task Definition with Environment Variables and Secrets
- name: Create task definition
  community.aws.ecs_taskdefinition:
    family: nginx
    containers:
    - name: nginx
      essential: true
      image: "nginx"
      environment:
        - name: "PORT"
          value: "8080"
      secrets:
        # For variables stored in Secrets Manager
        - name: "NGINX_HOST"
          valueFrom: "arn:aws:secretsmanager:us-west-2:123456789012:secret:nginx/NGINX_HOST"
        # For variables stored in Parameter Store
        - name: "API_KEY"
          valueFrom: "arn:aws:ssm:us-west-2:123456789012:parameter/nginx/API_KEY"
    launch_type: FARGATE
    cpu: 512
    memory: 1GB
    state: present
    network_mode: awsvpc
'''
RETURN = r'''
taskdefinition:
    description: a reflection of the input parameters
    type: dict
    returned: always
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils._text import to_text

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


class EcsTaskManager:
    """Handles ECS Tasks"""

    def __init__(self, module):
        self.module = module

        self.ecs = module.client('ecs')

    def describe_task(self, task_name):
        try:
            response = self.ecs.describe_task_definition(taskDefinition=task_name)
            return response['taskDefinition']
        except botocore.exceptions.ClientError:
            return None

    def register_task(self, family, task_role_arn, execution_role_arn, network_mode, container_definitions, volumes, launch_type, cpu, memory):
        validated_containers = []

        # Ensures the number parameters are int as required by boto
        for container in container_definitions:
            for param in ('memory', 'cpu', 'memoryReservation'):
                if param in container:
                    container[param] = int(container[param])

            if 'portMappings' in container:
                for port_mapping in container['portMappings']:
                    for port in ('hostPort', 'containerPort'):
                        if port in port_mapping:
                            port_mapping[port] = int(port_mapping[port])
                    if network_mode == 'awsvpc' and 'hostPort' in port_mapping:
                        if port_mapping['hostPort'] != port_mapping.get('containerPort'):
                            self.module.fail_json(msg="In awsvpc network mode, host port must be set to the same as "
                                                  "container port or not be set")

            validated_containers.append(container)

        params = dict(
            family=family,
            taskRoleArn=task_role_arn,
            containerDefinitions=container_definitions,
            volumes=volumes
        )
        if network_mode != 'default':
            params['networkMode'] = network_mode
        if cpu:
            params['cpu'] = cpu
        if memory:
            params['memory'] = memory
        if launch_type:
            params['requiresCompatibilities'] = [launch_type]
        if execution_role_arn:
            params['executionRoleArn'] = execution_role_arn

        try:
            response = self.ecs.register_task_definition(**params)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Failed to register task")

        return response['taskDefinition']

    def describe_task_definitions(self, family):
        data = {
            "taskDefinitionArns": [],
            "nextToken": None
        }

        def fetch():
            # Boto3 is weird about params passed, so only pass nextToken if we have a value
            params = {
                'familyPrefix': family
            }

            if data['nextToken']:
                params['nextToken'] = data['nextToken']

            result = self.ecs.list_task_definitions(**params)
            data['taskDefinitionArns'] += result['taskDefinitionArns']
            data['nextToken'] = result.get('nextToken', None)
            return data['nextToken'] is not None

        # Fetch all the arns, possibly across multiple pages
        while fetch():
            pass

        # Return the full descriptions of the task definitions, sorted ascending by revision
        return list(
            sorted(
                [self.ecs.describe_task_definition(taskDefinition=arn)['taskDefinition'] for arn in data['taskDefinitionArns']],
                key=lambda td: td['revision']
            )
        )

    def deregister_task(self, taskArn):
        response = self.ecs.deregister_task_definition(taskDefinition=taskArn)
        return response['taskDefinition']


def main():
    argument_spec = dict(
        state=dict(required=True, choices=['present', 'absent']),
        arn=dict(required=False, type='str'),
        family=dict(required=False, type='str'),
        revision=dict(required=False, type='int'),
        force_create=dict(required=False, default=False, type='bool'),
        containers=dict(required=True, type='list', elements='dict'),
        network_mode=dict(required=False, default='bridge', choices=['default', 'bridge', 'host', 'none', 'awsvpc'], type='str'),
        task_role_arn=dict(required=False, default='', type='str'),
        execution_role_arn=dict(required=False, default='', type='str'),
        volumes=dict(required=False, type='list', elements='dict'),
        launch_type=dict(required=False, choices=['EC2', 'FARGATE']),
        cpu=dict(),
        memory=dict(required=False, type='str')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              required_if=[('launch_type', 'FARGATE', ['cpu', 'memory'])]
                              )

    task_to_describe = None
    task_mgr = EcsTaskManager(module)
    results = dict(changed=False)

    if module.params['launch_type']:
        if not module.botocore_at_least('1.8.4'):
            module.fail_json(msg='botocore needs to be version 1.8.4 or higher to use launch_type')

    if module.params['execution_role_arn']:
        if not module.botocore_at_least('1.10.44'):
            module.fail_json(msg='botocore needs to be version 1.10.44 or higher to use execution_role_arn')

    if module.params['state'] == 'present':
        if 'containers' not in module.params or not module.params['containers']:
            module.fail_json(msg="To use task definitions, a list of containers must be specified")

        if 'family' not in module.params or not module.params['family']:
            module.fail_json(msg="To use task definitions, a family must be specified")

        network_mode = module.params['network_mode']
        launch_type = module.params['launch_type']
        if launch_type == 'FARGATE' and network_mode != 'awsvpc':
            module.fail_json(msg="To use FARGATE launch type, network_mode must be awsvpc")

        for container in module.params['containers']:
            if container.get('links') and network_mode == 'awsvpc':
                module.fail_json(msg='links parameter is not supported if network mode is awsvpc.')

            for environment in container.get('environment', []):
                environment['value'] = to_text(environment['value'])

            for environment_file in container.get('environmentFiles', []):
                if environment_file['value'] != 's3':
                    module.fail_json(msg='The only supported value for environmentFiles is s3.')

            for linux_param in container.get('linuxParameters', {}):
                if linux_param.get('devices') and launch_type == 'FARGATE':
                    module.fail_json(msg='devices parameter is not supported with the FARGATE launch type.')

                if linux_param.get('maxSwap') and launch_type == 'FARGATE':
                    module.fail_json(msg='maxSwap parameter is not supported with the FARGATE launch type.')
                elif linux_param.get('maxSwap') and linux_param['maxSwap'] < 0:
                    module.fail_json(msg='Accepted values for maxSwap are 0 or any positive integer.')

                if linux_param.get('swappiness') and (linux_param['swappiness'] < 0 or linux_param['swappiness'] > 100):
                    module.fail_json(msg='Accepted values for swappiness are whole numbers between 0 and 100.')

                if linux_param.get('sharedMemorySize') and launch_type == 'FARGATE':
                    module.fail_json(msg='sharedMemorySize parameter is not supported with the FARGATE launch type.')

                if linux_param.get('tmpfs') and launch_type == 'FARGATE':
                    module.fail_json(msg='tmpfs parameter is not supported with the FARGATE launch type.')

            if container.get('hostname') and network_mode == 'awsvpc':
                module.fail_json(msg='hostname parameter is not supported when the awsvpc network mode is used.')

            if container.get('extraHosts') and network_mode == 'awsvpc':
                module.fail_json(msg='extraHosts parameter is not supported when the awsvpc network mode is used.')

        family = module.params['family']
        existing_definitions_in_family = task_mgr.describe_task_definitions(module.params['family'])

        if 'revision' in module.params and module.params['revision']:
            # The definition specifies revision. We must guarantee that an active revision of that number will result from this.
            revision = int(module.params['revision'])

            # A revision has been explicitly specified. Attempt to locate a matching revision
            tasks_defs_for_revision = [td for td in existing_definitions_in_family if td['revision'] == revision]
            existing = tasks_defs_for_revision[0] if len(tasks_defs_for_revision) > 0 else None

            if existing and existing['status'] != "ACTIVE":
                # We cannot reactivate an inactive revision
                module.fail_json(msg="A task in family '%s' already exists for revision %d, but it is inactive" % (family, revision))
            elif not existing:
                if not existing_definitions_in_family and revision != 1:
                    module.fail_json(msg="You have specified a revision of %d but a created revision would be 1" % revision)
                elif existing_definitions_in_family and existing_definitions_in_family[-1]['revision'] + 1 != revision:
                    module.fail_json(msg="You have specified a revision of %d but a created revision would be %d" %
                                         (revision, existing_definitions_in_family[-1]['revision'] + 1))
        else:
            existing = None

            def _right_has_values_of_left(left, right):
                # Make sure the values are equivalent for everything left has
                for k, v in left.items():
                    if not ((not v and (k not in right or not right[k])) or (k in right and v == right[k])):
                        # We don't care about list ordering because ECS can change things
                        if isinstance(v, list) and k in right:
                            left_list = v
                            right_list = right[k] or []

                            if len(left_list) != len(right_list):
                                return False

                            for list_val in left_list:
                                if list_val not in right_list:
                                    return False
                        else:
                            return False

                # Make sure right doesn't have anything that left doesn't
                for k, v in right.items():
                    if v and k not in left:
                        return False

                return True

            def _task_definition_matches(requested_volumes, requested_containers, requested_task_role_arn, existing_task_definition):
                if td['status'] != "ACTIVE":
                    return None

                if requested_task_role_arn != td.get('taskRoleArn', ""):
                    return None

                existing_volumes = td.get('volumes', []) or []

                if len(requested_volumes) != len(existing_volumes):
                    # Nope.
                    return None

                if len(requested_volumes) > 0:
                    for requested_vol in requested_volumes:
                        found = False

                        for actual_vol in existing_volumes:
                            if _right_has_values_of_left(requested_vol, actual_vol):
                                found = True
                                break

                        if not found:
                            return None

                existing_containers = td.get('containerDefinitions', []) or []

                if len(requested_containers) != len(existing_containers):
                    # Nope.
                    return None

                for requested_container in requested_containers:
                    found = False

                    for actual_container in existing_containers:
                        if _right_has_values_of_left(requested_container, actual_container):
                            found = True
                            break

                    if not found:
                        return None

                return existing_task_definition

            # No revision explicitly specified. Attempt to find an active, matching revision that has all the properties requested
            for td in existing_definitions_in_family:
                requested_volumes = module.params['volumes'] or []
                requested_containers = module.params['containers'] or []
                requested_task_role_arn = module.params['task_role_arn']
                existing = _task_definition_matches(requested_volumes, requested_containers, requested_task_role_arn, td)

                if existing:
                    break

        if existing and not module.params.get('force_create'):
            # Awesome. Have an existing one. Nothing to do.
            results['taskdefinition'] = existing
        else:
            if not module.check_mode:
                # Doesn't exist. create it.
                volumes = module.params.get('volumes', []) or []
                results['taskdefinition'] = task_mgr.register_task(module.params['family'],
                                                                   module.params['task_role_arn'],
                                                                   module.params['execution_role_arn'],
                                                                   module.params['network_mode'],
                                                                   module.params['containers'],
                                                                   volumes,
                                                                   module.params['launch_type'],
                                                                   module.params['cpu'],
                                                                   module.params['memory'])
            results['changed'] = True

    elif module.params['state'] == 'absent':
        # When de-registering a task definition, we can specify the ARN OR the family and revision.
        if module.params['state'] == 'absent':
            if 'arn' in module.params and module.params['arn'] is not None:
                task_to_describe = module.params['arn']
            elif 'family' in module.params and module.params['family'] is not None and 'revision' in module.params and \
                    module.params['revision'] is not None:
                task_to_describe = module.params['family'] + ":" + str(module.params['revision'])
            else:
                module.fail_json(msg="To use task definitions, an arn or family and revision must be specified")

        existing = task_mgr.describe_task(task_to_describe)

        if not existing:
            pass
        else:
            # It exists, so we should delete it and mark changed. Return info about the task definition deleted
            results['taskdefinition'] = existing
            if 'status' in existing and existing['status'] == "INACTIVE":
                results['changed'] = False
            else:
                if not module.check_mode:
                    task_mgr.deregister_task(task_to_describe)
                results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()

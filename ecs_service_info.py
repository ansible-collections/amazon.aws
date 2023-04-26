#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ecs_service_info
version_added: 1.0.0
short_description: List or describe services in ECS
description:
    - Lists or describes services in ECS.
author:
    - "Mark Chance (@Java1Guy)"
    - "Darek Kaczynski (@kaczynskid)"
options:
    details:
        description:
            - Set this to true if you want detailed information about the services.
        required: false
        default: false
        type: bool
    events:
        description:
            - Whether to return ECS service events. Only has an effect if I(details=true).
        required: false
        default: true
        type: bool
    cluster:
        description:
            - The cluster ARNS in which to list the services.
        required: false
        type: str
    service:
        description:
            - One or more services to get details for
        required: false
        type: list
        elements: str
        aliases: ['name']
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic listing example
- community.aws.ecs_service_info:
    cluster: test-cluster
    service: console-test-service
    details: true
  register: output

# Basic listing example
- community.aws.ecs_service_info:
    cluster: test-cluster
  register: output
"""

RETURN = r"""
services:
    description: When details is false, returns an array of service ARNs, otherwise an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        clusterArn:
            description: The Amazon Resource Name (ARN) of the of the cluster that hosts the service.
            returned: always
            type: str
        desiredCount:
            description: The desired number of instantiations of the task definition to keep running on the service.
            returned: always
            type: int
        loadBalancers:
            description: A list of load balancer objects
            returned: always
            type: complex
            contains:
                loadBalancerName:
                    description: the name
                    returned: always
                    type: str
                containerName:
                    description: The name of the container to associate with the load balancer.
                    returned: always
                    type: str
                containerPort:
                    description: The port on the container to associate with the load balancer.
                    returned: always
                    type: int
        pendingCount:
            description: The number of tasks in the cluster that are in the PENDING state.
            returned: always
            type: int
        runningCount:
            description: The number of tasks in the cluster that are in the RUNNING state.
            returned: always
            type: int
        serviceArn:
            description:
              - The Amazon Resource Name (ARN) that identifies the service. The ARN contains the arn:aws:ecs namespace, followed by the region of the
                service, the AWS account ID of the service owner, the service namespace, and then the service name.
            sample: 'arn:aws:ecs:us-east-1:123456789012:service/my-service'
            returned: always
            type: str
        serviceName:
            description: A user-generated string used to identify the service
            returned: always
            type: str
        status:
            description: The valid values are ACTIVE, DRAINING, or INACTIVE.
            returned: always
            type: str
        taskDefinition:
            description: The ARN of a task definition to use for tasks in the service.
            returned: always
            type: str
        deployments:
            description: list of service deployments
            returned: always
            type: list
            elements: dict
        events:
            description: list of service events
            returned: when events is true
            type: list
            elements: dict
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class EcsServiceManager:
    """Handles ECS Services"""

    def __init__(self, module):
        self.module = module
        self.ecs = module.client("ecs")

    @AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
    def list_services_with_backoff(self, **kwargs):
        paginator = self.ecs.get_paginator("list_services")
        try:
            return paginator.paginate(**kwargs).build_full_result()
        except is_boto3_error_code("ClusterNotFoundException") as e:
            self.module.fail_json_aws(e, "Could not find cluster to list services")

    @AWSRetry.jittered_backoff(retries=5, delay=5, backoff=2.0)
    def describe_services_with_backoff(self, **kwargs):
        return self.ecs.describe_services(**kwargs)

    def list_services(self, cluster):
        fn_args = dict()
        if cluster and cluster is not None:
            fn_args["cluster"] = cluster
        try:
            response = self.list_services_with_backoff(**fn_args)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list ECS services")
        relevant_response = dict(services=response["serviceArns"])
        return relevant_response

    def describe_services(self, cluster, services):
        fn_args = dict()
        if cluster and cluster is not None:
            fn_args["cluster"] = cluster
        fn_args["services"] = services
        try:
            response = self.describe_services_with_backoff(**fn_args)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't describe ECS services")
        running_services = [self.extract_service_from(service) for service in response.get("services", [])]
        services_not_running = response.get("failures", [])
        return running_services, services_not_running

    def extract_service_from(self, service):
        # some fields are datetime which is not JSON serializable
        # make them strings
        if "deployments" in service:
            for d in service["deployments"]:
                if "createdAt" in d:
                    d["createdAt"] = str(d["createdAt"])
                if "updatedAt" in d:
                    d["updatedAt"] = str(d["updatedAt"])
        if "events" in service:
            if not self.module.params["events"]:
                del service["events"]
            else:
                for e in service["events"]:
                    if "createdAt" in e:
                        e["createdAt"] = str(e["createdAt"])
        return service


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    """ https://stackoverflow.com/a/312464 """
    for i in range(0, len(l), n):
        yield l[i:i + n]  # fmt: skip


def main():
    argument_spec = dict(
        details=dict(type="bool", default=False),
        events=dict(type="bool", default=True),
        cluster=dict(),
        service=dict(type="list", elements="str", aliases=["name"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    show_details = module.params.get("details")

    task_mgr = EcsServiceManager(module)
    if show_details:
        if module.params["service"]:
            services = module.params["service"]
        else:
            services = task_mgr.list_services(module.params["cluster"])["services"]
        ecs_info = dict(services=[], services_not_running=[])
        for chunk in chunks(services, 10):
            running_services, services_not_running = task_mgr.describe_services(module.params["cluster"], chunk)
            ecs_info["services"].extend(running_services)
            ecs_info["services_not_running"].extend(services_not_running)
    else:
        ecs_info = task_mgr.list_services(module.params["cluster"])

    module.exit_json(changed=False, **ecs_info)


if __name__ == "__main__":
    main()

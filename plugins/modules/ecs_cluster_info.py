#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = '''
---
module: ecs_cluster_info
version_added: 1.0.0
short_description: Gather information about ECS cluster
description:
  - Gather information about ECS cluster in AWS.
author:
  - "Aubin Bikouo (@abikouo)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DescribeClusters.html) for possible filters.
    type: dict
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all ECS clusters
- amazon.aws.ecs_cluster_info:

# Gather information about a particular ECS
- amazon.aws.ecs_cluster_info:
    filters:
      clusters:
        - ecs-sample-cluster-01

'''

RETURN = '''
clusters:
  description: List of matching Amazon Elastic Container Service.
  returned: always
  type: complex
  contains:
    cluster_arn:
      description:
        - The Amazon Resource Name (ARN) that identifies the cluster.
      type: str
      returned: always
    cluster_name:
      description:
        - A user-generated string that you use to identify your cluster.
      type: str
      returned: always
    configuration:
      description:
        - The execute command configuration for the cluster.
      type: complex
      returned: when value CONFIGURATIONS is specified in include filters.
      contains:
        execute_command_configuration:
          description:
            - The details of the execute command configuration.
          type: str
          returned: always
        kms_key_id:
          description:
            - Specify an Key Management Service key ID to encrypt the data between the local client and the container.
          type: str
          returned: always
        logging:
          description:
            - The log setting to use for redirecting logs for your execute command results.
          type: str
          returned: always
        log_configuration:
          description:
            - The log configuration for the results of the execute command actions.
              The logs can be sent to CloudWatch Logs or an Amazon S3 bucket.
          type: complex
          returned: always
          contains:
            cloud_watch_log_group_name:
              description:
                - The name of the CloudWatch log group to send logs to.
              type: str
              returned: always
            cloud_watch_encryption_enabled:
              description:
                - Determines whether to use encryption on the CloudWatch logs.
              type: bool
              returned: always
            s3_bucket_name:
              description:
                - The name of the S3 bucket to send logs to.
              type: str
              returned: always
            s3_encryption_enabled:
              description:
                - Determines whether to use encryption on the S3 logs.
              type: bool
              returned: always
            s3_key_prefix:
              description:
                - An optional folder in the S3 bucket to place logs in.
              type: str
              returned: always
    status:
      description:
        - The status of the cluster.
      type: str
      returned: always
      sample: ACTIVE
    registered_container_instances_count:
      description:
        - The number of container instances registered into the cluster.
      type: int
      returned: always
    running_tasks_count:
      description:
        - The number of tasks in the cluster that are in the RUNNING state.
      type: int
      returned: always
    pending_tasks_count:
      description:
        - The number of tasks in the cluster that are in the PENDING state.
      type: int
      returned: always
    active_services_count:
      description:
        - The number of services that are running on the cluster in an ACTIVE state.
      type: int
      returned: always
    statistics:
      description:
        - A dict of Additional information about your clusters that are separated by launch type.
      type: dict
      returned: always
    tags:
      description: A dict of tags associated with the ECS cluster.
      returned: always
      type: dict
    settings:
      description:
        - A dict of settings associated with the ECS cluster.
      type: dict
      returned: always
    capacity_providers:
      description:
        - The capacity providers associated with the cluster.
      type: list
      returned: always
      sample: []
    default_capacity_provider_strategy:
      description:
        - The default capacity provider strategy for the cluster.
      type: complex
      returned: always
      contains:
        capacity_provider:
          description:
            - The short name of the capacity provider.
          type: str
          returned: always
        weight:
          description:
            - The weight value designates the relative percentage of the total number of tasks launched that should use the specified capacity provider.
          type: int
          returned: always
        base:
          description:
            - The base value designates how many tasks, at a minimum, to run on the specified capacity provider.
          type: int
          returned: always
    attachments:
      description:
        - The resources attached to a cluster.
      type: complex
      returned: when value ATTACHMENTS is specified in include filters.
      contains:
        id:
          description:
            - The unique identifier for the attachment.
          type: str
          returned: always
        type:
          description:
            - The type of the attachment, such as ElasticNetworkInterface .
          type: str
          returned: always
        status:
          description:
            - The status of the attachment.
          type: str
          returned: always
        details:
          description:
            - Details of the attachment.
          type: complex
          returned: always
          contains:
            name:
              description:
                - The name of the key-value pair.
              type: str
              returned: always
            value:
              description:
                - The value of the key-value pair.
              type: str
              returned: always
    attachments_status:
      description:
        - The status of the capacity providers associated with the cluster.
      type: str
      returned: when ATTACHMENTS in specified in include filters.
      sample: UPDATE_IN_PROGRESS
'''

try:
    from botocore.exceptions import ClientError
    from botocore.exceptions import NoCredentialsError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def describe_clusters(module):

    connection = module.client('ecs', retry_decorator=AWSRetry.jittered_backoff())

    params = module.params.get("filters") or dict()

    try:
        result = connection.describe_clusters(aws_retry=True, **params)['clusters']
    except is_boto3_error_code('InvalidNetworkInterfaceID.NotFound'): # TODO: update with corresponding exception
        module.exit_json(clusters=[])
    except (ClientError, NoCredentialsError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)

    # Modify boto3 tags list to be ansible friendly dict and then camel_case
    camel_clusters = []
    for cluster in result:
        cluster['tags'] = boto3_tag_list_to_ansible_dict(cluster['Tags'])
        cluster['statistics'] = boto3_tag_list_to_ansible_dict(cluster.get('statistics', []))
        cluster['settings'] = boto3_tag_list_to_ansible_dict(cluster.get('settings', []))
        camel_clusters.append(camel_dict_to_snake_dict(cluster, ignore_list=["tags"]))

    module.exit_json(clusters=camel_clusters)


def main():

    module = AnsibleAWSModule(
        argument_spec=dict(
            filters=dict(default=None, type='dict')
        ),
        supports_check_mode=True,
    )

    describe_clusters(module)


if __name__ == '__main__':
    main()

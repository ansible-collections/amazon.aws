#!/usr/bin/python
# Copyright: (c) 2021, Daniil Kupchenko (@oukooveu)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: aws_msk_cluster
short_description: Manage Amazon MSK clusters.
version_added: "2.0.0"
description:
    - Create, delete and modify Amazon MSK (Managed Streaming for Apache Kafka) clusters.
author:
    - Daniil Kupchenko (@oukooveu)
options:
    state:
        description: Create (C(present)) or delete (C(absent)) cluster.
        choices: ['present', 'absent']
        type: str
        default: 'present'
    name:
        description: The name of the cluster.
        required: true
        type: str
    version:
        description:
            - The version of Apache Kafka.
            - This version should exist in given configuration.
            - This parameter is required when I(state=present).
            - Update operation requires botocore version >= 1.16.19.
        type: str
    configuration_arn:
        description:
            - ARN of the configuration to use.
            - This parameter is required when I(state=present).
        type: str
    configuration_revision:
        description:
            - The revision of the configuration to use.
            - This parameter is required when I(state=present).
        type: int
    nodes:
        description: The number of broker nodes in the cluster. Should be greater or equal to two.
        type: int
        default: 3
    instance_type:
        description:
            - The type of Amazon EC2 instances to use for Kafka brokers.
            - Update operation requires botocore version >= 1.19.58.
        choices:
            - kafka.t3.small
            - kafka.m5.large
            - kafka.m5.xlarge
            - kafka.m5.2xlarge
            - kafka.m5.4xlarge
        default: kafka.t3.small
        type: str
    ebs_volume_size:
        description: The size in GiB of the EBS volume for the data drive on each broker node.
        type: int
        default: 100
    subnets:
        description:
            - The list of subnets to connect to in the client virtual private cloud (VPC).
              AWS creates elastic network interfaces inside these subnets. Client applications use
              elastic network interfaces to produce and consume data.
            - Client subnets can't be in Availability Zone us-east-1e.
            - This parameter is required when I(state=present).
        type: list
        elements: str
    security_groups:
        description:
            - The AWS security groups to associate with the elastic network interfaces in order to specify
              who can connect to and communicate with the Amazon MSK cluster.
              If you don't specify a security group, Amazon MSK uses the default security group associated with the VPC.
        type: list
        elements: str
    encryption:
        description:
            - Includes all encryption-related information.
            - Effective only for new cluster and can not be updated.
        type: dict
        suboptions:
            kms_key_id:
                description:
                    - The ARN of the AWS KMS key for encrypting data at rest. If you don't specify a KMS key, MSK creates one for you and uses it.
                default: Null
                type: str
            in_transit:
                description: The details for encryption in transit.
                type: dict
                suboptions:
                    in_cluster:
                        description:
                            - When set to true, it indicates that data communication among the broker nodes of the cluster is encrypted.
                              When set to false, the communication happens in plaintext.
                        type: bool
                        default: True
                    client_broker:
                        description:
                            - Indicates the encryption setting for data in transit between clients and brokers. The following are the possible values.
                              TLS means that client-broker communication is enabled with TLS only.
                              TLS_PLAINTEXT means that client-broker communication is enabled for both TLS-encrypted, as well as plaintext data.
                              PLAINTEXT means that client-broker communication is enabled in plaintext only.
                        choices:
                            - TLS
                            - TLS_PLAINTEXT
                            - PLAINTEXT
                        type: str
                        default: TLS
    authentication:
        description:
            - Includes all client authentication related information.
            - Effective only for new cluster and can not be updated.
        type: dict
        suboptions:
            tls_ca_arn:
                description: List of ACM Certificate Authority ARNs.
                type: list
                elements: str
            sasl_scram:
                description: SASL/SCRAM authentication is enabled or not.
                type: bool
                default: False
    enhanced_monitoring:
        description: Specifies the level of monitoring for the MSK cluster.
        choices:
            - DEFAULT
            - PER_BROKER
            - PER_TOPIC_PER_BROKER
            - PER_TOPIC_PER_PARTITION
        default: DEFAULT
        type: str
    open_monitoring:
        description: The settings for open monitoring.
        type: dict
        suboptions:
            jmx_exporter:
                description: Indicates whether you want to enable or disable the JMX Exporter.
                type: bool
                default: False
            node_exporter:
                description: Indicates whether you want to enable or disable the Node Exporter.
                type: bool
                default: False
    logging:
        description: Logging configuration.
        type: dict
        suboptions:
            cloudwatch:
                description: Details of the CloudWatch Logs destination for broker logs.
                type: dict
                suboptions:
                    enabled:
                        description: Specifies whether broker logs get sent to the specified CloudWatch Logs destination.
                        type: bool
                        default: False
                    log_group:
                        description: The CloudWatch log group that is the destination for broker logs.
                        type: str
                        required: False
            firehose:
                description: Details of the Kinesis Data Firehose delivery stream that is the destination for broker logs.
                type: dict
                suboptions:
                    enabled:
                        description: Specifies whether broker logs get send to the specified Kinesis Data Firehose delivery stream.
                        type: bool
                        default: False
                    delivery_stream:
                        description: The Kinesis Data Firehose delivery stream that is the destination for broker logs.
                        type: str
                        required: False
            s3:
                description: Details of the Amazon S3 destination for broker logs.
                type: dict
                suboptions:
                    enabled:
                        description: Specifies whether broker logs get sent to the specified Amazon S3 destination.
                        type: bool
                        default: False
                    bucket:
                        description: The name of the S3 bucket that is the destination for broker logs.
                        type: str
                        required: False
                    prefix:
                        description: The S3 prefix that is the destination for broker logs.
                        type: str
                        required: False
    wait:
        description: Whether to wait for the cluster to be available or deleted.
        type: bool
        default: false
    wait_timeout:
        description: How many seconds to wait. Cluster creation can take up to 20-30 minutes.
        type: int
        default: 3600
    tags:
        description: Tag dictionary to apply to the cluster.
        type: dict
    purge_tags:
        description: Remove tags not listed in I(tags) when tags is specified.
        default: true
        type: bool
extends_documentation_fragment:
    - amazon.aws.aws
    - amazon.aws.ec2
notes:
    - All operations are time consuming, for example create takes 20-30 minutes,
      update kafka version -- more than one hour, update configuration -- 10-15 minutes;
    - Cluster's brokers get evenly distributed over a number of availability zones
      that's equal to the number of subnets.
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- aws_msk_cluster:
    name: kafka-cluster
    state: present
    version: 2.6.1
    nodes: 6
    ebs_volume_size: "{{ aws_msk_options.ebs_volume_size }}"
    subnets:
      - subnet-e3b48ce7c25861eeb
      - subnet-2990c8b25b07ddd43
      - subnet-d9fbeaf46c54bfab6
    wait: true
    wait_timeout: 1800
    configuration_arn: arn:aws:kafka:us-east-1:000000000001:configuration/kafka-cluster-configuration/aaaaaaaa-bbbb-4444-3333-ccccccccc-1
    configuration_revision: 1

- aws_msk_cluster:
    name: kafka-cluster
    state: absent
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.

bootstrap_broker_string:
    description: A list of brokers that a client application can use to bootstrap.
    type: complex
    contains:
        plain:
            description: A string containing one or more hostname:port pairs.
            type: str
        tls:
            description: A string containing one or more DNS names (or IP) and TLS port pairs.
            type: str
    returned: I(state=present) and cluster state is I(ACTIVE)
cluster_info:
    description: Description of the MSK cluster.
    type: dict
    returned: I(state=present)
response:
    description: The response from actual API call.
    type: dict
    returned: always
    sample: {}
"""

import time

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (
    camel_dict_to_snake_dict,
    compare_aws_tags,
    AWSRetry,
)


@AWSRetry.jittered_backoff(retries=5, delay=5)
def list_clusters_with_backoff(client, cluster_name):
    paginator = client.get_paginator("list_clusters")
    return paginator.paginate(ClusterNameFilter=cluster_name).build_full_result()


@AWSRetry.jittered_backoff(retries=5, delay=5)
def list_nodes_with_backoff(client, cluster_arn):
    paginator = client.get_paginator("list_nodes")
    return paginator.paginate(ClusterArn=cluster_arn).build_full_result()


def find_cluster_by_name(client, module, cluster_name):
    try:
        cluster_list = list_clusters_with_backoff(client, cluster_name).get("ClusterInfoList", [])
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:
        module.fail_json_aws(e, "Failed to find kafka cluster by name")
    if cluster_list:
        if len(cluster_list) != 1:
            module.fail_json(msg="Found more than one cluster with name '{0}'".format(cluster_name))
        return cluster_list[0]
    return {}


def get_cluster_state(client, module, arn):
    try:
        response = client.describe_cluster(ClusterArn=arn, aws_retry=True)
    except client.exceptions.NotFoundException:
        return "DELETED"
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:
        module.fail_json_aws(e, "Failed to get kafka cluster state")
    return response["ClusterInfo"]["State"]


def get_cluster_version(client, module, arn):
    try:
        response = client.describe_cluster(ClusterArn=arn, aws_retry=True)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:
        module.fail_json_aws(e, "Failed to get kafka cluster version")
    return response["ClusterInfo"]["CurrentVersion"]


def wait_for_cluster_state(client, module, arn, state="ACTIVE"):
    # As of 2021-06 boto3 doesn't offer any built in waiters
    start = time.time()
    timeout = int(module.params.get("wait_timeout"))
    check_interval = 60
    while True:
        current_state = get_cluster_state(client, module, arn)
        if current_state == state:
            return
        if time.time() - start > timeout:
            module.fail_json(
                msg="Timeout waiting for cluster {0} (desired state is '{1}')".format(
                    current_state, state
                )
            )
        time.sleep(check_interval)


def prepare_create_options(module):
    """
    Return data structure for cluster create operation
    """

    c_params = {
        "ClusterName": module.params["name"],
        "KafkaVersion": module.params["version"],
        "ConfigurationInfo": {
            "Arn": module.params["configuration_arn"],
            "Revision": module.params["configuration_revision"],
        },
        "NumberOfBrokerNodes": module.params["nodes"],
        "BrokerNodeGroupInfo": {
            "ClientSubnets": module.params["subnets"],
            "InstanceType": module.params["instance_type"],
        }
    }

    if module.params["security_groups"] and len(module.params["security_groups"]) != 0:
        c_params["BrokerNodeGroupInfo"]["SecurityGroups"] = module.params.get("security_groups")

    if module.params["ebs_volume_size"]:
        c_params["BrokerNodeGroupInfo"]["StorageInfo"] = {
            "EbsStorageInfo": {
                "VolumeSize": module.params.get("ebs_volume_size")
            }
        }

    if module.params["encryption"]:
        c_params["EncryptionInfo"] = {}
        if module.params["encryption"].get("kms_key_id"):
            c_params["EncryptionInfo"]["EncryptionAtRest"] = {
                "DataVolumeKMSKeyId": module.params["encryption"]["kms_key_id"]
            }
        c_params["EncryptionInfo"]["EncryptionInTransit"] = {
            "ClientBroker": module.params["encryption"]["in_transit"].get("client_broker", "TLS"),
            "InCluster": module.params["encryption"]["in_transit"].get("in_cluster", True)
        }

    if module.params["authentication"]:
        c_params["ClientAuthentication"] = {}
        if module.params["authentication"].get("sasl_scram"):
            c_params["ClientAuthentication"]["Sasl"] = {
                "Scram": module.params["authentication"]["sasl_scram"]
            }
        if module.params["authentication"].get("tls_ca_arn"):
            c_params["ClientAuthentication"]["Tls"] = {
                "CertificateAuthorityArnList": module.params["authentication"]["tls_ca_arn"]
            }

    c_params.update(prepare_enhanced_monitoring_options(module))
    c_params.update(prepare_open_monitoring_options(module))
    c_params.update(prepare_logging_options(module))

    return c_params


def prepare_enhanced_monitoring_options(module):
    m_params = {}
    m_params["EnhancedMonitoring"] = module.params["enhanced_monitoring"] or "DEFAULT"
    return m_params


def prepare_open_monitoring_options(module):
    m_params = {}
    open_monitoring = module.params["open_monitoring"] or {}
    m_params["OpenMonitoring"] = {
        "Prometheus": {
            "JmxExporter": {
                "EnabledInBroker": open_monitoring.get("jmx_exporter", False)
            },
            "NodeExporter": {
                "EnabledInBroker": open_monitoring.get("node_exporter", False)
            }
        }
    }
    return m_params


def prepare_logging_options(module):
    l_params = {}
    logging = module.params["logging"] or {}
    if logging.get("cloudwatch"):
        l_params["CloudWatchLogs"] = {
            "Enabled": module.params["logging"]["cloudwatch"].get("enabled"),
            "LogGroup": module.params["logging"]["cloudwatch"].get("log_group")
        }
    else:
        l_params["CloudWatchLogs"] = {
            "Enabled": False
        }
    if logging.get("firehose"):
        l_params["Firehose"] = {
            "Enabled": module.params["logging"]["firehose"].get("enabled"),
            "DeliveryStream": module.params["logging"]["firehose"].get("delivery_stream")
        }
    else:
        l_params["Firehose"] = {
            "Enabled": False
        }
    if logging.get("s3"):
        l_params["S3"] = {
            "Enabled": module.params["logging"]["s3"].get("enabled"),
            "Bucket": module.params["logging"]["s3"].get("bucket"),
            "Prefix": module.params["logging"]["s3"].get("prefix")
        }
    else:
        l_params["S3"] = {
            "Enabled": False
        }
    return {
        "LoggingInfo": {
            "BrokerLogs": l_params
        }
    }


def create_or_update_cluster(client, module):
    """
    Create new or update existing cluster
    """

    changed = False
    response = {}

    cluster = find_cluster_by_name(client, module, module.params["name"])

    if not cluster:

        changed = True

        if module.check_mode:
            return True, {}

        create_params = prepare_create_options(module)

        try:
            response = client.create_cluster(aws_retry=True, **create_params)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(e, "Failed to create kafka cluster")

        if module.params.get("wait"):
            wait_for_cluster_state(client, module, arn=response["ClusterArn"], state="ACTIVE")

    else:

        response["ClusterArn"] = cluster["ClusterArn"]
        response["changes"] = {}

        # prepare available update methods definitions with current/target values and options
        msk_cluster_changes = {
            "broker_count": {
                "current_value": cluster["NumberOfBrokerNodes"],
                "target_value": module.params.get("nodes"),
                "update_params": {
                    "TargetNumberOfBrokerNodes": module.params.get("nodes")
                }
            },
            "broker_storage": {
                "current_value": cluster["BrokerNodeGroupInfo"]["StorageInfo"]["EbsStorageInfo"]["VolumeSize"],
                "target_value": module.params.get("ebs_volume_size"),
                "update_params": {
                    "TargetBrokerEBSVolumeInfo": [
                        {"KafkaBrokerNodeId": "All", "VolumeSizeGB": module.params.get("ebs_volume_size")}
                    ]
                }
            },
            "broker_type": {
                "botocore_version": "1.19.58",
                "current_value": cluster["BrokerNodeGroupInfo"]["InstanceType"],
                "target_value": module.params.get("instance_type"),
                "update_params": {
                    "TargetInstanceType": module.params.get("instance_type")
                }
            },
            "cluster_configuration": {
                "current_value": {
                    "arn": cluster["CurrentBrokerSoftwareInfo"]["ConfigurationArn"],
                    "revision": cluster["CurrentBrokerSoftwareInfo"]["ConfigurationRevision"],
                },
                "target_value": {
                    "arn": module.params.get("configuration_arn"),
                    "revision": module.params.get("configuration_revision"),
                },
                "update_params": {
                    "ConfigurationInfo": {
                        "Arn": module.params.get("configuration_arn"),
                        "Revision": module.params.get("configuration_revision")
                    }
                }
            },
            "cluster_kafka_version": {
                "current_value": cluster["CurrentBrokerSoftwareInfo"]["KafkaVersion"],
                "target_value": module.params.get("version"),
                "update_params": {
                    "TargetKafkaVersion": module.params.get("version")
                }
            },
            "enhanced_monitoring": {
                "current_value": cluster["EnhancedMonitoring"],
                "target_value": module.params.get("enhanced_monitoring"),
                "update_method": "update_monitoring",
                "update_params": prepare_enhanced_monitoring_options(module)
            },
            "open_monitoring": {
                "current_value": {
                    "OpenMonitoring": cluster["OpenMonitoring"]
                },
                "target_value": prepare_open_monitoring_options(module),
                "update_method": "update_monitoring",
                "update_params": prepare_open_monitoring_options(module)
            },
            "logging": {
                "current_value": {
                    "LoggingInfo": cluster["LoggingInfo"]
                },
                "target_value": prepare_logging_options(module),
                "update_method": "update_monitoring",
                "update_params": prepare_logging_options(module)
            }
        }

        for method, options in msk_cluster_changes.items():

            if 'botocore_version' in options:
                if not module.botocore_at_least(options["botocore_version"]):
                    continue

            try:
                update_method = getattr(client, options.get("update_method", "update_" + method))
            except AttributeError as e:
                module.fail_json_aws(e, "There is no update method 'update_{0}'".format(method))

            if options["current_value"] != options["target_value"]:
                changed = True
                if module.check_mode:
                    return True, {}

                # need to get cluster version and check for the state because
                # there can be several updates requested but only one in time can be performed
                version = get_cluster_version(client, module, cluster["ClusterArn"])
                state = get_cluster_state(client, module, cluster["ClusterArn"])
                if state != "ACTIVE":
                    if module.params["wait"]:
                        wait_for_cluster_state(client, module, arn=cluster["ClusterArn"], state="ACTIVE")
                    else:
                        module.fail_json(
                            msg="Cluster can be updated only in active state, current state is '{0}'. check cluster state or use wait option".format(
                                state
                            )
                        )
                try:
                    response["changes"][method] = update_method(
                        ClusterArn=cluster["ClusterArn"],
                        CurrentVersion=version,
                        **options["update_params"]
                    )
                except (
                    botocore.exceptions.BotoCoreError,
                    botocore.exceptions.ClientError,
                ) as e:
                    module.fail_json_aws(
                        e, "Failed to update cluster via 'update_{0}'".format(method)
                    )

                if module.params["wait"]:
                    wait_for_cluster_state(client, module, arn=cluster["ClusterArn"], state="ACTIVE")

    changed |= update_cluster_tags(client, module, response["ClusterArn"])

    return changed, response


def update_cluster_tags(client, module, arn):
    new_tags = module.params.get('tags')
    if new_tags is None:
        return False
    purge_tags = module.params.get('purge_tags')

    try:
        existing_tags = client.list_tags_for_resource(ResourceArn=arn, aws_retry=True)['Tags']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to retrieve tags for cluster '{0}'".format(arn))

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)

    if not module.check_mode:
        try:
            if tags_to_remove:
                client.untag_resource(ResourceArn=arn, TagKeys=tags_to_remove, aws_retry=True)
            if tags_to_add:
                client.tag_resource(ResourceArn=arn, Tags=tags_to_add, aws_retry=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to set tags for cluster '{0}'".format(arn))

    changed = bool(tags_to_add) or bool(tags_to_remove)
    return changed


def delete_cluster(client, module):

    cluster = find_cluster_by_name(client, module, module.params["name"])

    if module.check_mode:
        if cluster:
            return True, cluster
        else:
            return False, {}

    if not cluster:
        return False, {}

    try:
        response = client.delete_cluster(
            ClusterArn=cluster["ClusterArn"],
            CurrentVersion=cluster["CurrentVersion"],
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, "Failed to delete kafka cluster")

    if module.params["wait"]:
        wait_for_cluster_state(client, module, arn=cluster["ClusterArn"], state="DELETED")

    response["bootstrap_broker_string"] = {}

    return True, response


def main():

    module_args = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        version=dict(type="str"),
        configuration_arn=dict(type="str"),
        configuration_revision=dict(type="int"),
        nodes=dict(type="int", default=3),
        instance_type=dict(
            choices=[
                "kafka.t3.small",
                "kafka.m5.large",
                "kafka.m5.xlarge",
                "kafka.m5.2xlarge",
                "kafka.m5.4xlarge",
            ],
            default="kafka.t3.small",
        ),
        ebs_volume_size=dict(type="int", default=100),
        subnets=dict(type="list", elements="str"),
        security_groups=dict(type="list", elements="str", required=False),
        encryption=dict(
            type="dict",
            options=dict(
                kms_key_id=dict(type="str", required=False),
                in_transit=dict(
                    type="dict",
                    options=dict(
                        in_cluster=dict(type="bool", default=True),
                        client_broker=dict(
                            choices=["TLS", "TLS_PLAINTEXT", "PLAINTEXT"],
                            default="TLS"
                        ),
                    ),
                ),
            ),
        ),
        authentication=dict(
            type="dict",
            options=dict(
                tls_ca_arn=dict(type="list", elements="str", required=False),
                sasl_scram=dict(type="bool", default=False),
            ),
        ),
        enhanced_monitoring=dict(
            choices=[
                "DEFAULT",
                "PER_BROKER",
                "PER_TOPIC_PER_BROKER",
                "PER_TOPIC_PER_PARTITION",
            ],
            default="DEFAULT",
            required=False,
        ),
        open_monitoring=dict(
            type="dict",
            options=dict(
                jmx_exporter=dict(type="bool", default=False),
                node_exporter=dict(type="bool", default=False),
            ),
        ),
        logging=dict(
            type="dict",
            options=dict(
                cloudwatch=dict(
                    type="dict",
                    options=dict(
                        enabled=dict(type="bool", default=False),
                        log_group=dict(type="str", required=False),
                    ),
                ),
                firehose=dict(
                    type="dict",
                    options=dict(
                        enabled=dict(type="bool", default=False),
                        delivery_stream=dict(type="str", required=False),
                    ),
                ),
                s3=dict(
                    type="dict",
                    options=dict(
                        enabled=dict(type="bool", default=False),
                        bucket=dict(type="str", required=False),
                        prefix=dict(type="str", required=False),
                    ),
                ),
            ),
        ),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=3600),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        required_if=[['state', 'present', ['version', 'configuration_arn', 'configuration_revision', 'subnets']]],
        supports_check_mode=True
    )

    client = module.client("kafka", retry_decorator=AWSRetry.jittered_backoff())

    if module.params["state"] == "present":
        if len(module.params["subnets"]) < 2:
            module.fail_json(
                msg="At least two client subnets should be provided"
            )
        if int(module.params["nodes"]) % int(len(module.params["subnets"])) != 0:
            module.fail_json(
                msg="The number of broker nodes must be a multiple of availability zones in the subnets parameter"
            )
        if len(module.params["name"]) > 64:
            module.fail_json(
                module.fail_json(msg='Cluster name "{0}" exceeds 64 character limit'.format(module.params["name"]))
            )
        changed, response = create_or_update_cluster(client, module)
    elif module.params["state"] == "absent":
        changed, response = delete_cluster(client, module)

    cluster_info = {}
    bootstrap_broker_string = {}
    if response.get("ClusterArn") and module.params["state"] == "present":
        try:
            cluster_info = client.describe_cluster(ClusterArn=response["ClusterArn"], aws_retry=True)[
                "ClusterInfo"
            ]
            if cluster_info.get("State") == "ACTIVE":
                brokers = client.get_bootstrap_brokers(ClusterArn=response["ClusterArn"], aws_retry=True)
                if brokers.get("BootstrapBrokerString"):
                    bootstrap_broker_string["plain"] = brokers["BootstrapBrokerString"]
                if brokers.get("BootstrapBrokerStringTls"):
                    bootstrap_broker_string["tls"] = brokers["BootstrapBrokerStringTls"]
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(
                e,
                "Can not obtain information about cluster {0}".format(
                    response["ClusterArn"]
                ),
            )

    module.exit_json(
        changed=changed,
        bootstrap_broker_string=bootstrap_broker_string,
        cluster_info=camel_dict_to_snake_dict(cluster_info),
        response=camel_dict_to_snake_dict(response),
    )


if __name__ == "__main__":
    main()

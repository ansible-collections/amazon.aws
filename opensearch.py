#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: opensearch
short_description: Creates OpenSearch or ElasticSearch domain
description:
  - Creates or modify a Amazon OpenSearch Service domain.
version_added: 4.0.0
author: "Sebastien Rosset (@sebastien-rosset)"
options:
  state:
    description:
      - Creates or modifies an existing OpenSearch domain.
      - Deletes an OpenSearch domain.
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
  domain_name:
    description:
      - The name of the Amazon OpenSearch/ElasticSearch Service domain.
      - Domain names are unique across the domains owned by an account within an AWS region.
    required: true
    type: str
  engine_version:
    description:
      ->
        The engine version to use. For example, 'ElasticSearch_7.10' or 'OpenSearch_1.1'.
      ->
        If the currently running version is not equal to I(engine_version),
        a cluster upgrade is triggered.
      ->
        It may not be possible to upgrade directly from the currently running version
        to I(engine_version). In that case, the upgrade is performed incrementally by
        upgrading to the highest compatible version, then repeat the operation until
        the cluster is running at the target version.
      ->
        The upgrade operation fails if there is no path from current version to I(engine_version).
      ->
        See OpenSearch documentation for upgrade compatibility.
    required: false
    type: str
  allow_intermediate_upgrades:
    description:
      - >
        If true, allow OpenSearch domain to be upgraded through one or more intermediate versions.
      - >
        If false, do not allow OpenSearch domain to be upgraded through intermediate versions.
        The upgrade operation fails if it's not possible to ugrade to I(engine_version) directly.
    required: false
    type: bool
    default: true
  cluster_config:
    description:
      - Parameters for the cluster configuration of an OpenSearch Service domain.
    type: dict
    suboptions:
      instance_type:
        description:
          - Type of the instances to use for the domain.
        required: false
        type: str
      instance_count:
        description:
          - Number of instances for the domain.
        required: false
        type: int
      zone_awareness:
        description:
          - A boolean value to indicate whether zone awareness is enabled.
        required: false
        type: bool
      availability_zone_count:
        description:
          - >
            An integer value to indicate the number of availability zones for a domain when zone awareness is enabled.
            This should be equal to number of subnets if VPC endpoints is enabled.
        required: false
        type: int
      dedicated_master:
        description:
          - A boolean value to indicate whether a dedicated master node is enabled.
        required: false
        type: bool
      dedicated_master_instance_type:
        description:
          - The instance type for a dedicated master node.
        required: false
        type: str
      dedicated_master_instance_count:
        description:
          - Total number of dedicated master nodes, active and on standby, for the domain.
        required: false
        type: int
      warm_enabled:
        description:
          - True to enable UltraWarm storage.
        required: false
        type: bool
      warm_type:
        description:
          - The instance type for the OpenSearch domain's warm nodes.
        required: false
        type: str
      warm_count:
        description:
          - The number of UltraWarm nodes in the domain.
        required: false
        type: int
      cold_storage_options:
        description:
          - Specifies the ColdStorageOptions config for a Domain.
        type: dict
        suboptions:
          enabled:
            description:
              - True to enable cold storage. Supported on Elasticsearch 7.9 or above.
            required: false
            type: bool
  ebs_options:
    description:
      - Parameters to configure EBS-based storage for an OpenSearch Service domain.
    type: dict
    suboptions:
      ebs_enabled:
        description:
          - Specifies whether EBS-based storage is enabled.
        required: false
        type: bool
      volume_type:
        description:
          - Specifies the volume type for EBS-based storage. "standard"|"gp2"|"io1"
        required: false
        type: str
      volume_size:
        description:
          - Integer to specify the size of an EBS volume.
        required: false
        type: int
      iops:
        description:
          - The IOPD for a Provisioned IOPS EBS volume (SSD).
        required: false
        type: int
  vpc_options:
    description:
      - Options to specify the subnets and security groups for a VPC endpoint.
    type: dict
    suboptions:
      subnets:
        description:
          - Specifies the subnet ids for VPC endpoint.
        required: false
        type: list
        elements: str
      security_groups:
        description:
          - Specifies the security group ids for VPC endpoint.
        required: false
        type: list
        elements: str
  snapshot_options:
    description:
      - Option to set time, in UTC format, of the daily automated snapshot.
    type: dict
    suboptions:
      automated_snapshot_start_hour:
        description:
          - >
            Integer value from 0 to 23 specifying when the service takes a daily automated snapshot
            of the specified Elasticsearch domain.
        required: false
        type: int
  access_policies:
    description:
      - IAM access policy as a JSON-formatted string.
    required: false
    type: dict
  encryption_at_rest_options:
    description:
      - Parameters to enable encryption at rest.
    type: dict
    suboptions:
      enabled:
        description:
          - Should data be encrypted while at rest.
        required: false
        type: bool
      kms_key_id:
        description:
          - If encryption at rest enabled, this identifies the encryption key to use.
          - The value should be a KMS key ARN. It can also be the KMS key id.
        required: false
        type: str
  node_to_node_encryption_options:
    description:
      - Node-to-node encryption options.
    type: dict
    suboptions:
      enabled:
        description:
            - True to enable node-to-node encryption.
        required: false
        type: bool
  cognito_options:
    description:
      - Parameters to configure OpenSearch Service to use Amazon Cognito authentication for OpenSearch Dashboards.
    type: dict
    suboptions:
      enabled:
        description:
          - The option to enable Cognito for OpenSearch Dashboards authentication.
        required: false
        type: bool
      user_pool_id:
        description:
          - The Cognito user pool ID for OpenSearch Dashboards authentication.
        required: false
        type: str
      identity_pool_id:
        description:
          - The Cognito identity pool ID for OpenSearch Dashboards authentication.
        required: false
        type: str
      role_arn:
        description:
          - The role ARN that provides OpenSearch permissions for accessing Cognito resources.
        required: false
        type: str
  domain_endpoint_options:
    description:
      - Options to specify configuration that will be applied to the domain endpoint.
    type: dict
    suboptions:
      enforce_https:
        description:
          - Whether only HTTPS endpoint should be enabled for the domain.
        type: bool
      tls_security_policy:
        description:
          - Specify the TLS security policy to apply to the HTTPS endpoint of the domain.
        type: str
      custom_endpoint_enabled:
        description:
          - Whether to enable a custom endpoint for the domain.
        type: bool
      custom_endpoint:
        description:
          - The fully qualified domain for your custom endpoint.
        type: str
      custom_endpoint_certificate_arn:
        description:
          - The ACM certificate ARN for your custom endpoint.
        type: str
  advanced_security_options:
    description:
      - Specifies advanced security options.
    type: dict
    suboptions:
      enabled:
        description:
          - True if advanced security is enabled.
          - You must enable node-to-node encryption to use advanced security options.
        type: bool
      internal_user_database_enabled:
        description:
          - True if the internal user database is enabled.
        type: bool
      master_user_options:
        description:
          - Credentials for the master user, username and password, ARN, or both.
        type: dict
        suboptions:
          master_user_arn:
            description:
              - ARN for the master user (if IAM is enabled).
            type: str
          master_user_name:
            description:
              - The username of the master user, which is stored in the Amazon OpenSearch Service domain internal database.
            type: str
          master_user_password:
            description:
              - The password of the master user, which is stored in the Amazon OpenSearch Service domain internal database.
            type: str
      saml_options:
        description:
          - The SAML application configuration for the domain.
        type: dict
        suboptions:
          enabled:
            description:
              - True if SAML is enabled.
              - To use SAML authentication, you must enable fine-grained access control.
              - You can only enable SAML authentication for OpenSearch Dashboards on existing domains,
                not during the creation of new ones.
              - Domains only support one Dashboards authentication method at a time.
                If you have Amazon Cognito authentication for OpenSearch Dashboards enabled,
                you must disable it before you can enable SAML.
            type: bool
          idp:
            description:
              - The SAML Identity Provider's information.
            type: dict
            suboptions:
              metadata_content:
                description:
                  - The metadata of the SAML application in XML format.
                type: str
              entity_id:
                description:
                  - The unique entity ID of the application in SAML identity provider.
                type: str
          master_user_name:
            description:
              - The SAML master username, which is stored in the Amazon OpenSearch Service domain internal database.
            type: str
          master_backend_role:
            description:
              - The backend role that the SAML master user is mapped to.
            type: str
          subject_key:
            description:
              - Element of the SAML assertion to use for username. Default is NameID.
            type: str
          roles_key:
            description:
              - Element of the SAML assertion to use for backend roles. Default is roles.
            type: str
          session_timeout_minutes:
            description:
              - The duration, in minutes, after which a user session becomes inactive. Acceptable values are between 1 and 1440, and the default value is 60.
            type: int
  auto_tune_options:
    description:
      - Specifies Auto-Tune options.
    type: dict
    suboptions:
      desired_state:
        description:
          - The Auto-Tune desired state. Valid values are ENABLED and DISABLED.
        type: str
        choices: ['ENABLED', 'DISABLED']
      maintenance_schedules:
        description:
          - A list of maintenance schedules.
        type: list
        elements: dict
        suboptions:
          start_at:
            description:
              - The timestamp at which the Auto-Tune maintenance schedule starts.
            type: str
          duration:
            description:
              - Specifies maintenance schedule duration, duration value and duration unit.
            type: dict
            suboptions:
              value:
                description:
                  - Integer to specify the value of a maintenance schedule duration.
                type: int
              unit:
                description:
                  - The unit of a maintenance schedule duration. Valid value is HOURS.
                choices: ['HOURS']
                type: str
          cron_expression_for_recurrence:
            description:
              - A cron expression for a recurring maintenance schedule.
            type: str
  wait:
    description:
      - Whether or not to wait for completion of OpenSearch creation, modification or deletion.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds.
    default: 300
    type: int
requirements:
  - botocore >= 1.21.38
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags
"""

EXAMPLES = """

- name: Create OpenSearch domain for dev environment, no zone awareness, no dedicated masters
  community.aws.opensearch:
    domain_name: "dev-cluster"
    engine_version: Elasticsearch_1.1
    cluster_config:
      instance_type: "t2.small.search"
      instance_count: 2
      zone_awareness: false
      dedicated_master: false
    ebs_options:
      ebs_enabled: true
      volume_type: "gp2"
      volume_size: 10
    access_policies: "{{ lookup('file', 'policy.json') | from_json }}"

- name: Create OpenSearch domain with dedicated masters
  community.aws.opensearch:
    domain_name: "my-domain"
    engine_version: OpenSearch_1.1
    cluster_config:
      instance_type: "t2.small.search"
      instance_count: 12
      dedicated_master: true
      zone_awareness: true
      availability_zone_count: 2
      dedicated_master_instance_type: "t2.small.search"
      dedicated_master_instance_count: 3
      warm_enabled: true
      warm_type: "ultrawarm1.medium.search"
      warm_count: 1
      cold_storage_options:
        enabled: false
    ebs_options:
      ebs_enabled: true
      volume_type: "io1"
      volume_size: 10
      iops: 1000
    vpc_options:
      subnets:
        - "subnet-e537d64a"
        - "subnet-e537d64b"
      security_groups:
        - "sg-dd2f13cb"
        - "sg-dd2f13cc"
    snapshot_options:
      automated_snapshot_start_hour: 13
    access_policies: "{{ lookup('file', 'policy.json') | from_json }}"
    encryption_at_rest_options:
      enabled: false
    node_to_node_encryption_options:
      enabled: false
    auto_tune_options:
      enabled: true
      maintenance_schedules:
      - start_at: "2025-01-12"
        duration:
          value: 1
          unit: "HOURS"
        cron_expression_for_recurrence: "cron(0 12 * * ? *)"
      - start_at: "2032-01-12"
        duration:
          value: 2
          unit: "HOURS"
        cron_expression_for_recurrence: "cron(0 12 * * ? *)"
    tags:
      Environment: Development
      Application: Search
    wait: true

- name: Increase size of EBS volumes for existing cluster
  community.aws.opensearch:
    domain_name: "my-domain"
    ebs_options:
      volume_size: 5
    wait: true

- name: Increase instance count for existing cluster
  community.aws.opensearch:
    domain_name: "my-domain"
    cluster_config:
      instance_count: 40
    wait: true

"""

from copy import deepcopy
import datetime
import json

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.six import string_types

# import module snippets
from ansible_collections.amazon.aws.plugins.module_utils.core import (
    AnsibleAWSModule,
    is_boto3_error_code,
)
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (
    AWSRetry,
    boto3_tag_list_to_ansible_dict,
    compare_policies,
)
from ansible_collections.community.aws.plugins.module_utils.opensearch import (
    compare_domain_versions,
    ensure_tags,
    get_domain_status,
    get_domain_config,
    get_target_increment_version,
    normalize_opensearch,
    parse_version,
    wait_for_domain_status,
)


def ensure_domain_absent(client, module):
    domain_name = module.params.get("domain_name")
    changed = False

    domain = get_domain_status(client, module, domain_name)
    if module.check_mode:
        module.exit_json(
            changed=True, msg="Would have deleted domain if not in check mode"
        )
    try:
        client.delete_domain(DomainName=domain_name)
        changed = True
    except is_boto3_error_code("ResourceNotFoundException"):
        # The resource does not exist, or it has already been deleted
        return dict(changed=False)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="trying to delete domain")

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not domain or not module.params.get("wait"):
        return dict(changed=changed)
    try:
        wait_for_domain_status(client, module, domain_name, "domain_deleted")
        return dict(changed=changed)
    except is_boto3_error_code("ResourceNotFoundException"):
        return dict(changed=changed)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, "awaiting domain deletion")


def upgrade_domain(client, module, source_version, target_engine_version):
    domain_name = module.params.get("domain_name")
    # Determine if it's possible to upgrade directly from source version
    # to target version, or if it's necessary to upgrade through intermediate major versions.
    next_version = target_engine_version
    # When perform_check_only is true, indicates that an upgrade eligibility check needs
    # to be performed. Does not actually perform the upgrade.
    perform_check_only = False
    if module.check_mode:
        perform_check_only = True
    current_version = source_version
    while current_version != target_engine_version:
        v = get_target_increment_version(client, module, domain_name, target_engine_version)
        if v is None:
            # There is no compatible version, according to the get_compatible_versions() API.
            # The upgrade should fail, but try anyway.
            next_version = target_engine_version
        if next_version != target_engine_version:
            # It's not possible to upgrade directly to the target version.
            # Check the module parameters to determine if this is allowed or not.
            if not module.params.get("allow_intermediate_upgrades"):
                module.fail_json(msg="Cannot upgrade from {0} to version {1}. The highest compatible version is {2}".format(
                    source_version, target_engine_version, next_version))

        parameters = {
            "DomainName": domain_name,
            "TargetVersion": next_version,
            "PerformCheckOnly": perform_check_only,
        }

        if not module.check_mode:
            # If background tasks are in progress, wait until they complete.
            # This can take several hours depending on the cluster size and the type of background tasks
            # (maybe an upgrade is already in progress).
            # It's not possible to upgrade a domain that has background tasks are in progress,
            # the call to client.upgrade_domain would fail.
            wait_for_domain_status(client, module, domain_name, "domain_available")

        try:
            client.upgrade_domain(**parameters)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            # In check mode (=> PerformCheckOnly==True), a ValidationException may be
            # raised if it's not possible to upgrade to the target version.
            module.fail_json_aws(
                e,
                msg="Couldn't upgrade domain {0} from {1} to {2}".format(
                    domain_name, current_version, next_version
                ),
            )

        if module.check_mode:
            module.exit_json(
                changed=True,
                msg="Would have upgraded domain from {0} to {1} if not in check mode".format(
                    current_version, next_version
                ),
            )
        current_version = next_version

    if module.params.get("wait"):
        wait_for_domain_status(client, module, domain_name, "domain_available")


def set_cluster_config(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False

    cluster_config = desired_domain_config["ClusterConfig"]
    cluster_opts = module.params.get("cluster_config")
    if cluster_opts is not None:
        if cluster_opts.get("instance_type") is not None:
            cluster_config["InstanceType"] = cluster_opts.get("instance_type")
        if cluster_opts.get("instance_count") is not None:
            cluster_config["InstanceCount"] = cluster_opts.get("instance_count")
        if cluster_opts.get("zone_awareness") is not None:
            cluster_config["ZoneAwarenessEnabled"] = cluster_opts.get("zone_awareness")
        if cluster_config["ZoneAwarenessEnabled"]:
            if cluster_opts.get("availability_zone_count") is not None:
                cluster_config["ZoneAwarenessConfig"] = {
                    "AvailabilityZoneCount": cluster_opts.get(
                        "availability_zone_count"
                    ),
                }

        if cluster_opts.get("dedicated_master") is not None:
            cluster_config["DedicatedMasterEnabled"] = cluster_opts.get(
                "dedicated_master"
            )
        if cluster_config["DedicatedMasterEnabled"]:
            if cluster_opts.get("dedicated_master_instance_type") is not None:
                cluster_config["DedicatedMasterType"] = cluster_opts.get(
                    "dedicated_master_instance_type"
                )
            if cluster_opts.get("dedicated_master_instance_count") is not None:
                cluster_config["DedicatedMasterCount"] = cluster_opts.get(
                    "dedicated_master_instance_count"
                )

        if cluster_opts.get("warm_enabled") is not None:
            cluster_config["WarmEnabled"] = cluster_opts.get("warm_enabled")
        if cluster_config["WarmEnabled"]:
            if cluster_opts.get("warm_type") is not None:
                cluster_config["WarmType"] = cluster_opts.get("warm_type")
            if cluster_opts.get("warm_count") is not None:
                cluster_config["WarmCount"] = cluster_opts.get("warm_count")

    cold_storage_opts = None
    if cluster_opts is not None:
        cold_storage_opts = cluster_opts.get("cold_storage_options")
    if compare_domain_versions(desired_domain_config["EngineVersion"], "Elasticsearch_7.9") < 0:
        # If the engine version is ElasticSearch < 7.9, cold storage is not supported.
        # When querying a domain < 7.9, the AWS API indicates cold storage is disabled (Enabled: False),
        # which makes sense. However, trying to do HTTP POST with Enable: False causes an API error.
        # The 'ColdStorageOptions' attribute should not be present in HTTP POST.
        if cold_storage_opts is not None and cold_storage_opts.get("enabled"):
            module.fail_json(msg="Cold Storage is not supported")
        cluster_config.pop("ColdStorageOptions", None)
        if (
            current_domain_config is not None
            and "ClusterConfig" in current_domain_config
        ):
            # Remove 'ColdStorageOptions' from the current domain config, otherwise the actual vs desired diff
            # will indicate a change must be done.
            current_domain_config["ClusterConfig"].pop("ColdStorageOptions", None)
    else:
        # Elasticsearch 7.9 and above support ColdStorageOptions.
        if (
            cold_storage_opts is not None
            and cold_storage_opts.get("enabled") is not None
        ):
            cluster_config["ColdStorageOptions"] = {
                "Enabled": cold_storage_opts.get("enabled"),
            }

    if (
        current_domain_config is not None
        and current_domain_config["ClusterConfig"] != cluster_config
    ):
        change_set.append(
            "ClusterConfig changed from {0} to {1}".format(
                current_domain_config["ClusterConfig"], cluster_config
            )
        )
        changed = True
    return changed


def set_ebs_options(module, current_domain_config, desired_domain_config, change_set):
    changed = False
    ebs_config = desired_domain_config["EBSOptions"]
    ebs_opts = module.params.get("ebs_options")
    if ebs_opts is None:
        return changed
    if ebs_opts.get("ebs_enabled") is not None:
        ebs_config["EBSEnabled"] = ebs_opts.get("ebs_enabled")

    if not ebs_config["EBSEnabled"]:
        desired_domain_config["EBSOptions"] = {
            "EBSEnabled": False,
        }
    else:
        if ebs_opts.get("volume_type") is not None:
            ebs_config["VolumeType"] = ebs_opts.get("volume_type")
        if ebs_opts.get("volume_size") is not None:
            ebs_config["VolumeSize"] = ebs_opts.get("volume_size")
        if ebs_opts.get("iops") is not None:
            ebs_config["Iops"] = ebs_opts.get("iops")

    if (
        current_domain_config is not None
        and current_domain_config["EBSOptions"] != ebs_config
    ):
        change_set.append(
            "EBSOptions changed from {0} to {1}".format(
                current_domain_config["EBSOptions"], ebs_config
            )
        )
        changed = True
    return changed


def set_encryption_at_rest_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    encryption_at_rest_config = desired_domain_config["EncryptionAtRestOptions"]
    encryption_at_rest_opts = module.params.get("encryption_at_rest_options")
    if encryption_at_rest_opts is None:
        return False
    if encryption_at_rest_opts.get("enabled") is not None:
        encryption_at_rest_config["Enabled"] = encryption_at_rest_opts.get("enabled")
    if not encryption_at_rest_config["Enabled"]:
        desired_domain_config["EncryptionAtRestOptions"] = {
            "Enabled": False,
        }
    else:
        if encryption_at_rest_opts.get("kms_key_id") is not None:
            encryption_at_rest_config["KmsKeyId"] = encryption_at_rest_opts.get(
                "kms_key_id"
            )

    if (
        current_domain_config is not None
        and current_domain_config["EncryptionAtRestOptions"]
        != encryption_at_rest_config
    ):
        change_set.append(
            "EncryptionAtRestOptions changed from {0} to {1}".format(
                current_domain_config["EncryptionAtRestOptions"],
                encryption_at_rest_config,
            )
        )
        changed = True
    return changed


def set_node_to_node_encryption_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    node_to_node_encryption_config = desired_domain_config[
        "NodeToNodeEncryptionOptions"
    ]
    node_to_node_encryption_opts = module.params.get("node_to_node_encryption_options")
    if node_to_node_encryption_opts is None:
        return changed
    if node_to_node_encryption_opts.get("enabled") is not None:
        node_to_node_encryption_config["Enabled"] = node_to_node_encryption_opts.get(
            "enabled"
        )

    if (
        current_domain_config is not None
        and current_domain_config["NodeToNodeEncryptionOptions"]
        != node_to_node_encryption_config
    ):
        change_set.append(
            "NodeToNodeEncryptionOptions changed from {0} to {1}".format(
                current_domain_config["NodeToNodeEncryptionOptions"],
                node_to_node_encryption_config,
            )
        )
        changed = True
    return changed


def set_vpc_options(module, current_domain_config, desired_domain_config, change_set):
    changed = False
    vpc_config = None
    if "VPCOptions" in desired_domain_config:
        vpc_config = desired_domain_config["VPCOptions"]
    vpc_opts = module.params.get("vpc_options")
    if vpc_opts is None:
        return changed
    vpc_subnets = vpc_opts.get("subnets")
    if vpc_subnets is not None:
        if vpc_config is None:
            vpc_config = {}
            desired_domain_config["VPCOptions"] = vpc_config
        # OpenSearch cluster is attached to VPC
        if isinstance(vpc_subnets, string_types):
            vpc_subnets = [x.strip() for x in vpc_subnets.split(",")]
        vpc_config["SubnetIds"] = vpc_subnets

    vpc_security_groups = vpc_opts.get("security_groups")
    if vpc_security_groups is not None:
        if vpc_config is None:
            vpc_config = {}
            desired_domain_config["VPCOptions"] = vpc_config
        if isinstance(vpc_security_groups, string_types):
            vpc_security_groups = [x.strip() for x in vpc_security_groups.split(",")]
        vpc_config["SecurityGroupIds"] = vpc_security_groups

    if current_domain_config is not None:
        # Modify existing cluster.
        current_cluster_is_vpc = False
        desired_cluster_is_vpc = False
        if (
            "VPCOptions" in current_domain_config
            and "SubnetIds" in current_domain_config["VPCOptions"]
            and len(current_domain_config["VPCOptions"]["SubnetIds"]) > 0
        ):
            current_cluster_is_vpc = True
        if (
            "VPCOptions" in desired_domain_config
            and "SubnetIds" in desired_domain_config["VPCOptions"]
            and len(desired_domain_config["VPCOptions"]["SubnetIds"]) > 0
        ):
            desired_cluster_is_vpc = True
        if current_cluster_is_vpc != desired_cluster_is_vpc:
            # AWS does not allow changing the type. Don't fail here so we return the AWS API error.
            change_set.append("VPCOptions changed between Internet and VPC")
            changed = True
        elif desired_cluster_is_vpc is False:
            # There are no VPCOptions to configure.
            pass
        else:
            # Note the subnets may be the same but be listed in a different order.
            if set(current_domain_config["VPCOptions"]["SubnetIds"]) != set(
                vpc_config["SubnetIds"]
            ):
                change_set.append(
                    "SubnetIds changed from {0} to {1}".format(
                        current_domain_config["VPCOptions"]["SubnetIds"],
                        vpc_config["SubnetIds"],
                    )
                )
                changed = True
            if set(current_domain_config["VPCOptions"]["SecurityGroupIds"]) != set(
                vpc_config["SecurityGroupIds"]
            ):
                change_set.append(
                    "SecurityGroup changed from {0} to {1}".format(
                        current_domain_config["VPCOptions"]["SecurityGroupIds"],
                        vpc_config["SecurityGroupIds"],
                    )
                )
                changed = True
    return changed


def set_snapshot_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    snapshot_config = desired_domain_config["SnapshotOptions"]
    snapshot_opts = module.params.get("snapshot_options")
    if snapshot_opts is None:
        return changed
    if snapshot_opts.get("automated_snapshot_start_hour") is not None:
        snapshot_config["AutomatedSnapshotStartHour"] = snapshot_opts.get(
            "automated_snapshot_start_hour"
        )
    if (
        current_domain_config is not None
        and current_domain_config["SnapshotOptions"] != snapshot_config
    ):
        change_set.append("SnapshotOptions changed")
        changed = True
    return changed


def set_cognito_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    cognito_config = desired_domain_config["CognitoOptions"]
    cognito_opts = module.params.get("cognito_options")
    if cognito_opts is None:
        return changed
    if cognito_opts.get("enabled") is not None:
        cognito_config["Enabled"] = cognito_opts.get("enabled")
    if not cognito_config["Enabled"]:
        desired_domain_config["CognitoOptions"] = {
            "Enabled": False,
        }
    else:
        if cognito_opts.get("cognito_user_pool_id") is not None:
            cognito_config["UserPoolId"] = cognito_opts.get("cognito_user_pool_id")
        if cognito_opts.get("cognito_identity_pool_id") is not None:
            cognito_config["IdentityPoolId"] = cognito_opts.get(
                "cognito_identity_pool_id"
            )
        if cognito_opts.get("cognito_role_arn") is not None:
            cognito_config["RoleArn"] = cognito_opts.get("cognito_role_arn")

    if (
        current_domain_config is not None
        and current_domain_config["CognitoOptions"] != cognito_config
    ):
        change_set.append(
            "CognitoOptions changed from {0} to {1}".format(
                current_domain_config["CognitoOptions"], cognito_config
            )
        )
        changed = True
    return changed


def set_advanced_security_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    advanced_security_config = desired_domain_config["AdvancedSecurityOptions"]
    advanced_security_opts = module.params.get("advanced_security_options")
    if advanced_security_opts is None:
        return changed
    if advanced_security_opts.get("enabled") is not None:
        advanced_security_config["Enabled"] = advanced_security_opts.get("enabled")
    if not advanced_security_config["Enabled"]:
        desired_domain_config["AdvancedSecurityOptions"] = {
            "Enabled": False,
        }
    else:
        if advanced_security_opts.get("internal_user_database_enabled") is not None:
            advanced_security_config[
                "InternalUserDatabaseEnabled"
            ] = advanced_security_opts.get("internal_user_database_enabled")
        master_user_opts = advanced_security_opts.get("master_user_options")
        if master_user_opts is not None:
            if master_user_opts.get("master_user_arn") is not None:
                advanced_security_config["MasterUserOptions"][
                    "MasterUserARN"
                ] = master_user_opts.get("master_user_arn")
            if master_user_opts.get("master_user_name") is not None:
                advanced_security_config["MasterUserOptions"][
                    "MasterUserName"
                ] = master_user_opts.get("master_user_name")
            if master_user_opts.get("master_user_password") is not None:
                advanced_security_config["MasterUserOptions"][
                    "MasterUserPassword"
                ] = master_user_opts.get("master_user_password")
        saml_opts = advanced_security_opts.get("saml_options")
        if saml_opts is not None:
            if saml_opts.get("enabled") is not None:
                advanced_security_config["SamlOptions"]["Enabled"] = saml_opts.get(
                    "enabled"
                )
            idp_opts = saml_opts.get("idp")
            if idp_opts is not None:
                if idp_opts.get("metadata_content") is not None:
                    advanced_security_config["SamlOptions"]["Idp"][
                        "MetadataContent"
                    ] = idp_opts.get("metadata_content")
                if idp_opts.get("entity_id") is not None:
                    advanced_security_config["SamlOptions"]["Idp"][
                        "EntityId"
                    ] = idp_opts.get("entity_id")
            if saml_opts.get("master_user_name") is not None:
                advanced_security_config["SamlOptions"][
                    "MasterUserName"
                ] = saml_opts.get("master_user_name")
            if saml_opts.get("master_backend_role") is not None:
                advanced_security_config["SamlOptions"][
                    "MasterBackendRole"
                ] = saml_opts.get("master_backend_role")
            if saml_opts.get("subject_key") is not None:
                advanced_security_config["SamlOptions"]["SubjectKey"] = saml_opts.get(
                    "subject_key"
                )
            if saml_opts.get("roles_key") is not None:
                advanced_security_config["SamlOptions"]["RolesKey"] = saml_opts.get(
                    "roles_key"
                )
            if saml_opts.get("session_timeout_minutes") is not None:
                advanced_security_config["SamlOptions"][
                    "SessionTimeoutMinutes"
                ] = saml_opts.get("session_timeout_minutes")

    if (
        current_domain_config is not None
        and current_domain_config["AdvancedSecurityOptions"] != advanced_security_config
    ):
        change_set.append(
            "AdvancedSecurityOptions changed from {0} to {1}".format(
                current_domain_config["AdvancedSecurityOptions"],
                advanced_security_config,
            )
        )
        changed = True
    return changed


def set_domain_endpoint_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    domain_endpoint_config = desired_domain_config["DomainEndpointOptions"]
    domain_endpoint_opts = module.params.get("domain_endpoint_options")
    if domain_endpoint_opts is None:
        return changed
    if domain_endpoint_opts.get("enforce_https") is not None:
        domain_endpoint_config["EnforceHTTPS"] = domain_endpoint_opts.get(
            "enforce_https"
        )
    if domain_endpoint_opts.get("tls_security_policy") is not None:
        domain_endpoint_config["TLSSecurityPolicy"] = domain_endpoint_opts.get(
            "tls_security_policy"
        )
    if domain_endpoint_opts.get("custom_endpoint_enabled") is not None:
        domain_endpoint_config["CustomEndpointEnabled"] = domain_endpoint_opts.get(
            "custom_endpoint_enabled"
        )
    if domain_endpoint_config["CustomEndpointEnabled"]:
        if domain_endpoint_opts.get("custom_endpoint") is not None:
            domain_endpoint_config["CustomEndpoint"] = domain_endpoint_opts.get(
                "custom_endpoint"
            )
        if domain_endpoint_opts.get("custom_endpoint_certificate_arn") is not None:
            domain_endpoint_config[
                "CustomEndpointCertificateArn"
            ] = domain_endpoint_opts.get("custom_endpoint_certificate_arn")

    if (
        current_domain_config is not None
        and current_domain_config["DomainEndpointOptions"] != domain_endpoint_config
    ):
        change_set.append(
            "DomainEndpointOptions changed from {0} to {1}".format(
                current_domain_config["DomainEndpointOptions"], domain_endpoint_config
            )
        )
        changed = True
    return changed


def set_auto_tune_options(
    module, current_domain_config, desired_domain_config, change_set
):
    changed = False
    auto_tune_config = desired_domain_config["AutoTuneOptions"]
    auto_tune_opts = module.params.get("auto_tune_options")
    if auto_tune_opts is None:
        return changed
    schedules = auto_tune_opts.get("maintenance_schedules")
    if auto_tune_opts.get("desired_state") is not None:
        auto_tune_config["DesiredState"] = auto_tune_opts.get("desired_state")
    if auto_tune_config["DesiredState"] != "ENABLED":
        desired_domain_config["AutoTuneOptions"] = {
            "DesiredState": "DISABLED",
        }
    elif schedules is not None:
        auto_tune_config["MaintenanceSchedules"] = []
        for s in schedules:
            schedule_entry = {}
            start_at = s.get("start_at")
            if start_at is not None:
                if isinstance(start_at, datetime.datetime):
                    # The property was parsed from yaml to datetime, but the AWS API wants a string
                    start_at = start_at.strftime("%Y-%m-%d")
                schedule_entry["StartAt"] = start_at
            duration_opt = s.get("duration")
            if duration_opt is not None:
                schedule_entry["Duration"] = {}
                if duration_opt.get("value") is not None:
                    schedule_entry["Duration"]["Value"] = duration_opt.get("value")
                if duration_opt.get("unit") is not None:
                    schedule_entry["Duration"]["Unit"] = duration_opt.get("unit")
            if s.get("cron_expression_for_recurrence") is not None:
                schedule_entry["CronExpressionForRecurrence"] = s.get(
                    "cron_expression_for_recurrence"
                )
            auto_tune_config["MaintenanceSchedules"].append(schedule_entry)
    if current_domain_config is not None:
        if (
            current_domain_config["AutoTuneOptions"]["DesiredState"]
            != auto_tune_config["DesiredState"]
        ):
            change_set.append(
                "AutoTuneOptions.DesiredState changed from {0} to {1}".format(
                    current_domain_config["AutoTuneOptions"]["DesiredState"],
                    auto_tune_config["DesiredState"],
                )
            )
            changed = True
        if (
            auto_tune_config["MaintenanceSchedules"]
            != current_domain_config["AutoTuneOptions"]["MaintenanceSchedules"]
        ):
            change_set.append(
                "AutoTuneOptions.MaintenanceSchedules changed from {0} to {1}".format(
                    current_domain_config["AutoTuneOptions"]["MaintenanceSchedules"],
                    auto_tune_config["MaintenanceSchedules"],
                )
            )
            changed = True
    return changed


def set_access_policy(module, current_domain_config, desired_domain_config, change_set):
    access_policy_config = None
    changed = False
    access_policy_opt = module.params.get("access_policies")
    if access_policy_opt is None:
        return changed
    try:
        access_policy_config = json.dumps(access_policy_opt)
    except Exception as e:
        module.fail_json(
            msg="Failed to convert the policy into valid JSON: %s" % str(e)
        )
    if current_domain_config is not None:
        # Updating existing domain
        current_access_policy = json.loads(current_domain_config["AccessPolicies"])
        if not compare_policies(current_access_policy, access_policy_opt):
            change_set.append(
                "AccessPolicy changed from {0} to {1}".format(
                    current_access_policy, access_policy_opt
                )
            )
            changed = True
            desired_domain_config["AccessPolicies"] = access_policy_config
    else:
        # Creating new domain
        desired_domain_config["AccessPolicies"] = access_policy_config
    return changed


def ensure_domain_present(client, module):
    domain_name = module.params.get("domain_name")

    # Create default if OpenSearch does not exist. If domain already exists,
    # the data is populated by retrieving the current configuration from the API.
    desired_domain_config = {
        "DomainName": module.params.get("domain_name"),
        "EngineVersion": "OpenSearch_1.1",
        "ClusterConfig": {
            "InstanceType": "t2.small.search",
            "InstanceCount": 2,
            "ZoneAwarenessEnabled": False,
            "DedicatedMasterEnabled": False,
            "WarmEnabled": False,
        },
        # By default create ES attached to the Internet.
        # If the "VPCOptions" property is specified, even if empty, the API server interprets
        # as incomplete VPC configuration.
        # "VPCOptions": {},
        "EBSOptions": {
            "EBSEnabled": False,
        },
        "EncryptionAtRestOptions": {
            "Enabled": False,
        },
        "NodeToNodeEncryptionOptions": {
            "Enabled": False,
        },
        "SnapshotOptions": {
            "AutomatedSnapshotStartHour": 0,
        },
        "CognitoOptions": {
            "Enabled": False,
        },
        "AdvancedSecurityOptions": {
            "Enabled": False,
        },
        "DomainEndpointOptions": {
            "CustomEndpointEnabled": False,
        },
        "AutoTuneOptions": {
            "DesiredState": "DISABLED",
        },
    }
    # Determine if OpenSearch domain already exists.
    # current_domain_config may be None if the domain does not exist.
    (current_domain_config, domain_arn) = get_domain_config(client, module, domain_name)
    if current_domain_config is not None:
        desired_domain_config = deepcopy(current_domain_config)

    if module.params.get("engine_version") is not None:
        # Validate the engine_version
        v = parse_version(module.params.get("engine_version"))
        if v is None:
            module.fail_json(
                "Invalid engine_version. Must be Elasticsearch_X.Y or OpenSearch_X.Y"
            )
        desired_domain_config["EngineVersion"] = module.params.get("engine_version")

    changed = False
    change_set = []  # For check mode purpose

    changed |= set_cluster_config(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_ebs_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_encryption_at_rest_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_node_to_node_encryption_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_vpc_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_snapshot_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_cognito_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_advanced_security_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_domain_endpoint_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_auto_tune_options(
        module, current_domain_config, desired_domain_config, change_set
    )
    changed |= set_access_policy(
        module, current_domain_config, desired_domain_config, change_set
    )

    if current_domain_config is not None:
        if (
            desired_domain_config["EngineVersion"]
            != current_domain_config["EngineVersion"]
        ):
            changed = True
            change_set.append("EngineVersion changed")
            upgrade_domain(
                client,
                module,
                current_domain_config["EngineVersion"],
                desired_domain_config["EngineVersion"],
            )

        if changed:
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg=f"Would have updated domain if not in check mode: {change_set}",
                )
            # Remove the "EngineVersion" attribute, the AWS API does not accept this attribute.
            desired_domain_config.pop("EngineVersion", None)
            try:
                client.update_domain_config(**desired_domain_config)
            except (
                botocore.exceptions.BotoCoreError,
                botocore.exceptions.ClientError,
            ) as e:
                module.fail_json_aws(
                    e, msg="Couldn't update domain {0}".format(domain_name)
                )

    else:
        # Create new OpenSearch cluster
        if module.params.get("access_policies") is None:
            module.fail_json(
                "state is present but the following is missing: access_policies"
            )

        changed = True
        if module.check_mode:
            module.exit_json(
                changed=True, msg="Would have created a domain if not in check mode"
            )
        try:
            response = client.create_domain(**desired_domain_config)
            domain = response["DomainStatus"]
            domain_arn = domain["ARN"]
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(
                e, msg="Couldn't update domain {0}".format(domain_name)
            )

    try:
        existing_tags = boto3_tag_list_to_ansible_dict(
            client.list_tags(ARN=domain_arn, aws_retry=True)["TagList"]
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Couldn't get tags for domain %s" % domain_name)

    desired_tags = module.params["tags"]
    purge_tags = module.params["purge_tags"]
    changed |= ensure_tags(
        client, module, domain_arn, existing_tags, desired_tags, purge_tags
    )

    if module.params.get("wait") and not module.check_mode:
        wait_for_domain_status(client, module, domain_name, "domain_available")

    domain = get_domain_status(client, module, domain_name)

    return dict(changed=changed, **normalize_opensearch(client, module, domain))


def main():

    module = AnsibleAWSModule(
        argument_spec=dict(
            state=dict(choices=["present", "absent"], default="present"),
            domain_name=dict(required=True),
            engine_version=dict(),
            allow_intermediate_upgrades=dict(required=False, type="bool", default=True),
            access_policies=dict(required=False, type="dict"),
            cluster_config=dict(
                type="dict",
                default=None,
                options=dict(
                    instance_type=dict(),
                    instance_count=dict(required=False, type="int"),
                    zone_awareness=dict(required=False, type="bool"),
                    availability_zone_count=dict(required=False, type="int"),
                    dedicated_master=dict(required=False, type="bool"),
                    dedicated_master_instance_type=dict(),
                    dedicated_master_instance_count=dict(type="int"),
                    warm_enabled=dict(required=False, type="bool"),
                    warm_type=dict(required=False),
                    warm_count=dict(required=False, type="int"),
                    cold_storage_options=dict(
                        type="dict",
                        default=None,
                        options=dict(
                            enabled=dict(required=False, type="bool"),
                        ),
                    ),
                ),
            ),
            snapshot_options=dict(
                type="dict",
                default=None,
                options=dict(
                    automated_snapshot_start_hour=dict(required=False, type="int"),
                ),
            ),
            ebs_options=dict(
                type="dict",
                default=None,
                options=dict(
                    ebs_enabled=dict(required=False, type="bool"),
                    volume_type=dict(required=False),
                    volume_size=dict(required=False, type="int"),
                    iops=dict(required=False, type="int"),
                ),
            ),
            vpc_options=dict(
                type="dict",
                default=None,
                options=dict(
                    subnets=dict(type="list", elements="str", required=False),
                    security_groups=dict(type="list", elements="str", required=False),
                ),
            ),
            cognito_options=dict(
                type="dict",
                default=None,
                options=dict(
                    enabled=dict(required=False, type="bool"),
                    user_pool_id=dict(required=False),
                    identity_pool_id=dict(required=False),
                    role_arn=dict(required=False, no_log=False),
                ),
            ),
            encryption_at_rest_options=dict(
                type="dict",
                default=None,
                options=dict(
                    enabled=dict(type="bool"),
                    kms_key_id=dict(required=False),
                ),
            ),
            node_to_node_encryption_options=dict(
                type="dict",
                default=None,
                options=dict(
                    enabled=dict(type="bool"),
                ),
            ),
            domain_endpoint_options=dict(
                type="dict",
                default=None,
                options=dict(
                    enforce_https=dict(type="bool"),
                    tls_security_policy=dict(),
                    custom_endpoint_enabled=dict(type="bool"),
                    custom_endpoint=dict(),
                    custom_endpoint_certificate_arn=dict(),
                ),
            ),
            advanced_security_options=dict(
                type="dict",
                default=None,
                options=dict(
                    enabled=dict(type="bool"),
                    internal_user_database_enabled=dict(type="bool"),
                    master_user_options=dict(
                        type="dict",
                        default=None,
                        options=dict(
                            master_user_arn=dict(),
                            master_user_name=dict(),
                            master_user_password=dict(no_log=True),
                        ),
                    ),
                    saml_options=dict(
                        type="dict",
                        default=None,
                        options=dict(
                            enabled=dict(type="bool"),
                            idp=dict(
                                type="dict",
                                default=None,
                                options=dict(
                                    metadata_content=dict(),
                                    entity_id=dict(),
                                ),
                            ),
                            master_user_name=dict(),
                            master_backend_role=dict(),
                            subject_key=dict(no_log=False),
                            roles_key=dict(no_log=False),
                            session_timeout_minutes=dict(type="int"),
                        ),
                    ),
                ),
            ),
            auto_tune_options=dict(
                type="dict",
                default=None,
                options=dict(
                    desired_state=dict(choices=["ENABLED", "DISABLED"]),
                    maintenance_schedules=dict(
                        type="list",
                        elements="dict",
                        default=None,
                        options=dict(
                            start_at=dict(),
                            duration=dict(
                                type="dict",
                                default=None,
                                options=dict(
                                    value=dict(type="int"),
                                    unit=dict(choices=["HOURS"]),
                                ),
                            ),
                            cron_expression_for_recurrence=dict(),
                        ),
                    ),
                ),
            ),
            tags=dict(type="dict", aliases=["resource_tags"]),
            purge_tags=dict(type="bool", default=True),
            wait=dict(type="bool", default=False),
            wait_timeout=dict(type="int", default=300),
        ),
        supports_check_mode=True,
    )

    module.require_botocore_at_least("1.21.38")

    try:
        client = module.client("opensearch", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS opensearch service")

    if module.params["state"] == "absent":
        ret_dict = ensure_domain_absent(client, module)
    else:
        ret_dict = ensure_domain_present(client, module)

    module.exit_json(**ret_dict)


if __name__ == "__main__":
    main()

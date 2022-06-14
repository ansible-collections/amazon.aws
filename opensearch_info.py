#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: opensearch_info
short_description: obtain information about one or more OpenSearch or ElasticSearch domain
description:
  - Obtain information about one Amazon OpenSearch Service domain.
version_added: 4.0.0
author: "Sebastien Rosset (@sebastien-rosset)"
options:
  domain_name:
    description:
      - The name of the Amazon OpenSearch/ElasticSearch Service domain.
    required: false
    type: str
  tags:
    description:
      - >
        A dict of tags that are used to filter OpenSearch domains that match
        all tag key, value pairs.
    required: false
    type: dict
requirements:
  - botocore >= 1.21.38
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
"""

EXAMPLES = '''
- name: Get information about an OpenSearch domain instance
  community.aws.opensearch_info:
    domain-name: my-search-cluster
  register: new_cluster_info

- name: Get all OpenSearch instances
  community.aws.opensearch_info:

- name: Get all OpenSearch instances that have the specified Key, Value tags
  community.aws.opensearch_info:
    tags:
      Applications: search
      Environment: Development
'''

RETURN = '''
instances:
  description: List of OpenSearch domain instances
  returned: always
  type: complex
  contains:
    domain_status:
      description: The current status of the OpenSearch domain.
      returned: always
      type: complex
      contains:
        arn:
          description: The ARN of the OpenSearch domain.
          returned: always
          type: str
        domain_id:
          description: The unique identifier for the OpenSearch domain.
          returned: always
          type: str
        domain_name:
          description: The name of the OpenSearch domain.
          returned: always
          type: str
        created:
          description:
            - >
              The domain creation status. True if the creation of a domain is complete.
              False if domain creation is still in progress.
          returned: always
          type: bool
        deleted:
          description:
            - >
              The domain deletion status.
              True if a delete request has been received for the domain but resource cleanup is still in progress.
              False if the domain has not been deleted.
              Once domain deletion is complete, the status of the domain is no longer returned.
          returned: always
          type: bool
        endpoint:
          description: The domain endpoint that you use to submit index and search requests.
          returned: always
          type: str
        endpoints:
          description:
            - >
              Map containing the domain endpoints used to submit index and search requests.
            - >
              When you create a domain attached to a VPC domain, this propery contains
              the DNS endpoint to which service requests are submitted.
            - >
              If you query the opensearch_info immediately after creating the OpenSearch cluster,
              the VPC endpoint may not be returned. It may take several minutes until the
              endpoints is available.
          type: dict
        processing:
          description:
            - >
              The status of the domain configuration.
              True if Amazon OpenSearch Service is processing configuration changes.
              False if the configuration is active.
          returned: always
          type: bool
        upgrade_processing:
          description: true if a domain upgrade operation is in progress.
          returned: always
          type: bool
        engine_version:
          description: The version of the OpenSearch domain.
          returned: always
          type: str
          sample: OpenSearch_1.1
        cluster_config:
          description:
            - Parameters for the cluster configuration of an OpenSearch Service domain.
          type: complex
          contains:
            instance_type:
              description:
                - Type of the instances to use for the domain.
              type: str
            instance_count:
              description:
                - Number of instances for the domain.
              type: int
            zone_awareness:
              description:
                - A boolean value to indicate whether zone awareness is enabled.
              type: bool
            availability_zone_count:
              description:
                - >
                  An integer value to indicate the number of availability zones for a domain when zone awareness is enabled.
                  This should be equal to number of subnets if VPC endpoints is enabled.
              type: int
            dedicated_master_enabled:
              description:
                - A boolean value to indicate whether a dedicated master node is enabled.
              type: bool
            zone_awareness_enabled:
              description:
                - A boolean value to indicate whether zone awareness is enabled.
              type: bool
            zone_awareness_config:
              description:
                - The zone awareness configuration for a domain when zone awareness is enabled.
              type: complex
              contains:
                availability_zone_count:
                  description:
                    - An integer value to indicate the number of availability zones for a domain when zone awareness is enabled.
                  type: int
            dedicated_master_type:
              description:
                - The instance type for a dedicated master node.
              type: str
            dedicated_master_count:
              description:
                - Total number of dedicated master nodes, active and on standby, for the domain.
              type: int
            warm_enabled:
              description:
                - True to enable UltraWarm storage.
              type: bool
            warm_type:
              description:
                - The instance type for the OpenSearch domain's warm nodes.
              type: str
            warm_count:
              description:
                - The number of UltraWarm nodes in the domain.
              type: int
            cold_storage_options:
              description:
                - Specifies the ColdStorageOptions config for a Domain.
              type: complex
              contains:
                enabled:
                  description:
                    - True to enable cold storage. Supported on Elasticsearch 7.9 or above.
                  type: bool
        ebs_options:
          description:
            - Parameters to configure EBS-based storage for an OpenSearch Service domain.
          type: complex
          contains:
            ebs_enabled:
              description:
                - Specifies whether EBS-based storage is enabled.
              type: bool
            volume_type:
              description:
                - Specifies the volume type for EBS-based storage. "standard"|"gp2"|"io1"
              type: str
            volume_size:
              description:
                - Integer to specify the size of an EBS volume.
              type: int
            iops:
              description:
                - The IOPD for a Provisioned IOPS EBS volume (SSD).
              type: int
        vpc_options:
          description:
            - Options to specify the subnets and security groups for a VPC endpoint.
          type: complex
          contains:
            vpc_id:
              description: The VPC ID for the domain.
              type: str
            subnet_ids:
              description:
                - Specifies the subnet ids for VPC endpoint.
              type: list
              elements: str
            security_group_ids:
              description:
                - Specifies the security group ids for VPC endpoint.
              type: list
              elements: str
            availability_zones:
              description:
                - The Availability Zones for the domain..
              type: list
              elements: str
        snapshot_options:
          description:
            - Option to set time, in UTC format, of the daily automated snapshot.
          type: complex
          contains:
            automated_snapshot_start_hour:
              description:
                - >
                  Integer value from 0 to 23 specifying when the service takes a daily automated snapshot
                  of the specified Elasticsearch domain.
              type: int
        access_policies:
          description:
            - IAM access policy as a JSON-formatted string.
          type: complex
        encryption_at_rest_options:
          description:
            - Parameters to enable encryption at rest.
          type: complex
          contains:
            enabled:
              description:
                - Should data be encrypted while at rest.
              type: bool
            kms_key_id:
              description:
                - If encryption at rest enabled, this identifies the encryption key to use.
                - The value should be a KMS key ARN. It can also be the KMS key id.
              type: str
        node_to_node_encryption_options:
          description:
            - Node-to-node encryption options.
          type: complex
          contains:
            enabled:
              description:
                  - True to enable node-to-node encryption.
              type: bool
        cognito_options:
          description:
            - Parameters to configure OpenSearch Service to use Amazon Cognito authentication for OpenSearch Dashboards.
          type: complex
          contains:
            enabled:
              description:
                - The option to enable Cognito for OpenSearch Dashboards authentication.
              type: bool
            user_pool_id:
              description:
                - The Cognito user pool ID for OpenSearch Dashboards authentication.
              type: str
            identity_pool_id:
              description:
                - The Cognito identity pool ID for OpenSearch Dashboards authentication.
              type: str
            role_arn:
              description:
                - The role ARN that provides OpenSearch permissions for accessing Cognito resources.
              type: str
        domain_endpoint_options:
          description:
            - Options to specify configuration that will be applied to the domain endpoint.
          type: complex
          contains:
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
          type: complex
          contains:
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
              type: complex
              contains:
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
              type: complex
              contains:
                enabled:
                  description:
                    - True if SAML is enabled.
                  type: bool
                idp:
                  description:
                    - The SAML Identity Provider's information.
                  type: complex
                  contains:
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
                    - >
                      The duration, in minutes, after which a user session becomes inactive.
                      Acceptable values are between 1 and 1440, and the default value is 60.
                  type: int
        auto_tune_options:
          description:
            - Specifies Auto-Tune options.
          type: complex
          contains:
            desired_state:
              description:
                - The Auto-Tune desired state. Valid values are ENABLED and DISABLED.
              type: str
            maintenance_schedules:
              description:
                - A list of maintenance schedules.
              type: list
              elements: dict
              contains:
                start_at:
                  description:
                    - The timestamp at which the Auto-Tune maintenance schedule starts.
                  type: str
                duration:
                  description:
                    - Specifies maintenance schedule duration, duration value and duration unit.
                  type: complex
                  contains:
                    value:
                      description:
                        - Integer to specify the value of a maintenance schedule duration.
                      type: int
                    unit:
                      description:
                        - The unit of a maintenance schedule duration. Valid value is HOURS.
                      type: str
                cron_expression_for_recurrence:
                  description:
                    - A cron expression for a recurring maintenance schedule.
                  type: str
    domain_config:
      description: The OpenSearch domain configuration
      returned: always
      type: complex
      contains:
        domain_name:
          description: The name of the OpenSearch domain.
          returned: always
          type: str
'''


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (
    AWSRetry,
    boto3_tag_list_to_ansible_dict,
    camel_dict_to_snake_dict,
)
from ansible_collections.community.aws.plugins.module_utils.opensearch import (
    get_domain_config,
    get_domain_status,
)


def domain_info(client, module):
    domain_name = module.params.get('domain_name')
    filter_tags = module.params.get('tags')

    domain_list = []
    if domain_name:
        domain_status = get_domain_status(client, module, domain_name)
        if domain_status:
            domain_list.append({'DomainStatus': domain_status})
    else:
        domain_summary_list = client.list_domain_names()['DomainNames']
        for d in domain_summary_list:
            domain_status = get_domain_status(client, module, d['DomainName'])
            if domain_status:
                domain_list.append({'DomainStatus': domain_status})

    # Get the domain tags
    for domain in domain_list:
        current_domain_tags = None
        domain_arn = domain['DomainStatus']['ARN']
        try:
            current_domain_tags = client.list_tags(ARN=domain_arn, aws_retry=True)["TagList"]
            domain['Tags'] = boto3_tag_list_to_ansible_dict(current_domain_tags)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            # This could potentially happen if a domain is deleted between the time
            # its domain status was queried and the tags were queried.
            domain['Tags'] = {}

    # Filter by tags
    if filter_tags:
        for tag_key in filter_tags:
            try:
                domain_list = [c for c in domain_list if ('Tags' in c) and (tag_key in c['Tags']) and (c['Tags'][tag_key] == filter_tags[tag_key])]
            except (TypeError, AttributeError) as e:
                module.fail_json(msg="OpenSearch tag filtering error", exception=e)

    # Get the domain config
    for idx, domain in enumerate(domain_list):
        domain_name = domain['DomainStatus']['DomainName']
        (domain_config, arn) = get_domain_config(client, module, domain_name)
        if domain_config:
            domain['DomainConfig'] = domain_config
        domain_list[idx] = camel_dict_to_snake_dict(domain,
                                                    ignore_list=['AdvancedOptions', 'Endpoints', 'Tags'])

    return dict(changed=False, domains=domain_list)


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            domain_name=dict(required=False),
            tags=dict(type='dict', required=False),
        ),
        supports_check_mode=True,
    )
    module.require_botocore_at_least("1.21.38")

    try:
        client = module.client("opensearch", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS opensearch service")

    module.exit_json(**domain_info(client, module))


if __name__ == '__main__':
    main()

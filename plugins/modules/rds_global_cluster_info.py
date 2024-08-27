#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2023 Ansible Project
# Copyright (c) 2023 Gomathi Selvi Srinivasan (@GomathiselviS)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: rds_global_cluster_info
version_added: 7.0.0
short_description: Obtain information about Aurora global database clusters
description:
  - Obtain information about Aurora global database clusters.
options:
    global_cluster_identifier:
        description:
          - The user-supplied Global DB cluster identifier.
          - If this parameter is specified, information from only the specific DB cluster is returned.
          - This parameter is not case-sensitive.
          - If supplied, must match an existing DBClusterIdentifier.
        type: str

author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
notes:
  - While developing this module, describe_global_cluster CLI did not yield any tag information.
  - Consequently, the "tags" parameter is not included in this module.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Get info of all existing DB clusters
  amazon.aws.rds_global_cluster_info:
  register: _result_cluster_info

- name: Get info on a specific DB cluster
  amazon.aws.rds_global_cluster_info:
    global_cluster_identifier: "{{ cluster_id }}"
  register: _result_global_cluster_info
"""

RETURN = r"""
global_clusters:
  description: List of global clusters.
  returned: always
  type: list
  elements: dict
  contains:
    global_cluster_identifier:
        description: User-supplied global database cluster identifier.
        type: str
        sample: "ansible-test-global-cluster"
    global_cluster_resource_id:
        description:
        - The Amazon Web Services Region-unique, immutable identifier for the global database cluster.
        type: str
        returned: always
        sample: "cluster-123456789012"
    global_cluster_arn:
        description:
        - The Amazon Resource Name (ARN) for the global database cluster.
        type: str
        returned: always
        sample: "arn:aws:rds::123456789012:global-cluster:ansible-test-global-cluster"
    status:
        description: The status of the DB cluster.
        type: str
        returned: always
        sample: "available"
    engine:
        description: The database engine of the DB cluster.
        type: str
        returned: always
        sample: "aurora-postgresql"
    engine_version:
        description: The database engine version.
        type: str
        returned: always
        sample: "14.8"
    storage_encrypted:
        description: Whether the DB cluster is storage encrypted.
        type: bool
        returned: always
        sample: false
    deletion_protection:
        description:
        - Indicates if the DB cluster has deletion protection enabled.
          The database can't be deleted when deletion protection is enabled.
        type: bool
        returned: always
        sample: false
    gloabl_cluster_members:
        description:
        - The list of primary and secondary clusters within the global database
          cluster.
        type: list
        elements: dict
        contains:
            db_cluster_arn:
                description: The Amazon Resource Name (ARN) for each Aurora DB cluster in the global cluster.
                type: str
                returned: always
                sample: "arn:aws:rds:us-east-1:123456789012:cluster:ansible-test-primary"
            readers:
                description: The Amazon Resource Name (ARN) for each read-only secondary cluster associated with the global cluster.
                type: list
                elements: str
                returned: always
                sample: "arn:aws:rds:us-east-2:123456789012:cluster:ansible-test-secondary"
            is_writer:
                description:
                - Indicates whether the Aurora DB cluster is the primary cluster for the global cluster with which it is associated.
                returned: always
                type: bool
                sample: false
            global_write_forwarding_status:
                description: The status of write forwarding for a secondary cluster in the global cluster.
                type: str
                returned: always
                sample: disabled
    failover_state:
        description:
        - A data object containing all properties for the current state of an in-process or
          pending switchover or failover process for this global cluster (Aurora global database).
        - This object is empty unless the SwitchoverGlobalCluster or FailoverGlobalCluster operation was called on this global cluster.
        type: dict
        contains:
            status:
                description:
                - The current status of the global cluster.
                type: str
                returned: always
                sample: "pending"
            from_db_cluster_arn:
                description: The Amazon Resource Name (ARN) of the Aurora DB cluster that is currently being demoted, and which is associated with this state.
                type: str
                returned: always
                sample: "arn:aws:rds:us-east-1:123456789012:cluster:ansible-test-primary"
            to_db_cluster_arn:
                description: The Amazon Resource Name (ARN) of the Aurora DB cluster that is currently being promoted, and which is associated with this state.
                type: str
                returned: always
                sample: "arn:aws:rds:us-east-2:123456789012:cluster:ansible-test-secondary"
            is_data_loss_allowed:
                description:
                - Indicates whether the operation is a global switchover or a global failover.
                - If data loss is allowed, then the operation is a global failover. Otherwise, it is a switchover.
                type: bool
                returned: always
                sample: false
"""


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.jittered_backoff(retries=10)
def _describe_global_clusters(client, **params):
    try:
        paginator = client.get_paginator("describe_global_clusters")
        return paginator.paginate(**params).build_full_result()["GlobalClusters"]
    except is_boto3_error_code("GlobalClusterNotFoundFault"):
        return []


def cluster_info(client, module):
    global_cluster_id = module.params.get("global_cluster_identifier")

    params = dict()
    if global_cluster_id:
        params["GlobalClusterIdentifier"] = global_cluster_id

    try:
        result = _describe_global_clusters(client, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Couldn't get Global cluster information.")

    return dict(
        changed=False, global_clusters=[camel_dict_to_snake_dict(cluster, ignore_list=["Tags"]) for cluster in result]
    )


def main():
    argument_spec = dict(
        global_cluster_identifier=dict(),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff(retries=10))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    module.exit_json(**cluster_info(client, module))


if __name__ == "__main__":
    main()

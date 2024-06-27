#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017, 2018 Michael De La Rue
# Copyright (c) 2017, 2018 Will Thames
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_instance_info
version_added: 5.0.0
short_description: obtain information about one or more RDS instances
description:
  - Obtain information about one or more RDS instances.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  db_instance_identifier:
    description:
      - The RDS instance's unique identifier.
    required: false
    aliases:
      - id
    type: str
  filters:
    description:
      - A filter that specifies one or more DB instances to describe.
        See U(https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeDBInstances.html)
    type: dict
author:
  - "Will Thames (@willthames)"
  - "Michael De La Rue (@mikedlr)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Get information about an instance
  amazon.aws.rds_instance_info:
    db_instance_identifier: new-database
  register: new_database_info

- name: Get all RDS instances
  amazon.aws.rds_instance_info:
"""

RETURN = r"""
instances:
  description: List of RDS instances
  returned: always
  type: complex
  contains:
    allocated_storage:
      description: Gigabytes of storage allocated to the database.
      returned: always
      type: int
      sample: 10
    auto_minor_version_upgrade:
      description: Whether minor version upgrades happen automatically.
      returned: always
      type: bool
      sample: true
    availability_zone:
      description: Availability Zone in which the database resides.
      returned: always
      type: str
      sample: us-west-2b
    backup_retention_period:
      description: Days for which backups are retained.
      returned: always
      type: int
      sample: 7
    ca_certificate_identifier:
      description: ID for the CA certificate.
      returned: always
      type: str
      sample: rds-ca-2015
    copy_tags_to_snapshot:
      description: Whether DB tags should be copied to the snapshot.
      returned: always
      type: bool
      sample: false
    db_instance_arn:
      description: ARN of the database instance.
      returned: always
      type: str
      sample: arn:aws:rds:us-west-2:123456789012:db:helloworld-rds
    db_instance_class:
      description: Instance class of the database instance.
      returned: always
      type: str
      sample: db.t3.small
    db_instance_identifier:
      description: Database instance identifier.
      returned: always
      type: str
      sample: helloworld-rds
    db_instance_port:
      description: Port used by the database instance.
      returned: always
      type: int
      sample: 0
    db_instance_status:
      description: Status of the database instance.
      returned: always
      type: str
      sample: available
    db_name:
      description: Name of the database.
      returned: always
      type: str
      sample: management
    db_parameter_groups:
      description: List of database parameter groups.
      returned: always
      type: complex
      contains:
        db_parameter_group_name:
          description: Name of the database parameter group.
          returned: always
          type: str
          sample: psql-pg-helloworld
        parameter_apply_status:
          description: Whether the parameter group has been applied.
          returned: always
          type: str
          sample: in-sync
    db_security_groups:
      description: List of security groups used by the database instance.
      returned: always
      type: list
      sample: []
    db_subnet_group:
      description: List of subnet groups.
      returned: always
      type: complex
      contains:
        db_subnet_group_description:
          description: Description of the DB subnet group.
          returned: always
          type: str
          sample: My database subnet group
        db_subnet_group_name:
          description: Name of the database subnet group.
          returned: always
          type: str
          sample: my-subnet-group
        subnet_group_status:
          description: Subnet group status.
          returned: always
          type: str
          sample: Complete
        subnets:
          description: List of subnets in the subnet group.
          returned: always
          type: complex
          contains:
            subnet_availability_zone:
              description: Availability zone of the subnet.
              returned: always
              type: complex
              contains:
                name:
                  description: Name of the availability zone.
                  returned: always
                  type: str
                  sample: us-west-2c
            subnet_identifier:
              description: Subnet ID.
              returned: always
              type: str
              sample: subnet-abcd1234
            subnet_status:
              description: Subnet status.
              returned: always
              type: str
              sample: Active
        vpc_id:
          description: VPC id of the subnet group.
          returned: always
          type: str
          sample: vpc-abcd1234
    dbi_resource_id:
      description: AWS Region-unique, immutable identifier for the DB instance.
      returned: always
      type: str
      sample: db-AAAAAAAAAAAAAAAAAAAAAAAAAA
    deletion_protection:
      description: C(True) if the DB instance has deletion protection enabled, C(False) if not.
      returned: always
      type: bool
      sample: False
      version_added: 3.3.0
      version_added_collection: community.aws
    domain_memberships:
      description: List of domain memberships.
      returned: always
      type: list
      sample: []
    endpoint:
      description: Database endpoint
      returned: always
      type: complex
      contains:
        address:
          description: Database endpoint address.
          returned: always
          type: str
          sample: helloworld-rds.ctrqpe3so1sf.us-west-2.rds.amazonaws.com
        hosted_zone_id:
          description: Route 53 hosted zone ID.
          returned: always
          type: str
          sample: Z1PABCD0000000
        port:
          description: Database endpoint port.
          returned: always
          type: int
          sample: 5432
    engine:
      description: Database engine.
      returned: always
      type: str
      sample: postgres
    engine_version:
      description: Database engine version.
      returned: always
      type: str
      sample: 9.5.10
    iam_database_authentication_enabled:
      description: Whether database authentication through IAM is enabled.
      returned: always
      type: bool
      sample: false
    instance_create_time:
      description: Date and time the instance was created.
      returned: always
      type: str
      sample: '2017-10-10T04:00:07.434000+00:00'
    iops:
      description: The Provisioned IOPS value for the DB instance.
      returned: always
      type: int
      sample: 1000
    kms_key_id:
      description: KMS Key ID.
      returned: always
      type: str
      sample: arn:aws:kms:us-west-2:123456789012:key/abcd1234-0000-abcd-1111-0123456789ab
    latest_restorable_time:
      description: Latest time to which a database can be restored with point-in-time restore.
      returned: always
      type: str
      sample: '2018-05-17T00:03:56+00:00'
    license_model:
      description: License model.
      returned: always
      type: str
      sample: postgresql-license
    master_username:
      description: Database master username.
      returned: always
      type: str
      sample: dbadmin
    monitoring_interval:
      description: Interval, in seconds, between points when Enhanced Monitoring metrics are collected for the DB instance.
      returned: always
      type: int
      sample: 0
    multi_az:
      description: Whether Multi-AZ is on.
      returned: always
      type: bool
      sample: false
    option_group_memberships:
      description: List of option groups.
      returned: always
      type: complex
      contains:
        option_group_name:
          description: Option group name.
          returned: always
          type: str
          sample: default:postgres-9-5
        status:
          description: Status of option group.
          returned: always
          type: str
          sample: in-sync
    pending_modified_values:
      description: Modified values pending application.
      returned: always
      type: complex
      contains: {}
    performance_insights_enabled:
      description: Whether performance insights are enabled.
      returned: always
      type: bool
      sample: false
    preferred_backup_window:
      description: Preferred backup window.
      returned: always
      type: str
      sample: 04:00-05:00
    preferred_maintenance_window:
      description: Preferred maintenance window.
      returned: always
      type: str
      sample: mon:05:00-mon:05:30
    publicly_accessible:
      description: Whether the DB is publicly accessible.
      returned: always
      type: bool
      sample: false
    read_replica_db_instance_identifiers:
      description: List of database instance read replicas.
      returned: always
      type: list
      sample: []
    storage_encrypted:
      description: Whether the storage is encrypted.
      returned: always
      type: bool
      sample: true
    storage_type:
      description: Storage type of the Database instance.
      returned: always
      type: str
      sample: gp2
    tags:
      description: Tags used by the database instance.
      returned: always
      type: complex
      contains: {}
    vpc_security_groups:
      description: List of VPC security groups.
      returned: always
      type: complex
      contains:
        status:
          description: Status of the VPC security group.
          returned: always
          type: str
          sample: active
        vpc_security_group_id:
          description: VPC Security Group ID.
          returned: always
          type: str
          sample: sg-abcd1234
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_instances
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def instance_info(
    client, module: AnsibleAWSModule, instance_name: Optional[str], filters: Optional[Dict[str, Union[str, List]]]
) -> List[Dict[str, Any]]:
    """
    Returns attributes of db instance(s), with instances optionally filtered by provided name and additional filters.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            instance_name (str, optional): Unique identifier of db instance to describe
            filters (dict, optional): Additional boto3-supported filters specifying db instance(s) to describe

        Returns:
            instances (list): List of instance attribute dicts converted from CamelCase to snake_case format
    """
    params = {}
    if instance_name:
        params["DBInstanceIdentifier"] = instance_name
    if filters:
        params["Filters"] = ansible_dict_to_boto3_filter_list(filters)

    results = describe_db_instances(client, **params)
    for instance in results:
        instance["Tags"] = boto3_tag_list_to_ansible_dict(instance.pop("TagList"))

    return [camel_dict_to_snake_dict(instance, ignore_list=["Tags"]) for instance in results]


def main():
    argument_spec = dict(
        db_instance_identifier=dict(aliases=["id"]),
        filters=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = module.client("rds")

    instance_name = module.params.get("db_instance_identifier")
    filters = module.params.get("filters")

    try:
        module.exit_json(changed=False, instances=instance_info(client, module, instance_name, filters))
    except AnsibleRDSError as e:
        module.fail_json_aws(e)


if __name__ == "__main__":
    main()

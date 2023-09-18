#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Jens Carl, Hothead Games Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
author:
  - "Jens Carl (@j-carl), Hothead Games Inc."
  - "Rafael Driutti (@rafaeldriutti)"
module: redshift
version_added: 1.0.0
short_description: create, delete, or modify an Amazon Redshift instance
description:
  - Creates, deletes, or modifies Amazon Redshift cluster instances.
options:
  command:
    description:
      - Specifies the action to take.
    required: true
    choices: [ 'create', 'facts', 'delete', 'modify' ]
    type: str
  identifier:
    description:
      - Redshift cluster identifier.
    required: true
    type: str
  node_type:
    description:
      - The node type of the cluster.
      - Require when I(command=create).
    choices: ['ds1.xlarge', 'ds1.8xlarge', 'ds2.xlarge', 'ds2.8xlarge', 'dc1.large','dc2.large',
              'dc1.8xlarge', 'dw1.xlarge', 'dw1.8xlarge', 'dw2.large', 'dw2.8xlarge']
    type: str
  username:
    description:
      - Master database username.
      - Used only when I(command=create).
    type: str
  password:
    description:
      - Master database password.
      - Used only when I(command=create).
    type: str
  cluster_type:
    description:
      - The type of cluster.
    choices: ['multi-node', 'single-node' ]
    default: 'single-node'
    type: str
  db_name:
    description:
      - Name of the database.
    type: str
  availability_zone:
    description:
      - Availability zone in which to launch cluster.
    aliases: ['zone', 'aws_zone']
    type: str
  number_of_nodes:
    description:
      - Number of nodes.
      - Only used when I(cluster_type=multi-node).
    type: int
  cluster_subnet_group_name:
    description:
      - Which subnet to place the cluster.
    aliases: ['subnet']
    type: str
  cluster_security_groups:
    description:
      - In which security group the cluster belongs.
    type: list
    elements: str
    aliases: ['security_groups']
  vpc_security_group_ids:
    description:
      - VPC security group
    aliases: ['vpc_security_groups']
    type: list
    elements: str
  skip_final_cluster_snapshot:
    description:
      - Skip a final snapshot before deleting the cluster.
      - Used only when I(command=delete).
    aliases: ['skip_final_snapshot']
    default: false
    type: bool
  final_cluster_snapshot_identifier:
    description:
      - Identifier of the final snapshot to be created before deleting the cluster.
      - If this parameter is provided, I(skip_final_cluster_snapshot) must be C(false).
      - Used only when I(command=delete).
    aliases: ['final_snapshot_id']
    type: str
  preferred_maintenance_window:
    description:
      - 'Maintenance window in format of C(ddd:hh24:mi-ddd:hh24:mi).  (Example: C(Mon:22:00-Mon:23:15))'
      - Times are specified in UTC.
      - If not specified then a random 30 minute maintenance window is assigned.
    aliases: ['maintance_window', 'maint_window']
    type: str
  cluster_parameter_group_name:
    description:
      - Name of the cluster parameter group.
    aliases: ['param_group_name']
    type: str
  automated_snapshot_retention_period:
    description:
      - The number of days that automated snapshots are retained.
    aliases: ['retention_period']
    type: int
  port:
    description:
      - Which port the cluster is listening on.
    type: int
  cluster_version:
    description:
      - Which version the cluster should have.
    aliases: ['version']
    choices: ['1.0']
    type: str
  allow_version_upgrade:
    description:
      - When I(allow_version_upgrade=true) the cluster may be automatically
        upgraded during the maintenance window.
    aliases: ['version_upgrade']
    default: true
    type: bool
  publicly_accessible:
    description:
      - If the cluster is accessible publicly or not.
    default: false
    type: bool
  encrypted:
    description:
      - If the cluster is encrypted or not.
    default: false
    type: bool
  elastic_ip:
    description:
      - An Elastic IP to use for the cluster.
    type: str
  new_cluster_identifier:
    description:
      - Only used when command=modify.
    aliases: ['new_identifier']
    type: str
  wait:
    description:
      - When I(command=create), I(command=modify) or I(command=restore) then wait for the database to enter the 'available' state.
      - When I(command=delete) wait for the database to be terminated.
    type: bool
    default: false
  wait_timeout:
    description:
      - When I(wait=true) defines how long in seconds before giving up.
    default: 300
    type: int
  enhanced_vpc_routing:
    description:
      - Whether the cluster should have enhanced VPC routing enabled.
    default: false
    type: bool
notes:
  - Support for I(tags) and I(purge_tags) was added in release 1.3.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Basic cluster provisioning example
  community.aws.redshift:
    command: create
    node_type: ds1.xlarge
    identifier: new_cluster
    username: cluster_admin
    password: 1nsecure

- name: Cluster delete example
  community.aws.redshift:
    command: delete
    identifier: new_cluster
    skip_final_cluster_snapshot: true
    wait: true
"""

RETURN = r"""
cluster:
    description: dictionary containing all the cluster information
    returned: success
    type: complex
    contains:
        identifier:
            description: Id of the cluster.
            returned: success
            type: str
            sample: "new_redshift_cluster"
        create_time:
            description: Time of the cluster creation as timestamp.
            returned: success
            type: float
            sample: 1430158536.308
        status:
            description: Status of the cluster.
            returned: success
            type: str
            sample: "available"
        db_name:
            description: Name of the database.
            returned: success
            type: str
            sample: "new_db_name"
        availability_zone:
            description: Amazon availability zone where the cluster is located. "None" until cluster is available.
            returned: success
            type: str
            sample: "us-east-1b"
        maintenance_window:
            description: Time frame when maintenance/upgrade are done.
            returned: success
            type: str
            sample: "sun:09:30-sun:10:00"
        private_ip_address:
            description: Private IP address of the main node.
            returned: success
            type: str
            sample: "10.10.10.10"
        public_ip_address:
            description: Public IP address of the main node. "None" when enhanced_vpc_routing is enabled.
            returned: success
            type: str
            sample: "0.0.0.0"
        port:
            description: Port of the cluster. "None" until cluster is available.
            returned: success
            type: int
            sample: 5439
        url:
            description: FQDN of the main cluster node. "None" until cluster is available.
            returned: success
            type: str
            sample: "new-redshift_cluster.jfkdjfdkj.us-east-1.redshift.amazonaws.com"
        enhanced_vpc_routing:
            description: status of the enhanced vpc routing feature.
            returned: success
            type: bool
        tags:
            description: aws tags for cluster.
            returned: success
            type: dict
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_aws_account_info
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def _ensure_tags(redshift, identifier, existing_tags, module):
    """Compares and update resource tags"""

    account_id, partition = get_aws_account_info(module)
    region = module.region
    resource_arn = f"arn:{partition}:redshift:{region}:{account_id}:cluster:{identifier}"
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")

    tags_to_add, tags_to_remove = compare_aws_tags(boto3_tag_list_to_ansible_dict(existing_tags), tags, purge_tags)

    if tags_to_add:
        try:
            redshift.create_tags(ResourceName=resource_arn, Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to add tags to cluster")

    if tags_to_remove:
        try:
            redshift.delete_tags(ResourceName=resource_arn, TagKeys=tags_to_remove)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to delete tags on cluster")

    changed = bool(tags_to_add or tags_to_remove)
    return changed


def _collect_facts(resource):
    """Transform cluster information to dict."""
    facts = {
        "identifier": resource["ClusterIdentifier"],
        "status": resource["ClusterStatus"],
        "username": resource["MasterUsername"],
        "db_name": resource["DBName"],
        "maintenance_window": resource["PreferredMaintenanceWindow"],
        "enhanced_vpc_routing": resource["EnhancedVpcRouting"],
    }

    for node in resource["ClusterNodes"]:
        if node["NodeRole"] in ("SHARED", "LEADER"):
            facts["private_ip_address"] = node["PrivateIPAddress"]
            if facts["enhanced_vpc_routing"] is False:
                facts["public_ip_address"] = node["PublicIPAddress"]
            else:
                facts["public_ip_address"] = None
            break

    # Some parameters are not ready instantly if you don't wait for available
    # cluster status
    facts["create_time"] = None
    facts["url"] = None
    facts["port"] = None
    facts["availability_zone"] = None
    facts["tags"] = {}

    if resource["ClusterStatus"] != "creating":
        facts["create_time"] = resource["ClusterCreateTime"]
        facts["url"] = resource["Endpoint"]["Address"]
        facts["port"] = resource["Endpoint"]["Port"]
        facts["availability_zone"] = resource["AvailabilityZone"]
        facts["tags"] = boto3_tag_list_to_ansible_dict(resource["Tags"])

    return facts


@AWSRetry.jittered_backoff()
def _describe_cluster(redshift, identifier):
    """
    Basic wrapper around describe_clusters with a retry applied
    """
    return redshift.describe_clusters(ClusterIdentifier=identifier)["Clusters"][0]


@AWSRetry.jittered_backoff()
def _create_cluster(redshift, **kwargs):
    """
    Basic wrapper around create_cluster with a retry applied
    """
    return redshift.create_cluster(**kwargs)


# Simple wrapper around delete, try to avoid throwing an error if some other
# operation is in progress
@AWSRetry.jittered_backoff(catch_extra_error_codes=["InvalidClusterState"])
def _delete_cluster(redshift, **kwargs):
    """
    Basic wrapper around delete_cluster with a retry applied.
    Explicitly catches 'InvalidClusterState' (~ Operation in progress) so that
    we can still delete a cluster if some kind of change operation was in
    progress.
    """
    return redshift.delete_cluster(**kwargs)


@AWSRetry.jittered_backoff(catch_extra_error_codes=["InvalidClusterState"])
def _modify_cluster(redshift, **kwargs):
    """
    Basic wrapper around modify_cluster with a retry applied.
    Explicitly catches 'InvalidClusterState' (~ Operation in progress) for cases
    where another modification is still in progress
    """
    return redshift.modify_cluster(**kwargs)


def create_cluster(module, redshift):
    """
    Create a new cluster

    module: AnsibleAWSModule object
    redshift: authenticated redshift connection object

    Returns:
    """

    identifier = module.params.get("identifier")
    node_type = module.params.get("node_type")
    username = module.params.get("username")
    password = module.params.get("password")
    d_b_name = module.params.get("db_name")
    wait = module.params.get("wait")
    wait_timeout = module.params.get("wait_timeout")
    tags = module.params.get("tags")

    changed = True
    # Package up the optional parameters
    params = {}
    for p in (
        "cluster_type",
        "cluster_security_groups",
        "vpc_security_group_ids",
        "cluster_subnet_group_name",
        "availability_zone",
        "preferred_maintenance_window",
        "cluster_parameter_group_name",
        "automated_snapshot_retention_period",
        "port",
        "cluster_version",
        "allow_version_upgrade",
        "number_of_nodes",
        "publicly_accessible",
        "encrypted",
        "elastic_ip",
        "enhanced_vpc_routing",
    ):
        # https://github.com/boto/boto3/issues/400
        if module.params.get(p) is not None:
            params[p] = module.params.get(p)

    if d_b_name:
        params["d_b_name"] = d_b_name
    if tags:
        tags = ansible_dict_to_boto3_tag_list(tags)
        params["tags"] = tags

    try:
        _describe_cluster(redshift, identifier)
        changed = False
    except is_boto3_error_code("ClusterNotFound"):
        try:
            _create_cluster(
                redshift,
                ClusterIdentifier=identifier,
                NodeType=node_type,
                MasterUsername=username,
                MasterUserPassword=password,
                **snake_dict_to_camel_dict(params, capitalize_first=True),
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to create cluster")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe cluster")
    if wait:
        attempts = wait_timeout // 60
        waiter = redshift.get_waiter("cluster_available")
        try:
            waiter.wait(ClusterIdentifier=identifier, WaiterConfig=dict(MaxAttempts=attempts))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout waiting for the cluster creation")
    try:
        resource = _describe_cluster(redshift, identifier)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe cluster")

    if tags:
        if _ensure_tags(redshift, identifier, resource["Tags"], module):
            changed = True
            resource = _describe_cluster(redshift, identifier)

    return changed, _collect_facts(resource)


def describe_cluster(module, redshift):
    """
    Collect data about the cluster.

    module: Ansible module object
    redshift: authenticated redshift connection object
    """
    identifier = module.params.get("identifier")

    try:
        resource = _describe_cluster(redshift, identifier)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Error describing cluster")

    return True, _collect_facts(resource)


def delete_cluster(module, redshift):
    """
    Delete a cluster.

    module: Ansible module object
    redshift: authenticated redshift connection object
    """

    identifier = module.params.get("identifier")
    wait = module.params.get("wait")
    wait_timeout = module.params.get("wait_timeout")

    params = {}
    for p in ("skip_final_cluster_snapshot", "final_cluster_snapshot_identifier"):
        if p in module.params:
            # https://github.com/boto/boto3/issues/400
            if module.params.get(p) is not None:
                params[p] = module.params.get(p)

    try:
        _delete_cluster(
            redshift, ClusterIdentifier=identifier, **snake_dict_to_camel_dict(params, capitalize_first=True)
        )
    except is_boto3_error_code("ClusterNotFound"):
        return False, {}
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to delete cluster")

    if wait:
        attempts = wait_timeout // 60
        waiter = redshift.get_waiter("cluster_deleted")
        try:
            waiter.wait(ClusterIdentifier=identifier, WaiterConfig=dict(MaxAttempts=attempts))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout deleting the cluster")

    return True, {}


def modify_cluster(module, redshift):
    """
    Modify an existing cluster.

    module: Ansible module object
    redshift: authenticated redshift connection object
    """

    identifier = module.params.get("identifier")
    wait = module.params.get("wait")
    wait_timeout = module.params.get("wait_timeout")

    # Package up the optional parameters
    params = {}
    for p in (
        "cluster_type",
        "cluster_security_groups",
        "vpc_security_group_ids",
        "cluster_subnet_group_name",
        "availability_zone",
        "preferred_maintenance_window",
        "cluster_parameter_group_name",
        "automated_snapshot_retention_period",
        "port",
        "cluster_version",
        "allow_version_upgrade",
        "number_of_nodes",
        "new_cluster_identifier",
    ):
        # https://github.com/boto/boto3/issues/400
        if module.params.get(p) is not None:
            params[p] = module.params.get(p)

    # enhanced_vpc_routing parameter change needs an exclusive request
    if module.params.get("enhanced_vpc_routing") is not None:
        try:
            _modify_cluster(
                redshift, ClusterIdentifier=identifier, EnhancedVpcRouting=module.params.get("enhanced_vpc_routing")
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg=f"Couldn't modify redshift cluster {identifier} ")
    if wait:
        attempts = wait_timeout // 60
        waiter = redshift.get_waiter("cluster_available")
        try:
            waiter.wait(ClusterIdentifier=identifier, WaiterConfig=dict(MaxAttempts=attempts))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout waiting for cluster enhanced vpc routing modification")

    # change the rest
    try:
        _modify_cluster(
            redshift, ClusterIdentifier=identifier, **snake_dict_to_camel_dict(params, capitalize_first=True)
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Couldn't modify redshift cluster {identifier} ")

    if module.params.get("new_cluster_identifier"):
        identifier = module.params.get("new_cluster_identifier")

    if wait:
        attempts = wait_timeout // 60
        waiter2 = redshift.get_waiter("cluster_available")
        try:
            waiter2.wait(ClusterIdentifier=identifier, WaiterConfig=dict(MaxAttempts=attempts))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout waiting for cluster modification")
    try:
        resource = _describe_cluster(redshift, identifier)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Couldn't modify redshift cluster {identifier} ")

    if _ensure_tags(redshift, identifier, resource["Tags"], module):
        resource = redshift.describe_clusters(ClusterIdentifier=identifier)["Clusters"][0]

    return True, _collect_facts(resource)


def main():
    argument_spec = dict(
        command=dict(choices=["create", "facts", "delete", "modify"], required=True),
        identifier=dict(required=True),
        node_type=dict(
            choices=[
                "ds1.xlarge",
                "ds1.8xlarge",
                "ds2.xlarge",
                "ds2.8xlarge",
                "dc1.large",
                "dc2.large",
                "dc1.8xlarge",
                "dw1.xlarge",
                "dw1.8xlarge",
                "dw2.large",
                "dw2.8xlarge",
            ],
            required=False,
        ),
        username=dict(required=False),
        password=dict(no_log=True, required=False),
        db_name=dict(required=False),
        cluster_type=dict(choices=["multi-node", "single-node"], default="single-node"),
        cluster_security_groups=dict(aliases=["security_groups"], type="list", elements="str"),
        vpc_security_group_ids=dict(aliases=["vpc_security_groups"], type="list", elements="str"),
        skip_final_cluster_snapshot=dict(aliases=["skip_final_snapshot"], type="bool", default=False),
        final_cluster_snapshot_identifier=dict(aliases=["final_snapshot_id"], required=False),
        cluster_subnet_group_name=dict(aliases=["subnet"]),
        availability_zone=dict(aliases=["aws_zone", "zone"]),
        preferred_maintenance_window=dict(aliases=["maintance_window", "maint_window"]),
        cluster_parameter_group_name=dict(aliases=["param_group_name"]),
        automated_snapshot_retention_period=dict(aliases=["retention_period"], type="int"),
        port=dict(type="int"),
        cluster_version=dict(aliases=["version"], choices=["1.0"]),
        allow_version_upgrade=dict(aliases=["version_upgrade"], type="bool", default=True),
        number_of_nodes=dict(type="int"),
        publicly_accessible=dict(type="bool", default=False),
        encrypted=dict(type="bool", default=False),
        elastic_ip=dict(required=False),
        new_cluster_identifier=dict(aliases=["new_identifier"]),
        enhanced_vpc_routing=dict(type="bool", default=False),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=300),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )

    required_if = [
        ("command", "delete", ["skip_final_cluster_snapshot"]),
        ("command", "create", ["node_type", "username", "password"]),
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
    )

    command = module.params.get("command")
    skip_final_cluster_snapshot = module.params.get("skip_final_cluster_snapshot")
    final_cluster_snapshot_identifier = module.params.get("final_cluster_snapshot_identifier")
    # can't use module basic required_if check for this case
    if command == "delete" and skip_final_cluster_snapshot is False and final_cluster_snapshot_identifier is None:
        module.fail_json(
            msg="Need to specify final_cluster_snapshot_identifier if skip_final_cluster_snapshot is False"
        )

    conn = module.client("redshift")

    changed = True
    if command == "create":
        (changed, cluster) = create_cluster(module, conn)

    elif command == "facts":
        (changed, cluster) = describe_cluster(module, conn)

    elif command == "delete":
        (changed, cluster) = delete_cluster(module, conn)

    elif command == "modify":
        (changed, cluster) = modify_cluster(module, conn)

    module.exit_json(changed=changed, cluster=cluster)


if __name__ == "__main__":
    main()

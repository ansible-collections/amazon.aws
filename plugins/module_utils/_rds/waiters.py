# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from time import sleep

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
    from botocore.exceptions import WaiterError
except ImportError:
    pass

from ..waiters import get_waiter
from .common import get_rds_method_attribute


def wait_for_instance_status(client, module, db_instance_id: str, waiter_name: str) -> None:
    """
    Waits until provided instance has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_instance_id (str): DB instance identifier
            waiter_name (str): Name of either a boto3 rds client waiter or an RDS waiter defined in module_utils/waiters.py
    """

    def wait(client, db_instance_id, waiter_name):
        try:
            waiter = client.get_waiter(waiter_name)
        except ValueError:
            # using a waiter in module_utils/waiters.py
            waiter = get_waiter(client, waiter_name)
        waiter.wait(WaiterConfig={"Delay": 60, "MaxAttempts": 60}, DBInstanceIdentifier=db_instance_id)

    waiter_expected_status = {
        "db_instance_deleted": "deleted",
        "db_instance_stopped": "stopped",
    }
    expected_status = waiter_expected_status.get(waiter_name, "available")
    for _wait_attempts in range(0, 10):
        try:
            wait(client, db_instance_id, waiter_name)
            break
        except WaiterError as e:
            # Instance may be renamed and AWSRetry doesn't handle WaiterError
            if e.last_response.get("Error", {}).get("Code") == "DBInstanceNotFound":
                sleep(10)
                continue
            module.fail_json_aws(e, msg=f"Error while waiting for DB instance {db_instance_id} to be {expected_status}")
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(
                e, msg=f"Unexpected error while waiting for DB instance {db_instance_id} to be {expected_status}"
            )


def wait_for_cluster_status(client, module, db_cluster_id: str, waiter_name: str) -> None:
    """
    Waits until provided cluster has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_cluster_id (str): DB cluster identifier
            waiter_name (str): Name of either a boto3 rds client waiter or an RDS waiter defined in module_utils/waiters.py
    """
    try:
        get_waiter(client, waiter_name).wait(DBClusterIdentifier=db_cluster_id)
    except WaiterError as e:
        if waiter_name == "cluster_deleted":
            msg = f"Failed to wait for DB cluster {db_cluster_id} to be deleted"
        else:
            msg = f"Failed to wait for DB cluster {db_cluster_id} to be available"
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed with an unexpected error while waiting for the DB cluster {db_cluster_id}")


def wait_for_instance_snapshot_status(client, module, db_snapshot_id: str, waiter_name: str) -> None:
    """
    Waits until provided instance snapshot has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_snapshot_id (str): DB instance snapshot identifier
            waiter_name (str): Name of a boto3 rds client waiter
    """
    try:
        client.get_waiter(waiter_name).wait(DBSnapshotIdentifier=db_snapshot_id)
    except WaiterError as e:
        if waiter_name == "db_snapshot_deleted":
            msg = f"Failed to wait for DB snapshot {db_snapshot_id} to be deleted"
        else:
            msg = f"Failed to wait for DB snapshot {db_snapshot_id} to be available"
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e, msg=f"Failed with an unexpected error while waiting for the DB snapshot {db_snapshot_id}"
        )


def wait_for_cluster_snapshot_status(client, module, db_snapshot_id: str, waiter_name: str) -> None:
    """
    Waits until provided cluster snapshot has reached the expected status for provided waiter.

    Fails the module if an exception is raised while waiting.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            db_snapshot_id (str): DB cluster snapshot identifier
            waiter_name (str): Name of a boto3 rds client waiter
    """
    try:
        client.get_waiter(waiter_name).wait(DBClusterSnapshotIdentifier=db_snapshot_id)
    except WaiterError as e:
        if waiter_name == "db_cluster_snapshot_deleted":
            msg = f"Failed to wait for DB cluster snapshot {db_snapshot_id} to be deleted"
        else:
            msg = f"Failed to wait for DB cluster snapshot {db_snapshot_id} to be available"
        module.fail_json_aws(e, msg=msg)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg=f"Failed with an unexpected error while waiting for the DB cluster snapshot {db_snapshot_id}",
        )


def wait_for_status(client, module, identifier: str, method_name: str) -> None:
    """
    Waits until provided resource has reached the expected final status for provided method.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            identifier (str): resource identifier
            method_name (str): Name of boto3 rds client method on whose final status to wait
    """
    rds_method_attributes = get_rds_method_attribute(method_name, module)
    waiter_name = rds_method_attributes.waiter
    resource = rds_method_attributes.resource

    if resource == "cluster":
        wait_for_cluster_status(client, module, identifier, waiter_name)
    elif resource == "instance":
        wait_for_instance_status(client, module, identifier, waiter_name)
    elif resource == "instance_snapshot":
        wait_for_instance_snapshot_status(client, module, identifier, waiter_name)
    elif resource == "cluster_snapshot":
        wait_for_cluster_snapshot_status(client, module, identifier, waiter_name)

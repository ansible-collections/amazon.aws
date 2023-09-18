#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: directconnect_link_aggregation_group
version_added: 1.0.0
short_description: Manage Direct Connect LAG bundles
description:
  - Create, delete, or modify a Direct Connect link aggregation group.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_direct_connect_link_aggregation_group).
    The usage did not change.
author:
  - "Sloane Hertel (@s-hertel)"
options:
  state:
    description:
      - The state of the Direct Connect link aggregation group.
    choices:
      - present
      - absent
    type: str
    required: true
  name:
    description:
      - The name of the Direct Connect link aggregation group.
    type: str
  link_aggregation_group_id:
    description:
      - The ID of the Direct Connect link aggregation group.
    type: str
  num_connections:
    description:
      - The number of connections with which to initialize the link aggregation group.
    type: int
  min_links:
    description:
      - The minimum number of physical connections that must be operational for the LAG itself to be operational.
    type: int
  location:
    description:
      - The location of the link aggregation group.
    type: str
  bandwidth:
    description:
      - The bandwidth of the link aggregation group.
    type: str
  force_delete:
    description:
      - This allows the minimum number of links to be set to 0, any hosted connections disassociated,
        and any virtual interfaces associated to the LAG deleted.
    type: bool
    default: false
  connection_id:
    description:
      - A connection ID to link with the link aggregation group upon creation.
    type: str
  delete_with_disassociation:
    description:
      - To be used with I(state=absent) to delete connections after disassociating them with the LAG.
    type: bool
    default: false
  wait:
    description:
      - Whether or not to wait for the operation to complete.
      - May be useful when waiting for virtual interfaces to be deleted.
      - The time to wait can be controlled by setting I(wait_timeout).
    type: bool
    default: false
  wait_timeout:
    description:
      - The duration in seconds to wait if I(wait=true).
    default: 120
    type: int
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""

# create a Direct Connect connection
- community.aws.directconnect_link_aggregation_group:
  state: present
  location: EqDC2
  lag_id: dxlag-xxxxxxxx
  bandwidth: 1Gbps
"""

RETURN = r"""
changed:
  type: str
  description: Whether or not the LAG has changed.
  returned: always
aws_device:
  type: str
  description: The AWS Direct Connection endpoint that hosts the LAG.
  sample: "EqSe2-1bwfvazist2k0"
  returned: when I(state=present)
connections:
  type: list
  description: A list of connections bundled by this LAG.
  sample:
    "connections": [
      {
         "aws_device": "EqSe2-1bwfvazist2k0",
         "bandwidth": "1Gbps",
         "connection_id": "dxcon-fgzjah5a",
         "connection_name": "Requested Connection 1 for Lag dxlag-fgtoh97h",
         "connection_state": "down",
         "lag_id": "dxlag-fgnsp4rq",
         "location": "EqSe2",
         "owner_account": "123456789012",
         "region": "us-west-2"
      }
      ]
  returned: when I(state=present)
connections_bandwidth:
  type: str
  description: The individual bandwidth of the physical connections bundled by the LAG.
  sample: "1Gbps"
  returned: when I(state=present)
lag_id:
  type: str
  description: Unique identifier for the link aggregation group.
  sample: "dxlag-fgnsp4rq"
  returned: when I(state=present)
lag_name:
  type: str
  description: User-provided name for the link aggregation group.
  returned: when I(state=present)
lag_state:
  type: str
  description: State of the LAG.
  sample: "pending"
  returned: when I(state=present)
location:
  type: str
  description: Where the connection is located.
  sample: "EqSe2"
  returned: when I(state=present)
minimum_links:
  type: int
  description: The minimum number of physical connections that must be operational for the LAG itself to be operational.
  returned: when I(state=present)
number_of_connections:
  type: int
  description: The number of physical connections bundled by the LAG.
  returned: when I(state=present)
owner_account:
  type: str
  description: Owner account ID of the LAG.
  returned: when I(state=present)
region:
  type: str
  description: The region in which the LAG exists.
  returned: when I(state=present)
"""

import traceback
import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.direct_connect import DirectConnectError
from ansible_collections.amazon.aws.plugins.module_utils.direct_connect import delete_connection
from ansible_collections.amazon.aws.plugins.module_utils.direct_connect import delete_virtual_interface
from ansible_collections.amazon.aws.plugins.module_utils.direct_connect import disassociate_connection_and_lag
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def lag_status(client, lag_id):
    return lag_exists(client, lag_id=lag_id, lag_name=None, verify=False)


def lag_exists(client, lag_id=None, lag_name=None, verify=True):
    """If verify=True, returns the LAG ID or None
    If verify=False, returns the LAG's data (or an empty dict)
    """
    try:
        if lag_id:
            response = client.describe_lags(lagId=lag_id)
        else:
            response = client.describe_lags()
    except botocore.exceptions.ClientError as e:
        if lag_id and verify:
            return False
        elif lag_id:
            return {}
        else:
            failed_op = "Failed to describe DirectConnect link aggregation groups."
        raise DirectConnectError(msg=failed_op, last_traceback=traceback.format_exc(), exception=e)

    match = []  # List of LAG IDs that are exact matches
    lag = []  # List of LAG data that are exact matches

    # look for matching connections
    if len(response.get("lags", [])) == 1 and lag_id:
        if response["lags"][0]["lagState"] != "deleted":
            match.append(response["lags"][0]["lagId"])
            lag.append(response["lags"][0])
    else:
        for each in response.get("lags", []):
            if each["lagState"] != "deleted":
                if not lag_id:
                    if lag_name == each["lagName"]:
                        match.append(each["lagId"])
                else:
                    match.append(each["lagId"])

    # verifying if the connections exists; if true, return connection identifier, otherwise return False
    if verify and len(match) == 1:
        return match[0]
    elif verify:
        return False

    # not verifying if the connection exists; just return current connection info
    else:
        if len(lag) == 1:
            return lag[0]
        else:
            return {}


def create_lag(client, num_connections, location, bandwidth, name, connection_id):
    if not name:
        raise DirectConnectError(
            msg="Failed to create a Direct Connect link aggregation group: name required.",
            last_traceback=None,
            exception="",
        )

    parameters = dict(
        numberOfConnections=num_connections, location=location, connectionsBandwidth=bandwidth, lagName=name
    )
    if connection_id:
        parameters.update(connectionId=connection_id)
    try:
        lag = client.create_lag(**parameters)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(
            msg=f"Failed to create DirectConnect link aggregation group {name}",
            last_traceback=traceback.format_exc(),
            exception=e,
        )

    return lag["lagId"]


def delete_lag(client, lag_id):
    try:
        client.delete_lag(lagId=lag_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(
            msg=f"Failed to delete Direct Connect link aggregation group {lag_id}.",
            last_traceback=traceback.format_exc(),
            exception=e,
        )


@AWSRetry.jittered_backoff(retries=5, delay=2, backoff=2.0, catch_extra_error_codes=["DirectConnectClientException"])
def _update_lag(client, lag_id, lag_name, min_links):
    params = {}
    if min_links:
        params.update(minimumLinks=min_links)
    if lag_name:
        params.update(lagName=lag_name)

    client.update_lag(lagId=lag_id, **params)


def update_lag(client, lag_id, lag_name, min_links, num_connections, wait, wait_timeout):
    start = time.time()

    if min_links and min_links > num_connections:
        raise DirectConnectError(
            msg=f"The number of connections {num_connections} must be greater than the minimum number of links {min_links} to update the LAG {lag_id}",
            last_traceback=None,
            exception=None,
        )

    while True:
        try:
            _update_lag(client, lag_id, lag_name, min_links)
        except botocore.exceptions.ClientError as e:
            if wait and time.time() - start <= wait_timeout:
                continue
            msg = f"Failed to update Direct Connect link aggregation group {lag_id}."
            if "MinimumLinks cannot be set higher than the number of connections" in e.response["Error"]["Message"]:
                msg += f"Unable to set the min number of links to {min_links} while the LAG connections are being requested"
            raise DirectConnectError(msg=msg, last_traceback=traceback.format_exc(), exception=e)
        else:
            break


def lag_changed(current_status, name, min_links):
    """Determines if a modifiable link aggregation group attribute has been modified."""
    return (name and name != current_status["lagName"]) or (min_links and min_links != current_status["minimumLinks"])


def ensure_present(
    client, num_connections, lag_id, lag_name, location, bandwidth, connection_id, min_links, wait, wait_timeout
):
    exists = lag_exists(client, lag_id, lag_name)
    if not exists and lag_id:
        raise DirectConnectError(
            msg=f"The Direct Connect link aggregation group {lag_id} does not exist.",
            last_traceback=None,
            exception="",
        )

    # the connection is found; get the latest state and see if it needs to be updated
    if exists:
        lag_id = exists
        latest_state = lag_status(client, lag_id)
        if lag_changed(latest_state, lag_name, min_links):
            update_lag(client, lag_id, lag_name, min_links, num_connections, wait, wait_timeout)
            return True, lag_id
        return False, lag_id

    # no connection found; create a new one
    else:
        lag_id = create_lag(client, num_connections, location, bandwidth, lag_name, connection_id)
        update_lag(client, lag_id, lag_name, min_links, num_connections, wait, wait_timeout)
        return True, lag_id


def describe_virtual_interfaces(client, lag_id):
    try:
        response = client.describe_virtual_interfaces(connectionId=lag_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(
            msg=f"Failed to describe any virtual interfaces associated with LAG: {lag_id}",
            last_traceback=traceback.format_exc(),
            exception=e,
        )
    return response.get("virtualInterfaces", [])


def get_connections_and_virtual_interfaces(client, lag_id):
    virtual_interfaces = describe_virtual_interfaces(client, lag_id)
    connections = lag_status(client, lag_id=lag_id).get("connections", [])
    return virtual_interfaces, connections


def disassociate_vis(client, lag_id, virtual_interfaces):
    for vi in virtual_interfaces:
        delete_virtual_interface(client, vi["virtualInterfaceId"])
        try:
            response = client.delete_virtual_interface(virtualInterfaceId=vi["virtualInterfaceId"])
        except botocore.exceptions.ClientError as e:
            raise DirectConnectError(
                msg=f"Could not delete virtual interface {vi} to delete link aggregation group {lag_id}.",
                last_traceback=traceback.format_exc(),
                exception=e,
            )


def ensure_absent(client, lag_id, lag_name, force_delete, delete_with_disassociation, wait, wait_timeout):
    lag_id = lag_exists(client, lag_id, lag_name)
    if not lag_id:
        return False

    latest_status = lag_status(client, lag_id)

    # determine the associated connections and virtual interfaces to disassociate
    virtual_interfaces, connections = get_connections_and_virtual_interfaces(client, lag_id)

    # If min_links is not 0, there are associated connections, or if there are virtual interfaces, ask for force_delete
    if any((latest_status["minimumLinks"], virtual_interfaces, connections)) and not force_delete:
        raise DirectConnectError(
            msg=(
                "There are a minimum number of links, hosted connections, or associated virtual interfaces for LAG"
                f" {lag_id}. To force deletion of the LAG use delete_force: True (if the LAG has virtual interfaces"
                " they will be deleted). Optionally, to ensure hosted connections are deleted after disassociation use"
                " delete_with_disassociation: True and wait: True (as Virtual Interfaces may take a few moments to"
                " delete)"
            ),
            last_traceback=None,
            exception=None,
        )

    # update min_links to be 0 so we can remove the LAG
    update_lag(client, lag_id, None, 0, len(connections), wait, wait_timeout)

    # if virtual_interfaces and not delete_vi_with_disassociation: Raise failure; can't delete while vi attached
    for connection in connections:
        disassociate_connection_and_lag(client, connection["connectionId"], lag_id)
        if delete_with_disassociation:
            delete_connection(client, connection["connectionId"])

    for vi in virtual_interfaces:
        delete_virtual_interface(client, vi["virtualInterfaceId"])

    start_time = time.time()
    while True:
        try:
            delete_lag(client, lag_id)
        except DirectConnectError as e:
            if (
                ("until its Virtual Interfaces are deleted" in e.exception)
                and (time.time() - start_time < wait_timeout)
                and wait
            ):
                continue
        else:
            return True


def main():
    argument_spec = dict(
        state=dict(required=True, choices=["present", "absent"]),
        name=dict(),
        link_aggregation_group_id=dict(),
        num_connections=dict(type="int"),
        min_links=dict(type="int"),
        location=dict(),
        bandwidth=dict(),
        connection_id=dict(),
        delete_with_disassociation=dict(type="bool", default=False),
        force_delete=dict(type="bool", default=False),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=120),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=[("link_aggregation_group_id", "name")],
        required_if=[("state", "present", ("location", "bandwidth"))],
    )

    try:
        connection = module.client("directconnect")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    state = module.params.get("state")
    response = {}
    try:
        if state == "present":
            changed, lag_id = ensure_present(
                connection,
                num_connections=module.params.get("num_connections"),
                lag_id=module.params.get("link_aggregation_group_id"),
                lag_name=module.params.get("name"),
                location=module.params.get("location"),
                bandwidth=module.params.get("bandwidth"),
                connection_id=module.params.get("connection_id"),
                min_links=module.params.get("min_links"),
                wait=module.params.get("wait"),
                wait_timeout=module.params.get("wait_timeout"),
            )
            response = lag_status(connection, lag_id)
        elif state == "absent":
            changed = ensure_absent(
                connection,
                lag_id=module.params.get("link_aggregation_group_id"),
                lag_name=module.params.get("name"),
                force_delete=module.params.get("force_delete"),
                delete_with_disassociation=module.params.get("delete_with_disassociation"),
                wait=module.params.get("wait"),
                wait_timeout=module.params.get("wait_timeout"),
            )
    except DirectConnectError as e:
        if e.last_traceback:
            module.fail_json(msg=e.msg, exception=e.last_traceback, **camel_dict_to_snake_dict(e.exception))
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


if __name__ == "__main__":
    main()

"""aws_cloudtrail.py.

An ansible-rulebook event source module for getting events from an AWS CloudTrail

Arguments:
---------
    access_key:    Optional AWS access key ID
    secret_key:    Optional AWS secret access key
    session_token: Optional STS session token for use with temporary credentials
    endpoint_url:  Optional URL to connect to instead of the default AWS endpoints
    region:        Optional AWS region to use
    delay_seconds: The number of seconds to wait between polling (default 10sec)

    lookup_attributes:  The optional list of lookup attributes.
                        lookup attribute are dictionary with an AttributeKey (string),
                        which specifies an attribute on which to filter the events
                        returned and an AttributeValue (string) which specifies
                        a value for the specified AttributeKey
    event_category:     The optional event category to return. (e.g. 'insight')

Example:
-------
    - ansible.eda.aws_cloudtrail:
        region: us-east-1
        lookup_attributes:
            - AttributeKey: 'EventSource'
              AttributeValue: 'ec2.amazonaws.com'
            - AttributeKey: 'ReadOnly'
              AttributeValue: 'true'
        event_category: management

"""

import asyncio
import json
from datetime import datetime
from typing import Any

from aiobotocore.session import get_session
from botocore.client import BaseClient


def _cloudtrail_event_to_dict(event: dict[str, Any]) -> dict[str, Any]:
    event["EventTime"] = event["EventTime"].isoformat()
    event["CloudTrailEvent"] = json.loads(event["CloudTrailEvent"])
    return event


def _get_events(
    events: list[dict[str, Any]], last_event_ids: list[str]
) -> tuple[list[dict[str, Any]], Any, list[str]]:
    event_time = None
    event_ids = []
    result = []
    for event in events:
        # skip last event
        if last_event_ids and event["EventId"] in last_event_ids:
            continue
        if event_time is None or event_time < event["EventTime"]:
            event_time = event["EventTime"]
            event_ids = [event["EventId"]]
        elif event_time == event["EventTime"]:
            event_ids.append(event["EventId"])
        result.append(event)
    return result, event_time, event_ids


async def _get_cloudtrail_events(
    client: BaseClient, params: dict[str, Any]
) -> list[dict[str, Any]]:
    paginator = client.get_paginator("lookup_events")
    results = await paginator.paginate(**params).build_full_result()
    events = results.get("Events", [])
    # type guards:
    if not isinstance(events, list):
        raise ValueError("Events is not a list")
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Event is not a dictionary")
    return events


ARGS_MAPPING = {
    "lookup_attributes": "LookupAttributes",
    "event_category": "EventCategory",
}


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Receive events via AWS CloudTrail."""
    delay = int(args.get("delay_seconds", 10))

    session = get_session()
    params = {}
    for key, value in ARGS_MAPPING.items():
        if args.get(key) is not None:
            params[value] = args.get(key)

    params["StartTime"] = datetime.utcnow()  # noqa: DTZ003

    async with session.create_client("cloudtrail", **connection_args(args)) as client:
        event_time = None
        event_ids: list[str] = []
        while True:
            if event_time is not None:
                params["StartTime"] = event_time
            events = await _get_cloudtrail_events(client, params)

            events, c_event_time, c_event_ids = _get_events(events, event_ids)
            for event in events:
                await queue.put(_cloudtrail_event_to_dict(event))

            event_ids = c_event_ids or event_ids
            event_time = c_event_time or event_time

            await asyncio.sleep(delay)


def connection_args(args: dict[str, Any]) -> dict[str, Any]:
    """Provide connection arguments to AWS CloudTrail."""
    selected_args = {}

    # Best Practice: get credentials from ~/.aws/credentials or the environment
    # However the following method are still possible
    if "access_key" in args:
        selected_args["aws_access_key_id"] = args["access_key"]
    if "secret_key" in args:
        selected_args["aws_secret_access_key"] = args["secret_key"]
    if "session_token" in args:
        selected_args["aws_session_token"] = args["session_token"]

    if "endpoint_url" in args:
        selected_args["endpoint_url"] = args["endpoint_url"]
    if "region" in args:
        selected_args["region_name"] = args["region"]
    return selected_args


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {}))

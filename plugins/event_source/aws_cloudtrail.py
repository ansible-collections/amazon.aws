"""
aws_cloudtrail.py

An ansible-rulebook event source module for getting events from an AWS CloudTrail

Arguments:
    access_key:    Optional AWS access key ID
    secret_key:    Optional AWS secret access key
    session_token: Optional STS session token for use with temporary credentials
    endpoint_url:  Optional URL to connect to instead of the default AWS endpoints
    region:        Optional AWS region to use
    delay_seconds: The number of seconds to wait between polling (default 10sec)

    lookup_attributes:  The optional list of lookup attributes.
                        lookup attribute are dictionnary with an AttributeKey (string),
                        which specifies an attribute on which to filter the events
                        returned and an AttributeValue (string) which specifies
                        a value for the specified AttributeKey
    event_category:     The optional event category to return. (e.g. 'insight')

Example:

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
from typing import Any, Dict

from aiobotocore.session import get_session
from ansible_collections.ansible.eda.plugins.utils.aws_utils import connection_args


def _cloudtrail_event_to_dict(event):
    event["EventTime"] = event["EventTime"].isoformat()
    event["CloudTrailEvent"] = json.loads(event["CloudTrailEvent"])
    return event


def get_events(events, last_event_ids):
    event_time = None
    event_ids = []
    result = []
    for e in events:
        # skip last event
        if last_event_ids and e["EventId"] in last_event_ids:
            continue
        if event_time is None or event_time < e["EventTime"]:
            event_time = e["EventTime"]
            event_ids = [e["EventId"]]
        elif event_time == e["EventTime"]:
            event_ids.append(e["EventId"])
        result.append(e)
    return result, event_time, event_ids


async def get_cloudtrail_events(client, params):
    paginator = client.get_paginator("lookup_events")
    results = await paginator.paginate(**params).build_full_result()
    return results.get("Events", [])


ARGS_MAPPING = {
    "lookup_attributes": "LookupAttributes",
    "event_category": "EventCategory",
}


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    delay = int(args.get("delay_seconds", 10))

    session = get_session()
    params = {}
    for k, v in ARGS_MAPPING.items():
        if args.get(k) is not None:
            params[v] = args.get(k)

    params["StartTime"] = datetime.utcnow()

    async with session.create_client("cloudtrail", **connection_args(args)) as client:
        event_time = None
        event_ids = []
        while True:
            events = await get_cloudtrail_events(client, params)
            if event_time is not None:
                params["StartTime"] = event_time

            events, c_event_time, c_event_ids = get_events(events, event_ids)
            for event in events:
                await queue.put(_cloudtrail_event_to_dict(event))

            event_ids = c_event_ids or event_ids
            event_time = c_event_time or event_time

            await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {}))

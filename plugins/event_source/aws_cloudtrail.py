"""
aws_cloudtrail.py

An ansible-rulebook event source module for getting events from an AWS CloudTrail

Arguments:
    connection - Parameters used to create AWS session
    lookup_attributes - A dictionary representing the filters to be applied.
    event_category - Specifies the event category.
    delay - The number of seconds to wait between polling (default 10sec)

Example:

    - ansible.eda.aws_cloudtrail:
        connection:
            aws_access_key_id: access123456789
            aws_secret_access_key: secret123456789
            region_name: us-east-1
            profile_name: default
        lookup_attributes:
            EventSource: ec2.amazonaws.com
            Username: ansible
        event_category: management

"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

import boto3.session


def _parse_user_inputs(**kwargs):
    params = {}
    attributes = kwargs.get("lookup_attributes")
    if attributes:
        filters_list = []
        for k, v in attributes.items():
            filter_dict = {"AttributeKey": k, "AttributeValue": v}
            if isinstance(v, bool):
                filter_dict["AttributeValue"] = str(v).lower()
            elif isinstance(v, int):
                filter_dict["AttributeValue"] = str(v)
        filters_list.append(filter_dict)
        params["LookupAttributes"] = filters_list

    event_category = kwargs.get("event_category")
    if event_category:
        params["EventCategory"] = event_category
    return params


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


class AnsibleAwsCloudTrailEventClient(object):
    def __init__(self, connection):
        session = boto3.session.Session(**connection)
        self.client = session.client("cloudtrail")

    def lookup_events(self, **kwargs):
        paginator = self.client.get_paginator("lookup_events")
        return paginator.paginate(**kwargs).build_full_result().get("Events", [])


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    delay = args.get("delay", 10)
    client = AnsibleAwsCloudTrailEventClient(args.get("connection"))
    params = _parse_user_inputs(**args)
    params["StartTime"] = datetime.utcnow()

    event_time = None
    event_ids = []

    while True:
        if event_time is not None:
            params["StartTime"] = event_time

        events = client.lookup_events(**params)
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

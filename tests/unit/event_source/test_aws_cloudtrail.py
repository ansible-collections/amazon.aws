import datetime
from unittest.mock import patch

import pytest
from asyncmock import AsyncMock
from mock import MagicMock

from extensions.eda.plugins.event_source.aws_cloudtrail import (
    _cloudtrail_event_to_dict,
    _get_events,
    connection_args,
)
from extensions.eda.plugins.event_source.aws_cloudtrail import main as cloudtrail_main
from tests.conftest import ListQueue


@pytest.mark.asyncio
async def test_receive_from_cloudtrail(eda_queue: ListQueue) -> None:
    session = AsyncMock()
    t1 = datetime.datetime.now()
    t2 = datetime.datetime.now()
    raw_events = {
        "Events": [
            {
                "EventTime": t1,
                "EventId": "1",
                "CloudTrailEvent": '{"hello": "world"}',
            },
            {
                "EventTime": t2,
                "EventId": "2",
                "CloudTrailEvent": '{"foo": "bar"}',
            },
        ]
    }
    with patch(
        "extensions.eda.plugins.event_source.aws_cloudtrail.get_session",  # noqa: E501
        return_value=session,
    ):
        iterator = AsyncMock()
        iterator.build_full_result.return_value = raw_events
        paginator = MagicMock()
        paginator.paginate.return_value = iterator
        client = AsyncMock()
        client.get_paginator = MagicMock(side_effect=[paginator, ValueError()])
        session.create_client.return_value = client
        session.create_client.not_async = True

        with pytest.raises(ValueError):
            await cloudtrail_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "delay_seconds": 1,
                },
            )
        assert eda_queue.queue[0] == {
            "EventTime": t1.isoformat(),
            "EventId": "1",
            "CloudTrailEvent": {"hello": "world"},
        }
        assert eda_queue.queue[1] == {
            "EventTime": t2.isoformat(),
            "EventId": "2",
            "CloudTrailEvent": {"foo": "bar"},
        }
        assert len(eda_queue.queue) == 2


def test_get_events() -> None:
    events = [
        {
            "EventId": "1",
            "EventTime": "2025-05-20T14:23:45",
        },
        {
            "EventId": "2",
            "EventTime": "2025-05-20T14:23:55",
        },
        {
            "EventId": "3",
            "EventTime": "2025-05-20T14:23:55",
        },
    ]
    res = _get_events(events=events, last_event_ids=["1"])
    assert res[0] == [events[1], events[2]]
    assert res[1] == events[1]["EventTime"]
    assert res[2] == [events[1]["EventId"], events[2]["EventId"]]


def test_connection_args() -> None:
    conn_args = {
        "access_key": "secret",
        "secret_key": "secret",
        "session_token": "token",
        "endpoint_url": "http://example.com",
        "region": "US",
    }

    selected_args = connection_args(conn_args)

    assert selected_args["aws_access_key_id"] == conn_args["access_key"]
    assert selected_args["aws_secret_access_key"] == conn_args["secret_key"]
    assert selected_args["aws_session_token"] == conn_args["session_token"]
    assert selected_args["endpoint_url"] == conn_args["endpoint_url"]
    assert selected_args["region_name"] == conn_args["region"]


def test_cloudtrail_event_to_dict() -> None:
    event = {
        "EventTime": datetime.datetime.now(),
        "CloudTrailEvent": '{"eventTime": "2024-05-20T18:25:43Z","eventSource": '
        '"ec2.amazonaws.com","eventName": "StartInstances"}',
    }

    res_event = _cloudtrail_event_to_dict(event)

    assert res_event["EventTime"] == event["EventTime"]
    assert res_event["CloudTrailEvent"]["eventTime"] == "2024-05-20T18:25:43Z"
    assert res_event["CloudTrailEvent"]["eventSource"] == "ec2.amazonaws.com"
    assert res_event["CloudTrailEvent"]["eventName"] == "StartInstances"

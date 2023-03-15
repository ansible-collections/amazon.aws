import datetime
from unittest.mock import patch

import pytest
from asyncmock import AsyncMock
from mock import MagicMock

from plugins.event_source.aws_cloudtrail import main as cloudtrail_main


@pytest.mark.asyncio
async def test_receive_from_cloudtrail(eda_queue):
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
        "plugins.event_source.aws_cloudtrail.get_session",  # noqa: E501
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

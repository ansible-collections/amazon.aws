from unittest.mock import patch

import pytest
from ansible_collections.ansible.eda.plugins.event_source.aws_sqs_queue import (
    main as sqs_main,
)
from asyncmock import AsyncMock


@pytest.mark.asyncio
async def test_receive_from_sqs(eda_queue):
    session = AsyncMock()
    with patch(
        "ansible_collections.ansible.eda.plugins.event_source.aws_sqs_queue.get_session",  # noqa: E501
        return_value=session,
    ):
        client = AsyncMock()
        client.get_queue_url.return_value = {"QueueUrl": "sqs_url"}

        message1 = {
            "MessageId": "1",
            "Body": "Hello World",
            "ReceiptHandle": None,
        }
        message2 = {
            "MessageId": "2",
            "Body": '{"Say":"Hello World"}',
            "ReceiptHandle": None,
        }

        response = {"Messages": [message1, message2]}
        client.receive_message = AsyncMock(side_effect=[response, ValueError()])

        session.create_client.return_value = client
        session.create_client.not_async = True

        with pytest.raises(ValueError):
            await sqs_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "name": "eda",
                    "delay_seconds": 1,
                },
            )
        assert eda_queue.queue[0] == {"body": "Hello World", "meta": {"MessageId": "1"}}
        assert eda_queue.queue[1] == {
            "body": {"Say": "Hello World"},
            "meta": {"MessageId": "2"},
        }
        assert len(eda_queue.queue) == 2

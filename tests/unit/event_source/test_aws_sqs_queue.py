import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from asyncmock import AsyncMock

pytest.importorskip("aiobotocore")

from ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue import _delete_messages
from ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue import main as sqs_main
from ansible_collections.amazon.aws.tests.unit.utils.event import ListQueue


@pytest.mark.asyncio
async def test_receive_from_sqs(eda_queue: ListQueue) -> None:
    session = AsyncMock()
    with patch(
        "ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue.get_session",
        return_value=session,
    ):
        client = AsyncMock()
        client.get_queue_url.return_value = {"QueueUrl": "sqs_url"}

        message1 = {
            "MessageId": "1",
            "Body": "Hello World",
            "ReceiptHandle": "abcdef",
        }
        message2 = {
            "MessageId": "2",
            "Body": '{"Say":"Hello World"}',
            "ReceiptHandle": "xyz123",
        }
        delete_response1 = {
            "Id": "1",
            "ReceiptHandle": "abcdef",
        }
        delete_response2 = {
            "Id": "2",
            "ReceiptHandle": "xyz123",
            "Code": "405",
            "Message": "Failed to delete Message",
            "SenderFault": True,
        }

        response = {"Messages": [message1, message2]}
        delete_response = {
            "Successful": [delete_response1],
            "Failed": [delete_response2],
        }
        client.receive_message = AsyncMock(side_effect=[response, ValueError()])
        client.delete_message_batch = AsyncMock(side_effect=[delete_response, ValueError()])

        session.create_client.return_value = client
        session.create_client.not_async = True

        with pytest.raises(ValueError):
            await sqs_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "name": "eda",
                    "delay_seconds": 1,
                    "max_number_of_messages": 3,
                    "queue_owner_aws_account_id": "123456",
                },
            )
        assert eda_queue.queue[0] == {
            "body": "Hello World",
            "meta": {"MessageId": "1", "event": {"uuid": "1"}},
        }
        assert eda_queue.queue[1] == {
            "body": {"Say": "Hello World"},
            "meta": {"MessageId": "2", "event": {"uuid": "2"}},
        }
        assert len(eda_queue.queue) == 2


@pytest.mark.asyncio
async def test_feedback_enabled_without_queue() -> None:
    """Test that ValueError is raised when feedback is enabled but no feedback queue is provided."""
    session = AsyncMock()
    with patch(
        "ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue.get_session",
        return_value=session,
    ):
        eda_queue = ListQueue()
        with pytest.raises(ValueError, match="feedback: true was set but no feedback queue was provided"):
            await sqs_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "name": "eda",
                    "feedback": True,
                },
            )


@pytest.mark.asyncio
async def test_feedback_mechanism(eda_queue: ListQueue) -> None:
    """Test the feedback mechanism with a feedback queue."""
    session = AsyncMock()
    with patch(
        "ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue.get_session",
        return_value=session,
    ):
        client = AsyncMock()
        client.get_queue_url.return_value = {"QueueUrl": "sqs_url"}

        message1 = {
            "MessageId": "1",
            "Body": '{"test":"data"}',
            "ReceiptHandle": "handle1",
        }
        response = {"Messages": [message1]}
        delete_response = {
            "Successful": [{"Id": "1", "ReceiptHandle": "handle1"}],
        }

        client.receive_message = AsyncMock(side_effect=[response, ValueError()])

        # Create a manual tracking mock for delete_message_batch
        delete_call_tracker = MagicMock()

        async def mock_delete_batch(*args, **kwargs):
            delete_call_tracker(*args, **kwargs)
            return delete_response

        client.delete_message_batch = mock_delete_batch

        session.create_client.return_value = client
        session.create_client.not_async = True

        # Create a feedback queue and pre-populate with a response
        feedback_queue = asyncio.Queue()
        await feedback_queue.put({"status": "processed"})

        with pytest.raises(ValueError):
            await sqs_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "name": "eda",
                    "delay_seconds": 1,
                    "feedback": True,
                    "feedback_timeout": 5,
                    "eda_feedback_queue": feedback_queue,
                },
            )

        # Verify the message was put in the queue
        assert len(eda_queue.queue) == 1
        assert eda_queue.queue[0]["body"] == {"test": "data"}
        # Verify delete was called
        delete_call_tracker.assert_called_once()


@pytest.mark.asyncio
async def test_feedback_timeout(eda_queue: ListQueue) -> None:
    """Test that TimeoutError is raised when feedback queue times out."""
    session = AsyncMock()
    with patch(
        "ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue.get_session",
        return_value=session,
    ):
        client = AsyncMock()
        client.get_queue_url.return_value = {"QueueUrl": "sqs_url"}

        message1 = {
            "MessageId": "1",
            "Body": '{"test":"data"}',
            "ReceiptHandle": "handle1",
        }
        response = {"Messages": [message1]}

        client.receive_message = AsyncMock(return_value=response)
        client.delete_message_batch = AsyncMock()

        session.create_client.return_value = client
        session.create_client.not_async = True

        # Create an empty feedback queue (nothing to get, will timeout)
        feedback_queue = asyncio.Queue()

        with pytest.raises(asyncio.TimeoutError):
            await sqs_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "name": "eda",
                    "delay_seconds": 1,
                    "feedback": True,
                    "feedback_timeout": 1,  # 1 second timeout
                    "eda_feedback_queue": feedback_queue,
                },
            )

        # Verify the message was put in the queue before timeout
        assert len(eda_queue.queue) == 1


@pytest.mark.asyncio
async def test_delete_messages_success() -> None:
    """Test _delete_messages with successful deletion."""
    delete_response = {
        "Successful": [
            {"Id": "1"},
            {"Id": "2"},
        ],
    }

    # Create a manual tracking mock
    call_tracker = MagicMock()

    async def mock_delete_batch(*args, **kwargs):
        call_tracker(*args, **kwargs)
        return delete_response

    client = AsyncMock()
    client.delete_message_batch = mock_delete_batch
    client.delete_message_batch.mock = call_tracker

    entries = [
        {"Id": "1", "ReceiptHandle": "handle1"},
        {"Id": "2", "ReceiptHandle": "handle2"},
    ]

    result = await _delete_messages(client, "queue_url", entries)

    assert result is True
    call_tracker.assert_called_once_with(
        QueueUrl="queue_url",
        Entries=entries,
    )


@pytest.mark.asyncio
async def test_delete_messages_failure() -> None:
    """Test _delete_messages with failed deletion."""
    client = AsyncMock()
    delete_response = {
        "Successful": [{"Id": "1"}],
        "Failed": [
            {
                "Id": "2",
                "Code": "500",
                "Message": "Internal Error",
                "SenderFault": False,
            }
        ],
    }
    client.delete_message_batch = AsyncMock(side_effect=[delete_response])

    entries = [
        {"Id": "1", "ReceiptHandle": "handle1"},
        {"Id": "2", "ReceiptHandle": "handle2"},
    ]

    result = await _delete_messages(client, "queue_url", entries)

    assert result is False


@pytest.mark.asyncio
async def test_delete_messages_all_failures() -> None:
    """Test _delete_messages with all messages failing to delete."""
    client = AsyncMock()
    delete_response = {
        "Failed": [
            {
                "Id": "1",
                "Code": "500",
                "Message": "Internal Error",
                "SenderFault": True,
            }
        ],
    }
    client.delete_message_batch = AsyncMock(side_effect=[delete_response])

    entries = [{"Id": "1", "ReceiptHandle": "handle1"}]

    result = await _delete_messages(client, "queue_url", entries)

    assert result is False


@pytest.mark.asyncio
async def test_unicode_error_handling(eda_queue: ListQueue) -> None:
    """Test handling of UnicodeError when decoding message body."""
    session = AsyncMock()
    with patch(
        "ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue.get_session",
        return_value=session,
    ):
        client = AsyncMock()
        client.get_queue_url.return_value = {"QueueUrl": "sqs_url"}

        # Create a message with body that will raise UnicodeError when json.loads is called
        message1 = {
            "MessageId": "1",
            "Body": "test",  # Will be patched to raise UnicodeError
            "ReceiptHandle": "handle1",
        }
        response = {"Messages": [message1]}
        delete_response = {"Successful": [{"Id": "1"}]}

        client.receive_message = AsyncMock(side_effect=[response, ValueError()])
        client.delete_message_batch = AsyncMock(side_effect=[delete_response])

        session.create_client.return_value = client
        session.create_client.not_async = True

        # Patch json.loads to raise UnicodeError
        with patch("json.loads", side_effect=UnicodeError("unicode error")):
            with pytest.raises(ValueError):
                await sqs_main(
                    eda_queue,
                    {
                        "region": "us-east-1",
                        "name": "eda",
                        "delay_seconds": 1,
                    },
                )

        # Verify the message was put in queue with None body
        assert len(eda_queue.queue) == 1
        assert eda_queue.queue[0]["body"] is None
        assert eda_queue.queue[0]["meta"]["MessageId"] == "1"


@pytest.mark.asyncio
async def test_delete_failure_in_feedback_mode(eda_queue: ListQueue) -> None:
    """Test that exception is raised when deletion fails in feedback mode."""
    session = AsyncMock()
    with patch(
        "ansible_collections.amazon.aws.extensions.eda.plugins.event_source.aws_sqs_queue.get_session",
        return_value=session,
    ):
        client = AsyncMock()
        client.get_queue_url.return_value = {"QueueUrl": "sqs_url"}

        message1 = {
            "MessageId": "1",
            "Body": '{"test":"data"}',
            "ReceiptHandle": "handle1",
        }
        response = {"Messages": [message1]}
        delete_response = {
            "Failed": [
                {
                    "Id": "1",
                    "Code": "500",
                    "Message": "Delete failed",
                    "SenderFault": False,
                }
            ],
        }

        client.receive_message = AsyncMock(side_effect=[response])
        client.delete_message_batch = AsyncMock(side_effect=[delete_response])

        session.create_client.return_value = client
        session.create_client.not_async = True

        # Create a feedback queue with a response
        feedback_queue = asyncio.Queue()
        await feedback_queue.put({"status": "processed"})

        with pytest.raises(Exception, match="Messages could not be deleted"):
            await sqs_main(
                eda_queue,
                {
                    "region": "us-east-1",
                    "name": "eda",
                    "delay_seconds": 1,
                    "feedback": True,
                    "feedback_timeout": 5,
                    "eda_feedback_queue": feedback_queue,
                },
            )

        # Verify the message was put in the queue
        assert len(eda_queue.queue) == 1

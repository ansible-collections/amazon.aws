import asyncio
import json
import logging
from typing import Any
from typing import TypedDict

import botocore.exceptions
from aiobotocore.session import get_session

DOCUMENTATION = r"""
---
short_description: Receive events via an AWS SQS queue
description:
  - An ansible-rulebook event source plugin for receiving events via an AWS SQS queue.
  - >
    This supports all the authentication methods supported by boto3 library:
    U(https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html).
options:
  access_key:
    description:
      - Optional AWS access key ID.
    type: str
  secret_key:
    description:
      - Optional AWS secret access key.
    type: str
  session_token:
    description:
      - Optional STS session token for use with temporary credentials.
    type: str
  endpoint_url:
    description:
      - Optional URL to connect to instead of the default AWS endpoints.
    type: str
  queue_owner_aws_account_id:
    description:
      - >
        Optional The Amazon Web Services account ID of the account that
        created the queue. This is only required when you are attempting
        to access a queue owned by another Amazon Web Services account.
    type: str
  region:
    description:
      - Optional AWS region to use.
    type: str
  name:
    description:
      - Name of the queue.
    type: str
    required: true
  delay_seconds:
    description:
      - The SQS long polling duration.
      - Set to V(0) to disable.
    type: int
    default: 2
  max_number_of_messages:
    description:
      - >
        Optional The maximum number of messages to return. Amazon SQS
        never returns more messages than this value (however, fewer
        messages might be returned). Valid values are V(1) to V(10).
    type: int
    default: 1
  feedback:
    type: bool
    default: false
    description:
      - Should the source plugin wait for feedback before
        processing the next event from SQS Queue.
        This flag allows ansible rulebook to pass in an asyncio
        queue which is passed in the O(eda_feedback_queue).
        The source plugin should wait for the response to come
        back on this queue before it picks the next event from
        SQS queue.
  feedback_timeout:
    type: int
    default: 120
    description:
      - Timeout in seconds to wait for feedback from the rule engine
        before raising an exception. Only applies when feedback is enabled.
  eda_feedback_queue:
    description:
      - Provided automatically by ansible-rulebook when the feedback
        parameter is enabled, this parameter utilizes an asyncio.Queue.
        It allows the system to wait for confirmation that an event has
        been safely persisted in the database before removing it from the 
        event queue. Users do not need to provide a value for this manually.
"""

EXAMPLES = r"""
- amazon.aws.aws_sqs_queue:
    region: us-east-1
    name: eda
    delay_seconds: 10
"""


DEFAULT_FEEDBACK_TIMEOUT = 120


class DeleteMessageBatchRequestEntryTypeDef(TypedDict):
    """Custom TypedDict for Delete Message Batch Request Entry."""

    Id: str
    ReceiptHandle: str


class MessageDeletionException(Exception):
    pass


class QueueConfig(TypedDict):
    """Configuration extracted from arguments."""

    queue_name: str
    wait_seconds: int
    max_number_of_messages: int
    queue_owner_aws_account_id: str | None
    feedback_enabled: bool
    feedback_timeout: int
    eda_feedback_queue: asyncio.Queue[Any] | None


def _validate_and_extract_config(args: dict[str, Any]) -> QueueConfig:
    """Validate arguments and extract configuration.

    Args:
        args: Dictionary of arguments

    Returns:
        QueueConfig with validated configuration

    Raises:
        ValueError: If required arguments are missing or invalid
    """
    if "name" not in args:
        msg = "Missing queue name"
        raise ValueError(msg)

    feedback_enabled = args.get("feedback", False)
    eda_feedback_queue = args.get("eda_feedback_queue", None)

    if feedback_enabled and eda_feedback_queue is None:
        msg = (
            "feedback: true was set but no feedback queue was provided. "
            "This requires a compatible version of ansible-rulebook that "
            "supports the feedback mechanism."
        )
        raise ValueError(msg)

    return QueueConfig(
        queue_name=str(args.get("name")),
        wait_seconds=int(args.get("delay_seconds", 2)),
        max_number_of_messages=int(args.get("max_number_of_messages", 1)),
        queue_owner_aws_account_id=args.get("queue_owner_aws_account_id"),
        feedback_enabled=feedback_enabled,
        feedback_timeout=int(args.get("feedback_timeout", DEFAULT_FEEDBACK_TIMEOUT)),
        eda_feedback_queue=eda_feedback_queue,
    )


async def _get_queue_url(
    client,
    queue_name: str,
    queue_owner_aws_account_id: str | None,
) -> str:
    """Retrieve the SQS queue URL.

    Args:
        client: AWS SQS client
        queue_name: Name of the queue
        queue_owner_aws_account_id: Optional account ID of queue owner

    Returns:
        Queue URL

    Raises:
        ValueError: If queue does not exist
    """
    queue_args = {"QueueName": queue_name}
    if queue_owner_aws_account_id:
        queue_args["QueueOwnerAWSAccountId"] = queue_owner_aws_account_id

    try:
        response = await client.get_queue_url(**queue_args)
    except botocore.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
            msg = f"Queue {queue_name} does not exist"
            raise ValueError(msg) from None
        raise

    return response["QueueUrl"]


def _parse_message_body(entry: dict[str, Any]) -> Any:
    """Parse the message body from JSON.

    Args:
        entry: SQS message entry

    Returns:
        Parsed message body or raw body if parsing fails
    """
    logger = logging.getLogger()

    try:
        return json.loads(entry["Body"])
    except json.JSONDecodeError:
        logger.error("JSON decode error, storing raw value")
        return entry["Body"]
    except UnicodeError:
        logger.exception("Unicode error while decoding message body")
        return None


async def _handle_feedback_and_delete(
    client,
    queue_url: str,
    delete_entry: DeleteMessageBatchRequestEntryTypeDef,
    config: QueueConfig,
) -> None:
    """Handle feedback mechanism and message deletion.

    Args:
        client: AWS SQS client
        queue_url: Queue URL
        delete_entry: Message deletion entry
        config: Queue configuration

    Raises:
        asyncio.TimeoutError: If feedback timeout is exceeded
        MessageDeletionException: If message deletion fails
    """
    logger = logging.getLogger()

    if config["feedback_enabled"] and config["eda_feedback_queue"]:
        try:
            await asyncio.wait_for(
                config["eda_feedback_queue"].get(),
                timeout=config["feedback_timeout"],
            )
            if not await _delete_messages(client, queue_url, [delete_entry]):
                logger.exception("Failed to delete messages, exiting")
                raise MessageDeletionException("Messages could not be deleted")
        except asyncio.TimeoutError:
            logger.exception("Timed out waiting for feedback")
            raise
    else:
        await _delete_messages(client, queue_url, [delete_entry])


async def _process_message(
    entry: dict[str, Any],
    queue: asyncio.Queue[Any],
    client,
    queue_url: str,
    config: QueueConfig,
) -> None:
    """Process a single SQS message.

    Args:
        entry: SQS message entry
        queue: Queue to put processed events
        client: AWS SQS client
        queue_url: Queue URL
        config: Queue configuration

    Raises:
        ValueError: If message format is invalid
    """
    if not isinstance(entry, dict) or "MessageId" not in entry:  # pragma: no cover
        err_msg = f"Unexpected response {entry}, missing MessageId."
        raise ValueError(err_msg)

    delete_entry = DeleteMessageBatchRequestEntryTypeDef(
        Id=entry["MessageId"],
        ReceiptHandle=entry["ReceiptHandle"],
    )

    meta = {
        "MessageId": entry["MessageId"],
        "event": {"uuid": entry["MessageId"]},
    }

    msg_body = _parse_message_body(entry)

    await queue.put({"body": msg_body, "meta": meta})
    await _handle_feedback_and_delete(client, queue_url, delete_entry, config)
    await asyncio.sleep(0)


async def _delete_messages(client, queue_url, entries) -> bool:
    result = False
    logger = logging.getLogger()
    # Need to remove msg from queue or else it'll reappear
    delete_results = await client.delete_message_batch(
        QueueUrl=queue_url,
        Entries=entries,
    )

    # Check if the deletion was successful
    if "Successful" in delete_results:
        result = True
        for item in delete_results["Successful"]:
            logger.debug(
                "Message with ID %s deleted successfully",
                item["Id"],
            )
    # Log a error if any message failed deletions
    if "Failed" in delete_results:
        result = False
        for item in delete_results["Failed"]:
            logger.error(
                "Error deleting message with ID : %s Error Code: %s Error Message: %s SenderFault: %s",
                item["Id"],
                item["Code"],
                item["Message"],
                str(item["SenderFault"]),
            )

    return result


async def main(
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Receive events via an AWS SQS queue."""
    logger = logging.getLogger()

    # Validate arguments and extract configuration
    config = _validate_and_extract_config(args)

    session = get_session()

    async with session.create_client("sqs", **connection_args(args)) as client:
        # Get the queue URL
        queue_url = await _get_queue_url(
            client,
            config["queue_name"],
            config["queue_owner_aws_account_id"],
        )

        # Main message processing loop
        while True:
            # This loop won't spin really fast as there is
            # essentially a sleep in the receive_message call
            response_msg = await client.receive_message(
                QueueUrl=queue_url,
                WaitTimeSeconds=config["wait_seconds"],
                MaxNumberOfMessages=config["max_number_of_messages"],
            )

            if "Messages" in response_msg:
                for entry in response_msg["Messages"]:
                    await _process_message(entry, queue, client, queue_url, config)
            else:
                logger.debug("No messages in queue")


def connection_args(args: dict[str, Any]) -> dict[str, Any]:
    """Provide connection arguments to AWS SQS queue."""
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
    # MockQueue if running directly

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"region": "us-east-1", "name": "eda"}))

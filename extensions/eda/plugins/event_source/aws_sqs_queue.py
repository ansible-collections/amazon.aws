import asyncio
import json
import logging
from typing import Any

import botocore.exceptions
from aiobotocore.session import get_session

DOCUMENTATION = r"""
---
short_description: Receive events via an AWS SQS queue.
description:
  - An ansible-rulebook event source plugin for receiving events via an AWS SQS queue.
  - This supports all the authentication methods supported by boto library:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
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
      - Set to 0 to disable.
    type: int
    default: 2
"""

EXAMPLES = r"""
- ansible.eda.aws_sqs_queue:
    region: us-east-1
    name: eda
    delay_seconds: 10
"""


# pylint: disable=too-many-locals
async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Receive events via an AWS SQS queue."""
    logger = logging.getLogger()

    if "name" not in args:
        msg = "Missing queue name"
        raise ValueError(msg)
    queue_name = str(args.get("name"))
    wait_seconds = int(args.get("delay_seconds", 2))

    session = get_session()
    async with session.create_client("sqs", **connection_args(args)) as client:
        try:
            response = await client.get_queue_url(QueueName=queue_name)
        except botocore.exceptions.ClientError as err:
            if (
                err.response["Error"]["Code"]
                == "AWS.SimpleQueueService.NonExistentQueue"
            ):
                msg = f"Queue {queue_name} does not exist"
                raise ValueError(msg) from None
            raise

        queue_url = response["QueueUrl"]

        while True:
            # This loop won't spin really fast as there is
            # essentially a sleep in the receive_message call
            response_msg = await client.receive_message(
                QueueUrl=queue_url,
                WaitTimeSeconds=wait_seconds,
            )

            if "Messages" in response_msg:
                for entry in response_msg["Messages"]:
                    if (
                        not isinstance(entry, dict) or "MessageId" not in entry
                    ):  # pragma: no cover
                        err_msg = (
                            f"Unexpected response {response_msg}, missing MessageId."
                        )
                        raise ValueError(err_msg)
                    meta = {"MessageId": entry["MessageId"]}
                    try:
                        msg_body = json.loads(entry["Body"])
                    except json.JSONDecodeError:
                        msg_body = entry["Body"]

                    await queue.put({"body": msg_body, "meta": meta})
                    await asyncio.sleep(0)

                    # Need to remove msg from queue or else it'll reappear
                    await client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=entry["ReceiptHandle"],
                    )
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

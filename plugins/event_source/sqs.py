"""
sqs.py

An ansible-rulebook event source plugin for receiving events via an AWS SQS queue.

Arguments:
    region: AWS region containing the SQS queue.
    queue:  Name of the SQS queue.
    wait_seconds: The SQS long polling duration. Set to 0 to disable. Defaults to 2.
"""

import asyncio
import json
import logging
from typing import Any, Dict

import botocore.exceptions
from aiobotocore.session import get_session


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    logger = logging.getLogger()

    region = args.get("region")
    queue_name = args.get("queue")
    wait_seconds = int(args.get("wait_seconds", 2))

    # Boto should get credentials from ~/.aws/credentials or the environment
    session = get_session()
    async with session.create_client("sqs", region_name=region) as client:
        try:
            response = await client.get_queue_url(QueueName=queue_name)
        except botocore.exceptions.ClientError as err:
            if (
                err.response["Error"]["Code"]
                == "AWS.SimpleQueueService.NonExistentQueue"
            ):
                raise RuntimeError("Queue %s does not exist" % queue_name)
            else:
                raise

        queue_url = response["QueueUrl"]

        while True:
            # This loop wont spin really fast as there is
            # essentially a sleep in the receive_message call
            response = await client.receive_message(
                QueueUrl=queue_url,
                WaitTimeSeconds=wait_seconds,
            )

            if "Messages" in response:
                for msg in response["Messages"]:
                    meta = {"MessageId": msg["MessageId"]}
                    try:
                        msg_body = json.loads(msg["Body"])
                    except json.JSONDecodeError:
                        msg_body = msg["Body"]

                    await queue.put({"body": msg_body, "meta": meta})
                    await asyncio.sleep(0)                        

                    # Need to remove msg from queue or else it'll reappear
                    await client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
            else:
                logger.debug("No messages in queue")


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"region": "us-east-1", "queue": "eda"}))

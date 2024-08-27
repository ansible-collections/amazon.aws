import asyncio
from typing import Any

import pytest


class ListQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, item: Any) -> None:
        self.queue.append(item)

    def put_nowait(self, item: Any) -> None:
        self.queue.append(item)


@pytest.fixture
def eda_queue() -> ListQueue:
    return ListQueue()

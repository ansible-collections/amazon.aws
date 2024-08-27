import asyncio
from typing import Any

import pytest


class ListQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, event) -> None:
        self.queue.append(event)

    def put_nowait(self, event) -> None:
        self.queue.append(event)


@pytest.fixture
def eda_queue():
    return ListQueue()

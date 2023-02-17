import pytest


class ListQueue:
    def __init__(self):
        self.queue = []

    async def put(self, event):
        self.queue.append(event)

    def put_nowait(self, event):
        self.queue.append(event)


@pytest.fixture
def eda_queue():
    return ListQueue()

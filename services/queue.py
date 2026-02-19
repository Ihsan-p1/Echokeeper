import asyncio
import logging
from collections.abc import Coroutine
from typing import Any
from config import QUEUE_SLEEP_SECONDS

log = logging.getLogger("queue")


class TranslateQueue:
    """
    Simple async task queue untuk rate-limit request ke HuggingFace API.
    Setiap task dieksekusi satu per satu dengan jeda QUEUE_SLEEP_SECONDS.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())
            log.info("TranslateQueue worker started.")

    def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            log.info("TranslateQueue worker stopped.")

    async def _worker(self) -> None:
        while True:
            coro, future = await self._queue.get()
            try:
                result = await coro
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self._queue.task_done()
                await asyncio.sleep(QUEUE_SLEEP_SECONDS)

    async def submit(self, coro: Coroutine[Any, Any, str]) -> str:
        """Submit a coroutine and await its result through the queue."""
        loop = asyncio.get_event_loop()
        future: asyncio.Future[str] = loop.create_future()
        await self._queue.put((coro, future))
        return await future


# Singleton
translate_queue = TranslateQueue()

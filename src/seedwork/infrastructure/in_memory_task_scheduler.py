from collections.abc import Sequence
from typing import Any

from seedwork.application.background_tasks import BackgroundTask, TaskHandler


class InMemoryTaskScheduler:
    def __init__(self) -> None:
        self._scheduled: list[BackgroundTask] = []
        self._handlers: dict[str, TaskHandler[Any]] = {}

    @property
    def scheduled(self) -> Sequence[BackgroundTask]:
        return list(self._scheduled)

    def register(self, task_type: str, handler: TaskHandler[Any]) -> None:
        self._handlers[task_type] = handler

    async def schedule(self, task: BackgroundTask) -> None:
        self._scheduled.append(task)

    async def execute_scheduled(self) -> None:
        for task in list(self._scheduled):
            handler = self._handlers.get(task.type)
            if handler:
                await handler.handle(task)

    def reset(self) -> None:
        self._scheduled.clear()

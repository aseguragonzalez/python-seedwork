from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from seedwork.application.background_tasks import BackgroundTask, TaskHandler, TaskScheduler


@runtime_checkable
class TaskSchedulerSpy(TaskScheduler, Protocol):
    @property
    def scheduled(self) -> Sequence[BackgroundTask]: ...

    def register(self, task_type: str, handler: TaskHandler[Any]) -> None: ...

    async def execute_scheduled(self) -> None: ...

    def reset(self) -> None: ...


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
        tasks, self._scheduled = list(self._scheduled), []
        for task in tasks:
            handler = self._handlers.get(task.type)
            if handler is None:
                continue
            await handler.handle(task)

    def reset(self) -> None:
        self._scheduled.clear()

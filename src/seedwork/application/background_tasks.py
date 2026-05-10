from datetime import datetime
from typing import Any, Literal, Protocol, TypeVar

TaskStatus = Literal["pending", "running", "completed", "failed"]


class BackgroundTask(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def type(self) -> str: ...  # 'domain.action_name'

    @property
    def payload(self) -> dict[str, Any]: ...  # solo primitivos

    @property
    def status(self) -> TaskStatus: ...

    @property
    def scheduled_at(self) -> datetime: ...

    @property
    def started_at(self) -> datetime | None: ...

    @property
    def completed_at(self) -> datetime | None: ...

    @property
    def attempts(self) -> int: ...

    @property
    def max_attempts(self) -> int: ...

    @property
    def last_error(self) -> str | None: ...

    @property
    def correlation_id(self) -> str: ...  # obligatorio

    @property
    def causation_id(self) -> str | None: ...


TTask_contra = TypeVar("TTask_contra", bound=BackgroundTask, contravariant=True)


class TaskQueue(Protocol):
    async def enqueue(self, task: BackgroundTask) -> None: ...

    async def dequeue(self) -> BackgroundTask | None: ...  # claim atómico

    async def ack(self, task_id: str) -> None: ...

    async def nack(self, task_id: str, error: str) -> None: ...

    async def find_by_id(self, task_id: str) -> BackgroundTask | None: ...


class TaskHandler(Protocol[TTask_contra]):
    async def handle(self, task: TTask_contra) -> None: ...


class TaskBus(Protocol):
    async def dispatch(self, task: BackgroundTask) -> None: ...

    def register(self, task_type: str, handler: "TaskHandler[Any]") -> None: ...

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from seedwork.application.background_tasks import BackgroundTask
from seedwork.application.integration_events import IntegrationEvent

OutboxStatus = Literal["pending", "published", "failed"]
TaskOutboxStatus = Literal["pending", "delivered", "failed"]


@dataclass(frozen=True, kw_only=True)
class IntegrationEventOutboxRecord:
    id: str
    event: IntegrationEvent
    status: OutboxStatus
    attempts: int
    created_at: datetime
    last_error: str | None = None
    published_at: datetime | None = None


class IntegrationEventOutboxRepository(Protocol):
    async def save(self, event: IntegrationEvent) -> None: ...

    async def find_pending(self, limit: int = 100) -> Sequence[IntegrationEventOutboxRecord]: ...

    async def mark_as_published(self, id: str) -> None: ...

    async def mark_as_failed(self, id: str, error: str) -> None: ...


class OutboxIntegrationEventPublisher:
    def __init__(self, repository: IntegrationEventOutboxRepository) -> None:
        self._repository = repository

    async def publish(self, events: Sequence[IntegrationEvent]) -> None:
        for event in events:
            await self._repository.save(event)


@dataclass(frozen=True, kw_only=True)
class TaskOutboxRecord:
    id: str
    task: BackgroundTask
    status: TaskOutboxStatus
    attempts: int
    created_at: datetime
    last_error: str | None = None
    delivered_at: datetime | None = None


class TaskOutboxRepository(Protocol):
    async def save(self, task: BackgroundTask) -> None: ...

    async def find_pending(self, limit: int = 100) -> Sequence[TaskOutboxRecord]: ...

    async def mark_as_delivered(self, id: str) -> None: ...

    async def mark_as_failed(self, id: str, error: str) -> None: ...


class OutboxTaskScheduler:
    def __init__(self, repository: TaskOutboxRepository) -> None:
        self._repository = repository

    async def schedule(self, task: BackgroundTask) -> None:
        await self._repository.save(task)

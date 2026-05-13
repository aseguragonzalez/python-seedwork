from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import uuid4

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


class IntegrationEventOutboxRepositorySpy(IntegrationEventOutboxRepository, Protocol):
    @property
    def all(self) -> Sequence[IntegrationEventOutboxRecord]: ...

    def reset(self) -> None: ...


class OutboxIntegrationEventPublisher:
    def __init__(self, repository: IntegrationEventOutboxRepository) -> None:
        self._repository = repository

    async def publish(self, events: Sequence[IntegrationEvent]) -> None:
        for event in events:
            await self._repository.save(event)


class InMemoryIntegrationEventOutboxRepository:
    def __init__(self) -> None:
        self._records: dict[str, IntegrationEventOutboxRecord] = {}

    @property
    def all(self) -> Sequence[IntegrationEventOutboxRecord]:
        return list(self._records.values())

    async def save(self, event: IntegrationEvent) -> None:
        record = IntegrationEventOutboxRecord(
            id=str(uuid4()),
            event=event,
            status="pending",
            attempts=0,
            created_at=datetime.now(UTC),
        )
        self._records[record.id] = record

    async def find_pending(self, limit: int = 100) -> Sequence[IntegrationEventOutboxRecord]:
        pending = [r for r in self._records.values() if r.status == "pending"]
        return pending[:limit]

    async def mark_as_published(self, id: str) -> None:
        r = self._records.get(id)
        if r:
            self._records[id] = replace(r, status="published", published_at=datetime.now(UTC))

    async def mark_as_failed(self, id: str, error: str) -> None:
        r = self._records.get(id)
        if r:
            self._records[id] = replace(
                r, status="failed", attempts=r.attempts + 1, last_error=error
            )

    def reset(self) -> None:
        self._records.clear()


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


class TaskOutboxRepositorySpy(TaskOutboxRepository, Protocol):
    @property
    def all(self) -> Sequence[TaskOutboxRecord]: ...

    def reset(self) -> None: ...


class OutboxTaskScheduler:
    def __init__(self, repository: TaskOutboxRepository) -> None:
        self._repository = repository

    async def schedule(self, task: BackgroundTask) -> None:
        await self._repository.save(task)


class InMemoryTaskOutboxRepository:
    def __init__(self) -> None:
        self._records: dict[str, TaskOutboxRecord] = {}

    @property
    def all(self) -> Sequence[TaskOutboxRecord]:
        return list(self._records.values())

    async def save(self, task: BackgroundTask) -> None:
        record = TaskOutboxRecord(
            id=str(uuid4()),
            task=task,
            status="pending",
            attempts=0,
            created_at=datetime.now(UTC),
        )
        self._records[record.id] = record

    async def find_pending(self, limit: int = 100) -> Sequence[TaskOutboxRecord]:
        pending = [r for r in self._records.values() if r.status == "pending"]
        return pending[:limit]

    async def mark_as_delivered(self, id: str) -> None:
        r = self._records.get(id)
        if r:
            self._records[id] = replace(r, status="delivered", delivered_at=datetime.now(UTC))

    async def mark_as_failed(self, id: str, error: str) -> None:
        r = self._records.get(id)
        if r:
            self._records[id] = replace(
                r, status="failed", attempts=r.attempts + 1, last_error=error
            )

    def reset(self) -> None:
        self._records.clear()

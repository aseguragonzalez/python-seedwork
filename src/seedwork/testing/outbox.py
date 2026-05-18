from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from seedwork.application.background_tasks import BackgroundTask
from seedwork.application.integration_events import IntegrationEvent
from seedwork.infrastructure.outbox import (
    IntegrationEventOutboxRecord,
    IntegrationEventOutboxRepository,
    TaskOutboxRecord,
    TaskOutboxRepository,
)


class IntegrationEventOutboxRepositorySpy(IntegrationEventOutboxRepository, Protocol):
    @property
    def all(self) -> Sequence[IntegrationEventOutboxRecord]: ...

    def reset(self) -> None: ...


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


class TaskOutboxRepositorySpy(TaskOutboxRepository, Protocol):
    @property
    def all(self) -> Sequence[TaskOutboxRecord]: ...

    def reset(self) -> None: ...


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

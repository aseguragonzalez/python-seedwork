from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from seedwork.application.integration_events import IntegrationEvent
from seedwork.application.outbox import OutboxRecord, OutboxRepository


class OutboxIntegrationEventPublisher:
    def __init__(self, repository: OutboxRepository) -> None:
        self._repository = repository

    async def publish(self, events: Sequence[IntegrationEvent]) -> None:
        for event in events:
            await self._repository.save(event)


class InMemoryOutboxRepository:
    def __init__(self) -> None:
        self._records: dict[str, OutboxRecord] = {}

    async def save(self, event: IntegrationEvent) -> None:
        record = OutboxRecord(
            id=str(uuid4()),
            event=event,
            status="pending",
            attempts=0,
            created_at=datetime.now(UTC),
        )
        self._records[record.id] = record

    async def find_pending(self, limit: int = 100) -> Sequence[OutboxRecord]:
        pending = [r for r in self._records.values() if r.status == "pending"]
        return pending[:limit]

    async def mark_as_published(self, id: str) -> None:
        record = self._records.get(id)
        if record:
            self._records[id] = replace(record, status="published", published_at=datetime.now(UTC))

    async def mark_as_failed(self, id: str, error: str) -> None:
        record = self._records.get(id)
        if record:
            self._records[id] = replace(
                record,
                status="failed",
                attempts=record.attempts + 1,
                last_error=error,
            )

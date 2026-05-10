from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from seedwork.application.integration_events import IntegrationEvent

OutboxStatus = Literal["pending", "published", "failed"]


@dataclass(frozen=True, kw_only=True)
class OutboxRecord:
    id: str  # record ID, distinto de event.id
    event: IntegrationEvent
    status: OutboxStatus
    attempts: int
    created_at: datetime
    last_error: str | None = None
    published_at: datetime | None = None


class OutboxRepository(Protocol):
    async def save(self, event: IntegrationEvent) -> None: ...

    async def find_pending(self, limit: int = 100) -> Sequence[OutboxRecord]: ...

    async def mark_as_published(self, id: str) -> None: ...

    async def mark_as_failed(self, id: str, error: str) -> None: ...

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


class DomainEvent(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def occurred_at(self) -> datetime: ...


@dataclass(frozen=True, kw_only=True)
class DomainEventRecord[TPayload]:
    payload: TPayload
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

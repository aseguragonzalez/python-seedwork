from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


class DomainEvent(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def occurred_at(self) -> datetime: ...

    @property
    def aggregate_id(self) -> str: ...


@dataclass(frozen=True, kw_only=True)
class BaseDomainEvent[TPayload]:
    payload: TPayload
    aggregate_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class BaseIntegrationEvent[TPayload_co]:
    type: str
    version: str
    aggregate_id: str
    payload: TPayload_co
    correlation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    causation_id: str | None = None
    metadata: dict[str, str] | None = None


class IntegrationEvent[TPayload_co](Protocol):
    @property
    def id(self) -> str: ...

    @property
    def type(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def occurred_at(self) -> datetime: ...

    @property
    def aggregate_id(self) -> str: ...

    @property
    def payload(self) -> TPayload_co: ...

    @property
    def correlation_id(self) -> str: ...

    @property
    def causation_id(self) -> str | None: ...

    @property
    def metadata(self) -> dict[str, str] | None: ...


class IntegrationEventPublisher(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent[Any]]) -> None: ...


class IntegrationEventHandler[TIntegrationEvent_contra: IntegrationEvent[Any]](Protocol):
    async def handle(self, event: TIntegrationEvent_contra) -> None: ...

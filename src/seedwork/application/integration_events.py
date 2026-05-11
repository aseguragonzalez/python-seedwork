from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar
from uuid import uuid4


class IntegrationEvent(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def type(self) -> str: ...  # 'bc.aggregate.event_name'

    @property
    def version(self) -> str: ...  # '1.0'

    @property
    def occurred_at(self) -> datetime: ...

    @property
    def aggregate_id(self) -> str: ...

    @property
    def payload(self) -> dict[str, Any]: ...  # solo primitivos serializables

    @property
    def correlation_id(self) -> str: ...  # obligatorio

    @property
    def causation_id(self) -> str | None: ...

    @property
    def metadata(self) -> dict[str, str] | None: ...  # traceparent, tenant_id, etc.


TIntegrationEvent_contra = TypeVar(
    "TIntegrationEvent_contra", bound=IntegrationEvent, contravariant=True
)


@dataclass(frozen=True, kw_only=True)
class IntegrationEventRecord:
    type: str
    version: str
    aggregate_id: str
    payload: dict[str, Any]
    correlation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    causation_id: str | None = None
    metadata: dict[str, str] | None = None


class IntegrationEventPublisher(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent]) -> None: ...


class IntegrationEventHandler(Protocol[TIntegrationEvent_contra]):
    async def handle(self, event: TIntegrationEvent_contra) -> None: ...

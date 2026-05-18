from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar, runtime_checkable
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class BaseIntegrationEvent:
    type: str
    version: str
    aggregate_id: str
    payload: dict[str, Any]
    correlation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    causation_id: str | None = None
    metadata: dict[str, str] | None = None


class IntegrationEvent(Protocol):
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
    def payload(self) -> dict[str, Any]: ...

    @property
    def correlation_id(self) -> str: ...

    @property
    def causation_id(self) -> str | None: ...

    @property
    def metadata(self) -> dict[str, str] | None: ...


TIntegrationEvent_contra = TypeVar(
    "TIntegrationEvent_contra", bound=IntegrationEvent, contravariant=True
)


class IntegrationEventPublisher(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent]) -> None: ...


@runtime_checkable
class IntegrationEventPublisherSpy(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent]) -> None: ...

    @property
    def published(self) -> Sequence[IntegrationEvent]: ...

    def reset(self) -> None: ...


class IntegrationEventHandler(Protocol[TIntegrationEvent_contra]):
    async def handle(self, event: TIntegrationEvent_contra) -> None: ...

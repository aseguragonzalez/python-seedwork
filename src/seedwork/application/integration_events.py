from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol, TypeVar


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


class IntegrationEventPublisherSpy(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent]) -> None: ...

    @property
    def published(self) -> Sequence[IntegrationEvent]: ...

    def reset(self) -> None: ...


class IntegrationEventHandler(Protocol[TIntegrationEvent_contra]):
    async def handle(self, event: TIntegrationEvent_contra) -> None: ...

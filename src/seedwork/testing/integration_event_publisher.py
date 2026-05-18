from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from seedwork.application.integration_events import IntegrationEvent


@runtime_checkable
class IntegrationEventPublisherSpy(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent]) -> None: ...

    @property
    def published(self) -> Sequence[IntegrationEvent]: ...

    def reset(self) -> None: ...


class InMemoryIntegrationEventPublisher:
    def __init__(self) -> None:
        self._published: list[IntegrationEvent] = []

    @property
    def published(self) -> Sequence[IntegrationEvent]:
        return list(self._published)

    async def publish(self, events: Sequence[IntegrationEvent]) -> None:
        self._published.extend(events)

    def reset(self) -> None:
        self._published.clear()

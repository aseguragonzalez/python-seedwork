from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from seedwork.application.integration_events import IntegrationEvent


@runtime_checkable
class IntegrationEventPublisherSpy(Protocol):
    async def publish(self, events: Sequence[IntegrationEvent[Any]]) -> None: ...

    @property
    def published(self) -> Sequence[IntegrationEvent[Any]]: ...

    def reset(self) -> None: ...


class InMemoryIntegrationEventPublisher:
    def __init__(self) -> None:
        self._published: list[IntegrationEvent[Any]] = []

    @property
    def published(self) -> Sequence[IntegrationEvent[Any]]:
        return list(self._published)

    async def publish(self, events: Sequence[IntegrationEvent[Any]]) -> None:
        self._published.extend(events)

    def reset(self) -> None:
        self._published.clear()

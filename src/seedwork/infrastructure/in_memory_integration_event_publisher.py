from collections.abc import Sequence

from seedwork.application.integration_events import IntegrationEvent


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

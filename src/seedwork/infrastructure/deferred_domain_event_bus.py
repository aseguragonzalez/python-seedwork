from collections import defaultdict
from collections.abc import Sequence
from typing import TypeVar

from seedwork.application.domain_events import DomainEventHandler
from seedwork.domain.domain_event import DomainEvent

TEvent_contra = TypeVar("TEvent_contra", bound=DomainEvent, contravariant=True)


class DeferredDomainEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[DomainEventHandler[DomainEvent]]] = (
            defaultdict(list)
        )
        self._pending: list[DomainEvent] = []

    def subscribe(
        self,
        event_type: type[TEvent_contra],
        handler: DomainEventHandler[TEvent_contra],
    ) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    async def publish(self, events: Sequence[DomainEvent]) -> None:
        self._pending.extend(events)

    async def flush(self) -> None:
        events, self._pending = self._pending, []
        for event in events:
            for handler in self._handlers.get(type(event), []):
                await handler.handle(event)

    def clear(self) -> None:
        self._pending.clear()

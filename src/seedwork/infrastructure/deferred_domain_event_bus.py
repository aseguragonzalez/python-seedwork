from collections import defaultdict
from collections.abc import Sequence
from typing import TypeVar

from seedwork.application.domain_event_bus import DomainEventHandler
from seedwork.domain.domain_event import DomainEvent

TEvent_contra = TypeVar("TEvent_contra", bound=DomainEvent, contravariant=True)


class DeferredDomainEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[DomainEventHandler[DomainEvent]]] = (
            defaultdict(list)
        )
        self._pending: dict[str, DomainEvent] = {}

    def subscribe(
        self,
        event_type: type[TEvent_contra],
        handler: DomainEventHandler[TEvent_contra],
    ) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    async def publish(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            if event.id not in self._pending:
                self._pending[event.id] = event

    async def dispatch(self) -> None:
        events = list(self._pending.values())
        self._pending.clear()
        for event in events:
            for handler in self._handlers.get(type(event), []):
                await handler.handle(event)

    def discard(self) -> None:
        self._pending.clear()

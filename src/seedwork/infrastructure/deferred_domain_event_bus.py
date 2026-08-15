from collections import defaultdict
from collections.abc import Sequence
from contextvars import ContextVar

from seedwork.application.domain_event_bus import DomainEventHandler
from seedwork.domain.domain_event import DomainEvent


class DeferredDomainEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[DomainEventHandler[DomainEvent]]] = (
            defaultdict(list)
        )
        self._pending: ContextVar[dict[str, DomainEvent]] = ContextVar(
            "deferred_domain_event_bus_pending"
        )

    def _pending_events(self) -> dict[str, DomainEvent]:
        try:
            return self._pending.get()
        except LookupError:
            pending: dict[str, DomainEvent] = {}
            self._pending.set(pending)
            return pending

    def subscribe[TEvent: DomainEvent](
        self,
        event_type: type[TEvent],
        handler: DomainEventHandler[TEvent],
    ) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    async def publish(self, events: Sequence[DomainEvent]) -> None:
        pending = self._pending_events()
        for event in events:
            if event.id not in pending:
                pending[event.id] = event

    async def dispatch(self) -> None:
        pending = self._pending_events()
        events = list(pending.values())
        pending.clear()
        for event in events:
            for handler in self._handlers.get(type(event), []):
                await handler.handle(event)

    def discard(self) -> None:
        self._pending_events().clear()

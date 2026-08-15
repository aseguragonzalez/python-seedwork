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
        # A task spawned after _pending is set inherits a reference to the
        # same dict, not a copy. Mutating it in place would leak across
        # contexts, so every write below replaces it via ContextVar.set(...)
        # instead of mutating this returned dict.
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
        pending = dict(self._pending_events())
        for event in events:
            if event.id not in pending:
                pending[event.id] = event
        self._pending.set(pending)

    async def dispatch(self) -> None:
        events = list(self._pending_events().values())
        self._pending.set({})
        for event in events:
            for handler in self._handlers.get(type(event), []):
                await handler.handle(event)

    def discard(self) -> None:
        self._pending.set({})

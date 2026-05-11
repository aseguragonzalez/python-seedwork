from collections.abc import Sequence
from typing import Protocol, TypeVar

from seedwork.domain.domain_event import DomainEvent

TEvent_contra = TypeVar("TEvent_contra", bound=DomainEvent, contravariant=True)


class DomainEventBusPublisher(Protocol):
    async def publish(self, events: Sequence[DomainEvent]) -> None: ...


class DomainEventHandler(Protocol[TEvent_contra]):
    async def handle(self, event: TEvent_contra) -> None: ...


class DomainEventBusSubscriber(Protocol):
    def subscribe(
        self,
        event_type: type[TEvent_contra],
        handler: "DomainEventHandler[TEvent_contra]",
    ) -> None: ...


class DomainEventBus(DomainEventBusPublisher, DomainEventBusSubscriber, Protocol):
    async def dispatch(self) -> None: ...

    def discard(self) -> None: ...


# Kept for backwards compatibility — alias to DomainEventBusPublisher
DomainEventPublisher = DomainEventBusPublisher

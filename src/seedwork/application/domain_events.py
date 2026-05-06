from collections.abc import Sequence
from typing import Protocol, TypeVar

from seedwork.domain.domain_event import DomainEvent

TEvent_contra = TypeVar("TEvent_contra", bound=DomainEvent, contravariant=True)


class DomainEventPublisher(Protocol):
    async def publish(self, events: Sequence[DomainEvent]) -> None: ...


class DomainEventHandler(Protocol[TEvent_contra]):
    async def handle(self, event: TEvent_contra) -> None: ...

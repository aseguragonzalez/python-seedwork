from dataclasses import dataclass, field
from typing import Self

from seedwork.domain.domain_event import DomainEvent
from seedwork.domain.entity import Entity


@dataclass(frozen=True, eq=False, kw_only=True)
class AggregateRoot[TId](Entity[TId]):
    domain_events: tuple[DomainEvent, ...] = field(
        default=(), repr=False, hash=False, compare=False
    )

    def _record(self, *events: DomainEvent) -> Self:
        return self._evolve(domain_events=(*self.domain_events, *events))

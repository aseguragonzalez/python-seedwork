from typing import Any

from seedwork.application.domain_events import DomainEventPublisher
from seedwork.domain.aggregate_root import AggregateRoot
from seedwork.domain.repository import Repository


class DomainEventPublishingRepository[TId, TAggregate: AggregateRoot[Any]]:
    def __init__(
        self,
        inner: Repository[TId, TAggregate],
        publisher: DomainEventPublisher,
    ) -> None:
        self._inner = inner
        self._publisher = publisher

    async def find_by_id(self, entity_id: TId) -> TAggregate | None:
        return await self._inner.find_by_id(entity_id)

    async def save(self, aggregate: TAggregate) -> None:
        await self._inner.save(aggregate)
        if aggregate.domain_events:
            await self._publisher.publish(aggregate.domain_events)

    async def delete_by_id(self, entity_id: TId) -> None:
        await self._inner.delete_by_id(entity_id)

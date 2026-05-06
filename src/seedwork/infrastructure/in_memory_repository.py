from collections.abc import Hashable
from typing import Any, cast

from seedwork.domain.aggregate_root import AggregateRoot


class InMemoryRepository[TId: Hashable, TAggregate: AggregateRoot[Any]]:
    def __init__(self) -> None:
        self._store: dict[TId, TAggregate] = {}

    async def find_by_id(self, entity_id: TId) -> TAggregate | None:
        return self._store.get(entity_id)

    async def save(self, aggregate: TAggregate) -> None:
        self._store[cast(TId, aggregate.id)] = aggregate

    async def delete_by_id(self, entity_id: TId) -> None:
        self._store.pop(entity_id, None)

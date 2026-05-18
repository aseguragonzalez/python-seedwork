from collections.abc import Hashable, Sequence
from typing import Any, Protocol, cast, runtime_checkable

from seedwork.domain.aggregate_root import AggregateRoot
from seedwork.domain.repository import Repository


@runtime_checkable
class RepositorySpy[TId: Hashable, TAggregate: AggregateRoot[Any]](
    Repository[TId, TAggregate], Protocol
):
    @property
    def all(self) -> Sequence[TAggregate]: ...

    def reset(self) -> None: ...


class InMemoryRepository[TId: Hashable, TAggregate: AggregateRoot[Any]]:
    def __init__(self) -> None:
        self._store: dict[TId, TAggregate] = {}

    async def find_by_id(self, entity_id: TId) -> TAggregate | None:
        return self._store.get(entity_id)

    async def save(self, aggregate: TAggregate) -> None:
        self._store[cast(TId, aggregate.id)] = aggregate

    async def delete_by_id(self, entity_id: TId) -> None:
        self._store.pop(entity_id, None)

    @property
    def all(self) -> Sequence[TAggregate]:
        return list(self._store.values())

    def reset(self) -> None:
        self._store.clear()

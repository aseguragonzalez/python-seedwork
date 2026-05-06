from typing import Any, Protocol, TypeVar

from seedwork.domain.aggregate_root import AggregateRoot

TId_contra = TypeVar("TId_contra", contravariant=True)
TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any])


class Repository(Protocol[TId_contra, TAggregate]):
    async def find_by_id(self, entity_id: TId_contra) -> TAggregate | None: ...
    async def save(self, aggregate: TAggregate) -> None: ...
    async def delete_by_id(self, entity_id: TId_contra) -> None: ...

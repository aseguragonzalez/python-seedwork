from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

TQuery_contra = TypeVar("TQuery_contra", bound="Query[Any]", contravariant=True)
TResult_co = TypeVar("TResult_co", covariant=True)


@dataclass(frozen=True, kw_only=True)
class Query[TResult]: ...


class QueryHandler(Protocol[TQuery_contra, TResult_co]):
    async def execute(self, query: TQuery_contra) -> TResult_co | None: ...


class QueryBus(Protocol):
    async def ask[TResult](self, query: Query[TResult]) -> TResult | None: ...

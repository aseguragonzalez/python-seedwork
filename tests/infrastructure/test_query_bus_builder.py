from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from seedwork.application.queries import Query, QueryBus, QueryHandler
from seedwork.infrastructure.query_bus_builder import QueryBusBuilder
from seedwork.infrastructure.registry_query_bus import RegistryQueryBus


@dataclass
class AccountDto:
    account_id: str


@dataclass(frozen=True, kw_only=True)
class GetAccountQuery(Query[AccountDto]):
    account_id: str


class GetAccountHandler(QueryHandler[GetAccountQuery, AccountDto]):
    async def handle(self, query: GetAccountQuery) -> AccountDto | None:
        return AccountDto(query.account_id)


async def test_builder_returns_result() -> None:
    bus = QueryBusBuilder(RegistryQueryBus()).register(GetAccountQuery, GetAccountHandler()).build()
    result = await bus.ask(GetAccountQuery(account_id="acc-1"))
    assert result is not None
    assert result.account_id == "acc-1"


async def test_builder_middleware_order() -> None:
    calls: list[str] = []

    def make_middleware(name: str) -> Callable[[QueryBus], QueryBus]:
        def middleware(inner: QueryBus) -> QueryBus:
            class WrappedBus:
                async def ask(self, query: Query[Any]) -> Any:
                    calls.append(name)
                    return await inner.ask(query)

            return WrappedBus()

        return middleware

    bus = (
        QueryBusBuilder(RegistryQueryBus())
        .register(GetAccountQuery, GetAccountHandler())
        .use(make_middleware("first"))
        .use(make_middleware("second"))
        .build()
    )
    await bus.ask(GetAccountQuery(account_id="acc-1"))
    assert calls == ["first", "second"]

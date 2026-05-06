from dataclasses import dataclass

import pytest

from seedwork.application.queries import Query, QueryHandler
from seedwork.infrastructure.registry_query_bus import RegistryQueryBus


@dataclass
class AccountDto:
    account_id: str


@dataclass(frozen=True, kw_only=True)
class GetAccountQuery(Query[AccountDto]):
    account_id: str


class GetAccountHandler(QueryHandler[GetAccountQuery, AccountDto]):
    async def execute(self, query: GetAccountQuery) -> AccountDto | None:
        return AccountDto(query.account_id)


class GetMissingHandler(QueryHandler[GetAccountQuery, AccountDto]):
    async def execute(self, query: GetAccountQuery) -> AccountDto | None:
        return None


async def test_ask_returns_result_when_found() -> None:
    bus = RegistryQueryBus()
    bus.register(GetAccountQuery, GetAccountHandler())
    result = await bus.ask(GetAccountQuery(account_id="acc-1"))
    assert result is not None
    assert result.account_id == "acc-1"


async def test_ask_returns_none_when_not_found() -> None:
    bus = RegistryQueryBus()
    bus.register(GetAccountQuery, GetMissingHandler())
    result = await bus.ask(GetAccountQuery(account_id="acc-1"))
    assert result is None


async def test_ask_without_handler_raises() -> None:
    bus = RegistryQueryBus()
    with pytest.raises(KeyError):
        await bus.ask(GetAccountQuery(account_id="acc-1"))

from bank_account.application.get_balance.balance_response import BalanceResponse
from bank_account.application.get_balance.get_balance_handler import GetBalanceHandler
from bank_account.application.get_balance.get_balance_query import GetBalanceQuery


class InMemoryBankAccountReadRepository:
    def __init__(self, data: dict[str, BalanceResponse]) -> None:
        self._data = data

    async def find_balance(self, account_id: str) -> BalanceResponse | None:
        return self._data.get(account_id)


async def test_get_balance_returns_balance_when_account_exists() -> None:
    repo = InMemoryBankAccountReadRepository(
        {"acc-1": BalanceResponse(account_id="acc-1", balance=100.0, currency="EUR")}
    )
    result = await GetBalanceHandler(repo).handle(GetBalanceQuery(account_id="acc-1"))
    assert result == BalanceResponse(account_id="acc-1", balance=100.0, currency="EUR")


async def test_get_balance_returns_none_when_account_not_found() -> None:
    repo = InMemoryBankAccountReadRepository({})
    result = await GetBalanceHandler(repo).handle(GetBalanceQuery(account_id="acc-1"))
    assert result is None

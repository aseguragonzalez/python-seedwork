from bank_account.application.get_balance.balance_response import BalanceResponse
from bank_account.application.get_balance.bank_account_read_repository import (
    BankAccountReadRepository,
)
from bank_account.application.get_balance.get_balance_query import GetBalanceQuery

from seedwork.application.queries import QueryHandler


class GetBalanceHandler(QueryHandler[GetBalanceQuery, BalanceResponse]):
    def __init__(self, repository: BankAccountReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetBalanceQuery) -> BalanceResponse | None:
        return await self._repository.find_balance(query.account_id)

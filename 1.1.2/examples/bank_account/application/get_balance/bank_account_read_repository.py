from typing import Protocol

from bank_account.application.get_balance.balance_response import BalanceResponse


class BankAccountReadRepository(Protocol):
    async def find_balance(self, account_id: str) -> BalanceResponse | None: ...

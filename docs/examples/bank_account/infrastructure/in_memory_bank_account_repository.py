from bank_account.application.get_balance.balance_response import BalanceResponse
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.bank_account_repository import BankAccountRepository

from seedwork.infrastructure import InMemoryRepository


class InMemoryBankAccountRepository(
    InMemoryRepository[BankAccountId, BankAccount],
    BankAccountRepository,
):
    async def find_balance(self, account_id: str) -> BalanceResponse | None:
        account = await self.find_by_id(BankAccountId(account_id))
        if account is None:
            return None
        return BalanceResponse(
            account_id=account_id,
            balance=account.balance.amount,
            currency=account.balance.currency,
        )

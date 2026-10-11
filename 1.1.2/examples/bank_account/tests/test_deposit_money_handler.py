import pytest
from bank_account.application.deposit_money.deposit_money_command import DepositMoneyCommand
from bank_account.application.deposit_money.deposit_money_handler import DepositMoneyHandler
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.errors import AccountNotFoundError
from bank_account.domain.money import Money
from bank_account.domain.user_id import UserId
from bank_account.infrastructure.in_memory_bank_account_repository import (
    InMemoryBankAccountRepository,
)


async def test_deposit_increases_balance() -> None:
    repo = InMemoryBankAccountRepository()
    account = BankAccount.open(
        id=BankAccountId("acc-1"),
        owner_id=UserId("user-1"),
        initial_balance=Money(amount=100.0, currency="EUR"),
    )
    await repo.save(account)

    handler = DepositMoneyHandler(repo)
    await handler.handle(DepositMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR"))

    updated = await repo.find_by_id(BankAccountId("acc-1"))
    assert updated is not None
    assert updated.balance == Money(amount=150.0, currency="EUR")


async def test_deposit_on_nonexistent_account_raises() -> None:
    repo = InMemoryBankAccountRepository()
    handler = DepositMoneyHandler(repo)

    with pytest.raises(AccountNotFoundError):
        await handler.handle(DepositMoneyCommand(account_id="ghost", amount=10.0, currency="EUR"))

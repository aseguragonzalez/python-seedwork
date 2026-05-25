import pytest
from bank_account.application.withdraw_money.withdraw_money_command import WithdrawMoneyCommand
from bank_account.application.withdraw_money.withdraw_money_handler import WithdrawMoneyHandler
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.errors import AccountNotFoundError, InsufficientFundsError
from bank_account.domain.money import Money
from bank_account.domain.user_id import UserId
from bank_account.infrastructure.in_memory_bank_account_repository import (
    InMemoryBankAccountRepository,
)


async def test_withdraw_decreases_balance() -> None:
    repo = InMemoryBankAccountRepository()
    account = BankAccount.open(
        id=BankAccountId("acc-1"),
        owner_id=UserId("user-1"),
        initial_balance=Money(amount=200.0, currency="EUR"),
    )
    await repo.save(account)

    handler = WithdrawMoneyHandler(repo)
    await handler.handle(WithdrawMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR"))

    updated = await repo.find_by_id(BankAccountId("acc-1"))
    assert updated is not None
    assert updated.balance == Money(amount=150.0, currency="EUR")


async def test_withdraw_on_nonexistent_account_raises() -> None:
    repo = InMemoryBankAccountRepository()
    handler = WithdrawMoneyHandler(repo)

    with pytest.raises(AccountNotFoundError):
        await handler.handle(WithdrawMoneyCommand(account_id="ghost", amount=10.0, currency="EUR"))


async def test_withdraw_insufficient_funds_raises() -> None:
    repo = InMemoryBankAccountRepository()
    account = BankAccount.open(
        id=BankAccountId("acc-1"),
        owner_id=UserId("user-1"),
        initial_balance=Money(amount=30.0, currency="EUR"),
    )
    await repo.save(account)

    handler = WithdrawMoneyHandler(repo)

    with pytest.raises(InsufficientFundsError):
        await handler.handle(WithdrawMoneyCommand(account_id="acc-1", amount=100.0, currency="EUR"))

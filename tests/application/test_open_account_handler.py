from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.open_account.open_account_handler import OpenAccountHandler
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.money import Money

from seedwork.testing import InMemoryRepository


class BankAccountInMemoryRepository(InMemoryRepository[BankAccountId, BankAccount]):
    pass


async def test_open_account_saves_account_with_initial_balance() -> None:
    repo = BankAccountInMemoryRepository()
    handler = OpenAccountHandler(repo)

    await handler.handle(
        OpenAccountCommand(account_id="acc-1", initial_balance=100.0, currency="EUR")
    )

    account = await repo.find_by_id(BankAccountId("acc-1"))
    assert account is not None
    assert account.balance == Money(amount=100.0, currency="EUR")


async def test_open_account_records_domain_event() -> None:
    repo = BankAccountInMemoryRepository()
    handler = OpenAccountHandler(repo)

    await handler.handle(
        OpenAccountCommand(account_id="acc-2", initial_balance=50.0, currency="USD")
    )

    account = await repo.find_by_id(BankAccountId("acc-2"))
    assert account is not None
    assert len(account.domain_events) == 1

from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.open_account.open_account_handler import OpenAccountHandler
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.bank_account_repository import BankAccountRepository
from bank_account.domain.events.account_opened import AccountOpened
from bank_account.domain.money import Money
from bank_account.infrastructure.in_memory_bank_account_repository import (
    InMemoryBankAccountRepository,
)

from seedwork.infrastructure import DeferredDomainEventBus, DomainEventPublishingRepository


async def test_open_account_saves_account_with_initial_balance() -> None:
    inner_repo = InMemoryBankAccountRepository()
    event_bus = DeferredDomainEventBus()
    repo: BankAccountRepository = DomainEventPublishingRepository(inner_repo, event_bus)
    handler = OpenAccountHandler(repo)

    await handler.handle(
        OpenAccountCommand(account_id="acc-1", initial_balance=100.0, currency="EUR")
    )

    account = await inner_repo.find_by_id(BankAccountId("acc-1"))
    assert account is not None
    assert account.balance == Money(amount=100.0, currency="EUR")


async def test_open_account_dispatches_account_opened_event() -> None:
    published: list[AccountOpened] = []

    from seedwork.application import DomainEventHandler

    class SpyHandler(DomainEventHandler[AccountOpened]):
        async def handle(self, event: AccountOpened) -> None:
            published.append(event)

    inner_repo = InMemoryBankAccountRepository()
    event_bus = DeferredDomainEventBus()
    event_bus.subscribe(AccountOpened, SpyHandler())
    repo: BankAccountRepository = DomainEventPublishingRepository(inner_repo, event_bus)
    handler = OpenAccountHandler(repo)

    await handler.handle(
        OpenAccountCommand(account_id="acc-3", initial_balance=200.0, currency="EUR")
    )
    await event_bus.dispatch()

    assert len(published) == 1
    assert isinstance(published[0], AccountOpened)

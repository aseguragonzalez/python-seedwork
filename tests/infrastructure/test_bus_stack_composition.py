"""
Integration test showing the recommended bus stack composition:
    Validation > Transactional > DomainEventCoordinator > RegistryCommandBus
"""

from types import TracebackType
from typing import Self

from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.open_account.open_account_handler import OpenAccountHandler
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId

from seedwork.infrastructure.command_bus_builder import CommandBusBuilder
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus
from seedwork.infrastructure.in_memory_repository import InMemoryRepository


class BankAccountInMemoryRepository(InMemoryRepository[BankAccountId, BankAccount]):
    pass


class FakeUnitOfWork:
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass


async def test_full_bus_stack_dispatches_command() -> None:
    repo = BankAccountInMemoryRepository()
    event_bus = DeferredDomainEventBus()
    uow = FakeUnitOfWork()

    bus = (
        CommandBusBuilder()
        .register(OpenAccountCommand, OpenAccountHandler(repo))
        .with_transaction(uow)
        .with_domain_event_coordination(event_bus)
        .build()
    )

    result = await bus.dispatch(
        OpenAccountCommand(account_id="acc-1", initial_balance=200.0, currency="EUR")
    )

    assert result.ok
    account = await repo.find_by_id(BankAccountId("acc-1"))
    assert account is not None


async def test_full_bus_stack_with_legacy_flushing_method() -> None:
    """Backwards-compat: with_domain_event_flushing still works."""
    repo = BankAccountInMemoryRepository()
    event_bus = DeferredDomainEventBus()
    uow = FakeUnitOfWork()

    bus = (
        CommandBusBuilder()
        .register(OpenAccountCommand, OpenAccountHandler(repo))
        .with_transaction(uow)
        .with_domain_event_flushing(event_bus)  # deprecated alias
        .build()
    )

    result = await bus.dispatch(
        OpenAccountCommand(account_id="acc-2", initial_balance=100.0, currency="EUR")
    )

    assert result.ok

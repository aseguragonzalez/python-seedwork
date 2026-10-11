from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Self

import pytest
from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.open_account.open_account_handler import OpenAccountHandler
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.events.account_opened import AccountOpened
from bank_account.domain.money import Money
from bank_account.domain.user_id import UserId

from seedwork.application.commands import CommandBus, CommandHandler
from seedwork.domain.domain_error import DomainError
from seedwork.infrastructure.command_bus_builder import CommandBusBuilder
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus
from seedwork.infrastructure.domain_event_publishing_repository import (
    DomainEventPublishingRepository,
)
from seedwork.infrastructure.registry_command_bus import RegistryCommandBus
from seedwork.testing import InMemoryRepository


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
        CommandBusBuilder(RegistryCommandBus())
        .register(OpenAccountCommand, OpenAccountHandler(repo))
        .with_transaction(uow)
        .with_domain_event_coordination(event_bus)
        .build()
    )

    result = await bus.dispatch(
        OpenAccountCommand(
            account_id="acc-1", owner_id="user-1", initial_balance=200.0, currency="EUR"
        )
    )

    assert result.is_ok
    account = await repo.find_by_id(BankAccountId("acc-1"))
    assert account is not None


class SpyUnitOfWork:
    def __init__(self) -> None:
        self.sessions = 0
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        self.sessions += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commits += 1
        else:
            self.rollbacks += 1


class SpyAccountOpenedHandler:
    def __init__(self) -> None:
        self.handled: list[AccountOpened] = []

    async def handle(self, event: AccountOpened) -> None:
        self.handled.append(event)


class OpenAccountThenHandler(CommandHandler[OpenAccountCommand]):
    """Saves the aggregate (publishing its events), then runs `after_save`."""

    def __init__(
        self,
        repository: DomainEventPublishingRepository[BankAccountId, BankAccount],
        after_save: Callable[[], Awaitable[None]],
    ) -> None:
        self._repository = repository
        self._after_save = after_save

    async def handle(self, command: OpenAccountCommand) -> None:
        account = BankAccount.open(
            id=BankAccountId(command.account_id),
            owner_id=UserId(command.owner_id),
            initial_balance=Money(amount=command.initial_balance, currency=command.currency),
        )
        await self._repository.save(account)
        await self._after_save()


def build_full_stack(
    uow: SpyUnitOfWork,
    event_handler: SpyAccountOpenedHandler,
    after_save: Callable[[], Awaitable[None]],
) -> CommandBus:
    event_bus = DeferredDomainEventBus()
    event_bus.subscribe(AccountOpened, event_handler)
    repository = DomainEventPublishingRepository(BankAccountInMemoryRepository(), event_bus)
    return (
        CommandBusBuilder(RegistryCommandBus())
        .register(OpenAccountCommand, OpenAccountThenHandler(repository, after_save))
        .with_transaction(uow)
        .with_domain_event_coordination(event_bus)
        .build()
    )


OPEN_ACCOUNT = OpenAccountCommand(
    account_id="acc-1", owner_id="user-1", initial_balance=200.0, currency="EUR"
)


async def test_full_stack_rolls_back_when_handler_raises_domain_error_after_save() -> None:
    async def reject() -> None:
        raise DomainError("Rejected after save", "REJECTED")

    uow = SpyUnitOfWork()
    event_handler = SpyAccountOpenedHandler()
    bus = build_full_stack(uow, event_handler, reject)

    result = await bus.dispatch(OPEN_ACCOUNT)

    assert result.is_failed
    assert result.errors[0].code == "REJECTED"
    assert result.errors[0].description == "Rejected after save"
    assert uow.sessions == 1
    assert uow.commits == 0
    assert uow.rollbacks == 1
    assert event_handler.handled == []


async def test_full_stack_commits_and_dispatches_events_when_handler_succeeds() -> None:
    async def succeed() -> None:
        pass

    uow = SpyUnitOfWork()
    event_handler = SpyAccountOpenedHandler()
    bus = build_full_stack(uow, event_handler, succeed)

    result = await bus.dispatch(OPEN_ACCOUNT)

    assert result.is_ok
    assert uow.sessions == 1
    assert uow.commits == 1
    assert uow.rollbacks == 0
    assert len(event_handler.handled) == 1


async def test_full_stack_rolls_back_and_reraises_when_handler_raises_non_domain_error() -> None:
    async def crash() -> None:
        raise RuntimeError("Storage failure")

    uow = SpyUnitOfWork()
    event_handler = SpyAccountOpenedHandler()
    bus = build_full_stack(uow, event_handler, crash)

    with pytest.raises(RuntimeError, match="Storage failure"):
        await bus.dispatch(OPEN_ACCOUNT)

    assert uow.sessions == 1
    assert uow.commits == 0
    assert uow.rollbacks == 1
    assert event_handler.handled == []

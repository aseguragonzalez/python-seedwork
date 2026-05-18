from dataclasses import dataclass

import pytest
from bank_account.domain.errors import InsufficientFundsError

from seedwork.application.commands import Command, CommandHandler
from seedwork.infrastructure.registry_command_bus import RegistryCommandBus


@dataclass(frozen=True, kw_only=True)
class OpenAccountCommand(Command):
    account_id: str


class FailingCommand(Command): ...


class OpenAccountHandler(CommandHandler[OpenAccountCommand]):
    def __init__(self) -> None:
        self.handled_with: OpenAccountCommand | None = None

    async def handle(self, command: OpenAccountCommand) -> None:
        self.handled_with = command


class DomainErrorHandler(CommandHandler[FailingCommand]):
    async def handle(self, command: FailingCommand) -> None:
        raise InsufficientFundsError()


async def test_dispatch_calls_registered_handler() -> None:
    handler = OpenAccountHandler()
    bus = RegistryCommandBus()
    bus.register(OpenAccountCommand, handler)
    command = OpenAccountCommand(account_id="acc-1")
    result = await bus.dispatch(command)
    assert result.is_ok
    assert handler.handled_with is command


async def test_dispatch_without_handler_raises() -> None:
    bus = RegistryCommandBus()
    with pytest.raises(KeyError):
        await bus.dispatch(OpenAccountCommand(account_id="acc-1"))


async def test_dispatch_domain_error_returns_fail_result() -> None:
    bus = RegistryCommandBus()
    bus.register(FailingCommand, DomainErrorHandler())
    result = await bus.dispatch(FailingCommand())
    assert not result.is_ok
    assert result.errors[0].code == "INSUFFICIENT_FUNDS"


async def test_dispatch_non_domain_error_reraises() -> None:
    class BrokenHandler(CommandHandler[FailingCommand]):
        async def handle(self, command: FailingCommand) -> None:
            raise RuntimeError("unexpected")

    bus = RegistryCommandBus()
    bus.register(FailingCommand, BrokenHandler())
    with pytest.raises(RuntimeError):
        await bus.dispatch(FailingCommand())

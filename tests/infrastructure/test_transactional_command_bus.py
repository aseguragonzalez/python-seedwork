from types import TracebackType
from typing import Self

import pytest

from seedwork.application.commands import Command, CommandHandler
from seedwork.infrastructure.registry_command_bus import RegistryCommandBus
from seedwork.infrastructure.transactional_command_bus import TransactionalCommandBus


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


class OkCommand(Command): ...


class FailCommand(Command): ...


class OkHandler(CommandHandler[OkCommand]):
    async def handle(self, command: OkCommand) -> None:
        pass


class FailHandler(CommandHandler[FailCommand]):
    async def handle(self, command: FailCommand) -> None:
        raise RuntimeError("boom")


async def test_successful_command_commits() -> None:
    uow = SpyUnitOfWork()
    registry = RegistryCommandBus()
    registry.register(OkCommand, OkHandler())
    bus = TransactionalCommandBus(registry, uow)
    result = await bus.dispatch(OkCommand())
    assert result.is_ok
    assert uow.sessions == 1
    assert uow.commits == 1
    assert uow.rollbacks == 0


async def test_failing_command_rolls_back() -> None:
    uow = SpyUnitOfWork()
    registry = RegistryCommandBus()
    registry.register(FailCommand, FailHandler())
    bus = TransactionalCommandBus(registry, uow)
    with pytest.raises(RuntimeError):
        await bus.dispatch(FailCommand())
    assert uow.sessions == 1
    assert uow.commits == 0
    assert uow.rollbacks == 1

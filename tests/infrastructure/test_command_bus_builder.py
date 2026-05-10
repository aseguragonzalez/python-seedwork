from collections.abc import Callable

from seedwork.application.commands import Command, CommandBus, CommandHandler, Result
from seedwork.infrastructure.command_bus_builder import CommandBusBuilder
from seedwork.infrastructure.transactional_command_bus import TransactionalCommandBus
from tests.infrastructure.test_transactional_command_bus import SpyUnitOfWork


class MyCommand(Command): ...


class MyHandler(CommandHandler[MyCommand]):
    async def handle(self, command: MyCommand) -> None:
        pass


async def test_builder_dispatches_registered_command() -> None:
    bus = CommandBusBuilder().register(MyCommand, MyHandler()).build()
    result = await bus.dispatch(MyCommand())
    assert result.ok


def test_builder_with_transaction_wraps_correctly() -> None:
    uow = SpyUnitOfWork()
    bus = CommandBusBuilder().register(MyCommand, MyHandler()).with_transaction(uow).build()
    assert isinstance(bus, TransactionalCommandBus)


async def test_builder_middleware_order() -> None:
    calls: list[str] = []

    def make_middleware(name: str) -> Callable[[CommandBus], CommandBus]:
        def middleware(inner: CommandBus) -> CommandBus:
            class WrappedBus:
                async def dispatch(self, command: Command) -> Result:
                    calls.append(name)
                    return await inner.dispatch(command)

            return WrappedBus()

        return middleware

    bus = (
        CommandBusBuilder()
        .register(MyCommand, MyHandler())
        .use(make_middleware("first"))
        .use(make_middleware("second"))
        .build()
    )
    await bus.dispatch(MyCommand())
    assert calls == ["first", "second"]

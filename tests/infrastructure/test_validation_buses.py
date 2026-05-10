from dataclasses import dataclass

from seedwork.application.commands import Command, CommandHandler
from seedwork.application.queries import Query
from seedwork.infrastructure.registry_command_bus import RegistryCommandBus
from seedwork.infrastructure.registry_query_bus import RegistryQueryBus
from seedwork.infrastructure.validation_command_bus import ValidationCommandBus, ValidationQueryBus

# ─── Helpers ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, kw_only=True)
class ValidCommand(Command):
    value: str


@dataclass(frozen=True, kw_only=True)
class InvalidCommand(Command):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("value cannot be empty")


@dataclass(frozen=True, kw_only=True)
class ValidQuery(Query[str]):
    value: str


@dataclass(frozen=True, kw_only=True)
class InvalidQuery(Query[str]):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("value cannot be empty")


class ValidCommandHandler(CommandHandler[ValidCommand]):
    async def handle(self, command: ValidCommand) -> None:
        pass


class InvalidCommandHandlerStub(CommandHandler[InvalidCommand]):
    async def handle(self, command: InvalidCommand) -> None:
        pass


class ValidQueryHandler:
    async def handle(self, query: ValidQuery) -> str | None:
        return query.value


class InvalidQueryHandlerStub:
    async def handle(self, query: InvalidQuery) -> str | None:
        return query.value


# ─── ValidationCommandBus tests ─────────────────────────────────────────────────


async def test_valid_command_is_dispatched() -> None:
    registry = RegistryCommandBus()
    registry.register(ValidCommand, ValidCommandHandler())
    bus = ValidationCommandBus(registry)

    result = await bus.dispatch(ValidCommand(value="hello"))
    assert result.ok


async def test_invalid_command_returns_fail_result() -> None:
    # Build an invalid command via object.__setattr__ bypassing frozen dataclass
    cmd = object.__new__(InvalidCommand)
    object.__setattr__(cmd, "value", "")

    registry = RegistryCommandBus()
    registry.register(InvalidCommand, InvalidCommandHandlerStub())
    bus = ValidationCommandBus(registry)

    result = await bus.dispatch(cmd)
    assert not result.ok
    assert result.errors[0].code == "validation_error"


# ─── ValidationQueryBus tests ────────────────────────────────────────────────────


async def test_valid_query_is_dispatched() -> None:
    registry = RegistryQueryBus()
    registry.register(ValidQuery, ValidQueryHandler())  # type: ignore[arg-type]
    bus = ValidationQueryBus(registry)

    result = await bus.ask(ValidQuery(value="hello"))
    assert result == "hello"


async def test_invalid_query_returns_none() -> None:
    # Build an invalid query bypassing frozen dataclass
    query = object.__new__(InvalidQuery)
    object.__setattr__(query, "value", "")

    registry = RegistryQueryBus()
    registry.register(InvalidQuery, InvalidQueryHandlerStub())  # type: ignore[arg-type]
    bus = ValidationQueryBus(registry)

    result = await bus.ask(query)
    assert result is None

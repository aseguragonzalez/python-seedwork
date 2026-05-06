from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, Self, TypeVar

TCommand_contra = TypeVar("TCommand_contra", bound="Command", contravariant=True)


@dataclass(frozen=True, kw_only=True)
class ResultError:
    code: str
    description: str


@dataclass(frozen=True, kw_only=True)
class Result:
    ok: bool
    errors: tuple[ResultError, ...] = ()

    @classmethod
    def succeeded(cls) -> Self:
        return cls(ok=True)

    @classmethod
    def failed(cls, errors: Sequence[ResultError]) -> Self:
        return cls(ok=False, errors=tuple(errors))


@dataclass(frozen=True, kw_only=True)
class Command: ...


class CommandHandler(Protocol[TCommand_contra]):
    async def execute(self, command: TCommand_contra) -> None: ...


class CommandBus(Protocol):
    async def dispatch(self, command: Command) -> Result: ...

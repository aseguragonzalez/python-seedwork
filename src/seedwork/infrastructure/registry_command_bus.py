from typing import Any

from seedwork.application.commands import Command, CommandHandler, Result, ResultError
from seedwork.domain.domain_error import DomainError


class RegistryCommandBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Command], CommandHandler[Any]] = {}

    def register(self, command_type: type[Command], handler: CommandHandler[Any]) -> None:
        self._handlers[command_type] = handler

    async def dispatch(self, command: Command) -> Result:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise KeyError(f"No handler registered for {type(command).__name__}")
        try:
            await handler.handle(command)
            return Result.succeeded()
        except DomainError as e:
            return Result.failed([ResultError(code=e.code, description=str(e))])

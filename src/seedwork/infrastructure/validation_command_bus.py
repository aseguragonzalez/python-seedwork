from typing import Any

from seedwork.application.commands import Command, CommandBus, Result, ResultError
from seedwork.application.queries import Query, QueryBus


class ValidationCommandBus:
    def __init__(self, inner: CommandBus) -> None:
        self._inner = inner

    async def dispatch(self, command: Command) -> Result:
        # __post_init__ ya validó al construir el command.
        # Si se quiere validación explícita en el bus (por si el command
        # se construye por deserialización sin pasar por __init__):
        try:
            if hasattr(command, "__post_init__"):
                command.__post_init__()  # type: ignore[operator]
        except Exception as e:
            return Result.failed([ResultError(code="validation_error", description=str(e))])
        return await self._inner.dispatch(command)


class ValidationQueryBus:
    def __init__(self, inner: QueryBus) -> None:
        self._inner = inner

    async def ask(self, query: Query[Any]) -> Any:
        try:
            if hasattr(query, "__post_init__"):
                query.__post_init__()  # type: ignore[operator]
        except Exception:
            return None
        return await self._inner.ask(query)

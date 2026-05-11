from seedwork.application.commands import Command, CommandBus, Result, ResultError
from seedwork.application.queries import Query, QueryBus


class ValidationCommandBus:
    def __init__(self, inner: CommandBus) -> None:
        self._inner = inner

    async def dispatch(self, command: Command) -> Result:
        # __post_init__ ya validó al construir el command.
        # Si se quiere validación explícita en el bus (por si el command
        # se construye por deserialización sin pasar por __init__):
        post_init = getattr(command, "__post_init__", None)
        if callable(post_init):
            try:
                post_init()
            except Exception as e:
                return Result.failed([ResultError(code="validation_error", description=str(e))])
        return await self._inner.dispatch(command)


class ValidationQueryBus:
    def __init__(self, inner: QueryBus) -> None:
        self._inner = inner

    async def ask[TResult](self, query: Query[TResult]) -> TResult | None:
        post_init = getattr(query, "__post_init__", None)
        if callable(post_init):
            try:
                post_init()
            except Exception:
                return None
        return await self._inner.ask(query)

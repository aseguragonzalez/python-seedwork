from typing import Any, cast

from seedwork.application.queries import Query, QueryBus, QueryHandler


class RegistryQueryBus(QueryBus):
    def __init__(self) -> None:
        self._handlers: dict[type[Query[Any]], QueryHandler[Any, Any]] = {}

    def register(self, query_type: type[Query[Any]], handler: QueryHandler[Any, Any]) -> None:
        self._handlers[query_type] = handler

    async def ask[TResult](self, query: Query[TResult]) -> TResult | None:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise KeyError(f"No handler registered for {type(query).__name__}")
        return cast(TResult | None, await handler.execute(query))

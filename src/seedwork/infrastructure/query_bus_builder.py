from typing import Any, Self

from seedwork.application.queries import Query, QueryBus, QueryBusMiddleware, QueryHandler
from seedwork.infrastructure.registry_query_bus import RegistryQueryBus


class QueryBusBuilder:
    def __init__(self, registry: RegistryQueryBus) -> None:
        self._registry = registry
        self._steps: list[QueryBusMiddleware] = []

    def register(self, query_type: type[Query[Any]], handler: QueryHandler[Any, Any]) -> Self:
        self._registry.register(query_type, handler)
        return self

    def use(self, middleware: QueryBusMiddleware) -> Self:
        self._steps.append(middleware)
        return self

    def build(self) -> QueryBus:
        bus: QueryBus = self._registry
        for step in reversed(self._steps):
            bus = step(bus)
        return bus

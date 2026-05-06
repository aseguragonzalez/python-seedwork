from collections.abc import Callable
from typing import Any, Self

from seedwork.application.queries import Query, QueryBus, QueryHandler
from seedwork.infrastructure.registry_query_bus import RegistryQueryBus


class QueryBusBuilder:
    def __init__(self) -> None:
        self._registry = RegistryQueryBus()
        self._steps: list[Callable[[QueryBus], QueryBus]] = []

    def register(self, query_type: type[Query[Any]], handler: QueryHandler[Any, Any]) -> Self:
        self._registry.register(query_type, handler)
        return self

    def use(self, middleware: Callable[[QueryBus], QueryBus]) -> Self:
        self._steps.append(middleware)
        return self

    def build(self) -> QueryBus:
        bus: QueryBus = self._registry
        for step in reversed(self._steps):
            bus = step(bus)
        return bus

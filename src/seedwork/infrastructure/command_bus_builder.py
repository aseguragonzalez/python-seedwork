from collections.abc import Callable
from typing import Any, Self

from seedwork.application.commands import Command, CommandBus, CommandHandler
from seedwork.application.domain_events import DomainEventBus
from seedwork.domain.unit_of_work import UnitOfWork
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus
from seedwork.infrastructure.domain_event_coordinator_command_bus import (
    DomainEventCoordinatorCommandBus,
)
from seedwork.infrastructure.registry_command_bus import RegistryCommandBus
from seedwork.infrastructure.transactional_command_bus import TransactionalCommandBus


class CommandBusBuilder:
    def __init__(self) -> None:
        self._registry = RegistryCommandBus()
        self._steps: list[Callable[[CommandBus], CommandBus]] = []

    def register(self, command_type: type[Command], handler: CommandHandler[Any]) -> Self:
        self._registry.register(command_type, handler)
        return self

    def with_transaction(self, unit_of_work: UnitOfWork) -> Self:
        self._steps.append(lambda inner: TransactionalCommandBus(inner, unit_of_work))
        return self

    def with_domain_event_coordination(self, event_bus: DomainEventBus) -> Self:
        self._steps.append(lambda inner: DomainEventCoordinatorCommandBus(inner, event_bus))
        return self

    def with_domain_event_flushing(self, event_bus: DeferredDomainEventBus) -> Self:
        """Deprecated: use with_domain_event_coordination instead."""
        return self.with_domain_event_coordination(event_bus)

    def use(self, middleware: Callable[[CommandBus], CommandBus]) -> Self:
        self._steps.append(middleware)
        return self

    def build(self) -> CommandBus:
        bus: CommandBus = self._registry
        for step in reversed(self._steps):
            bus = step(bus)
        return bus

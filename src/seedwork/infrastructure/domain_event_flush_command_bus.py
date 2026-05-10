from seedwork.application.commands import Command, CommandBus, Result
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus


class DomainEventFlushCommandBus:
    def __init__(
        self,
        inner: CommandBus,
        event_bus: DeferredDomainEventBus,
    ) -> None:
        self._inner = inner
        self._event_bus = event_bus

    async def dispatch(self, command: Command) -> Result:
        result = await self._inner.dispatch(command)
        if result.ok:
            await self._event_bus.flush()
        else:
            self._event_bus.clear()
        return result

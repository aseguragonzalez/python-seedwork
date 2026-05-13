from seedwork.application.commands import Command, CommandBus, Result
from seedwork.application.domain_event_bus import DomainEventBus


class DomainEventCoordinatorCommandBus:
    def __init__(
        self,
        inner: CommandBus,
        event_bus: DomainEventBus,
    ) -> None:
        self._inner = inner
        self._event_bus = event_bus

    async def dispatch(self, command: Command) -> Result:
        result = await self._inner.dispatch(command)
        if result.ok:
            await self._event_bus.dispatch()
        else:
            self._event_bus.discard()
        return result

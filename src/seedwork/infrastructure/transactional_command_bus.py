from seedwork.application.commands import Command, CommandBus, Result
from seedwork.domain.unit_of_work import UnitOfWork


class TransactionalCommandBus(CommandBus):
    def __init__(self, inner: CommandBus, unit_of_work: UnitOfWork) -> None:
        self._inner = inner
        self._unit_of_work = unit_of_work

    async def dispatch(self, command: Command) -> Result:
        async with self._unit_of_work:
            return await self._inner.dispatch(command)

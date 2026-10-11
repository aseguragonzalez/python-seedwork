from seedwork.application.commands import Command, CommandBus, Result
from seedwork.domain.unit_of_work import UnitOfWork


class _FailedResultRollback(Exception):
    """Raised inside the unit of work so `__aexit__` rolls back a failed result."""

    def __init__(self, result: Result) -> None:
        super().__init__("Command returned a failed result; rolling back the unit of work")
        self.result = result


class TransactionalCommandBus:
    """Runs each dispatch inside the unit of work and commits only on success.

    - `Result.ok()`: commit (`__aexit__` with no exception). A commit error propagates.
    - `Result.failed()`: roll back (`__aexit__` receives an exception); the same failed
      `Result` is returned, not raised.
    - Exception from the inner bus: roll back and re-raise.
    """

    def __init__(self, inner: CommandBus, unit_of_work: UnitOfWork) -> None:
        self._inner = inner
        self._unit_of_work = unit_of_work

    async def dispatch(self, command: Command) -> Result:
        try:
            async with self._unit_of_work:
                result = await self._inner.dispatch(command)
                if result.is_failed:
                    raise _FailedResultRollback(result)
                return result
        except _FailedResultRollback as rollback:
            return rollback.result

from types import TracebackType
from typing import Self

import pytest

from seedwork.application.commands import Command, Result, ResultError
from seedwork.infrastructure.transactional_command_bus import TransactionalCommandBus


class SpyUnitOfWork:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self._fail_commit = fail_commit
        self.sessions = 0
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        self.sessions += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollbacks += 1
            return
        self.commits += 1
        if self._fail_commit:
            raise ConnectionError("commit failed")


class AnyCommand(Command): ...


class StubCommandBus:
    def __init__(self, result: Result) -> None:
        self._result = result

    async def dispatch(self, command: Command) -> Result:
        return self._result


class RaisingCommandBus:
    async def dispatch(self, command: Command) -> Result:
        raise RuntimeError("boom")


async def test_ok_result_commits() -> None:
    uow = SpyUnitOfWork()
    ok = Result.ok()
    bus = TransactionalCommandBus(StubCommandBus(ok), uow)

    result = await bus.dispatch(AnyCommand())

    assert result is ok
    assert uow.sessions == 1
    assert uow.commits == 1
    assert uow.rollbacks == 0


async def test_failed_result_rolls_back_and_returns_the_same_result() -> None:
    uow = SpyUnitOfWork()
    failed = Result.failed([ResultError(code="err", description="fail")])
    bus = TransactionalCommandBus(StubCommandBus(failed), uow)

    result = await bus.dispatch(AnyCommand())

    assert result is failed
    assert uow.sessions == 1
    assert uow.commits == 0
    assert uow.rollbacks == 1


async def test_inner_exception_rolls_back_and_is_reraised() -> None:
    uow = SpyUnitOfWork()
    bus = TransactionalCommandBus(RaisingCommandBus(), uow)

    with pytest.raises(RuntimeError, match="boom"):
        await bus.dispatch(AnyCommand())

    assert uow.sessions == 1
    assert uow.commits == 0
    assert uow.rollbacks == 1


async def test_commit_exception_is_reraised() -> None:
    uow = SpyUnitOfWork(fail_commit=True)
    bus = TransactionalCommandBus(StubCommandBus(Result.ok()), uow)

    with pytest.raises(ConnectionError, match="commit failed"):
        await bus.dispatch(AnyCommand())

    assert uow.sessions == 1
    assert uow.commits == 1
    assert uow.rollbacks == 0

from seedwork.application.commands import Command, Result, ResultError
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus
from seedwork.infrastructure.domain_event_flush_command_bus import DomainEventFlushCommandBus


class OkCommand(Command): ...


class FailCommand(Command): ...


class SpyCommandBus:
    def __init__(self, result: Result) -> None:
        self._result = result
        self.dispatched: list[Command] = []

    async def dispatch(self, command: Command) -> Result:
        self.dispatched.append(command)
        return self._result


class SpyDeferredBus(DeferredDomainEventBus):
    def __init__(self) -> None:
        super().__init__()
        self.flushed = 0
        self.cleared = 0

    async def flush(self) -> None:
        self.flushed += 1

    def clear(self) -> None:
        self.cleared += 1


async def test_ok_result_calls_flush() -> None:
    inner = SpyCommandBus(Result.succeeded())
    event_bus = SpyDeferredBus()
    bus = DomainEventFlushCommandBus(inner, event_bus)

    result = await bus.dispatch(OkCommand())

    assert result.ok
    assert event_bus.flushed == 1
    assert event_bus.cleared == 0


async def test_fail_result_calls_clear_not_flush() -> None:
    inner = SpyCommandBus(Result.failed([ResultError(code="err", description="fail")]))
    event_bus = SpyDeferredBus()
    bus = DomainEventFlushCommandBus(inner, event_bus)

    result = await bus.dispatch(FailCommand())

    assert not result.ok
    assert event_bus.flushed == 0
    assert event_bus.cleared == 1

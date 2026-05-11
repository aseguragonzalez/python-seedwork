from seedwork.application.commands import Command, Result, ResultError
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus
from seedwork.infrastructure.domain_event_coordinator_command_bus import (
    DomainEventCoordinatorCommandBus,
)
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
        self.dispatched_count = 0
        self.discarded_count = 0

    async def dispatch(self) -> None:
        self.dispatched_count += 1

    def discard(self) -> None:
        self.discarded_count += 1


async def test_ok_result_calls_dispatch() -> None:
    inner = SpyCommandBus(Result.succeeded())
    event_bus = SpyDeferredBus()
    bus = DomainEventCoordinatorCommandBus(inner, event_bus)

    result = await bus.dispatch(OkCommand())

    assert result.ok
    assert event_bus.dispatched_count == 1
    assert event_bus.discarded_count == 0


async def test_fail_result_calls_discard_not_dispatch() -> None:
    inner = SpyCommandBus(Result.failed([ResultError(code="err", description="fail")]))
    event_bus = SpyDeferredBus()
    bus = DomainEventCoordinatorCommandBus(inner, event_bus)

    result = await bus.dispatch(FailCommand())

    assert not result.ok
    assert event_bus.dispatched_count == 0
    assert event_bus.discarded_count == 1


async def test_result_is_propagated() -> None:
    inner = SpyCommandBus(Result.succeeded())
    event_bus = SpyDeferredBus()
    bus = DomainEventCoordinatorCommandBus(inner, event_bus)

    result = await bus.dispatch(OkCommand())

    assert result is Result.succeeded() or result.ok


# Backwards compat: DomainEventFlushCommandBus is an alias
async def test_flush_bus_alias_ok_calls_dispatch() -> None:
    inner = SpyCommandBus(Result.succeeded())
    event_bus = SpyDeferredBus()
    bus = DomainEventFlushCommandBus(inner, event_bus)

    result = await bus.dispatch(OkCommand())

    assert result.ok
    assert event_bus.dispatched_count == 1


async def test_flush_bus_alias_fail_calls_discard() -> None:
    inner = SpyCommandBus(Result.failed([ResultError(code="err", description="fail")]))
    event_bus = SpyDeferredBus()
    bus = DomainEventFlushCommandBus(inner, event_bus)

    result = await bus.dispatch(FailCommand())

    assert not result.ok
    assert event_bus.discarded_count == 1


# Legacy names in flush_command_bus test for backwards compat verification
async def test_ok_result_calls_flush() -> None:
    inner = SpyCommandBus(Result.succeeded())
    event_bus = SpyDeferredBus()
    bus = DomainEventCoordinatorCommandBus(inner, event_bus)

    result = await bus.dispatch(OkCommand())

    assert result.ok
    assert event_bus.dispatched_count == 1
    assert event_bus.discarded_count == 0


async def test_fail_result_calls_clear_not_flush() -> None:
    inner = SpyCommandBus(Result.failed([ResultError(code="err", description="fail")]))
    event_bus = SpyDeferredBus()
    bus = DomainEventCoordinatorCommandBus(inner, event_bus)

    result = await bus.dispatch(FailCommand())

    assert not result.ok
    assert event_bus.dispatched_count == 0
    assert event_bus.discarded_count == 1

import asyncio
from dataclasses import dataclass

from seedwork.application.domain_event_bus import DomainEventHandler
from seedwork.domain.domain_event import BaseDomainEvent, DomainEvent
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus


@dataclass(frozen=True, kw_only=True)
class OrderPlacedPayload:
    order_id: str


@dataclass(frozen=True)
class OrderPlaced(BaseDomainEvent[OrderPlacedPayload]):
    pass


@dataclass(frozen=True, kw_only=True)
class OrderShippedPayload:
    order_id: str


@dataclass(frozen=True)
class OrderShipped(BaseDomainEvent[OrderShippedPayload]):
    pass


class SpyHandler(DomainEventHandler[OrderPlaced]):
    def __init__(self) -> None:
        self.received: list[DomainEvent] = []

    async def handle(self, event: OrderPlaced) -> None:
        self.received.append(event)


async def test_subscribe_publish_dispatch_handlers_invoked_in_order() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event1 = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))
    event2 = OrderPlaced(aggregate_id="o-2", payload=OrderPlacedPayload(order_id="o-2"))
    await bus.publish([event1, event2])
    await bus.dispatch()

    assert handler.received == [event1, event2]


async def test_dispatch_with_no_events_is_noop() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    await bus.dispatch()

    assert handler.received == []


async def test_multiple_handlers_for_same_event_type() -> None:
    bus = DeferredDomainEventBus()
    h1 = SpyHandler()
    h2 = SpyHandler()
    bus.subscribe(OrderPlaced, h1)
    bus.subscribe(OrderPlaced, h2)

    event = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])
    await bus.dispatch()

    assert h1.received == [event]
    assert h2.received == [event]


async def test_event_without_subscriber_does_not_raise() -> None:
    bus = DeferredDomainEventBus()
    event = OrderShipped(aggregate_id="o-1", payload=OrderShippedPayload(order_id="o-1"))
    await bus.publish([event])
    await bus.dispatch()


async def test_discard_empties_without_dispatching() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])
    bus.discard()
    await bus.dispatch()

    assert handler.received == []


async def test_idempotent_publish_same_event_id_invoked_once() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])
    await bus.publish([event])
    await bus.dispatch()

    assert len(handler.received) == 1
    assert handler.received[0] is event


async def test_dispatch_clears_pending_so_second_dispatch_is_noop() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])
    await bus.dispatch()
    await bus.dispatch()

    assert len(handler.received) == 1


async def test_concurrent_tasks_do_not_share_pending_events() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    a_published = asyncio.Event()
    b_done = asyncio.Event()

    task_a_received: list[DomainEvent] = []
    task_b_received: list[DomainEvent] = []

    event_a = OrderPlaced(aggregate_id="a", payload=OrderPlacedPayload(order_id="a"))
    event_b = OrderPlaced(aggregate_id="b", payload=OrderPlacedPayload(order_id="b"))

    async def task_a() -> None:
        await bus.publish([event_a])
        a_published.set()
        await b_done.wait()
        before = len(handler.received)
        await bus.dispatch()
        task_a_received.extend(handler.received[before:])

    async def task_b() -> None:
        await a_published.wait()
        await bus.publish([event_b])
        before = len(handler.received)
        await bus.dispatch()
        task_b_received.extend(handler.received[before:])
        b_done.set()

    await asyncio.gather(task_a(), task_b())

    assert task_a_received == [event_a]
    assert task_b_received == [event_b]
    assert handler.received.count(event_a) == 1
    assert handler.received.count(event_b) == 1
    assert len(handler.received) == 2


async def test_fresh_task_context_sees_no_pending_events_from_other_context() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    other_published = asyncio.Event()
    event = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))

    async def other_context() -> None:
        await bus.publish([event])
        other_published.set()

    async def fresh_context() -> None:
        await other_published.wait()
        await bus.dispatch()
        bus.discard()

    other_task = asyncio.create_task(other_context())
    fresh_task = asyncio.create_task(fresh_context())
    await asyncio.gather(other_task, fresh_task)

    assert handler.received == []


async def test_child_task_spawned_after_publish_cannot_drain_parent_buffer() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event = OrderPlaced(aggregate_id="o-1", payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])

    async def child() -> None:
        bus.discard()

    await asyncio.create_task(child())

    await bus.dispatch()

    assert handler.received == [event]

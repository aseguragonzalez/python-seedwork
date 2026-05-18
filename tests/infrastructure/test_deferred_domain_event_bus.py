from dataclasses import dataclass

from seedwork.application.domain_event_bus import DomainEventHandler
from seedwork.domain.domain_event import DomainEvent, DomainEventRecord
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus


@dataclass(frozen=True, kw_only=True)
class OrderPlacedPayload:
    order_id: str


@dataclass(frozen=True)
class OrderPlaced(DomainEventRecord[OrderPlacedPayload]):
    pass


@dataclass(frozen=True, kw_only=True)
class OrderShippedPayload:
    order_id: str


@dataclass(frozen=True)
class OrderShipped(DomainEventRecord[OrderShippedPayload]):
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

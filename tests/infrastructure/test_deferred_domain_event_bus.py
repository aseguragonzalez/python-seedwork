from dataclasses import dataclass

from seedwork.application.domain_events import DomainEventHandler
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


async def test_subscribe_publish_flush_handlers_invoked_in_order() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event1 = OrderPlaced(payload=OrderPlacedPayload(order_id="o-1"))
    event2 = OrderPlaced(payload=OrderPlacedPayload(order_id="o-2"))
    await bus.publish([event1, event2])
    await bus.flush()

    assert handler.received == [event1, event2]


async def test_flush_with_no_events_is_noop() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    await bus.flush()

    assert handler.received == []


async def test_multiple_handlers_for_same_event_type() -> None:
    bus = DeferredDomainEventBus()
    h1 = SpyHandler()
    h2 = SpyHandler()
    bus.subscribe(OrderPlaced, h1)
    bus.subscribe(OrderPlaced, h2)

    event = OrderPlaced(payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])
    await bus.flush()

    assert h1.received == [event]
    assert h2.received == [event]


async def test_event_without_subscriber_does_not_raise() -> None:
    bus = DeferredDomainEventBus()
    event = OrderShipped(payload=OrderShippedPayload(order_id="o-1"))
    await bus.publish([event])
    # should not raise
    await bus.flush()


async def test_clear_empties_without_dispatching() -> None:
    bus = DeferredDomainEventBus()
    handler = SpyHandler()
    bus.subscribe(OrderPlaced, handler)

    event = OrderPlaced(payload=OrderPlacedPayload(order_id="o-1"))
    await bus.publish([event])
    bus.clear()
    await bus.flush()

    assert handler.received == []

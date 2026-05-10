from typing import Any

from seedwork.application.integration_events import IntegrationEventRecord
from seedwork.infrastructure.in_memory_integration_event_publisher import (
    InMemoryIntegrationEventPublisher,
)


def make_event(correlation_id: str = "corr-1") -> IntegrationEventRecord[dict[str, Any]]:
    return IntegrationEventRecord(
        type="bank.account.opened",
        version="1.0",
        aggregate_id="acc-1",
        payload={"account_id": "acc-1"},
        correlation_id=correlation_id,
    )


async def test_publish_accumulates_events() -> None:
    publisher = InMemoryIntegrationEventPublisher()
    e1 = make_event("c-1")
    e2 = make_event("c-2")

    await publisher.publish([e1])
    await publisher.publish([e2])

    assert list(publisher.published) == [e1, e2]


async def test_published_getter_returns_copy() -> None:
    publisher = InMemoryIntegrationEventPublisher()
    e1 = make_event()
    await publisher.publish([e1])

    snapshot = publisher.published
    await publisher.publish([make_event("c-99")])

    assert len(snapshot) == 1  # snapshot is not affected


async def test_clear_removes_all_published() -> None:
    publisher = InMemoryIntegrationEventPublisher()
    await publisher.publish([make_event()])
    publisher.clear()

    assert list(publisher.published) == []

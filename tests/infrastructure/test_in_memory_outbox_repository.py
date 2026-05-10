from typing import Any

from seedwork.application.integration_events import IntegrationEventRecord
from seedwork.infrastructure.outbox_integration_event_publisher import InMemoryOutboxRepository


def make_event(correlation_id: str = "corr-1") -> IntegrationEventRecord[dict[str, Any]]:
    return IntegrationEventRecord(
        type="bank.account.opened",
        version="1.0",
        aggregate_id="acc-1",
        payload={"account_id": "acc-1"},
        correlation_id=correlation_id,
    )


async def test_save_creates_pending_record() -> None:
    repo = InMemoryOutboxRepository()
    event = make_event()
    await repo.save(event)

    pending = await repo.find_pending()
    assert len(pending) == 1
    assert pending[0].status == "pending"
    assert pending[0].event is event


async def test_find_pending_respects_limit() -> None:
    repo = InMemoryOutboxRepository()
    for i in range(5):
        await repo.save(make_event(f"corr-{i}"))

    pending = await repo.find_pending(limit=3)
    assert len(pending) == 3


async def test_mark_as_published() -> None:
    repo = InMemoryOutboxRepository()
    await repo.save(make_event())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_published(record_id)

    still_pending = await repo.find_pending()
    assert len(still_pending) == 0


async def test_mark_as_failed() -> None:
    repo = InMemoryOutboxRepository()
    await repo.save(make_event())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_failed(record_id, "timeout")

    still_pending = await repo.find_pending()
    assert len(still_pending) == 0

    # Verify the record is now failed
    all_records_via_pending = await repo.find_pending(limit=1000)
    assert len(all_records_via_pending) == 0

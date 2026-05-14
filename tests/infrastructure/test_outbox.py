from seedwork.application.background_tasks import BaseBackgroundTask
from seedwork.application.base_integration_event import BaseIntegrationEvent
from seedwork.infrastructure.outbox import (
    InMemoryIntegrationEventOutboxRepository,
    InMemoryTaskOutboxRepository,
    OutboxIntegrationEventPublisher,
    OutboxTaskScheduler,
)


def make_event(correlation_id: str = "corr-1") -> BaseIntegrationEvent:
    return BaseIntegrationEvent(
        type="bank.account.opened",
        version="1.0",
        aggregate_id="acc-1",
        payload={"account_id": "acc-1"},
        correlation_id=correlation_id,
    )


def make_task(task_type: str = "domain.send_email") -> BaseBackgroundTask:
    return BaseBackgroundTask(
        type=task_type,
        payload={"key": "value"},
        correlation_id="corr-1",
    )


async def test_ie_outbox_save_creates_pending_record() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    event = make_event()
    await repo.save(event)

    pending = await repo.find_pending()
    assert len(pending) == 1
    assert pending[0].status == "pending"
    assert pending[0].event is event


async def test_ie_outbox_find_pending_respects_limit() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    for i in range(5):
        await repo.save(make_event(f"corr-{i}"))

    pending = await repo.find_pending(limit=3)
    assert len(pending) == 3


async def test_ie_outbox_mark_as_published() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    await repo.save(make_event())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_published(record_id)

    still_pending = await repo.find_pending()
    assert len(still_pending) == 0


async def test_ie_outbox_mark_as_published_sets_published_at() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    await repo.save(make_event())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_published(record_id)

    assert repo.all[0].published_at is not None


async def test_ie_outbox_mark_as_failed() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    await repo.save(make_event())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_failed(record_id, "timeout")

    still_pending = await repo.find_pending()
    assert len(still_pending) == 0
    assert repo.all[0].status == "failed"
    assert repo.all[0].last_error == "timeout"
    assert repo.all[0].attempts == 1


async def test_ie_outbox_all_returns_all_records() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    await repo.save(make_event("c-1"))
    await repo.save(make_event("c-2"))

    assert len(repo.all) == 2


async def test_ie_outbox_reset_clears_all() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    await repo.save(make_event())
    repo.reset()

    assert len(repo.all) == 0


async def test_outbox_ie_publisher_saves_each_event() -> None:
    repo = InMemoryIntegrationEventOutboxRepository()
    publisher = OutboxIntegrationEventPublisher(repo)
    e1 = make_event("c-1")
    e2 = make_event("c-2")

    await publisher.publish([e1, e2])

    assert len(repo.all) == 2


async def test_task_outbox_save_creates_pending_record() -> None:
    repo = InMemoryTaskOutboxRepository()
    task = make_task()
    await repo.save(task)

    pending = await repo.find_pending()
    assert len(pending) == 1
    assert pending[0].status == "pending"
    assert pending[0].task is task


async def test_task_outbox_find_pending_respects_limit() -> None:
    repo = InMemoryTaskOutboxRepository()
    for i in range(5):
        await repo.save(make_task(f"domain.task_{i}"))

    pending = await repo.find_pending(limit=2)
    assert len(pending) == 2


async def test_task_outbox_mark_as_delivered() -> None:
    repo = InMemoryTaskOutboxRepository()
    await repo.save(make_task())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_delivered(record_id)

    still_pending = await repo.find_pending()
    assert len(still_pending) == 0
    assert repo.all[0].delivered_at is not None


async def test_task_outbox_mark_as_failed() -> None:
    repo = InMemoryTaskOutboxRepository()
    await repo.save(make_task())
    pending = await repo.find_pending()
    record_id = pending[0].id

    await repo.mark_as_failed(record_id, "queue full")

    still_pending = await repo.find_pending()
    assert len(still_pending) == 0
    assert repo.all[0].status == "failed"
    assert repo.all[0].last_error == "queue full"
    assert repo.all[0].attempts == 1


async def test_task_outbox_all_returns_all_records() -> None:
    repo = InMemoryTaskOutboxRepository()
    await repo.save(make_task("t1"))
    await repo.save(make_task("t2"))

    assert len(repo.all) == 2


async def test_task_outbox_reset_clears_all() -> None:
    repo = InMemoryTaskOutboxRepository()
    await repo.save(make_task())
    repo.reset()

    assert len(repo.all) == 0


async def test_outbox_task_scheduler_saves_task() -> None:
    repo = InMemoryTaskOutboxRepository()
    scheduler = OutboxTaskScheduler(repo)

    await scheduler.schedule(make_task())

    assert len(repo.all) == 1

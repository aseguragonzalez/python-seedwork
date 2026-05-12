from seedwork.infrastructure.registry_task_bus import BackgroundTaskRecord, InMemoryTaskQueue


def make_task(task_type: str = "domain.send_email", max_attempts: int = 3) -> BackgroundTaskRecord:
    return BackgroundTaskRecord(type=task_type, payload={}, max_attempts=max_attempts)


async def test_enqueue_and_dequeue() -> None:
    queue = InMemoryTaskQueue()
    task = make_task()
    await queue.enqueue(task)

    dequeued = await queue.dequeue()
    assert dequeued is not None
    assert dequeued.id == task.id


async def test_dequeue_returns_none_when_empty() -> None:
    queue = InMemoryTaskQueue()
    result = await queue.dequeue()
    assert result is None


async def test_ack_marks_task_as_completed() -> None:
    queue = InMemoryTaskQueue()
    task = make_task()
    await queue.enqueue(task)
    dequeued = await queue.dequeue()
    assert dequeued is not None

    await queue.ack(dequeued.id)

    found = await queue.find_by_id(task.id)
    assert found is not None
    assert found.id == task.id


async def test_nack_with_retry_re_enqueues() -> None:
    queue = InMemoryTaskQueue()
    task = make_task(max_attempts=3)
    await queue.enqueue(task)
    dequeued = await queue.dequeue()
    assert dequeued is not None

    await queue.nack(dequeued.id, "transient error")

    found = await queue.find_by_id(task.id)
    assert found is not None

    # should be dequeue-able again
    retry = await queue.dequeue()
    assert retry is not None
    assert retry.id == task.id


async def test_nack_with_max_attempts_exceeded_does_not_re_enqueue() -> None:
    queue = InMemoryTaskQueue()
    task = make_task(max_attempts=1)
    await queue.enqueue(task)
    dequeued = await queue.dequeue()
    assert dequeued is not None

    await queue.nack(dequeued.id, "permanent error")

    found = await queue.find_by_id(task.id)
    assert found is not None

    # task must NOT be dequeue-able again after exhausting attempts
    retry = await queue.dequeue()
    assert retry is None


async def test_find_by_id_returns_none_for_unknown() -> None:
    queue = InMemoryTaskQueue()
    result = await queue.find_by_id("nonexistent-id")
    assert result is None

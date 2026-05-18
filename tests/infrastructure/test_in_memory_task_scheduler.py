from seedwork.application.background_tasks import BaseBackgroundTask, TaskHandler
from seedwork.testing import InMemoryTaskScheduler


class SpyTaskHandler(TaskHandler[BaseBackgroundTask]):
    def __init__(self) -> None:
        self.handled: list[BaseBackgroundTask] = []

    async def handle(self, task: BaseBackgroundTask) -> None:
        self.handled.append(task)


def make_task(task_type: str = "domain.send_email") -> BaseBackgroundTask:
    return BaseBackgroundTask(
        type=task_type,
        payload={"key": "val"},
        correlation_id="corr-1",
    )


async def test_schedule_accumulates_tasks() -> None:
    scheduler = InMemoryTaskScheduler()
    t1 = make_task()
    t2 = make_task("domain.notify")

    await scheduler.schedule(t1)
    await scheduler.schedule(t2)

    assert len(scheduler.scheduled) == 2


async def test_scheduled_getter_returns_copy() -> None:
    scheduler = InMemoryTaskScheduler()
    t1 = make_task()
    await scheduler.schedule(t1)

    snapshot = scheduler.scheduled
    await scheduler.schedule(make_task("other"))

    assert len(snapshot) == 1


async def test_execute_scheduled_calls_registered_handler() -> None:
    scheduler = InMemoryTaskScheduler()
    handler = SpyTaskHandler()
    scheduler.register("domain.send_email", handler)
    task = make_task("domain.send_email")
    await scheduler.schedule(task)

    await scheduler.execute_scheduled()

    assert task in handler.handled


async def test_execute_scheduled_with_no_handler_does_not_raise() -> None:
    scheduler = InMemoryTaskScheduler()
    task = make_task("domain.unknown")
    await scheduler.schedule(task)

    # Should not raise even with no handler registered
    await scheduler.execute_scheduled()


async def test_execute_scheduled_calls_all_scheduled_tasks() -> None:
    scheduler = InMemoryTaskScheduler()
    handler = SpyTaskHandler()
    scheduler.register("domain.send_email", handler)

    t1 = make_task("domain.send_email")
    t2 = make_task("domain.send_email")
    await scheduler.schedule(t1)
    await scheduler.schedule(t2)

    await scheduler.execute_scheduled()

    assert len(handler.handled) == 2


async def test_reset_clears_scheduled() -> None:
    scheduler = InMemoryTaskScheduler()
    await scheduler.schedule(make_task())
    scheduler.reset()

    assert len(scheduler.scheduled) == 0


async def test_reset_prevents_execution() -> None:
    scheduler = InMemoryTaskScheduler()
    handler = SpyTaskHandler()
    scheduler.register("domain.send_email", handler)
    await scheduler.schedule(make_task("domain.send_email"))
    scheduler.reset()

    await scheduler.execute_scheduled()

    assert len(handler.handled) == 0


def test_in_memory_task_scheduler_satisfies_spy_protocol() -> None:
    from seedwork.testing import TaskSchedulerSpy

    scheduler = InMemoryTaskScheduler()
    assert isinstance(scheduler, TaskSchedulerSpy)

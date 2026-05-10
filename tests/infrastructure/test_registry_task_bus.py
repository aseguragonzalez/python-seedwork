import pytest

from seedwork.application.background_tasks import BackgroundTask, TaskHandler
from seedwork.infrastructure.registry_task_bus import BackgroundTaskRecord, RegistryTaskBus


class SpyTaskHandler(TaskHandler[BackgroundTaskRecord]):
    def __init__(self) -> None:
        self.handled: list[BackgroundTask] = []

    async def handle(self, task: BackgroundTaskRecord) -> None:
        self.handled.append(task)


def make_task(task_type: str = "domain.send_email") -> BackgroundTaskRecord:
    return BackgroundTaskRecord(type=task_type, payload={})


async def test_dispatch_calls_registered_handler() -> None:
    bus = RegistryTaskBus()
    handler = SpyTaskHandler()
    task = make_task()
    bus.register(task.type, handler)

    await bus.dispatch(task)

    assert task in handler.handled


async def test_dispatch_raises_when_no_handler() -> None:
    bus = RegistryTaskBus()
    task = make_task("domain.unknown")

    with pytest.raises(ValueError, match="No handler registered"):
        await bus.dispatch(task)

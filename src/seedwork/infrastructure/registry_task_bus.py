"""
RegistryTaskBus — simple handler registry for background tasks.

Note: TaskQueue, InMemoryTaskQueue and BackgroundTaskRecord are kept here for
backwards compatibility only. New code should use InMemoryTaskScheduler instead.
"""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from seedwork.application.background_tasks import BackgroundTask, TaskHandler


class RegistryTaskBus:
    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler[Any]] = {}

    def register(self, task_type: str, handler: TaskHandler[Any]) -> None:
        self._handlers[task_type] = handler

    async def dispatch(self, task: BackgroundTask) -> None:
        handler = self._handlers.get(task.type)
        if not handler:
            raise ValueError(f"No handler registered for task type: {task.type}")
        await handler.handle(task)


# ---------------------------------------------------------------------------
# Kept for backwards compatibility — will be removed in a future release.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class BackgroundTaskRecord:
    """Concrete BackgroundTask with legacy lifecycle fields (backwards compat)."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    payload: dict[str, Any] = field(default_factory=lambda: {})
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    # Legacy lifecycle fields — not part of the minimal BackgroundTask protocol
    status: str = "pending"
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    attempts: int = 0
    max_attempts: int = 3
    last_error: str | None = None


class InMemoryTaskQueue:
    """Deprecated — use InMemoryTaskScheduler instead."""

    def __init__(self) -> None:
        self._store: dict[str, BackgroundTaskRecord] = {}
        self._queue: list[str] = []

    async def enqueue(self, task: BackgroundTask) -> None:
        # Preserve max_attempts from BackgroundTaskRecord if available.
        max_attempts: int = getattr(task, "max_attempts", 3)
        record = BackgroundTaskRecord(
            id=task.id,
            type=task.type,
            payload=task.payload,
            correlation_id=task.correlation_id,
            causation_id=task.causation_id,
            max_attempts=max_attempts,
        )
        self._store[record.id] = record
        self._queue.append(record.id)

    async def dequeue(self) -> BackgroundTask | None:
        for task_id in list(self._queue):
            task = self._store.get(task_id)
            if task and task.status == "pending":
                self._queue.remove(task_id)
                running = replace(task, status="running", started_at=datetime.now(UTC))
                self._store[task_id] = running
                return running
        return None

    async def ack(self, task_id: str) -> None:
        task = self._store.get(task_id)
        if task:
            self._store[task_id] = replace(task, status="completed", completed_at=datetime.now(UTC))

    async def nack(self, task_id: str, error: str) -> None:
        task = self._store.get(task_id)
        if not task:
            return
        updated = replace(task, attempts=task.attempts + 1, last_error=error)
        if updated.attempts >= updated.max_attempts:
            self._store[task_id] = replace(updated, status="failed")
        else:
            self._store[task_id] = replace(updated, status="pending")
            self._queue.append(task_id)

    async def find_by_id(self, task_id: str) -> BackgroundTask | None:
        return self._store.get(task_id)

from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar
from uuid import uuid4


class BackgroundTask(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def type(self) -> str: ...

    @property
    def payload(self) -> dict[str, Any]: ...

    @property
    def correlation_id(self) -> str: ...

    @property
    def causation_id(self) -> str | None: ...

    @property
    def metadata(self) -> dict[str, str] | None: ...


@dataclass(frozen=True, kw_only=True)
class BaseBackgroundTask:
    type: str
    payload: dict[str, Any]
    correlation_id: str
    causation_id: str | None = None
    metadata: dict[str, str] | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


class TaskScheduler(Protocol):
    async def schedule(self, task: BackgroundTask) -> None: ...


TTask_contra = TypeVar("TTask_contra", bound=BackgroundTask, contravariant=True)


class TaskHandler(Protocol[TTask_contra]):
    async def handle(self, task: TTask_contra) -> None: ...

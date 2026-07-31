from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4


class BackgroundTask[TPayload_co](Protocol):
    @property
    def id(self) -> str: ...

    @property
    def type(self) -> str: ...

    @property
    def payload(self) -> TPayload_co: ...

    @property
    def correlation_id(self) -> str: ...

    @property
    def causation_id(self) -> str | None: ...

    @property
    def metadata(self) -> dict[str, str] | None: ...


@dataclass(frozen=True, kw_only=True)
class BaseBackgroundTask[TPayload_co]:
    type: str
    payload: TPayload_co
    correlation_id: str
    causation_id: str | None = None
    metadata: dict[str, str] | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


class TaskScheduler(Protocol):
    async def schedule(self, task: BackgroundTask[Any]) -> None: ...


class TaskHandler[TTask_contra: BackgroundTask[Any]](Protocol):
    async def handle(self, task: TTask_contra) -> None: ...

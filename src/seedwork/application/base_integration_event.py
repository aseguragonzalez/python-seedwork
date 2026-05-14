from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class BaseIntegrationEvent:
    type: str
    version: str
    aggregate_id: str
    payload: dict[str, Any]
    correlation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    causation_id: str | None = None
    metadata: dict[str, str] | None = None

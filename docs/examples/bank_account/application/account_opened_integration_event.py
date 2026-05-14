from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from bank_account.domain.events.account_opened import AccountOpened


@dataclass(frozen=True, kw_only=True)
class AccountOpenedIntegrationEvent:
    type: str
    version: str
    aggregate_id: str
    payload: dict[str, Any]
    correlation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    causation_id: str | None = None
    metadata: dict[str, str] | None = None

    @classmethod
    def from_domain_event(cls, event: AccountOpened) -> AccountOpenedIntegrationEvent:
        return cls(
            type="bank_account.account_opened",
            version="1.0",
            aggregate_id=str(event.payload.account_id),
            payload={
                "account_id": str(event.payload.account_id),
                "initial_balance": event.payload.initial_balance,
                "currency": event.payload.currency,
            },
            correlation_id=event.id,
        )

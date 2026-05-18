from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from bank_account.application.request_context import correlation_id as _correlation_id

from seedwork.application.base_integration_event import BaseIntegrationEvent

if TYPE_CHECKING:
    from bank_account.domain.events.account_opened import AccountOpened


class AccountOpenedIntegrationEvent(BaseIntegrationEvent):
    @classmethod
    def from_domain_event(cls, event: AccountOpened) -> AccountOpenedIntegrationEvent:
        return cls(
            type="bank_account.account_opened",
            version="1.0",
            aggregate_id=event.aggregate_id,
            payload={
                "account_id": event.aggregate_id,
                "initial_balance": event.payload.initial_balance,
                "currency": event.payload.currency,
            },
            correlation_id=_correlation_id.get(str(uuid4())),
            causation_id=event.id,
        )

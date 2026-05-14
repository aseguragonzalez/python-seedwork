from __future__ import annotations

from typing import TYPE_CHECKING

from seedwork.application.base_integration_event import BaseIntegrationEvent

if TYPE_CHECKING:
    from bank_account.domain.events.account_opened import AccountOpened


class AccountOpenedIntegrationEvent(BaseIntegrationEvent):
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

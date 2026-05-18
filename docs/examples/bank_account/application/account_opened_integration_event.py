from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from bank_account.application.request_context import correlation_id as _correlation_id

from seedwork.application.integration_events import BaseIntegrationEvent

if TYPE_CHECKING:
    from bank_account.domain.events.account_opened import AccountOpened


class AccountOpenedIntegrationEvent(BaseIntegrationEvent):
    TYPE: ClassVar[str] = "bank_account.account_opened"
    VERSION: ClassVar[str] = "1.0"

    @classmethod
    def from_domain_event(cls, event: AccountOpened) -> AccountOpenedIntegrationEvent:
        return cls(
            type=cls.TYPE,
            version=cls.VERSION,
            aggregate_id=event.aggregate_id,
            payload={
                "account_id": event.aggregate_id,
                "initial_balance": event.payload.initial_balance,
                "currency": event.payload.currency,
            },
            correlation_id=_correlation_id.get(str(uuid4())),
            causation_id=event.id,
        )

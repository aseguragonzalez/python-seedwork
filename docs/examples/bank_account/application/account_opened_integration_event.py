from dataclasses import dataclass

from seedwork.infrastructure.integration_event_record import IntegrationEventRecord


@dataclass(frozen=True, kw_only=True)
class AccountOpenedIntegrationEvent(IntegrationEventRecord):
    account_id: str
    owner: str
    initial_balance: float
    currency: str

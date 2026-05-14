from dataclasses import dataclass

from seedwork.infrastructure.integration_event_record import IntegrationEventRecord


@dataclass(frozen=True, kw_only=True)
class AccountOpenedIntegrationEvent(IntegrationEventRecord):
    account_id: str
    owner: str
    initial_balance: float
    currency: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "payload",
            {
                "account_id": self.account_id,
                "owner": self.owner,
                "initial_balance": self.initial_balance,
                "currency": self.currency,
            },
        )

from __future__ import annotations

from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True, kw_only=True)
class AccountOpenedPayload:
    initial_balance: float
    currency: str


@dataclass(frozen=True)
class AccountOpened(BaseDomainEvent[AccountOpenedPayload]):
    @classmethod
    def create(cls, initial_balance: float, currency: str, aggregate_id: str) -> AccountOpened:
        return cls(
            payload=AccountOpenedPayload(initial_balance=initial_balance, currency=currency),
            aggregate_id=aggregate_id,
        )

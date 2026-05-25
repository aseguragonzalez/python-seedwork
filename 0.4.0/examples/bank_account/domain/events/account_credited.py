from __future__ import annotations

from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True, kw_only=True)
class AccountCreditedPayload:
    amount: float
    currency: str


@dataclass(frozen=True)
class AccountCredited(BaseDomainEvent[AccountCreditedPayload]):
    @classmethod
    def create(cls, amount: float, currency: str, aggregate_id: str) -> AccountCredited:
        return cls(
            payload=AccountCreditedPayload(amount=amount, currency=currency),
            aggregate_id=aggregate_id,
        )

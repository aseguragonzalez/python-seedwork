from __future__ import annotations

from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True, kw_only=True)
class AccountDebitedPayload:
    amount: float
    currency: str


@dataclass(frozen=True)
class AccountDebited(BaseDomainEvent[AccountDebitedPayload]):
    @classmethod
    def create(cls, amount: float, currency: str, aggregate_id: str) -> AccountDebited:
        return cls(
            payload=AccountDebitedPayload(amount=amount, currency=currency),
            aggregate_id=aggregate_id,
        )

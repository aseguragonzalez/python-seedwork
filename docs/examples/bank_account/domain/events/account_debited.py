from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True, kw_only=True)
class AccountDebitedPayload:
    amount: float
    currency: str


@dataclass(frozen=True)
class AccountDebited(BaseDomainEvent[AccountDebitedPayload]):
    pass

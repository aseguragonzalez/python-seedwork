from dataclasses import dataclass

from seedwork.domain.domain_event import DomainEventRecord


@dataclass(frozen=True, kw_only=True)
class AccountCreditedPayload:
    amount: float
    currency: str


@dataclass(frozen=True)
class AccountCredited(DomainEventRecord[AccountCreditedPayload]):
    pass

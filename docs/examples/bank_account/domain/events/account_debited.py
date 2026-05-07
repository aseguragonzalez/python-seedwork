from dataclasses import dataclass

from seedwork.domain.domain_event import DomainEventRecord


@dataclass(frozen=True, kw_only=True)
class AccountDebitedPayload:
    account_id: str
    amount: float
    currency: str


@dataclass(frozen=True)
class AccountDebited(DomainEventRecord[AccountDebitedPayload]):
    pass

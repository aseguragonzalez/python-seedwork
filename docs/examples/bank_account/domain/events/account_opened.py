from dataclasses import dataclass

from seedwork.domain.domain_event import DomainEventRecord


@dataclass(frozen=True, kw_only=True)
class AccountOpenedPayload:
    initial_balance: float
    currency: str


@dataclass(frozen=True)
class AccountOpened(DomainEventRecord[AccountOpenedPayload]):
    pass

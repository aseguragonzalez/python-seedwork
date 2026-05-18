from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True, kw_only=True)
class AccountOpenedPayload:
    initial_balance: float
    currency: str


@dataclass(frozen=True)
class AccountOpened(BaseDomainEvent[AccountOpenedPayload]):
    pass

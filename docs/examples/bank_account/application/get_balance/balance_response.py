from dataclasses import dataclass


@dataclass(frozen=True)
class BalanceResponse:
    account_id: str
    balance: float
    currency: str

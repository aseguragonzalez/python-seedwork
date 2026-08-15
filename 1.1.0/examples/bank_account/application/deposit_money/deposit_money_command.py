from dataclasses import dataclass

from seedwork.application.commands import Command


@dataclass(frozen=True, kw_only=True)
class DepositMoneyCommand(Command):
    account_id: str
    amount: float
    currency: str

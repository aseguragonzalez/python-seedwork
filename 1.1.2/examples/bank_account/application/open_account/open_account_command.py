from dataclasses import dataclass

from seedwork.application.commands import Command


@dataclass(frozen=True, kw_only=True)
class OpenAccountCommand(Command):
    account_id: str
    owner_id: str
    initial_balance: float
    currency: str

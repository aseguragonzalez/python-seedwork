from dataclasses import dataclass

from examples.bank_account.application.get_balance.balance_response import BalanceResponse
from seedwork.application.queries import Query


@dataclass(frozen=True, kw_only=True)
class GetBalanceQuery(Query[BalanceResponse]):
    account_id: str

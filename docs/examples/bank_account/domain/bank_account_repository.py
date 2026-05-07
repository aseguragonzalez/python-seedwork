from typing import Protocol

from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId

from seedwork.domain.repository import Repository


class BankAccountRepository(Repository[BankAccountId, BankAccount], Protocol):
    pass

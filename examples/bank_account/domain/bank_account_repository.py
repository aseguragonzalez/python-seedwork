from typing import Protocol

from examples.bank_account.domain.bank_account import BankAccount
from examples.bank_account.domain.bank_account_id import BankAccountId
from seedwork.domain.repository import Repository


class BankAccountRepository(Repository[BankAccountId, BankAccount], Protocol):
    pass

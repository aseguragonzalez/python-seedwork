from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.errors import CurrencyMismatchError, InsufficientFundsError
from bank_account.domain.events.account_credited import AccountCredited
from bank_account.domain.events.account_debited import AccountDebited
from bank_account.domain.events.account_opened import AccountOpened
from bank_account.domain.money import Money
from bank_account.domain.user_id import UserId

from seedwork.domain.aggregate_root import AggregateRoot


@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(AggregateRoot[BankAccountId]):
    owner_id: UserId
    balance: Money

    @classmethod
    def reconstitute(cls, id: BankAccountId, owner_id: UserId, balance: Money) -> Self:
        return cls(id=id, owner_id=owner_id, balance=balance)

    @classmethod
    def open(cls, id: BankAccountId, owner_id: UserId, initial_balance: Money) -> Self:
        return cls(id=id, owner_id=owner_id, balance=initial_balance)._record(
            AccountOpened.create(
                initial_balance=initial_balance.amount,
                currency=initial_balance.currency,
                aggregate_id=str(id),
            )
        )

    def credit(self, amount: Money) -> Self:
        if amount.currency != self.balance.currency:
            raise CurrencyMismatchError(self.balance.currency, amount.currency)
        new_balance = Money(
            amount=self.balance.amount + amount.amount,
            currency=self.balance.currency,
        )
        return self._evolve(balance=new_balance)._record(
            AccountCredited.create(
                amount=amount.amount,
                currency=amount.currency,
                aggregate_id=str(self.id),
            )
        )

    def debit(self, amount: Money) -> Self:
        if amount.currency != self.balance.currency:
            raise CurrencyMismatchError(self.balance.currency, amount.currency)
        if amount.amount > self.balance.amount:
            raise InsufficientFundsError()
        new_balance = Money(
            amount=self.balance.amount - amount.amount,
            currency=self.balance.currency,
        )
        return self._evolve(balance=new_balance)._record(
            AccountDebited.create(
                amount=amount.amount,
                currency=amount.currency,
                aggregate_id=str(self.id),
            )
        )

    def validate(self) -> None:
        pass

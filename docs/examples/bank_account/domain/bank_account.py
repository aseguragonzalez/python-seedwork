from dataclasses import dataclass
from typing import Self

from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.errors import CurrencyMismatchError, InsufficientFundsError
from bank_account.domain.events.account_credited import (
    AccountCredited,
    AccountCreditedPayload,
)
from bank_account.domain.events.account_debited import (
    AccountDebited,
    AccountDebitedPayload,
)
from bank_account.domain.events.account_opened import AccountOpened, AccountOpenedPayload
from bank_account.domain.money import Money

from seedwork.domain.aggregate_root import AggregateRoot


@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(AggregateRoot[BankAccountId]):
    balance: Money

    @classmethod
    def reconstitute(cls, id: BankAccountId, balance: Money) -> Self:
        return cls(id=id, balance=balance)

    @classmethod
    def open(cls, id: BankAccountId, initial_balance: Money) -> Self:
        event = AccountOpened(
            aggregate_id=id,
            payload=AccountOpenedPayload(
                initial_balance=initial_balance.amount,
                currency=initial_balance.currency,
            ),
        )
        return cls(id=id, balance=initial_balance, domain_events=(event,))

    def credit(self, amount: Money) -> Self:
        if amount.currency != self.balance.currency:
            raise CurrencyMismatchError(self.balance.currency, amount.currency)
        new_amount = self.balance.amount + amount.amount
        new_balance = Money(amount=new_amount, currency=self.balance.currency)
        return self._evolve(balance=new_balance)._record(
            AccountCredited(
                aggregate_id=self.id,
                payload=AccountCreditedPayload(
                    amount=amount.amount,
                    currency=amount.currency,
                ),
            )
        )

    def validate(self) -> None:
        pass

    def debit(self, amount: Money) -> Self:
        if amount.currency != self.balance.currency:
            raise CurrencyMismatchError(self.balance.currency, amount.currency)
        if amount.amount > self.balance.amount:
            raise InsufficientFundsError()
        new_amount = self.balance.amount - amount.amount
        new_balance = Money(amount=new_amount, currency=self.balance.currency)
        return self._evolve(balance=new_balance)._record(
            AccountDebited(
                aggregate_id=self.id,
                payload=AccountDebitedPayload(
                    amount=amount.amount,
                    currency=amount.currency,
                ),
            )
        )

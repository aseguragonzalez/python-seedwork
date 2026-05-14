import pytest
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.errors import CurrencyMismatchError, InsufficientFundsError
from bank_account.domain.events.account_credited import AccountCredited
from bank_account.domain.events.account_debited import AccountDebited
from bank_account.domain.events.account_opened import AccountOpened
from bank_account.domain.money import Money


def make_account(
    account_id: str = "acc-1",
    amount: float = 100.0,
    currency: str = "EUR",
) -> BankAccount:
    return BankAccount.open(
        id=BankAccountId(account_id),
        initial_balance=Money(amount=amount, currency=currency),
    )


def test_open_account_records_account_opened_event() -> None:
    account = make_account()
    assert len(account.domain_events) == 1
    assert isinstance(account.domain_events[0], AccountOpened)


def test_open_account_sets_initial_balance() -> None:
    account = make_account(amount=200.0, currency="USD")
    assert account.balance == Money(amount=200.0, currency="USD")


def test_credit_records_account_credited_event() -> None:
    account = make_account()
    updated = account.credit(Money(amount=50.0, currency="EUR"))
    assert any(isinstance(e, AccountCredited) for e in updated.domain_events)


def test_credit_increases_balance() -> None:
    account = make_account(amount=100.0)
    updated = account.credit(Money(amount=50.0, currency="EUR"))
    assert updated.balance == Money(amount=150.0, currency="EUR")


def test_debit_records_account_debited_event() -> None:
    account = make_account(amount=100.0)
    updated = account.debit(Money(amount=40.0, currency="EUR"))
    assert any(isinstance(e, AccountDebited) for e in updated.domain_events)


def test_debit_decreases_balance() -> None:
    account = make_account(amount=100.0)
    updated = account.debit(Money(amount=40.0, currency="EUR"))
    assert updated.balance == Money(amount=60.0, currency="EUR")


def test_debit_raises_on_insufficient_funds() -> None:
    account = make_account(amount=10.0)
    with pytest.raises(InsufficientFundsError):
        account.debit(Money(amount=100.0, currency="EUR"))


def test_credit_raises_on_currency_mismatch() -> None:
    account = make_account(currency="EUR")
    with pytest.raises(CurrencyMismatchError):
        account.credit(Money(amount=50.0, currency="USD"))


def test_debit_raises_on_currency_mismatch() -> None:
    account = make_account(currency="EUR")
    with pytest.raises(CurrencyMismatchError):
        account.debit(Money(amount=10.0, currency="USD"))

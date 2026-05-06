from dataclasses import FrozenInstanceError

import pytest

from examples.bank_account.domain.bank_account import BankAccount
from examples.bank_account.domain.bank_account_id import BankAccountId
from examples.bank_account.domain.errors import CurrencyMismatchError, InsufficientFundsError
from examples.bank_account.domain.events.account_opened import AccountOpened
from examples.bank_account.domain.money import Money


def make_account(balance: float = 100.0, currency: str = "EUR") -> BankAccount:
    return BankAccount.open(BankAccountId("acc-1"), Money(amount=balance, currency=currency))


def test_open_records_domain_event() -> None:
    account = make_account()
    assert len(account.domain_events) == 1
    assert isinstance(account.domain_events[0], AccountOpened)


def test_domain_events_is_immutable() -> None:
    account = make_account()
    assert isinstance(account.domain_events, tuple)


def test_credit_appends_event() -> None:
    account = make_account().credit(Money(amount=50.0, currency="EUR"))
    assert len(account.domain_events) == 2


def test_debit_appends_event() -> None:
    account = make_account(200.0).debit(Money(amount=50.0, currency="EUR"))
    assert len(account.domain_events) == 2


def test_is_immutable() -> None:
    account = make_account()
    with pytest.raises(FrozenInstanceError):
        account.domain_events = ()  # type: ignore[misc]


def test_evolve_returns_new_instance() -> None:
    account = make_account()
    credited = account.credit(Money(amount=50.0, currency="EUR"))
    assert credited is not account


def test_evolve_preserves_identity() -> None:
    account = make_account()
    credited = account.credit(Money(amount=50.0, currency="EUR"))
    assert credited == account


def test_record_does_not_mutate_original() -> None:
    account = make_account()
    original_event_count = len(account.domain_events)
    account.credit(Money(amount=50.0, currency="EUR"))
    assert len(account.domain_events) == original_event_count


def test_debit_raises_on_insufficient_funds() -> None:
    account = make_account(balance=50.0)
    with pytest.raises(InsufficientFundsError):
        account.debit(Money(amount=100.0, currency="EUR"))


def test_credit_raises_on_currency_mismatch() -> None:
    account = make_account(currency="EUR")
    with pytest.raises(CurrencyMismatchError):
        account.credit(Money(amount=10.0, currency="USD"))


def test_debit_raises_on_currency_mismatch() -> None:
    account = make_account(currency="EUR")
    with pytest.raises(CurrencyMismatchError):
        account.debit(Money(amount=10.0, currency="USD"))


def test_reconstitute_restores_state_without_events() -> None:
    account = BankAccount.reconstitute(
        id=BankAccountId("acc-1"),
        balance=Money(amount=250.0, currency="EUR"),
    )
    assert account.id == BankAccountId("acc-1")
    assert account.balance == Money(amount=250.0, currency="EUR")
    assert len(account.domain_events) == 0


def test_reconstitute_instance_is_equal_to_open_instance() -> None:
    opened = make_account(balance=100.0)
    reconstituted = BankAccount.reconstitute(
        id=BankAccountId("acc-1"),
        balance=Money(amount=100.0, currency="EUR"),
    )
    assert opened == reconstituted

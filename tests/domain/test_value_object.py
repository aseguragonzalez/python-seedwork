from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime

import pytest

from examples.bank_account.domain.money import EmptyCurrencyError, Money, NegativeAmountError
from seedwork.domain.value_object import ValueObject


def test_equality_same_properties() -> None:
    assert Money(amount=10.0, currency="EUR") == Money(amount=10.0, currency="EUR")


def test_inequality_different_properties() -> None:
    assert Money(amount=10.0, currency="EUR") != Money(amount=20.0, currency="EUR")


def test_inequality_different_currency() -> None:
    assert Money(amount=10.0, currency="EUR") != Money(amount=10.0, currency="USD")


@dataclass(frozen=True, kw_only=True)
class Amount(ValueObject):
    value: float


def test_inequality_different_value_object_types() -> None:
    assert Money(amount=10.0, currency="EUR") != Amount(value=10.0)


def test_inequality_non_value_object() -> None:
    assert Money(amount=10.0, currency="EUR") != "not a value object"


def test_same_reference_is_equal() -> None:
    m = Money(amount=10.0, currency="EUR")
    assert m == m


def test_hash_consistent_with_equality() -> None:
    a = Money(amount=10.0, currency="EUR")
    b = Money(amount=10.0, currency="EUR")
    assert hash(a) == hash(b)


def test_str_representation() -> None:
    m = Money(amount=10.0, currency="EUR")
    result = str(m)
    assert "Money" in result
    assert "10.0" in result
    assert "EUR" in result


@dataclass(frozen=True, kw_only=True)
class DateVO(ValueObject):
    dt: datetime


def test_datetime_equality() -> None:
    dt1 = datetime(2024, 1, 1, tzinfo=UTC)
    dt2 = datetime(2024, 1, 1, tzinfo=UTC)
    assert DateVO(dt=dt1) == DateVO(dt=dt2)


@dataclass(frozen=True, kw_only=True)
class ListVO(ValueObject):
    items: tuple[int, ...]


def test_tuple_property_equality() -> None:
    assert ListVO(items=(1, 2, 3)) == ListVO(items=(1, 2, 3))


def test_tuple_property_inequality() -> None:
    assert ListVO(items=(1, 2, 3)) != ListVO(items=(1, 2))


def test_is_immutable() -> None:
    m = Money(amount=10.0, currency="EUR")
    with pytest.raises(FrozenInstanceError):
        m.amount = 99.0  # type: ignore[misc]


def test_money_raises_on_negative_amount() -> None:
    with pytest.raises(NegativeAmountError):
        Money(amount=-1.0, currency="EUR")


def test_money_raises_on_empty_currency() -> None:
    with pytest.raises(EmptyCurrencyError):
        Money(amount=10.0, currency="")

import pytest
from bank_account.domain.errors import AccountNotFoundError, InsufficientFundsError

from seedwork.domain.domain_error import DomainError


class ConcreteError(DomainError):
    def __init__(self) -> None:
        super().__init__("something went wrong", "CONCRETE_ERROR")


def test_domain_error_code_is_preserved() -> None:
    error = ConcreteError()
    assert error.code == "CONCRETE_ERROR"


def test_domain_error_message_is_preserved() -> None:
    error = ConcreteError()
    assert str(error) == "something went wrong"


def test_domain_error_is_exception() -> None:
    error = ConcreteError()
    assert isinstance(error, Exception)


def test_domain_error_is_raisable() -> None:
    with pytest.raises(DomainError):
        raise ConcreteError()


def test_domain_error_subclass_preserves_code() -> None:
    error = InsufficientFundsError()
    assert error.code == "INSUFFICIENT_FUNDS"


def test_domain_error_subclass_is_exception() -> None:
    error = InsufficientFundsError()
    assert isinstance(error, Exception)


def test_account_not_found_message_contains_id() -> None:
    error = AccountNotFoundError("abc-123")
    assert "abc-123" in str(error)

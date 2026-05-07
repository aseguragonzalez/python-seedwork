from dataclasses import dataclass

from seedwork.domain.domain_error import DomainError
from seedwork.domain.value_object import ValueObject


class NegativeAmountError(DomainError):
    def __init__(self) -> None:
        super().__init__("Amount cannot be negative", "NEGATIVE_AMOUNT")


class EmptyCurrencyError(DomainError):
    def __init__(self) -> None:
        super().__init__("Currency cannot be empty", "EMPTY_CURRENCY")


@dataclass(frozen=True, kw_only=True)
class Money(ValueObject):
    amount: float
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise NegativeAmountError()
        if not self.currency:
            raise EmptyCurrencyError()

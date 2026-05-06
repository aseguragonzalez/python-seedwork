from seedwork.domain.domain_error import DomainError


class InsufficientFundsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Insufficient funds", "INSUFFICIENT_FUNDS")


class CurrencyMismatchError(DomainError):
    def __init__(self, expected: str, received: str) -> None:
        super().__init__(
            f"Currency mismatch: expected {expected}, got {received}",
            "CURRENCY_MISMATCH",
        )


class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} not found", "ACCOUNT_NOT_FOUND")

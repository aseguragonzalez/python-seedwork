from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ValidationErrorDetail:
    code: str
    message: str


class ValidationErrors(Exception):
    def __init__(self, errors: list[ValidationErrorDetail]) -> None:
        self.errors = errors
        super().__init__(repr(errors))

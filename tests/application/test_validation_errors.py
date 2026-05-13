import pytest

from seedwork.application.validation_errors import ValidationErrorDetail, ValidationErrors


def test_validation_errors_stores_details() -> None:
    details = [
        ValidationErrorDetail(code="required", message="Field is required"),
        ValidationErrorDetail(code="max_length", message="Too long"),
    ]
    exc = ValidationErrors(details)
    assert exc.errors == details


def test_validation_errors_is_exception() -> None:
    exc = ValidationErrors([ValidationErrorDetail(code="err", message="bad")])
    with pytest.raises(ValidationErrors):
        raise exc

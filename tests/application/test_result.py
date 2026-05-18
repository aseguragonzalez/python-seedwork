from seedwork.application.commands import Result, ResultError


def test_succeeded_result_is_ok() -> None:
    result = Result.ok()
    assert result.is_ok


def test_failed_result_is_fail() -> None:
    errors = [ResultError(code="ERR", description="Something went wrong")]
    result = Result.failed(errors)
    assert not result.is_ok


def test_failed_result_contains_errors() -> None:
    errors = [ResultError(code="ERR", description="desc")]
    result = Result.failed(errors)
    assert len(result.errors) == 1
    assert result.errors[0].code == "ERR"


def test_succeeded_result_has_no_errors() -> None:
    result = Result.ok()
    assert len(result.errors) == 0


def test_errors_are_immutable_tuple() -> None:
    result = Result.failed(
        [
            ResultError(code="E1", description="d1"),
            ResultError(code="E2", description="d2"),
        ]
    )
    assert isinstance(result.errors, tuple)

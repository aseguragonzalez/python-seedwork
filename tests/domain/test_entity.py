import pytest

from seedwork.domain.entity import Entity, NullEntityIdError


class UserId(str):
    pass


class User(Entity[UserId]):
    pass


class Product(Entity[UserId]):
    pass


def test_entity_raises_when_id_is_none() -> None:
    with pytest.raises(NullEntityIdError):
        User(id=None)  # type: ignore[arg-type]


def test_entity_equality_same_id() -> None:
    user_a = User(id=UserId("1"))
    user_b = User(id=UserId("1"))
    assert user_a == user_b


def test_entity_inequality_different_id() -> None:
    user_a = User(id=UserId("1"))
    user_b = User(id=UserId("2"))
    assert user_a != user_b


def test_entity_inequality_different_type() -> None:
    user = User(id=UserId("1"))
    product = Product(id=UserId("1"))
    assert user != product


def test_entity_inequality_non_entity() -> None:
    user = User(id=UserId("1"))
    assert user != "not an entity"


def test_entity_same_reference_is_equal() -> None:
    user = User(id=UserId("1"))
    assert user == user


def test_entity_hash_consistent_with_equality() -> None:
    user_a = User(id=UserId("1"))
    user_b = User(id=UserId("1"))
    assert hash(user_a) == hash(user_b)

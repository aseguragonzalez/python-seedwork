from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.money import Money

from seedwork.infrastructure.in_memory_repository import InMemoryRepository, RepositorySpy


def make_account(account_id: str = "acc-1", balance: float = 100.0) -> BankAccount:
    return BankAccount.open(BankAccountId(account_id), Money(amount=balance, currency="EUR"))


async def test_save_and_find_by_id() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    account = make_account()

    await repo.save(account)

    found = await repo.find_by_id(BankAccountId("acc-1"))
    assert found is account


async def test_find_by_id_returns_none_for_missing() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()

    result = await repo.find_by_id(BankAccountId("missing"))
    assert result is None


async def test_delete_removes_aggregate() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    account = make_account()
    await repo.save(account)

    await repo.delete_by_id(BankAccountId("acc-1"))

    assert await repo.find_by_id(BankAccountId("acc-1")) is None


async def test_delete_nonexistent_does_not_raise() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    await repo.delete_by_id(BankAccountId("ghost"))


async def test_save_overwrites_existing() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    account = make_account()
    await repo.save(account)

    updated = account.credit(Money(amount=50.0, currency="EUR"))
    await repo.save(updated)

    found = await repo.find_by_id(BankAccountId("acc-1"))
    assert found is updated


async def test_stores_multiple_aggregates_independently() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    a1 = make_account("acc-1", 100.0)
    a2 = make_account("acc-2", 200.0)
    await repo.save(a1)
    await repo.save(a2)

    assert await repo.find_by_id(BankAccountId("acc-1")) is a1
    assert await repo.find_by_id(BankAccountId("acc-2")) is a2


async def test_all_returns_all_saved_aggregates() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    a1 = make_account("acc-1", 100.0)
    a2 = make_account("acc-2", 200.0)
    await repo.save(a1)
    await repo.save(a2)

    assert set(repo.all) == {a1, a2}


async def test_all_returns_empty_when_no_aggregates() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()

    assert list(repo.all) == []


async def test_reset_clears_all_saved_aggregates() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    await repo.save(make_account("acc-1"))
    await repo.save(make_account("acc-2"))

    repo.reset()

    assert list(repo.all) == []
    assert await repo.find_by_id(BankAccountId("acc-1")) is None


def test_in_memory_repository_satisfies_repository_spy_protocol() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    assert isinstance(repo, RepositorySpy)

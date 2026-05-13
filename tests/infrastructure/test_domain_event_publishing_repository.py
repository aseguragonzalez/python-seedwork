from collections.abc import Sequence

from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.money import Money

from seedwork.application.domain_event_bus import DomainEventBusPublisher
from seedwork.domain.domain_event import DomainEvent
from seedwork.domain.repository import Repository
from seedwork.infrastructure.domain_event_publishing_repository import (
    DomainEventPublishingRepository,
)


class InMemoryBankAccountRepository(Repository[BankAccountId, BankAccount]):
    def __init__(self) -> None:
        self._store: dict[BankAccountId, BankAccount] = {}

    async def find_by_id(self, entity_id: BankAccountId) -> BankAccount | None:
        return self._store.get(entity_id)

    async def save(self, aggregate: BankAccount) -> None:
        self._store[aggregate.id] = aggregate

    async def delete_by_id(self, entity_id: BankAccountId) -> None:
        self._store.pop(entity_id, None)


class SpyPublisher(DomainEventBusPublisher):
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: Sequence[DomainEvent]) -> None:
        self.published.extend(events)


async def test_save_publishes_domain_events() -> None:
    inner = InMemoryBankAccountRepository()
    publisher = SpyPublisher()
    repo = DomainEventPublishingRepository(inner, publisher)

    account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
    await repo.save(account)

    assert len(publisher.published) == 1


async def test_save_with_no_events_does_not_publish() -> None:
    """An aggregate with no domain events should not call publish."""
    inner = InMemoryBankAccountRepository()
    publisher = SpyPublisher()
    repo = DomainEventPublishingRepository(inner, publisher)

    # Save once to persist (consumes the event), then save plain copy via inner
    account = BankAccount.open(BankAccountId("acc-4"), Money(amount=10.0, currency="EUR"))
    await inner.save(account)  # bypass publishing repo so events are NOT cleared

    # Create an account-like object with no events by saving it a second time directly
    # (In real code, a reconstituted aggregate has no events)
    from dataclasses import replace as dc_replace

    no_events_account = dc_replace(account, domain_events=())
    await inner.save(no_events_account)

    # Now save via publishing repo — no events, so publish should NOT be called
    await repo.save(no_events_account)
    assert len(publisher.published) == 0


async def test_find_by_id_delegates_to_inner() -> None:
    inner = InMemoryBankAccountRepository()
    publisher = SpyPublisher()
    repo = DomainEventPublishingRepository(inner, publisher)

    account = BankAccount.open(BankAccountId("acc-2"), Money(amount=50.0, currency="EUR"))
    await inner.save(account)

    found = await repo.find_by_id(BankAccountId("acc-2"))
    assert found is account


async def test_find_by_id_returns_none_for_missing() -> None:
    inner = InMemoryBankAccountRepository()
    publisher = SpyPublisher()
    repo = DomainEventPublishingRepository(inner, publisher)

    found = await repo.find_by_id(BankAccountId("nonexistent"))
    assert found is None


async def test_delete_does_not_publish_events() -> None:
    inner = InMemoryBankAccountRepository()
    publisher = SpyPublisher()
    repo = DomainEventPublishingRepository(inner, publisher)

    account = BankAccount.open(BankAccountId("acc-3"), Money(amount=50.0, currency="EUR"))
    await inner.save(account)
    await repo.delete_by_id(BankAccountId("acc-3"))

    assert len(publisher.published) == 0
    assert await inner.find_by_id(BankAccountId("acc-3")) is None

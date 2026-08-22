# Getting Started

This guide walks through building a minimal bounded context with python-seedwork. The running example is a bank account domain that can open accounts, deposit money, and read the balance. For a more complete bank account example, see [`docs/examples/bank_account/`](examples/bank_account/).

## 1. Install

```bash
pip install python-seedwork
```

Requires Python 3.12+.

## 2. Define value objects

Value objects are immutable domain concepts identified entirely by their attributes. Subclass `ValueObject` as a frozen dataclass and override `validate()` to enforce invariants — `ValueObject.__post_init__` calls it automatically.

```python
from dataclasses import dataclass
from seedwork.domain import DomainError, ValueObject


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

    def validate(self) -> None:
        if self.amount < 0:
            raise NegativeAmountError()
        if not self.currency:
            raise EmptyCurrencyError()


Money(amount=10.0, currency="EUR") == Money(amount=10.0, currency="EUR")  # True
Money(amount=10.0, currency="EUR") == Money(amount=20.0, currency="EUR")  # False
```

## 3. Define domain errors

Always subclass `DomainError` with a named class. The `code` string is used for machine-readable error identification at the API boundary.

```python
from seedwork.domain import DomainError


class InsufficientFundsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Insufficient funds", "INSUFFICIENT_FUNDS")


class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} not found", "ACCOUNT_NOT_FOUND")
```

## 4. Define domain events

Domain events record meaningful state changes. Define a typed payload dataclass, then extend `BaseDomainEvent[TPayload]` with a `create()` classmethod that takes plain data and builds the payload internally — the aggregate calls `create()`, never the constructor directly. Name events in past tense.

```python
from dataclasses import dataclass
from typing import Self
from seedwork.domain import BaseDomainEvent


@dataclass(frozen=True, kw_only=True)
class AccountOpenedPayload:
    initial_balance: float
    currency: str


@dataclass(frozen=True)
class AccountOpened(BaseDomainEvent[AccountOpenedPayload]):
    @classmethod
    def create(cls, initial_balance: float, currency: str, aggregate_id: str) -> Self:
        return cls(
            payload=AccountOpenedPayload(initial_balance=initial_balance, currency=currency),
            aggregate_id=aggregate_id,
        )


@dataclass(frozen=True, kw_only=True)
class MoneyDepositedPayload:
    amount: float
    currency: str


@dataclass(frozen=True)
class MoneyDeposited(BaseDomainEvent[MoneyDepositedPayload]):
    @classmethod
    def create(cls, amount: float, currency: str, aggregate_id: str) -> Self:
        return cls(
            payload=MoneyDepositedPayload(amount=amount, currency=currency),
            aggregate_id=aggregate_id,
        )
```

`aggregate_id` is required — every event must be traceable back to the aggregate that raised it. `id` (UUID) and `occurred_at` (UTC timestamp) are generated automatically.

## 5. Build an aggregate root

Aggregate roots are frozen dataclasses. All state-change methods return a new instance — aggregates are fully immutable. Use `_evolve(**changes)._record(*events)` to produce new instances with updated state and appended events. `Entity.validate()` is abstract, so every aggregate must override it — return `None` if there's nothing to check.

Two factory patterns apply: a named constructor (`open`, `create`) for new aggregates, and `reconstitute` for loading from persistence.

```python
from dataclasses import dataclass
from typing import NewType, Self
from seedwork.domain import AggregateRoot


BankAccountId = NewType("BankAccountId", str)


@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(AggregateRoot[BankAccountId]):
    balance: Money

    def validate(self) -> None:
        pass

    @classmethod
    def open(cls, id: BankAccountId, initial_balance: Money) -> Self:
        return cls(id=id, balance=initial_balance)._record(
            AccountOpened.create(
                initial_balance=initial_balance.amount,
                currency=initial_balance.currency,
                aggregate_id=str(id),
            )
        )

    @classmethod
    def reconstitute(cls, id: BankAccountId, balance: Money) -> Self:
        return cls(id=id, balance=balance)  # no domain_events — already published

    def deposit(self, amount: Money) -> Self:
        new_balance = Money(
            amount=self.balance.amount + amount.amount,
            currency=self.balance.currency,
        )
        return self._evolve(balance=new_balance)._record(
            MoneyDeposited.create(
                amount=amount.amount,
                currency=amount.currency,
                aggregate_id=str(self.id),
            )
        )

    def withdraw(self, amount: Money) -> Self:
        if amount.amount > self.balance.amount:
            raise InsufficientFundsError()
        return self._evolve(
            balance=Money(
                amount=self.balance.amount - amount.amount,
                currency=self.balance.currency,
            )
        )
```

## 6. Define the repository interface

Repository interfaces live in the domain layer. Implementations live in infrastructure.

```python
from seedwork.domain import Repository


class BankAccountRepository(Repository[BankAccountId, BankAccount]):
    ...
```

## 7. Define commands and handlers

Commands represent write intentions. The handler's job is orchestration only: load the aggregate, call the domain method, save the returned instance. `CommandHandler` is a structural `Protocol` — the method must be named `handle`.

```python
from dataclasses import dataclass
from seedwork.application import Command, CommandHandler


@dataclass(frozen=True, kw_only=True)
class DepositMoneyCommand(Command):
    account_id: str
    amount: float
    currency: str


class DepositMoneyHandler(CommandHandler[DepositMoneyCommand]):
    def __init__(self, repository: BankAccountRepository) -> None:
        self._repository = repository

    async def handle(self, command: DepositMoneyCommand) -> None:
        account_id = BankAccountId(command.account_id)
        account = await self._repository.find_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(command.account_id)

        updated = account.deposit(Money(amount=command.amount, currency=command.currency))
        await self._repository.save(updated)
        # DomainEventPublishingRepository publishes events after save automatically
```

## 8. Define queries and handlers

Queries are read-only. Each query declares its return type as a type parameter — `QueryBus.ask` is fully typed at the call site with no casts. `QueryHandler` is also a structural `Protocol` — the method must be named `handle`.

Define a dedicated read repository as an ad-hoc `Protocol` in the application layer. Never pass a domain `Repository` to a query handler.

```python
from dataclasses import dataclass
from typing import Protocol
from seedwork.application import Query, QueryHandler


@dataclass(frozen=True)
class BalanceResponse:
    account_id: str
    balance: float
    currency: str


@dataclass(frozen=True, kw_only=True)
class GetBalanceQuery(Query[BalanceResponse]):
    account_id: str


class BankAccountReadRepository(Protocol):
    async def find_balance(self, account_id: str) -> BalanceResponse | None: ...


class GetBalanceHandler(QueryHandler[GetBalanceQuery, BalanceResponse]):
    def __init__(self, repository: BankAccountReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetBalanceQuery) -> BalanceResponse | None:
        return await self._repository.find_balance(query.account_id)
```

## 9. Wire the buses

Use the builders to assemble the bus stack at the composition root. Both builders take the underlying registry — `RegistryCommandBus` / `RegistryQueryBus` — as a constructor argument. Wrap the repository with `DomainEventPublishingRepository` so events are published transparently after every `save`. `InMemoryRepository` lives in `seedwork.testing` — it's meant for tests and prototyping, not production code.

```python
from seedwork.infrastructure import (
    CommandBusBuilder,
    DomainEventPublishingRepository,
    QueryBusBuilder,
    RegistryCommandBus,
    RegistryQueryBus,
)
from seedwork.testing import InMemoryRepository

# Write side — InMemoryRepository is useful for tests and prototyping
repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
publishing_repo = DomainEventPublishingRepository(repo, my_event_bus)

command_bus = (
    CommandBusBuilder(RegistryCommandBus())
    .register(DepositMoneyCommand, DepositMoneyHandler(publishing_repo))
    .with_transaction(uow)
    .build()
)

# Read side
query_bus = (
    QueryBusBuilder(RegistryQueryBus())
    .register(GetBalanceQuery, GetBalanceHandler(read_repo))
    .build()
)
```

`my_event_bus` must satisfy `DomainEventBusPublisher` (`publish(events) -> None`). See [Component Reference](component-reference.md#domaineventbus-family) for the full domain-event coordination story — pairing `DeferredDomainEventBus` with `CommandBusBuilder.with_domain_event_coordination` so events only dispatch after a command succeeds.

## 10. Dispatch

```python
# Commands return Result — DomainError is caught and converted to Result.failed
result = await command_bus.dispatch(
    DepositMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR")
)
if result.is_failed:
    for error in result.errors:
        print(error.code, error.description)

# Queries return the declared result type or None
balance = await query_bus.ask(GetBalanceQuery(account_id="acc-1"))
# balance: BalanceResponse | None  ← inferred, no cast needed
if balance is None:
    ...  # account not found
```

## Next steps

- [`docs/examples/bank_account/`](examples/bank_account/) — complete, self-contained bounded context exercising every building block.
- [Component Reference](component-reference.md) — detailed documentation on every class and protocol.
- [Coding Standards](coding-standards.md) — conventions aligned with DDD and Clean Architecture.

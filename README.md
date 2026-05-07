# python-seedwork

[![PyPI version](https://img.shields.io/pypi/v/python-seedwork)](https://pypi.org/project/python-seedwork/)
[![Python](https://img.shields.io/pypi/pyversions/python-seedwork)](https://pypi.org/project/python-seedwork/)
[![License: MIT](https://img.shields.io/pypi/l/python-seedwork)](LICENSE)
[![CI](https://github.com/aseguragonzalez/python-seedwork/actions/workflows/ci.yml/badge.svg)](https://github.com/aseguragonzalez/python-seedwork/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/aseguragonzalez/python-seedwork/branch/main/graph/badge.svg)](https://codecov.io/gh/aseguragonzalez/python-seedwork)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

DDD and Hexagonal Architecture building blocks for Python. Provides base classes and infrastructure primitives for domain-driven design: entities, aggregates, value objects, domain events, CQRS buses, and more.

## Installation

```bash
pip install python-seedwork
```

Requires Python 3.12+.

The package ships a `py.typed` marker (PEP 561), so mypy and pyright will pick up the inline types automatically — no extra stubs needed.

## Overview

The library is organised into three layers:

| Layer | Package | What it provides |
|---|---|---|
| Domain | `seedwork.domain` | `Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, `DomainError`, `Repository`, `UnitOfWork` |
| Application | `seedwork.application` | `Command`/`Query` CQRS contracts, `Result`, `DomainEventPublisher` |
| Infrastructure | `seedwork.infrastructure` | `RegistryCommandBus`, `RegistryQueryBus`, `TransactionalCommandBus`, `DomainEventPublishingRepository`, builders |

Everything is also re-exported from the top-level `seedwork` package for convenience.

---

## Domain layer

### ValueObject

Immutable domain concept identified by its properties. Subclass as a `@dataclass(frozen=True, kw_only=True)` and add fields directly. Equality and hashing are structural — delegated to the dataclass.

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

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise NegativeAmountError()
        if not self.currency:
            raise EmptyCurrencyError()


Money(amount=10.0, currency="EUR") == Money(amount=10.0, currency="EUR")  # True
Money(amount=10.0, currency="EUR") == Money(amount=20.0, currency="EUR")  # False
```

---

### Entity

Domain object identified by a typed `id`. Two entities of the same class with the same `id` are equal. Subclass as a `@dataclass(frozen=True, eq=False, kw_only=True)` — `eq=False` preserves the identity-based `__eq__` and `__hash__` defined by `Entity`.

```python
from dataclasses import dataclass
from typing import NewType
from seedwork.domain import Entity

BankAccountId = NewType("BankAccountId", str)

@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(Entity[BankAccountId]):
    pass

a = BankAccount(id=BankAccountId("acc-1"))
b = BankAccount(id=BankAccountId("acc-1"))
a == b  # True
```

Passing `None` as `id` raises `NullEntityIdError`.

IDs that need structural validation (e.g. format checks, multi-field IDs) can still use a `ValueObject` subclass as the type parameter — `Entity[TId]` accepts any type.

---

### AggregateRoot

Extends `Entity` with an immutable `domain_events` tuple. All state changes return a new instance — aggregates are fully immutable. Use `_evolve(**changes)` to produce a new instance with updated fields, and `_record(*events)` to append domain events.

Two factory patterns apply: `open`/`create` for new aggregates (includes initial events), and `reconstitute` for loading from persistence (no events — those have already been published).

```python
from dataclasses import dataclass
from typing import Self
from seedwork.domain import AggregateRoot, DomainEventRecord

@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(AggregateRoot[BankAccountId]):
    balance: Money

    @classmethod
    def open(cls, id: BankAccountId, initial_balance: Money) -> Self:
        event = AccountOpened(
            payload=AccountOpenedPayload(
                account_id=id,
                initial_balance=initial_balance.amount,
                currency=initial_balance.currency,
            )
        )
        return cls(id=id, balance=initial_balance, domain_events=(event,))

    def credit(self, amount: Money) -> Self:
        return self._evolve(
            balance=Money(
                amount=self.balance.amount + amount.amount,
                currency=self.balance.currency,
            )
        )._record(
            AccountCredited(
                payload=AccountCreditedPayload(
                    account_id=self.id,
                    amount=amount.amount,
                    currency=amount.currency,
                )
            )
        )

account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
account.domain_events   # tuple[DomainEvent, ...] — immutable

# Reconstitute from persistence — no domain events
account = BankAccount.reconstitute(
    id=BankAccountId("acc-1"),
    balance=Money(amount=100.0, currency="EUR"),
)
account.domain_events   # ()
```

---

### DomainEvent / DomainEventRecord

`DomainEvent` is a `Protocol` — it defines the structural interface (`id: str`, `occurred_at: datetime`) that all domain events satisfy. Concrete events extend `DomainEventRecord`, a frozen dataclass that auto-generates `id` (UUID) and `occurred_at` (UTC timestamp) and carries a typed payload.

```python
from dataclasses import dataclass
from seedwork.domain import DomainEventRecord

@dataclass(frozen=True)
class AccountOpenedPayload:
    account_id: str
    initial_balance: float
    currency: str

@dataclass(frozen=True)
class AccountOpened(DomainEventRecord[AccountOpenedPayload]):
    pass

event = AccountOpened(payload=AccountOpenedPayload("acc-1", 100.0, "EUR"))
event.id          # auto-generated UUID string
event.occurred_at # datetime in UTC
event.payload     # AccountOpenedPayload(account_id="acc-1", ...)
```

---

### DomainError

Base class for typed domain errors. Carries a `code` string for machine-readable identification and a human-readable message. Always subclass with a named class — do not raise `DomainError` directly.

```python
from seedwork.domain import DomainError

class InsufficientFundsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Insufficient funds", "INSUFFICIENT_FUNDS")

class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} not found", "ACCOUNT_NOT_FOUND")

error = InsufficientFundsError()
error.code  # "INSUFFICIENT_FUNDS"
str(error)  # "Insufficient funds"
```

`RegistryCommandBus` catches `DomainError` and converts it to `Result.failed` automatically (see below).

---

### Repository

Generic async CRUD interface parameterised by id type and aggregate type.

```python
from seedwork.domain import Repository

class BankAccountRepository(Repository[BankAccountId, BankAccount]):
    async def find_by_id(self, entity_id: BankAccountId) -> BankAccount | None: ...
    async def save(self, aggregate: BankAccount) -> None: ...
    async def delete_by_id(self, entity_id: BankAccountId) -> None: ...
```

---

### UnitOfWork

Structural `Protocol` for session/transaction boundaries. Implementations must be async context managers — no base class inheritance required. `__aexit__` should commit when `exc_type is None` and roll back otherwise.

```python
from types import TracebackType

class MyUnitOfWork:
    async def __aenter__(self) -> "MyUnitOfWork":
        # open session
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
```

---

## Application layer

### Command / CommandHandler / Result

Commands represent write intentions. Subclass `Command` as a frozen dataclass. `CommandHandler` processes one command type. `Result` carries success or a list of `ResultError` values.

```python
from dataclasses import dataclass
from seedwork.application import Command, CommandHandler, Result, ResultError

@dataclass(frozen=True, kw_only=True)
class OpenAccountCommand(Command):
    account_id: str
    initial_balance: float

class OpenAccountHandler(CommandHandler[OpenAccountCommand]):
    async def execute(self, command: OpenAccountCommand) -> None:
        # perform domain logic, persist, etc.
        ...

# Result usage
result = Result.succeeded()
result.ok   # True

result = Result.failed([ResultError(code="ERR", description="Something went wrong")])
not result.ok   # True
result.errors   # tuple[ResultError, ...]
```

---

### Query / QueryHandler

Queries represent read intentions. Subclass `Query` as a frozen dataclass. `QueryHandler` returns `T | None` — `None` signals absence.

```python
from dataclasses import dataclass
from seedwork.application import Query, QueryHandler

@dataclass(frozen=True, kw_only=True)
class GetAccountQuery(Query):
    account_id: str

@dataclass
class AccountDto:
    account_id: str
    balance: float

class GetAccountHandler(QueryHandler[GetAccountQuery, AccountDto]):
    async def execute(self, query: GetAccountQuery) -> AccountDto | None:
        # fetch from storage ...
        account = ...
        if account is None:
            return None
        return AccountDto(account.id, account.balance.amount)

result = await bus.ask(GetAccountQuery(account_id="acc-1"))
if result is None:
    ...  # not found
```

---

### DomainEventPublisher / DomainEventHandler

`DomainEventPublisher` and `DomainEventHandler` are `Protocol`s — no inheritance required. Any class with the right method signature satisfies the interface.

```python
from collections.abc import Sequence

from seedwork.application import DomainEventPublisher, DomainEventHandler
from seedwork.domain import DomainEvent

class MyPublisher(DomainEventPublisher):
    async def publish(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            # send to message broker, etc.
            ...

class AccountOpenedHandler(DomainEventHandler[AccountOpened]):
    async def handle(self, event: AccountOpened) -> None:
        # send welcome email, update read model, etc.
        ...
```

---

## Infrastructure layer

### RegistryCommandBus

Maps command types to handlers and dispatches asynchronously. `DomainError` exceptions are caught and returned as `Result.failed`; all other exceptions propagate.

```python
from seedwork.infrastructure import RegistryCommandBus

bus = RegistryCommandBus()
bus.register(OpenAccountCommand, OpenAccountHandler())

result = await bus.dispatch(OpenAccountCommand(account_id="acc-1", initial_balance=100.0))
result.ok   # True

# DomainError → Result.failed
result = await bus.dispatch(...)  # handler raises InsufficientFundsError
not result.ok              # True
result.errors[0].code      # "INSUFFICIENT_FUNDS"
```

---

### RegistryQueryBus

Maps query types to handlers and dispatches asynchronously.

```python
from seedwork.infrastructure import RegistryQueryBus

bus = RegistryQueryBus()
bus.register(GetAccountQuery, GetAccountHandler())

result = await bus.ask(GetAccountQuery(account_id="acc-1"))
result is not None  # True when found
```

---

### TransactionalCommandBus

Decorator bus that wraps every dispatch in the `UnitOfWork` context manager. Commit and rollback are the context manager's responsibility.

```python
from seedwork.infrastructure import TransactionalCommandBus

bus = TransactionalCommandBus(inner_bus, unit_of_work)
# async with unit_of_work: dispatch(command)
```

---

### CommandBusBuilder / QueryBusBuilder

Fluent builders for composing middleware stacks. Middleware is applied outermost-first: the first `.with_*()` call becomes the outermost decorator.

```python
from seedwork.infrastructure import CommandBusBuilder

bus = (
    CommandBusBuilder()
    .register(OpenAccountCommand, OpenAccountHandler())
    .with_transaction(uow)
    .build()
)

result = await bus.dispatch(OpenAccountCommand(account_id="acc-1", initial_balance=100.0))
```

```python
from seedwork.infrastructure import QueryBusBuilder

bus = (
    QueryBusBuilder()
    .register(GetAccountQuery, GetAccountHandler())
    .build()
)

result = await bus.ask(GetAccountQuery(account_id="acc-1"))
```

Custom middleware can be added with `.use(middleware)` on both builders. The middleware type is `Callable[[CommandBus], CommandBus]` or `Callable[[QueryBus], QueryBus]`.

---

### DomainEventPublishingRepository

Decorator repository that publishes domain events after `save`. `find_by_id` and `delete_by_id` delegate directly to the inner repository without publishing.

```python
from seedwork.infrastructure import DomainEventPublishingRepository

repo = DomainEventPublishingRepository(inner_repo, publisher)

account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
await repo.save(account)
# inner_repo.save is called, then publisher.publish with account.domain_events
```

---

### InMemoryRepository

Generic in-memory repository implementation backed by a plain dict. Useful for tests and prototyping — no persistence, no external dependencies.

```python
from seedwork.infrastructure import InMemoryRepository

repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()

account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
await repo.save(account)

found = await repo.find_by_id(BankAccountId("acc-1"))   # BankAccount
missing = await repo.find_by_id(BankAccountId("none"))  # None

await repo.delete_by_id(BankAccountId("acc-1"))
```

`InMemoryRepository` satisfies the `Repository` protocol structurally, so it can be used anywhere a `Repository[TId, TAggregate]` is expected without explicit inheritance.

---

## Design decisions

### Structural typing via `Protocol` (PEP 544)

All contracts with no shared implementation are defined as `Protocol` rather than abstract base classes. Implementations do not need to inherit from the seedwork base — any class that satisfies the structural interface is accepted by the type checker.

Protocols in this library:

| Contract | Layer |
|---|---|
| `DomainEvent`, `Repository`, `UnitOfWork` | Domain |
| `DomainEventPublisher`, `DomainEventHandler`, `CommandHandler`, `CommandBus`, `QueryHandler`, `QueryBus` | Application |

`Command` and `Query` remain frozen dataclass bases rather than Protocols — they are semantic DDD markers where nominal (inheritance-based) typing communicates intent more clearly than structural typing.

### TypeVar variance naming (PEP 484)

TypeVars with declared variance carry `_co` (covariant) or `_contra` (contravariant) suffixes as specified by PEP 484. This makes the variance constraint visible at the point of use without navigating to the TypeVar definition:

- `TCommand_contra`, `TQuery_contra`, `TEvent_contra` — handler input parameters are contravariant: a handler of a supertype satisfies a handler of a subtype.
- `TId_contra` — repository ID parameter is contravariant.
- `TResult_co` — query handler result is covariant: a handler returning a subtype satisfies a handler returning a supertype.

### Protocol method bodies (PEP 544)

Protocol method stubs use `...` as body, following PEP 544 convention for `.py` files. Python requires a syntactic body for all function definitions; `...` is the minimal idiomatic form.

---

## Development

### Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
git clone https://github.com/aseguragonzalez/python-seedwork.git
cd python-seedwork
make install
```

### Available commands

| Command | Description |
|---|---|
| `make install` | Install all dependencies (including dev) |
| `make lint` | Run ruff linter |
| `make format` | Format and auto-fix with ruff |
| `make typecheck` | Run pyright type checker |
| `make test` | Run tests with coverage |
| `make test-no-cov` | Run tests without coverage |
| `make clean` | Remove build artifacts and caches |
| `make check` | Run lint, typecheck, and tests |

Run `make help` to list all available commands.

### Project structure

```text
python-seedwork/
├── src/seedwork/
│   ├── domain/        # Entity, AggregateRoot, ValueObject, DomainEvent, DomainError, Repository, UnitOfWork
│   ├── application/   # Command/Query CQRS contracts, Result, DomainEventPublisher
│   └── infrastructure/# RegistryCommandBus, RegistryQueryBus, builders, InMemoryRepository
├── examples/
│   └── bank_account/  # Full working example of a DDD bounded context using seedwork
└── tests/             # Unit tests mirroring the src/ structure
```

### Conventional commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org) specification. Commit messages must use one of these types:

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change with no feature or fix |
| `test` | Adding or updating tests |
| `chore` | Build, tooling, or dependency updates |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `build` | Build system changes |
| `revert` | Revert a previous commit |

Examples:

```text
feat: add TransactionalQueryBus
fix: raise NullEntityIdError when id is None
chore: upgrade ruff to 0.9
```

The `commit-msg` pre-commit hook enforces this format automatically. `python-semantic-release` uses these prefixes to determine the next version and generate the changelog.

### Examples

The `examples/bank_account/` directory contains a complete bounded context built with seedwork — domain model, value objects, aggregate root, domain events, errors, and repository interface. It is the reference implementation used by the test suite and a good starting point when building your own domain.

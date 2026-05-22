# Coding Standards

> These standards apply to projects **built on top of this package** (consuming bounded contexts). They describe how consumer code should use the seedwork building blocks, not how the seedwork library itself is implemented.

## Python baseline

- Python 3.12+. Use `from __future__ import annotations` in all files.
- Immutable value types: frozen dataclasses (`@dataclass(frozen=True)`).
- Async/await throughout application and infrastructure layers.
- Type hints everywhere. No `Any` in domain or application code.
- `Protocol` for ports/contracts. `@dataclass` for data-carrying types.
- `__post_init__` for validation in Commands, Queries, and Value Objects — no validation bus needed.

---

## Do / Don't overview

| Do | Don't |
|---|---|
| `Protocol` for ports | `ABC` for ports (use only for base classes with shared logic) |
| Frozen dataclass for VOs, Commands, Queries | Mutable objects in domain/application |
| `handle()` in handlers | `execute()` (renamed — breaking change) |
| `__post_init__` for validation | Separate validator classes or `ValidationCommandBus` |
| `T_co` / `T_contra` variance suffixes | Plain `T` for covariant/contravariant TypeVars |
| Bus stack: `with_domain_event_coordination → registry` | Skipping `with_domain_event_coordination` in wiring |
| Publish integration events from `DomainEventHandler` | Publish integration events from aggregate |
| `dispatch()` / `discard()` on `DeferredDomainEventBus` | `flush()` / `clear()` (old names) |
| `from seedwork.testing import InMemoryRepository, InMemoryIntegrationEventPublisher` | Import InMemory from `seedwork.infrastructure` |

---

## Domain layer

### Entity

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import NewType
from uuid import UUID

from seedwork.domain import Entity

AccountId = NewType("AccountId", UUID)

@dataclass(frozen=True, eq=False, kw_only=True)
class Account(Entity[AccountId]):
    owner_id: AccountId
    balance: int

    def validate(self) -> None:
        pass  # add domain invariants here if needed
```

> **NewType note.** Typed identifiers (`AccountId = NewType("AccountId", UUID)`) catch mix-ups between `AccountId` and `UserId` at the type-checker level with zero runtime overhead.

### Value Object

```python
from __future__ import annotations
from dataclasses import dataclass

from seedwork.domain import DomainError, ValueObject


class NegativeAmountError(DomainError):
    def __init__(self) -> None:
        super().__init__("Amount cannot be negative", "NEGATIVE_AMOUNT")


@dataclass(frozen=True, kw_only=True)
class Money(ValueObject):
    amount: float
    currency: str

    def validate(self) -> None:
        if self.amount < 0:
            raise NegativeAmountError()
```

- Always `frozen=True` and `kw_only=True`.
- Extend `ValueObject` and put invariants in `validate()` — raise `DomainError` subclasses, never `ValueError`.
- No setters, no mutation methods — return new instances.

### Aggregate

```python
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID

from seedwork.domain import AggregateRoot

@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(AggregateRoot[BankAccountId]):
    owner_id: BankAccountId
    balance: Money

    def validate(self) -> None:
        pass

    @classmethod
    def open(cls, id: BankAccountId, owner_id: BankAccountId, initial_balance: Money) -> BankAccount:
        return cls(id=id, owner_id=owner_id, balance=initial_balance)._record(
            AccountOpened(
                payload=AccountOpenedPayload(
                    initial_balance=initial_balance.amount,
                    currency=initial_balance.currency,
                ),
                aggregate_id=str(id),
            )
        )

    def deposit(self, amount: Money) -> BankAccount:
        new_balance = Money(amount=self.balance.amount + amount.amount, currency=self.balance.currency)
        return self._evolve(balance=new_balance)._record(
            MoneyDeposited(
                payload=MoneyDepositedPayload(amount=amount.amount),
                aggregate_id=str(self.id),
            )
        )
```

- `AggregateRoot` is `frozen=True` — state changes return new instances via `_evolve(**kwargs)`.
- `domain_events` is `tuple[DomainEvent, ...]` (immutable). `_record(*events)` returns a new instance with the events appended.
- `id` is inherited from `Entity[TId]` — do not re-declare it in the subclass.
- The `DomainEventPublishingRepository` reads `domain_events` after each `save()`. The `DeferredDomainEventBus` deduplicates by `event.id` — no manual clearing needed.

### Domain Events

Use a frozen payload dataclass for the event fields. `BaseDomainEvent[TPayload]` provides `id` and `occurred_at` with defaults; `aggregate_id` is a **required** constructor argument — pass it explicitly to identify the emitting aggregate.

```python
from __future__ import annotations
from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True)
class AccountOpenedPayload:
    initial_balance: int
    currency: str


@dataclass(frozen=True)
class AccountOpened(BaseDomainEvent[AccountOpenedPayload]):
    pass
```

Usage from the aggregate:

```python
AccountOpened(
    payload=AccountOpenedPayload(initial_balance=100, currency="EUR"),
    aggregate_id=str(self.id),   # required — identifies the emitting aggregate
)
```

- **No `type` or `version` fields** — domain events are internal to the bounded context. Routing is done with `isinstance` / `type()`.
- Named in past tense: `AccountOpened`, `MoneyDeposited`.

### Repository

```python
from __future__ import annotations
from typing import Protocol
from .account import BankAccount

class BankAccountRepository(Repository[BankAccountId, BankAccount], Protocol):
    pass
```

- `Protocol` with `Repository[BankAccountId, BankAccount]` as base — structural typing. The method signatures (`find_by_id`, `save`, `delete_by_id`) are inherited from `Repository`; no need to redeclare them.
- `pass` body is intentional: inheriting `Repository[TId, TAgg]` already carries the full contract. Redeclaring methods is redundant and couples the port to the base class's naming.
- Returns domain types, never ORM models.

### Errors

```python
from seedwork.domain import DomainError

class InsufficientFundsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Insufficient funds", "INSUFFICIENT_FUNDS")

class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} not found", "ACCOUNT_NOT_FOUND")
```

- Extend `DomainError`, the base domain exception type.
- The `RegistryCommandBus` catches `DomainError` and wraps it in a failed `Result`.
- Override `__init__` to bake in a stable `code` string — call sites only supply domain-specific arguments.

---

## Application layer

### Command and handler

```python
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from seedwork.application import Command, CommandHandler
from seedwork.domain import DomainError


class InvalidInitialBalanceError(DomainError):
    def __init__(self) -> None:
        super().__init__("initial_balance must be non-negative", "INVALID_INITIAL_BALANCE")


@dataclass(frozen=True, kw_only=True)
class OpenAccountCommand(Command):
    account_id: str
    initial_balance: float
    currency: str

    def __post_init__(self) -> None:
        if self.initial_balance < 0:
            raise InvalidInitialBalanceError()

class OpenAccountCommandHandler(CommandHandler[OpenAccountCommand]):
    def __init__(self, repository: BankAccountRepository) -> None:
        self._repository = repository

    async def handle(self, command: OpenAccountCommand) -> None:
        account = BankAccount.open(
            id=BankAccountId(command.account_id),
            owner_id=BankAccountId(command.account_id),
            initial_balance=Money(amount=command.initial_balance, currency=command.currency),
        )
        await self._repository.save(account)
```

- Method name is `handle()`, **not** `execute()`.
- `__post_init__` validates the command before the handler runs — raise `DomainError` subclasses so the bus converts failures into `Result.failed`.
- `handle()` returns `None`. The bus wraps the outcome in `Result.ok()` on success or `Result.failed(errors)` on `DomainError`.

### Query and handler

```python
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from seedwork.application import Query, QueryHandler

@dataclass(frozen=True, kw_only=True)
class GetAccountQuery(Query[AccountView]):
    account_id: str

@dataclass(frozen=True, kw_only=True)
class AccountView:
    id: str
    balance: float

class GetAccountQueryHandler(QueryHandler[GetAccountQuery, AccountView]):
    def __init__(self, repository: AccountReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetAccountQuery) -> AccountView | None:
        return await self._repository.find_view(query.account_id)
```

- `handle()` returns `T | None` — the `Maybe` equivalent in Python.
- Query handlers read only — no state mutations, no domain events.

### Result

```python
# Command bus returns Result — inspect at the entry point
result = await command_bus.dispatch(command)

if result.is_failed:      # @property bool
    return error_response(result.errors)

# also: result.is_ok
```

`Result.ok()` — success. `Result.failed(errors)` — domain failure. Both are class methods.
`result.is_ok` and `result.is_failed` are `@property` on the dataclass (no parentheses).

### CommandBus wiring

```python
from seedwork.infrastructure import CommandBusBuilder, RegistryCommandBus

registry = RegistryCommandBus()
command_bus = (
    CommandBusBuilder(registry)
    .register(OpenAccountCommand, OpenAccountCommandHandler(repository))
    .with_transaction(uow)                      # optional — TransactionalCommandBus
    .with_domain_event_coordination(event_bus)  # DomainEventCoordinatorCommandBus
    .build()
)
```

Order: `with_transaction` (outermost) → `with_domain_event_coordination` → registry (innermost).

### Execution context — correlationId propagation

`correlation_id` is a cross-cutting tracing concern set at the entry point. The `Command` does **not** carry it.

```python
# shared module, e.g. request_context.py
from contextvars import ContextVar
from uuid import uuid4

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

# Entry point (API controller, subscriber)
def set_correlation_id(incoming_id: str | None = None) -> None:
    correlation_id.set(incoming_id or str(uuid4()))
```

`contextvars.ContextVar` propagates automatically through asyncio tasks — no explicit parameter threading needed.

---

### Domain Event handler (in-process)

```python
from seedwork.application import DomainEventHandler
from .events import AccountOpened
from .request_context import correlation_id as _correlation_id

class AccountOpenedDomainEventHandler(DomainEventHandler[AccountOpened]):
    def __init__(
        self,
        publisher: IntegrationEventPublisher,
        task_scheduler: TaskScheduler,
    ) -> None:
        self._publisher = publisher
        self._task_scheduler = task_scheduler

    async def handle(self, event: AccountOpened) -> None:
        ie = AccountOpenedIntegrationEvent.from_domain_event(event)
        await self._publisher.publish([ie])
        task = SendWelcomeEmailTask.from_domain_event(event)
        await self._task_scheduler.schedule(task)
```

- Injected with `IntegrationEventPublisher` and/or `TaskScheduler` — not with a repository.
- Runs synchronously inside the same transaction (dispatched by `DomainEventBus.dispatch()`).
- `_correlation_id.get()` reads from the ambient ContextVar — set once per request at the entry point.

### Integration Events

Integration events cross bounded-context boundaries with eventual consistency via the outbox pattern.

**Concrete event — use `BaseIntegrationEvent` and a `from_domain_event()` factory:**

```python
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from seedwork.application.integration_events import BaseIntegrationEvent
from .request_context import correlation_id as _correlation_id

if TYPE_CHECKING:
    from .events import AccountOpened


class AccountOpenedIntegrationEvent(BaseIntegrationEvent):
    TYPE: ClassVar[str] = "bank_account.account_opened"
    VERSION: ClassVar[str] = "1.0"

    @classmethod
    def from_domain_event(cls, event: AccountOpened) -> AccountOpenedIntegrationEvent:
        return cls(
            type=cls.TYPE,
            version=cls.VERSION,
            aggregate_id=event.aggregate_id,
            payload={
                "account_id": event.aggregate_id,
                "initial_balance": event.payload.initial_balance,
                "currency": event.payload.currency,
            },
            correlation_id=_correlation_id.get(str(uuid4())),  # from execution context
            causation_id=event.id,                              # domain event that caused this
        )
```

**Consumer side (Subscriber entrypoint):**

```python
from seedwork.application import IntegrationEventHandler

class AccountOpenedIntegrationEventHandler(IntegrationEventHandler[AccountOpenedIntegrationEvent]):
    async def handle(self, event: AccountOpenedIntegrationEvent) -> None:
        # React to an integration event from another bounded context
        ...
```

Key rules:

- `correlation_id` from execution context (`ContextVar`) — not from the domain event.
- `causation_id` = `event.id` (the domain event that triggered this).
- `publish()` takes a `Sequence[IntegrationEvent]` — pass `[event]` even for a single event.
- Version from day 1; bump on breaking payload changes.

### Background Tasks

Background tasks represent work executed reliably but asynchronously within the same service.

```python
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from seedwork.application.background_tasks import BaseBackgroundTask
from .request_context import correlation_id as _correlation_id

if TYPE_CHECKING:
    from .events import AccountOpened


class SendWelcomeEmailTask(BaseBackgroundTask):
    TYPE: ClassVar[str] = "send_welcome_email"

    @classmethod
    def from_domain_event(cls, event: AccountOpened) -> SendWelcomeEmailTask:
        return cls(
            type=cls.TYPE,
            payload={"account_id": event.aggregate_id},
            correlation_id=_correlation_id.get(str(uuid4())),
            causation_id=event.id,
        )


class SendWelcomeEmailTaskHandler(TaskHandler[SendWelcomeEmailTask]):
    async def handle(self, task: SendWelcomeEmailTask) -> None:
        # idempotent — may be retried
        ...
```

Key rules:

- `TYPE` class attribute as discriminator for routing.
- Schedule from a `DomainEventHandler` via `await task_scheduler.schedule(task)`.
- Design handlers **idempotent** — the task runner may deliver more than once.

---

## Infrastructure layer

### Repository implementation

```python
from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

class SqlAlchemyBankAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: BankAccountId) -> BankAccount | None:
        row = await self._session.get(AccountModel, str(id))
        return _to_domain(row) if row else None

    async def save(self, account: BankAccount) -> None:
        model = _to_model(account)
        await self._session.merge(model)
```

### DomainEventPublishingRepository

Decorates a repository to publish domain events after each save:

```python
from seedwork.infrastructure import DomainEventPublishingRepository

publishing_repo = DomainEventPublishingRepository(
    SqlAlchemyAccountRepository(session),
    event_bus,  # satisfies DomainEventBusPublisher
)
```

- Takes `DomainEventBusPublisher` (the segregated interface).
- After `save()`, reads `aggregate.domain_events` and calls `event_bus.publish(events)`.
- The command handler remains unaware of event publishing.

### Full wiring example

```python
from seedwork.infrastructure import (
    CommandBusBuilder,
    DeferredDomainEventBus,
    DomainEventPublishingRepository,
    RegistryCommandBus,
)
from seedwork.testing import InMemoryIntegrationEventPublisher, InMemoryTaskScheduler

event_bus = DeferredDomainEventBus()

publisher = InMemoryIntegrationEventPublisher()   # or OutboxIntegrationEventPublisher
scheduler = InMemoryTaskScheduler()               # or OutboxTaskScheduler
scheduler.register(SendWelcomeEmailTask.TYPE, SendWelcomeEmailTaskHandler())

event_bus.subscribe(AccountOpened, AccountOpenedDomainEventHandler(publisher, scheduler))

account_repo = DomainEventPublishingRepository(
    SqlAlchemyBankAccountRepository(session),
    event_bus,
)

registry = RegistryCommandBus()
command_bus = (
    CommandBusBuilder(registry)
    .register(OpenAccountCommand, OpenAccountCommandHandler(account_repo))
    .with_transaction(uow)
    .with_domain_event_coordination(event_bus)
    .build()
)
```

`dispatch()` processes the buffered events; `discard()` clears without processing. The buffer is a `dict[str, DomainEvent]` keyed by `event.id` — saving the same aggregate twice does not duplicate events.

### InMemory implementations (tests)

All InMemory types are in `seedwork.testing`, not `seedwork.infrastructure`:

```python
from seedwork.testing import (
    InMemoryRepository,       # + RepositorySpy (all, reset)
    InMemoryIntegrationEventPublisher,  # + IntegrationEventPublisherSpy (published, reset)
    InMemoryTaskScheduler,    # + TaskSchedulerSpy (scheduled, register, execute_scheduled, reset)
    InMemoryIntegrationEventOutboxRepository,
    InMemoryTaskOutboxRepository,
)
```

```python
# spy usage in tests
publisher = InMemoryIntegrationEventPublisher()
scheduler = InMemoryTaskScheduler()
scheduler.register(SendWelcomeEmailTask.TYPE, SendWelcomeEmailTaskHandler())

await command_bus.dispatch(OpenAccountCommand(...))

assert len(publisher.published) == 1
assert publisher.published[0].type == "bank_account.account_opened"

await scheduler.execute_scheduled()   # executes all scheduled tasks in-process
assert len(scheduler.scheduled) == 0  # tasks were consumed
```

- `InMemoryIntegrationEventPublisher` is spy-only — do not execute, integration events target other bounded contexts.
- `InMemoryTaskScheduler` supports both spy inspection (`scheduled`) and execution (`execute_scheduled()`).
- `reset()` clears state between tests.

---

## Naming conventions

| Concept | Convention | Example |
|---|---|---|
| Aggregate / Entity | `PascalCase` | `BankAccount`, `Transaction` |
| Value Object | `PascalCase` | `Money`, `BankAccountId` |
| Domain Event | Past tense `PascalCase` | `AccountOpened`, `MoneyDeposited` |
| Domain Event Payload | Past tense + `Payload` suffix | `AccountOpenedPayload` |
| Integration Event | Past tense + `IntegrationEvent` suffix | `AccountOpenedIntegrationEvent` |
| Command | Imperative + `Command` | `OpenAccountCommand` |
| Query | Noun phrase + `Query` | `GetBalanceQuery` |
| Command Handler | Imperative + `Handler` | `OpenAccountHandler` |
| Query Handler | Noun phrase + `Handler` | `GetBalanceHandler` |
| Domain Event Handler | Noun phrase + `DomainEventHandler` | `AccountOpenedDomainEventHandler` |
| Background Task | Imperative + `Task` | `SendWelcomeEmailTask` |
| Task Handler | Imperative + `TaskHandler` | `SendWelcomeEmailTaskHandler` |
| Repository (port) | `{Aggregate}Repository` | `BankAccountRepository` |
| Repository (impl) | `{ORM}{Aggregate}Repository` | `SqlAlchemyBankAccountRepository` |
| Module file | `snake_case.py` | `bank_account_repository.py` |

---

## File / folder structure

```text
src/
  domain/
    bank_account.py          # AggregateRoot + domain logic
    bank_account_id.py       # Value Object / NewType
    money.py                 # Value Object
    events/
      account_opened.py      # DomainEvent + payload dataclass
    errors.py
    bank_account_repository.py  # Repository Protocol
  application/
    open_account/
      open_account_command.py
      open_account_handler.py
    get_balance/
      get_balance_query.py
      get_balance_handler.py
    account_opened_domain_event_handler.py
    account_opened_integration_event.py
    send_welcome_email/
      send_welcome_email_task.py
      send_welcome_email_task_handler.py
    request_context.py        # ContextVar for correlationId
  infrastructure/
    sqlalchemy_bank_account_repository.py
    outbox_integration_event_publisher.py
    outbox_task_scheduler.py
    composition_root.py
tests/
  unit/
    domain/
    application/
  integration/
    infrastructure/
```

---

## Design decisions

### Protocols over ABCs

Python ABCs enforce implementation via `isinstance` checks. `Protocol` achieves structural subtyping — the implementor never imports the port. This is the correct dependency-inversion direction for hexagonal architecture.

Use ABCs only when a base class carries shared, non-trivial logic (e.g., `BaseBackgroundTask`, `BaseDomainEvent`, `AggregateRoot`).

```python
# Port — Protocol, zero coupling to domain
# 'pass' body: Repository[BankAccountId, BankAccount] already carries the contract
class BankAccountRepository(Repository[BankAccountId, BankAccount], Protocol):
    pass

# Adapter — no import of the Protocol required
class SqlAlchemyBankAccountRepository:
    async def find_by_id(self, id: BankAccountId) -> BankAccount | None:
        ...
```

### TypeVar variance naming

When a generic `Protocol` is covariant or contravariant, name the TypeVar explicitly:

```python
from typing import TypeVar

T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)

class QueryHandler(Protocol[T_contra, T_co]):
    async def handle(self, query: T_contra) -> T_co: ...
```

### Spy interfaces for testing

```python
from typing import Protocol, runtime_checkable
from seedwork.testing import RepositorySpy

# RepositorySpy is @runtime_checkable — isinstance() works at runtime
assert isinstance(repo, RepositorySpy)
assert len(repo.all) == 1

repo.reset()  # between tests
```

Keep spy interfaces out of production code paths — import them only in tests and InMemory implementations.

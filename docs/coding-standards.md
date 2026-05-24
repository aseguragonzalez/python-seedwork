# Coding Standards

> These standards apply to projects **built on top of this package** (consuming bounded contexts). They describe how consumer code should use the seedwork building blocks, not how the seedwork library itself is implemented.

## Python baseline

- Python 3.12+. Use `from __future__ import annotations` in all files.
- Immutable value types: frozen dataclasses (`@dataclass(frozen=True)`).
- Async/await throughout application and infrastructure layers.
- Type hints everywhere. No `Any` in domain or application code.
- `Protocol` for ports/contracts. `@dataclass` for data-carrying types.
- `__post_init__` for validation in all dataclasses (Commands, Queries, Value Objects, and others).

---

## Do / Don't overview

| Do | Don't |
|---|---|
| `Protocol` for ports | `ABC` for ports (use only for base classes with shared logic) |
| Frozen dataclass for immutability (VOs, Commands, Queries, Aggregates, Entities, ...) | `@dataclass` without `frozen=True` |
| `__post_init__` for validation | Dedicated validator classes or external validation layers |
| `T_co` / `T_contra` variance suffixes | Plain `T` for covariant/contravariant TypeVars |
| Publish integration events from `DomainEventHandler` | Publish integration events from aggregate |

---

## Domain layer

### Entity

An `Entity` is a domain object with a durable identity — two instances with the same `id` are the same entity regardless of their other fields. `eq=False` on the dataclass delegates equality to the inherited `Entity.__eq__`, which compares by `id` only.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import NewType
from uuid import UUID

from seedwork.domain import Entity

AccountId = NewType("AccountId", UUID)
UserId = NewType("UserId", UUID)

@dataclass(frozen=True, eq=False, kw_only=True)
class Account(Entity[AccountId]):
    owner_id: UserId
    balance: int

    def validate(self) -> None:
        pass  # add domain invariants here if needed
```

#### Key points

- `id` is inherited from `Entity[TId]` — do not re-declare it in the subclass.
- `eq=False` is required — equality is by identity, not by field values.
- Domain logic (invariants, rules) lives in `validate()`, not in handlers.
- Use `NewType` for typed identifiers — catches mix-ups between `AccountId` and `UserId` at the type-checker level with zero runtime overhead.

#### Don't

- Re-declare `id` in the subclass.
- Put orchestration, I/O, or repository calls inside an entity.

---

### Value Object

A Value Object models a domain concept with no identity — two instances with the same data are interchangeable. Immutability is enforced by `frozen=True`; validity is enforced at construction via `validate()`.

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

#### Key points

- Always `frozen=True` and `kw_only=True`.
- `validate()` is called by `ValueObject.__post_init__`; subclasses override it to enforce invariants.
- Return new instances from transformation methods — never mutate in place.

#### Do

- Raise `DomainError` subclasses in `validate()`.

#### Don't

- Raise `ValueError` or generic exceptions — always raise `DomainError` subclasses.
- Use a Value Object for a concept that needs to be tracked individually over time — that is an Entity.

---

### Aggregate

`AggregateRoot` extends `Entity` and acts as the consistency boundary of the aggregate cluster — all external writes must go through it. It is a frozen dataclass: every state-change method must return a new instance via `_evolve(**kwargs)._record(*events)`.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import NewType
from uuid import UUID

from seedwork.domain import AggregateRoot

UserId = NewType("UserId", UUID)

@dataclass(frozen=True, eq=False, kw_only=True)
class BankAccount(AggregateRoot[BankAccountId]):
    owner_id: UserId
    balance: Money

    def validate(self) -> None:
        pass

    @classmethod
    def open(cls, id: BankAccountId, owner_id: UserId, initial_balance: Money) -> BankAccount:
        return cls(id=id, owner_id=owner_id, balance=initial_balance)._record(
            AccountOpened.create(
                initial_balance=initial_balance.amount,
                currency=initial_balance.currency,
                aggregate_id=str(id),
            )
        )

    def deposit(self, amount: Money) -> BankAccount:
        new_balance = Money(amount=self.balance.amount + amount.amount, currency=self.balance.currency)
        return self._evolve(balance=new_balance)._record(
            MoneyDeposited.create(
                amount=amount.amount,
                aggregate_id=str(self.id),
            )
        )
```

#### Key points

- `domain_events` is `tuple[DomainEvent, ...]` (immutable). `_record(*events)` returns a new instance with the events appended.
- `id` is inherited from `Entity[TId]` — do not re-declare it in the subclass.
- The `DomainEventPublishingRepository` reads `domain_events` after each `save()`. The `DeferredDomainEventBus` deduplicates by `event.id` — no manual clearing needed.

#### Do

- Use `_evolve(**kwargs)._record(*events)` for all state changes.
- Use class factory methods (`open`, `reconstitute`) — never expose the constructor directly to application code.

#### Don't

- Mutate state in place — `AggregateRoot` is frozen.
- Put orchestration, I/O, or repository calls inside the aggregate.
- Re-declare `id` in the subclass.

---

### Domain Events

A Domain Event represents something that happened in the domain — a meaningful business fact, not a technical operation. Events are always recorded by the aggregate root itself via `_record(*events)`; no external code creates or injects them.

Use a frozen payload dataclass for the event fields. `BaseDomainEvent[TPayload]` provides `id` and `occurred_at` with defaults; `aggregate_id` is a **required** constructor argument — pass it explicitly to identify the emitting aggregate.

```python
from __future__ import annotations
from dataclasses import dataclass

from seedwork.domain.domain_event import BaseDomainEvent


@dataclass(frozen=True)
class AccountOpenedPayload:
    initial_balance: float
    currency: str


@dataclass(frozen=True)
class AccountOpened(BaseDomainEvent[AccountOpenedPayload]):
    @classmethod
    def create(cls, initial_balance: float, currency: str, aggregate_id: str) -> AccountOpened:
        return cls(
            payload=AccountOpenedPayload(initial_balance=initial_balance, currency=currency),
            aggregate_id=aggregate_id,
        )
```

Usage from the aggregate:

```python
AccountOpened.create(
    initial_balance=initial_balance.amount,
    currency=initial_balance.currency,
    aggregate_id=str(self.id),
)
```

#### Key points

- Named in past tense: `AccountOpened`, `MoneyDeposited`.
- Keep payloads minimal — use a frozen payload dataclass with primitive or value object fields.
- Routing is done with `isinstance` / `type()` — no `type` or `version` fields needed.

#### Do

- Use a `create()` classmethod as factory — callers pass plain data, the factory constructs the payload internally. This decouples the aggregate from the payload structure.

#### Don't

- Call the constructor directly from the aggregate — always go through `create()`.
- Add `type` or `version` fields — domain events are internal to the bounded context.
- Create domain events outside the aggregate — handlers and repositories must never instantiate events directly.
- Use domain events to communicate to other services — use Integration Events for that.

> **Deletion note.** Deletion is not automatically a domain event. Use `delete_by_id` for technical removal with no business significance. If deletion is a meaningful domain occurrence (e.g. closing an account), model it as an aggregate behaviour (`account.close()`) that records the event — the handler then calls `save()` or `delete_by_id()` as appropriate. Never use `delete_by_id` when a domain event must be raised.

---

### Repository

A Repository is a domain port — defined in the domain layer as a `Protocol`, implemented in infrastructure. Its sole concern is the persistence of aggregates: it abstracts storage behind a collection-like interface so the domain never depends on a specific technology. Only aggregate roots have repositories; child entities and value objects are persisted as part of their aggregate, never independently.

```python
from __future__ import annotations
from typing import Protocol
from .account import BankAccount

class BankAccountRepository(Repository[BankAccountId, BankAccount], Protocol):
    pass
```

#### Key points

- The interface is defined in the domain layer; the concrete implementation lives in infrastructure.
- `Protocol` with `Repository[TId, TAgg]` as base — structural typing, no coupling between port and adapter.
- Method signatures (`find_by_id`, `save`, `delete_by_id`) are inherited from `Repository`; no need to redeclare them.
- `pass` body is intentional — redeclaring methods is redundant and couples the port to the base class's naming.

#### Don't

- Add query methods (`find_by_email`, `find_by_status`) to the domain repository — define a read port in the application layer.
- Return ORM models from the repository — return domain types only.

---

### Domain Errors

Domain errors represent business rule violations — named, typed, and defined in the domain layer. Each distinct invariant gets its own class extending `DomainError`.

```python
from seedwork.domain import DomainError

class InsufficientFundsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Insufficient funds", "INSUFFICIENT_FUNDS")

class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} not found", "ACCOUNT_NOT_FOUND")
```

#### Key points

- The `code` string is the machine-readable identifier — bake it into `__init__` so call sites only supply domain-specific arguments.
- The `RegistryCommandBus` catches `DomainError` and wraps it in a failed `Result` automatically — handlers never catch them.
- Define one subclass per distinct business rule violation.

#### Don't

- Raise `ValueError` or generic exceptions for business rule violations.
- Catch `DomainError` in the handler — let the bus convert it to `Result.failed`.

---

## Application layer

### Command and handler

A `Command` expresses an intent to change state — it carries the input data and validates it in `__post_init__`. A `CommandHandler` receives a guaranteed-valid command, loads or creates an aggregate, calls the domain method, and saves. No business logic lives in the handler.

```python
from __future__ import annotations
from dataclasses import dataclass
from seedwork.application import Command, CommandHandler
from seedwork.domain import DomainError


class InvalidInitialBalanceError(DomainError):
    def __init__(self) -> None:
        super().__init__("initial_balance must be non-negative", "INVALID_INITIAL_BALANCE")


@dataclass(frozen=True, kw_only=True)
class OpenAccountCommand(Command):
    account_id: str
    owner_id: str
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
            owner_id=UserId(command.owner_id),
            initial_balance=Money(amount=command.initial_balance, currency=command.currency),
        )
        await self._repository.save(account)
```

#### Key points

- The handler's sole responsibility: obtain aggregate (or create new) → call domain method → save. No business logic.
- `__post_init__` validates the command before the handler runs — the handler receives a guaranteed-valid command.
- `handle()` returns `None`. The bus wraps the outcome in `Result.ok()` on success or `Result.failed(errors)` on `DomainError`.

#### Don't

- Put business logic or domain conditions in the handler.
- Call `publish(aggregate.domain_events)` — `DomainEventPublishingRepository` does this automatically after `save()`.
- Return values from `handle()`.

---

### Query and handler

A `Query` expresses an intent to read data — always read-only. A `QueryHandler` returns `T | None` and never loads full aggregates nor triggers side effects.

```python
from __future__ import annotations
from dataclasses import dataclass
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

#### Key points

- `Query[TResult]` is generic — declare the response type on each query subclass.
- `handle()` returns `T | None` — return `None` for not-found cases.
- Use a **read repository** (application-layer port) that returns projections, not the domain repository.

#### Don't

- Load full aggregates just to extract a few fields.
- Trigger side effects from a query handler — no `save()`, no domain events.
- Return domain aggregates as query results.

---

### Result

`Result` is the return type of every command dispatch: `ok` on success, `failed` with typed errors on a domain rule violation. It eliminates unchecked exceptions from the application boundary.

```python
# Command bus returns Result — inspect at the entry point
result = await command_bus.dispatch(command)

if result.is_failed:      # @property bool
    return error_response(result.errors)

# also: result.is_ok
```

#### Key points

- `Result.ok()` — success. `Result.failed(errors)` — domain failure. Both are class methods.
- `result.is_ok` and `result.is_failed` are `@property` on the dataclass (no parentheses).

---

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

#### Key points

- Order: `with_transaction` (outermost) → `with_domain_event_coordination` → registry (innermost).
- `with_domain_event_coordination(event_bus)` calls `dispatch()` on success and `discard()` on failure.

#### Do

- Always use `CommandBusBuilder` — never instantiate bus decorators manually.

#### Don't

- Place `with_domain_event_coordination()` outside `with_transaction()` — events must be dispatched within the open transaction.

---

### Integration Events

An Integration Event communicates a meaningful business fact from this bounded context to the outside world. Unlike domain events (internal, synchronous), integration events cross service boundaries and are delivered asynchronously. They carry a stable, versioned contract: once published, their schema must not break consumers.

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

#### Key points

- `TYPE` and `VERSION` are class-level constants passed to `BaseIntegrationEvent`.
- `correlation_id` from execution context (`ContextVar`) — not from the domain event.
- `causation_id` = `event.id` (the domain event that triggered this).
- `publish()` takes a `Sequence[IntegrationEvent]` — pass `[event]` even for a single event.

#### Do

- Version from day 1; bump on breaking payload changes.
- Use a `from_domain_event()` factory classmethod on the integration event class.

#### Don't

- Publish from the aggregate or the command handler — always publish from `DomainEventHandler`.
- Omit `correlation_id`.
- Mutate an existing integration event schema — introduce a new version instead.

---

### Background Tasks

A Background Task defers work that must happen eventually but does not need to complete within the current request — sending emails, triggering webhooks, calling external APIs. Tasks are written to an outbox before the transaction commits, guaranteeing at-least-once execution by a worker even if the process crashes mid-flight.

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

#### Key points

- `TYPE` class attribute as discriminator for routing.
- `correlation_id` from execution context — not from the domain event.
- `causation_id` = `event.id` (the domain event that triggered this).

#### Do

- Design handlers **idempotent** — the task runner may deliver more than once.
- Schedule from a `DomainEventHandler` via `await task_scheduler.schedule(task)`.

#### Don't

- Schedule tasks from the aggregate or the command handler.
- Omit `correlation_id`.
- Use background tasks to communicate with other services — use integration events for that.

---

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

#### Key points

- `contextvars.ContextVar` propagates automatically through asyncio tasks — no explicit parameter threading needed.
- Set once per request at the entry point; read anywhere via `correlation_id.get()`.

#### Don't

- Thread `correlation_id` through function or handler signatures — use the `ContextVar` directly.
- Read `correlation_id` from the domain event — domain events do not carry it.

---

### DomainEventHandler

A `DomainEventHandler` reacts to a domain event inside the same transaction. It is the only place where integration events are published and background tasks are scheduled — never from the aggregate or the command handler.

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

#### Key points

- Runs synchronously inside the same transaction (dispatched by `DomainEventBus.dispatch()`).
- Both `publish()` and `schedule()` write to the outbox inside the current transaction — actual delivery is eventual.
- `_correlation_id.get()` reads from the ambient ContextVar — set once per request at the entry point.

#### Don't

- Inject a repository into a `DomainEventHandler` — it must not load or save aggregates.
- Read `correlation_id` from the domain event — it does not carry it.

---

## Infrastructure layer

### DomainEventPublishingRepository

Decorates a repository to publish domain events after each save:

```python
from seedwork.infrastructure import DomainEventPublishingRepository

publishing_repo = DomainEventPublishingRepository(
    SqlAlchemyBankAccountRepository(session),
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

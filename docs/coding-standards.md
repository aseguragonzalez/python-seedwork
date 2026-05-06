# Coding Standards

These standards apply to projects built on top of this package.

## Python baseline

- `pyright` with `typeCheckingMode = "strict"` always — no `# type: ignore` in domain or application layers except where unavoidable at generic boundaries (documented in this package itself).
- All domain classes are immutable frozen dataclasses. Use `__post_init__` for validation.
- No `Any` in domain or application layers. Infrastructure may use it only at adapter boundaries (e.g. ORM row dicts).
- `ruff` with `select = ["E", "F", "I", "UP", "B", "SIM", "ANN"]` for linting and formatting.

---

## Do and Don't — Overview

| Do | Don't |
|---|---|
| Keep domain free of framework and infrastructure imports | Import framework types, ORMs, or HTTP in the domain layer |
| One use case = one command/query + one handler | Put multiple use cases in a single handler |
| Return new instances from behavior methods via `_evolve`/`_record` | Mutate aggregate state in place |
| Raise a `DomainError` subclass for domain violations | Raise generic `Exception` or `ValueError` from domain code |
| Name events in past tense (`MoneyDeposited`) | Name events like commands (`DepositMoney`) |
| Reference other aggregates by their ID value object only | Hold object references to other aggregate roots |
| Use primitives in command/query constructors | Leak domain types through port interfaces when avoidable |
| Stack buses: `with_transaction → registry` | Open a transaction without a wrapping bus |
| One public class per file; file name matches class in `snake_case` | Put multiple unrelated classes in one file |

---

## Domain layer

### Entities

- Subclass `Entity[ID]` as `@dataclass(frozen=True, eq=False, kw_only=True)`. The `ID` type parameter can be a `ValueObject` subclass (for IDs with structural rules) or a `NewType` alias over a primitive (for simple typed wrappers with no validation). Prefer `NewType` for IDs that only need nominal typing — it avoids the `.value` accessor and carries zero runtime overhead.
- Equality is by identity only — never compare entities by attributes.
- Use `_evolve(**changes)` to produce a new instance with updated fields. Do not expose public setters.

### Value objects

- Subclass `ValueObject` as `@dataclass(frozen=True, kw_only=True)`. Declare fields directly on the subclass. Use `__post_init__` for validation; raise a `DomainError` subclass on invalid input (co-located in the same file as the value object).
- Equality and hashing are structural and delegated to the dataclass — all fields participate automatically.
- All constructors are keyword-only: `Money(amount=10.0, currency="EUR")`.

### Aggregates

- Subclass `AggregateRoot[ID]` as `@dataclass(frozen=True, eq=False, kw_only=True)`. Use class methods (`open`, `create`, `reconstitute`) as named factories.
- Behavior methods return a new instance — chain `_evolve(state_changes)._record(event)`.
- `reconstitute` class methods pass no `domain_events` — those have already been published.
- Expose only the root to the outside; internal entities and value objects are not shared directly.

### Domain events

- Subclass `DomainEventRecord[TPayload]` as a `@dataclass(frozen=True)`.
- Define `TPayload` as a separate `@dataclass(frozen=True)` with primitive-only fields.
- Name events in past tense (`AccountOpened`, `MoneyDeposited`).
- Pass the payload as `DomainEventRecord(payload=...)` — `id` and `occurred_at` are auto-generated.

### Repositories

- Define repository interfaces in the domain layer, extending `Repository[ID, T]`.
- Implement in infrastructure.
- Do not add query methods that return DTOs or expose persistence details in the interface.

### Errors

- `DomainError` is a base class — always subclass with a named class: `class InsufficientFundsError(DomainError): ...`. Do not raise `DomainError` directly.
- The class name carries the ubiquitous language; `code` carries the external contract identifier for API mapping.
- Do not catch infrastructure exceptions in the domain layer.

---

## Application layer

### Commands and handlers

- One command class per write use case, subclassing `Command` as `@dataclass(frozen=True, kw_only=True)`. The decorator is required — omitting it means fields are not part of `__init__` and construction will fail at runtime.
- One handler implementing `CommandHandler[TCommand]` (Protocol — no inheritance required).
- Handler pattern: load aggregate → call domain method → save the **returned** instance. Event publishing is handled transparently by `DomainEventPublishingRepository` — do not publish events inside handlers.
- Use primitives in commands when the handler constructs domain objects internally. This keeps the port boundary free of domain type coupling.
- Do not put business logic in the handler — only orchestration.

### Queries and handlers

- One query class per read use case, subclassing `Query[TResult]` as `@dataclass(frozen=True, kw_only=True)`. The result type parameter is mandatory — it makes `QueryBus.ask` fully typed with no `Any` at the call site.
- One handler implementing `QueryHandler[TQuery, TResult]` (Protocol — no inheritance required), returning a plain dataclass — never a domain entity or aggregate.
- **Never inject a domain `Repository[TId, TAggregate]` into a query handler.** Define an ad-hoc read repository as a Protocol in the application layer (alongside the query) and implement it in infrastructure. This decouples the read model from the write model and allows read-side optimizations.
- Handlers are read-only: no commands dispatched, no state changed.

### Domain event handlers

- Implement `DomainEventHandler[TEvent]` (Protocol — no inheritance required).
- One concern per handler (e.g. update projection, send notification — these are separate handlers).
- Design for idempotency when the bus may redeliver events.
- Wiring (routing event types to handlers) is the responsibility of the consuming project's composition root.

---

## Infrastructure layer

- Implement `Repository` and `UnitOfWork` here, not in domain.
- Wire `RegistryCommandBus` and `RegistryQueryBus` with handlers via `.register(...)`.
- Compose command buses using `CommandBusBuilder`: `.with_transaction()` wraps the `RegistryCommandBus`.
- Wrap the repository with `DomainEventPublishingRepository` to publish events transparently after `save`.
- Do not put domain or application use-case logic in infrastructure.

---

## Naming conventions

| Artifact | Convention | Example |
|---|---|---|
| Aggregate / Entity | `PascalCase` noun | `BankAccount`, `Transaction` |
| ID (`NewType` or VO) | `<EntityName>Id` | `BankAccountId = NewType("BankAccountId", str)` |
| Value object | `PascalCase` noun | `Money`, `EmailAddress` |
| Domain event | `PascalCase` past tense | `MoneyDeposited`, `AccountOpened` |
| Domain event payload | `<EventName>Payload` | `MoneyDepositedPayload` |
| Command | `PascalCase` verb phrase + `Command` | `DepositMoneyCommand`, `OpenAccountCommand` |
| Query | `Get<Noun>Query` or `Find<Noun>Query` | `GetBalanceQuery`, `FindActiveAccountsQuery` |
| Command / query handler | `<UseCaseName>Handler` | `DepositMoneyHandler`, `GetBalanceHandler` |
| Write repository interface | `<Aggregate>Repository` | `BankAccountRepository` |
| Read repository interface | `<Aggregate>ReadRepository` | `BankAccountReadRepository` |
| Domain error class | `<Context>Error` | `InsufficientFundsError` |
| Domain event handler | `On<EventName>` or by concern | `OnMoneyDeposited`, `UpdateBalanceProjection` |
| File names | `snake_case`, one class per file | `bank_account.py`, `deposit_money_handler.py` |

---

## File and folder structure

```text
src/
└── <bounded_context>/
    ├── domain/
    │   ├── <aggregate>.py
    │   ├── <aggregate>_id.py
    │   ├── value_objects/
    │   │   └── <value_object>.py
    │   ├── events/
    │   │   └── <event_name>.py
    │   └── <aggregate>_repository.py
    ├── application/
    │   └── <use_case>/
    │       ├── <use_case>_command.py            # or _query.py
    │       ├── <use_case>_handler.py
    │       ├── <use_case>_response.py           # plain dataclass (queries only)
    │       └── <aggregate>_read_repository.py   # read port Protocol (queries only)
    └── infrastructure/
        ├── <impl>_<aggregate>_repository.py     # write repository
        └── <impl>_<aggregate>_read_repository.py  # read repository
```

One public class per file. File name matches the exported class name in `snake_case`.

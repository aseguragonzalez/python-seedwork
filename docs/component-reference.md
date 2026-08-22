# Component Reference

All components are exported from the package root (`seedwork`), except the testing layer, which is exported from `seedwork.testing` and is for use in consumer tests only — never import it from production code.

---

## Domain layer

### `Entity[TId]`

- **Role:** Base class for DDD entities. Identity over attributes — two entities are equal when they share the same `id` of the same concrete class, regardless of other fields.
- **Usage:** Subclass as `@dataclass(frozen=True, eq=False, kw_only=True)` and declare `id` via inheritance. `Entity` is an `ABC` with an abstract `validate() -> None` — every subclass must override it (return `None`/`pass` if there are no extra invariants). `Entity.__post_init__` raises `NullEntityIdError` if `id` is `None`, then calls `self.validate()`. **Do not override `__post_init__`** in a subclass — it would shadow the base implementation and silently skip both the null-`id` guard and the `validate()` dispatch unless you remember to call `super().__post_init__()`. Put invariant checks in `validate()` instead.
- **Key methods:** `__eq__` compares by `id` when both objects are the same concrete class. `__hash__` is based on `id`. `_evolve(**changes) -> Self` returns a new instance with the given fields replaced.

### `AggregateRoot[TId]`

- **Role:** Root of an aggregate. Single entry point for state changes. Accumulates domain events without side effects — all behavior methods return new instances.
- **Fields:** `domain_events: tuple[DomainEvent, ...]` — immutable, keyword-only, excluded from `repr`, `hash`, and `eq`. Defaults to `()`.
- **Key methods:** `_evolve(**changes) -> Self` — inherited from `Entity`; produces a new instance with updated fields. `_record(*events) -> Self` — returns a new instance with the given events appended to `domain_events`.
- **Usage pattern:** Use two factory patterns: `open`/`create` for new aggregates — construct the instance, then chain `._record(EventClass.create(...))` to attach the raised event; `reconstitute` for loading from persistence — construct with no `._record(...)` call (those events have already been published). Behavior methods chain `self._evolve(**state_change)._record(EventClass.create(...))` and return the new instance. `DomainEventPublishingRepository` reads `domain_events` and publishes after `save`. Every concrete `AggregateRoot` must still implement `Entity.validate()`.

### `ValueObject`

- **Role:** Immutable domain concept defined entirely by its attributes. Subclass as `@dataclass(frozen=True, kw_only=True)`. Equality and hashing are structural — delegated to the dataclass.
- **Usage:** Declare fields directly on the subclass. Override `validate() -> None` for invariant checks — `ValueObject.__post_init__` calls it automatically, and the default implementation is a no-op, so overriding is optional (unlike `Entity`, which makes it abstract). Raise a `DomainError` subclass on invalid input (co-located in the same file). All fields are keyword-only.

### `DomainEvent` / `BaseDomainEvent[TPayload]`

- `DomainEvent` — Protocol defining the structural interface for domain events: `id: str`, `occurred_at: datetime` and `aggregate_id: str`.
- `BaseDomainEvent[TPayload]` — frozen, keyword-only dataclass. Declares `payload: TPayload` and `aggregate_id: str` (both **required**, no defaults), then `id: str` (defaults to a UUID) and `occurred_at: datetime` (defaults to UTC now).
- **Pattern:** define a frozen payload dataclass, then a frozen event extending `BaseDomainEvent[Payload]` with a `create()` classmethod that takes plain data and builds the payload internally. Name events in past tense. Keep payload fields primitive (serializable).

```python
@dataclass(frozen=True, kw_only=True)
class MoneyDepositedPayload:
    amount: float
    currency: str

@dataclass(frozen=True)
class MoneyDeposited(BaseDomainEvent[MoneyDepositedPayload]):
    @classmethod
    def create(cls, amount: float, currency: str, aggregate_id: str) -> "MoneyDeposited":
        return cls(
            payload=MoneyDepositedPayload(amount=amount, currency=currency),
            aggregate_id=aggregate_id,
        )
```

### `Repository[TId, TAggregate]`

- **Methods:** `find_by_id(entity_id: TId) -> TAggregate | None`, `save(aggregate: TAggregate) -> None`, `delete_by_id(entity_id: TId) -> None`. All are `async`.
- Define a typed sub-interface in the domain layer; implement in infrastructure.

### `UnitOfWork`

- **Protocol** (structural — no inheritance required). Implementations must provide `__aenter__(self) -> Self` and `__aexit__(self, exc_type, exc_val, exc_tb) -> None`. `__aexit__` should commit when `exc_type is None` and roll back otherwise — `TransactionalCommandBus` relies on this contract.

### `DomainError`

- Base `Exception` subclass. Constructor `(message: str, code: str)`. Exposes `self.code`. Always subclass with a named class — `DomainError` itself is not meant to be raised directly.

---

## Application layer

### `Result` / `ResultError`

- `Result.ok()` / `Result.failed(errors: Sequence[ResultError])` — both class methods. `.errors: tuple[ResultError, ...]` (immutable).
- Check with the `is_ok` and `is_failed` **properties** — no parentheses: `if result.is_failed: ...`
- Do not write `if result.ok:` — `ok` is the class method that *builds* a success, so the expression is always truthy and every failure reads as success. `Result` has no `ok` instance attribute at all; accessing `result.ok` returns the bound classmethod object itself, which is always truthy.
- Use for expected domain failures at the application boundary; let infrastructure exceptions propagate.

### `Command` / `CommandBus` / `CommandHandler[TCommand]`

- `Command` — frozen dataclass base. Subclass as `@dataclass(frozen=True, kw_only=True)` and declare fields directly.
- `CommandHandler[TCommand]` — Protocol. `handle(self, command: TCommand) -> None` (async). The method must be named `handle` — buses call it structurally, so a differently named method fails silently at dispatch time rather than at class definition.
- `CommandBus` — Protocol. `dispatch(self, command: Command) -> Result` (async).

### `Query[TResult]` / `QueryBus` / `QueryHandler[TQuery, TResult]`

- `Query[TResult]` — generic frozen dataclass base. Subclass as `@dataclass(frozen=True, kw_only=True)` and declare the result type as a type parameter: `class MyQuery(Query[MyResponse])`.
- `QueryHandler[TQuery, TResult]` — Protocol. `handle(self, query: TQuery) -> TResult | None` (async). Return `None` to signal absence.
- `QueryBus` — Protocol. `ask(self, query: Query[TResult]) -> TResult | None` (async). The return type is inferred from the query's type parameter — no `Any`, no cast at the call site.

### `DomainEventBus` family

- `DomainEventBusPublisher` — Protocol. `publish(self, events: Sequence[DomainEvent]) -> None` (async). Accepts any sequence — tuples from `aggregate.domain_events` are passed directly.
- `DomainEventHandler[TEvent]` — Protocol. `handle(self, event: TEvent) -> None` (async).
- `DomainEventBusSubscriber` — Protocol. `subscribe(self, event_type: type[TEvent], handler: DomainEventHandler[TEvent]) -> None`.
- `DomainEventBus` — Protocol combining both, plus `dispatch() -> None` (async) and `discard() -> None`. `DeferredDomainEventBus` (infrastructure layer) is the concrete implementation.
- Do not inject a `DomainEventBusPublisher` into command handlers — wrap the repository with `DomainEventPublishingRepository` instead.

### `IntegrationEvent` family

- `BaseIntegrationEvent[TPayload]` — frozen, keyword-only dataclass. Declares `type: str`, `version: str`, `aggregate_id: str`, `payload: TPayload`, `correlation_id: str` (all required), then `id` (UUID default), `occurred_at` (UTC now default), `causation_id: str | None = None`, `metadata: dict[str, str] | None = None`.
- `IntegrationEvent[TPayload]` — Protocol mirroring the same structural shape, for adapters that don't want to inherit `BaseIntegrationEvent`.
- `IntegrationEventPublisher` — Protocol. `publish(self, events: Sequence[IntegrationEvent[Any]]) -> None` (async).
- `IntegrationEventHandler[TIntegrationEvent]` — Protocol. `handle(self, event: TIntegrationEvent) -> None` (async).
- Use integration events to notify other bounded contexts; keep them versioned (`version`) and traceable (`correlation_id`/`causation_id`) since, unlike domain events, they cross process/service boundaries.

### `BackgroundTask` family

- `BackgroundTask[TPayload]` — Protocol: `id`, `type`, `payload: TPayload`, `correlation_id`, `causation_id: str | None`, `metadata: dict[str, str] | None`.
- `BaseBackgroundTask[TPayload]` — frozen, keyword-only dataclass implementation of the same shape. `type`, `payload`, `correlation_id` are required; `id` defaults to a UUID; `causation_id`/`metadata` default to `None`.
- `TaskScheduler` — Protocol. `schedule(self, task: BackgroundTask[Any]) -> None` (async).
- `TaskHandler[TTask]` — Protocol. `handle(self, task: TTask) -> None` (async).
- Use for fire-and-forget side effects (e.g. sending an email) triggered from a domain event handler, dispatched through a `TaskScheduler` rather than performed inline.

### `ValidationErrorDetail` / `ValidationErrors`

- `ValidationErrorDetail` — frozen, keyword-only dataclass: `code: str`, `message: str`.
- `ValidationErrors` — `Exception` subclass. Constructor `(errors: list[ValidationErrorDetail])`. Exposes `self.errors`. Use for input-shape validation at the application boundary (e.g. a command's fields), distinct from `DomainError`, which represents a broken domain invariant.

---

## Infrastructure layer

### `RegistryCommandBus`

- Routes commands to handlers via in-process registry keyed by command class.
- `register(command_type, handler)`, `dispatch(command) -> Result`.
- Catches `DomainError` and converts to `Result.failed`. All other exceptions propagate.

```python
bus = RegistryCommandBus()
bus.register(OpenAccountCommand, OpenAccountHandler(repo))

result = await bus.dispatch(OpenAccountCommand(account_id="acc-1", initial_balance=100.0))
result.is_ok  # True

# DomainError → Result.failed
result = await bus.dispatch(...)  # handler raises InsufficientFundsError
result.is_failed       # True
result.errors[0].code  # "INSUFFICIENT_FUNDS"
```

### `RegistryQueryBus`

- Same registry pattern for queries. `register(query_type, handler)`, `ask(query) -> TResult | None`. The bus is generically typed, so the return type matches the registered query handler result type.
- Raises `KeyError` when no handler is registered for the query type.

```python
bus = RegistryQueryBus()
bus.register(GetBalanceQuery, GetBalanceHandler(read_repo))

balance = await bus.ask(GetBalanceQuery(account_id="acc-1"))
# balance: BalanceResponse | None
```

### `TransactionalCommandBus`

- Decorator. Wraps dispatch in the `UnitOfWork` context manager (`async with unit_of_work`). Commit and rollback are the context manager's responsibility.

```python
bus = TransactionalCommandBus(inner=registry_bus, unit_of_work=uow)
# Every dispatch runs inside: async with uow: inner.dispatch(command)
```

### `DomainEventCoordinatorCommandBus`

- Decorator. Pairs a `CommandBus` with a `DomainEventBus` (typically `DeferredDomainEventBus`): after a successful dispatch (`result.is_ok`) it calls `event_bus.dispatch()`, delivering every event deferred during the command; on failure or an exception it calls `event_bus.discard()` instead — a rolled-back command must never leak events to subscribers. An exception is re-raised after discarding.

```python
bus = DomainEventCoordinatorCommandBus(inner=registry_bus, event_bus=deferred_bus)
```

### `DeferredDomainEventBus`

- Concrete `DomainEventBus` implementation. `subscribe(event_type, handler)` registers a handler; `publish(events)` buffers events per-request (backed by a `ContextVar`, so concurrent requests don't cross-contaminate) instead of dispatching immediately; `dispatch()` delivers all buffered events to their subscribed handlers and clears the buffer; `discard()` clears the buffer without dispatching.
- Typically wrapped by `DomainEventPublishingRepository` (as the `event_bus` it publishes into) and paired with `DomainEventCoordinatorCommandBus` (or `CommandBusBuilder.with_domain_event_coordination`) so events only reach handlers once the whole command has committed.

### `DomainEventPublishingRepository[TId, TAggregate]`

- Decorator. Reads `aggregate.domain_events` and calls `event_bus.publish(aggregate.domain_events)` after every `save` (only when there are events to publish). `delete_by_id` and `find_by_id` delegate without side effects. Constructor: `(inner: Repository[TId, TAggregate], event_bus: DomainEventBusPublisher)` — both positional or keyword, but the keyword name is `event_bus`, not `publisher`.

```python
repo = DomainEventPublishingRepository(inner=BankAccountRepositoryImpl(), event_bus=my_event_bus)

account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
await repo.save(account)
# inner_repo.save is called first, then event_bus.publish(account.domain_events)
```

### `CommandBusBuilder`

- Constructor: `(registry: RegistryCommandBus)` — the registry is the innermost bus in the stack, not created implicitly.
- `.register(command_type, handler)` — wire handler on the underlying registry (last registration wins).
- `.with_transaction(unit_of_work)` — add `TransactionalCommandBus`.
- `.with_domain_event_coordination(event_bus)` — add `DomainEventCoordinatorCommandBus`.
- `.use(middleware: Callable[[CommandBus], CommandBus])` — add custom middleware.
- `.build() -> CommandBus` — return assembled bus.
- Declaration order = stack order; first declared = outermost.

```python
bus = (
    CommandBusBuilder(RegistryCommandBus())
    .register(OpenAccountCommand, OpenAccountHandler(repo))
    .register(DepositMoneyCommand, DepositMoneyHandler(repo))
    .with_transaction(uow)
    .build()
)

result = await bus.dispatch(DepositMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR"))
```

### `QueryBusBuilder`

- Constructor: `(registry: RegistryQueryBus)` — same rationale as `CommandBusBuilder`.
- `.register(query_type, handler)` — wire handler.
- `.use(middleware: Callable[[QueryBus], QueryBus])` — add custom middleware.
- `.build() -> QueryBus` — return assembled bus.

```python
bus = (
    QueryBusBuilder(RegistryQueryBus())
    .register(GetBalanceQuery, GetBalanceHandler(read_repo))
    .build()
)

balance = await bus.ask(GetBalanceQuery(account_id="acc-1"))
```

### Outbox family

Implements the [transactional outbox pattern](https://microservices.io/patterns/data/transactional-outbox.html) so integration events and background tasks are persisted in the same transaction as the aggregate change, then delivered by a separate relay process — avoiding dual-write inconsistency between the domain change and the side effect.

- `IntegrationEventOutboxRecord` — frozen, keyword-only dataclass: `id`, `event: IntegrationEvent[Any]`, `status: OutboxStatus`, `attempts: int`, `created_at: datetime`, `last_error: str | None`, `published_at: datetime | None`.
- `OutboxStatus` — `Literal["pending", "published", "failed"]`.
- `IntegrationEventOutboxRepository` — Protocol: `save(event)`, `find_pending(limit=100) -> Sequence[IntegrationEventOutboxRecord]`, `mark_as_published(id)`, `mark_as_failed(id, error)`. Implement against your persistence layer; write it in the same transaction as the aggregate save.
- `OutboxIntegrationEventPublisher` — `IntegrationEventPublisher` implementation that writes to an `IntegrationEventOutboxRepository` instead of publishing directly — pair it with a separate relay/worker that reads `find_pending`, delivers, then calls `mark_as_published`/`mark_as_failed`.
- `TaskOutboxRecord` / `TaskOutboxStatus` (`Literal["pending", "delivered", "failed"]`) / `TaskOutboxRepository` / `OutboxTaskScheduler` — the same pattern for `BackgroundTask` scheduling instead of integration events.

```python
publisher = OutboxIntegrationEventPublisher(repository=my_outbox_repository)
# publisher.publish(events) persists each event as "pending" instead of delivering it directly
```

---

## Testing layer

Exported from `seedwork.testing`, not the top-level `seedwork` package. For use in consumer tests only — never import it from production code. Every in-memory implementation has a matching `*Spy` structural `Protocol` documenting the shape consumers can assert against: an `all`/`published`/`scheduled` collection plus a `reset()` method. `RepositorySpy`, `IntegrationEventPublisherSpy`, and `TaskSchedulerSpy` are `@runtime_checkable`; `IntegrationEventOutboxRepositorySpy` and `TaskOutboxRepositorySpy` are plain `Protocol`s (no `isinstance()` checks against them).

### `InMemoryRepository[TId, TAggregate]` / `RepositorySpy`

- Generic in-memory `Repository` implementation backed by a plain `dict`. Intended for use in tests and as a starting point for proof-of-concept implementations.
- Satisfies the `Repository[TId, TAggregate]` Protocol structurally — no inheritance declaration needed.
- All three `Repository` methods (`find_by_id`, `save`, `delete_by_id`) are `async` and match the contract exactly. Adds `all` (a `Sequence[TAggregate]` snapshot of the store) and `reset()`.

```python
repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
await repo.save(account)
found = await repo.find_by_id(BankAccountId("acc-1"))
```

### `InMemoryIntegrationEventPublisher` / `IntegrationEventPublisherSpy`

- In-memory `IntegrationEventPublisher`. `publish(events)` appends to an internal list; `published` exposes a `Sequence[IntegrationEvent[Any]]` snapshot; `reset()` clears it.

### `InMemoryTaskScheduler` / `TaskSchedulerSpy`

- In-memory `TaskScheduler`. `schedule(task)` appends to an internal list (`scheduled` exposes the snapshot). `register(task_type, handler)` wires a `TaskHandler` per task type; `execute_scheduled()` drains the queue, invoking the registered handler for each task's `type` (silently skipping tasks with no registered handler). `reset()` clears the queue.

### `InMemoryIntegrationEventOutboxRepository` / `IntegrationEventOutboxRepositorySpy`

- In-memory `IntegrationEventOutboxRepository`. `save` stores a new `"pending"` `IntegrationEventOutboxRecord`; `find_pending`/`mark_as_published`/`mark_as_failed` implement the outbox contract in memory. `all` exposes every record regardless of status; `reset()` clears the store.

### `InMemoryTaskOutboxRepository` / `TaskOutboxRepositorySpy`

- Same pattern as `InMemoryIntegrationEventOutboxRepository`, for `TaskOutboxRepository`/`TaskOutboxRecord`/`TaskOutboxStatus`.

# Component Reference

All components are exported from the package root (`seedwork`).

---

## Domain layer

### `Entity[TId]`

- **Role:** Base class for DDD entities. Identity over attributes — two entities are equal when they share the same `id` of the same concrete class, regardless of other fields.
- **Usage:** Subclass as `@dataclass(frozen=True, eq=False, kw_only=True)` and declare `id` via inheritance. Use `__post_init__` for additional validation. Raises `NullEntityIdError` if `id` is `None`.
- **Key methods:** `__eq__` compares by `id` when both objects are the same concrete class. `__hash__` is based on `id`. `_evolve(**changes) -> Self` returns a new instance with the given fields replaced.

### `AggregateRoot[TId]`

- **Role:** Root of an aggregate. Single entry point for state changes. Accumulates domain events without side effects — all behavior methods return new instances.
- **Fields:** `domain_events: tuple[DomainEvent, ...]` — immutable, keyword-only, excluded from `repr`, `hash`, and `eq`. Passed to the constructor when seeding events (e.g. in factory class methods).
- **Key methods:** `_evolve(**changes) -> Self` — inherited from `Entity`; produces a new instance with updated fields. `_record(*events) -> Self` — returns a new instance with the given events appended to `domain_events`.
- **Usage pattern:** Use two factory patterns: `open`/`create` for new aggregates — pass `domain_events=(event,)` in the constructor; `reconstitute` for loading from persistence — pass no `domain_events` (those have already been published). Behavior methods chain `_evolve(state_change)._record(event)` and return the new instance. `DomainEventPublishingRepository` reads `domain_events` and publishes after `save`.

### `ValueObject`

- **Role:** Immutable domain concept defined entirely by its attributes. Subclass as `@dataclass(frozen=True, kw_only=True)`. Equality and hashing are structural — delegated to the dataclass.
- **Usage:** Declare fields directly on the subclass. Use `__post_init__` for validation; raise a `DomainError` subclass on invalid input (co-located in the same file). All fields are keyword-only.

### `DomainEvent` / `DomainEventRecord[TPayload]`

- `DomainEvent` — Protocol defining the structural interface for domain events: `id: str` and `occurred_at: datetime`.
- `DomainEventRecord[TPayload]` — frozen dataclass; declares `payload: TPayload` first, then `id: str` (default UUID) and `occurred_at: datetime` (default UTC now).
- **Pattern:** define a frozen dataclass `Payload`, then a frozen dataclass event extending `DomainEventRecord[Payload]`. Name events in past tense. Keep payload fields primitive (serializable).

```python
@dataclass(frozen=True)
class MoneyDepositedPayload:
    account_id: str
    amount: float
    currency: str

@dataclass(frozen=True)
class MoneyDeposited(DomainEventRecord[MoneyDepositedPayload]):
    pass
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

- `Result.succeeded()` / `Result.failed(errors: list[ResultError])`. Check with `result.ok: bool`. `.errors: tuple[ResultError, ...]` (immutable).
- Use for expected domain failures at the application boundary; let infrastructure exceptions propagate.

### `Command` / `CommandBus` / `CommandHandler[TCommand]`

- `Command` — frozen dataclass base. Subclass as `@dataclass(frozen=True, kw_only=True)` and declare fields directly.
- `CommandHandler[TCommand]` — Protocol. `execute(self, command: TCommand) -> None` (async).
- `CommandBus` — Protocol. `dispatch(self, command: Command) -> Result` (async).

### `Query[TResult]` / `QueryBus` / `QueryHandler[TQuery, TResult]`

- `Query[TResult]` — generic frozen dataclass base. Subclass as `@dataclass(frozen=True, kw_only=True)` and declare the result type as a type parameter: `class MyQuery(Query[MyResponse])`.
- `QueryHandler[TQuery, TResult]` — Protocol. `execute(self, query: TQuery) -> TResult | None` (async). Return `None` to signal absence.
- `QueryBus` — Protocol. `ask(self, query: Query[TResult]) -> TResult | None` (async). The return type is inferred from the query's type parameter — no `Any`, no cast at the call site.

### `DomainEventPublisher`

- Protocol. `publish(self, events: Sequence[DomainEvent]) -> None` (async). Accepts any sequence — tuples from `aggregate.domain_events` are passed directly.
- Do not inject into command handlers — use `DomainEventPublishingRepository` instead.

### `DomainEventHandler[TEvent]`

- Protocol. `handle(self, event: TEvent) -> None` (async).

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
result.ok  # True

# DomainError → Result.failed
result = await bus.dispatch(...)  # handler raises InsufficientFundsError
result.ok              # False
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

### `DomainEventPublishingRepository[TId, TAggregate]`

- Decorator. Reads `aggregate.domain_events` and calls `publisher.publish(aggregate.domain_events)` after every `save`. `delete_by_id` and `find_by_id` delegate without side effects.

```python
repo = DomainEventPublishingRepository(inner=BankAccountRepositoryImpl(), publisher=my_publisher)

account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
await repo.save(account)
# inner_repo.save is called first, then publisher.publish(account.domain_events)
```

### `CommandBusBuilder`

- `.register(command_type, handler)` — wire handler (last registration wins).
- `.with_transaction(unit_of_work)` — add `TransactionalCommandBus`.
- `.use(middleware: Callable[[CommandBus], CommandBus])` — add custom middleware.
- `.build() -> CommandBus` — return assembled bus.
- Declaration order = stack order; first declared = outermost.

```python
bus = (
    CommandBusBuilder()
    .register(OpenAccountCommand, OpenAccountHandler(repo))
    .register(DepositMoneyCommand, DepositMoneyHandler(repo))
    .with_transaction(uow)
    .build()
)

result = await bus.dispatch(DepositMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR"))
```

### `QueryBusBuilder`

- `.register(query_type, handler)` — wire handler.
- `.use(middleware: Callable[[QueryBus], QueryBus])` — add custom middleware.
- `.build() -> QueryBus` — return assembled bus.

```python
bus = (
    QueryBusBuilder()
    .register(GetBalanceQuery, GetBalanceHandler(read_repo))
    .build()
)

balance = await bus.ask(GetBalanceQuery(account_id="acc-1"))
```

### `InMemoryRepository[TId, TAggregate]`

- Generic in-memory `Repository` implementation backed by a plain `dict`. Intended for use in tests and as a starting point for proof-of-concept implementations.
- Satisfies the `Repository[TId, TAggregate]` Protocol structurally — no inheritance declaration needed.
- All three methods (`find_by_id`, `save`, `delete_by_id`) are `async` and match the `Repository` contract exactly.

```python
repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
await repo.save(account)
found = await repo.find_by_id(BankAccountId("acc-1"))
```

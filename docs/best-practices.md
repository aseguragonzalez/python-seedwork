# Best Practices

This guide explains how to use the seedwork package effectively.

## Aggregate design

**Keep aggregates small.** Prefer a focused consistency boundary over a large object graph. Small aggregates are easier to reason about, test, and serialize.

**Reference other aggregates by ID only.** Never hold object references to other aggregate roots. Cross-aggregate operations are coordinated in the application layer (load both, call behavior on each, save both).

**Enforce invariants inside the root.** All rules that must always hold (e.g. `balance >= 0`, required fields) should be checked inside `__post_init__` or behavior methods. Raise a `DomainError` subclass on violation — never allow invalid state to be constructed.

**Behavior methods return new instances.** Aggregates are immutable. Use `_evolve(**changes)` to produce a new instance with updated state, then chain `_record(*events)` to append the corresponding domain events. `DomainEventPublishingRepository` reads `domain_events` and publishes after `save`.

```python
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
```

**Use a static factory for reconstitution.** When loading an aggregate from persistence, use a `reconstitute` class method that passes no events — those have already been published. This ensures each command execution starts with a clean event slate.

```python
@classmethod
def reconstitute(cls, id: BankAccountId, balance: Money) -> Self:
    return cls(id=id, balance=balance)  # no domain_events
```

---

## Commands and handlers

**One command class per write use case.** The handler's job is orchestration: load the aggregate, call the domain method, save. Keep all business logic inside the aggregate.

**Handler pattern:**

```python
class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} not found", "ACCOUNT_NOT_FOUND")

class DepositMoneyHandler(CommandHandler[DepositMoneyCommand]):
    def __init__(self, repository: BankAccountRepository) -> None:
        self._repository = repository

    async def execute(self, command: DepositMoneyCommand) -> None:
        account_id = BankAccountId(command.account_id)
        account = await self._repository.find_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(command.account_id)

        updated = account.credit(Money(amount=command.amount, currency=command.currency))
        await self._repository.save(updated)
        # DomainEventPublishingRepository publishes events automatically
```

**Stack buses in the canonical order.** Use `CommandBusBuilder` to assemble the stack:

```python
bus = (
    CommandBusBuilder()
    .register(DepositMoneyCommand, DepositMoneyHandler(repository))
    .with_transaction(uow)
    .build()
)
```

**Handle domain failures via `Result`.** `RegistryCommandBus` catches `DomainError` thrown by handlers and converts it to `Result.failed`. Infrastructure failures (timeouts, connection drops) propagate as raised exceptions — do not wrap them in `Result`.

```python
result = await bus.dispatch(command)
if not result.ok:
    return JSONResponse({"errors": [{"code": e.code, "description": e.description} for e in result.errors]}, status_code=422)
```

---

## Domain events

**Record events when something meaningful happens.** Use `_record(*events)` inside behavior methods whenever a state change has business significance. Name events in past tense (`MoneyDeposited`, `AccountOpened`).

**Keep event payloads serializable.** Use primitives only in the payload dataclass. Do not embed `ValueObject` instances or aggregate references — serialize their scalar values instead.

```python
@dataclass(frozen=True)
class MoneyDepositedPayload:
    account_id: str   # str, not BankAccountId
    amount: float
    currency: str

@dataclass(frozen=True)
class MoneyDeposited(DomainEventRecord[MoneyDepositedPayload]):
    pass
```

**Event publishing is transparent.** Do not inject `DomainEventPublisher` into command handlers. Wrap the repository with `DomainEventPublishingRepository` at composition time — it reads `aggregate.domain_events` and calls `publisher.publish` after every `save`, keeping handlers free of event-publishing logic.

```python
repository = DomainEventPublishingRepository(BankAccountRepositoryImpl(), my_event_publisher)
```

**`domain_events` is a pure read.** No side effects. It is an immutable tuple on the aggregate instance — each behavior method produces a new instance with an updated tuple.

---

## Queries and read model

**Declare the query with its result type.** `Query` is generic — pass the response type as a type parameter. This makes `QueryBus.ask` fully typed: no `Any`, no cast.

```python
@dataclass(frozen=True, kw_only=True)
class GetBalanceQuery(Query[BalanceResponse]):
    account_id: str

result = await bus.ask(GetBalanceQuery(account_id="acc-1"))
# result: BalanceResponse | None  ← inferred, no cast needed
```

**Never use domain repositories in query handlers.** `Repository[TId, TAggregate]` loads a full aggregate with all its behavior. Queries need a projection — loading an aggregate to extract two fields couples the read model to the write model and prevents read-side optimizations (denormalized views, caches, separate read stores).

Define a read repository as an ad-hoc port in the application layer:

```python
# application/ports.py
class BankAccountReadRepository(Protocol):
    async def find_balance(self, account_id: str) -> BalanceResponse | None: ...
```

Implement it in infrastructure against whatever data source makes sense (SQL view, cache, read store). The domain aggregate is never involved.

**Return plain DTOs — never domain entities.** Response dataclasses should contain only primitive fields.

```python
@dataclass(frozen=True)
class BalanceResponse:
    account_id: str
    balance: float
    currency: str

class GetBalanceHandler(QueryHandler[GetBalanceQuery, BalanceResponse]):
    def __init__(self, repository: BankAccountReadRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetBalanceQuery) -> BalanceResponse | None:
        return await self._repository.find_balance(query.account_id)
```

**Keep query handlers read-only.** Do not dispatch commands or change state inside a query handler. Queries are for reading; commands are for writing.

**Return `None` for absence and authorization failures.** Never reveal whether a resource exists to an unauthorized caller.

```python
result = await query_bus.ask(GetBalanceQuery(account_id=account_id))
if result is None:
    return Response(status_code=404)
return JSONResponse(vars(result))
```

---

## Dependency direction

This is the only rule that must never be broken:

- **Domain layer** — no imports from application or infrastructure. Pure Python, no framework, no database, no HTTP.
- **Application layer** — depends on domain types and abstract ports only. No concrete infrastructure.
- **Infrastructure layer** — implements domain/application interfaces and depends inward. Never imported by domain or application.

```text
Domain ← Application ← Infrastructure
```

---

## Testing

**Domain: unit test aggregates and value objects directly.** No mocks needed. Test that behavior methods return instances with the expected state, raise on invariant violations, and carry the right events.

```python
def test_credit_appends_event() -> None:
    account = BankAccount.open(BankAccountId("acc-1"), Money(amount=100.0, currency="EUR"))
    updated = account.credit(Money(amount=50.0, currency="EUR"))
    assert len(updated.domain_events) == 2
    assert isinstance(updated.domain_events[1], AccountCredited)
    assert updated.balance == Money(amount=150.0, currency="EUR")
```

**Handlers: test with `InMemoryRepository`.** The built-in `InMemoryRepository[TId, TAggregate]` eliminates dict-backed boilerplate. Pair it with a spy `DomainEventPublisher` to assert that the handler saves the correct aggregate state and emits the expected events.

```python
async def test_deposit_credits_account() -> None:
    repo: InMemoryRepository[BankAccountId, BankAccount] = InMemoryRepository()
    publisher = SpyPublisher()
    wrapped_repo = DomainEventPublishingRepository(repo, publisher)

    handler = DepositMoneyHandler(wrapped_repo)
    await handler.execute(DepositMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR"))

    account = await repo.find_by_id(BankAccountId("acc-1"))
    assert account is not None
    assert len(publisher.published) == 1
```

See `examples/bank_account/` for complete examples.

**Integration: wire real buses and in-memory repositories** to validate the full stack (`TransactionalCommandBus → RegistryCommandBus`) when you need to verify bus composition.

---

## Summary

| Area | Practice |
|---|---|
| Aggregates | Small; reference others by ID; enforce invariants; behavior methods return new instances |
| Commands | Thin handlers — orchestration only; load → domain → save returned instance |
| Bus stack | `TransactionalCommandBus → RegistryCommandBus` |
| Events | Past-tense names; serializable primitive payload; published transparently by repository decorator |
| Queries | `Query[TResult]` typed; read repositories (not domain repos); return plain DTOs; no side effects |
| Dependencies | Domain pure; application uses ports; infrastructure implements and points inward |
| Testing | Unit test domain directly; test handlers with `InMemoryRepository` + spy publisher |

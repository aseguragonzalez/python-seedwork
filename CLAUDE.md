# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install        # uv sync + install pre-commit hooks (run once after clone)
make all            # full validation: lint + typecheck + tests + pre-commit hooks
make check          # lint + typecheck + tests (what CI runs)
make pre-commit     # run all pre-commit hooks against all files (includes markdownlint)
make lint           # ruff check src tests docs/examples
make format         # ruff format + ruff check --fix
make typecheck      # pyright
make test           # pytest with coverage (fails below 90%)
make test-no-cov    # pytest without coverage gate
make clean          # remove dist, .coverage, caches, __pycache__
```

Run a single test file or test by name:

```bash
uv run pytest tests/domain/test_entity.py
uv run pytest tests/domain/test_entity.py::test_equality_by_id
```

Commit messages are enforced by a `commit-msg` pre-commit hook using Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`). `python-semantic-release` derives versions and the changelog from these prefixes.

## Architecture

This is a **library** (`src/seedwork/`), not an application. It ships DDD and Hexagonal Architecture building blocks. Consuming projects import from `seedwork` (everything is re-exported from the top-level `__init__.py`).

The library is split into three layers that mirror DDD's dependency rule — domain has no outward imports, application depends only on domain, infrastructure depends on both:

```text
seedwork.domain        → pure Python, no framework
seedwork.application   → CQRS contracts + Result
seedwork.infrastructure → concrete bus/repository implementations
```

`docs/examples/bank_account/` is the canonical reference implementation — a complete bounded context that exercises every building block. Tests in `tests/` exercise the seedwork internals; `docs/examples/` is consumed by those tests as fixtures.

## Key design decisions

**Protocols over ABCs.** All contracts with no shared implementation use `Protocol` (PEP 544). Implementations satisfy them structurally — no inheritance required. The exceptions are `Command`, `Query`, and `ValueObject`/`Entity`/`AggregateRoot`, which use nominal typing because inheritance communicates DDD intent.

**Immutable aggregates.** `AggregateRoot` is a frozen dataclass. Every state-change method must return a new instance via `_evolve(**changes)._record(*events)`. Never mutate in place.

**`Query[TResult]` is generic.** `Query` uses PEP 695 type-parameter syntax. Every query subclass declares its response type: `class GetBalanceQuery(Query[BalanceResponse])`. This makes `QueryBus.ask` fully typed — the return type is inferred at the call site with no `Any` or cast.

**Read repositories are separate ports.** Query handlers must never receive a `Repository[TId, TAggregate]`. Define an ad-hoc `Protocol` read repository in the application layer (alongside the query), returning projections directly. Domain aggregates are only loaded in command handlers.

**Bus middleware uses the decorator pattern.** `CommandBusBuilder` and `QueryBusBuilder` accumulate middleware steps and apply them in reverse order so the first declared step becomes the outermost decorator. `TransactionalCommandBus` wraps `RegistryCommandBus`, not the other way round.

**`DomainEventPublishingRepository` is a repository decorator.** Do not publish events inside command handlers. Wrap the concrete repository at composition time; it reads `aggregate.domain_events` and calls `publisher.publish` after every `save`.

## Type-checking constraints

- `pyright` runs in `typeCheckingMode = "strict"` — no `# type: ignore` in `src/` or `tests/`.
- No `Any` in domain or application layers. Infrastructure may use it only at adapter boundaries (e.g. the registry dict keyed on `type[Query[Any]]`).
- TypeVar suffixes follow PEP 484: `_co` = covariant, `_contra` = contravariant.

## Testing patterns

- Domain: unit-test aggregates and value objects directly — no mocks needed.
- Command handlers: use `InMemoryRepository[TId, TAggregate]` (ships with the library) + a spy `DomainEventPublisher`.
- Query handlers: use an inline in-memory read repository (a plain class satisfying the read `Protocol`).
- Coverage gate is 90% on `src/seedwork/` — running `make test` will fail if it drops below.

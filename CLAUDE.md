# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

All commands below must be run inside the project's `.devcontainer/` (image `mcr.microsoft.com/devcontainers/python:3.13`, `uv` pre-installed, `postCreateCommand: make install`), not directly on the host. This keeps the Python version, `uv` version, and tool versions identical to CI. If you're not already inside the devcontainer, open/rebuild it before running any `make` target or `uv run` command.

## Commands

```bash
make install        # uv sync + install pre-commit hooks (run once after container create)
make all            # full validation: lint + typecheck + tests + pre-commit hooks
make check          # lint + typecheck + tests (what CI runs)
make pre-commit     # run all pre-commit hooks against all files (includes markdownlint)
make lint           # ruff check src tests docs/examples
make format         # ruff format + ruff check --fix
make typecheck      # pyright
make test           # pytest with coverage (fails below 90%)
make test-no-cov    # pytest without coverage gate
make build          # uv build (produces dist/*.whl and dist/*.tar.gz)
make clean          # remove dist, .coverage, caches, __pycache__
```

Run a single test file or test by name:

```bash
uv run pytest tests/domain/test_entity.py
uv run pytest tests/domain/test_entity.py::test_equality_by_id
```

## Maintenance workflow

1. **Analyze** — before writing code, understand the gap or bug and confirm scope.
2. **Open an issue** — use the matching `.github/ISSUE_TEMPLATE/*` (bug report, feature request, question) and apply the labels that match its content (`gh label list` for the current set).
3. **Branch from `main`**, implement the change, keep it scoped to the issue.
4. **Open a PR against `main`** that links the issue (e.g. `Closes #123`), following the description structure in the global git/GitHub conventions (What/Why/How/How to test).
5. **Wait for CI to pass**, then merge — this repo only **squash-merges** (`squash_merge_commit_title: PR_TITLE`, `squash_merge_commit_message: BLANK`).

### PR title / release policy

Because the repo only squash-merges, **the PR title is the only text that becomes the commit message on `main`**, and `python-semantic-release` parses that message to decide whether/how to bump the version (`feat` → minor, `fix`/`perf` → patch, breaking change footer → major, everything else → no release). The title must:

- Use a Conventional Commits prefix from `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert` — enforced by `.github/workflows/pr-title-lint.yml`.
- Be chosen deliberately based on whether the change should trigger a release, not out of habit — a docs-only or tooling change should be `docs:`/`chore:`/`ci:`, not `fix:`/`feat:`.
- Stay in sync with the allowed types in `.pre-commit-config.yaml`'s `conventional-pre-commit` hook, which enforces the same prefixes on individual commit messages via the local `commit-msg` hook (this matters for local development discipline even though only the PR title reaches `main`).

## Documentation language

All documentation in this repo — `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `docs/`, code comments, commit and PR text — is written in **English**, regardless of the language used in the conversation that produced a change.

## Architecture

This is a **library** (`src/seedwork/`), not an application. It ships DDD and Hexagonal Architecture building blocks. Consuming projects import from `seedwork` (everything is re-exported from the top-level `__init__.py`).

The library is split into three layers that enforce the dependency rule of Hexagonal Architecture — domain has no outward imports, application depends only on domain, infrastructure depends on both:

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

**Domain events use a `create()` factory.** Domain event classes expose a `create()` classmethod that accepts plain data and constructs the payload internally. Aggregate methods call `EventClass.create(...)` rather than the constructor directly — this decouples the aggregate from the payload structure.

## Type-checking constraints

- `pyright` runs in `typeCheckingMode = "strict"` — no `# type: ignore` in `src/` or `tests/`.
- No `Any` in domain or application layers. Infrastructure may use it only at adapter boundaries (e.g. the registry dict keyed on `type[Query[Any]]`).
- TypeVar suffixes follow PEP 484: `_co` = covariant, `_contra` = contravariant.

## Testing patterns

- Domain: unit-test aggregates and value objects directly — no mocks needed.
- Command handlers: use `InMemoryRepository[TId, TAggregate]` from `seedwork.testing` — assert on `repo.find_by_id()` and `aggregate.domain_events` directly.
- Query handlers: use an inline in-memory read repository (a plain class satisfying the read `Protocol`).
- Integration and task side-effects: use `InMemoryIntegrationEventPublisher` and `InMemoryTaskScheduler` from `seedwork.testing` — both expose spy attributes (`published`, `scheduled`) and a `reset()` method.
- Coverage gate is 90% on `src/seedwork/` — running `make test` will fail if it drops below.

## Claude Code skills for this repo

No project-scoped skills exist yet under `.claude/skills/`. Candidates worth adding as recurring maintenance tasks come up: one covering the devcontainer check cycle end-to-end (`make all` inside the container), and one for verifying a PR's release-readiness (correct title prefix, linked issue, CI green) before requesting review.

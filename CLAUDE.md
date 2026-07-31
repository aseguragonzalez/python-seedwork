# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

DDD and Hexagonal Architecture building blocks for Python. **This is a library of
abstractions, not a domain application.** Every class is imported/subclassed/composed by
downstream projects — design decisions here are public contracts.

**All work happens inside the devcontainer.** Every command in this document assumes it
runs there, so tool versions match CI exactly. Start it once with:

```bash
devcontainer up --workspace-folder .
```

Then run any `make` target via:

```bash
devcontainer exec --workspace-folder . make <target>
```

(The host also happens to have `uv`/Python available in this environment, but don't rely
on that — the devcontainer is the source of truth for versions, and other environments
running this repo may not have a usable host toolchain at all.)

## Workflow

Every change goes through three stages — never skip straight to code:

1. **Analyze and open the issue.** Understand the request, confirm the understanding with
   the requester, then open (or confirm) a GitHub issue using the matching
   `.github/ISSUE_TEMPLATE/*` with clear, testable acceptance criteria. No PR without a
   linked issue (e.g. `Closes #N`).
2. **Plan before implementing.** Re-read the issue and draft an implementation plan that
   separates **code**, **tests**, and **documentation** as independent tracks built against
   the same agreed contracts (Protocols/signatures decided up front), so the tracks don't
   conflict with each other.
3. **Implement in parallel.** Execute the plan using parallel agents for code, tests, and
   documentation (see `.claude/agents/`) against the contracts fixed in step 2. Subagents
   don't share context with the main conversation or each other — include the fixed
   contract explicitly in every agent's prompt, don't assume they can infer it from one
   another's work.

Additional rules that apply throughout:

- All documentation and GitHub artifacts — issues, PRs, commit messages, code comments —
  are written in English, regardless of the language used in conversation, and are
  **direct and concise**: state the what/why/how, never the conversation or reasoning
  process that led to it. No narrative, no TL;DR filler.
- While analyzing any request, check whether nearby code could be improved. If so, do not
  bundle the improvement into the current change — open a separate issue for it (see the
  `boy-scout` skill).
- For bug reports, analyze the problem and propose a solution before opening an issue for
  it (see the `bug-triage` skill).
- PR review comments (yours or a bot reviewer's) are answered in English, as a reply in the
  same review-comment thread — never a new top-level PR comment.
- This repo only **squash-merges** (`squash_merge_commit_title: PR_TITLE`,
  `squash_merge_commit_message: BLANK`), so **the PR title is the only text that becomes
  the commit message on `main`** — see "Commit and PR conventions" below.
- See `.claude/skills/gh-workflow/SKILL.md` for label taxonomy, identity, reviewer, and
  issue/PR mechanics.

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

## Commit and PR conventions

`python-semantic-release` reads the PR title (the only text that reaches `main`, since the
repo squash-merges) to decide whether — and what kind of — a release ships. Getting the
type wrong is not cosmetic: it either ships a spurious release or silently swallows one
that should have shipped.

- The type **must match the layer actually changed**: `docs:` for changes limited to
  `docs/` or `CLAUDE.md`, `ci:` for pipeline-only changes, `chore:`/`build:` for tooling
  (`Makefile`, `.claude/`, dependency bumps), `fix:`/`feat:` only when `src/seedwork/`
  behaviour changes.
- Use a prefix from `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`,
  `ci`, `build`, `revert` — enforced by `.github/workflows/pr-title-lint.yml` and, for
  individual commits, `.pre-commit-config.yaml`'s `conventional-pre-commit` hook.
- Breaking changes need a `BREAKING CHANGE:` footer (not just `feat!:`/`fix!:` in the
  title) — see the commit-type table in `.claude/skills/gh-workflow/SKILL.md` for the full
  mapping and worked examples.
- Refactors use `refactor:` and must never carry behaviour changes — a refactor must not
  trigger a release.

## Architecture

This is a **library** (`src/seedwork/`), not an application. It ships DDD and Hexagonal Architecture building blocks. Consuming projects import from `seedwork` (everything is re-exported from the top-level `__init__.py`).

The library is split into four layers that enforce the dependency rule of Hexagonal Architecture — domain has no outward imports, application depends only on domain, infrastructure depends on both, testing is a separate consumer-facing toolkit:

- **`src/seedwork/domain/`** — `Entity`, `ValueObject`, `AggregateRoot`, `DomainEvent`, `Repository`, `UnitOfWork`, `DomainError`. Pure Python, no framework, no outward imports.
- **`src/seedwork/application/`** — `Command`/`CommandBus`/`CommandHandler`, `Query[TResult]`/`QueryBus`/`QueryHandler`, `DomainEventBus`, `IntegrationEvent`/`IntegrationEventPublisher`, `BackgroundTask`/`TaskScheduler`, `Result`/`ResultError`, `ValidationErrors`. Depends only on domain.
- **`src/seedwork/infrastructure/`** — `RegistryCommandBus`/`RegistryQueryBus`, `CommandBusBuilder`/`QueryBusBuilder`, `TransactionalCommandBus`, `DomainEventCoordinatorCommandBus`, `DeferredDomainEventBus`, `DomainEventPublishingRepository`, `OutboxIntegrationEventPublisher`, `OutboxTaskScheduler`, `IntegrationEventOutboxRepository`, `TaskOutboxRepository`. Concrete bus/repository implementations; the only layer that may use `Any` at adapter boundaries.
- **`src/seedwork/testing/`** — `InMemoryRepository`, `InMemoryIntegrationEventPublisher`, `InMemoryTaskScheduler`, `InMemoryIntegrationEventOutboxRepository`, `InMemoryTaskOutboxRepository`, and their `*Spy` variants. For use in consumer tests only — never imported from production code.

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

## Claude Code agents and skills for this repo

Agents under `.claude/agents/` implement the parallel code/test/docs tracks from
"Workflow" above, plus two cross-cutting agents:

- **`python-implementer`** — the `src/seedwork/` track, against a fixed contract.
- **`python-test-writer`** — the `tests/` track, against the same contract.
- **`docs-aligner`** — the `docs/` track, against the same contract.
- **`boy-scout`** — finds and either executes or files refactoring opportunities.
- **`bug-analyst`** — investigates a reported defect and proposes a fix before any issue is opened.

Skills under `.claude/skills/`:

- **`gh-workflow`** — the full issue-first workflow: identity, label taxonomy, reviewer, commit-type table, and PR release-readiness checks.
- **`boy-scout`** — when/how to apply the boy-scout rule (execute inline vs. separate issue).
- **`bug-triage`** — the analyze → confirm → issue flow for bug reports.

`.claude/settings.json` (committed, shared across contributors) holds a conservative,
mostly-read-only permissions allowlist (`make *`, `uv run/sync/build`, `git status/diff/log/show/branch`,
read-only `gh`) for these workflows — it deliberately excludes `git commit`/`push` and
`gh issue`/`pr create`, which always prompt. Personal or exploratory permissions belong in
each contributor's own `.claude/settings.local.json` instead.

# Contributing

Thank you for taking the time to contribute. This document explains how to set up the project locally and the conventions to follow when submitting changes.

## Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) — used for dependency management and running tools

## Local setup

```bash
git clone https://github.com/aseguragonzalez/python-seedwork.git
cd python-seedwork
make install
```

`make install` runs `uv sync` and installs the pre-commit hooks (ruff, pyright, conventional-commit).

## Running checks

```bash
make check          # lint + typecheck + tests (recommended before pushing)
make lint           # ruff check src tests docs/examples
make format         # ruff format + auto-fix src tests docs/examples
make typecheck      # pyright
make test           # pytest with coverage
make test-no-cov    # pytest without coverage
```

All checks must pass before opening a pull request.

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) because releases and the changelog are generated automatically by `python-semantic-release`. Use one of the following types:

| Type | When to use |
|---|---|
| `feat` | A new feature visible to users of the package |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | Refactoring with no behavior change |
| `test` | Adding or updating tests |
| `chore` | Tooling, CI, dependencies — no production code |

A breaking change must include `BREAKING CHANGE:` in the commit footer.

Examples:

```text
feat: add InMemoryRepository generic base class
fix: make DomainEvent Protocol attributes read-only
docs: add InMemoryRepository to component reference
```

## Pull request process

1. Fork the repository and create a branch from `main`.
2. Make your changes. Add or update tests to cover the change — the coverage threshold is 90%.
3. Run all checks locally and make sure they pass.
4. Open a pull request against `main`. Describe what changed and why.
5. A maintainer will review and merge once CI is green.

## Design principles

Changes to the library should stay aligned with the project's core goals:

- **Python-idiomatic** — prefer Protocols over ABCs, `T | None` over wrapper types, frozen dataclasses over mutable classes.
- **Zero dependencies** — the package has no runtime dependencies and must stay that way.
- **DDD faithful** — components should map cleanly to DDD concepts. When in doubt, check Evans or Vernon.

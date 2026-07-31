# Contributing

Thank you for taking the time to contribute. This document explains how to set up the project locally and the conventions to follow when submitting changes.

## Prerequisites

- Docker and the [Dev Containers CLI](https://github.com/devcontainers/cli) (`npm install -g @devcontainers/cli`) — all commands in this document run inside the devcontainer, which matches CI's Python/`uv` versions exactly.
- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated as yourself (`gh auth login`) — every issue and pull request is created and managed with `gh`, not the web UI.

## Local setup

```bash
git clone https://github.com/aseguragonzalez/python-seedwork.git
cd python-seedwork
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . make install
```

`make install` runs `uv sync` and installs the pre-commit hooks (ruff, pyright, conventional-commit).

## Running checks

Run any target inside the devcontainer, e.g. `devcontainer exec --workspace-folder . make check`:

```bash
make check          # lint + typecheck + tests (recommended before pushing)
make lint           # ruff check src tests docs/examples
make format         # ruff format + auto-fix src tests docs/examples
make typecheck      # pyright
make test           # pytest with coverage
make test-no-cov    # pytest without coverage
```

All checks must pass before opening a pull request. All documentation and GitHub artifacts — issues, pull requests, commit messages, code comments — must be written in English.

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) because this repo only squash-merges, so the **PR title** is the only text `python-semantic-release` ever sees to decide releases and the changelog. Pick the type by which layer actually changed, not by habit — see `CLAUDE.md`'s "Commit and PR conventions" and `.claude/skills/gh-workflow/SKILL.md` for the full table:

| Type | When to use |
|---|---|
| `feat` | A new feature visible to users of the package (`src/seedwork/`) |
| `fix` | A bug fix (`src/seedwork/`) |
| `docs` | Documentation only (`docs/`, `README.md`, `CLAUDE.md`) |
| `refactor` | Refactoring with no behavior change |
| `test` | Adding or updating tests |
| `ci` | CI/pipeline-only changes |
| `chore` | Tooling, dependencies, `.claude/` — no production code |

A breaking change must include `BREAKING CHANGE:` in the commit footer.

Examples:

```text
feat: add InMemoryRepository generic base class
fix: make DomainEvent Protocol attributes read-only
docs: add InMemoryRepository to component reference
```

## Pull request process

1. Start from a GitHub issue: every pull request must reference an existing issue (e.g. `Closes #123`) describing the problem or request it addresses. Open one first if none exists (see `CLAUDE.md` — "Workflow").
2. Branch from `main`. One logical change per pull request.
3. Add or update tests to cover the change — the coverage threshold is 90%.
4. Run `make check` inside the devcontainer and make sure it passes (CI runs the same checks).
5. Write the PR description directly and concisely (What/Why/How/How to test, per the PR template) — do not include narrative about how the change was investigated or discussed.
6. A maintainer will review and merge once CI is green.

## Design principles

Changes to the library should stay aligned with the project's core goals:

- **Python-idiomatic** — prefer Protocols over ABCs, `T | None` over wrapper types, frozen dataclasses over mutable classes.
- **Zero dependencies** — the package has no runtime dependencies and must stay that way.
- **DDD faithful** — components should map cleanly to DDD concepts. When in doubt, check Evans or Vernon.

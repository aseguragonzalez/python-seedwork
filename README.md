# python-seedwork

[![PyPI version](https://img.shields.io/pypi/v/python-seedwork)](https://pypi.org/project/python-seedwork/)
[![Python](https://img.shields.io/pypi/pyversions/python-seedwork)](https://pypi.org/project/python-seedwork/)
[![License: MIT](https://img.shields.io/pypi/l/python-seedwork)](LICENSE)
[![CI](https://github.com/aseguragonzalez/python-seedwork/actions/workflows/ci.yml/badge.svg)](https://github.com/aseguragonzalez/python-seedwork/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/aseguragonzalez/python-seedwork/branch/main/graph/badge.svg)](https://codecov.io/gh/aseguragonzalez/python-seedwork)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

DDD and Hexagonal Architecture building blocks for Python.

## Goals

- **Unify design patterns.** Provide a shared vocabulary — entities, aggregates, value objects, domain events, CQRS buses — so every bounded context starts from the same foundation.
- **Keep domain logic pure.** The domain layer has zero framework or infrastructure imports. Business rules live in the domain; everything else lives in infrastructure.
- **Clear layer boundaries.** Protocols define contracts; implementations satisfy them structurally. The dependency direction is enforced: domain ← application ← infrastructure.

## Installation

```bash
pip install python-seedwork
```

Requires Python 3.12+. Ships a `py.typed` marker (PEP 561) — mypy and pyright pick up the inline types automatically.

## How to Use

See [Getting Started](docs/getting-started.md) for a step-by-step walkthrough: define a value object, build an aggregate root, create a command handler, and wire a bus.

The [Component Reference](docs/component-reference.md) covers every class and protocol in detail. A complete working example lives in [`docs/examples/bank_account/`](docs/examples/bank_account/).

## What's Included

| Layer | Package | Components |
|---|---|---|
| Domain | `seedwork.domain` | `Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, `DomainEventRecord`, `DomainError`, `Repository`, `UnitOfWork` |
| Application | `seedwork.application` | `Command`, `Query[TResult]`, `CommandHandler`, `QueryHandler`, `CommandBus`, `QueryBus`, `Result`, `DomainEventPublisher`, `DomainEventHandler` |
| Infrastructure | `seedwork.infrastructure` | `RegistryCommandBus`, `RegistryQueryBus`, `TransactionalCommandBus`, `CommandBusBuilder`, `QueryBusBuilder`, `DomainEventPublishingRepository`, `InMemoryRepository` |

All components are also re-exported from the top-level `seedwork` package.

## Built With

- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) — dependency management and packaging
- [Ruff](https://github.com/astral-sh/ruff) — linting and formatting
- [Pyright](https://github.com/microsoft/pyright) — strict static type checking
- [pytest](https://docs.pytest.org/) — testing with coverage gate
- [python-semantic-release](https://python-semantic-release.readthedocs.io/) — automated versioning and changelog

## Development

**Requirements:** Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/aseguragonzalez/python-seedwork.git
cd python-seedwork
make install
```

| Command | Description |
|---|---|
| `make check` | Lint, typecheck, and tests (what CI runs) |
| `make lint` | Run ruff linter |
| `make format` | Format and auto-fix with ruff |
| `make typecheck` | Run pyright |
| `make test` | Run tests with coverage (90% gate) |
| `make test-no-cov` | Run tests without coverage |
| `make clean` | Remove build artifacts and caches |

## Documentation

- [Getting Started](docs/getting-started.md) — step-by-step guide for building with this library
- [Component Reference](docs/component-reference.md) — every class, protocol, and method
- [Best Practices](docs/best-practices.md) — patterns and idioms for effective use
- [Coding Standards](docs/coding-standards.md) — conventions aligned with DDD and Clean Architecture

## Contributing

This project follows the [Conventional Commits](https://www.conventionalcommits.org) specification. The `commit-msg` pre-commit hook enforces the format; `python-semantic-release` derives versions and the changelog from commit prefixes automatically.

## References

- Evans, E. — *Domain-Driven Design: Tackling Complexity in the Heart of Software* (2003)
- Vernon, V. — *Implementing Domain-Driven Design* (2013)
- Martin, R. C. — *Clean Architecture: A Craftsman's Guide to Software Structure and Design* (2017)

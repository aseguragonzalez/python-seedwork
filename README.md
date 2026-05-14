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

## Components

| Layer | Package | Components |
|---|---|---|
| Domain | `seedwork.domain` | `Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, `DomainEventRecord`, `DomainError`, `Repository`, `UnitOfWork` |
| Application | `seedwork.application` | `Command`, `Query[TResult]`, `CommandHandler`, `QueryHandler`, `CommandBus`, `QueryBus`, `Result`, `DomainEventBusPublisher`, `DomainEventBusSubscriber`, `DomainEventBus`, `DomainEventHandler`, `BaseIntegrationEvent`, `IntegrationEvent`, `IntegrationEventPublisher`, `IntegrationEventHandler`, `BackgroundTask`, `TaskScheduler` |
| Infrastructure | `seedwork.infrastructure` | `RegistryCommandBus`, `RegistryQueryBus`, `TransactionalCommandBus`, `DomainEventCoordinatorCommandBus`, `CommandBusBuilder`, `QueryBusBuilder`, `DeferredDomainEventBus`, `DomainEventPublishingRepository`, `InMemoryRepository` |

All components are also re-exported from the top-level `seedwork` package.

## Installation

```bash
pip install python-seedwork
```

Requires Python 3.12+. Ships a `py.typed` marker (PEP 561) — mypy and pyright pick up the inline types automatically.

## Documentation

Comprehensive guides are available in the [`docs/`](docs/) directory:

- [Getting Started](docs/getting-started.md)
- [Component Reference](docs/component-reference.md)
- [Best Practices](docs/best-practices.md)
- [Coding Standards](docs/coding-standards.md)

A complete [Bank Account example](docs/examples/bank_account/) demonstrates all patterns end-to-end.

## Requirements

Python 3.12+, [uv](https://github.com/astral-sh/uv)

## Built With

- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) — dependency management and packaging
- [Ruff](https://github.com/astral-sh/ruff) — linting and formatting
- [Pyright](https://github.com/microsoft/pyright) — strict static type checking
- [pytest](https://docs.pytest.org/) — testing with coverage gate
- [python-semantic-release](https://python-semantic-release.readthedocs.io/) — automated versioning and changelog

## Development

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

## Contributing

This project follows the [Conventional Commits](https://www.conventionalcommits.org) specification. The `commit-msg` pre-commit hook enforces the format; `python-semantic-release` derives versions and the changelog from commit prefixes automatically.

## References

This package draws on the following literature and on the experience of building solid, scalable, and maintainable systems in different stacks (PHP, C#, Python, TypeScript).

- Eric Evans, _Domain-Driven Design: Tackling Complexity in the Heart of Software_ [1]
- Vaughn Vernon, _Implementing Domain-Driven Design_ [2]
- Robert C. Martin, _Clean Architecture: A Craftsman's Guide to Software Structure and Design_ [3]
- .NET Microservices: Architecture for Containerized .NET Applications [4]
- Architecture Patterns with Python, Harry Percival & Bob Gregory [5]

[1]: https://www.amazon.es/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215
[2]: https://www.amazon.es/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577
[3]: https://www.amazon.es/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164
[4]: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/
[5]: https://www.oreilly.com/library/view/architecture-patterns-with/9781492052197/

## License

[MIT](LICENSE)
